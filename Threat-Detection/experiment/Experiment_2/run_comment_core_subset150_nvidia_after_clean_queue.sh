#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

while pgrep -f "run_clean_ablation_reruns_queue.sh" >/dev/null; do
  echo "$(date -Iseconds) waiting for clean_ablation_reruns_queue.sh to finish"
  sleep 60
done

python3 -u experiment_2_nullsubject_core_subset150.py --model-key gpt120b --runs 1 --workers 4 --limit 150 --wrapper comment --no-strip-subject --output-prefix comment_core_subset150
python3 -u experiment_2_nullsubject_core_subset150.py --model-key gpt20b --runs 1 --workers 4 --limit 150 --wrapper comment --no-strip-subject --output-prefix comment_core_subset150
python3 -u experiment_2_nullsubject_core_subset150.py --model-key nemotron --runs 1 --workers 4 --limit 150 --wrapper comment --no-strip-subject --output-prefix comment_core_subset150
