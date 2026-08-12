#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Clean canonical reruns after purging invalid fixed/fixed2 intermediates.
# Trace selector in experiment_2_nullsubject_core_subset150.py now excludes
# IMPORTANT-BUSINESS-CORE-PRINT traces.

python3 -u experiment_2_nullsubject_core_subset150.py --model-key gpt120b --runs 1 --workers 4 --limit 150 --wrapper comment --strip-subject --output-prefix nullsubject_core_subset150
python3 -u experiment_2_nullsubject_core_subset150.py --model-key nemotron --runs 1 --workers 4 --limit 150 --wrapper comment --strip-subject --output-prefix nullsubject_core_subset150

# Canonical print Nemotron was good-selector but incomplete after power loss;
# this resumes/fills from the canonical CSV.
python3 -u experiment_2_nullsubject_core_subset150.py --model-key nemotron --runs 1 --workers 4 --limit 150 --wrapper print --no-strip-subject --output-prefix printwrap_core_subset150
