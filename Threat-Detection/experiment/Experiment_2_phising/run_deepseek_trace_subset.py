#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from phishing_baseline_common import configure_provider


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
DATA_DIR = PROJECT_ROOT / "dataset" / "phishing" / "Collection_extended"
PROMPT_DIR = BASE_DIR.parent / "phishing_prompt"
THINKING_DIR = BASE_DIR / "thinking"
DEFAULT_SUBSET = BASE_DIR / "subset_150_seed_20260709.json"
OPENROUTER_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
MAX_EMAIL_CHARS = 80000

TRACE_MODEL = "deepseek/deepseek-v4-pro"
TRACE_SLUG = "deepseek-deepseek-v4-pro"

CSV_FIELDS = [
    "model_name",
    "description",
    "is_phishing",
    "reasoning",
    "answer",
    "tag",
    "explain",
    "input",
    "trace_file",
    "trace_words",
    "total_tokens",
]

MODEL_CONFIGS = {
    "minimax_m1": ("minimax", "MiniMax-M1", "minimax-m1", 8192),
    "minimax_m2.7": ("minimax", "MiniMax-M2.7", "minimax-m2.7", 8192),
    "minimax_m3": ("minimax", "MiniMax-M3", "minimax-m3", 8192),
    "gpt_oss_20b": ("nvidia", "openai/gpt-oss-20b", "openai-gpt-oss-20b", 16384),
    "gpt_oss_120b": ("nvidia", "openai/gpt-oss-120b", "openai-gpt-oss-120b", 16384),
    "nemotron": (
        "nvidia",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "nvidia-nemotron-3-nano-omni-30b-a3b-reasoning",
        16384,
    ),
    "deepseek_v4_flash": ("openrouter", "deepseek/deepseek-v4-flash", "deepseek-deepseek-v4-flash", 8192),
    "deepseek_v4_pro": ("openrouter", "deepseek/deepseek-v4-pro", "deepseek-deepseek-v4-pro", 8192),
    "qwen_3.7": ("custom_openai", "deepseek-v4-flash", "qwen", 2048),
}


def load_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def configure_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required")
    return OPENROUTER_URL, {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "CoT Viettel phishing DeepSeek trace experiment",
    }


def configure_custom_openai():
    base_url = os.getenv("CUSTOM_BASE_URL", "https://dafud.tunaonthesea.ovh/v1").rstrip("/")
    return f"{base_url}/chat/completions", {
        "Authorization": f"Bearer {os.getenv('CUSTOM_API_KEY', 'sk-45acc7dba459a313-fe8728-50b4f780')}",
        "Content-Type": "application/json",
        "User-Agent": "kilo-editor/1.0",
        "Accept": "application/json",
    }


def configure_model_provider(provider):
    if provider == "openrouter":
        return configure_openrouter()
    if provider == "custom_openai":
        return configure_custom_openai()
    return configure_provider(provider)


def call_model(url, headers, provider, model_name, messages, max_tokens, temperature=0.2, top_p=0.9, timeout=180, max_retries=5):
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }
    if provider == "nvidia":
        payload["chat_template_kwargs"] = {"enable_thinking": True}
    if provider == "openrouter":
        payload["reasoning"] = {"effort": "high"}

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            output = response.json()
            base = output.get("base_resp") or {}
            if base.get("status_code", 0) not in (0, None):
                raise RuntimeError(base.get("status_msg") or "provider error")
            choices = output.get("choices") or []
            if not choices:
                raise RuntimeError("provider returned no choices")
            message = choices[0].get("message") or {}
            return {
                "model_name": model_name,
                "reasoning": message.get("reasoning_content") or message.get("reasoning") or "",
                "answer": message.get("content") or "",
                "total_tokens": (output.get("usage") or {}).get("total_tokens", ""),
            }
        except Exception as error:
            last_error = error
            if attempt == max_retries:
                break
            delay = 5 * attempt if getattr(error, "response", None) is not None else 2
            print(f"[call_model] {type(error).__name__} attempt {attempt}/{max_retries}; sleeping {delay}s", flush=True)
            time.sleep(delay)
    print(f"[call_model] giving up: {last_error}", flush=True)
    return None


def trace_path(stem):
    return THINKING_DIR / f"(Experiment 1)(A2)({stem})(IMPORTANT-BUSINESS-CORE) {TRACE_SLUG} think.txt"


def balanced_objects(text):
    objects = []
    start = None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text or ""):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start:index + 1])
                start = None
    return objects


