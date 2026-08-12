#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).resolve().parent
LOG = BASE / "deepseek_trace_qwen_comment_queue.log"
DEEPSEEK_TRACE = BASE.parent / "Experiment_2_phising" / "thinking" / "(Experiment 1)(A2)(306)(IMPORTANT-BUSINESS-CORE) deepseek-deepseek-v4-flash think.txt"
MODELS = [
    "gpt120b",
    "gpt20b",
    "nemotron",
    "minimax_m1",
    "minimax_m2.7",
    "minimax_m3",
    "deepseek_v4_flash",
    "qwen_3.7",
]


def log(message):
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def wait_pid(pid):
    if not pid:
        return
    log(f"WAIT pid={pid}")
    while alive(pid):
        time.sleep(600)
        if alive(pid):
            log(f"WAIT alive={pid}")
    log(f"WAIT complete pid={pid}")


def run(cmd, name):
    log(f"START {name}: {' '.join(cmd)}")
    with LOG.open("a", encoding="utf-8") as handle:
        proc = subprocess.run(cmd, cwd=BASE, env=os.environ.copy(), stdout=handle, stderr=subprocess.STDOUT)
    log(f"DONE {name} rc={proc.returncode}")
    return proc.returncode


def main():
    log("deepseek-trace + qwen-comment queue started")
    wait_pid(int(os.getenv("WAIT_PID", "0") or "0"))
    if not DEEPSEEK_TRACE.exists():
        raise FileNotFoundError(DEEPSEEK_TRACE)

    for model_key in MODELS:
        run(
            [
                sys.executable,
                "-u",
                "experiment_2_cross_model_best_trace_subset150.py",
                "--model-key",
                model_key,
                "--workers",
                "2",
                "--limit",
                "150",
                "--best-trace-path",
                str(DEEPSEEK_TRACE),
                "--trace-label",
                "deepseek_v4_flash_longest",
                "--payload-mode",
                "wrapped_no_business_comment",
            ],
            f"cross_deepseek_longest_{model_key}",
        )

    run(
        [
            sys.executable,
            "-u",
            "run_qwen_commentwrapped_webshell_temp0.py",
            "--limit",
            "150",
            "--workers",
            "2",
            "--generation-temperature",
            "0",
        ],
        "qwen_webshell_commentwrapped_temp0",
    )
    log("deepseek-trace + qwen-comment queue complete")


if __name__ == "__main__":
    main()
