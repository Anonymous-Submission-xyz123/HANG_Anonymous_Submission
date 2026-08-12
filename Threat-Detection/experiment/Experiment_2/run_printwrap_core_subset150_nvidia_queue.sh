#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -u experiment_2_printwrap_core_subset150_nvidia_gpt120b.py --runs 1
python3 -u experiment_2_printwrap_core_subset150_nvidia_gpt20b.py --runs 1
python3 -u experiment_2_printwrap_core_subset150_nvidia_nemotron.py --runs 1
