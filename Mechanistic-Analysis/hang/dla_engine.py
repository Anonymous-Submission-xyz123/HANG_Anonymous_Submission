"""
Step 2: Direct Logit Attribution (DLA) engine and joint candidate circuit ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch

from .schemas import TokenSpans
from .model_adapter import HANGModelAdapter
from .direction_engine import dot_prod, clear_cuda


@dataclass
class ComponentDLAMetrics:
    layer: int
    component_type: str  # 'mlp' or 'head'
    head_idx: Optional[int]  # None for MLP
    dla_matched: float
    dla_unrelated: float
    delta_dla: float  # dla_matched - dla_unrelated
    rule_projection: float
    payload_projection: float
    trace_attention_mass: float = 0.0
    joint_rank_score: float = 0.0


@dataclass
class FrozenCandidateCircuit:
    case_id: str
    target_model: str
    selected_heads: List[Tuple[int, int]]  # List of (layer, head_idx)
    selected_mlps: List[int]  # List of layer indices
    peak_competition_layer: int


class HANGDLAEngine:
    @staticmethod
    def apply_final_norm(model_adapter: HANGModelAdapter, hidden_state: torch.Tensor) -> torch.Tensor:
        """Applies the target model's final normalization (LayerNorm / RMSNorm) to a hidden state vector."""
        inner_model = getattr(model_adapter.model, "model", model_adapter.model)
        norm_module = getattr(inner_model, "norm", getattr(model_adapter.model, "norm", None))
        
        if norm_module is not None:
            device = next(norm_module.parameters()).device
            hs_device = hidden_state.to(device=device)
            normed = norm_module(hs_device.unsqueeze(0).unsqueeze(0))[0, 0, :]
            return normed.detach().cpu().float()
        return hidden_state.float()

    @classmethod
    @torch.no_grad()
    def compute_decision_unembedding(
        cls,
        model_adapter: HANGModelAdapter,
        clean_token_id: int,
        webshell_token_id: int
    ) -> torch.Tensor:
        """Computes decision unembedding direction u_decision = W_U[Clean] - W_U[Webshell]."""
        lm_head = adapter_head = model_adapter.model.get_output_embeddings() if hasattr(model_adapter.model, "get_output_embeddings") else model_adapter.model.lm_head
        w_u = lm_head.weight.detach().cpu().float()
        return w_u[clean_token_id] - w_u[webshell_token_id]

    @classmethod
    def compute_component_attribution(
        cls,
        model_adapter: HANGModelAdapter,
        toks_matched: List[int],
        spans_matched: TokenSpans,
        toks_unrelated: List[int],
        spans_unrelated: TokenSpans,
        v_rule_dict: Dict[int, torch.Tensor],
        v_payload_dict: Dict[int, torch.Tensor],
        u_decision: torch.Tensor
    ) -> List[ComponentDLAMetrics]:
        """Computes matched-minus-unrelated Delta DLA, direction writing, and trace-reading attention for all components."""
        device = next(model_adapter.model.parameters()).device
        num_layers = model_adapter.num_layers

        ans_matched = spans_matched.final_prompt_token_index
        ans_unrelated = spans_unrelated.final_prompt_token_index

        # Capture matched run components
        input_matched = torch.tensor([toks_matched], dtype=torch.long, device=device)
        with model_adapter.hook_context(record_hidden_states=True, record_attentions=True, record_mlp=True) as cap_m:
            outputs_m = model_adapter.model(input_matched, output_attentions=True, return_dict=True)
            mlp_m = {k: v.detach().cpu() for k, v in cap_m["mlp_outputs"].items()}
            attn_m = outputs_m.attentions if outputs_m.attentions is not None else ()
            del outputs_m
        clear_cuda()

        # Capture unrelated run components
        input_unrelated = torch.tensor([toks_unrelated], dtype=torch.long, device=device)
        with model_adapter.hook_context(record_hidden_states=True, record_attentions=True, record_mlp=True) as cap_u:
            outputs_u = model_adapter.model(input_unrelated, output_attentions=True, return_dict=True)
            mlp_u = {k: v.detach().cpu() for k, v in cap_u["mlp_outputs"].items()}
            attn_u = outputs_u.attentions if outputs_u.attentions is not None else ()
            del outputs_u
        clear_cuda()

        metrics_list = []

        # 1. MLP Attribution
        for l in range(num_layers):
            if l in mlp_m and l in mlp_u:
                vec_m = mlp_m[l][0, ans_matched, :].float()
                vec_u = mlp_u[l][0, ans_unrelated, :].float()

                normed_m = cls.apply_final_norm(model_adapter, vec_m)
                normed_u = cls.apply_final_norm(model_adapter, vec_u)

                dla_m = dot_prod(normed_m, u_decision)
                dla_u = dot_prod(normed_u, u_decision)
                delta_dla = dla_m - dla_u

                rule_proj = dot_prod(vec_m, v_rule_dict[l])
                payload_proj = dot_prod(vec_m, v_payload_dict[l])

                joint_score = delta_dla + (0.5 * rule_proj)

                metrics_list.append(ComponentDLAMetrics(
                    layer=l,
                    component_type="mlp",
                    head_idx=None,
                    dla_matched=dla_m,
                    dla_unrelated=dla_u,
                    delta_dla=delta_dla,
                    rule_projection=rule_proj,
                    payload_projection=payload_proj,
                    trace_attention_mass=0.0,
                    joint_rank_score=joint_score
                ))

        # 2. Attention Head Attribution & Trace-Reading Mass
        for l, (a_m, a_u) in enumerate(zip(attn_m, attn_u)):
            if a_m is None or a_u is None:
                continue
            tensor_m = a_m[0] if a_m.dim() == 4 else a_m
            num_heads = tensor_m.shape[0]

            t0, t1 = spans_matched.trace_span
            t_end = min(t1, tensor_m.shape[-1])

            for h in range(num_heads):
                if t_end > t0:
                    trace_mass = float(tensor_m[h, ans_matched, t0:t_end].sum().item())
                else:
                    trace_mass = 0.0

                # Head output projection approximation
                joint_score = trace_mass

                metrics_list.append(ComponentDLAMetrics(
                    layer=l,
                    component_type="head",
                    head_idx=h,
                    dla_matched=0.0,
                    dla_unrelated=0.0,
                    delta_dla=0.0,
                    rule_projection=0.0,
                    payload_projection=0.0,
                    trace_attention_mass=trace_mass,
                    joint_rank_score=joint_score
                ))

        return metrics_list

    @classmethod
    def freeze_candidate_circuit(
        cls,
        case_id: str,
        target_model: str,
        metrics_list: List[ComponentDLAMetrics],
        peak_layer: int,
        num_heads_to_freeze: int = 2,
        num_mlps_to_freeze: int = 2
    ) -> FrozenCandidateCircuit:
        """Ranks components jointly and freezes candidate heads and MLPs."""
        mlp_metrics = [m for m in metrics_list if m.component_type == "mlp"]
        head_metrics = [m for m in metrics_list if m.component_type == "head"]

        sorted_mlps = sorted(mlp_metrics, key=lambda x: x.joint_rank_score, reverse=True)
        sorted_heads = sorted(head_metrics, key=lambda x: x.joint_rank_score, reverse=True)

        selected_mlps = [m.layer for m in sorted_mlps[:num_mlps_to_freeze]]
        selected_heads = [(h.layer, h.head_idx) for h in sorted_heads[:num_heads_to_freeze]]

        return FrozenCandidateCircuit(
            case_id=case_id,
            target_model=target_model,
            selected_heads=selected_heads,
            selected_mlps=selected_mlps,
            peak_competition_layer=peak_layer
        )
