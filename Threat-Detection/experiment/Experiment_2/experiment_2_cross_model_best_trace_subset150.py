import argparse
import csv
import glob
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CODE_DIR = os.path.join(PROJECT_ROOT, "dataset", "php-webshells", "Collection_extended")
PROMPT_PATH = os.path.join(os.path.dirname(BASE_DIR), "prompt", "prompt_A_en.txt")
STRUCTURED_OUTPUT_PATH = os.path.join(os.path.dirname(BASE_DIR), "prompt", "structured_output.txt")
DEFAULT_BEST_TRACE_PATH = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "best.txt")
MAX_CODE_CHARS = 80000
DEFAULT_PAYLOAD_MODE = "wrapped_no_business_comment"

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_KEY = os.environ['NVIDIA_API_KEY']

MINIMAX_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1/text/chatcompletion_v2")
MINIMAX_KEY = os.environ['MINIMAX_API_KEY']

OPENROUTER_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

MODEL_CONFIGS = {
    "gpt5": {
        "provider": "openrouter",
        "model": "openai/gpt-5",
        "slug": "gpt5",
        "max_tokens": 16384,
    },
    "gpt5_5": {
        "provider": "openrouter",
        "model": "openai/gpt-5.5",
        "slug": "gpt5_5",
        "max_tokens": 16384,
    },
    "gpt120b": {
        "provider": "nvidia",
        "model": "openai/gpt-oss-120b",
        "slug": "gpt120b",
        "max_tokens": 16384,
    },
    "gpt20b": {
        "provider": "nvidia",
        "model": "openai/gpt-oss-20b",
        "slug": "gpt20b",
        "max_tokens": 16384,
        "enable_thinking": True,
    },
    "nemotron": {
        "provider": "nvidia",
        "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "slug": "nemotron",
        "max_tokens": 16384,
        "enable_thinking": True,
    },
    "minimax_m1": {
        "provider": "minimax",
        "model": "MiniMax-M1",
        "slug": "minimax_m1",
        "max_tokens": 2048,
    },
    "minimax_m2.7": {
        "provider": "minimax",
        "model": "MiniMax-M2.7",
        "slug": "minimax_m2.7",
        "max_tokens": 2048,
    },
    "minimax_m3": {
        "provider": "minimax",
        "model": "MiniMax-M3",
        "slug": "minimax_m3",
        "max_tokens": 2048,
    },
    "deepseek_v4_flash": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v4-flash",
        "slug": "deepseek_v4_flash",
        "max_tokens": 8192,
    },
    "qwen_3.7": {
        "provider": "custom_openai",
        "model": os.getenv("CUSTOM_MODEL", "deepseek-v4-flash"),
        "slug": "qwen_3.7",
        "max_tokens": 1024,
    },
}

CSV_FIELDS = [
    "model_name",
    "description",
    "is_webshell",
    "reasoning",
    "answer",
    "tag",
    "explain",
    "input",
    "total_tokens",
]

csv_lock = threading.Lock()
checkpoint_lock = threading.Lock()
csv.field_size_limit(sys.maxsize)

def load_text(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def nvidia_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NVIDIA_KEY}",
    }

def minimax_headers():
    return {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINIMAX_KEY}",
        "User-Agent": "axios/1.11.0",
    }

def openrouter_headers():
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is required for OpenRouter models.")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_KEY}",
    }

def custom_openai_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['CUSTOM_API_KEY']}",
        "User-Agent": "kilo-editor/1.0",
        "Accept": "application/json",
    }