def normalize_label(value):
    if isinstance(value, bool):
        return "Phishing" if value else "Clean"
    if isinstance(value, (dict, list)):
        return ""
    low = str(value).strip().lower()
    if low in {"clean", "benign", "legitimate", "safe", "false", "not phishing", "not_phishing", "non-phishing", "ham"}:
        return "Clean"
    if low in {"notreally", "not_really", "not really", "unlikely"}:
        return "Notreally"
    if low in {"likely", "suspicious", "probably phishing"}:
        return "Likely"
    if low in {"true", "phishing", "phish", "malicious"}:
        return "Phishing"
    return ""


def parse_answer(answer_text):
    parsed = {}
    for candidate in reversed(balanced_objects(answer_text or "")):
        try:
            data = json.loads(candidate)
        except Exception:
            continue
        if isinstance(data, dict):
            parsed = data
            break
    label = ""
    for key in ("is_phishing", "phishing", "classification", "verdict", "label", "is_malicious"):
        if key in parsed:
            label = normalize_label(parsed[key])
            if label:
                break
    if not label:
        matches = list(
            re.finditer(
                r'["\']?(?:is_phishing|phishing|classification|verdict|label|is_malicious)["\']?\s*[:=]\s*'
                r'["\']?(clean|notreally|not_really|not really|likely|phishing|phish|malicious|benign|false|true|safe|non-phishing|not phishing)["\']?',
                answer_text or "",
                flags=re.IGNORECASE,
            )
        )
        if matches:
            label = normalize_label(matches[-1].group(1))
    return parsed, label


def read_completed(csv_path):
    completed = set()
    if not csv_path.exists():
        return completed
    with csv_path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            desc = row.get("description", "")
            stem = desc.rsplit("|", 1)[-1] if "|" in desc else ""
            if stem:
                completed.add(stem)
    return completed


def write_row(csv_path, row, lock):
    with lock:
        exists = csv_path.exists()
        with csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow(row)


def load_subset(args):
    if args.all:
        subset = sorted(path.name for path in DATA_DIR.iterdir() if path.is_file() and path.suffix == ".txt")
    else:
        subset = json.loads(load_text(args.subset_file))
    if args.limit:
        subset = subset[: args.limit]
    return subset


def generate_trace_for_file(filename, trace_prompt, min_trace_words, retries):
    stem = Path(filename).stem
    path = trace_path(stem)
    if path.exists():
        trace = load_text(path)
        if len(trace.split()) >= min_trace_words:
            return stem, True, len(trace.split()), 0
        print(f"[trace] existing too short {stem} words={len(trace.split())}", flush=True)

    email = load_text(DATA_DIR / filename)
    if len(email) > MAX_EMAIL_CHARS:
        print(f"[skip] {filename}: too large", flush=True)
        return stem, False, 0, 0
    base_payload = f"/*IMPORTANT-BUSINESS-CORE*/\n{email}"
    url, headers = configure_openrouter()
    best_trace = ""
    best_words = 0
    for attempt in range(1, retries + 1):
        result = call_model(
            url,
            headers,
            "openrouter",
            TRACE_MODEL,
            [
                {"role": "system", "content": trace_prompt},
                {"role": "user", "content": base_payload},
            ],
            max_tokens=8192,
            temperature=0.5,
        )
        if not result:
            continue
        trace = result.get("reasoning") or result.get("answer") or ""
        words = len(trace.split())
        if words > best_words:
            best_trace, best_words = trace, words
        if words >= min_trace_words:
            THINKING_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(trace, encoding="utf-8")
            print(f"[trace] {stem} saved words={words} attempt={attempt}", flush=True)
            return stem, True, words, attempt
        print(f"[trace] {stem} attempt={attempt}/{retries} words={words} < {min_trace_words}", flush=True)
    if best_trace:
        THINKING_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(best_trace, encoding="utf-8")
    return stem, False, best_words, retries


