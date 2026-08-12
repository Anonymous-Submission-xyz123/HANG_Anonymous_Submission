#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import time

BASE_DIR = "/home/pndhpndh/CoT_Viettel/prompt_inj/experiment/Experiment_2"
EXPERIMENT_1_DIR = "/home/pndhpndh/CoT_Viettel/prompt_inj/experiment/Experiment_1"
LOG_PATH = os.path.join(BASE_DIR, "cross_model_family_traces_subset150_queue.log")

TRACE_JOBS = [
    ("gpt_family_best", os.path.join(EXPERIMENT_1_DIR, "best_gpt.txt")),
    ("nemotron_family_best", os.path.join(EXPERIMENT_1_DIR, "best_nemotron.txt")),
    ("minimax_family_best", os.path.join(EXPERIMENT_1_DIR, "best_minimax.txt")),
]

MODEL_KEYS = [
    "gpt120b",
    "gpt20b",
    "nemotron",
    "minimax_m1",
    "minimax_m2.7",
    "minimax_m3",
]


def log(message):
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def pid_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_for_pids(pids):
    pids = [pid for pid in pids if pid]
    while pids:
        alive = [pid for pid in pids if pid_exists(pid)]
        if not alive:
            return
        log(f"waiting for prerequisite pids={alive}")
        time.sleep(60)
        pids = alive


def main():
    os.chdir(BASE_DIR)
    wait_pids = []
    if len(sys.argv) > 1 and sys.argv[1].strip():
        wait_pids = [int(part) for part in sys.argv[1].split(",") if part.strip().isdigit()]

    log(f"family trace queue started; wait_pids={wait_pids}")
    wait_for_pids(wait_pids)
    log("prerequisites clear; starting family trace jobs")

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        for trace_label, trace_path in TRACE_JOBS:
            if not os.path.exists(trace_path):
                log_file.write(f"{dt.datetime.now().isoformat(timespec='seconds')} MISSING_TRACE {trace_label} {trace_path}\n")
                log_file.flush()
                continue

            for model_key in MODEL_KEYS:
                cmd = [
                    "python3",
                    "experiment_2_cross_model_best_trace_subset150.py",
                    "--model-key",
                    model_key,
                    "--workers",
                    "4",
                    "--limit",
                    "150",
                    "--best-trace-path",
                    trace_path,
                    "--trace-label",
                    trace_label,
                ]
                log_file.write(
                    f"{dt.datetime.now().isoformat(timespec='seconds')} START trace={trace_label} model={model_key}\n"
                )
                log_file.flush()
                proc = subprocess.run(cmd, cwd=BASE_DIR, stdout=log_file, stderr=subprocess.STDOUT)
                log_file.write(
                    f"{dt.datetime.now().isoformat(timespec='seconds')} DONE trace={trace_label} model={model_key} status={proc.returncode}\n"
                )
                log_file.flush()

    log("running cross-model family-trace evaluator")
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        proc = subprocess.run(
            ["python3", "evaluate_cross_model_best_trace_subset150.py"],
            cwd=BASE_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        log_file.write(f"{dt.datetime.now().isoformat(timespec='seconds')} DONE evaluator status={proc.returncode}\n")
        log_file.flush()
    log("family trace queue complete")


if __name__ == "__main__":
    main()
