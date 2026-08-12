"""
Model adapter with safe PyTorch hook context management for HANG white-box caching.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import torch
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed


@dataclass
class ModelRunResult:
    prompt_token_ids: List[int]
    generated_token_ids: List[int]
    generated_text: str
    logits: Optional[torch.Tensor] = None
    layer_hidden_states: Dict[int, torch.Tensor] = field(default_factory=dict)
    layer_attentions: Dict[int, torch.Tensor] = field(default_factory=dict)
    layer_mlp_outputs: Dict[int, torch.Tensor] = field(default_factory=dict)
    cache_semantics: Dict[str, str] = field(default_factory=dict)


class HANGModelAdapter:
    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen2.5-3B-Instruct",
        torch_dtype: torch.dtype = torch.bfloat16,
        device_map: str = "auto",
        local_files_only: bool = True,
        max_memory: Optional[Dict[Any, str]] = None,
    ):
        self.model_name = model_name_or_path
        self.device_map = device_map

        print(f"[HANGModelAdapter] Loading tokenizer: {model_name_or_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            local_files_only=local_files_only,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print(f"[HANGModelAdapter] Loading model: {model_name_or_path}")
        # Eager attention materializes [batch, heads, seq, seq], which is
        # infeasible for the 7--8k token overnight prompts during ordinary
        # scoring/intervention passes.  Allow an explicit override for
        # attention-analysis runs that genuinely need attention weights.
        # FlexAttention is opt-in until the environment's Triton version
        # provides the AttrsDescriptor API required by torch.compile.
        attn_impl = os.environ.get("HANG_ATTN_IMPLEMENTATION", "eager")
        self.attn_impl = attn_impl
        load_kwargs = {}
        if max_memory is not None:
            load_kwargs["max_memory"] = max_memory
        is_nemotron_omni = (
            isinstance(model_name_or_path, str)
            and "nemotron-3-nano-omni" in model_name_or_path.lower()
        )
        load_attn_impl = "eager" if is_nemotron_omni and attn_impl != "eager" else attn_impl
        effective_device_map = device_map
        if (
            is_nemotron_omni
            and device_map == "auto"
            and torch.cuda.is_available()
        ):
            effective_device_map = {"": 0}
            load_kwargs.pop("max_memory", None)
            print("[HANGModelAdapter] Using single-GPU device map for Nemotron Omni.")
        try:
            from transformers import AutoConfig

            config = AutoConfig.from_pretrained(
                model_name_or_path,
                trust_remote_code=True,
            )
            if hasattr(config, "use_flash_attn"):
                config.use_flash_attn = False
            if hasattr(config, "vision_config"):
                if hasattr(config.vision_config, "use_flash_attn"):
                    config.vision_config.use_flash_attn = False
                config.vision_config._attn_implementation = load_attn_impl
            if hasattr(config, "llm_config"):
                if hasattr(config.llm_config, "use_flash_attn"):
                    config.llm_config.use_flash_attn = False
                config.llm_config._attn_implementation = load_attn_impl

            self.model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                config=config,
                dtype=torch_dtype,
                device_map=effective_device_map,
                local_files_only=local_files_only,
                attn_implementation=load_attn_impl,
                trust_remote_code=True,
                **load_kwargs,
            )
        except Exception as e:
            # Fallback retry without local_files_only if explicitly needed
            missing_cache_terms = (
                "not found in the cache",
                "cannot find the requested files",
                "does not appear to have a file",
                "offline mode",
            )
            if local_files_only and any(term in str(e).lower() for term in missing_cache_terms):
                print(f"[HANGModelAdapter] Local load failed, trying online load for {model_name_or_path}...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name_or_path,
                    config=config,
                    dtype=torch_dtype,
                    device_map=effective_device_map,
                    local_files_only=False,
                    attn_implementation=load_attn_impl,
                    trust_remote_code=True,
                    **load_kwargs,
                )
            else:
                raise e

        if self.attn_impl != load_attn_impl:
            self._set_attention_implementation(self.attn_impl)
        self.model.eval()
        if hasattr(self.model, "language_model"):
            self.model.forward = self.model.language_model.forward
            self.model.generate = self.model.language_model.generate
        self.layers = self._find_layers()
        self.num_layers = len(self.layers)
        print(f"[HANGModelAdapter] Model loaded successfully. Total layers: {self.num_layers}")

    def _set_attention_implementation(self, attn_impl: str) -> None:
        """Patch loaded sub-configs when the multimodal wrapper rejects an impl."""
        visited = set()
        configs = [getattr(self.model, "config", None)]
        for module in self.model.modules():
            configs.append(getattr(module, "config", None))
        for cfg in configs:
            if cfg is None or id(cfg) in visited:
                continue
            visited.add(id(cfg))
            for attr in ("_attn_implementation", "_attn_implementation_internal"):
                if hasattr(cfg, attr):
                    setattr(cfg, attr, attn_impl)
            for nested in ("llm_config", "vision_config"):
                sub_cfg = getattr(cfg, nested, None)
                if sub_cfg is not None:
                    for attr in ("_attn_implementation", "_attn_implementation_internal"):
                        if hasattr(sub_cfg, attr):
                            setattr(sub_cfg, attr, attn_impl)
        print(f"[HANGModelAdapter] Switched loaded attention implementation to {attn_impl}.")

    def _find_layers(self) -> torch.nn.ModuleList:
        """Finds decoder layers in model structure."""
        def _get_submodule(parent, name):
            if name in parent._modules:
                return parent._modules[name]
            return getattr(parent, name)

        # Look in model._modules
        for sub_name in ["text_model", "model", "language_model"]:
            if sub_name in self.model._modules:
                sub = self.model._modules[sub_name]
                if hasattr(sub, "backbone") and hasattr(sub.backbone, "layers"):
                    return sub.backbone.layers
                if "layers" in sub._modules:
                    return _get_submodule(sub, "layers")

        if "layers" in self.model._modules:
            return self.model._modules["layers"]

        if hasattr(self.model, "get_decoder"):
            dec = self.model.get_decoder()
            if hasattr(dec, "layers"):
                return dec.layers

        raise AttributeError(f"Could not locate decoder layers in model {type(self.model)}.")

    @contextmanager
    def hook_context(
        self,
        record_hidden_states: bool = True,
        record_attentions: bool = True,
        record_mlp: bool = False
    ):
        """Context manager for safely registering PyTorch hooks and removing them via try...finally."""
        handles = []
        captured_hidden_states: Dict[int, torch.Tensor] = {}
        captured_attentions: Dict[int, torch.Tensor] = {}
        captured_mlp: Dict[int, torch.Tensor] = {}

        try:
            for layer_idx, layer_module in enumerate(self.layers):
                def make_hook(l_idx):
                    def hook(module, input_tensor, output_tensor):
                        if record_hidden_states:
                            if isinstance(output_tensor, tuple):
                                hs = output_tensor[0]
                            else:
                                hs = output_tensor
                            captured_hidden_states[l_idx] = hs.detach().cpu()

                        if record_attentions and isinstance(output_tensor, tuple) and len(output_tensor) > 1:
                            attn = output_tensor[1]
                            if attn is not None:
                                captured_attentions[l_idx] = attn.detach().cpu()
                    return hook

                h = layer_module.register_forward_hook(make_hook(layer_idx))
                handles.append(h)
                mlp_module = getattr(layer_module, "mlp", None)
                if record_mlp and mlp_module is not None:
                    def make_mlp_hook(l_idx):
                        def mlp_hook(module, inputs, output):
                            value = output[0] if isinstance(output, tuple) else output
                            captured_mlp[l_idx] = value.detach().cpu()
                        return mlp_hook

                    handles.append(
                        mlp_module.register_forward_hook(make_mlp_hook(layer_idx))
                    )

                mixer_module = getattr(layer_module, "mixer", None)
                if record_mlp and mixer_module is not None:
                    def make_mixer_hook(l_idx):
                        def mixer_hook(module, inputs, output):
                            value = output[0] if isinstance(output, tuple) else output
                            captured_mlp[l_idx] = value.detach().cpu()
                        return mixer_hook

                    handles.append(
                        mixer_module.register_forward_hook(make_mixer_hook(layer_idx))
                    )

            yield {
                "hidden_states": captured_hidden_states,
                "attentions": captured_attentions,
                "mlp_outputs": captured_mlp
            }

        finally:
            # Guarantee hook cleanup
            for h in handles:
                h.remove()

    @torch.no_grad()
    def run_with_cache(
        self,
        token_ids: List[int],
        max_new_tokens: int = 128,
        temperature: float = 0.0,
        do_sample: bool = False,
        seed: int = 42,
        record_activations: bool = True
    ) -> ModelRunResult:
        """Generate, then cache a full prompt-plus-generation forward pass."""
        set_seed(seed)
        device = next(self.model.parameters()).device
        input_ids_tensor = torch.tensor([token_ids], dtype=torch.long, device=device)

        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }
        if do_sample and temperature > 0:
            gen_kwargs["temperature"] = temperature

        gen_out = self.model.generate(input_ids_tensor, **gen_kwargs)
        gen_token_ids = gen_out[0][len(token_ids):].tolist()
        gen_text = self.tokenizer.decode(gen_token_ids, skip_special_tokens=True)

        hidden_states_dict = {}
        attentions_dict = {}
        mlp_outputs_dict = {}
        logits_tensor = None

        # Re-run the complete sequence so cached tensors include both prompt and
        # generated positions. This keeps generated_token_span meaningful for
        # downstream activation analysis.
        if record_activations:
            with self.hook_context(
                record_hidden_states=True,
                record_attentions=False,
                record_mlp=True,
            ) as captured:
                outputs = self.model(
                    gen_out,
                    output_hidden_states=True,
                    output_attentions=self.attn_impl == "eager",
                    return_dict=True
                )
                logits_tensor = outputs.logits.detach().cpu()
                hidden_states_dict = captured["hidden_states"]
                attentions_dict = {
                    idx: value.detach().cpu()
                    for idx, value in enumerate(outputs.attentions or ())
                    if value is not None
                }
                mlp_outputs_dict = captured["mlp_outputs"]
        else:
            outputs = self.model(gen_out, return_dict=True)
            logits_tensor = outputs.logits.detach().cpu()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return ModelRunResult(
            prompt_token_ids=token_ids,
            generated_token_ids=gen_token_ids,
            generated_text=gen_text,
            logits=logits_tensor,
            layer_hidden_states=hidden_states_dict,
            layer_attentions=attentions_dict,
            layer_mlp_outputs=mlp_outputs_dict,
            cache_semantics={
                "logits": (
                    "lm_head output over prompt plus generated tokens; shape "
                    "[batch, full_seq, vocab]"
                ),
                "hidden_states": (
                    "decoder-layer output after residual updates and before "
                    "the model final normalization; shape [batch, full_seq, d_model]"
                ),
                "attentions": (
                    "post-softmax attention probabilities; shape "
                    "[batch, heads, query_seq, key_seq]"
                ),
                "mlp_outputs": (
                    "MLP module output before residual addition; shape "
                    "[batch, full_seq, d_model]"
                ),
            },
        )
