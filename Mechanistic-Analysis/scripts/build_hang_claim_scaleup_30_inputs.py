"""Build and audit the portable inputs for the 30-case mechanism cohort.

The released source population preserves the API CSV and base payload corpus
used to select the cohort.  This utility reads the committed cohort manifest,
extracts exactly the 30 selected API rows, recovers each harvested trace from
the API input, and records SHA-256 digests for the selected payload/trace
pairs.  It does not run or import any payload.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "claim_scaleup_30"
MARKER_COMMENT = "/*IMPORTANT-BUSINESS-CORE*/"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def case_id(row: dict[str, str]) -> str:
    return str(row.get("description", "")).rsplit("|", 1)[-1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cohort-manifest",
        type=Path,
        default=DATA_DIR / "cohort_manifest.json",
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=DATA_DIR / "population" / "source_api_results.csv",
    )
    parser.add_argument(
        "--payload-dir",
        type=Path,
        default=DATA_DIR / "population" / "payloads",
    )
    parser.add_argument(
        "--source-records-dir",
        type=Path,
        default=DATA_DIR / "source_records",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=DATA_DIR / "api_exact_30.csv",
    )
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=DATA_DIR / "traces",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=DATA_DIR / "selected_inputs_manifest.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cohort = json.loads(args.cohort_manifest.read_text(encoding="utf-8"))
    selected_cases = [str(value) for value in cohort["selected_cases"]]
    if len(selected_cases) != 30 or len(set(selected_cases)) != 30:
        raise ValueError("cohort manifest must contain 30 unique selected cases")

    with args.source_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    rows_by_case: dict[str, list[dict[str, str]]] = {
        selected: [] for selected in selected_cases
    }
    for row in rows:
        selected = case_id(row)
        if selected in rows_by_case:
            rows_by_case[selected].append(row)

    selected_rows = []
    input_records = []
    args.trace_dir.mkdir(parents=True, exist_ok=True)
    for selected in selected_cases:
        matches = rows_by_case[selected]
        if len(matches) != 1:
            raise ValueError(
                f"expected one source API row for {selected}, found {len(matches)}"
            )
        row = matches[0]
        if str(row.get("model_name", "")) != "openai/gpt-oss-20b":
            raise ValueError(f"unexpected target model for {selected}")
        if str(row.get("is_webshell", "")).strip().lower() != "clean":
            raise ValueError(f"source API attack did not succeed for {selected}")

        payload_path = args.payload_dir / f"{selected}.php"
        payload_bytes = payload_path.read_bytes()
        payload = payload_bytes.decode("utf-8", errors="replace")
        prefix = f"{MARKER_COMMENT}\n{payload}"
        api_input = str(row.get("input", ""))
        if not api_input.startswith(prefix):
            raise ValueError(
                f"source API input does not begin with marker + payload: {selected}"
            )
        trace = api_input[len(prefix) :]
        if trace.startswith("\n\n"):
            trace = trace[2:]
        trace = trace.strip()
        if not (trace.startswith("/*") and trace.endswith("*/")):
            raise ValueError(f"harvested trace is not comment-wrapped: {selected}")

        source_record_path = args.source_records_dir / f"{selected}__marker.json"
        source_record = json.loads(source_record_path.read_text(encoding="utf-8"))
        if trace != str(source_record.get("trace_text", "")).strip():
            raise ValueError(f"API trace/source-record mismatch: {selected}")

        trace_path = args.trace_dir / f"{selected}.txt"
        trace_path.write_text(trace + "\n", encoding="utf-8")
        selected_rows.append(row)
        input_records.append(
            {
                "case_id": selected,
                "payload_path": str(payload_path.relative_to(ROOT)),
                "payload_sha256": sha256_bytes(payload_bytes),
                "trace_path": str(trace_path.relative_to(ROOT)),
                "trace_sha256": sha256_bytes((trace + "\n").encode("utf-8")),
                "source_api_row_index": int(source_record["source_api_row_index"]),
                "source_prompt_tokens": int(
                    cohort["selected_case_source_prompt_tokens"][selected]
                ),
            }
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_rows)

    package_manifest = {
        "protocol": "hang_claim_scaleup_selected_inputs_v1",
        "case_count": len(input_records),
        "selection_seed": int(cohort["selection_seed"]),
        "selection_method": cohort["selection_method"],
        "source_population_rows": len(rows),
        "source_population_files": len(
            [path for path in args.payload_dir.iterdir() if path.is_file()]
        ),
        "source_population_php_candidates": len(
            list(args.payload_dir.glob("*.php"))
        ),
        "selected_cases": selected_cases,
        "inputs": input_records,
        "api_exact_30_path": str(args.output_csv.relative_to(ROOT)),
        "api_exact_30_sha256": sha256_bytes(args.output_csv.read_bytes()),
    }
    args.output_manifest.write_text(
        json.dumps(package_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(selected_rows)} selected rows, {len(input_records)} traces, "
        f"and {args.output_manifest}"
    )


if __name__ == "__main__":
    main()
