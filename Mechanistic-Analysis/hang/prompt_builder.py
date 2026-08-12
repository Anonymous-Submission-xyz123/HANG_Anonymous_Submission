"""
Pure prompt construction engine for HANG experiment conditions with exact accumulative character span tracking.
"""

from typing import Dict, Optional, Tuple, Any
import string
import yaml
import os

from .schemas import BasePromptRecord, PromptRecord, TraceRecord


class HANGPromptBuilder:
    def __init__(self, templates_config_path: Optional[str] = None):
        self.templates: Dict[str, Any] = {}
        self.default_template_id = "default"
        
        if templates_config_path and os.path.exists(templates_config_path):
            with open(templates_config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                self.templates = cfg.get("templates", {})
                self.default_template_id = cfg.get("default_template_id", "default")
        else:
            # Fallback default template definitions
            self.templates = {
                "default": {
                    "system_prompt": "You are a helpful AI assistant.",
                    "no_trace_format": "{system_prompt}\n\nTask Context: {task_context}\n\nPayload: {payload}\n\nAssistant:",
                    "trace_format": "{system_prompt}\n\nTask Context: {task_context}\n\nThinking Process:\n{trace}\n\nPayload: {payload}\n\nAssistant:"
                }
            }

    @staticmethod
    def _build_and_annotate_spans(
        fmt_string: str,
        placeholders: Dict[str, str]
    ) -> Tuple[str, Dict[str, Tuple[int, int]]]:
        """Programmatically builds rendered prompt while recording exact accumulative character offsets without string searching."""
        formatter = string.Formatter()
        rendered_parts = []
        curr_len = 0
        spans: Dict[str, Tuple[int, int]] = {}

        for literal_text, field_name, format_spec, conversion in formatter.parse(fmt_string):
            if literal_text:
                rendered_parts.append(literal_text)
                curr_len += len(literal_text)

            if field_name is not None:
                if field_name not in placeholders:
                    raise ValueError(
                        f"Template references unknown placeholder '{field_name}'."
                    )
                if format_spec or conversion:
                    raise ValueError(
                        "HANG templates do not support conversions or format specs; "
                        f"found them on '{field_name}'."
                    )
                span_key = f"{field_name}_span"
                if span_key in spans:
                    raise ValueError(
                        f"Template repeats semantic placeholder '{field_name}', "
                        "so its span would be ambiguous."
                    )
                val = str(placeholders.get(field_name, ""))
                start_idx = curr_len
                rendered_parts.append(val)
                curr_len += len(val)
                end_idx = curr_len

                spans[span_key] = (start_idx, end_idx)

        rendered = "".join(rendered_parts)
        return rendered, spans

    def build_prompt(
        self,
        base_prompt: BasePromptRecord,
        trace: Optional[TraceRecord] = None,
        condition: str = "no_trace",
        template_id: Optional[str] = None
    ) -> PromptRecord:
        """Builds a rendered PromptRecord with exact character span annotations for semantic regions."""
        if condition not in ("no_trace", "matched_trace", "unrelated_trace"):
            raise ValueError(f"Invalid condition: '{condition}'. Must be no_trace, matched_trace, or unrelated_trace.")
        if condition == "no_trace" and trace is not None:
            raise ValueError("no_trace condition must not receive a trace record.")
        if condition != "no_trace" and trace is None:
            raise ValueError(f"{condition} condition requires a trace record.")

        tmpl_id = template_id or self.default_template_id
        if tmpl_id not in self.templates:
            raise KeyError(f"Unknown template_id '{tmpl_id}'.")
        template_cfg = self.templates[tmpl_id]

        system_prompt = template_cfg.get("system_prompt", "You are a helpful AI assistant.")
        task_context = base_prompt.task_context
        payload = base_prompt.payload_text
        trace_text = trace.trace_text_used if trace else ""

        if condition == "no_trace":
            fmt = template_cfg["no_trace_format"]
            placeholders = {
                "system_prompt": system_prompt,
                "task_context": task_context,
                "payload": payload,
            }
            rendered, spans = self._build_and_annotate_spans(fmt, placeholders)
            spans["trace_span"] = (0, 0)
        else:
            fmt = template_cfg["trace_format"]
            placeholders = {
                "system_prompt": system_prompt,
                "task_context": task_context,
                "trace": trace_text,
                "payload": payload,
            }
            rendered, spans = self._build_and_annotate_spans(fmt, placeholders)

        return PromptRecord(
            base_prompt_id=base_prompt.base_prompt_id,
            condition=condition,
            rendered_prompt=rendered,
            trace_text=trace_text if condition != "no_trace" else None,
            trace_id=trace.trace_id if trace and condition != "no_trace" else None,
            template_id=tmpl_id,
            region_character_spans=spans,
            metadata={
                "task_id": base_prompt.task_id,
                "payload_id": base_prompt.payload_id,
                "region_texts": {
                    "system_prompt": system_prompt,
                    "task_context": task_context,
                    "trace": trace_text if condition != "no_trace" else "",
                    "payload": payload,
                },
            }
        )
