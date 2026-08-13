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

The repository includes the complete prespecified 30-case GPT-OSS-20B
mechanism cohort, matched literal and no-literal-label controls, recorded cloud
outputs, and CPU-only summary code. A separate six-case subset supports the
attention and compact instrumentation comparisons.

```bash
cd Mechanistic-Analysis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
export HANG_MODEL_PATH=/path/to/gpt-oss-20b
```

Audit the 30 selected inputs and rebuild all recorded summaries:

```bash
python scripts/build_hang_claim_scaleup_30_inputs.py
python scripts/summarize_hang_claim_scaleup_30.py
```

Re-run the 30-case model stages on a machine that can load GPT-OSS-20B:

```bash
python scripts/run_hang_claim_scaleup_30.py \
  --model-path "$HANG_MODEL_PATH" \
  --output-dir outputs/hang_claim_scaleup_30 \
  --resume
```

Regenerate the paper-facing scale-up figure:

```bash
python scripts/plot_hang_claim_scaleup_30.py
```

Recorded results are under `artifacts/claim_scaleup_30/`; new model outputs are
written under `outputs/<run>/records`, `tables`, and `figures`. See the
mechanism README for the separate six-case supporting-analysis commands.

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

The released Appendix A evaluation sets contain 594 webshells, 1,000 phishing
emails, and 901 PowerShell scripts.

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
