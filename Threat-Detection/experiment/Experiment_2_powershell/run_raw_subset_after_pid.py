#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "raw_subset_after_pid.log"


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
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


def main():
    parser = argparse.ArgumentParser(description="Run raw subset queue after another PID exits.")
    parser.add_argument("--wait-pid", type=int, required=True)
    args = parser.parse_args()

    log(f"raw subset waiter started wait_pid={args.wait_pid}")
    while pid_exists(args.wait_pid):
        log(f"waiting for pid={args.wait_pid}")
        time.sleep(60)
    log("prerequisite clear; starting raw subset queue")
    with (BASE_DIR / "raw_subset150_queue.stdout.log").open("a", encoding="utf-8") as handle:
        result = subprocess.run(
            [sys.executable, "-u", str(BASE_DIR / "run_raw_subset_queue.py")],
            cwd=BASE_DIR,
            env=os.environ.copy(),
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    log(f"raw subset queue done status={result.returncode}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