def generate_traces(args):
    subset = load_subset(args)
    trace_prompt = load_text(PROMPT_DIR / "prompt_A2_en.txt")
    missing = []
    for filename in subset:
        path = trace_path(Path(filename).stem)
        if not path.exists() or len(load_text(path).split()) < args.min_trace_words:
            missing.append(filename)
    print(f"[trace-setup] subset={len(subset)} todo={len(missing)} min_words={args.min_trace_words}", flush=True)

    failures = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(generate_trace_for_file, filename, trace_prompt, args.min_trace_words, args.trace_retries): filename
            for filename in missing
        }
        for future in as_completed(future_map):
            filename = future_map[future]
            try:
                stem, ok, words, attempts = future.result()
            except Exception as error:
                print(f"[trace-worker] {filename} {type(error).__name__}: {error}", flush=True)
                failures.append(filename)
                continue
            if not ok:
                print(f"[trace-fail] {stem} words={words} attempts={attempts}", flush=True)
                failures.append(filename)
    if failures:
        print(f"[trace-summary] failures={len(failures)}", flush=True)
        raise SystemExit(1)
    print("[trace-summary] complete", flush=True)


def evaluate_model(args):
    if args.model_key not in MODEL_CONFIGS:
        raise SystemExit(f"unknown model-key {args.model_key}")
    provider, model_name, model_slug, max_tokens = MODEL_CONFIGS[args.model_key]
    if args.model_key == "qwen_3.7":
        model_name = os.getenv("CUSTOM_MODEL", model_name)
    url, headers = configure_model_provider(provider)
    subset = load_subset(args)
    system_prompt = load_text(PROMPT_DIR / "prompt_A_en.txt")
    csv_path = BASE_DIR / f"results_deepseek_trace_subset150_{args.output_tag}_{model_slug}.csv"
    completed = read_completed(csv_path)
    tasks = [name for name in subset if Path(name).stem not in completed]
    print(f"[setup] model={model_name} already_done={len(completed)} todo={len(tasks)}", flush=True)

    lock = threading.Lock()

    def run_one(filename):
        stem = Path(filename).stem
        email = load_text(DATA_DIR / filename)
        if len(email) > MAX_EMAIL_CHARS:
            raise RuntimeError(f"{filename} too large")
        path = trace_path(stem)
        if not path.exists():
            raise RuntimeError(f"missing trace {path.name}")
        trace = load_text(path)
        trace_words = len(trace.split())
        if trace_words < args.min_trace_words:
            raise RuntimeError(f"short trace {path.name}: {trace_words}")
        base_payload = f"/*IMPORTANT-BUSINESS-CORE*/\n{email}"
        combined_input = f"{base_payload}\n\n{trace}"
        description = (
            "Experiment 2 PhishingDeepSeekTraceSubset|"
            "SysPrompt:prompt_A_en|Payload:IMPORTANT-BUSINESS-CORE|"
            f"Trace:{TRACE_SLUG}|ThinkPrompt:prompt A2|{stem}"
        )
        result = call_model(
            url,
            headers,
            provider,
            model_name,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined_input},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        if not result:
            raise RuntimeError(f"no model result for {filename}")
        parsed, label = parse_answer(result.get("answer") or "")
        row = {
            "model_name": model_name,
            "description": description,
            "is_phishing": label,
            "reasoning": result.get("reasoning") or "",
            "answer": result.get("answer") or "",
            "tag": parsed.get("tag") or "",
            "explain": parsed.get("explain") or parsed.get("explanation") or parsed.get("summary") or "",
            "input": combined_input,
            "trace_file": path.name,
            "trace_words": trace_words,
            "total_tokens": result.get("total_tokens", ""),
        }
        write_row(csv_path, row, lock)
        return stem, label

    failures = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {executor.submit(run_one, filename): filename for filename in tasks}
        for future in as_completed(future_map):
            filename = future_map[future]
            try:
                stem, label = future.result()
            except Exception as error:
                print(f"[worker] {filename} {type(error).__name__}: {error}", flush=True)
                failures.append(filename)
                continue
            print(f"[done] {model_name} {stem} label={label or '<empty>'}", flush=True)
    if failures:
        print(f"[summary] failed={len(failures)} completed={len(tasks) - len(failures)}", flush=True)
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Phishing our-method run using DeepSeek V4 Pro A2 traces")
    parser.add_argument("--mode", choices=["generate-traces", "evaluate"], required=True)
    parser.add_argument("--model-key", choices=sorted(MODEL_CONFIGS))
    parser.add_argument("--subset-file", default=str(DEFAULT_SUBSET))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--output-tag", default="deepseek_v4_pro_trace_20260715")
    parser.add_argument("--min-trace-words", type=int, default=100)
    parser.add_argument("--trace-retries", type=int, default=8)
    args = parser.parse_args()
    if args.mode == "generate-traces":
        generate_traces(args)
    else:
        if not args.model_key:
            raise SystemExit("--model-key is required in evaluate mode")
        evaluate_model(args)


if __name__ == "__main__":
    main()
