"""
Quantitative metrics calculation module for attention routing, representation shift, and logit shift.
"""

import os
from typing import Dict, Tuple
import torch

from .cache import HANGCacheManager
from .schemas import AnalysisMetrics, RunRecord, TokenSpans


class HANGMetricsCalculator:
    @staticmethod
    def compute_attention_routing_mass(
        attn_matrix: torch.Tensor,
        answer_idx: int,
        trace_span: Tuple[int, int]
    ) -> float:
        """Computes mean attention mass assigned by answer position to trace tokens across all heads."""
        t_start, t_end = trace_span
        if t_end <= t_start or attn_matrix is None:
            return 0.0

        # attn_matrix shape: [heads, seq_len, seq_len] or [batch, heads, seq_len, seq_len]
        if attn_matrix.dim() == 4:
            attn_matrix = attn_matrix[0]

        if answer_idx >= attn_matrix.shape[-2]:
            answer_idx = attn_matrix.shape[-2] - 1

        # Extract attention from answer token to trace range
        trace_attn = attn_matrix[:, answer_idx, t_start:min(t_end, attn_matrix.shape[-1])]
        mean_mass = trace_attn.sum(dim=-1).mean().item()
        return float(mean_mass)

    @staticmethod
    def compute_max_head_trace_attention(
        attn_matrix: torch.Tensor,
        answer_idx: int,
        trace_span: Tuple[int, int]
    ) -> float:
        """Computes maximum trace attention mass among all attention heads at answer position."""
        t_start, t_end = trace_span
        if t_end <= t_start or attn_matrix is None:
            return 0.0

        if attn_matrix.dim() == 4:
            attn_matrix = attn_matrix[0]

        if answer_idx >= attn_matrix.shape[-2]:
            answer_idx = attn_matrix.shape[-2] - 1

        trace_attn = attn_matrix[:, answer_idx, t_start:min(t_end, attn_matrix.shape[-1])]
        max_mass = trace_attn.sum(dim=-1).max().item()
        return float(max_mass)

    @staticmethod
    def compute_cosine_similarity(
        vec_a: torch.Tensor,
        vec_b: torch.Tensor
    ) -> float:
        """Computes cosine similarity between two vector representations."""
        if vec_a is None or vec_b is None:
            return 0.0
        v_a = vec_a.squeeze().float()
        v_b = vec_b.squeeze().float()
        if v_a.dim() > 1:
            v_a = v_a[-1]  # Use last position token representation
        if v_b.dim() > 1:
            v_b = v_b[-1]
        
        sim = torch.nn.functional.cosine_similarity(v_a.unsqueeze(0), v_b.unsqueeze(0), dim=-1)
        return float(sim.item())

    @staticmethod
    def compute_logit_shift(
        logits_condition: torch.Tensor,
        logits_baseline: torch.Tensor,
        target_token_id: int,
        refusal_token_id: int
    ) -> float:
        """Computes logit shift between attack target token and refusal reference token."""
        if logits_condition is None or logits_baseline is None:
            return 0.0

        l_cond = logits_condition.squeeze()[-1]
        l_base = logits_baseline.squeeze()[-1]

        target_diff = l_cond[target_token_id] - l_base[target_token_id]
        refusal_diff = l_cond[refusal_token_id] - l_base[refusal_token_id]

        shift = (target_diff - refusal_diff).item()
        return float(shift)

    @classmethod
    def compute_saved_run_metrics(
        cls,
        run_record: RunRecord,
        cache_manager: HANGCacheManager,
    ) -> AnalysisMetrics:
        """Regenerate core per-run metrics from persisted tensors only."""
        spans = TokenSpans.from_dict(run_record.token_spans)
        run_dir = os.path.join(cache_manager.cache_dir, run_record.run_id)
        if not os.path.isdir(run_dir):
            raise FileNotFoundError(
                f"No saved cache directory for run '{run_record.run_id}'."
            )

        attention_masses = []
        max_head_masses = []
        similarities: Dict[int, float] = {}
        for filename in sorted(os.listdir(run_dir)):
            if filename.startswith("attention_layer_") and filename.endswith(".pt"):
                layer = int(filename.removesuffix(".pt").rsplit("_", 1)[1])
                tensor = cache_manager.load_cache(
                    run_record.run_id, f"attention_layer_{layer}"
                )
                attention_masses.append(
                    cls.compute_attention_routing_mass(
                        tensor, spans.final_prompt_token_index, spans.trace_span
                    )
                )
                max_head_masses.append(
                    cls.compute_max_head_trace_attention(
                        tensor, spans.final_prompt_token_index, spans.trace_span
                    )
                )
            elif filename.startswith("hidden_state_layer_") and filename.endswith(".pt"):
                layer = int(filename.removesuffix(".pt").rsplit("_", 1)[1])
                tensor = cache_manager.load_cache(
                    run_record.run_id, f"hidden_state_layer_{layer}"
                )
                if (
                    spans.trace_span[1] > spans.trace_span[0]
                    and tensor is not None
                    and tensor.shape[1] > spans.final_prompt_token_index
                ):
                    trace_state = tensor[
                        :, spans.trace_span[0]:spans.trace_span[1], :
                    ].float().mean(dim=1)
                    answer_state = tensor[
                        :, spans.final_prompt_token_index, :
                    ].float()
                    similarities[layer] = cls.compute_cosine_similarity(
                        trace_state, answer_state
                    )

        return AnalysisMetrics(
            base_prompt_id=run_record.base_prompt_id,
            condition=run_record.condition,
            target_model=run_record.target_model,
            mean_trace_attention_mass=(
                sum(attention_masses) / len(attention_masses)
                if attention_masses else 0.0
            ),
            max_head_trace_attention=(
                max(max_head_masses) if max_head_masses else 0.0
            ),
            cosine_similarity_trace_answer=similarities,
            attack_success=run_record.attack_success,
        )
