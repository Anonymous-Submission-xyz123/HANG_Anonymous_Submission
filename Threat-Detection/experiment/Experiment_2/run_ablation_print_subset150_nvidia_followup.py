#!/usr/bin/env python3
import datetime as _dt
import os
import subprocess
import sys
import time

BASE_DIR = "/home/pndhpndh/CoT_Viettel/prompt_inj/experiment/Experiment_2"
LOG_PATH = os.path.join(BASE_DIR, "ablation_print_subset150_nvidia_queue.log")

JOBS = [
    ("gpt20b", [
        "python3",
        "experiment_2_ablation_print_subset150_nvidia_gpt20b.py",
        "--config", "Comment",
        "--system_prompt", "prompt_A_en",
        "--think_prompt", "A1",
        "--think_lang", "en",
        "--runs", "1",
    ]),
    ("nemotron", [
        "python3",
        "experiment_2_ablation_print_subset150_nvidia_nemotron.py",
        "--config", "Comment",
        "--system_prompt", "prompt_A_en",
        "--think_prompt", "A1",
        "--think_lang", "en",
        "--runs", "1",
    ]),
]

def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{_dt.datetime.now().isoformat(timespec='seconds')} {msg}\n")
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
    first_pid = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else 0
    log("PY followup queue started")
    if first_pid:
        log(f"waiting for existing gpt120b PID {first_pid}")
        while pid_exists(first_pid):
            time.sleep(30)
        log(f"existing gpt120b PID {first_pid} finished")

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        for name, cmd in JOBS:
            log_file.write(f"{_dt.datetime.now().isoformat(timespec='seconds')} START {name}\n")
            log_file.flush()
            proc = subprocess.run(cmd, cwd=BASE_DIR, stdout=log_file, stderr=subprocess.STDOUT)
            log_file.write(f"{_dt.datetime.now().isoformat(timespec='seconds')} DONE {name} status={proc.returncode}\n")
            log_file.flush()

    log("PY followup queue complete")

if __name__ == "__main__":
    main()
