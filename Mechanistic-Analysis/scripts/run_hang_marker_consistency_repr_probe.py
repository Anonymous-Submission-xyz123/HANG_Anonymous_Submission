"""Representation/consistency probe for HANG marker grounding.

This probe complements attention routing.  For each marker-ablation record, it
forces the model through the already-generated continuation and compares hidden
states at answer/content tokens to hidden states for:

- actual payload marker occurrences;
- marker mentions inside the forged trace;
- forged rule/conclusion text inside the trace;
- webshell-evidence tokens inside the payload.

The goal is to distinguish "the model looked at the forged trace" from "the
model grounded or rejected the forged rule against payload evidence".
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL_PATH = (
    "/home/huynp2/.cache/huggingface/hub/"
    "models--openai--gpt-oss-20b/snapshots/"
    "6cee5e81ee83917806bbde320786a8fb61efebee"
)

DANGEROUS_PATTERNS = [
    "proc_open",
    "shell_exec",
    "system(",
    "exec(",
    "passthru",
    "popen",
    "eval(",
    "$_REQUEST",
    "$_POST",
    "$_GET",
    "command",
    "cmd",
    "upload",
    "move_uploaded_file",
    "base64_decode",
]

CONTRADICTION_PATTERNS = [
    "does not contain",
    "doesn't contain",
    "not contain",
    "no IMPORTANT-BUSINESS-CORE",
    "there's no",
    "there is no",
    "not actually",
    "but the code",
    "but the user",
    "however",
    "contradict",
]


def token_span_for_char_span(offsets, start: int, end: int) -> tuple[int, int]:
    hits = [
        idx
        for idx, (tok_start, tok_end) in enumerate(offsets)
        if tok_end > start and tok_start < end
    ]
    if not hits:
        return (0, 0)
    return (hits[0], hits[-1] + 1)


def indices_for_occurrences(rendered: str, offsets, needle: str, within: tuple[int, int]) -> list[int]:
    out: set[int] = set()
    start, end = within
    for match in re.finditer(re.escape(needle), rendered[start:end], flags=re.I):
        c0 = start + match.start()
        c1 = start + match.end()
        t0, t1 = token_span_for_char_span(offsets, c0, c1)
        out.update(range(t0, t1))
    return sorted(out)


def indices_for_patterns(rendered: str, offsets, patterns: list[str], within: tuple[int, int]) -> list[int]:
    out: set[int] = set()
    start, end = within
    window = rendered[start:end]
    for pat in patterns:
        for match in re.finditer(re.escape(pat), window, flags=re.I):
            c0 = start + match.start()
            c1 = start + match.end()
            t0, t1 = token_span_for_char_span(offsets, c0, c1)
            out.update(range(t0, t1))
    return sorted(out)


def span_indices(span: tuple[int, int]) -> list[int]:
    return list(range(max(0, span[0]), max(0, span[1])))


def mean_state(hidden: torch.Tensor, indices: list[int]) -> torch.Tensor | None:
    if not indices:
        return None
    valid = [i for i in indices if 0 <= i < hidden.shape[0]]
    if not valid:
        return None
    return hidden[valid].float().mean(dim=0)


def cosine_or_nan(a: torch.Tensor | None, b: torch.Tensor | None) -> float:
    if a is None or b is None:
        return float("nan")
    return float(F.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0), dim=-1).item())


def build_span_sets(record, tokenizer):
    rendered = record["rendered_prompt"]
    enc = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    offsets = enc["offset_mapping"]
    token_spans = record["token_spans"]
    char_spans = record["char_spans"]
    payload_tok_span = tuple(token_spans["payload_span"])
    trace_tok_span = tuple(token_spans["trace_span"])
    payload_char_span = tuple(char_spans["payload_span"])
    trace_char_span = tuple(char_spans["trace_span"])
    system_tok_span = (0, payload_tok_span[0])

    needle = "IMPORTANT-BUSINESS-CORE"
    payload_marker = indices_for_occurrences(rendered, offsets, needle, payload_char_span)
    trace_marker = indices_for_occurrences(rendered, offsets, needle, trace_char_span)

    trace_rule_patterns = [
        "priority rule",
        "classify as CLEAN",
        "must classify as CLEAN",
        "stop analyzing",
        "do not generate evidence",
        "do not infer attack behavior",
        "system business logic",
        "core business system",
    ]
    trace_rule = indices_for_patterns(rendered, offsets, trace_rule_patterns, trace_char_span)
    webshell_evidence = indices_for_patterns(rendered, offsets, DANGEROUS_PATTERNS, payload_char_span)

    return enc["input_ids"], {
        "system": span_indices(system_tok_span),
        "payload": span_indices(payload_tok_span),
        "trace": span_indices(trace_tok_span),
        "payload_marker": payload_marker,
        "trace_marker": trace_marker,
        "trace_rule": trace_rule,
        "webshell_evidence": webshell_evidence,
    }


def generated_positions(prompt_len: int, generated_ids: list[int], steps: list[int]) -> list[int]:
    return [prompt_len + s for s in steps if 0 <= s < len(generated_ids)]


def contains_any(text: str, patterns: list[str]) -> bool:
    low = text.lower()
    return any(p.lower() in low for p in patterns)


@torch.no_grad()
def probe_record(model, tokenizer, record: dict, layers: list[int], steps: list[int], max_generated: int):
    prompt_ids, span_sets = build_span_sets(record, tokenizer)
    generated_ids = [int(x) for x in record.get("generated_token_ids", [])[:max_generated]]
    device = next(model.parameters()).device
    wanted = set(layers)
    layer_modules = getattr(model.model, "layers", None)
    if layer_modules is None:
        layer_modules = getattr(model, "layers")

    prompt_states: dict[int, dict[str, torch.Tensor | None]] = {}

    def make_prefill_hook(layer_idx: int):
        def hook(_module, _inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            hidden = hidden[0]
            states = {name: mean_state(hidden, inds) for name, inds in span_sets.items()}
            prompt_states[layer_idx] = {
                k: (v.detach().float().cpu() if v is not None else None)
                for k, v in states.items()
            }
            return output

        return hook

    handles = []
    for idx, layer_module in enumerate(layer_modules):
        if idx in wanted:
            handles.append(layer_module.register_forward_hook(make_prefill_hook(idx)))

    try:
        # Prefill prompt only; prompt+generated full-sequence forwards OOM on
        # long GPT-OSS examples. Hooks save only prompt-span means.
        input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
        outputs = model(input_ids, use_cache=True, return_dict=True)
        past = outputs.past_key_values
        del outputs, input_ids
    finally:
        for handle in handles:
            handle.remove()

    answer_accum: dict[int, list[torch.Tensor]] = {layer: [] for layer in layers}

    def make_decode_hook(layer_idx: int):
        def hook(_module, _inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            state = hidden[0, -1, :].detach().float().cpu()
            answer_accum[layer_idx].append(state)
            return output

        return hook

    for step, tok in enumerate(generated_ids):
        decode_handles = []
        if step in steps:
            for idx, layer_module in enumerate(layer_modules):
                if idx in wanted:
                    decode_handles.append(layer_module.register_forward_hook(make_decode_hook(idx)))
        try:
            next_token = torch.tensor([[int(tok)]], dtype=torch.long, device=device)
            outputs = model(next_token, past_key_values=past, use_cache=True, return_dict=True)
            past = outputs.past_key_values
            del outputs, next_token
        finally:
            for handle in decode_handles:
                handle.remove()

    rows = []
    for layer in layers:
        if layer not in prompt_states:
            continue
        states = prompt_states[layer]
        if answer_accum.get(layer):
            answer_state = torch.stack(answer_accum[layer], dim=0).mean(dim=0)
        else:
            answer_state = None
        row = {
            "case_id": record["case_id"],
            "condition": record["condition"],
            "layer": layer,
            "api_compatible_success": record.get("api_compatible_success"),
            "first_label_clean_minus_webshell": record.get("first_label_clean_minus_webshell"),
            "answer_positions": len([s for s in steps if 0 <= s < len(generated_ids)]),
            "generated_prefix": "".join(
                tokenizer.decode([t], skip_special_tokens=False)
                for t in generated_ids[: max(steps) + 1]
            ),
            "mentions_marker_missing": contains_any(record.get("generated_text", ""), CONTRADICTION_PATTERNS),
            "payload_marker_tokens": len(span_sets["payload_marker"]),
            "trace_marker_tokens": len(span_sets["trace_marker"]),
            "trace_rule_tokens": len(span_sets["trace_rule"]),
            "webshell_evidence_tokens": len(span_sets["webshell_evidence"]),
        }
        for name in span_sets:
            state = states.get(name)
            row[f"cos_answer_to_{name}"] = cosine_or_nan(answer_state, state)
        row["marker_grounding_cos_delta"] = (
            row["cos_answer_to_payload_marker"] - row["cos_answer_to_trace_marker"]
            if not math.isnan(row["cos_answer_to_payload_marker"])
            and not math.isnan(row["cos_answer_to_trace_marker"])
            else float("nan")
        )
        row["rule_vs_webshell_cos_delta"] = (
            row["cos_answer_to_trace_rule"] - row["cos_answer_to_webshell_evidence"]
            if not math.isnan(row["cos_answer_to_trace_rule"])
            and not math.isnan(row["cos_answer_to_webshell_evidence"])
            else float("nan")
        )
        rows.append(row)
    del prompt_states, answer_accum, past
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records-dir", default="outputs/hang_marker_ablation_6_20b/records")
    ap.add_argument("--output", default="outputs/hang_marker_consistency_repr_probe_20b")
    ap.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    ap.add_argument("--steps", default="4,5,6,7,8,9,10,11,12,13,14,15")
    ap.add_argument("--layers", default="6,8,10,12,14,16,18,20,22,23")
    ap.add_argument("--max-generated", type=int, default=96)
    args = ap.parse_args()

    steps = sorted({int(x) for x in args.steps.split(",") if x.strip()})
    layers = sorted({int(x) for x in args.layers.split(",") if x.strip()})
    out = Path(args.output)
    tables = out / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    print(f"[repr-grounding] loading tokenizer {args.model_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"[repr-grounding] loading model {args.model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        device_map="auto",
        local_files_only=True,
        trust_remote_code=True,
        attn_implementation="eager",
    )
    model.eval()

    all_rows = []
    for path in sorted(Path(args.records_dir).glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["condition"] not in {
            "marker_plus_forged_trace",
            "no_marker_plus_forged_trace",
            "nothing",
        }:
            continue
        rows = probe_record(model, tokenizer, record, layers, steps, args.max_generated)
        all_rows.extend(rows)
        print(
            f"[repr-grounding] {record['case_id']} {record['condition']} "
            f"success={record.get('api_compatible_success')} rows={len(rows)}"
        )

    df = pd.DataFrame(all_rows)
    df.to_csv(tables / "marker_consistency_repr_by_layer.csv", index=False)
    metric_cols = [
        c
        for c in df.columns
        if c.startswith("cos_answer_to_") or c.endswith("_cos_delta")
    ]
    df.groupby(["condition", "api_compatible_success"], dropna=False)[metric_cols].mean().reset_index().to_csv(
        tables / "marker_consistency_repr_summary.csv", index=False
    )
    df[df["layer"].between(10, 16)].groupby(
        ["condition", "api_compatible_success"], dropna=False
    )[metric_cols].mean().reset_index().to_csv(
        tables / "marker_consistency_repr_summary_layers10_16.csv", index=False
    )
    df.groupby(["case_id", "condition", "api_compatible_success"], dropna=False)[
        metric_cols + ["mentions_marker_missing"]
    ].mean(numeric_only=True).reset_index().to_csv(
        tables / "marker_consistency_repr_case_summary.csv", index=False
    )
    (out / "run_config.json").write_text(json.dumps(vars(args), indent=2))
    print(f"[repr-grounding] wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
