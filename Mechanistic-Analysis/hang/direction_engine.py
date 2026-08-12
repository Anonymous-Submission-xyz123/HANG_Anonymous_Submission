"""
Step 1: Residual direction discovery engine and causal direction intervention engine.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import gc
from typing import Dict, List, Optional, Tuple, Any
import torch
import torch.nn.functional as F

from .schemas import TokenSpans
from .model_adapter import HANGModelAdapter
from .scorer import ScoredMarginResult, score_continuation_margin_hooked


def clear_cuda():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def dot_prod(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.dot(a.float().flatten(), b.float().flatten()).item())


def cosine_sim(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(F.cosine_similarity(a.float().flatten().unsqueeze(0), b.float().flatten().unsqueeze(0)).item())


@dataclass
class LayerDirectionMetrics:
    layer: int
    rule_direction_norm: float
    payload_direction_norm: float
    s_rule_matched: float
    s_payload_matched: float
    competition_score: float  # s_rule_matched - s_payload_matched
    rule_payload_cosine: float
    rule_relative_norm: float = 0.0


@dataclass
class DirectionInterventionResult:
    case_id: str
    target_layer: int
    intervention_type: str  # 'add_rule', 'sub_rule', 'strengthen_payload', 'random_control'
    coefficient: float
    scored_margin: ScoredMarginResult
    delta_margin_from_baseline: float


class HANGDirectionEngine:
    @staticmethod
    @torch.no_grad()
    def extract_answer_residuals(
        model_adapter: HANGModelAdapter,
        prompt_token_ids: List[int],
        answer_idx: int
    ) -> List[torch.Tensor]:
        """Extracts residual hidden state at answer_idx for every layer (0 to L-1)."""
        device = next(model_adapter.model.parameters()).device
        input_ids = torch.tensor([prompt_token_ids], dtype=torch.long, device=device)
        # Do not request output_hidden_states here: on long prompts that keeps
        # (layers x sequence x hidden) tensors alive and can consume tens of
        # GB.  A forward hook copies only the one semantic position needed for
        # direction discovery.
        residuals_by_layer: Dict[int, torch.Tensor] = {}
        handles = []
        for layer_idx, layer_module in enumerate(model_adapter.layers):
            def make_hook(idx):
                def hook(module, inputs, output):
                    hs = output[0] if isinstance(output, tuple) else output
                    residuals_by_layer[idx] = hs[0, answer_idx, :].detach().cpu().float()
                return hook
            handles.append(layer_module.register_forward_hook(make_hook(layer_idx)))
        try:
            base_model = getattr(
                model_adapter.model,
                model_adapter.model.base_model_prefix,
                None,
            )
            if base_model is None:
                base_model = getattr(model_adapter.model, "model", model_adapter.model)
            outputs = base_model(
                input_ids,
                output_attentions=False,
                use_cache=False,
                return_dict=True,
            )
            del outputs
        finally:
            for handle in handles:
                handle.remove()
        residuals = [residuals_by_layer[i] for i in range(len(model_adapter.layers))]
        del input_ids
        gc.collect()
        clear_cuda()
        return residuals

    @classmethod
    def compute_layer_directions(
        cls,
        model_adapter: HANGModelAdapter,
        toks_matched: List[int],
        ans_matched: int,
        toks_unrelated: List[int],
        ans_unrelated: int,
        toks_no_trace: List[int],
        ans_no_trace: int,
        toks_benign: Optional[List[int]] = None,
        ans_benign: Optional[int] = None
    ) -> Tuple[List[LayerDirectionMetrics], Dict[int, torch.Tensor], Dict[int, torch.Tensor]]:
        """Computes layerwise rule and payload directions, norms, and competition scores."""
        res_matched = cls.extract_answer_residuals(model_adapter, toks_matched, ans_matched)
        res_unrelated = cls.extract_answer_residuals(model_adapter, toks_unrelated, ans_unrelated)
        res_no_trace = cls.extract_answer_residuals(model_adapter, toks_no_trace, ans_no_trace)
        
        if toks_benign is not None and ans_benign is not None:
            res_benign = cls.extract_answer_residuals(model_adapter, toks_benign, ans_benign)
        else:
            res_benign = None

        num_layers = len(res_matched)
        metrics_list = []
        v_rule_dict = {}
        v_payload_dict = {}

        for l in range(num_layers):
            v_r = res_matched[l] - res_unrelated[l]
            norm_r = float(v_r.norm().item())
            residual_scale = 0.5 * (
                float(res_matched[l].norm().item())
                + float(res_unrelated[l].norm().item())
            )
            relative_norm = norm_r / max(residual_scale, 1e-8)
            v_r_hat = v_r / (norm_r + 1e-8)
            v_rule_dict[l] = v_r_hat

            if res_benign is None:
                v_p = torch.zeros_like(v_r)
                norm_p = float("nan")
                v_p_hat = torch.zeros_like(v_r_hat)
            else:
                v_p = res_no_trace[l] - res_benign[l]
                norm_p = float(v_p.norm().item())
                v_p_hat = v_p / (norm_p + 1e-8) if norm_p > 1e-6 else torch.zeros_like(v_r_hat)
            v_payload_dict[l] = v_p_hat

            s_rule = dot_prod(res_matched[l], v_r_hat)
            s_payload = dot_prod(res_matched[l], v_p_hat)
            comp_score = float("nan") if res_benign is None else s_rule - s_payload

            metrics_list.append(LayerDirectionMetrics(
                layer=l,
                rule_direction_norm=norm_r,
                payload_direction_norm=norm_p,
                s_rule_matched=s_rule,
                s_payload_matched=s_payload,
                competition_score=comp_score,
                rule_payload_cosine=(
                    float("nan")
                    if res_benign is None
                    else cosine_sim(v_r, v_p)
                ),
                rule_relative_norm=relative_norm,
            ))

        return metrics_list, v_rule_dict, v_payload_dict

    @classmethod
    @contextmanager
    def vector_intervention_context(
        cls,
        model_adapter: HANGModelAdapter,
        target_layer: int,
        direction_vec: torch.Tensor,
        coefficient: float,
        answer_idx: int
    ):
        """Context manager applying vector intervention (+ coeff * direction_vec) at answer position."""
        handles = []
        layer_module = model_adapter.layers[target_layer]

        def hook(module, input_tensor, output_tensor):
            hs = output_tensor[0] if isinstance(output_tensor, tuple) else output_tensor
            hs = hs.clone()
            add_vec = (coefficient * direction_vec).to(device=hs.device, dtype=hs.dtype)
            hs[:, answer_idx, :] = hs[:, answer_idx, :] + add_vec
            if isinstance(output_tensor, tuple):
                return (hs,) + output_tensor[1:]
            return hs

        h = layer_module.register_forward_hook(hook)
        handles.append(h)
        try:
            yield
        finally:
            for h in handles:
                h.remove()

    @classmethod
    def run_direction_intervention(
        cls,
        model_adapter: HANGModelAdapter,
        case_id: str,
        prompt_token_ids: List[int],
        answer_idx: int,
        target_layer: int,
        direction_vec: torch.Tensor,
        coefficient: float,
        intervention_type: str,
        baseline_margin: float,
        raw_direction_norm: Optional[float] = None,
    ) -> DirectionInterventionResult:
        """Executes vector intervention during hooked pass and scores margin on active logits."""
        device = next(model_adapter.model.parameters()).device
        input_ids = torch.tensor([prompt_token_ids], dtype=torch.long, device=device)

        scale = float(raw_direction_norm) if raw_direction_norm is not None else 1.0
        with cls.vector_intervention_context(model_adapter, target_layer, direction_vec, coefficient * scale, answer_idx):
            margin_result = score_continuation_margin_hooked(
            model=model_adapter.model,
            tokenizer=model_adapter.tokenizer,
            prompt_token_ids=prompt_token_ids,
            hooked_forward=lambda ids, logits_to_keep: model_adapter.model(
                ids, return_dict=True, use_cache=False, logits_to_keep=logits_to_keep
            ))

        return DirectionInterventionResult(
            case_id=case_id,
            target_layer=target_layer,
            intervention_type=intervention_type,
            coefficient=coefficient,
            scored_margin=margin_result,
            delta_margin_from_baseline=margin_result.margin - baseline_margin
        )
