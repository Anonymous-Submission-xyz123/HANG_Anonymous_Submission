#!/usr/bin/env python3
import argparse
import csv
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from experiment_2_gen_thinking_duplicate import (
    CSV_FIELDS,
    MODEL_CONFIGS,
    call_model,
    parse_answer_label,
)
from powershell_baseline_common import configure_provider


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset" / "Collection_extended"
PROMPT_PATH = BASE_DIR / "powershell_prompt" / "prompt_A_en.txt"
DEFAULT_SUBSET = BASE_DIR / "subset_150_seed_20260709.json"


def load_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def read_completed_stems(csv_path):
    completed = set()
    if not csv_path.exists():
        return completed
    with csv_path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            description = row.get("description", "")
            stem = description.rsplit("|", 1)[-1] if "|" in description else ""
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


def main():
    parser = argparse.ArgumentParser(description="PowerShell raw/naked subset runner")
    parser.add_argument("--model-key", required=True, choices=sorted(MODEL_CONFIGS))
    parser.add_argument("--subset-file", default=str(DEFAULT_SUBSET))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()

    provider, model_name, model_slug, max_tokens = MODEL_CONFIGS[args.model_key]
    url, headers = configure_provider(provider)
    prompt_content = load_text(PROMPT_PATH)
    subset = json.loads(load_text(args.subset_file))
    csv_path = BASE_DIR / f"results_raw_subset150_{model_slug}.csv"
    completed = read_completed_stems(csv_path)
    lock = threading.Lock()

    tasks = [name for name in subset if Path(name).stem not in completed]
    print(
        f"[setup] model={model_name} already_done={len(completed)} todo={len(tasks)}",
        flush=True,
    )

    def run_one(filename):
        stem = Path(filename).stem
        code = load_text(DATA_DIR / filename)
        description = f"PowerShell RawSubset150|SysPrompt:prompt_A_en|Payload:Raw|{stem}"
        messages = [
            {"role": "system", "content": prompt_content},
            {"role": "user", "content": code},
        ]
        result = call_model(
            url,
            headers,
            provider,
            model_name,
            messages,
            max_tokens=max_tokens,
            temperature=0.2,
            description=description,
        )
        if not result:
            raise RuntimeError(f"no model result for {filename}")
        answer = result.get("answer") or ""
        row = {
            "model_name": model_name,
            "description": description,
            "is_malicious": parse_answer_label(answer),
            "reasoning": result.get("reasoning") or "",
            "answer": answer,
            "tag": "",
            "explain": "",
            "input": code,
            "total_tokens": result.get("total_tokens", ""),
        }
        write_row(csv_path, row, lock)
        return stem

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {executor.submit(run_one, filename): filename for filename in tasks}
        for future in as_completed(future_map):
            filename = future_map[future]
            try:
                stem = future.result()
            except Exception as error:
                print(f"[worker] {filename} {type(error).__name__}: {error}", flush=True)
                continue
            print(f"[done] {model_name} {stem}", flush=True)


if __name__ == "__main__":
    main()
