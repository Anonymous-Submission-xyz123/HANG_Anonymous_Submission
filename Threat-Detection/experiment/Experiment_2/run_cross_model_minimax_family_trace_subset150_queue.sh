#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

BEST_TRACE="$(dirname "$0")/../Experiment_1/best_minimax.txt"
TRACE_LABEL="minimax_family_best"

models=(
  gpt120b
  gpt20b
  nemotron
  minimax_m1
  minimax_m2.7
  minimax_m3
)

for model in "${models[@]}"; do
  cmd="python3 -u experiment_2_cross_model_best_trace_subset150.py --model-key ${model} --workers 4 --limit 150 --best-trace-path ${BEST_TRACE} --trace-label ${TRACE_LABEL}"
  echo "$(date -Iseconds) START ${cmd}"
  ${cmd}
  echo "$(date -Iseconds) DONE ${cmd} status=$?"
done
