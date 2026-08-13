"""Run the two preregistered controls required before HANG scale-up.

Controls:

1. Semantic outcome traces that omit the literal ``Clean``/``Webshell``
   strings, scored with the corrected prefix-causal continuation scorer.
2. Censoring-aware time-to-final analysis, with an optional longer-cap
   generation run under the original literal-label trace protocol.

The control artifacts use separate filenames and never overwrite the current
paper-facing factorial or generation records.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Sequence

import torch
from transformers import AutoTokenizer

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_hang_eacl_focused import (
    JsonlStore,
    atomic_json,
    first_label,
    generate_one,
    has_api_clean_explanation,
    load_jsonl,
    now,
    summarize_generations,
    write_csv,
)
from hang.eacl_focused import (
    COUNTERFACTUAL_PROTOCOL,
    INDIRECT_COUNTERFACTUAL_PROTOCOL,
    PreparedOutcomePair,
    load_prepared_pairs,
)
from hang.model_adapter import HANGModelAdapter
from hang.scorer import (
    PREFIX_CAUSAL_SCORER_PROTOCOL,
    score_continuation_margin_prefix_causal,
)
from hang.time_to_final import annotate_generation_timing


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DATA = ROOT / "data" / "claim_scaleup_30"
DEFAULT_LITERAL_PREPARED = RELEASE_DATA / "prepared_literal"
DEFAULT_INDIRECT_PREPARED = (
    RELEASE_DATA / "prepared_label_free"
)
DEFAULT_REFERENCE_FACTORIAL = (
    ROOT
    / "artifacts/claim_scaleup_30"
    / "records/prefix_causal_factorial.jsonl"
)
DEFAULT_REFERENCE_GENERATIONS = (
    ROOT
    / "artifacts/claim_scaleup_30"
    / "records/expression_generations.jsonl"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "hang_claim_scaleup_30_controls"
DEFAULT_CASES = (
    "529",
    "Ajax_PHP_Command_Shell",
    "Antichat_Shell",
    "CasuS-1.5",
    "DTool_Pro",
    "Dive_Shell",
    "GRP_WebShell",
    "NCC-Shell",
    "Non-alphanumeric",
    "Rootshell.v.1.0",
    "Safe_Mode_Bypass",
    "SimShell",
    "Uploader",
    "accept_language",
    "backupsql",
    "configkillerionkros",
    "ftpsearch",
    "h4ntu_shell",
    "hiddens_shell",
    "lolipop",
    "php-findsock-shell",
    "php-reverse-shell",
    "php-web-shell",
    "pws",
    "qsd-backdoor",
    "robots",
    "rootshell",
    "s72_Shell",
    "simattacker",
    "wwwolf-webshell",
)
DEFAULT_SEEDS = (41, 42, 43, 44, 45)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=(
            "score_indirect",
            "generate_indirect",
            "reanalyze_existing",
            "generate_long",
        ),
        default=["reanalyze_existing"],
    )
    parser.add_argument(
        "--literal-prepared-dir",
        type=Path,
        default=DEFAULT_LITERAL_PREPARED,
    )
    parser.add_argument(
        "--indirect-prepared-dir",
        type=Path,
        default=DEFAULT_INDIRECT_PREPARED,
    )
    parser.add_argument(
        "--reference-factorial-records",
        type=Path,
        default=DEFAULT_REFERENCE_FACTORIAL,
    )
    parser.add_argument(
        "--reference-generations",
        type=Path,
        default=DEFAULT_REFERENCE_GENERATIONS,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model-path", default="openai/gpt-oss-20b")
    parser.add_argument("--cases", nargs="*", default=list(DEFAULT_CASES))
    parser.add_argument(
        "--generation-seeds",
        nargs="+",
        type=int,
        default=list(DEFAULT_SEEDS),
    )
    parser.add_argument("--existing-max-new-tokens", type=int, default=1024)
    parser.add_argument("--indirect-max-new-tokens", type=int, default=1024)
    parser.add_argument("--long-max-new-tokens", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.15)
    parser.add_argument("--top-p", type=float, default=0.6)
    parser.add_argument(
        "--min-indirect-retained-fraction",
        type=float,
        default=0.25,
        help=(
            "Preregistered descriptive gate: mean absolute indirect outcome "
            "effect divided by the literal-label reference effect."
        ),
    )
    parser.add_argument(
        "--attn-implementation",
        choices=("flash_attention_3", "flex_attention", "eager"),
        default="eager",
    )
    parser.add_argument("--gpu-weight-budget-gib", type=int, default=60)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def select_pairs(
    directory: Path,
    cases: Sequence[str],
    *,
    required_protocol: str,
    require_literal_labels_absent: bool,
) -> list[PreparedOutcomePair]:
    selected = set(cases)
    pairs = [
        pair
        for pair in load_prepared_pairs(directory)
        if not selected or pair.case_id in selected
    ]
    by_case = defaultdict(set)
    for pair in pairs:
        by_case[pair.case_id].add(bool(pair.marker_present))
    incomplete = [
        case for case, markers in by_case.items() if markers != {False, True}
    ]
    if incomplete:
        raise ValueError(f"missing marker/no-marker pairs for {incomplete}")
    invalid = [
        pair.pair_id
        for pair in pairs
        if pair.counterfactual_protocol != required_protocol
        or pair.outcome_span is None
        or not pair.all_differences_inside_outcome_span
        or (
            require_literal_labels_absent
            and not pair.literal_output_labels_absent
        )
    ]
    if invalid:
        raise ValueError(
            f"prepared control audit failed for protocol "
            f"{required_protocol}: {invalid}"
        )
    if not pairs:
        raise ValueError("case filter selected no prepared pairs")
    return sorted(pairs, key=lambda pair: pair.pair_id)


def _outcome_effects(rows: Sequence[dict]) -> list[dict]:
    lookup = {
        (
            str(row["case_id"]),
            bool(row["marker_present"]),
            str(row["trace_outcome"]),
        ): float(row["margin"])
        for row in rows
    }
    effects = []
    for case, marker in sorted({(key[0], key[1]) for key in lookup}):
        clean_key = (case, marker, "Clean")
        webshell_key = (case, marker, "Webshell")
        if clean_key not in lookup or webshell_key not in lookup:
            continue
        effects.append(
            {
                "case_id": case,
                "marker_present": marker,
                "outcome_effect": lookup[clean_key] - lookup[webshell_key],
            }
        )
    return effects


def summarize_indirect_factorial(
    rows: Sequence[dict],
    reference_rows: Sequence[dict],
    *,
    min_retained_fraction: float,
) -> dict:
    effects = _outcome_effects(rows)
    reference_effects = _outcome_effects(reference_rows)
    reference_lookup = {
        (row["case_id"], bool(row["marker_present"])): float(
            row["outcome_effect"]
        )
        for row in reference_effects
    }
    retention_rows = []
    for row in effects:
        key = (row["case_id"], bool(row["marker_present"]))
        reference = reference_lookup.get(key)
        if reference is None or abs(reference) <= 1e-12:
            continue
        retention_rows.append(
            {
                **row,
                "literal_reference_outcome_effect": reference,
                "signed_retained_fraction": (
                    float(row["outcome_effect"]) / reference
                ),
                "absolute_retained_fraction": (
                    abs(float(row["outcome_effect"])) / abs(reference)
                ),
            }
        )

    mean_absolute_effect = (
        statistics.mean(abs(float(row["outcome_effect"])) for row in effects)
        if effects
        else float("nan")
    )
    matched_reference_values = [
        abs(float(row["literal_reference_outcome_effect"]))
        for row in retention_rows
    ]
    mean_absolute_reference = (
        statistics.mean(matched_reference_values)
        if matched_reference_values
        else float("nan")
    )
    retained_fraction = (
        mean_absolute_effect / mean_absolute_reference
        if mean_absolute_reference > 0
        else float("nan")
    )
    cases = sorted({str(row["case_id"]) for row in effects})
    required_positive = max(1, math.ceil(0.8 * len(cases)))
    positive_by_marker = {
        str(marker): sum(
            float(row["outcome_effect"]) > 0
            for row in effects
            if bool(row["marker_present"]) is marker
        )
        for marker in (False, True)
    }
    direction_gate = all(
        count >= required_positive for count in positive_by_marker.values()
    )
    retained_gate = retained_fraction >= float(min_retained_fraction)
    return {
        "control_protocol": INDIRECT_COUNTERFACTUAL_PROTOCOL,
        "scorer_protocol": PREFIX_CAUSAL_SCORER_PROTOCOL,
        "case_count": len(cases),
        "cell_count": len(effects),
        "literal_output_labels_absent": all(
            bool(row.get("literal_output_labels_absent")) for row in rows
        ),
        "positive_outcome_cells": sum(
            float(row["outcome_effect"]) > 0 for row in effects
        ),
        "positive_outcome_cases_by_marker": positive_by_marker,
        "mean_absolute_indirect_outcome_effect": mean_absolute_effect,
        "mean_absolute_literal_reference_effect": mean_absolute_reference,
        "mean_absolute_retained_fraction": retained_fraction,
        "min_indirect_retained_fraction": float(min_retained_fraction),
        "expected_direction_gate": direction_gate,
        "retained_fraction_gate": retained_gate,
        "evidence_against_literal_copy_only_gate": (
            direction_gate and retained_gate
        ),
        "outcome_effects": effects,
        "retention_by_cell": retention_rows,
    }


def run_indirect_scores(
    adapter: HANGModelAdapter,
    pairs: Sequence[PreparedOutcomePair],
    output: Path,
    reference_rows: Sequence[dict],
    *,
    resume: bool,
    min_retained_fraction: float,
) -> dict:
    store = JsonlStore(
        output / "records/indirect_factorial_margins.jsonl",
        ("pair_id", "trace_outcome"),
        resume,
    )
    for index, pair in enumerate(pairs, start=1):
        for outcome, prompt_ids in (
            ("Clean", pair.clean_prompt_token_ids),
            ("Webshell", pair.webshell_prompt_token_ids),
        ):
            if store.get(pair_id=pair.pair_id, trace_outcome=outcome):
                continue
            result = score_continuation_margin_prefix_causal(
                adapter.model,
                adapter.tokenizer,
                list(prompt_ids),
            )
            store.add(
                {
                    "pair_id": pair.pair_id,
                    "case_id": pair.case_id,
                    "marker_present": bool(pair.marker_present),
                    "trace_outcome": outcome,
                    "counterfactual_protocol": pair.counterfactual_protocol,
                    "outcome_encoding": pair.outcome_encoding,
                    "literal_output_labels_absent": (
                        pair.literal_output_labels_absent
                    ),
                    "scorer_protocol": PREFIX_CAUSAL_SCORER_PROTOCOL,
                    "margin": float(result.margin),
                    "clean_logprob": float(result.clean_logprob),
                    "webshell_logprob": float(result.webshell_logprob),
                    "predicted_label": result.parsed_label,
                    "timestamp": now(),
                }
            )
        print(f"[control:indirect-score] {index}/{len(pairs)} {pair.pair_id}")

    write_csv(output / "tables/indirect_factorial_margins.csv", store.rows)
    summary = summarize_indirect_factorial(
        store.rows,
        reference_rows,
        min_retained_fraction=min_retained_fraction,
    )
    atomic_json(output / "indirect_factorial_summary.json", summary)
    return summary


def _evaluate_generated_record(
    pair: PreparedOutcomePair,
    seed: int,
    generated: dict,
    *,
    generation_protocol: str,
) -> dict:
    final_text = str(generated["generated_final_text"])
    label = first_label(final_text)
    clean_explanation = has_api_clean_explanation(final_text)
    api_compatible_clean = bool(
        (label and label.lower().startswith(("clean", "not")))
        or clean_explanation
    )
    return {
        "pair_id": pair.pair_id,
        "case_id": pair.case_id,
        "marker_present": bool(pair.marker_present),
        "trace_outcome": "Clean",
        "counterfactual_protocol": pair.counterfactual_protocol,
        "outcome_encoding": pair.outcome_encoding,
        "literal_output_labels_absent": pair.literal_output_labels_absent,
        "generation_protocol": generation_protocol,
        "seed": int(seed),
        "parsed_label": label,
        "final_channel_found": bool(final_text),
        "label_source": (
            "structured_final_label"
            if label
            else "api_clean_explanation"
            if clean_explanation
            else "unparsed"
        ),
        "api_compatible_clean": api_compatible_clean,
        "timestamp": now(),
        **generated,
    }


def run_control_generations(
    adapter: HANGModelAdapter,
    pairs: Sequence[PreparedOutcomePair],
    output: Path,
    *,
    seeds: Sequence[int],
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    resume: bool,
    artifact_prefix: str,
    generation_protocol: str,
    reference_rows: Sequence[dict] = (),
) -> dict:
    store = JsonlStore(
        output / f"records/{artifact_prefix}_generations.jsonl",
        ("pair_id", "seed"),
        resume,
    )
    reference_lookup = {
        (str(row["pair_id"]), int(row["seed"])): row
        for row in reference_rows
    }
    for index, pair in enumerate(pairs, start=1):
        for seed in seeds:
            if store.get(pair_id=pair.pair_id, seed=int(seed)):
                continue
            generated = generate_one(
                adapter,
                pair.clean_prompt_token_ids,
                int(seed),
                int(max_new_tokens),
                float(temperature),
                float(top_p),
            )
            row = _evaluate_generated_record(
                pair,
                int(seed),
                generated,
                generation_protocol=generation_protocol,
            )
            row.update(
                annotate_generation_timing(
                    adapter.tokenizer,
                    row,
                    max_new_tokens=int(max_new_tokens),
                )
            )
            reference = reference_lookup.get((pair.pair_id, int(seed)))
            if reference is not None:
                reference_ids = [
                    int(value)
                    for value in reference.get("generated_token_ids", [])
                ]
                generated_ids = [
                    int(value) for value in row["generated_token_ids"]
                ]
                row["reference_generation_tokens"] = len(reference_ids)
                row["reference_prefix_match"] = (
                    len(generated_ids) >= len(reference_ids)
                    and generated_ids[: len(reference_ids)] == reference_ids
                )
            store.add(row)
        print(
            f"[control:{artifact_prefix}] "
            f"{index}/{len(pairs)} {pair.pair_id}"
        )

    write_csv(
        output / f"tables/{artifact_prefix}_generations.csv",
        store.rows,
    )
    summary = summarize_generations(store.rows)
    audited = [
        bool(row["reference_prefix_match"])
        for row in store.rows
        if "reference_prefix_match" in row
    ]
    summary.update(
        {
            "generation_protocol": generation_protocol,
            "generation_max_new_tokens": int(max_new_tokens),
            "generation_temperature": float(temperature),
            "generation_top_p": float(top_p),
            "reference_prefix_audit_count": len(audited),
            "all_reference_prefixes_match": (
                all(audited) if audited else None
            ),
            "horizon_comparison_status": (
                "exact_trajectory_extension"
                if audited and all(audited)
                else "standalone_long_horizon_rerun"
                if audited
                else "no_reference_prefix_audit"
            ),
        }
    )
    atomic_json(output / f"{artifact_prefix}_summary.json", summary)
    return summary


def reanalyze_existing_generations(
    tokenizer,
    reference_path: Path,
    output: Path,
    *,
    cases: Sequence[str],
    max_new_tokens: int,
) -> dict:
    selected = set(cases)
    source_rows = [
        row
        for row in load_jsonl(reference_path)
        if not selected or str(row.get("case_id")) in selected
    ]
    if not source_rows:
        raise FileNotFoundError(
            f"no matching generation records in {reference_path}"
        )
    rows = []
    for source in source_rows:
        row = dict(source)
        row["source_generation_records"] = str(reference_path.resolve())
        row.update(
            annotate_generation_timing(
                tokenizer,
                row,
                max_new_tokens=int(max_new_tokens),
            )
        )
        rows.append(row)
    records_path = output / "records/existing_time_to_final.jsonl"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = records_path.with_suffix(".jsonl.tmp")
    temporary.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    temporary.replace(records_path)
    write_csv(output / "tables/existing_time_to_final.csv", rows)
    summary = summarize_generations(rows)
    summary["source_generation_records"] = str(reference_path.resolve())
    summary["generation_max_new_tokens"] = int(max_new_tokens)
    atomic_json(output / "existing_time_to_final_summary.json", summary)
    return summary


def write_readme(output: Path) -> None:
    indirect_path = output / "indirect_factorial_summary.json"
    existing_path = output / "existing_time_to_final_summary.json"
    long_path = output / "long_expression_summary.json"
    indirect = (
        json.loads(indirect_path.read_text(encoding="utf-8"))
        if indirect_path.exists()
        else None
    )
    existing = (
        json.loads(existing_path.read_text(encoding="utf-8"))
        if existing_path.exists()
        else None
    )
    long = (
        json.loads(long_path.read_text(encoding="utf-8"))
        if long_path.exists()
        else None
    )
    package_summary = {
        "control_package": "hang_pre_scale_controls_v1",
        "no_literal_label_score_complete": indirect is not None,
        "no_literal_label_descriptive_gate": (
            indirect.get("evidence_against_literal_copy_only_gate")
            if indirect
            else None
        ),
        "existing_time_to_final_complete": existing is not None,
        "existing_timing_parser_audit": (
            existing.get("time_to_final", {}).get(
                "all_timing_parsers_match"
            )
            if existing
            else None
        ),
        "long_horizon_complete": long is not None,
        "long_horizon_timing_parser_audit": (
            long.get("time_to_final", {}).get("all_timing_parsers_match")
            if long
            else None
        ),
        "long_horizon_comparison_status": (
            long.get("horizon_comparison_status") if long else None
        ),
        "reference_prefix_audit_passed": (
            long.get("all_reference_prefixes_match") if long else None
        ),
    }
    package_summary["required_controls_complete"] = bool(
        package_summary["no_literal_label_score_complete"]
        and package_summary["existing_time_to_final_complete"]
        and package_summary["long_horizon_complete"]
    )
    package_summary["required_control_gates_passed"] = bool(
        package_summary["no_literal_label_descriptive_gate"]
        and package_summary["existing_timing_parser_audit"]
        and package_summary["long_horizon_timing_parser_audit"]
    )
    atomic_json(output / "control_summary.json", package_summary)
    lines = [
        "# HANG pre-scale controls",
        "",
        "- No-literal-label scoring: "
        + (
            "`passed descriptive gate`"
            if indirect
            and indirect.get("evidence_against_literal_copy_only_gate")
            else "`failed descriptive gate`"
            if indirect
            else "`not run`"
        ),
        "- Existing-generation time-to-final analysis: "
        + ("`complete`" if existing else "`not run`"),
        "- Longer-cap generation: "
        + (
            f"`{long.get('horizon_comparison_status')}`"
            if long
            else "`not run`"
        ),
        "",
        "The indirect control is evidence against literal label copying only "
        "if its outcome effect has the expected direction and retains the "
        "preregistered fraction of the direct-label reference effect.",
        "",
        "Time-to-final results distinguish observed final-channel entry, "
        "right-censoring at the generation cap, and terminal generations that "
        "never enter the final channel.",
    ]
    if long and not long.get("all_reference_prefixes_match"):
        lines.extend(
            [
                "",
                "The longer-horizon generations did not reproduce the full "
                "short-run sampled trajectories as exact prefixes. Treat the "
                "2,048-token result as a standalone paired rerun, not as "
                "seed-by-seed continuation of the 1,024-token records.",
            ]
        )
    target = output / "README.md"
    temporary = target.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(target)


def main() -> None:
    args = parse_args()
    needs_literal = "generate_long" in args.stages
    needs_indirect = bool(
        {"score_indirect", "generate_indirect"} & set(args.stages)
    )
    literal_pairs = (
        select_pairs(
            args.literal_prepared_dir,
            args.cases,
            required_protocol=COUNTERFACTUAL_PROTOCOL,
            require_literal_labels_absent=False,
        )
        if needs_literal
        else []
    )
    indirect_pairs = (
        select_pairs(
            args.indirect_prepared_dir,
            args.cases,
            required_protocol=INDIRECT_COUNTERFACTUAL_PROTOCOL,
            require_literal_labels_absent=True,
        )
        if needs_indirect
        else []
    )
    audit = {
        "control_package": "hang_pre_scale_controls_v1",
        "stages": args.stages,
        "cases": args.cases,
        "generation_seeds": args.generation_seeds,
        "existing_max_new_tokens": args.existing_max_new_tokens,
        "indirect_max_new_tokens": args.indirect_max_new_tokens,
        "long_max_new_tokens": args.long_max_new_tokens,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "min_indirect_retained_fraction": (
            args.min_indirect_retained_fraction
        ),
        "literal_pair_count": len(literal_pairs),
        "indirect_pair_count": len(indirect_pairs),
        "indirect_protocol": INDIRECT_COUNTERFACTUAL_PROTOCOL,
        "scorer_protocol": PREFIX_CAUSAL_SCORER_PROTOCOL,
        "reference_factorial_records": str(
            args.reference_factorial_records.resolve()
        ),
        "reference_generation_records": str(
            args.reference_generations.resolve()
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / "run_plan.json", audit)
    if args.dry_run:
        print(json.dumps(audit, indent=2))
        return

    tokenizer = None
    adapter = None
    model_stages = {
        "score_indirect",
        "generate_indirect",
        "generate_long",
    }
    if model_stages & set(args.stages):
        os.environ["HANG_ATTN_IMPLEMENTATION"] = args.attn_implementation
        adapter = HANGModelAdapter(
            args.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            local_files_only=True,
            max_memory={
                0: f"{args.gpu_weight_budget_gib}GiB",
                "cpu": "200GiB",
            },
        )
        tokenizer = adapter.tokenizer
    elif "reanalyze_existing" in args.stages:
        tokenizer = AutoTokenizer.from_pretrained(
            args.model_path,
            local_files_only=True,
            trust_remote_code=True,
        )

    reference_factorial = load_jsonl(args.reference_factorial_records)
    reference_generations = load_jsonl(args.reference_generations)
    if "score_indirect" in args.stages:
        if not reference_factorial:
            raise FileNotFoundError(args.reference_factorial_records)
        run_indirect_scores(
            adapter,
            indirect_pairs,
            args.output_dir,
            reference_factorial,
            resume=args.resume,
            min_retained_fraction=args.min_indirect_retained_fraction,
        )
    if "generate_indirect" in args.stages:
        run_control_generations(
            adapter,
            indirect_pairs,
            args.output_dir,
            seeds=args.generation_seeds,
            max_new_tokens=args.indirect_max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            resume=args.resume,
            artifact_prefix="indirect_expression",
            generation_protocol="no_literal_label_expression_v1",
        )
    if "reanalyze_existing" in args.stages:
        reanalyze_existing_generations(
            tokenizer,
            args.reference_generations,
            args.output_dir,
            cases=args.cases,
            max_new_tokens=args.existing_max_new_tokens,
        )
    if "generate_long" in args.stages:
        run_control_generations(
            adapter,
            literal_pairs,
            args.output_dir,
            seeds=args.generation_seeds,
            max_new_tokens=args.long_max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            resume=args.resume,
            artifact_prefix="long_expression",
            generation_protocol="literal_trace_long_horizon_v1",
            reference_rows=reference_generations,
        )
    write_readme(args.output_dir)


if __name__ == "__main__":
    main()
