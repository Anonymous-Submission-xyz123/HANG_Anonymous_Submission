#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -u experiment_2_nullsubject_core_subset150.py --model-key minimax_m1 --runs 1 --workers 3 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150_fixed
python3 -u experiment_2_nullsubject_core_subset150.py --model-key minimax_m2.7 --runs 1 --workers 3 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150_fixed
python3 -u experiment_2_nullsubject_core_subset150.py --model-key minimax_m3 --runs 1 --workers 3 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150_fixed
