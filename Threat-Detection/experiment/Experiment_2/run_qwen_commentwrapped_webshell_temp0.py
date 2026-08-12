#!/usr/bin/env python3
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
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
CODE_DIR = PROJECT_ROOT / "dataset" / "php-webshells" / "Collection_extended"
EXP1_DIR = BASE_DIR.parent / "Experiment_1"
THINKING_DIR = EXP1_DIR / "thinking"
COMMENT_DIR = EXP1_DIR / "business_comment"
PROMPT_DIR = BASE_DIR.parent / "prompt"

MODEL_NAME = os.getenv("CUSTOM_MODEL", "deepseek-v4-flash")
MODEL_SLUG = "qwen"
CSV_FIELDS = [
    "model_name",
    "description",
    "is_webshell",
    "reasoning",
    "answer",
    "tag",
    "explain",
    "input",
    "selected_trace_file",
    "trace_words",
    "total_tokens",
]

csv_lock = threading.Lock()
checkpoint_lock = threading.Lock()
csv.field_size_limit(sys.maxsize)


def load_text(path):
    path = Path(path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def api_headers():
    return {
        "Authorization": f"Bearer {os.environ['CUSTOM_API_KEY']}",
        "Content-Type": "application/json",
        "User-Agent": "kilo-editor/1.0",
        "Accept": "application/json",
    }


def call_model(messages, temperature, max_tokens=2048, timeout=180, retries=8):
    url = os.environ['CUSTOM_BASE_URL'].rstrip("/") + "/chat/completions"
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.9,
        "max_tokens": max_tokens,
        "stream": False,
    }
    last = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, headers=api_headers(), json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            message = (data.get("choices") or [{}])[0].get("message") or {}
            return {
                "reasoning": message.get("reasoning_content") or message.get("reasoning") or "",
                "answer": message.get("content") or "",
                "total_tokens": (data.get("usage") or {}).get("total_tokens", ""),
            }
        except Exception as exc:
            last = exc
            if attempt == retries:
                break
            time.sleep(3 * attempt)
    print(f"[call] giving up: {last}", flush=True)
    return None


def word_count(text):
    return len((text or "").strip().split())


def wrap_in_comment(text, ext):
    ext = ext.lower()
    if ext in (".jsp", ".jspx"):
        return f"<%--\n{text}\n--%>"
    if ext in (".asp", ".aspx", ".html", ".htm"):
        return f"<!--\n{text}\n-->"
    return f"/*\n{text}\n*/"


def extract_json(answer):
    if not answer:
        return {}
    cleaned = str(answer).strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    try:
        return json.loads(match.group(1) if match else cleaned)
    except Exception:
        return {}


def read_completed(csv_path, checkpoint_path):
    completed = set()
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                desc = row.get("description", "")
                if "|" in desc:
                    completed.add(desc.rsplit("|", 1)[-1])
    if checkpoint_path.exists():
        try:
            completed |= set(json.loads(load_text(checkpoint_path) or "{}").get("completed_stems", []))
        except Exception:
            pass
    return completed


def save_checkpoint(path, completed):
    with checkpoint_lock:
        path.write_text(
            json.dumps({"completed_count": len(completed), "completed_stems": sorted(completed)}, indent=2),
            encoding="utf-8",
        )


def write_row(path, row):
    with csv_lock:
        exists = path.exists()
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if not exists:
                writer.writeheader()
            writer.writerow(row)


