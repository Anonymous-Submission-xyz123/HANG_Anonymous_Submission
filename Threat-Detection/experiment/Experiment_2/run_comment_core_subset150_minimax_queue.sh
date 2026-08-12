#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -u experiment_2_nullsubject_core_subset150.py --model-key minimax_m1 --runs 1 --workers 3 --limit 150 --wrapper comment --no-strip-subject --output-prefix comment_core_subset150
python3 -u experiment_2_nullsubject_core_subset150.py --model-key minimax_m2.7 --runs 1 --workers 3 --limit 150 --wrapper comment --no-strip-subject --output-prefix comment_core_subset150
python3 -u experiment_2_nullsubject_core_subset150.py --model-key minimax_m3 --runs 1 --workers 3 --limit 150 --wrapper comment --no-strip-subject --output-prefix comment_core_subset150
