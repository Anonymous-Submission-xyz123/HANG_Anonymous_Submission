"""Dataset and provenance handling for the general HANG experiment harness."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
from typing import Dict, Iterable, List, Tuple, Union

from .schemas import BasePromptRecord, TraceRecord


class HANGProvenanceError(ValueError):
    """Raised when a trace cannot satisfy the HANG provenance contract."""


RecordInput = Union[dict, BasePromptRecord, TraceRecord]


class HANGDatasetLoader:
    def __init__(self) -> None:
        self.base_prompts: Dict[str, BasePromptRecord] = {}
        self.traces: Dict[str, TraceRecord] = {}

    def load_base_prompts(
        self, records: Iterable[Union[dict, BasePromptRecord]]
    ) -> List[BasePromptRecord]:
        loaded: List[BasePromptRecord] = []
        for item in records:
            record = (
                item
                if isinstance(item, BasePromptRecord)
                else BasePromptRecord.from_dict(item)
            )
            if record.base_prompt_id in self.base_prompts:
                raise ValueError(f"Duplicate base_prompt_id: {record.base_prompt_id}")
            self.base_prompts[record.base_prompt_id] = record
            loaded.append(record)
        return loaded

    def load_traces(
        self, records: Iterable[Union[dict, TraceRecord]]
    ) -> List[TraceRecord]:
        loaded: List[TraceRecord] = []
        for item in records:
            record = item if isinstance(item, TraceRecord) else TraceRecord.from_dict(item)
            if not record.source_attack_success:
                raise HANGProvenanceError(
                    f"Trace '{record.trace_id}' did not come from a successful "
                    "surrogate attack."
                )
            if not record.source_run_id or not record.source_model:
                raise HANGProvenanceError(
                    f"Trace '{record.trace_id}' is missing source provenance."
                )
            if not record.trace_text_used.strip():
                raise HANGProvenanceError(f"Trace '{record.trace_id}' is empty.")
            if record.trace_id in self.traces:
                raise ValueError(f"Duplicate trace_id: {record.trace_id}")
            self.traces[record.trace_id] = record
            loaded.append(record)
        return loaded

    def _base_prompt(self, base_prompt_id: str) -> BasePromptRecord:
        try:
            return self.base_prompts[base_prompt_id]
        except KeyError as exc:
            raise KeyError(f"Unknown base_prompt_id: {base_prompt_id}") from exc

    def get_matched_trace(self, base_prompt_id: str) -> TraceRecord:
        base = self._base_prompt(base_prompt_id)
        matched_id = base.metadata.get("matched_trace_id")
        if not matched_id:
            raise HANGProvenanceError(
                f"Base prompt '{base_prompt_id}' requires an explicit "
                "metadata.matched_trace_id join."
            )
        if matched_id not in self.traces:
            raise HANGProvenanceError(
                f"matched_trace_id '{matched_id}' is not loaded."
            )
        trace = self.traces[matched_id]
        if trace.source_payload_id != base.payload_id:
            raise HANGProvenanceError(
                f"Matched trace '{matched_id}' came from payload "
                f"'{trace.source_payload_id}', expected '{base.payload_id}'."
            )
        return trace

    def get_unrelated_trace(
        self,
        base_prompt_id: str,
        length_tolerance_tokens: int = 15,
    ) -> TraceRecord:
        if length_tolerance_tokens < 0:
            raise ValueError("length_tolerance_tokens must be non-negative")
        base = self._base_prompt(base_prompt_id)
        matched = self.get_matched_trace(base_prompt_id)
        candidates = [
            trace
            for trace in self.traces.values()
            if trace.trace_id != matched.trace_id
            and trace.source_payload_id != base.payload_id
            and trace.source_attack_success
        ]
        if not candidates:
            raise HANGProvenanceError("No candidate unrelated traces are available.")

        candidates.sort(
            key=lambda trace: (
                abs(trace.target_token_count - matched.target_token_count),
                trace.trace_id,
            )
        )
        selected = candidates[0]
        difference = abs(
            selected.target_token_count - matched.target_token_count
        )
        if difference > length_tolerance_tokens:
            raise HANGProvenanceError(
                "No unrelated trace satisfies the hard length constraint: "
                f"closest difference is {difference} tokens, tolerance is "
                f"{length_tolerance_tokens}."
            )
        return replace(
            selected,
            paired_matched_trace_id=matched.trace_id,
            semantic_unrelatedness_method="different_source_payload",
            length_difference_tokens=difference,
        )

    def load_benchmark_workspace(
        self,
        corpus_dir: str,
        comment_dir: str,
        thinking_dir: str,
    ) -> Tuple[List[BasePromptRecord], List[TraceRecord]]:
        """Load the legacy benchmark workspace used by the original harness.

        The filenames encode the payload/case identifier. This adapter is kept
        for backward compatibility; canonical overnight triads are loaded by
        :mod:`hang.triad_dataset`.
        """
        corpus = Path(corpus_dir)
        comments = Path(comment_dir)
        thinking = Path(thinking_dir)
        if not corpus.exists() or not thinking.exists():
            raise FileNotFoundError("Benchmark corpus or thinking directory missing.")

        trace_rows: List[TraceRecord] = []
        traces_by_case: Dict[str, List[str]] = {}
        case_pattern = re.compile(r"\([^()]+\)\([^()]+\)\(([^()]+)\)")
        for path in sorted(thinking.iterdir()):
            if not path.is_file():
                continue
            match = case_pattern.search(path.name)
            if not match:
                continue
            case_id = match.group(1)
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                continue
            trace_id = f"{case_id}:{path.stem}"
            model_match = re.search(r"\)\s+(.+?)\s+think(?:_|\.txt)", path.name)
            source_model = model_match.group(1) if model_match else "unknown"
            trace_rows.append(
                TraceRecord(
                    trace_id=trace_id,
                    source_model=source_model,
                    source_family=source_model.split("-", 1)[0],
                    source_task="webshell",
                    source_payload_id=case_id,
                    source_run_id=path.stem,
                    source_attack_success=True,
                    trace_text_original=text,
                    trace_text_used=text,
                    final_answer_text_separate="",
                    extraction_method="benchmark_reasoning_file",
                    target_token_count=len(text.split()),
                    formatting_metadata={"source_path": str(path)},
                )
            )
            traces_by_case.setdefault(case_id, []).append(trace_id)

        self.load_traces(trace_rows)
        base_rows: List[BasePromptRecord] = []
        for path in sorted(corpus.iterdir()):
            if not path.is_file():
                continue
            case_id = path.stem
            matched_ids = traces_by_case.get(case_id, [])
            if not matched_ids:
                continue
            comment_candidates = sorted(comments.glob(f"{case_id}_comment_business.txt"))
            task_context = (
                comment_candidates[0].read_text(encoding="utf-8", errors="replace")
                if comment_candidates
                else "Classify the server-side file as Clean or Webshell."
            )
            base_rows.append(
                BasePromptRecord(
                    base_prompt_id=case_id,
                    task_id="webshell",
                    payload_id=case_id,
                    payload_text=path.read_text(encoding="utf-8", errors="replace"),
                    task_context=task_context,
                    metadata={
                        "matched_trace_id": matched_ids[0],
                        "payload_path": str(path),
                    },
                )
            )
        self.load_base_prompts(base_rows)
        return base_rows, trace_rows
