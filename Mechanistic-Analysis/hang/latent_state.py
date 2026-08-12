"""Pure helpers for the cross-case writable latent-state experiment.

The primary intervention site is the textually identical answer scaffold that
follows the transplanted trace and precedes the divergent Clean/Webshell label. A
leave-one-case-out direction is estimated from other cases, which prevents an
exact donor patch from importing either the held-out payload or its literal
outcome-token residuals.
"""

from __future__ import annotations

import itertools
import statistics
from collections import defaultdict
from typing import Mapping, Sequence

import torch

from .scorer import continuation_token_partition


LATENT_STATE_PROTOCOL = "loo_shared_answer_scaffold_prefix_causal_residual_v2"
PRIMARY_ALPHA = 1.0


def answer_scaffold_positions(tokenizer, prompt_token_count: int) -> tuple[list[int], list[int]]:
    """Return absolute positions and token IDs for the shared scoring scaffold."""
    shared, _clean_suffix, _webshell_suffix = continuation_token_partition(tokenizer)
    if not shared:
        raise ValueError("canonical scorer has no shared answer scaffold")
    start = int(prompt_token_count)
    return list(range(start, start + len(shared))), list(shared)


def balanced_sign_patterns(count: int) -> list[tuple[int, ...]]:
    """Enumerate deterministic, nontrivial, maximally balanced sign controls."""
    if count < 2:
        raise ValueError("at least two donor cases are required")
    positive_count = count // 2
    patterns = []
    for positive_indices in itertools.combinations(range(count), positive_count):
        positive = set(positive_indices)
        patterns.append(
            tuple(1 if index in positive else -1 for index in range(count))
        )
    return patterns


def mean_direction(
    clean_by_case: Mapping[str, Mapping[int, torch.Tensor]],
    webshell_by_case: Mapping[str, Mapping[int, torch.Tensor]],
    cases: Sequence[str],
    layers: Sequence[int],
    signs: Sequence[int] | None = None,
) -> dict[int, torch.Tensor]:
    """Average Clean-minus-Webshell residual differences over donor cases."""
    ordered = list(cases)
    if not ordered:
        raise ValueError("direction requires at least one donor case")
    if signs is None:
        signs = [1] * len(ordered)
    if len(signs) != len(ordered):
        raise ValueError("one direction sign is required per donor case")
    result = {}
    for layer in layers:
        values = [
            int(sign) * (
                clean_by_case[case][int(layer)]
                - webshell_by_case[case][int(layer)]
            )
            for case, sign in zip(ordered, signs)
        ]
        result[int(layer)] = torch.stack(values).mean(dim=0)
    return result


def norm_match_direction(
    candidate: Mapping[int, torch.Tensor],
    reference: Mapping[int, torch.Tensor],
    layers: Sequence[int],
) -> dict[int, torch.Tensor]:
    """Match each control layer's norm to the corresponding true direction."""
    matched = {}
    for layer in layers:
        key = int(layer)
        value = candidate[key]
        target = reference[key]
        value_norm = torch.linalg.vector_norm(value.float())
        target_norm = torch.linalg.vector_norm(target.float())
        if float(value_norm) <= 1e-12:
            matched[key] = torch.zeros_like(value)
        else:
            matched[key] = value * (target_norm / value_norm)
    return matched


def _median(values: Sequence[float]) -> float:
    return statistics.median(values) if values else float("nan")


