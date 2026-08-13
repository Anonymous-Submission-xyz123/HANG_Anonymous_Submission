"""Pure-data summaries for the 30-case HANG mechanism scale-up."""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from hang.resampling import (
    bootstrap_mean_ci,
    paired_sign_flip_p,
    resampling_metadata,
)
from hang.time_to_final import TIME_TO_FINAL_PROTOCOL, summarize_time_to_final


SCALEUP_PROTOCOL = "label_pressure_expression_scaleup_v1"
SCORER_PROTOCOL = "shared_scaffold_label_suffix_prefix_causal_v2"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def summarize_pressure(rows: Sequence[dict]) -> dict:
    lookup = {
        (
            str(row["case_id"]),
            bool(row["marker_present"]),
            str(row["trace_outcome"]),
        ): float(row["margin"])
        for row in rows
    }
    cases = sorted({key[0] for key in lookup})
    expected = {
        (case, marker, outcome)
        for case in cases
        for marker in (False, True)
        for outcome in ("Clean", "Webshell")
    }
    missing = sorted(expected - set(lookup))
    if missing:
        raise ValueError(f"factorial margin cells are missing: {missing}")

    outcome_effects = []
    clean_marker_effects = []
    outcome_marker_interactions = []
    for case in cases:
        effects = {}
        for marker in (False, True):
            effect = (
                lookup[(case, marker, "Clean")]
                - lookup[(case, marker, "Webshell")]
            )
            effects[marker] = effect
            outcome_effects.append(
                {
                    "case_id": case,
                    "marker_present": marker,
                    "outcome_effect": effect,
                }
            )
        clean_marker = (
            lookup[(case, True, "Clean")]
            - lookup[(case, False, "Clean")]
        )
        clean_marker_effects.append(clean_marker)
        outcome_marker_interactions.append(effects[True] - effects[False])

    absolute_pressure = [abs(row["outcome_effect"]) for row in outcome_effects]
    mean_absolute_pressure = statistics.mean(absolute_pressure)
    mean_clean_marker = statistics.mean(clean_marker_effects)
    mean_absolute_clean_marker = statistics.mean(
        abs(value) for value in clean_marker_effects
    )
    mean_interaction = statistics.mean(outcome_marker_interactions)
    minimum_positive = max(1, math.ceil(0.8 * len(cases)))
    positive_without = sum(
        row["outcome_effect"] > 0
        for row in outcome_effects
        if not row["marker_present"]
    )
    positive_with = sum(
        row["outcome_effect"] > 0
        for row in outcome_effects
        if row["marker_present"]
    )
    checks = {
        "positive_pressure_without_marker_at_least_80_percent": (
            positive_without >= minimum_positive
        ),
        "positive_pressure_with_marker_at_least_80_percent": (
            positive_with >= minimum_positive
        ),
        "mean_clean_marker_effect_at_most_quarter_pressure": (
            abs(mean_clean_marker) <= 0.25 * mean_absolute_pressure
        ),
        "mean_absolute_clean_marker_effect_at_most_quarter_pressure": (
            mean_absolute_clean_marker <= 0.25 * mean_absolute_pressure
        ),
        "mean_outcome_marker_interaction_at_most_quarter_pressure": (
            abs(mean_interaction) <= 0.25 * mean_absolute_pressure
        ),
    }
    by_marker = {}
    for marker in (False, True):
        values = [
            row["outcome_effect"]
            for row in outcome_effects
            if row["marker_present"] is marker
        ]
        by_marker[str(marker)] = {
            "n": len(values),
            "positive_count": sum(value > 0 for value in values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "case_bootstrap_ci95": bootstrap_mean_ci(values),
            "sign_flip_p": paired_sign_flip_p(values),
        }
    return {
        "case_count": len(cases),
        "cell_count": len(outcome_effects),
        "positive_cell_count": sum(
            row["outcome_effect"] > 0 for row in outcome_effects
        ),
        "positive_without_marker_count": positive_without,
        "positive_with_marker_count": positive_with,
        "outcome_effects": outcome_effects,
        "outcome_effect_by_marker": by_marker,
        "mean_absolute_trace_outcome_effect": mean_absolute_pressure,
        "mean_clean_marker_margin_effect": mean_clean_marker,
        "mean_absolute_clean_marker_margin_effect": mean_absolute_clean_marker,
        "mean_outcome_by_marker_interaction": mean_interaction,
        "clean_marker_effects": [
            {"case_id": case, "marker_margin_effect": value}
            for case, value in zip(cases, clean_marker_effects)
        ],
        "clean_marker_case_bootstrap_ci95": bootstrap_mean_ci(
            clean_marker_effects
        ),
        "clean_marker_sign_flip_p": paired_sign_flip_p(clean_marker_effects),
        "outcome_by_marker_interactions": [
            {"case_id": case, "outcome_by_marker_interaction": value}
            for case, value in zip(cases, outcome_marker_interactions)
        ],
        "checks": checks,
        "passed_label_pressure_gate": (
            checks["positive_pressure_without_marker_at_least_80_percent"]
            and checks["positive_pressure_with_marker_at_least_80_percent"]
        ),
        "passed_marker_small_pressure_gate": (
            checks["mean_clean_marker_effect_at_most_quarter_pressure"]
            and checks[
                "mean_absolute_clean_marker_effect_at_most_quarter_pressure"
            ]
        ),
        "interaction_diagnostic_is_small": checks[
            "mean_outcome_marker_interaction_at_most_quarter_pressure"
        ],
        "case_level_inference": resampling_metadata(len(cases)),
    }


def summarize_expression(rows: Sequence[dict], cases: Sequence[str]) -> dict:
    selected_cases = [str(case) for case in cases]
    selected_set = set(selected_cases)
    grouped: dict[bool, list[dict]] = defaultdict(list)
    by_case_marker: dict[tuple[str, bool], list[dict]] = defaultdict(list)
    for row in rows:
        case = str(row.get("case_id"))
        if case not in selected_set:
            continue
        marker = bool(row["marker_present"])
        grouped[marker].append(row)
        by_case_marker[(case, marker)].append(row)

    rates = {}
    for marker in (False, True):
        values = grouped[marker]
        exits = sum(bool(row.get("final_channel_found")) for row in values)
        expressions = sum(
            bool(row.get("api_compatible_clean")) for row in values
        )
        rates[str(marker)] = {
            "n": len(values),
            "exit_count": exits,
            "exit_rate": exits / len(values) if values else float("nan"),
            "injected_decision_expression_count": expressions,
            "injected_decision_expression_rate": (
                expressions / len(values) if values else float("nan")
            ),
            "expression_given_exit_rate": (
                expressions / exits if exits else float("nan")
            ),
        }

    case_rows = []
    exit_deltas = []
    expression_deltas = []
    for case in selected_cases:
        absent = by_case_marker[(case, False)]
        present = by_case_marker[(case, True)]
        if not absent or not present:
            raise ValueError(f"incomplete paired generations for {case}")
        exit_absent = statistics.mean(
            bool(row.get("final_channel_found")) for row in absent
        )
        exit_present = statistics.mean(
            bool(row.get("final_channel_found")) for row in present
        )
        expression_absent = statistics.mean(
            bool(row.get("api_compatible_clean")) for row in absent
        )
        expression_present = statistics.mean(
            bool(row.get("api_compatible_clean")) for row in present
        )
        exit_delta = exit_present - exit_absent
        expression_delta = expression_present - expression_absent
        exit_deltas.append(exit_delta)
        expression_deltas.append(expression_delta)
        case_rows.append(
            {
                "case_id": case,
                "exit_rate_without_marker": exit_absent,
                "exit_rate_with_marker": exit_present,
                "marker_exit_rate_delta": exit_delta,
                "expression_rate_without_marker": expression_absent,
                "expression_rate_with_marker": expression_present,
                "marker_expression_rate_delta": expression_delta,
                "seeds_without_marker": len(absent),
                "seeds_with_marker": len(present),
            }
        )

    exit_delta = rates["True"]["exit_rate"] - rates["False"]["exit_rate"]
    expression_delta = (
        rates["True"]["injected_decision_expression_rate"]
        - rates["False"]["injected_decision_expression_rate"]
    )
    minimum_nonnegative = max(1, math.ceil(0.8 * len(selected_cases)))
    checks = {
        "marker_increases_exit_rate": exit_delta > 0,
        "marker_increases_expression_rate": expression_delta > 0,
        "nonnegative_exit_delta_at_least_80_percent_of_cases": (
            sum(value >= 0 for value in exit_deltas) >= minimum_nonnegative
        ),
        "nonnegative_expression_delta_at_least_80_percent_of_cases": (
            sum(value >= 0 for value in expression_deltas)
            >= minimum_nonnegative
        ),
    }
    timed_rows = [
        row
        for row in rows
        if row.get("time_to_final_protocol") == TIME_TO_FINAL_PROTOCOL
    ]
    return {
        "case_count": len(selected_cases),
        "rates_by_marker": rates,
        "marker_exit_rate_delta": exit_delta,
        "marker_expression_rate_delta": expression_delta,
        "mean_paired_case_exit_delta": statistics.mean(exit_deltas),
        "mean_paired_case_expression_delta": statistics.mean(expression_deltas),
        "paired_case_exit_delta_ci95": bootstrap_mean_ci(exit_deltas),
        "paired_case_expression_delta_ci95": bootstrap_mean_ci(
            expression_deltas
        ),
        "paired_case_exit_sign_flip_p": paired_sign_flip_p(exit_deltas),
        "paired_case_expression_sign_flip_p": paired_sign_flip_p(
            expression_deltas
        ),
        "case_level_rates": case_rows,
        "case_level_inference": resampling_metadata(len(selected_cases)),
        "checks": checks,
        "passed_exit_and_expression_gate": all(checks.values()),
        "time_to_final_status": (
            "complete" if len(timed_rows) == len(rows) else "incomplete"
        ),
        "time_to_final": (
            summarize_time_to_final(timed_rows)
            if timed_rows and len(timed_rows) == len(rows)
            else None
        ),
    }


def build_claim_scaleup_summary(
    artifact_dir: Path,
    cases: Sequence[str],
    *,
    generation_seed_count: int = 5,
    generation_max_new_tokens: int = 1024,
) -> dict:
    literal_rows = load_jsonl(
        artifact_dir / "records" / "prefix_causal_factorial.jsonl"
    )
    indirect_rows = load_jsonl(
        artifact_dir / "records" / "indirect_factorial_margins.jsonl"
    )
    generation_rows = load_jsonl(
        artifact_dir / "records" / "expression_generations.jsonl"
    )
    cases = [str(case) for case in cases]
    expected_factorial = 4 * len(cases)
    expected_generations = 2 * len(cases) * int(generation_seed_count)
    generation_counts: dict[tuple[str, bool], int] = defaultdict(int)
    for row in generation_rows:
        generation_counts[(str(row["case_id"]), bool(row["marker_present"]))] += 1
    completion = {
        "literal_factorial": len(literal_rows) == expected_factorial,
        "indirect_factorial": len(indirect_rows) == expected_factorial,
        "generation_row_count": len(generation_rows) == expected_generations,
        "generation_case_marker_cells_complete": all(
            generation_counts[(case, marker)] == int(generation_seed_count)
            for case in cases
            for marker in (False, True)
        ),
    }
    if not all(completion.values()):
        return {
            "protocol": SCALEUP_PROTOCOL,
            "case_count": len(cases),
            "complete": False,
            "completion_checks": completion,
        }

    indirect = json.loads(
        (artifact_dir / "indirect_factorial_summary.json").read_text(
            encoding="utf-8"
        )
    )
    pressure = summarize_pressure(literal_rows)
    expression = summarize_expression(generation_rows, cases)
    supported = bool(
        pressure["passed_label_pressure_gate"]
        and pressure["passed_marker_small_pressure_gate"]
        and indirect["evidence_against_literal_copy_only_gate"]
        and expression["passed_exit_and_expression_gate"]
    )
    return {
        "protocol": SCALEUP_PROTOCOL,
        "scorer_protocol": SCORER_PROTOCOL,
        "case_count": len(cases),
        "generation_seed_count": int(generation_seed_count),
        "generation_max_new_tokens": int(generation_max_new_tokens),
        "complete": True,
        "completion_checks": completion,
        "pressure": pressure,
        "label_free_control": indirect,
        "expression": expression,
        "claim_supported_on_scaled_cohort": supported,
        "interpretation": (
            "Controlled trace conclusions impose label-specific continuation "
            "pressure. Removing literal output labels weakens but does not "
            "eliminate that pressure. A trace-consistent visible marker is "
            "best interpreted as regulating within-budget final expression, "
            "not as the sole source of the controlled-conclusion effect."
        ),
        "scope": [
            "GPT-OSS-20B",
            "Webshell classification",
            "30 prespecified API-successful bypass-derived cases",
            "five generation seeds per marker condition",
            "1024-token generation horizon",
        ],
    }
