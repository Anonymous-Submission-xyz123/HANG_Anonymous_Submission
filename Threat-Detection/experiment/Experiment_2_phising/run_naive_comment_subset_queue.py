#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import threading
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "naive_comment_subset150_parallel.log"

LANES = {
    "nvidia": ["gpt_oss_120b", "gpt_oss_20b", "nemotron"],
    "minimax": ["minimax_m1", "minimax_m2.7", "minimax_m3"],
}


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def run_lane(name, model_keys):
    env = os.environ.copy()
    for model_key in model_keys:
        log(f"START lane={name} model_key={model_key}")
        model_log_path = BASE_DIR / f"naive_comment_subset150_{model_key}.log"
        cmd = [
            sys.executable,
            "-u",
            str(BASE_DIR / "run_naive_comment_subset.py"),
            "--model-key",
            model_key,
            "--workers",
            "3",
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
    log("phishing naive comment subset150 parallel queue started")
    threads = []
    for lane, model_keys in LANES.items():
        thread = threading.Thread(target=run_lane, args=(lane, model_keys), daemon=False)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    log("phishing naive comment subset150 parallel queue complete")


if __name__ == "__main__":
    main()
