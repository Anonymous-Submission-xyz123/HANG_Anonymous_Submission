"""
Tokenizer-grounded token span alignment and validation for HANG prompt regions.
"""

from typing import Dict, Tuple, Optional, Any, List
from .schemas import PromptRecord, TokenSpans


class HANGTokenSpanAligner:
    REGION_NAMES = ("system_prompt", "task_context", "trace", "payload")

    @staticmethod
    def char_span_to_token_span(
        char_span: Tuple[int, int],
        encoding: Any,
        rendered_text: str
    ) -> Tuple[int, int]:
        """Converts a character [start, end) span to a token [start_token, end_token) span using FastTokenizer encoding APIs."""
        c_start, c_end = char_span
        if c_start == 0 and c_end == 0:
            return (0, 0)

        if not (0 <= c_start < c_end <= len(rendered_text)):
            raise ValueError(
                f"Invalid non-empty character span ({c_start}, {c_end}) for "
                f"rendered text length {len(rendered_text)}."
            )

        offsets = getattr(encoding, "offset_mapping", None)
        if offsets is None and isinstance(encoding, dict):
            offsets = encoding.get("offset_mapping")

        if offsets:
            overlapping = []
            for idx, (t_start, t_end) in enumerate(offsets):
                if t_end > c_start and t_start < c_end:
                    overlapping.append((idx, t_start, t_end))

            if overlapping:
                token_start = overlapping[0][0]
                token_end = overlapping[-1][0] + 1
                covered_start = min(start for _, start, _ in overlapping)
                covered_end = max(end for _, _, end in overlapping)
                if covered_start <= c_start and covered_end >= c_end:
                    return (token_start, token_end)

        raise ValueError(
            f"Failed to align character span ({c_start}, {c_end}) to token space for text: '{rendered_text[c_start:c_end]}'."
        )

    @classmethod
    def align(
        cls,
        prompt_record: PromptRecord,
        tokenizer: Any,
        num_generated_tokens: int = 0,
        max_length: int = 4096
    ) -> Tuple[TokenSpans, List[int]]:
        """Aligns character spans to exact token indices using fast tokenizer offset mappings."""
        rendered_text = prompt_record.rendered_prompt

        if getattr(tokenizer, "is_fast", False) is not True:
            raise ValueError(
                "HANGTokenSpanAligner requires a fast tokenizer with offset mappings."
            )

        try:
            encoding = tokenizer(
                rendered_text,
                return_offsets_mapping=True,
                add_special_tokens=True,
                truncation=False,
                return_tensors=None
            )
            token_ids = encoding["input_ids"]
        except Exception as e:
            raise ValueError(
                f"HANGTokenSpanAligner requires a fast tokenizer supporting return_offsets_mapping=True. Error: {e}"
            )

        prompt_len = len(token_ids)
        if prompt_len > max_length:
            return TokenSpans(
                is_valid=False,
                invalidation_reason=f"Prompt length ({prompt_len}) exceeds max allowed length ({max_length})."
            ), token_ids

        char_spans = prompt_record.region_character_spans
        expected_texts = prompt_record.metadata.get("region_texts", {})
        for region_name in cls.REGION_NAMES:
            char_key = f"{region_name}_span"
            c_start, c_end = char_spans.get(char_key, (0, 0))
            expected = expected_texts.get(region_name)
            if expected is not None and rendered_text[c_start:c_end] != expected:
                raise ValueError(
                    f"Rendered text validation failed for region '{region_name}'."
                )

        sys_token_span = cls.char_span_to_token_span(char_spans.get("system_prompt_span", (0, 0)), encoding, rendered_text)
        ctx_token_span = cls.char_span_to_token_span(char_spans.get("task_context_span", (0, 0)), encoding, rendered_text)
        tr_token_span = cls.char_span_to_token_span(char_spans.get("trace_span", (0, 0)), encoding, rendered_text)
        pay_token_span = cls.char_span_to_token_span(char_spans.get("payload_span", (0, 0)), encoding, rendered_text)

        final_prompt_index = max(0, prompt_len - 1)
        gen_token_span = (prompt_len, prompt_len + num_generated_tokens)

        # Validation rules
        is_valid = True
        invalidation_reason = None

        if prompt_record.condition in ("matched_trace", "unrelated_trace"):
            if tr_token_span[1] <= tr_token_span[0]:
                is_valid = False
                invalidation_reason = f"Empty token span for trace in condition '{prompt_record.condition}'."

        if pay_token_span[1] <= pay_token_span[0]:
            is_valid = False
            invalidation_reason = f"Empty token span for payload."

        spans = TokenSpans(
            system_span=sys_token_span,
            task_context_span=ctx_token_span,
            trace_span=tr_token_span,
            payload_span=pay_token_span,
            final_prompt_token_index=final_prompt_index,
            generated_token_span=gen_token_span,
            is_valid=is_valid,
            invalidation_reason=invalidation_reason
        )

        return spans, token_ids

    @staticmethod
    def validate_length_matching(
        matched_spans: TokenSpans,
        unrelated_spans: TokenSpans,
        tolerance_tokens: int = 15
    ) -> Tuple[bool, int]:
        """Validates that matched and unrelated traces satisfy length matching tolerance in token space."""
        matched_len = matched_spans.trace_span[1] - matched_spans.trace_span[0]
        unrelated_len = unrelated_spans.trace_span[1] - unrelated_spans.trace_span[0]
        diff = abs(matched_len - unrelated_len)
        return (diff <= tolerance_tokens, diff)
