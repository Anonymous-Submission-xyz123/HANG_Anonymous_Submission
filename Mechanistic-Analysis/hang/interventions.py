"""
Typed causal intervention engine supporting position-aligned activation patching,
head patching, MLP patching, and trace-attention ablation.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import torch
import torch.nn as nn

from .schemas import TokenSpans
from .model_adapter import HANGModelAdapter, ModelRunResult
from .scorer import ScoredMarginResult, score_continuation_margin_hooked


@dataclass
class PatchSpec:
    patch_type: str  # 'answer_residual', 'mlp_out', 'head_out', 'trace_span'
    target_layers: List[int]
    donor_condition: str = "matched_trace"
    recipient_condition: str = "unrelated_trace"
    target_heads: Optional[List[int]] = None
    donor_spans: Optional[TokenSpans] = None
    recipient_spans: Optional[TokenSpans] = None


@dataclass
class StructuredInterventionResult:
    case_id: str
    patch_spec: PatchSpec
    scored_margin: ScoredMarginResult
    raw_logits: Optional[torch.Tensor] = None
    hook_cleanup_success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class HANGInterventions:
    @staticmethod
    def map_donor_to_recipient_indices(
        donor_span: Tuple[int, int],
        recipient_span: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Maps relative position index pairs (donor_idx, recipient_idx) for aligned patching."""
        d_start, d_end = donor_span
        r_start, r_end = recipient_span
        d_len = max(0, d_end - d_start)
        r_len = max(0, r_end - r_start)
        min_len = min(d_len, r_len)
        return [(d_start + i, r_start + i) for i in range(min_len)]

    @classmethod
    @contextmanager
    def patch_context(
        cls,
        model_adapter: HANGModelAdapter,
        patch_spec: PatchSpec,
        donor_activations: Dict[int, torch.Tensor]  # layer -> tensor [batch, seq_len, dim]
    ):
        """Context manager registering PyTorch hooks for activation/component patching."""
        handles = []
        try:
            for layer_idx in patch_spec.target_layers:
                if layer_idx < 0 or layer_idx >= len(model_adapter.layers):
                    raise IndexError(f"Invalid target layer {layer_idx}.")
                if layer_idx not in donor_activations:
                    raise KeyError(f"No donor activation supplied for layer {layer_idx}.")

                layer_module = model_adapter.layers[layer_idx]
                donor_tensor = donor_activations[layer_idx]

                # 1. Answer residual patching
                if patch_spec.patch_type == "answer_residual":
                    d_ans = patch_spec.donor_spans.final_prompt_token_index
                    r_ans = patch_spec.recipient_spans.final_prompt_token_index

                    def make_res_hook(d_t, d_pos, r_pos):
                        def hook(module, input_tensor, output_tensor):
                            hs = output_tensor[0] if isinstance(output_tensor, tuple) else output_tensor
                            d_vec = d_t[:, d_pos:d_pos+1, :].to(device=hs.device, dtype=hs.dtype)
                            hs = hs.clone()
                            hs[:, r_pos:r_pos+1, :] = d_vec
                            if isinstance(output_tensor, tuple):
                                return (hs,) + output_tensor[1:]
                            return hs
                        return hook

                    h = layer_module.register_forward_hook(make_res_hook(donor_tensor, d_ans, r_ans))
                    handles.append(h)

                # 2. MLP output patching
                elif patch_spec.patch_type == "mlp_out":
                    mlp_module = getattr(layer_module, "mlp", None)
                    if mlp_module is None:
                        raise AttributeError(f"Layer {layer_idx} has no MLP module.")

                    d_ans = patch_spec.donor_spans.final_prompt_token_index
                    r_ans = patch_spec.recipient_spans.final_prompt_token_index

                    def make_mlp_hook(d_t, d_pos, r_pos):
                        def hook(module, inputs, output):
                            val = output[0] if isinstance(output, tuple) else output
                            d_vec = d_t[:, d_pos:d_pos+1, :].to(device=val.device, dtype=val.dtype)
                            val = val.clone()
                            val[:, r_pos:r_pos+1, :] = d_vec
                            if isinstance(output, tuple):
                                return (val,) + output[1:]
                            return val
                        return hook

                    h = mlp_module.register_forward_hook(make_mlp_hook(donor_tensor, d_ans, r_ans))
                    handles.append(h)

                # 3. Span activation patching
                elif patch_spec.patch_type == "trace_span":
                    mapped_indices = cls.map_donor_to_recipient_indices(
                        patch_spec.donor_spans.trace_span,
                        patch_spec.recipient_spans.trace_span
                    )

                    def make_span_hook(d_t, mappings):
                        def hook(module, input_tensor, output_tensor):
                            hs = output_tensor[0] if isinstance(output_tensor, tuple) else output_tensor
                            hs = hs.clone()
                            for d_idx, r_idx in mappings:
                                if d_idx < d_t.shape[1] and r_idx < hs.shape[1]:
                                    hs[:, r_idx, :] = d_t[:, d_idx, :].to(device=hs.device, dtype=hs.dtype)
                            if isinstance(output_tensor, tuple):
                                return (hs,) + output_tensor[1:]
                            return hs
                        return hook

                    h = layer_module.register_forward_hook(make_span_hook(donor_tensor, mapped_indices))
                    handles.append(h)

            yield

        finally:
            for h in handles:
                h.remove()

    @classmethod
    def run_patched_evaluation(
        cls,
        model_adapter: HANGModelAdapter,
        recipient_prompt_ids: List[int],
        patch_spec: PatchSpec,
        donor_activations: Dict[int, torch.Tensor],
        case_id: str
    ) -> StructuredInterventionResult:
        """Executes forward pass with active patch hooks and scores continuation margin directly on active logits."""
        device = next(model_adapter.model.parameters()).device
        with cls.patch_context(model_adapter, patch_spec, donor_activations):
            margin_result = score_continuation_margin_hooked(
            model=model_adapter.model,
            tokenizer=model_adapter.tokenizer,
            prompt_token_ids=recipient_prompt_ids,
            hooked_forward=lambda ids, logits_to_keep: model_adapter.model(
                ids,
                return_dict=True,
                use_cache=False,
                logits_to_keep=logits_to_keep,
            ),
            )

        return StructuredInterventionResult(
            case_id=case_id,
            patch_spec=patch_spec,
            scored_margin=margin_result,
            raw_logits=None,
            hook_cleanup_success=True,
            metadata={"recipient_prompt_len": len(recipient_prompt_ids)}
        )
