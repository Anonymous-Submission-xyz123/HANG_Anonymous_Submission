"""
Dataclasses and serializable schema records for HANG mechanism experiment harness.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime


@dataclass
class TraceRecord:
    trace_id: str
    source_model: str
    source_family: str
    source_task: str
    source_payload_id: str
    source_run_id: str
    source_attack_success: bool
    trace_text_original: str
    trace_text_used: str
    final_answer_text_separate: str
    extraction_method: str
    original_token_count: int = 0
    target_token_count: int = 0
    normalization_steps: List[str] = field(default_factory=list)
    truncation_applied: bool = False
    formatting_metadata: Dict[str, Any] = field(default_factory=dict)
    paired_matched_trace_id: Optional[str] = None
    semantic_unrelatedness_method: Optional[str] = None
    length_difference_tokens: int = 0
    format_match_status: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceRecord":
        return cls(**data)


@dataclass
class BasePromptRecord:
    base_prompt_id: str
    task_id: str
    payload_id: str
    payload_text: str
    task_context: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BasePromptRecord":
        return cls(**data)


@dataclass
class PromptRecord:
    base_prompt_id: str
    condition: str  # 'no_trace', 'matched_trace', 'unrelated_trace'
    rendered_prompt: str
    trace_text: Optional[str] = None
    trace_id: Optional[str] = None
    template_id: str = "default"
    region_character_spans: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Convert tuples to lists for JSON compatibility
        if d.get("region_character_spans"):
            d["region_character_spans"] = {k: list(v) for k, v in d["region_character_spans"].items()}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptRecord":
        data_copy = dict(data)
        if "region_character_spans" in data_copy and data_copy["region_character_spans"]:
            data_copy["region_character_spans"] = {
                k: tuple(v) for k, v in data_copy["region_character_spans"].items()
            }
        return cls(**data_copy)


@dataclass
class TokenSpans:
    system_span: Tuple[int, int] = (0, 0)
    task_context_span: Tuple[int, int] = (0, 0)
    trace_span: Tuple[int, int] = (0, 0)
    payload_span: Tuple[int, int] = (0, 0)
    final_prompt_token_index: int = 0
    generated_token_span: Tuple[int, int] = (0, 0)
    is_valid: bool = True
    invalidation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_span": list(self.system_span),
            "task_context_span": list(self.task_context_span),
            "trace_span": list(self.trace_span),
            "payload_span": list(self.payload_span),
            "final_prompt_token_index": self.final_prompt_token_index,
            "generated_token_span": list(self.generated_token_span),
            "is_valid": self.is_valid,
            "invalidation_reason": self.invalidation_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenSpans":
        return cls(
            system_span=tuple(data.get("system_span", (0, 0))),
            task_context_span=tuple(data.get("task_context_span", (0, 0))),
            trace_span=tuple(data.get("trace_span", (0, 0))),
            payload_span=tuple(data.get("payload_span", (0, 0))),
            final_prompt_token_index=data.get("final_prompt_token_index", 0),
            generated_token_span=tuple(data.get("generated_token_span", (0, 0))),
            is_valid=data.get("is_valid", True),
            invalidation_reason=data.get("invalidation_reason"),
        )


@dataclass
class RunRecord:
    run_id: str
    base_prompt_id: str
    condition: str
    target_model: str
    generation_seed: int
    prompt_token_ids: List[int]
    token_spans: Dict[str, Any]
    generated_token_ids: List[int]
    generated_text: str
    attack_success: bool
    evaluator_version: str
    evaluator_score: float
    evaluator_output: str
    activation_cache_path: Optional[str] = None
    logits_cache_path: Optional[str] = None
    attention_cache_path: Optional[str] = None
    rendered_prompt: Optional[str] = None
    trace_id: Optional[str] = None
    template_id: Optional[str] = None
    generation_config: Dict[str, Any] = field(default_factory=dict)
    cache_metadata_path: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunRecord":
        return cls(**data)


@dataclass
class EvaluationRecord:
    run_id: str
    attack_success: bool
    score: float
    evaluator_version: str
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationRecord":
        return cls(**data)


@dataclass
class AnalysisMetrics:
    base_prompt_id: str
    condition: str
    target_model: str
    mean_trace_attention_mass: float = 0.0
    max_head_trace_attention: float = 0.0
    cosine_similarity_trace_answer: Dict[int, float] = field(default_factory=dict)
    layerwise_logit_shifts: Dict[int, float] = field(default_factory=dict)
    attack_success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisMetrics":
        data_copy = dict(data)
        if "cosine_similarity_trace_answer" in data_copy and isinstance(data_copy["cosine_similarity_trace_answer"], dict):
            data_copy["cosine_similarity_trace_answer"] = {
                int(k): float(v) for k, v in data_copy["cosine_similarity_trace_answer"].items()
            }
        if "layerwise_logit_shifts" in data_copy and isinstance(data_copy["layerwise_logit_shifts"], dict):
            data_copy["layerwise_logit_shifts"] = {
                int(k): float(v) for k, v in data_copy["layerwise_logit_shifts"].items()
            }
        return cls(**data_copy)


@dataclass
class InterventionConfig:
    intervention_type: str  # 'ablation' or 'patching'
    target_layers: List[int]
    target_heads: Optional[List[int]] = None
    patch_location: str = "attn_out"  # 'attn_out', 'post_attn', 'post_mlp'
    donor_condition: str = "matched_trace"
    recipient_condition: str = "unrelated_trace"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterventionConfig":
        return cls(**data)
