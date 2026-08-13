# Mechanistic Artifact Provenance

The six-case/30-case discrepancy was resolved from committed Git history, not
by treating the six local cases as a proxy for the scale-up.

- Anonymous artifact base: `8c58ffbca35235accf9b34a13d93424b6e4a01fc`
  (`Restore complete Appendix A datasets`).
- Mechanism source repository: `gpt-oss-lens` commit
  `125807d536a19a7d5a19162495547a167a629957` (`final`, `origin/main`).
- Source API CSV repository: `prompt_inj` commit
  `8c453c521fd200cb449e0cfdc939c5741ecec935`; the result CSV was last changed
  by `54dbced8fe9b2da299b79c4e8aab0b25495aad37`.
- Base payload corpus provenance: `prompt_inj` commit
  `a737364fda2df3151f08329f276be7889fac0db9`.

The primary 30-case package was copied from these tracked files:

- `outputs/sri_eacl_claim_scaleup_cohort_20b_v1.json`
- `outputs/sri_eacl_claim_scaleup_source_records_20b_v1/`
- `outputs/sri_eacl_claim_scaleup_prepared_20b_v1/`
- `outputs/sri_eacl_claim_scaleup_no_literal_label_prepared_20b_v1/`
- `outputs/sri_eacl_claim_scaleup_20b_v1/`

Packaging changes were limited to HANG naming, repository-relative path
metadata, CPU-only summaries, and the correction of five-case resampling code
that was computationally intractable at 30 cases. The six-case input files are
retained only for their separate attention/instrumentation role.
