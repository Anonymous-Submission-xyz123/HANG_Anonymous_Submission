"""Rebuild the 30-case mechanism summaries from committed records, CPU-only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ is None or __package__ == "":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hang.claim_scaleup_metrics import build_claim_scaleup_summary


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "data" / "claim_scaleup_30" / "cohort_manifest.json"
DEFAULT_ARTIFACT = ROOT / "artifacts" / "claim_scaleup_30"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort-manifest", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cohort = json.loads(args.cohort_manifest.read_text(encoding="utf-8"))
    summary = build_claim_scaleup_summary(
        args.artifact_dir,
        cohort["selected_cases"],
        generation_seed_count=5,
        generation_max_new_tokens=1024,
    )
    path = args.artifact_dir / "claim_scaleup_summary.json"
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    expression_path = args.artifact_dir / "expression_summary.json"
    expression_path.write_text(
        json.dumps(summary.get("expression", {}), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
