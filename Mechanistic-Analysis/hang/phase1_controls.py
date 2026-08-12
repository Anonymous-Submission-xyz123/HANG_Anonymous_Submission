"""Utilities and acceptance gates for the corrected HANG Phase 1 screen."""

from __future__ import annotations

from dataclasses import dataclass, replace
from statistics import median
from typing import Iterable, Sequence

from .schemas import TokenSpans


@dataclass(frozen=True)
class LengthMatchedPrompt:
    prompt_token_ids: list[int]
    token_spans: TokenSpans
    matched_trace_tokens: int
    unrelated_trace_tokens: int
    length_difference_tokens: int


def splice_length_matched_trace(
    matched_prompt_token_ids: Sequence[int],
    matched_spans: TokenSpans,
    unrelated_trace_token_ids: Sequence[int],
    *,
    tolerance_tokens: int = 15,
) -> LengthMatchedPrompt:
    """Replace only the matched trace token span with an unrelated trace.

    Building the control from the matched prompt keeps the system, task,
    payload, and suffix token IDs identical.  The replacement is rejected
    before any model work if its target-token length differs by more than the
    configured tolerance.
    """
    trace_start, trace_end = matched_spans.trace_span
    if not (0 <= trace_start < trace_end <= len(matched_prompt_token_ids)):
        raise ValueError("matched trace span is invalid")
    if not unrelated_trace_token_ids:
        raise ValueError("unrelated trace must not be empty")
    if tolerance_tokens < 0:
        raise ValueError("tolerance_tokens must be nonnegative")

    matched_count = trace_end - trace_start
    unrelated_count = len(unrelated_trace_token_ids)
    difference = unrelated_count - matched_count
    if abs(difference) > tolerance_tokens:
        raise ValueError(
            "unrelated trace length mismatch: "
            f"matched={matched_count}, unrelated={unrelated_count}, "
            f"tolerance={tolerance_tokens}"
        )

    prompt_ids = (
        list(matched_prompt_token_ids[:trace_start])
        + list(unrelated_trace_token_ids)
        + list(matched_prompt_token_ids[trace_end:])
    )

    def shift_span(span: tuple[int, int]) -> tuple[int, int]:
        # Only spans lying entirely at or after the replaced trace move by the
        # length delta.  Spans that precede the trace (e.g. the payload in the
        # marker-ablation layout, where payload comes *before* the trace) keep
        # their original indices.  Shifting them unconditionally corrupts the
        # payload span whenever the trace does not precede the payload.
        if span[0] >= trace_end:
            return (span[0] + difference, span[1] + difference)
        return span

    new_spans = replace(
        matched_spans,
        trace_span=(trace_start, trace_start + unrelated_count),
        payload_span=shift_span(matched_spans.payload_span),
        final_prompt_token_index=(
            matched_spans.final_prompt_token_index + difference
        ),
        # This helper constructs a prompt, not a completed generation.
        generated_token_span=(len(prompt_ids), len(prompt_ids)),
    )
    if new_spans.final_prompt_token_index != len(prompt_ids) - 1:
        raise ValueError("rebuilt final prompt index is inconsistent")

    return LengthMatchedPrompt(
        prompt_token_ids=prompt_ids,
        token_spans=new_spans,
        matched_trace_tokens=matched_count,
        unrelated_trace_tokens=unrelated_count,
        length_difference_tokens=abs(difference),
    )


def bidirectional_effect(add_delta: float, remove_delta: float) -> float:
    return (add_delta - remove_delta) / 2.0


def choose_control_layers(
    num_layers: int, selected_layer: int
) -> list[int]:
    """Return three distinct location controls, excluding the selected layer."""
    if num_layers < 4:
        raise ValueError("at least four layers are required")
    requested = [0, num_layers // 2, num_layers - 1]
    controls: list[int] = []
    for layer in requested:
        if layer == selected_layer or layer in controls:
            candidates = sorted(
                (
                    candidate
                    for candidate in range(num_layers)
                    if candidate != selected_layer and candidate not in controls
                ),
                key=lambda candidate: (abs(candidate - layer), candidate),
            )
            layer = candidates[0]
        controls.append(layer)
    return controls


def evaluate_phase1_gates(
    real_rows: Sequence[dict],
    random_effects: Iterable[float],
    layer_control_effects: Iterable[float],
    *,
    tolerance: float = 1e-4,
) -> dict:
    """Evaluate the signed, dose, random, and location gates."""
    ordered = sorted(real_rows, key=lambda row: float(row["coefficient"]))
    one = next(row for row in ordered if float(row["coefficient"]) == 1.0)
    add = [float(row["add_delta"]) for row in ordered]
    remove = [float(row["remove_delta"]) for row in ordered]
    random_abs = [abs(float(value)) for value in random_effects]
    layer_abs = [abs(float(value)) for value in layer_control_effects]
    if len(random_abs) != 5:
        raise ValueError("exactly five random effects are required")
    if len(layer_abs) != 3:
        raise ValueError("exactly three layer-control effects are required")

    real_effect = bidirectional_effect(
        float(one["add_delta"]), float(one["remove_delta"])
    )
    checks = {
        "real_addition_positive_at_1x": float(one["add_delta"]) > 0,
        "real_removal_negative_at_1x": float(one["remove_delta"]) < 0,
        "addition_nondecreasing": all(
            later >= earlier - tolerance
            for earlier, later in zip(add, add[1:])
        ),
        "removal_nonincreasing": all(
            later <= earlier + tolerance
            for earlier, later in zip(remove, remove[1:])
        ),
        "real_gt_2x_random_median": (
            real_effect > 2 * median(random_abs)
        ),
        "real_gt_random_max": real_effect > max(random_abs),
        "real_gt_2x_layer_median": (
            real_effect > 2 * median(layer_abs)
        ),
        "real_gt_layer_max": real_effect > max(layer_abs),
    }
    return {
        "passed": all(checks.values()),
        "real_effect": real_effect,
        "median_abs_random_effect": median(random_abs),
        "max_abs_random_effect": max(random_abs),
        "median_abs_layer_control_effect": median(layer_abs),
        "max_abs_layer_control_effect": max(layer_abs),
        "checks": checks,
    }
