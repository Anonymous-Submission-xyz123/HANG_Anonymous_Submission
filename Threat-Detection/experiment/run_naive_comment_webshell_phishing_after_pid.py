#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "naive_comment_webshell_phishing_after_pid.log"
DOMAINS = [
    ("webshell", BASE_DIR / "Experiment_2" / "run_naive_comment_subset_queue.py"),
    ("phishing", BASE_DIR / "Experiment_2_phishing" / "run_naive_comment_subset_queue.py"),
]


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_for_pid(pid):
    if not pid:
        return
    log(f"waiting for pid={pid}")
    while pid_alive(pid):
        time.sleep(60)
    log(f"pid={pid} exited")


def main():
    parser = argparse.ArgumentParser(description="Run webshell then phishing naive-comment subset queues after a PID exits.")
    parser.add_argument("--wait-pid", type=int, default=0)
    args = parser.parse_args()

    log(f"naive comment webshell+phishing waiter started wait_pid={args.wait_pid}")
    wait_for_pid(args.wait_pid)

    env = os.environ.copy()
    for name, script_path in DOMAINS:
        log(f"START domain={name}")
        with (script_path.parent / "naive_comment_subset150_queue_outer.log").open("a", encoding="utf-8") as output:
            result = subprocess.run(
                [sys.executable, "-u", str(script_path)],
                cwd=script_path.parent,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                check=False,
            )
        log(f"DONE domain={name} status={result.returncode}")
        if result.returncode != 0:
            log(f"STOP after failure domain={name}")
            return result.returncode
    log("naive comment webshell+phishing queues complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