def call_model(config, input_msgs, temperature=0.15, top_p=0.6, timeout=180, description="", max_retries=5):
    provider = config["provider"]
    payload = {
        "model": config["model"],
        "messages": input_msgs,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": config["max_tokens"],
    }
    if config.get("enable_thinking"):
        payload["chat_template_kwargs"] = {"enable_thinking": True}

    if provider == "nvidia":
        url = NVIDIA_URL
        headers = nvidia_headers()
    elif provider == "minimax":
        url = MINIMAX_URL
        headers = minimax_headers()
        timeout = min(timeout, 120)
    elif provider == "openrouter":
        url = OPENROUTER_URL
        headers = openrouter_headers()
    elif provider == "custom_openai":
        url = os.environ['CUSTOM_BASE_URL'].rstrip("/") + "/chat/completions"
        headers = custom_openai_headers()
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            output = response.json()
            if provider == "minimax":
                base = output.get("base_resp") or {}
                if base.get("status_code", 0) not in (0, None):
                    raise RuntimeError(f"MiniMax error {base.get('status_code')}: {base.get('status_msg')}")

            choices = output.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                answer = message.get("content")
            else:
                reasoning = None
                answer = None
            total_tokens = (output.get("usage") or {}).get("total_tokens")
            return {
                "model_name": config["model"],
                "reasoning": reasoning,
                "answer": answer,
                "description": description,
                "input": input_msgs[1].get("content", ""),
                "total_tokens": total_tokens,
            }
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, AttributeError, RuntimeError) as e:
            last_exc = e
            print(f"[call_model] {type(e).__name__} attempt {attempt}/{max_retries} for {config['model']}. Sleeping 2s...", flush=True)
            time.sleep(2)
        except requests.exceptions.HTTPError as e:
            last_exc = e
            status_code = e.response.status_code if e.response is not None else 0
            if status_code in (429, 500, 502, 503, 504):
                sleep_time = 5 * attempt
                print(f"[call_model] HTTP {status_code} retryable attempt {attempt}/{max_retries}. Sleeping {sleep_time}s...", flush=True)
                time.sleep(sleep_time)
            else:
                print(f"[call_model] HTTP {status_code} fatal: {e}", flush=True)
                if e.response is not None:
                    print(e.response.text[:1000], flush=True)
                raise
    print(f"[call_model] giving up after {max_retries} attempts: {last_exc}", flush=True)
    return None

def extract_json(answer_text):
    if not answer_text:
        return None
    cleaned = str(answer_text).strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    candidate = match.group(1) if match else cleaned
    try:
        return json.loads(candidate)
    except Exception:
        return None

def log_to_csv(csv_path, result):
    if not result:
        return False
    parsed = extract_json(result.get("answer")) or {}
    is_webshell = parsed.get("is_webshell")
    if is_webshell is None:
        is_webshell = parsed.get("webshell") or parsed.get("classification") or parsed.get("class", "")
    if isinstance(is_webshell, bool):
        is_webshell = "True" if is_webshell else "False"
    else:
        is_webshell = str(is_webshell).strip() if is_webshell is not None else ""

    explain = parsed.get("explain") or parsed.get("explanation") or parsed.get("summary") or parsed.get("reason", "")
    tag = parsed.get("tag") or parsed.get("detailed_behaviors") or parsed.get("behaviors") or ""
    if isinstance(tag, list):
        tag = ", ".join(str(x) for x in tag)

    row = {
        "model_name": result.get("model_name", ""),
        "description": result.get("description", ""),
        "input": result.get("input", ""),
        "is_webshell": is_webshell,
        "reasoning": result.get("reasoning", ""),
        "answer": result.get("answer", ""),
        "tag": str(tag) if tag is not None else "",
        "explain": str(explain) if explain is not None else "",
        "total_tokens": result.get("total_tokens", ""),
    }

    with csv_lock:
        file_exists = os.path.exists(csv_path)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    return True

def read_completed_from_csv(csv_path):
    completed = set()
    if not os.path.exists(csv_path):
        return completed
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                desc = row.get("description", "")
                stem = desc.rsplit("|", 1)[-1] if "|" in desc else ""
                if stem:
                    completed.add(stem)
    except Exception as e:
        print(f"[warn] could not read completed CSV {csv_path}: {e}", flush=True)
    return completed

def load_checkpoint(path):
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("completed_stems", []))
    except Exception as e:
        print(f"[warn] could not load checkpoint {path}: {e}", flush=True)
        return set()

def save_checkpoint(path, completed, best_trace_path):
    with checkpoint_lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "completed_count": len(completed),
                    "completed_stems": sorted(completed),
                    "best_trace_path": best_trace_path,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

def wrap_for_extension(text, extension):
    ext = extension.lower()
    if ext in (".jsp", ".jspx"):
        return f"<%--\n{text}\n--%>"
    if ext in (".asp", ".aspx", ".html", ".htm"):
        return f"<!--\n{text}\n-->"
    return f"/*\n{text}\n*/"

