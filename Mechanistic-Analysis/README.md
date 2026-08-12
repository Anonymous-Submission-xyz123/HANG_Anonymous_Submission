# Mechanistic Analysis

Code and bundled inputs for Section 7 and Appendix C of **Harvested
Adversarial Neural Guidance: Borrowed Thoughts, Stolen Decisions**.

The paper asks whether the semantic conclusion carried by a harvested HANG
trace changes the target's decision before answer generation. It uses matched
prompt pairs, controlled terminal conclusions, literal-label removal, marker
ablation, answer-state representation analysis, and a supporting attention
comparison. The code in this directory is specific to those analyses.

## Claims and Scope

The paper reports the following results:

1. Changing only a trace's terminal conclusion shifts the GPT-OSS-20B
   `Clean`-versus-`Webshell` decision margin.
2. The shift remains positive after literal schema labels are replaced with
   semantically equivalent, non-identical expressions.
3. Removing the matching marker weakens but does not eliminate the controlled
   conclusion effect.
4. The controlled conclusion changes answer-state alignment in layers 10-16.
5. In a six-payload comparison, harvested traces receive more full-context
   attention than evaluated CoT-Forgery traces, primarily at the expense of
   payload attention. The paper treats this as supporting evidence rather than
   a complete causal account.

The bundled six-case inputs are a compact execution check for the local
GPT-OSS-20B pipeline. The paper's principal controlled-conclusion and marker
results use 30 payloads. Do not report six-case smoke-test statistics as the
paper's 30-case estimates.

## Layout

```text
Mechanistic-Analysis/
├── data/
│   ├── api_exact_6.csv       # Six API inputs used by the compact reproduction
│   ├── payloads/             # Original webshell payloads for those cases
│   ├── system_prompt.txt     # Target classifier prompt
│   └── traces/               # Corresponding harvested surrogate traces
├── hang/                     # Reusable data, model, scoring, and intervention code
├── scripts/                  # Experiment and post-processing entry points
├── requirements.txt
└── README.md
```

The [`hang/README.md`](hang/README.md) file documents the Python package and its
data contracts.

## Environment

The white-box analyses require a machine capable of loading GPT-OSS-20B. Set a
local snapshot with `--model-path` when the public model identifier cannot be
loaded directly.

```bash
cd Mechanistic-Analysis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
```

For deterministic comparisons, keep the script defaults unless intentionally
running a new experimental condition. The original target settings are
`temperature=0.15`, `top_p=0.6`, and seed `42`.

## Bundled Six-Case Reproduction

Run the local API-input reproduction:

```bash
python scripts/run_hang_api_exact_6.py \
  --model openai/gpt-oss-20b \
  --model-path /path/to/gpt-oss-20b \
  --output outputs/hang_api_exact_6_20b
```

Compute the corresponding label-margin, answer-state, and attention summaries:

```bash
python scripts/run_hang_api_exact_mechanism_metrics.py \
  --records-dir outputs/hang_api_exact_6_20b/records \
  --model-path /path/to/gpt-oss-20b \
  --output outputs/hang_api_exact_mechanism_package_20b
```

Run the compact marker ablation and representation probe:

```bash
python scripts/run_hang_marker_ablation_6.py \
  --model-path /path/to/gpt-oss-20b \
  --output outputs/hang_marker_ablation_6_20b

python scripts/run_hang_marker_consistency_repr_probe.py \
  --records-dir outputs/hang_marker_ablation_6_20b/records \
  --model-path /path/to/gpt-oss-20b \
  --output outputs/hang_marker_consistency_repr_probe_20b
```

The inference scripts above accept `--help`, use hyphenated argument names, and
write experiment artifacts with `--output`. Plot-only utilities use
`--output-dir`.

## Advanced Analyses

`run_hang_missing_interventions.py` performs attention ablation and activation
patching over previously generated records. It requires explicit paths to the
source runs and attention metrics:

```bash
python scripts/run_hang_missing_interventions.py \
  --source-runs /path/to/source/runs \
  --attention-metrics /path/to/mechanism_subset_metrics.csv \
  --model-path /path/to/gpt-oss-20b \
  --output outputs/hang_missing_interventions_20b
```

The `postprocess_*`, `plot_*`, and `replot_*` entry points operate on generated
records. They do not run model inference and should be used only with the
matching run configuration recorded in the output directory.

## Output Contract

New runs write immutable per-case records under `records/`, aggregate tables
under `tables/`, figures under `figures/`, and a run configuration at the output
root. Preserve the configuration and exact input record with every reported
number. Avoid comparing runs that differ in prompt template, model revision,
tokenizer revision, generation budget, or evaluator version.
