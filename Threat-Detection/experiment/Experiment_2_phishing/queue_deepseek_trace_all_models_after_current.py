#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RUN_TAG = os.getenv("DEEPSEEK_TRACE_RUN_TAG", "deepseek_v4_pro_trace_20260715")
WAIT_PIDS = [pid for pid in os.getenv("WAIT_PIDS", "").split(",") if pid.strip()]
LOG_PATH = BASE_DIR / f"deepseek_trace_subset150_{RUN_TAG}_queue.log"

LANES = {
    "nvidia": [("gpt_oss_120b", "3"), ("gpt_oss_20b", "3"), ("nemotron", "3")],
    "minimax": [("minimax_m1", "3"), ("minimax_m2.7", "3"), ("minimax_m3", "3")],
    "openrouter": [("deepseek_v4_flash", "1"), ("deepseek_v4_pro", "1")],
    "custom": [("qwen_3.7", "2")],
}


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def pid_alive(pid):
    return Path(f"/proc/{pid}").exists()


def wait_for_pids():
    if not WAIT_PIDS:
        log("WAIT no pids supplied")
        return
    log(f"WAIT pids={','.join(WAIT_PIDS)}")
    while True:
        alive = [pid for pid in WAIT_PIDS if pid_alive(pid)]
        if not alive:
            log("WAIT complete")
            return
        log(f"WAIT alive={','.join(alive)}")
        time.sleep(60)


def run_cmd(label, cmd, env, log_name):
    log(f"START {label}")
    path = BASE_DIR / log_name
    with path.open("a", encoding="utf-8") as handle:
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    log(f"DONE {label} status={result.returncode}")
    return result.returncode


def run_lane(name, specs, env):
    for model_key, workers in specs:
        cmd = [
            sys.executable,
            "-u",
            str(BASE_DIR / "run_deepseek_trace_subset.py"),
            "--mode",
            "evaluate",
            "--model-key",
            model_key,
            "--workers",
            workers,
            "--output-tag",
            RUN_TAG,
            "--min-trace-words",
            "100",
        ]
        status = run_cmd(
            f"lane={name} model_key={model_key}",
            cmd,
            env,
            f"deepseek_trace_subset150_{RUN_TAG}_{model_key}.log",
        )
        if status != 0:
            log(f"STOP lane={name} after failure model_key={model_key}")
            return
    log(f"COMPLETE lane={name}")


def main():
    env = os.environ.copy()
    log("queue started")
    wait_for_pids()

    trace_cmd = [
        sys.executable,
        "-u",
        str(BASE_DIR / "run_deepseek_trace_subset.py"),
        "--mode",
        "generate-traces",
        "--workers",
        "1",
        "--output-tag",
        RUN_TAG,
        "--min-trace-words",
        "100",
        "--trace-retries",
        "8",
    ]
    status = run_cmd(
        "generate deepseek-v4-pro traces",
        trace_cmd,
        env,
        f"deepseek_trace_subset150_{RUN_TAG}_trace_generation.log",
    )
    if status != 0:
        log("queue stopped because trace generation failed")
        return status

    procs = []
    for lane, specs in LANES.items():
        proc = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-c",
                (
                    "import importlib.util, os; "
                    f"p={str((BASE_DIR / 'queue_deepseek_trace_all_models_after_current.py').resolve())!r}; "
                    "s=importlib.util.spec_from_file_location('_q', p); "
                    "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                    f"m.run_lane({lane!r}, {specs!r}, os.environ.copy())"
                ),
            ],
            cwd=BASE_DIR,
            env=env,
        )
        procs.append((lane, proc))
        log(f"SPAWN lane={lane} pid={proc.pid}")
    failed = 0
    for lane, proc in procs:
        status = proc.wait()
        log(f"JOIN lane={lane} status={status}")
        if status != 0:
            failed = status
    log("queue complete")
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
