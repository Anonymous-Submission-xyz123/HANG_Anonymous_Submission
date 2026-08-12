#!/usr/bin/env zsh
set -u

cd "$(dirname "$0")"

FIRST_PID="${1:-}"
LOG="ablation_print_subset150_nvidia_queue.log"

{
  date
  echo "FOLLOWUP queue started"
  if [[ -n "$FIRST_PID" ]]; then
    echo "Waiting for existing gpt120b PID $FIRST_PID"
    while kill -0 "$FIRST_PID" 2>/dev/null; do
      sleep 30
    done
    echo "Existing gpt120b PID $FIRST_PID finished"
    date
  fi

  echo "START gpt20b"
  python3 experiment_2_ablation_print_subset150_nvidia_gpt20b.py --config Comment --system_prompt prompt_A_en --think_prompt A1 --think_lang en --runs 1
  echo "DONE gpt20b status=$?"
  date

  echo "START nemotron"
  python3 experiment_2_ablation_print_subset150_nvidia_nemotron.py --config Comment --system_prompt prompt_A_en --think_prompt A1 --think_lang en --runs 1
  echo "DONE nemotron status=$?"
  date
} >> "$LOG" 2>&1
