#!/usr/bin/env python3
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP_ROOT = ROOT / "prompt_inj" / "experiment"
LOG_PATH = EXP_ROOT / "overnight_finish_missing_matrix.log"


def log(message):
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now().isoformat(timespec='seconds')} {message}\n")
        handle.flush()


def pid_alive(pid):
    return Path(f"/proc/{pid}").exists()


def wait_for_pids(pids, label):
    pids = [str(pid) for pid in pids if str(pid).strip()]
    if not pids:
        log(f"WAIT {label}: no pids")
        return
    log(f"WAIT {label}: pids={','.join(pids)}")
    while True:
        alive = [pid for pid in pids if pid_alive(pid)]
        if not alive:
            log(f"WAIT {label}: complete")
            return
        log(f"WAIT {label}: alive={','.join(alive)}")
        time.sleep(120)


def run_job(name, cwd, cmd, env=None):
    cwd = Path(cwd)
    log(f"START {name} cwd={cwd} cmd={' '.join(cmd)}")
    log_path = cwd / f"overnight_{name}.log"
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    with log_path.open("a", encoding="utf-8") as handle:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=merged_env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    log(f"DONE {name} status={result.returncode} log={log_path}")
    return result.returncode


def main():
    env_keys = {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
        "MINIMAX_API_KEY": os.getenv("MINIMAX_API_KEY", ""),
    }
    log("overnight missing-matrix scheduler started")

    # Current jobs when this scheduler was launched:
    # 17565 = email strong naive Qwen resume.
    # 22223 = queued email DeepSeek-V4-Pro trace all-model run.
    wait_for_pids(os.getenv("WAIT_PIDS", "").split(","), "current prerequisites")

    py = sys.executable
    email = EXP_ROOT / "Experiment_2_phising"
    powershell = EXP_ROOT / "Experiment_2_powershell"
    webshell = EXP_ROOT / "Experiment_2"

    # Email phishing: no wrapping. Finish strong naive Nemotron, then resume the
    # existing baseline queue for CoT Forgery / H-CoT / AutoRAN leftovers.
    run_job(
        "email_strong_naive_nemotron",
        email,
        [
            py,
            "-u",
            "run_naive_comment_subset.py",
            "--model-key",
            "nemotron",
            "--workers",
            "3",
            "--prompt-file",
            str(EXP_ROOT / "phishing_prompt" / "prompt_A_strong_en.txt"),
            "--output-tag",
            "strong_prompt_20260714",
        ],
        env_keys,
    )
    run_job(
        "email_baselines_resume",
        email,
        [py, "-u", "run_baselines_150_sequential.py"],
        env_keys,
    )

    # PowerShell: comment wrapped. Finish short naive-comment cells, continue
    # OpenRouter DeepSeek full/subset runs, then resume subset baseline queue.
    for model_key in ("minimax_m3", "nemotron"):
        run_job(
            f"powershell_naive_comment_resume_{model_key}",
            powershell,
            [
                py,
                "-u",
                "run_naive_comment_subset.py",
                "--model-key",
                model_key,
                "--workers",
                "3",
            ],
            env_keys,
        )

    run_job(
        "powershell_deepseek_flash_full_resume",
        powershell,
        [
            py,
            "-u",
            "experiment_2_gen_thinking_duplicate.py",
            "--model-key",
            "deepseek_v4_flash",
            "--runs",
            "1",
            "--workers",
            "1",
            "--output-tag",
            "full_openrouter_deepseek_v4_flash",
        ],
        env_keys,
    )
    run_job(
        "powershell_deepseek_pro_subset150_commentwrapped",
        powershell,
        [
            py,
            "-u",
            "experiment_2_gen_thinking_duplicate.py",
            "--model-key",
            "deepseek_v4_pro",
            "--runs",
            "1",
            "--workers",
            "1",
            "--subset-file",
            str(powershell / "subset_150_seed_20260709.json"),
            "--output-tag",
            "subset150_openrouter_deepseek_v4_pro",
        ],
        env_keys,
    )
    run_job(
        "powershell_baselines_resume",
        powershell,
        [py, "-u", "run_baselines_150_sequential.py"],
        env_keys,
    )

    # Webshell: comment wrapped. Resume DeepSeek OpenRouter our-method runs with
    # comment marker plus PHP comment-wrapped trace. These scripts self-resume by
    # completed stems in the target CSV.
    run_job(
        "webshell_deepseek_pro_commentwrapped_resume",
        webshell,
        [
            py,
            "-u",
            "experiment_2_gemini25_flash_openrouter_our_method_subset.py",
            "--model",
            "deepseek/deepseek-v4-pro",
            "--limit",
            "150",
            "--workers",
            "1",
            "--output-tag",
            "deepseek_v4_pro_openrouter_subset150_traceT05_commentwrapped",
            "--min-trace-words",
            "100",
            "--trace-retries",
            "8",
            "--trace-temperature",
            "0.5",
            "--eval-temperature",
            "0.2",
            "--prefix-mode",
            "comment",
            "--trace-wrap",
            "php_comment",
        ],
        env_keys,
    )
    run_job(
        "webshell_deepseek_flash_commentwrapped_subset150",
        webshell,
        [
            py,
            "-u",
            "experiment_2_gemini25_flash_openrouter_our_method_subset.py",
            "--model",
            "deepseek/deepseek-v4-flash",
            "--limit",
            "150",
            "--workers",
            "1",
            "--output-tag",
            "deepseek_v4_flash_openrouter_subset150_traceT05_commentwrapped",
            "--min-trace-words",
            "100",
            "--trace-retries",
            "8",
            "--trace-temperature",
            "0.5",
            "--eval-temperature",
            "0.2",
            "--prefix-mode",
            "comment",
            "--trace-wrap",
            "php_comment",
        ],
        env_keys,
    )

    log("overnight missing-matrix scheduler complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