def summarize_latent_state(
    rows: Sequence[dict],
    *,
    primary_alpha: float = PRIMARY_ALPHA,
    min_recovery: float = 0.25,
    identity_tolerance: float = 1e-3,
    monotonic_tolerance: float = 0.05,
) -> dict:
    """Evaluate preregistered exact-transfer, cross-case, and control gates."""
    exact = defaultdict(list)
    cross = defaultdict(list)
    controls = defaultdict(list)
    identity_deltas = []
    dose_rows = defaultdict(dict)
    cases = set()
    for row in rows:
        kind = str(row.get("intervention", ""))
        direction = str(row.get("direction", ""))
        recovery = float(row.get("recovery", float("nan")))
        case_id = str(row.get("case_id", ""))
        if case_id:
            cases.add(case_id)
        if row.get("identity_delta") is not None:
            identity_deltas.append(abs(float(row["identity_delta"])))
        if kind == "exact_scaffold_patch":
            exact[direction].append(recovery)
        elif kind == "cross_case_direction":
            alpha = float(row["alpha"])
            dose_rows[(case_id, direction)][alpha] = recovery
            if abs(alpha - float(primary_alpha)) < 1e-12:
                cross[direction].append(recovery)
        elif kind == "balanced_sign_control":
            controls[(str(row["control_id"]), direction)].append(recovery)

    case_count = len(cases)
    required_positive = max(1, case_count - 1)
    exact_forward = exact["forward"]
    exact_reverse = exact["reverse"]
    cross_forward = cross["forward"]
    cross_reverse = cross["reverse"]
    exact_medians = {
        "forward": _median(exact_forward),
        "reverse": _median(exact_reverse),
    }
    cross_medians = {
        "forward": _median(cross_forward),
        "reverse": _median(cross_reverse),
    }
    control_medians = {
        f"{control_id}_{direction}": _median(values)
        for (control_id, direction), values in sorted(controls.items())
        if values
    }
    absolute_controls = [abs(value) for value in control_medians.values()]

    monotonic_counts = {}
    for direction in ("forward", "reverse"):
        count = 0
        for case_id in sorted(cases):
            values = dose_rows.get((case_id, direction), {})
            ordered = [values[alpha] for alpha in sorted(values)]
            if len(ordered) >= 3 and all(
                after + monotonic_tolerance >= before
                for before, after in zip(ordered, ordered[1:])
            ):
                count += 1
        monotonic_counts[direction] = count

    checks = {
        "identity_noop": (
            bool(identity_deltas)
            and max(identity_deltas) < float(identity_tolerance)
        ),
        "exact_forward_recovery": (
            bool(exact_forward) and exact_medians["forward"] >= min_recovery
        ),
        "exact_reverse_recovery": (
            bool(exact_reverse) and exact_medians["reverse"] >= min_recovery
        ),
        "exact_forward_expected_sign": (
            sum(value > 0 for value in exact_forward) >= required_positive
        ),
        "exact_reverse_expected_sign": (
            sum(value > 0 for value in exact_reverse) >= required_positive
        ),
        "cross_case_forward_recovery": (
            bool(cross_forward) and cross_medians["forward"] >= min_recovery
        ),
        "cross_case_reverse_recovery": (
            bool(cross_reverse) and cross_medians["reverse"] >= min_recovery
        ),
        "cross_case_forward_expected_sign": (
            sum(value > 0 for value in cross_forward) >= required_positive
        ),
        "cross_case_reverse_expected_sign": (
            sum(value > 0 for value in cross_reverse) >= required_positive
        ),
        "forward_dose_monotonic": (
            monotonic_counts.get("forward", 0) >= required_positive
        ),
        "reverse_dose_monotonic": (
            monotonic_counts.get("reverse", 0) >= required_positive
        ),
        "beats_norm_matched_sign_controls": (
            bool(absolute_controls)
            and min(cross_medians.values()) > max(absolute_controls)
            and min(cross_medians.values())
            > 2 * statistics.median(absolute_controls)
        ),
    }
    exact_gate_keys = (
        "identity_noop",
        "exact_forward_recovery",
        "exact_reverse_recovery",
        "exact_forward_expected_sign",
        "exact_reverse_expected_sign",
    )
    cross_gate_keys = (
        "cross_case_forward_recovery",
        "cross_case_reverse_recovery",
        "cross_case_forward_expected_sign",
        "cross_case_reverse_expected_sign",
        "forward_dose_monotonic",
        "reverse_dose_monotonic",
        "beats_norm_matched_sign_controls",
    )
    passed_exact = all(checks[key] for key in exact_gate_keys)
    passed_cross = all(checks[key] for key in cross_gate_keys)
    return {
        "protocol": LATENT_STATE_PROTOCOL,
        "case_count": case_count,
        "primary_alpha": float(primary_alpha),
        "passed_exact_common_token_transfer_gate": passed_exact,
        "passed_cross_case_latent_direction_gate": passed_cross,
        "passed_writable_latent_state_gate": passed_exact and passed_cross,
        "checks": checks,
        "median_exact_recovery": exact_medians,
        "median_cross_case_recovery": cross_medians,
        "max_identity_delta": (
            max(identity_deltas) if identity_deltas else float("nan")
        ),
        "monotonic_case_counts": monotonic_counts,
        "control_median_recoveries": control_medians,
    }
