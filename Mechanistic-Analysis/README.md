# Mechanistic Analysis

Code, inputs, and recorded outputs for Section 7 and Appendix C of
**Harvested Adversarial Neural Guidance: Borrowed Thoughts, Stolen Decisions**.

The primary mechanism study uses a prespecified 30-case GPT-OSS-20B webshell
cohort. It crosses the terminal conclusion carried by an injected trace
(`Clean` or `Webshell`) with marker presence, repeats the comparison after
removing the literal schema labels from the trace, and measures whether the
injected decision reaches the final answer. A separate six-case experiment
supports the attention comparison. The two sample sizes refer to different
experiments and must not be pooled.

## Claims and Scope

The released evidence supports the following narrow claims:

1. Changing only a trace's terminal conclusion shifts the GPT-OSS-20B
   `Clean`-versus-`Webshell` continuation margin.
2. The shift remains positive when the literal strings `Clean` and `Webshell`
   are replaced by semantically equivalent, non-identical descriptions.
3. The matching marker is not necessary for the controlled-conclusion effect,
   but it increases within-1024-token final-channel entry and expression of the
   injected `Clean` decision.
4. The controlled conclusion changes answer-state alignment in layers 10-16.
5. On six payloads, harvested traces receive more full-context attention than
   evaluated CoT-Forgery traces. This is supporting evidence, not a complete
   causal explanation.

The artifact does not establish that the marker is a direct attention target,
that the model blindly trusts all injected reasoning, or that attention alone
causes HANG success.

## Recorded 30-Case Results

The committed cloud-run records reproduce these aggregate results:

- The controlled outcome effect is positive in all 60 case-by-marker cells.
  The mean margin shift is `9.44` without the marker and `11.73` with it.
- The no-literal-label control is also positive in all 60 cells. Its mean
  absolute effect is `5.70`, retaining `53.8%` of the literal-label reference
  effect on average.
- Across five seeds per case and marker condition, final-channel entry rises
  from `78/150` (`52.0%`) without the marker to `117/150` (`78.0%`) with it.
  Expression of the injected `Clean` decision rises from `50/150` (`33.3%`) to
  `109/150` (`72.7%`).

These are recorded GPT-OSS-20B results. Rebuilding summaries and figures is
CPU-only; re-running the model stages requires a machine that can load the
20B model.

## Layout

```text
Mechanistic-Analysis/
|-- artifacts/claim_scaleup_30/  # Recorded cloud-run rows, summaries, figures
|-- data/
|   |-- claim_scaleup_30/
|   |   |-- population/          # Full presampling API CSV and payload corpus
|   |   |-- api_exact_30.csv     # The selected 30 successful source rows
|   |   |-- traces/              # Selected harvested traces
|   |   |-- source_records/      # Marker/no-marker source prompts
|   |   |-- prepared_literal/    # 60 controlled terminal-conclusion pairs
|   |   `-- prepared_label_free/ # 60 no-literal-label control pairs
|   |-- api_exact_6.csv          # Six-case attention/execution subset
|   |-- payloads/ and traces/    # Six-case supporting-analysis inputs
|   `-- system_prompt.txt
|-- hang/                        # Data, model, scoring, and analysis code
|-- scripts/                     # Preparation, execution, summary, and plotting
|-- tests/
|-- requirements.txt
`-- README.md
```

See [`data/README.md`](data/README.md) for the two input scopes and
[`artifacts/claim_scaleup_30/README.md`](artifacts/claim_scaleup_30/README.md)
for the recorded-output contract.

## Environment

```bash
cd Mechanistic-Analysis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
```

## CPU-Only Reproduction

Rebuild and audit the selected input package from the committed source
population and cohort manifest:

```bash
python scripts/build_hang_claim_scaleup_30_inputs.py
```

Recompute the consolidated mechanism and expression summaries:

```bash
python scripts/summarize_hang_claim_scaleup_30.py
```

Regenerate the paper-facing three-panel figure from recorded tables:

```bash
python scripts/plot_hang_claim_scaleup_30.py
```

## Re-running the 30-Case Model Experiment

The committed prepared pairs allow the scored and generated stages to be run
without reconstructing prompts. Keep the original settings unless testing a
new condition: temperature `0.15`, `top_p=0.6`, five seeds `41`-`45`, and a
1024-token generation horizon.

```bash
python scripts/run_hang_claim_scaleup_30.py \
  --model-path /path/to/gpt-oss-20b \
  --output-dir outputs/hang_claim_scaleup_30 \
  --resume
```

To reconstruct the prespecified cohort and prepared pairs from the full source
population before running the model:

```bash
python scripts/prepare_hang_claim_scaleup_30.py \
  --model-path /path/to/gpt-oss-20b
```

The preparation stage uses the tokenizer but does not load model weights. The
model runner is append-only/resumable and writes a run plan before inference.

## Six-Case Supporting Analysis

The older `run_hang_api_exact_6.py`,
`run_hang_api_exact_mechanism_metrics.py`, and
`run_hang_marker_consistency_repr_probe.py` entry points reproduce the compact
execution, representation, and attention checks. Their six-case statistics
must not be reported as the 30-case controlled-conclusion estimates.

## Lightweight Checks

These checks do not load GPT-OSS-20B:

```bash
python -m compileall -q .
PYTHONPATH="$PWD" python -m unittest discover -s tests -v
```

They verify source/selected-row round trips, prepared-pair invariants, recorded
row counts, summary claims, evaluator parsing, and schema serialization.

## Output Contract

New model runs write immutable per-case rows under `records/`, aggregate tables
under `tables/`, figures under `figures/`, and a run plan at the output root.
Preserve the exact input manifest and model/tokenizer revision with every
reported number. Do not compare runs that differ in prompt template, scoring
protocol, generation budget, or evaluator version without labeling the change.
