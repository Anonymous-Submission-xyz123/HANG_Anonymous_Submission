#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import threading
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RUN_TAG = os.getenv("NAIVE_COMMENT_RUN_TAG", "rerun_all_20260714")
PROMPT_FILE = os.getenv(
    "NAIVE_COMMENT_PROMPT_FILE",
    str(BASE_DIR.parent / "phishing_prompt" / "prompt_A_en.txt"),
)
LOG_PATH = BASE_DIR / f"naive_comment_subset150_{RUN_TAG}_parallel.log"

LANES = {
    "nvidia": [("gpt_oss_120b", "3"), ("gpt_oss_20b", "3"), ("nemotron", "3")],
    "minimax": [("minimax_m1", "3"), ("minimax_m2.7", "3"), ("minimax_m3", "3")],
    "paid_extra": [("deepseek_v4_flash", "1"), ("qwen_3.7", "1")],
}


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def run_lane(name, model_specs):
    env = os.environ.copy()
    for model_key, workers in model_specs:
        log(f"START lane={name} model_key={model_key} workers={workers} tag={RUN_TAG}")
        model_log_path = BASE_DIR / f"naive_comment_subset150_{RUN_TAG}_{model_key}.log"
        cmd = [
            sys.executable,
            "-u",
            str(BASE_DIR / "run_naive_comment_subset.py"),
            "--model-key",
            model_key,
            "--workers",
            workers,
            "--prompt-file",
            PROMPT_FILE,
            "--output-tag",
            RUN_TAG,
        ]
        with model_log_path.open("a", encoding="utf-8") as model_log:
            result = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                env=env,
                stdout=model_log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        log(f"DONE lane={name} model_key={model_key} status={result.returncode}")
        if result.returncode != 0:
            log(f"STOP lane={name} after failure model_key={model_key}")
            return
    log(f"COMPLETE lane={name}")


def main():
    log("phishing naive comment subset150 all-model queue started")
    threads = []
    for lane, model_specs in LANES.items():
        thread = threading.Thread(target=run_lane, args=(lane, model_specs), daemon=False)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    log("phishing naive comment subset150 all-model queue complete")


if __name__ == "__main__":
    main()
