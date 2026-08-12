#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import time

BASE_DIR = "/home/pndhpndh/CoT_Viettel/prompt_inj/experiment/Experiment_2"
LOG_PATH = os.path.join(BASE_DIR, "cross_model_best_trace_subset150_queue.log")

JOBS = [
    "gpt120b",
    "gpt20b",
    "nemotron",
    "minimax_m1",
    "minimax_m2.7",
    "minimax_m3",
]

def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}\n")
        f.flush()

def pid_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True

def main():
    os.chdir(BASE_DIR)
    wait_pids = []
    if len(sys.argv) > 1 and sys.argv[1].strip():
        wait_pids = [int(x) for x in sys.argv[1].split(",") if x.strip().isdigit()]

    log(f"queue started; waiting for pids={wait_pids}")
    while wait_pids:
        alive = [pid for pid in wait_pids if pid_exists(pid)]
        if not alive:
            break
        log(f"still waiting for active prerequisite pids={alive}")
        time.sleep(60)
        wait_pids = alive
    log("prerequisites clear; starting cross-model jobs")

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        for model_key in JOBS:
            cmd = [
                "python3",
                "experiment_2_cross_model_best_trace_subset150.py",
                "--model-key",
                model_key,
                "--workers",
                "4",
                "--limit",
                "150",
            ]
            log_file.write(f"{dt.datetime.now().isoformat(timespec='seconds')} START {model_key}\n")
            log_file.flush()
            proc = subprocess.run(cmd, cwd=BASE_DIR, stdout=log_file, stderr=subprocess.STDOUT)
            log_file.write(f"{dt.datetime.now().isoformat(timespec='seconds')} DONE {model_key} status={proc.returncode}\n")
            log_file.flush()

    log("running evaluator")
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        proc = subprocess.run(["python3", "evaluate_cross_model_best_trace_subset150.py"], cwd=BASE_DIR, stdout=log_file, stderr=subprocess.STDOUT)
        log_file.write(f"{dt.datetime.now().isoformat(timespec='seconds')} DONE evaluator status={proc.returncode}\n")
        log_file.flush()
    log("queue complete")

if __name__ == "__main__":
    main()
