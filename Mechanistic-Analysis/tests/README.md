# Lightweight Tests

These tests check the 30-case cohort/source round trip, prepared controls,
recorded cloud-run summaries, deterministic large-cohort resampling, the
separate six-case supporting subset, and parser/schema contracts without
loading GPT-OSS-20B or importing GPU-only dependencies.

Run from the repository root:

```bash
PYTHONPATH=HANG_Anonymous_Submission/Mechanistic-Analysis \
  python -m unittest discover \
  -s HANG_Anonymous_Submission/Mechanistic-Analysis/tests \
  -v
```

They are meant to catch packaging mistakes, not to reproduce the white-box
mechanistic experiments.
