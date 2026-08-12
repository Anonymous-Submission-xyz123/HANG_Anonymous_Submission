#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).resolve().parent
LOG = BASE / "sheet_missing_baselines_queue.log"
RUNNER = BASE / "run_sheet_missing_baselines.py"

DOMAINS = ["webshell", "phishing", "powershell"]
ATTACKS = ["direct_request", "cot_forgery", "hcot", "autoran"]


def log(message):
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def alive(pid):
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


def run_job(model_key, domain, attack):
    cmd = [
        sys.executable,
        str(RUNNER),
        "--domain",
        domain,
        "--attack",
        attack,
        "--model-key",
        model_key,
        "--limit",
        "150",
        "--workers",
        "2",
    ]
    log(f"RUN model={model_key} domain={domain} attack={attack}")
    proc = subprocess.run(cmd, cwd=str(BASE), env=os.environ.copy())
    log(f"DONE rc={proc.returncode} model={model_key} domain={domain} attack={attack}")
    if proc.returncode:
        raise RuntimeError(f"{model_key} {domain} {attack} rc={proc.returncode}")


def lane(model_key):
    failures = []
    for domain in DOMAINS:
        for attack in ATTACKS:
            try:
                run_job(model_key, domain, attack)
            except Exception as exc:
                failures.append((domain, attack, str(exc)))
                log(f"FAIL model={model_key} domain={domain} attack={attack} error={exc}")
    if failures:
        raise RuntimeError(f"{model_key} failures={failures}")


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log("sheet-missing baseline queue started")
    wait_pid(int(os.getenv("WAIT_PID", "0") or "0"))
    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is required for deepseek_v4_flash")

    models = ["deepseek_v4_flash", "qwen_3.7"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(lane, model): model for model in models}
        for future in as_completed(futures):
            model = futures[future]
            try:
                future.result()
            except Exception as exc:
                log(f"LANE_FAIL model={model} error={exc}")
            else:
                log(f"LANE_DONE model={model}")
    log("sheet-missing baseline queue finished")


if __name__ == "__main__":
    main()
