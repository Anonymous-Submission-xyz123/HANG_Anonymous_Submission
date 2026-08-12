"""
Step 3: Targeted Path Patching engine and signed gap recovery analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import torch

from .schemas import TokenSpans, RunRecord
from .model_adapter import HANGModelAdapter
from .dla_engine import FrozenCandidateCircuit
from .interventions import HANGInterventions, PatchSpec, StructuredInterventionResult
from .direction_engine import clear_cuda


@dataclass
class PathPatchSummary:
    case_id: str
    target_model: str
    patch_type: str
    donor_condition: str
    receiver_condition: str
    donor_baseline_margin: float
    receiver_baseline_margin: float
    patched_margin: float
    donor_receiver_gap: float  # donor_margin - receiver_margin
    patched_receiver_delta: float  # patched_margin - receiver_margin
    gap_recovery_percent: float
    patched_layers: List[int]
    status: str


class HANGPathPatchEngine:
    @classmethod
    def calculate_gap_recovery(
        cls,
        donor_margin: float,
        receiver_margin: float,
        patched_margin: float
    ) -> float:
        """Calculates signed gap recovery percentage: (patched - receiver) / (donor - receiver) * 100."""
        denom = donor_margin - receiver_margin
        if abs(denom) < 1e-6:
            return 0.0
        return ((patched_margin - receiver_margin) / denom) * 100.0

    @classmethod
    def run_forward_path_patch(
        cls,
        model_adapter: HANGModelAdapter,
        circuit: FrozenCandidateCircuit,
        donor_rec: RunRecord,
        donor_spans: TokenSpans,
        receiver_rec: RunRecord,
        recipient_spans: TokenSpans,
        patch_type: str = "mlp_out",
        donor_margin: Optional[float] = None,
        receiver_margin: Optional[float] = None,
    ) -> PathPatchSummary:
        """Executes forward path patching (Donor: Matched HANG -> Receiver: Unrelated or No-Trace)."""
        device = next(model_adapter.model.parameters()).device
        num_layers = model_adapter.num_layers

        # Capture donor hidden states
        donor_input = torch.tensor([donor_rec.prompt_token_ids], dtype=torch.long, device=device)
        with model_adapter.hook_context(record_hidden_states=True, record_mlp=True) as captured:
            outputs = model_adapter.model(donor_input, return_dict=True)
            if patch_type == "mlp_out":
                donor_activations = {k: v.detach().cpu() for k, v in captured["mlp_outputs"].items()}
            else:
                donor_activations = {k: v.detach().cpu() for k, v in captured["hidden_states"].items()}
            del outputs
        clear_cuda()

        patch_spec = PatchSpec(
            patch_type=patch_type,
            target_layers=circuit.selected_mlps,
            donor_condition=donor_rec.condition,
            recipient_condition=receiver_rec.condition,
            donor_spans=donor_spans,
            recipient_spans=recipient_spans
        )

        res: StructuredInterventionResult = HANGInterventions.run_patched_evaluation(
            model_adapter=model_adapter,
            recipient_prompt_ids=receiver_rec.prompt_token_ids,
            patch_spec=patch_spec,
            donor_activations=donor_activations,
            case_id=circuit.case_id
        )

        # Baseline margins from unpatched records if available, else scored
        if donor_margin is None or receiver_margin is None:
            raise ValueError("donor_margin and receiver_margin are required for signed recovery")
        patched_margin = res.scored_margin.margin

        gap = donor_margin - receiver_margin
        delta = patched_margin - receiver_margin
        recovery_pct = cls.calculate_gap_recovery(donor_margin, receiver_margin, patched_margin)

        return PathPatchSummary(
            case_id=circuit.case_id,
            target_model=circuit.target_model,
            patch_type=patch_type,
            donor_condition=donor_rec.condition,
            receiver_condition=receiver_rec.condition,
            donor_baseline_margin=donor_margin,
            receiver_baseline_margin=receiver_margin,
            patched_margin=patched_margin,
            donor_receiver_gap=gap,
            patched_receiver_delta=delta,
            gap_recovery_percent=recovery_pct,
            patched_layers=circuit.selected_mlps,
            status="PASSED"
        )
