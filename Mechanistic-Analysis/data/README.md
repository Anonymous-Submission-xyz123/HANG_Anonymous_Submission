# Mechanism Input Data

This directory contains two deliberately separate input scopes.

## Primary 30-Case Cohort

`claim_scaleup_30/` is the input package for the paper's principal
controlled-conclusion, no-literal-label, and marker-expression results.

- `population/source_api_results.csv` is the 594-row GPT-OSS-20B source API
  result file used before local outcome scoring.
- `population/payloads/` is the corresponding 120-file base payload corpus
  considered by the cohort-preparation code.
- `cohort_manifest.json` records the fixed seed, eligibility audit, exclusions,
  original five retained cases, and 25 additional sampled cases.
- `api_exact_30.csv` contains exactly one successful source API row for each
  selected case.
- `traces/` contains the 30 harvested traces recovered byte-for-byte from the
  selected API inputs.
- `source_records/` contains marker-present and marker-absent source prompts
  for every selected case.
- `prepared_literal/` contains 60 matched controlled-conclusion pairs: 30
  cases crossed with marker present/absent.
- `prepared_label_free/` contains the corresponding 60 semantic controls in
  which literal output-label strings are absent.
- `selected_inputs_manifest.json` records hashes and paths for the selected
  payload/trace pairs.

Run `python scripts/build_hang_claim_scaleup_30_inputs.py` from the parent
directory to reconstruct and verify the selected CSV, traces, and hashes.

## Six-Case Supporting Inputs

`api_exact_6.csv`, `payloads/`, and `traces/` preserve the compact six-payload
execution/attention subset. They support the separate attention and local
instrumentation comparisons; they are not the sample behind the primary
30-case estimates.

All payloads are untrusted text. Do not execute them.
