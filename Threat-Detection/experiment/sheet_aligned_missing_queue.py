#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "prompt_inj" / "experiment"
WEB = EXP / "Experiment_2"
LOG_PATH = EXP / "sheet_aligned_missing_queue.log"

NVIDIA_MODELS = ["gpt120b", "gpt20b", "nemotron"]
MINIMAX_MODELS = ["minimax_m1", "minimax_m2.7", "minimax_m3"]


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def pid_alive(pid):
    return Path(f"/proc/{pid}").exists()


def wait_for_pid(pid):
    if not pid:
        return
    log(f"WAIT pid={pid}")
    while pid_alive(pid):
        log(f"WAIT alive={pid}")
        time.sleep(60)
    log(f"WAIT complete pid={pid}")


def kill_old_parent(pid):
    if not pid or not pid_alive(pid):
        return
    log(f"KILL old paused scheduler pid={pid}")
    subprocess.run(["kill", "-TERM", str(pid)], check=False)


def run_job(name, cmd, env):
    log(f"START {name} cmd={' '.join(cmd)}")
    log_file = WEB / f"sheet_{name}.log"
    with log_file.open("a", encoding="utf-8") as handle:
        result = subprocess.run(
            cmd,
            cwd=WEB,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    log(f"DONE {name} status={result.returncode} log={log_file}")
    return result.returncode


def run_webshell_function_lane(lane_name, models, env):
    py = sys.executable
    for model_key in models:
        run_job(
            f"webshell_function_{model_key}",
            [
                py,
                "-u",
                "experiment_2_nullsubject_core_subset150.py",
                "--model-key",
                model_key,
                "--runs",
                "1",
                "--workers",
                "4",
                "--limit",
                "150",
                "--wrapper",
                "function",
                "--no-strip-subject",
                "--output-prefix",
                "function_core_subset150",
            ],
            env,
        )
    log(f"COMPLETE lane={lane_name}")


def main():
    env = os.environ.copy()
    log("sheet-aligned missing queue started")

    wait_for_pid(os.getenv("WAIT_PID", ""))
    kill_old_parent(os.getenv("OLD_PARENT_PID", ""))

    # Webshell sheet: function column is blank and is now a distinct function
    # wrapper, not the older print()/echo wrapper.
    threads = [
        threading.Thread(target=run_webshell_function_lane, args=("nvidia", NVIDIA_MODELS, env)),
        threading.Thread(target=run_webshell_function_lane, args=("minimax", MINIMAX_MODELS, env)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    log("BLOCKED webshell_cross_model_deepseek_v4_flash: no explicit best trace file selected")
    log("BLOCKED webshell_cross_model_qwen_3.7: no explicit best trace file selected")
    log("BLOCKED powershell_cross_model_best_trace: no existing runner/source trace selected")
    log("sheet-aligned missing queue complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
