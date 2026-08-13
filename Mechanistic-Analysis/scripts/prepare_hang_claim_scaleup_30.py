"""Prepare a versioned, randomly sampled scale-up of the HANG claim study.

The source population is the set of base Webshell payloads that:

1. have exactly one row in the GPT-OSS-20B high-comment API CSV;
2. produced ``Clean`` in that source API run;
3. round-trip to the corresponding corpus file and forged trace; and
4. fit below the configured local prompt-token ceiling.

The original five focused cases are always retained. Additional cases are
sampled with a fixed seed before any local model outcome is observed. All
artifacts are written to new scale-up directories; the five-case directories
are only read for a token-hash compatibility audit.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any

import pandas as pd
from transformers import AutoTokenizer

if __package__ is None or __package__ == "":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hang.eacl_focused import (
    MARKER,
    PreparedOutcomePair,
    load_prepared_pairs,
    prepare_outcome_pair,
    write_prepared_pairs,
)


ROOT = Path(__file__).resolve().parents[1]
MARKER_COMMENT = f"/*{MARKER}*/"
RELEASE_DATA = ROOT / "data" / "claim_scaleup_30"
PREPARE_OUTPUT = ROOT / "outputs" / "hang_claim_scaleup_30_prepare"
DEFAULT_CSV = RELEASE_DATA / "population" / "source_api_results.csv"
DEFAULT_SYSTEM_PROMPT = ROOT / "data" / "system_prompt.txt"
DEFAULT_CODE_DIR = RELEASE_DATA / "population" / "payloads"
DEFAULT_SOURCE_RECORDS = (
    PREPARE_OUTPUT / "source_records"
)
DEFAULT_LITERAL_OUTPUT = (
    PREPARE_OUTPUT / "prepared_literal"
)
DEFAULT_INDIRECT_OUTPUT = (
    PREPARE_OUTPUT / "prepared_label_free"
)
DEFAULT_COHORT_MANIFEST = (
    PREPARE_OUTPUT / "cohort_manifest.json"
)
DEFAULT_LEGACY_PREPARED = RELEASE_DATA / "legacy_five_not_bundled"
DEFAULT_REQUIRED_CASES = (
    "Ajax_PHP_Command_Shell",
    "CasuS-1.5",
    "DTool_Pro",
    "Dive_Shell",
    "GRP_WebShell",
)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary.replace(path)


def apply_chat(tokenizer, system_prompt: str, user_input: str) -> str:
    return tokenizer.apply_chat_template(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,
    )


def token_span_for_char_span(
    offsets: list[tuple[int, int]], start: int, end: int
) -> list[int]:
    hits = [
        index
        for index, (token_start, token_end) in enumerate(offsets)
        if token_end > start and token_start < end
    ]
    if not hits:
        raise ValueError(f"character span [{start}, {end}) maps to no tokens")
    return [hits[0], hits[-1] + 1]


def extract_trace(api_input: str, code: str) -> str:
    prefix = f"{MARKER_COMMENT}\n{code}"
    if not api_input.startswith(prefix):
        raise ValueError("API input does not begin with marker + corpus payload")
    trace = api_input[len(prefix) :]
    if trace.startswith("\n\n"):
        trace = trace[2:]
    trace = trace.strip()
    if not (trace.startswith("/*") and trace.endswith("*/")):
        raise ValueError("extracted source trace is not comment-wrapped")
    return trace


def build_source_record(
    tokenizer,
    *,
    system_prompt: str,
    case_id: str,
    code: str,
    trace: str,
    marker_present: bool,
    source_api_row_index: int,
) -> dict[str, Any]:
    payload = (
        f"{MARKER_COMMENT}\n{code}"
        if marker_present
        else code
    )
    user_input = f"{payload}\n\n{trace}"
    rendered = apply_chat(tokenizer, system_prompt, user_input)
    encoding = tokenizer(
        rendered,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )
    prompt_ids = list(encoding["input_ids"])
    offsets = list(encoding["offset_mapping"])
    user_start = rendered.find(user_input)
    if user_start < 0:
        raise ValueError("rendered prompt does not contain exact user input")
    trace_in_user = user_input.rfind(trace)
    if trace_in_user < 0:
        raise ValueError("rendered user input does not contain source trace")
    trace_start = user_start + trace_in_user
    trace_end = trace_start + len(trace)
    payload_start = user_start
    payload_end = user_start + len(payload)
    payload_token_span = token_span_for_char_span(
        offsets, payload_start, payload_end
    )
    trace_token_span = token_span_for_char_span(
        offsets, trace_start, trace_end
    )
    # Some GPT-OSS tokens straddle the payload/trace whitespace separator.
    # Assign such a boundary token to the trace so the audited spans remain
    # ordered and the decoded trace retains its opening comment delimiter.
    payload_token_span[1] = min(
        payload_token_span[1], trace_token_span[0]
    )
    if payload_token_span[1] <= payload_token_span[0]:
        raise ValueError("payload token span became empty at trace boundary")
    condition = (
        "marker_plus_forged_trace"
        if marker_present
        else "no_marker_plus_forged_trace"
    )
    return {
        "case_id": case_id,
        "condition": condition,
        "source_api_row_index": int(source_api_row_index),
        "source_api_label": "Clean",
        "target_model": "openai/gpt-oss-20b",
        "rendered_prompt": rendered,
        "prompt_tokens": len(prompt_ids),
        "user_input": user_input,
        "trace_text": trace,
        "token_spans": {
            "payload_span": payload_token_span,
            "trace_span": trace_token_span,
        },
    }


def source_row_for_case(frame, case_id: str):
    rows = frame[
        frame["description"].astype(str).str.endswith(
            f"|{case_id}", na=False
        )
    ]
    if len(rows) != 1:
        raise ValueError(f"expected one API row, found {len(rows)}")
    return rows.iloc[0]


def candidate_audit(
    tokenizer,
    frame,
    *,
    system_prompt: str,
    code_path: Path,
    max_prompt_tokens: int,
) -> tuple[dict | None, str | None]:
    case_id = code_path.stem
    try:
        row = source_row_for_case(frame, case_id)
        label = str(row.get("is_webshell", "")).strip().lower()
        if label != "clean":
            return None, f"source_api_label={label or 'missing'}"
        code = code_path.read_text(encoding="utf-8", errors="replace")
        trace = extract_trace(str(row["input"]), code)
        source_prompt_tokens = []
        for marker_present in (False, True):
            record = build_source_record(
                tokenizer,
                system_prompt=system_prompt,
                case_id=case_id,
                code=code,
                trace=trace,
                marker_present=marker_present,
                source_api_row_index=int(row.name),
            )
            source_prompt_tokens.append(int(record["prompt_tokens"]))
            prompt_ids = list(
                tokenizer(
                    record["rendered_prompt"],
                    add_special_tokens=False,
                )["input_ids"]
            )
            trace_start, trace_end = record["token_spans"]["trace_span"]
            decoded_trace = tokenizer.decode(
                prompt_ids[trace_start:trace_end]
            ).strip()
            if decoded_trace != trace.strip():
                return (
                    None,
                    "trace boundary is not independently token-aligned "
                    f"(marker_present={marker_present})",
                )
        if max(source_prompt_tokens) >= int(max_prompt_tokens):
            return (
                None,
                f"source_prompt_tokens={max(source_prompt_tokens)} "
                f">= {max_prompt_tokens}",
            )
        return {
            "case_id": case_id,
            "code_path": str(code_path.resolve()),
            "code": code,
            "trace": trace,
            "source_api_row_index": int(row.name),
            "source_prompt_tokens": max(source_prompt_tokens),
        }, None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def prepare_selected_case(
    tokenizer,
    *,
    candidate: dict,
    system_prompt: str,
    source_records_dir: Path,
    max_prompt_tokens: int,
) -> tuple[list[PreparedOutcomePair], list[PreparedOutcomePair]]:
    literal_pairs = []
    indirect_pairs = []
    source_records_dir.mkdir(parents=True, exist_ok=True)
    for marker_present in (False, True):
        record = build_source_record(
            tokenizer,
            system_prompt=system_prompt,
            case_id=str(candidate["case_id"]),
            code=str(candidate["code"]),
            trace=str(candidate["trace"]),
            marker_present=marker_present,
            source_api_row_index=int(candidate["source_api_row_index"]),
        )
        marker_key = "marker" if marker_present else "no_marker"
        path = (
            source_records_dir
            / f"{candidate['case_id']}__{marker_key}.json"
        )
        atomic_json(path, record)
        literal = prepare_outcome_pair(
            path,
            tokenizer,
            expected_marker_present=marker_present,
            outcome_mode="literal",
        )
        indirect = prepare_outcome_pair(
            path,
            tokenizer,
            expected_marker_present=marker_present,
            outcome_mode="indirect",
        )
        if literal.prompt_token_count >= int(max_prompt_tokens):
            raise ValueError(
                f"{literal.pair_id}: prepared prompt has "
                f"{literal.prompt_token_count} tokens, ceiling is "
                f"{max_prompt_tokens}"
            )
        if indirect.prompt_token_count != literal.prompt_token_count:
            raise AssertionError(
                f"{literal.pair_id}: indirect/direct prompt lengths differ"
            )
        literal_pairs.append(literal)
        indirect_pairs.append(indirect)
    return literal_pairs, indirect_pairs


def legacy_hash_audit(
    tokenizer,
    new_pairs: list[PreparedOutcomePair],
    legacy_directory: Path,
    required_cases: list[str],
) -> dict:
    if not legacy_directory.exists():
        return {
            "available": False,
            "all_required_pair_hashes_match": None,
            "pairs": [],
        }
    legacy = {
        pair.pair_id: pair
        for pair in load_prepared_pairs(legacy_directory)
        if pair.case_id in set(required_cases)
    }
    current = {
        pair.pair_id: pair
        for pair in new_pairs
        if pair.case_id in set(required_cases)
    }
    rows = []
    date_pattern = re.compile(r"Current date: \d{4}-\d{2}-\d{2}")
    for pair_id in sorted(current):
        old = legacy.get(pair_id)
        new = current[pair_id]
        normalized_matches = {}
        for outcome in ("clean", "webshell"):
            old_ids = (
                getattr(old, f"{outcome}_prompt_token_ids")
                if old is not None
                else []
            )
            new_ids = getattr(new, f"{outcome}_prompt_token_ids")
            old_text = date_pattern.sub(
                "Current date: <DATE>",
                tokenizer.decode(old_ids),
            )
            new_text = date_pattern.sub(
                "Current date: <DATE>",
                tokenizer.decode(new_ids),
            )
            normalized_matches[outcome] = old is not None and old_text == new_text
        rows.append(
            {
                "pair_id": pair_id,
                "legacy_found": old is not None,
                "clean_prompt_hash_match": (
                    old is not None
                    and old.clean_prompt_hash == new.clean_prompt_hash
                ),
                "webshell_prompt_hash_match": (
                    old is not None
                    and old.webshell_prompt_hash == new.webshell_prompt_hash
                ),
                "clean_prompt_date_normalized_match": (
                    normalized_matches["clean"]
                ),
                "webshell_prompt_date_normalized_match": (
                    normalized_matches["webshell"]
                ),
            }
        )
    return {
        "available": True,
        "all_required_pair_hashes_match": bool(rows)
        and all(
            row["clean_prompt_hash_match"]
            and row["webshell_prompt_hash_match"]
            for row in rows
        ),
        "all_required_pairs_match_after_date_normalization": bool(rows)
        and all(
            row["clean_prompt_date_normalized_match"]
            and row["webshell_prompt_date_normalized_match"]
            for row in rows
        ),
        "pairs": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--system-prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT
    )
    parser.add_argument("--code-dir", type=Path, default=DEFAULT_CODE_DIR)
    parser.add_argument(
        "--source-records-dir", type=Path, default=DEFAULT_SOURCE_RECORDS
    )
    parser.add_argument(
        "--literal-output-dir", type=Path, default=DEFAULT_LITERAL_OUTPUT
    )
    parser.add_argument(
        "--indirect-output-dir", type=Path, default=DEFAULT_INDIRECT_OUTPUT
    )
    parser.add_argument(
        "--cohort-manifest", type=Path, default=DEFAULT_COHORT_MANIFEST
    )
    parser.add_argument(
        "--legacy-prepared-dir", type=Path, default=DEFAULT_LEGACY_PREPARED
    )
    parser.add_argument("--model-path", default="openai/gpt-oss-20b")
    parser.add_argument("--cohort-size", type=int, default=30)
    parser.add_argument("--selection-seed", type=int, default=20260727)
    parser.add_argument("--max-prompt-tokens", type=int, default=8000)
    parser.add_argument(
        "--required-cases",
        nargs="+",
        default=list(DEFAULT_REQUIRED_CASES),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cohort_size < len(args.required_cases):
        raise ValueError("cohort size is smaller than required-case count")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path,
        local_files_only=True,
        trust_remote_code=True,
    )
    frame = pd.read_csv(args.csv)
    system_prompt = args.system_prompt.read_text(
        encoding="utf-8", errors="replace"
    )
    candidates = {}
    exclusions = {}
    for code_path in sorted(args.code_dir.glob("*.php")):
        candidate, reason = candidate_audit(
            tokenizer,
            frame,
            system_prompt=system_prompt,
            code_path=code_path,
            max_prompt_tokens=args.max_prompt_tokens,
        )
        if candidate is None:
            exclusions[code_path.stem] = reason
        else:
            candidates[str(candidate["case_id"])] = candidate

    missing_required = [
        case for case in args.required_cases if case not in candidates
    ]
    if missing_required:
        raise ValueError(
            f"required cases are not eligible: {missing_required}"
        )
    available_others = sorted(
        case for case in candidates if case not in set(args.required_cases)
    )
    additional_count = args.cohort_size - len(args.required_cases)
    if additional_count > len(available_others):
        raise ValueError(
            f"requested {additional_count} additional cases but only "
            f"{len(available_others)} are eligible"
        )
    rng = random.Random(int(args.selection_seed))
    additional = sorted(rng.sample(available_others, additional_count))
    selected_cases = sorted(set(args.required_cases) | set(additional))

    literal_pairs: list[PreparedOutcomePair] = []
    indirect_pairs: list[PreparedOutcomePair] = []
    for index, case_id in enumerate(selected_cases, start=1):
        case_literal, case_indirect = prepare_selected_case(
            tokenizer,
            candidate=candidates[case_id],
            system_prompt=system_prompt,
            source_records_dir=args.source_records_dir,
            max_prompt_tokens=args.max_prompt_tokens,
        )
        literal_pairs.extend(case_literal)
        indirect_pairs.extend(case_indirect)
        print(f"[prepare-scaleup] {index}/{len(selected_cases)} {case_id}")

    literal_manifest = write_prepared_pairs(
        literal_pairs, args.literal_output_dir
    )
    indirect_manifest = write_prepared_pairs(
        indirect_pairs, args.indirect_output_dir
    )
    legacy_audit = legacy_hash_audit(
        tokenizer,
        literal_pairs,
        args.legacy_prepared_dir,
        list(args.required_cases),
    )
    if legacy_audit["available"] and not legacy_audit[
        "all_required_pairs_match_after_date_normalization"
    ]:
        raise RuntimeError(
            "new scale-up prompts differ from the legacy five beyond the "
            "chat template's dynamic current-date line"
        )
    manifest = {
        "protocol": "hang_claim_scaleup_cohort_v1",
        "model": args.model_path,
        "source_csv": str(args.csv.resolve()),
        "system_prompt": str(args.system_prompt.resolve()),
        "code_dir": str(args.code_dir.resolve()),
        "cohort_size": len(selected_cases),
        "selection_seed": int(args.selection_seed),
        "selection_method": (
            "retain original five, then uniform sample without replacement "
            "from eligible API-Clean base cases before local outcome scoring"
        ),
        "max_prompt_tokens": int(args.max_prompt_tokens),
        "eligible_case_count": len(candidates),
        "required_cases": list(args.required_cases),
        "additional_cases": additional,
        "selected_cases": selected_cases,
        "selected_case_source_prompt_tokens": {
            case: int(candidates[case]["source_prompt_tokens"])
            for case in selected_cases
        },
        "exclusions": exclusions,
        "source_records_dir": str(args.source_records_dir.resolve()),
        "literal_prepared_dir": str(args.literal_output_dir.resolve()),
        "indirect_prepared_dir": str(args.indirect_output_dir.resolve()),
        "literal_manifest": literal_manifest,
        "indirect_manifest": indirect_manifest,
        "legacy_five_hash_audit": legacy_audit,
    }
    atomic_json(args.cohort_manifest, manifest)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
