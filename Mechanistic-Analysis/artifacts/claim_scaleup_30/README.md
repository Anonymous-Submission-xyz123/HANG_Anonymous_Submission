# Recorded 30-Case Mechanism Run

This directory contains the completed GPT-OSS-20B cloud-run artifacts for the
prespecified 30-case mechanism cohort.

- `run_plan.json` records the cohort, model, conditions, seeds, generation
  budget, and scorer protocol. Original cloud-only absolute paths were
  normalized to repository-relative paths during packaging.
- `records/prefix_causal_factorial.jsonl` contains 120 literal-label margin
  rows: 30 cases x 2 marker conditions x 2 controlled conclusions.
- `records/indirect_factorial_margins.jsonl` contains the matching 120
  no-literal-label rows.
- `records/expression_generations.jsonl` contains 300 generations: 30 cases x
  2 marker conditions x 5 seeds.
- `tables/` contains CSV views of those immutable JSONL records.
- `indirect_factorial_summary.json`, `expression_summary.json`, and
  `claim_scaleup_summary.json` are deterministic derived summaries.
- `figures/` contains the paper-facing scale-up plots.

The raw model rows were copied without semantic changes from committed
`gpt-oss-lens` artifacts. The summary files can be rebuilt CPU-only with:

```bash
PYTHONPATH="$PWD" python scripts/summarize_hang_claim_scaleup_30.py
```

The summary uses cases as the independent unit. For 30 cases it reports a
fixed-seed, deterministic 100,000-draw percentile bootstrap and 200,000-draw
paired sign-flip Monte Carlo test. Small cohorts retain exact enumeration.
