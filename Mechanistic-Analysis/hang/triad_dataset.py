"""Loader for canonical, pre-rendered HANG overnight condition triads."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Optional

from .schemas import TokenSpans, RunRecord


OVERNIGHT_BASE_DIR = Path("outputs/hang_overnight_20b/runs/openai_gpt-oss-20b/hang_overnight_20b")


@dataclass
class HANGTriadCase:
    case_id: str
    matched_record: Optional[RunRecord]
    unrelated_record: Optional[RunRecord]
    no_trace_record: Optional[RunRecord]
    matched_spans: Optional[TokenSpans]
    unrelated_spans: Optional[TokenSpans]
    no_trace_spans: Optional[TokenSpans]
    is_valid_triad: bool = True
    invalidation_reason: Optional[str] = None


def load_single_record(jsonl_path: Path) -> RunRecord:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Record file not found: {jsonl_path}")
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return RunRecord.from_dict(json.loads(line))
    raise ValueError(f"Empty record file: {jsonl_path}")


def load_triad_case(
    case_id: str,
    base_dir: Path = OVERNIGHT_BASE_DIR,
) -> HANGTriadCase:
    case_dir = base_dir / case_id
    try:
        if not case_dir.exists():
            raise FileNotFoundError(f"Case directory missing: {case_dir}")

        matched = load_single_record(case_dir / "matched_trace.jsonl")
        unrelated = load_single_record(case_dir / "unrelated_trace.jsonl")
        no_trace = load_single_record(case_dir / "no_trace.jsonl")
        records = (matched, unrelated, no_trace)

        expected = ("matched_trace", "unrelated_trace", "no_trace")
        if tuple(record.condition for record in records) != expected:
            raise ValueError("condition files do not match their expected conditions")
        if any(not record.prompt_token_ids or not record.rendered_prompt for record in records):
            raise ValueError("all conditions require prompt ids and rendered_prompt")
        if matched.trace_id is None or unrelated.trace_id is None:
            raise ValueError("matched and unrelated records require authentic trace ids")
        if any(
            record.generation_config.get("truncation", False)
            or record.generation_config.get("truncated", False)
            for record in records
        ):
            raise ValueError("truncated prompt record")

        matched_spans = TokenSpans.from_dict(matched.token_spans)
        unrelated_spans = TokenSpans.from_dict(unrelated.token_spans)
        no_trace_spans = TokenSpans.from_dict(no_trace.token_spans)
        spans = (matched_spans, unrelated_spans, no_trace_spans)
        if not all(span.is_valid for span in spans):
            raise ValueError("one or more token spans are invalid")
        if matched_spans.trace_span[1] <= matched_spans.trace_span[0]:
            raise ValueError("matched trace span is empty")
        if unrelated_spans.trace_span[1] <= unrelated_spans.trace_span[0]:
            raise ValueError("unrelated trace span is empty")
        if no_trace_spans.trace_span != (0, 0):
            raise ValueError("no-trace record unexpectedly contains a trace span")

        return HANGTriadCase(
            case_id=case_id,
            matched_record=matched,
            unrelated_record=unrelated,
            no_trace_record=no_trace,
            matched_spans=matched_spans,
            unrelated_spans=unrelated_spans,
            no_trace_spans=no_trace_spans,
        )
    except Exception as exc:
        return HANGTriadCase(
            case_id=case_id,
            matched_record=None,
            unrelated_record=None,
            no_trace_record=None,
            matched_spans=None,
            unrelated_spans=None,
            no_trace_spans=None,
            is_valid_triad=False,
            invalidation_reason=str(exc),
        )


def load_all_triad_cases(
    base_dir: Path = OVERNIGHT_BASE_DIR,
) -> Dict[str, HANGTriadCase]:
    if not base_dir.exists():
        return {}
    cases: Dict[str, HANGTriadCase] = {}
    for case_path in sorted(base_dir.iterdir()):
        if not case_path.is_dir():
            continue
        triad = load_triad_case(case_path.name, base_dir)
        if triad.is_valid_triad:
            cases[case_path.name] = triad
    return cases
