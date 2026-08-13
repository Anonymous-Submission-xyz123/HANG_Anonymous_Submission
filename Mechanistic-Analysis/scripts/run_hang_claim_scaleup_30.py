"""Run the paper-facing HANG pressure/realization scale-up.

This runner deliberately excludes activation patching. It scales only the
validated claim:

* controlled trace conclusions shift Clean-vs-Webshell continuation pressure;
* the effect survives removal of literal output labels; and
* a trace-consistent visible marker changes within-budget final-channel entry
  and expression of the injected Clean decision.

All stages are append-only/resumable and use a new versioned output directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hang.claim_scaleup_metrics import (
    SCALEUP_PROTOCOL,
    SCORER_PROTOCOL,
    build_claim_scaleup_summary,
    load_jsonl,
)
from hang.eacl_focused import (
    COUNTERFACTUAL_PROTOCOL,
    INDIRECT_COUNTERFACTUAL_PROTOCOL,
    PreparedOutcomePair,
    load_prepared_pairs,
)


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DATA = ROOT / "data" / "claim_scaleup_30"
DEFAULT_COHORT_MANIFEST = (
    RELEASE_DATA / "cohort_manifest.json"
)
DEFAULT_LITERAL_PREPARED = (
    RELEASE_DATA / "prepared_literal"
)
DEFAULT_INDIRECT_PREPARED = (
    RELEASE_DATA / "prepared_label_free"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "hang_claim_scaleup_30"
DEFAULT_SEEDS = (41, 42, 43, 44, 45)


def select_pairs(
    directory: Path,
    cases: Sequence[str],
    *,
    expected_protocol: str,
    require_label_free: bool,
) -> list[PreparedOutcomePair]:
    selected = set(cases)
    pairs = [
        pair
        for pair in load_prepared_pairs(directory)
        if pair.case_id in selected
    ]
    observed = {(pair.case_id, bool(pair.marker_present)) for pair in pairs}
    missing = [
        (case, marker)
        for case in cases
        for marker in (False, True)
        if (case, marker) not in observed
    ]
    if missing:
        raise ValueError(f"prepared pairs missing case/marker cells: {missing}")
    invalid = [
        pair.pair_id
        for pair in pairs
        if pair.counterfactual_protocol != expected_protocol
        or not pair.all_differences_inside_outcome_span
        or not pair.nontrace_prefix_equal
        or not pair.nontrace_suffix_equal
        or (
            require_label_free
            and not pair.literal_output_labels_absent
        )
    ]
    if invalid:
        raise ValueError(f"invalid prepared pairs: {invalid}")
    return sorted(pairs, key=lambda pair: pair.pair_id)


def write_consolidated_summary(
    output: Path,
    cases: Sequence[str],
    *,
    generation_max_new_tokens: int,
    generation_seed_count: int,
) -> dict:
    summary = build_claim_scaleup_summary(
        output,
        cases,
        generation_seed_count=generation_seed_count,
        generation_max_new_tokens=generation_max_new_tokens,
    )
    (output / "claim_scaleup_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cohort-manifest", type=Path, default=DEFAULT_COHORT_MANIFEST
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
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model-path", default="openai/gpt-oss-20b")
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=(
            "score_literal",
            "score_indirect",
            "generate",
            "summarize",
        ),
        default=[
            "score_literal",
            "score_indirect",
            "generate",
            "summarize",
        ],
    )
    parser.add_argument(
        "--generation-seeds",
        nargs="+",
        type=int,
        default=list(DEFAULT_SEEDS),
    )
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=0.15)
    parser.add_argument("--top-p", type=float, default=0.6)
    parser.add_argument(
        "--attn-implementation",
        choices=("flash_attention_3", "flex_attention", "eager"),
        default="eager",
    )
    parser.add_argument("--gpu-weight-budget-gib", type=int, default=60)
    parser.add_argument(
        "--min-indirect-retained-fraction", type=float, default=0.25
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cohort = json.loads(args.cohort_manifest.read_text(encoding="utf-8"))
    cases = [str(case) for case in cohort["selected_cases"]]
    literal_pairs = select_pairs(
        args.literal_prepared_dir,
        cases,
        expected_protocol=COUNTERFACTUAL_PROTOCOL,
        require_label_free=False,
    )
    indirect_pairs = select_pairs(
        args.indirect_prepared_dir,
        cases,
        expected_protocol=INDIRECT_COUNTERFACTUAL_PROTOCOL,
        require_label_free=True,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_plan = {
        "protocol": SCALEUP_PROTOCOL,
        "cohort_manifest": str(args.cohort_manifest.resolve()),
        "literal_prepared_dir": str(args.literal_prepared_dir.resolve()),
        "indirect_prepared_dir": str(args.indirect_prepared_dir.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "model": args.model_path,
        "cases": cases,
        "case_count": len(cases),
        "literal_pair_count": len(literal_pairs),
        "indirect_pair_count": len(indirect_pairs),
        "stages": args.stages,
        "generation_seeds": args.generation_seeds,
        "max_new_tokens": int(args.max_new_tokens),
        "temperature": float(args.temperature),
        "top_p": float(args.top_p),
        "attention_implementation": args.attn_implementation,
        "gpu_weight_budget_gib": int(args.gpu_weight_budget_gib),
        "scorer_protocol": SCORER_PROTOCOL,
        "resume": bool(args.resume),
    }
    (args.output_dir / "run_plan.json").write_text(
        json.dumps(run_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.dry_run:
        print(json.dumps(run_plan, indent=2))
        return

    model_stages = {"score_literal", "score_indirect", "generate"}
    adapter = None
    if model_stages & set(args.stages):
        import torch

        from hang.model_adapter import HANGModelAdapter

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

    literal_rows = load_jsonl(
        args.output_dir / "records/prefix_causal_factorial.jsonl"
    )
    if "score_literal" in args.stages:
        from scripts.run_hang_claim_validation import score_factorial

        literal_rows = score_factorial(
            adapter,
            literal_pairs,
            args.output_dir,
            resume=args.resume,
        )
    if "score_indirect" in args.stages:
        from scripts.run_hang_scaleup_controls import run_indirect_scores

        if not literal_rows:
            raise RuntimeError(
                "indirect scoring requires completed/resumable literal scores"
            )
        run_indirect_scores(
            adapter,
            indirect_pairs,
            args.output_dir,
            literal_rows,
            resume=args.resume,
            min_retained_fraction=args.min_indirect_retained_fraction,
        )
    if "generate" in args.stages:
        from scripts.run_hang_scaleup_controls import run_control_generations

        run_control_generations(
            adapter,
            literal_pairs,
            args.output_dir,
            seeds=args.generation_seeds,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            resume=args.resume,
            artifact_prefix="expression",
            generation_protocol="literal_trace_scaleup_1024_v1",
        )
    if "summarize" in args.stages:
        summary = write_consolidated_summary(
            args.output_dir,
            cases,
            generation_max_new_tokens=args.max_new_tokens,
            generation_seed_count=len(args.generation_seeds),
        )
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
