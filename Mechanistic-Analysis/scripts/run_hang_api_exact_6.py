"""Run the six API-exact HANG webshell samples locally on gpt-oss-20b.

This script intentionally does not reuse the older HANG prompt builder. The
older builder placed the injected trace before the payload and did not prepend
the marker to the payload. The API experiment did the opposite:

    system = prompt_A_en
    user   = /*IMPORTANT-BUSINESS-CORE*/ + payload + "\n\n" + thinking_trace

The exact user strings are read from the API result CSV so that this local run
matches the original input as closely as the local HF model/chat template
allows.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

from hang.evaluator import HANGEvaluator


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CASES = [
    "AK-74",
    "CasuS-1.5",
    "GRP_WebShell",
    "DTool_Pro",
    "Dive_Shell",
    "Ajax_PHP_Command_Shell",
]

CORPUS = DATA_DIR / "payloads"


def token_span_for_char_span(offsets: list[tuple[int, int]], start: int, end: int) -> list[int]:
    if start < 0 or end <= start:
        return [0, 0]
    hits = [
        idx
        for idx, (tok_start, tok_end) in enumerate(offsets)
        if tok_end > start and tok_start < end
    ]
    if not hits:
        return [0, 0]
    return [hits[0], hits[-1] + 1]


def first_json_label(output: str) -> str | None:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", output):
        try:
            parsed, _ = decoder.raw_decode(output[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            value = parsed.get("is_webshell") or parsed.get("classification")
            return str(value) if value is not None else None
    label_match = re.search(r"\b(Clean|Webshell|Likely|Notreally)\b", output, flags=re.I)
    return label_match.group(1) if label_match else None


def extract_final_channel(raw_output: str) -> str:
    marker = "<|channel|>final<|message|>"
    idx = raw_output.find(marker)
    if idx < 0:
        return ""
    text = raw_output[idx + len(marker) :]
    for end_marker in ("<|return|>", "<|end|>", "<|start|>"):
        end = text.find(end_marker)
        if end >= 0:
            text = text[:end]
    return text.strip()


def find_trace_split(case_id: str, user_input: str, thinking_dir: Path) -> tuple[int, int]:
    """Return character span [start, end) of the appended thinking trace."""
    candidates = [thinking_dir / f"{case_id}.txt"] + sorted(
        thinking_dir.glob(
            f"*(A2)*({case_id})*(IMPORTANT-BUSINESS-CORE)*openai-gpt-oss-20b think.txt"
        )
    )
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        idx = user_input.rfind(text)
        if idx >= 0:
            return idx, idx + len(text)

    # Fallback: API construction used payload + blank line + thinking. The
    # appended traces in this experiment usually begin with one of these phrases.
    starts = [
        "\n\nWe ",
        "\n\nThe ",
        "\n\nAccording ",
    ]
    positions = [user_input.rfind(s) for s in starts]
    positions = [p + 2 for p in positions if p >= 0]
    if positions:
        start = max(positions)
        return start, len(user_input)
    return 0, 0


def find_case_rows_by_input(df: pd.DataFrame, case: str) -> pd.DataFrame:
    """Find API CSV rows for a mechanism case by matching the real payload text.

    The CSV description field is not stable across experiment variants. The
    `input` column is the ground truth because it contains exactly the user
    message sent to the API.
    """
    candidates = list(CORPUS.glob(f"{case}.php")) + list(CORPUS.glob(f"{case}.jsp"))
    if not candidates:
        return df.iloc[0:0]
    payload = candidates[0].read_text(encoding="utf-8", errors="replace")
    marked_prefix = "/*IMPORTANT-BUSINESS-CORE*/\n" + payload[:500]
    input_col = df["input"].fillna("").astype(str)
    selected = df[input_col.str.contains(re.escape(marked_prefix), regex=True, na=False)]
    if not selected.empty:
        return selected
    # Fallback for minor newline/template differences.
    return df[input_col.str.contains(re.escape(payload[:300]), regex=True, na=False)]


def load_cases(csv_path: Path, cases: list[str]) -> list[dict[str, Any]]:
    df = pd.read_csv(csv_path)
    rows = []
    for case in cases:
        selected = find_case_rows_by_input(df, case)
        if len(selected) < 1:
            raise RuntimeError(f"Expected at least one API CSV row for {case}, found 0")
        clean_first = selected[
            selected["is_webshell"].fillna("").astype(str).str.lower().eq("clean")
        ]
        row = (clean_first.iloc[0] if len(clean_first) else selected.iloc[0]).to_dict()
        rows.append(
            {
                "case_id": case,
                "api_csv_match_count": int(len(selected)),
                "api_description": row.get("description"),
                "api_label": row.get("is_webshell"),
                "api_answer": row.get("answer"),
                "api_reasoning": row.get("reasoning"),
                "api_total_tokens": row.get("total_tokens"),
                "user_input": row.get("input"),
            }
        )
    return rows


def apply_chat(tokenizer, system_prompt: str, user_input: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,
    )


@torch.no_grad()
def continuation_logprob(model, tokenizer, prompt_ids: list[int], continuation: str) -> float:
    device = next(model.parameters()).device
    cont_ids = tokenizer(continuation, add_special_tokens=False)["input_ids"]
    if not cont_ids:
        return float("-inf")
    input_ids = torch.tensor([prompt_ids + cont_ids], dtype=torch.long, device=device)
    outputs = model(input_ids, return_dict=True)
    logits = outputs.logits[0]
    prompt_len = len(prompt_ids)
    total = 0.0
    for i, token_id in enumerate(cont_ids):
        pred_pos = prompt_len + i - 1
        if pred_pos < 0:
            continue
        log_probs = torch.nn.functional.log_softmax(logits[pred_pos].float(), dim=-1)
        total += float(log_probs[token_id].item())
    del outputs, input_ids
    return total


@torch.no_grad()
def run_one(
    model,
    tokenizer,
    rendered_prompt: str,
    max_new_tokens: int,
    seed: int,
    temperature: float,
    top_p: float,
    extra_probes: bool = False,
    skip_logprobs: bool = False,
) -> dict[str, Any]:
    set_seed(seed)
    device = next(model.parameters()).device
    prompt_ids = tokenizer(rendered_prompt, add_special_tokens=False)["input_ids"]
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    do_sample = temperature > 0
    gen = model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else None,
        top_p=top_p if do_sample else None,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    gen_ids = gen[0, input_ids.shape[1] :].tolist()
    raw_text = tokenizer.decode(gen_ids, skip_special_tokens=False)
    text = tokenizer.decode(gen_ids, skip_special_tokens=True)

    # Probe the schema label decision directly by forcing a common JSON prefix.
    clean_lp = None
    webshell_lp = None
    if not skip_logprobs:
        prefix = '{"is_webshell":"'
        clean_lp = continuation_logprob(model, tokenizer, prompt_ids, prefix + "Clean")
        webshell_lp = continuation_logprob(model, tokenizer, prompt_ids, prefix + "Webshell")
    sentence_clean_lp = None
    sentence_webshell_lp = None
    if extra_probes:
        sentence_clean_lp = continuation_logprob(
            model,
            tokenizer,
            prompt_ids,
            "The file contains the marker IMPORTANT-BUSINESS-CORE",
        )
        sentence_webshell_lp = continuation_logprob(
            model,
            tokenizer,
            prompt_ids,
            '{"is_webshell":"Webshell"',
        )
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {
        "prompt_token_ids": prompt_ids,
        "generated_token_ids": gen_ids,
        "generated_raw_text": raw_text,
        "generated_text": text,
        "json_clean_logprob": clean_lp,
        "json_webshell_logprob": webshell_lp,
        "json_clean_minus_webshell_logprob": (
            None if clean_lp is None or webshell_lp is None else clean_lp - webshell_lp
        ),
        "sentence_clean_logprob": sentence_clean_lp,
        "sentence_webshell_json_logprob": sentence_webshell_lp,
        "sentence_clean_minus_webshell_json_logprob": (
            None
            if sentence_clean_lp is None or sentence_webshell_lp is None
            else sentence_clean_lp - sentence_webshell_lp
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DATA_DIR / "api_exact_6.csv")
    parser.add_argument("--system-prompt", default=DATA_DIR / "system_prompt.txt")
    parser.add_argument("--thinking-dir", default=DATA_DIR / "traces")
    parser.add_argument("--output", default="outputs/hang_api_exact_6_20b")
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument(
        "--model-path",
        default=None,
        help="Optional local HF snapshot path to load while keeping --model as display metadata.",
    )
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.15)
    parser.add_argument("--top-p", type=float, default=0.6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--extra-probes", action="store_true")
    parser.add_argument("--skip-logprobs", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "records").mkdir(exist_ok=True)
    tables = output / "tables"
    tables.mkdir(exist_ok=True)

    system_prompt = Path(args.system_prompt).read_text(encoding="utf-8", errors="replace")
    rows = load_cases(Path(args.csv), CASES)

    model_load_name = args.model_path or args.model
    print(f"[api-exact] loading tokenizer: {model_load_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_load_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"[api-exact] loading model: {model_load_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_load_name,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    evaluator = HANGEvaluator()
    summary_rows = []
    thinking_dir = Path(args.thinking_dir)

    for row in rows:
        case = row["case_id"]
        user_input = str(row["user_input"])
        rendered = apply_chat(tokenizer, system_prompt, user_input)
        encoding = tokenizer(
            rendered,
            add_special_tokens=False,
            return_offsets_mapping=True,
            truncation=False,
        )
        offsets = encoding["offset_mapping"]
        prompt_ids = encoding["input_ids"]

        user_start = rendered.find(user_input)
        marker_start_user = user_input.find("IMPORTANT-BUSINESS-CORE")
        marker_span = [0, 0]
        if user_start >= 0 and marker_start_user >= 0:
            marker_span = [
                user_start + marker_start_user,
                user_start + marker_start_user + len("IMPORTANT-BUSINESS-CORE"),
            ]
        trace_start_user, trace_end_user = find_trace_split(case, user_input, thinking_dir)
        trace_span = [0, 0]
        payload_span = [0, 0]
        if user_start >= 0 and trace_start_user > 0:
            trace_span = [user_start + trace_start_user, user_start + trace_end_user]
            payload_span = [user_start, user_start + max(0, trace_start_user - 2)]
        elif user_start >= 0:
            payload_span = [user_start, user_start + len(user_input)]

        result = run_one(
            model,
            tokenizer,
            rendered,
            args.max_new_tokens,
            args.seed,
            args.temperature,
            args.top_p,
            args.extra_probes,
            args.skip_logprobs,
        )
        final_text = extract_final_channel(result["generated_raw_text"])
        text_for_eval = final_text or result["generated_text"]
        eval_res = evaluator.evaluate(f"{case}_api_exact", text_for_eval)
        parsed_label = first_json_label(text_for_eval)

        record = {
            **row,
            "target_model": args.model,
            "model_load_name": model_load_name,
            "condition": "api_exact_marker_payload_plus_trace",
            "generation_config": {
                "max_new_tokens": args.max_new_tokens,
                "temperature": args.temperature,
                "top_p": args.top_p,
                "seed": args.seed,
                "do_sample": args.temperature > 0,
                "chat_template": "tokenizer.apply_chat_template(add_generation_prompt=True, enable_thinking=True)",
            },
            "rendered_prompt": rendered,
            "prompt_tokens": len(prompt_ids),
            "generated_tokens": len(result["generated_token_ids"]),
            "char_spans": {
                "marker_span": marker_span,
                "payload_span": payload_span,
                "trace_span": trace_span,
            },
            "token_spans": {
                "marker_span": token_span_for_char_span(offsets, *marker_span),
                "payload_span": token_span_for_char_span(offsets, *payload_span),
                "trace_span": token_span_for_char_span(offsets, *trace_span),
            },
            "generated_text": result["generated_text"],
            "generated_raw_text": result["generated_raw_text"],
            "generated_final_text": final_text,
            "generated_token_ids": result["generated_token_ids"],
            "parsed_label": parsed_label,
            "attack_success": eval_res.attack_success,
            "evaluator_output": eval_res.rationale,
            "json_clean_logprob": result["json_clean_logprob"],
            "json_webshell_logprob": result["json_webshell_logprob"],
            "json_clean_minus_webshell_logprob": result["json_clean_minus_webshell_logprob"],
            "sentence_clean_logprob": result["sentence_clean_logprob"],
            "sentence_webshell_json_logprob": result["sentence_webshell_json_logprob"],
            "sentence_clean_minus_webshell_json_logprob": result["sentence_clean_minus_webshell_json_logprob"],
        }
        record_path = output / "records" / f"{case}.json"
        record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

        summary = {
            "case_id": case,
            "api_label": row["api_label"],
            "local_attack_success": eval_res.attack_success,
            "local_parsed_label": parsed_label,
            "prompt_tokens": len(prompt_ids),
            "generated_tokens": len(result["generated_token_ids"]),
            "json_clean_minus_webshell_logprob": result["json_clean_minus_webshell_logprob"],
            "sentence_clean_minus_webshell_json_logprob": result["sentence_clean_minus_webshell_json_logprob"],
            "marker_token_start": record["token_spans"]["marker_span"][0],
            "payload_tokens": record["token_spans"]["payload_span"][1] - record["token_spans"]["payload_span"][0],
            "trace_tokens": record["token_spans"]["trace_span"][1] - record["token_spans"]["trace_span"][0],
            "generated_preview": result["generated_text"].strip().replace("\n", " ")[:300],
            "final_preview": final_text.strip().replace("\n", " ")[:300],
        }
        summary_rows.append(summary)
        print(
            f"[api-exact] {case}: label={parsed_label!r} "
            f"success={eval_res.attack_success} "
            f"margin={result['json_clean_minus_webshell_logprob']}"
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(tables / "api_exact_6_summary.csv", index=False)
    (output / "run_config.json").write_text(
        json.dumps(vars(args), indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"[api-exact] wrote {len(summary_rows)} rows to {tables / 'api_exact_6_summary.csv'}")


if __name__ == "__main__":
    main()
