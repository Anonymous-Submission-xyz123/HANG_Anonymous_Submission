# HANG Reproduction Artifact

Code and data for **Harvested Adversarial Neural Guidance: Borrowed Thoughts,
Stolen Decisions**. This README is the execution index; experiment-specific
details are in each module README.

## Reproduction Map

| Paper section | Directory | Reproduces |
| --- | --- | --- |
| Sections 5-6, Appendices A-B and D | [`Threat-Detection/`](Threat-Detection/) | Webshell, phishing, and PowerShell evasion |
| Section 7, Appendix C | [`Mechanistic-Analysis/`](Mechanistic-Analysis/) | Controlled conclusions, marker ablation, representations, and attention |
| Section 8, Appendix E | [`Active-Execution-Hijacking/`](Active-Execution-Hijacking/) | InjecAgent tool-use hijacking |

Use Python 3.10 or newer. Run each module in a separate virtual environment.
Model weights and external baseline prompt assets are not bundled.

## 1. Mechanistic Analysis

The repository includes six exact GPT-OSS-20B API inputs, their payloads,
harvested traces, and target system prompt. These provide a compact execution
check. The paper's principal controlled-conclusion estimates use 30 payloads.

```bash
cd Mechanistic-Analysis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
export HANG_MODEL_PATH=/path/to/gpt-oss-20b
```

Reproduce the six target runs:

```bash
python scripts/run_hang_api_exact_6.py \
  --model-path "$HANG_MODEL_PATH" \
  --output outputs/hang_api_exact_6_20b
```

Compute mechanism metrics:

```bash
python scripts/run_hang_api_exact_mechanism_metrics.py \
  --records-dir outputs/hang_api_exact_6_20b/records \
  --model-path "$HANG_MODEL_PATH" \
  --output outputs/hang_api_exact_mechanism_package_20b
```

Run the marker and representation checks:

```bash
python scripts/run_hang_marker_ablation_6.py \
  --model-path "$HANG_MODEL_PATH" \
  --output outputs/hang_marker_ablation_6_20b

python scripts/run_hang_marker_consistency_repr_probe.py \
  --records-dir outputs/hang_marker_ablation_6_20b/records \
  --model-path "$HANG_MODEL_PATH" \
  --output outputs/hang_marker_consistency_repr_probe_20b
```

Outputs are written under `outputs/<run>/records`, `tables`, and `figures`.

## 2. Active Execution Hijacking

```bash
cd Active-Execution-Hijacking
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
```

Rebuild the released action-specific manifest:

```bash
python -m src.build_trace_manifest \
  --output data/harvested_traces_template.json
```

Harvest traces from a surrogate, for example GPT-OSS-20B:

```bash
export NVIDIA_API_KEY=...
python -m src.harvest_traces_gpt20b
```

Evaluate the same trace mapping on a target:

```bash
python -m src.evaluate_prompted_agent \
  --model_type GPT \
  --model_name openai/gpt-oss-20b \
  --setting base \
  --prompt_type InjecAgent \
  --attack_method hang \
  --harvested_trace_path data/harvested_traces_gpt20b.json \
  --num_workers 4
```

Expected dataset sizes are 510 direct-harm cases and 544 data-stealing cases.
Results are written under `results/`.

## 3. Threat-Detection Evasion

```bash
cd Threat-Detection
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NVIDIA_API_KEY=...
```

Run one GPT-OSS-20B evaluation per domain:

```bash
# Webshell
python experiment/Experiment_2/experiment_2_gen_thinking_duplicate_gpt-oss-20b-high.py \
  --config IMPORTANT-BUSINESS-CORE --system_prompt prompt_A_en \
  --think_prompt A2 --runs 1

# Phishing
python experiment/Experiment_2_phishing/experiment_2_gen_thinking_duplicate_gpt-oss-20b-high.py \
  --config IMPORTANT-BUSINESS-CORE --system_prompt prompt_A_en \
  --think_prompt A2 --runs 1

# PowerShell
python experiment/Experiment_2_powershell/experiment_2_gen_thinking_duplicate.py \
  --model-key gpt_oss_20b --config IMPORTANT-BUSINESS-CORE \
  --system_prompt prompt_A_en --think_prompt A2 --runs 1 --workers 3
```

Surrogate generation uses temperature `0.7`. Target evaluation uses
temperature `0.15` and `top_p=0.6`. Raw CSVs are the source records; summary
CSVs are derived outputs. See [`Threat-Detection/README.md`](Threat-Detection/README.md)
for model-specific runners and dataset provenance.

## Manifest Check

```bash
(cd Active-Execution-Hijacking && \
  python -m src.build_trace_manifest --output /tmp/hang_manifest.json)
```

The manifest contains 62 action-specific entries: 30 direct-harm and 32
data-stealing instruction-tool pairs.

Treat all threat-detection samples as untrusted text; do not execute them.