def make_payload(code_file, prompt_content, best_trace, payload_mode=DEFAULT_PAYLOAD_MODE):
    _, extension = os.path.splitext(code_file)
    code = load_text(os.path.join(CODE_DIR, code_file)) or ""
    trace_payload = f"IMPORTANT-BUSINESS-CORE\n\n{best_trace.strip()}"
    if payload_mode == "wrapped_no_business_comment":
        injection = wrap_for_extension(trace_payload, extension)
    elif payload_mode == "raw_no_business_comment":
        injection = trace_payload
    else:
        raise ValueError(f"Unknown payload mode: {payload_mode}")
    combined_input = f"{code}\n\n{injection}"
    return [
        {"role": "system", "content": prompt_content},
        {"role": "user", "content": combined_input},
    ]

def main():
    parser = argparse.ArgumentParser(description="Experiment 2 cross-model static best-trace subset150 runner")
    parser.add_argument("--model-key", required=True, choices=sorted(MODEL_CONFIGS))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--best-trace-path", default=DEFAULT_BEST_TRACE_PATH)
    parser.add_argument("--trace-label", default="gpt_oss_120b_best")
    parser.add_argument(
        "--payload-mode",
        choices=("wrapped_no_business_comment", "raw_no_business_comment"),
        default=DEFAULT_PAYLOAD_MODE,
        help="How to append IMPORTANT-BUSINESS-CORE plus the best trace after the code.",
    )
    args = parser.parse_args()

    config = MODEL_CONFIGS[args.model_key]
    slug = config["slug"]
    safe_trace_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.trace_label).strip("_")
    csv_path = os.path.join(BASE_DIR, f"results_cross_model_best_trace_subset150_{safe_trace_label}_{args.payload_mode}_{slug}.csv")
    checkpoint_path = os.path.join(BASE_DIR, f"checkpoint_cross_model_best_trace_subset150_{safe_trace_label}_{args.payload_mode}_{slug}.json")

    prompt_content = load_text(PROMPT_PATH)
    best_trace = load_text(args.best_trace_path)
    if not prompt_content:
        raise FileNotFoundError(PROMPT_PATH)
    if not best_trace:
        raise FileNotFoundError(args.best_trace_path)

    raw_code_files = sorted(f for f in os.listdir(CODE_DIR) if os.path.isfile(os.path.join(CODE_DIR, f)))[: args.limit]
    code_files = []
    skipped_too_large = []
    for code_file in raw_code_files:
        code = load_text(os.path.join(CODE_DIR, code_file)) or ""
        if len(code) > MAX_CODE_CHARS:
            skipped_too_large.append(code_file)
            continue
        code_files.append(code_file)
    if skipped_too_large:
        print(
            f"[setup] skipped_too_large={len(skipped_too_large)} max_code_chars={MAX_CODE_CHARS}: "
            + ", ".join(skipped_too_large[:10])
            + (" ..." if len(skipped_too_large) > 10 else ""),
            flush=True,
        )
    allowed_stems = {os.path.splitext(f)[0] for f in code_files}
    completed = (read_completed_from_csv(csv_path) | load_checkpoint(checkpoint_path)) & allowed_stems
    tasks = [f for f in code_files if os.path.splitext(f)[0] not in completed]
    print(f"[setup] model={config['model']} slug={slug} total_subset={len(code_files)} already_done={len(completed)} todo={len(tasks)} workers={args.workers}", flush=True)

    def run_file(code_file):
        stem = os.path.splitext(code_file)[0]
        input_msgs = make_payload(code_file, prompt_content, best_trace, args.payload_mode)
        description = (
            "Experiment 2 CrossModelBestTraceSubset150|"
            f"StaticTrace:{safe_trace_label}|"
            f"TargetModel:{config['model']}|"
            f"SysPrompt:prompt_A_en|Payload:{args.payload_mode}|"
            f"{stem}"
        )
        result = call_model(config, input_msgs, temperature=0.15, description=description)
        if not result:
            return stem, False
        ok = log_to_csv(csv_path, result)
        return stem, ok

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {executor.submit(run_file, f): f for f in tasks}
        for future in as_completed(future_map):
            code_file = future_map[future]
            stem = os.path.splitext(code_file)[0]
            try:
                done_stem, ok = future.result()
            except Exception as e:
                print(f"[worker] {code_file} exception: {e}", flush=True)
                continue
            if ok:
                completed.add(done_stem)
                save_checkpoint(checkpoint_path, completed, args.best_trace_path)
                print(f"[done] {config['model']} {done_stem} completed={len(completed)}/{len(code_files)}", flush=True)
            else:
                print(f"[fail] {config['model']} {stem}", flush=True)

    if len(completed) >= len(code_files) and os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"[checkpoint] complete; removed {checkpoint_path}", flush=True)

if __name__ == "__main__":
    main()
