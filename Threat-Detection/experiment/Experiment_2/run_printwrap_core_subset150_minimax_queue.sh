#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -u experiment_2_printwrap_core_subset150_minimax_m1.py --runs 1
python3 -u experiment_2_printwrap_core_subset150_minimax_m2.7.py --runs 1
python3 -u experiment_2_printwrap_core_subset150_minimax_m3.py --runs 1
