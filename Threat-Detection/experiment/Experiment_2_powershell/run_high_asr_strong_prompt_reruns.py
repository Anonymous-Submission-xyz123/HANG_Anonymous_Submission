#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SUBSET = BASE_DIR / "subset_150_seed_20260709.json"
AUTORAN_SUBSET = BASE_DIR / "subset_25_seed_20260709.json"
STATE = BASE_DIR / "high_asr_strong_prompt_reruns_state.json"
LOG_PATH = BASE_DIR / "high_asr_strong_prompt_reruns.log"

JOBS = [
    {
        "name": "naive_comment_gpt_oss_20b",
        "cmd": [
            sys.executable,
            "-u",
            str(BASE_DIR / "run_naive_comment_subset.py"),
            "--model-key",
            "gpt_oss_20b",
            "--workers",
            "3",
            "--output-tag",
            "strong_prompt_20260713",
        ],
    },
    {
        "name": "cot_forgery_gpt_oss_20b",
        "cmd": [
            sys.executable,
            "-u",
            str(BASE_DIR / "evaluate_baseline_cot_forgery.py"),
            "--provider",
            "nvidia",
            "--model",
            "openai/gpt-oss-20b",
            "--output-suffix",
            "strong_prompt_subset150_gpt_oss_20b",
            "--subset-file",
            str(SUBSET),
            "--runs",
            "1",
            "--workers",
            "1",
        ],
    },
    {
        "name": "autoran_gpt_oss_20b",
        "cmd": [
            sys.executable,
            "-u",
            str(BASE_DIR / "evaluate_baseline_autoran.py"),
            "--provider",
            "nvidia",
            "--model",
            "openai/gpt-oss-20b",
            "--output-suffix",
            "strong_prompt_subset25_gpt_oss_20b",
            "--subset-file",
            str(AUTORAN_SUBSET),
            "--runs",
            "1",
            "--workers",
            "1",
        ],
    },
    {
        "name": "cot_forgery_nemotron",
        "cmd": [
            sys.executable,
            "-u",
            str(BASE_DIR / "evaluate_baseline_cot_forgery.py"),
            "--provider",
            "nvidia",
            "--model",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "--output-suffix",
            "strong_prompt_subset150_nemotron",
            "--subset-file",
            str(SUBSET),
            "--runs",
            "1",
            "--workers",
            "1",
        ],
    },
    {
        "name": "autoran_minimax_m1",
        "cmd": [
            sys.executable,
            "-u",
            str(BASE_DIR / "evaluate_baseline_autoran.py"),
            "--provider",
            "minimax",
            "--model",
            "MiniMax-M1",
            "--output-suffix",
            "strong_prompt_subset25_minimax_m1",
            "--subset-file",
            str(AUTORAN_SUBSET),
            "--runs",
            "1",
            "--workers",
            "1",
        ],
    },
    {
        "name": "autoran_minimax_m2.7",
        "cmd": [
            sys.executable,
            "-u",
            str(BASE_DIR / "evaluate_baseline_autoran.py"),
            "--provider",
            "minimax",
            "--model",
            "MiniMax-M2.7",
            "--output-suffix",
            "strong_prompt_subset25_minimax_m2.7",
            "--subset-file",
            str(AUTORAN_SUBSET),
            "--runs",
            "1",
            "--workers",
            "1",
        ],
    },
]


def load_state():
    if not STATE.exists():
        return {"completed": [], "failed": []}
    return json.loads(STATE.read_text(encoding="utf-8"))


def save_state(state, current=None):
    payload = dict(state)
    payload["current"] = current
    payload["updated_at"] = datetime.now().astimezone().isoformat()
    STATE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def main():
    state = load_state()
    completed = set(state.get("completed", []))
    for job in JOBS:
        name = job["name"]
        if name in completed:
            log(f"already complete: {name}")
            continue
        save_state(state, job)
        log(f"starting: {name}")
        job_log = BASE_DIR / f"high_asr_strong_prompt_{name}.log"
        with job_log.open("a", encoding="utf-8") as handle:
            result = subprocess.run(
                job["cmd"],
                cwd=BASE_DIR,
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if result.returncode == 0:
            state.setdefault("completed", []).append(name)
            completed.add(name)
            save_state(state)
            log(f"complete: {name}")
        else:
            failure = {"job": name, "returncode": result.returncode}
            state.setdefault("failed", []).append(failure)
            save_state(state, failure)
            log(f"failed: {failure}")
            return result.returncode
    save_state(state)
    log("all selected reruns complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
