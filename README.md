# Harvested Adversarial Neural Guidance (HANG)

Official anonymous submission repository for **Harvested Adversarial Neural Guidance (HANG)**, studying how synthetic pre-computed reasoning traces ("forged thinking") influence autoregressive reasoning models and tool-integrated agents.

---

## Repository Structure

```text
HANG_Anonymous_Submission/
├── Mechanistic-Analysis/        # Mechanistic interpretability suite (attention mass, logit shifts, interventions)
│   ├── hang/                    # Core mechanistic analysis Python library
│   ├── scripts/                 # Execution, probing, and plotting scripts
│   ├── requirements.txt         # Dependencies for mechanistic analysis
│   └── README.md                # Detailed mechanistic pipeline documentation
├── Active-Execution-Hijacking/  # Benchmark and evaluation suite for tool-integrated LLM agent hijacking
│   ├── data/                    # Evaluation benchmark datasets
│   ├── src/                     # Evaluation harnesses and model adapters
│   └── README.md                # Active execution hijacking instructions
└── Threat-Detection/            # WebShell & phishing threat detection dataset and experiments
    ├── dataset/                 # Raw and extended payload collections
    └── experiment/              # Thinking trace generation and evaluation scripts
```

---

## Overview of Modules

### 1. Mechanistic Analysis (`Mechanistic-Analysis/`)
Investigates the internal mechanisms behind forged-rationale imprinting:
- **Routing Displacement**: Injected trace content captures task-attributable attention routing in middle-to-late transformer layers.
- **Continuation Margin Shift**: Calculates continuation logodds margins of attacker-desired output continuations.
- **Interventions**: Attention ablation and activation patching engine for mechanistic verification.

For execution instructions, refer to [`Mechanistic-Analysis/README.md`](Mechanistic-Analysis/README.md).

### 2. Active Execution Hijacking (`Active-Execution-Hijacking/`)
Evaluates the susceptibility of tool-augmented reasoning agents to indirect execution hijacking when processing untrusted inputs containing injected rationale traces.

### 3. Threat Detection (`Threat-Detection/`)
Contains datasets and experiments evaluating defense and detection pipelines against malicious payloads (e.g., PHP webshells, phishing scripts) embedded with forged reasoning guidance.

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/Anonymous-Submission-xyz123/HANG_Anonymous_Submission.git
cd HANG_Anonymous_Submission

# Set environment
export PYTHONPATH=.

# Setup & run Mechanistic Analysis
cd Mechanistic-Analysis
pip install -r requirements.txt
python scripts/run_hang_api_exact_6.py --model_path /path/to/gpt-oss-20b --output_dir outputs/hang_api_exact_6_20b
```
