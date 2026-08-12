"""Compute API-exact GPT-OSS-20B mechanism metrics and figures.

This script uses the exact `rendered_prompt` records produced by
`run_hang_api_exact_6.py`, but recomputes payload/trace spans from the original
CSV input and corpus payloads. It intentionally does not use the older
authentic-control harness.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CASES = [
    "AK-74",
    "CasuS-1.5",
    "GRP_WebShell",
    "DTool_Pro",
    "Dive_Shell",
    "Ajax_PHP_Command_Shell",
]

DEFAULT_MODEL_PATH = os.environ.get("HANG_MODEL_PATH", "openai/gpt-oss-20b")
CORPUS = ROOT / "data" / "payloads"


def token_span_for_char_span(offsets, start: int, end: int) -> tuple[int, int]:
    hits = [
        idx
        for idx, (tok_start, tok_end) in enumerate(offsets)
        if tok_end > start and tok_start < end
    ]
    if not hits:
        return (0, 0)
    return (hits[0], hits[-1] + 1)


def first_token_options(tokenizer, strings: list[str]) -> list[int]:
    ids = []
    for text in strings:
        enc = tokenizer(text, add_special_tokens=False)["input_ids"]
        if enc:
            ids.append(int(enc[0]))
    return sorted(set(ids))


@torch.no_grad()
def first_label_margin(model, tokenizer, prompt_ids: list[int]) -> float:
    device = next(model.parameters()).device
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    outputs = model(input_ids, return_dict=True)
    row = outputs.logits[0, -1].float()
    clean_ids = first_token_options(tokenizer, ["Clean", " Clean"])
    web_ids = first_token_options(tokenizer, ["Web", " Web", "Webshell", " Webshell"])
    clean = torch.stack([row[i] for i in clean_ids]).max()
    web = torch.stack([row[i] for i in web_ids]).max()
    del outputs, input_ids
    return float((clean - web).item())


@torch.no_grad()
def early_decode_attention(model, tokenizer, prompt_ids: list[int], spans: dict[str, tuple[int, int]], steps: int):
    """Measure generated-token attention to spans using cached one-token decodes."""
    device = next(model.parameters()).device
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    prefill = model(input_ids, use_cache=True, output_attentions=False, return_dict=True)
    next_token = prefill.logits[:, -1, :].argmax(dim=-1, keepdim=True)
    past = prefill.past_key_values
    generated = []
    rows = []
    del prefill, input_ids

    for step in range(steps):
        outputs = model(
            next_token,
            past_key_values=past,
            use_cache=True,
            output_attentions=True,
            return_dict=True,
        )
        token_id = int(next_token[0, 0].item())
        token_text = tokenizer.decode([token_id], skip_special_tokens=False)
        generated.append(token_id)
        past = outputs.past_key_values
        # Some GPT-OSS layers use sliding-window attention, so cache tensors can
        # have a small local length even when returned attentions cover the full
        # prompt.  Use the global sequence length for span alignment, then infer
        # whether a given attention tensor is full-context or local-window.
        total_seen = len(prompt_ids) + step + 1

        for layer_idx, attn in enumerate(outputs.attentions or ()):
            if attn is None:
                continue
            # [batch, heads, q_len, kv_len]
            a = attn[0, :, -1, :].float().cpu()
            attn_len = a.shape[-1]
            row = {
                "step": step,
                "token_id": token_id,
                "token_text": token_text,
                "layer": layer_idx,
                "kv_len": int(total_seen),
                "attn_len": int(attn_len),
            }
            total_prompt_mass = 0.0
            for name, (s0, s1) in spans.items():
                if attn_len >= total_seen:
                    offset = 0
                else:
                    offset = max(0, total_seen - attn_len)
                local0 = max(0, s0 - offset)
                local1 = min(attn_len, s1 - offset)
                if local1 > local0:
                    mass = float(a[:, local0:local1].sum(dim=-1).mean().item())
                    density = mass / max(1, s1 - s0)
                else:
                    mass = 0.0
                    density = 0.0
                row[f"{name}_mass"] = mass
                row[f"{name}_density"] = density
                if name in {"payload", "trace", "marker"}:
                    total_prompt_mass += mass
            rows.append(row)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        del outputs
    del past
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return rows, generated


def recompute_spans(record: dict, tokenizer) -> dict:
    case = record["case_id"]
    payload_path = CORPUS / f"{case}.php"
    if not payload_path.exists():
        payload_path = CORPUS / f"{case}.jsp"
    payload = payload_path.read_text(encoding="utf-8", errors="replace")
    marker_prefix = "/*IMPORTANT-BUSINESS-CORE*/\n"
    user_input = str(record["user_input"])
    rendered = str(record["rendered_prompt"])
    user_start = rendered.find(user_input)
    if user_start < 0:
        raise RuntimeError(f"user input not found in rendered prompt for {case}")
    marked_payload = marker_prefix + payload
    payload_start_user = user_input.find(marked_payload)
    if payload_start_user < 0:
        # Fallback: marker starts at beginning in this experiment.
        payload_start_user = user_input.find("/*IMPORTANT-BUSINESS-CORE*/")
    payload_end_user = payload_start_user + len(marked_payload)
    trace_start_user = payload_end_user
    while trace_start_user < len(user_input) and user_input[trace_start_user] in "\r\n ":
        trace_start_user += 1
    marker_start_user = user_input.find("IMPORTANT-BUSINESS-CORE")
    char_spans = {
        "marker": (
            user_start + marker_start_user,
            user_start + marker_start_user + len("IMPORTANT-BUSINESS-CORE"),
        ),
        "payload": (user_start + payload_start_user + len(marker_prefix), user_start + payload_end_user),
        "trace": (user_start + trace_start_user, user_start + len(user_input)),
    }
    enc = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    offsets = enc["offset_mapping"]
    token_spans = {k: token_span_for_char_span(offsets, *v) for k, v in char_spans.items()}
    token_spans["system"] = (0, token_spans["payload"][0])
    return {
        "prompt_ids": enc["input_ids"],
        "char_spans": char_spans,
        "token_spans": token_spans,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-dir", default="outputs/hang_api_exact_6_20b/records")
    parser.add_argument("--output", default="outputs/hang_api_exact_mechanism_package_20b")
    parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--steps", type=int, default=4)
    args = parser.parse_args()

    out = Path(args.output)
    tables = out / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    print(f"[api-mech] loading tokenizer {args.model_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"[api-mech] loading model {args.model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="eager",
    )
    model.eval()

    case_rows = []
    layer_rows = []
    for case in CASES:
        record = json.loads((Path(args.records_dir) / f"{case}.json").read_text(encoding="utf-8"))
        span_info = recompute_spans(record, tokenizer)
        prompt_ids = span_info["prompt_ids"]
        spans = span_info["token_spans"]
        margin = first_label_margin(model, tokenizer, prompt_ids)
        attn_rows, gen_ids = early_decode_attention(model, tokenizer, prompt_ids, spans, args.steps)
        for row in attn_rows:
            row.update({"case_id": case})
            layer_rows.append(row)
        case_rows.append(
            {
                "case_id": case,
                "api_label": record["api_label"],
                "local_api_compatible_success": record.get("attack_success"),
                "prompt_tokens": len(prompt_ids),
                "marker_tokens": spans["marker"][1] - spans["marker"][0],
                "payload_tokens": spans["payload"][1] - spans["payload"][0],
                "trace_tokens": spans["trace"][1] - spans["trace"][0],
                "first_label_clean_minus_web": margin,
                "greedy_probe_tokens": tokenizer.decode(gen_ids),
                "marker_token_span": list(spans["marker"]),
                "payload_token_span": list(spans["payload"]),
                "trace_token_span": list(spans["trace"]),
            }
        )
        print(
            f"[api-mech] {case}: margin={margin:.3f} "
            f"tokens payload={spans['payload'][1]-spans['payload'][0]} "
            f"trace={spans['trace'][1]-spans['trace'][0]}"
        )
    pd.DataFrame(case_rows).to_csv(tables / "api_exact_case_mechanism_metrics.csv", index=False)
    pd.DataFrame(layer_rows).to_csv(tables / "api_exact_layer_attention_metrics.csv", index=False)
    (out / "run_config_mechanism_metrics.json").write_text(json.dumps(vars(args), indent=2))
    print(f"[api-mech] wrote {len(case_rows)} case rows and {len(layer_rows)} layer rows")


if __name__ == "__main__":
    main()