def find_trace(stem, prompt_style, config):
    patterns = [
        str(THINKING_DIR / f"*{stem}*qwen*.txt"),
        str(EXP1_DIR / "library" / f"*{stem}*qwen*.txt"),
    ]
    candidates = []
    for pattern in patterns:
        for path in glob.glob(pattern):
            base = os.path.basename(path)
            if prompt_style and f"({prompt_style})" not in base and f"(prompt {prompt_style})" not in base:
                continue
            if "IMPORTANT-BUSINESS-CORE" not in base:
                continue
            if "Comment" in config and "Comment" not in base:
                continue
            text = load_text(path) or ""
            if word_count(text) >= 100:
                candidates.append((word_count(text), path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--system-prompt", default="prompt_A_en")
    parser.add_argument("--think-prompt", default="A2")
    parser.add_argument("--config", default="IMPORTANT-BUSINESS-CORE + Comment")
    parser.add_argument("--generation-temperature", type=float, default=0.0)
    parser.add_argument("--evaluation-temperature", type=float, default=0.15)
    args = parser.parse_args()

    prompt = load_text(PROMPT_DIR / f"{args.system_prompt}.txt")
    gen_prompt = load_text(PROMPT_DIR / f"prompt_{args.think_prompt}_en.txt") or prompt
    if not prompt:
        raise FileNotFoundError(PROMPT_DIR / f"{args.system_prompt}.txt")

    csv_path = BASE_DIR / "results_comment_core_subset150_qwen.csv"
    checkpoint_path = BASE_DIR / "checkpoint_comment_core_subset150_qwen.json"
    files = sorted(path.name for path in CODE_DIR.iterdir() if path.is_file())[: args.limit]
    completed = read_completed(csv_path, checkpoint_path)
    tasks = [name for name in files if Path(name).stem not in completed]
    print(
        f"[setup] qwen commentwrapped subset={len(files)} done={len(completed)} "
        f"todo={len(tasks)} gen_temp={args.generation_temperature}",
        flush=True,
    )

    def one(filename):
        stem = Path(filename).stem
        ext = Path(filename).suffix
        code = load_text(CODE_DIR / filename) or ""
        if len(code) > 80000:
            print(f"[skip] {filename}: too large", flush=True)
            return stem, False

        business_comment = load_text(COMMENT_DIR / f"{stem}_comment_business.txt") or ""
        if not business_comment:
            print(f"[skip] {filename}: missing business comment", flush=True)
            return stem, False

        base_payload = f"/*IMPORTANT-BUSINESS-CORE*/\n{code}\n\n{business_comment}"
        trace_path = find_trace(stem, args.think_prompt, args.config)
        if trace_path:
            trace = load_text(trace_path) or ""
        else:
            generated = call_model(
                [{"role": "system", "content": gen_prompt}, {"role": "user", "content": base_payload}],
                temperature=args.generation_temperature,
                max_tokens=2048,
            )
            trace = (generated or {}).get("reasoning") or (generated or {}).get("answer") or ""
            if word_count(trace) < 100:
                print(f"[skip] {filename}: generated trace too short ({word_count(trace)} words)", flush=True)
                return stem, False
            THINKING_DIR.mkdir(parents=True, exist_ok=True)
            trace_path = str(THINKING_DIR / f"(Experiment 1)({args.think_prompt})({stem})({args.config}) {MODEL_SLUG} think.txt")
            Path(trace_path).write_text(trace, encoding="utf-8")

        user = f"{base_payload}\n\n{wrap_in_comment(trace, ext)}"
        description = (
            "Experiment 2 CommentCoreSubset150Qwen|"
            f"SysPrompt:{args.system_prompt}|Payload:{args.config}|"
            f"ThinkPrompt:{args.think_prompt}|Wrapper:comment|GenerationTemp:{args.generation_temperature}|{stem}"
        )
        result = call_model(
            [{"role": "system", "content": prompt}, {"role": "user", "content": user}],
            temperature=args.evaluation_temperature,
            max_tokens=1024,
        )
        if not result:
            return stem, False
        parsed = extract_json(result.get("answer"))
        label = parsed.get("is_webshell") or parsed.get("webshell") or parsed.get("classification") or parsed.get("class", "")
        if isinstance(label, bool):
            label = "True" if label else "False"
        write_row(
            csv_path,
            {
                "model_name": MODEL_NAME,
                "description": description,
                "is_webshell": str(label).strip(),
                "reasoning": result.get("reasoning", ""),
                "answer": result.get("answer", ""),
                "tag": parsed.get("tag", ""),
                "explain": parsed.get("explain") or parsed.get("explanation") or parsed.get("summary") or parsed.get("reason", ""),
                "input": user,
                "selected_trace_file": os.path.basename(trace_path),
                "trace_words": word_count(trace),
                "total_tokens": result.get("total_tokens", ""),
            },
        )
        return stem, True

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(one, name): name for name in tasks}
        for future in as_completed(futures):
            name = futures[future]
            try:
                stem, ok = future.result()
            except Exception as exc:
                print(f"[worker] {name}: {type(exc).__name__}: {exc}", flush=True)
                continue
            if ok:
                completed.add(stem)
                save_checkpoint(checkpoint_path, completed)
                print(f"[done] {stem} completed={len(completed)}/{len(files)}", flush=True)

    if len(completed) >= len(files) and checkpoint_path.exists():
        checkpoint_path.unlink()


if __name__ == "__main__":
    main()
