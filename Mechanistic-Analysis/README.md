# Mechanistic Analysis of HANG

Code and pipeline for mechanistic analysis of **Harvested Adversarial Neural Guidance (HANG)**, analyzing how reasoning models respond to synthetic pre-computed reasoning traces ("forged thinking").

---

## 1. Setup

```bash
pip install -r requirements.txt
export PYTHONPATH=.
```

---

## 2. Execution Pipeline

### Core Experiments
```bash
# 1. Baseline Evaluation
python scripts/run_hang_api_exact_6.py --model_path /path/to/gpt-oss-20b --output_dir outputs/hang_api_exact_6_20b

# 2. Mechanism Metrics (Attention & Logit shift)
python scripts/run_hang_api_exact_mechanism_metrics.py --run_dir outputs/hang_api_exact_6_20b --output_dir outputs/hang_api_exact_mechanism_package_20b

# 3. Marker Ablation Study
python scripts/run_hang_marker_ablation_6.py --model_path /path/to/gpt-oss-20b --output_dir outputs/hang_marker_ablation_6_20b

# 4. Representation Probing
python scripts/run_hang_marker_consistency_repr_probe.py --model_path /path/to/gpt-oss-20b --output_dir outputs/hang_marker_consistency_repr_probe_20b

# 5. Interventions (Attention Ablation & Activation Patching)
python scripts/run_hang_missing_interventions.py --model_path /path/to/gpt-oss-20b --output_dir outputs/hang_missing_interventions_20b
```

### Postprocessing & Plotting
```bash
python scripts/postprocess_trace_provenance_03_07.py
python scripts/plot_hang_trace_provenance_figures.py
python scripts/replot_deliberation_exit.py
python scripts/replot_eacl_03_07.py
```


