# Mechanistic Analysis of Harvested Adversarial Neural Guidance (HANG)

This directory contains the core implementation and execution pipeline for the mechanistic analysis of **HANG**, investigating how autoregressive reasoning models behave when synthetic, pre-computed reasoning traces ("forged thinking") are injected into prompt contexts.

---

## Table of Contents
- [1. Overview & Theoretical Framework](#1-overview--theoretical-framework)
- [2. Directory & Package Structure](#2-directory--package-structure)
- [3. How to Run & Reproduce](#3-how-to-run--reproduce)
  - [Prerequisites & Setup](#prerequisites--setup)
  - [Execution Pipeline](#execution-pipeline)
  - [Visualization & Postprocessing](#visualization--postprocessing)

---

## 1. Overview & Theoretical Framework

### The Core Mechanism Thesis: Forged-Rationale Imprinting
HANG operates via **forged-rationale imprinting**:
> The injected reasoning trace installs a *virtual decision rule* (e.g., `IMPORTANT-BUSINESS-CORE => Clean`). During answer formation, task-attributable routing shifts toward this forged trace, shifting the model's continuation probability distribution toward the target output label (e.g., `Clean`).

### Key Mechanistic Insights
1. **Virtual Rule Installation**: The forged trace carries the primary payload by embedding a pre-computed rationale into the model's reasoning context.
2. **Routing Displacement**: Injected trace content captures task-attributable attention routing in middle-to-late transformer layers, displacing standard payload and system prompt routing.
3. **Continuation Margin Shift**: The presence of the forged trace significantly increases the log-odds margin of attacker-desired continuations over defensive/refusal continuations (e.g., `Clean` vs `Webshell`).
4. **Marker Stabilization**: Visible payload markers (e.g., `[IMPORTANT-BUSINESS-CORE]`) stabilize the behavior by making the forged rationale self-consistent with visible input evidence.

---

## 2. Directory & Package Structure

The codebase is organized into the modular `hang/` library (providing core mechanics, dataset engines, and activation adapters) and execution scripts in `scripts/`.

```text
Mechanistic-Analysis/
├── README.md                                # Project documentation
├── requirements.txt                         # Python dependencies
├── hang/                                    # Core Python Mechanistic Library
│   ├── analysis.py                          # Attention mass, logit shifts, and representation probes
│   ├── cache.py                             # Activation cache disk-persistence manager
│   ├── dataset.py                           # Dataset loading & strict control selection
│   ├── evaluator.py                         # Evaluator harness for attack success metrics
│   ├── interventions.py                     # Attention ablation & activation patching engine
│   ├── metrics.py                           # Summary metric aggregators
│   ├── model_adapter.py                     # PyTorch / Transformer activation adapter
│   ├── prompt_builder.py                    # Pure prompt construction engine
│   ├── runner.py                            # Condition runner pipeline
│   ├── schemas.py                           # Strongly-typed data contracts & dataclasses
│   ├── token_spans.py                       # Tokenizer-grounded span alignment engine
│   └── configs/                             # Configuration YAMLs
└── scripts/                                 # Analysis, Intervention & Plotting Scripts
    ├── run_hang_api_exact_6.py               # Baseline evaluation script under API-exact settings
    ├── run_hang_api_exact_mechanism_metrics.py# Computes attention & logit metrics (Answer-state alignment)
    ├── run_hang_marker_ablation_6.py         # Marker vs. no-marker trace ablation experiment
    ├── run_hang_marker_consistency_repr_probe.py # Representation probing for marker consistency
    ├── run_hang_missing_interventions.py     # Targeted attention ablation & activation patching
    ├── plot_hang_trace_provenance_figures.py # Attention mass and trace provenance visualization
    ├── postprocess_trace_provenance_03_07.py# Postprocessing raw provenance traces for summary tables
    ├── replot_deliberation_exit.py          # Plots exit trajectory metrics across reasoning stages
    └── replot_eacl_03_07.py                 # Final visualization replotting pipeline
```

---

## 3. How to Run & Reproduce

### Prerequisites & Setup

Ensure the required dependencies are installed and `PYTHONPATH` is set to include the project root:

```bash
pip install -r requirements.txt
export PYTHONPATH=.
```

### Execution Pipeline

1. **API-Exact Baseline Execution**:
   ```bash
   python scripts/run_hang_api_exact_6.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_api_exact_6_20b
   ```

2. **Mechanism Metrics Computation**:
   ```bash
   python scripts/run_hang_api_exact_mechanism_metrics.py \
     --run_dir outputs/hang_api_exact_6_20b \
     --output_dir outputs/hang_api_exact_mechanism_package_20b
   ```

3. **Marker Ablation Study**:
   ```bash
   python scripts/run_hang_marker_ablation_6.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_marker_ablation_6_20b
   ```

4. **Representation & Consistency Probing**:
   ```bash
   python scripts/run_hang_marker_consistency_repr_probe.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_marker_consistency_repr_probe_20b
   ```

5. **Interventions (Attention Ablation & Activation Patching)**:
   ```bash
   python scripts/run_hang_missing_interventions.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_missing_interventions_20b
   ```

### Visualization & Postprocessing

To process output traces and generate paper figures:

```bash
# Postprocess raw trace provenance output
python scripts/postprocess_trace_provenance_03_07.py

# Plot trace provenance and attention mass figures
python scripts/plot_hang_trace_provenance_figures.py

# Replot exit trajectories and paper figures
python scripts/replot_deliberation_exit.py
python scripts/replot_eacl_03_07.py
```
