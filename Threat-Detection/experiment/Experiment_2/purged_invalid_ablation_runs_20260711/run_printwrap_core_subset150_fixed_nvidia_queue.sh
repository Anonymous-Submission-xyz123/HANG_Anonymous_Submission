#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -u experiment_2_nullsubject_core_subset150.py --model-key gpt120b --runs 1 --workers 4 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150_fixed
python3 -u experiment_2_nullsubject_core_subset150.py --model-key gpt20b --runs 1 --workers 4 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150_fixed
python3 -u experiment_2_nullsubject_core_subset150.py --model-key nemotron --runs 1 --workers 4 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150_fixed
