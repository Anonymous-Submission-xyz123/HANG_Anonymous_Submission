# `hang` Package

Reusable components for the HANG mechanistic-analysis experiments. The package
loads fixed prompt/trace records, aligns character regions to target-tokenizer
spans, runs local models, computes decision metrics, and applies causal
interventions.

## Core Data Contracts

- `TraceRecord` records trace text and provenance, including the source model
  and source payload.
- `BasePromptRecord` identifies the task context and original payload.
- `PromptRecord` stores the rendered experimental condition and character
  spans.
- `TokenSpans` stores tokenizer-aligned prompt regions.
- `RunRecord` stores the exact prompt tokens, generated tokens, evaluator
  result, and cache references for one run.
- `AnalysisMetrics` stores derived per-condition metrics.
- `InterventionConfig` defines an ablation or patching operation.

The generic condition runner supports `no_trace`, `matched_trace`, and
`unrelated_trace`. Paper-facing scripts may construct stricter matched pairs
directly when an intervention must change only one trace feature.

## Components

| File | Responsibility |
| --- | --- |
| `dataset.py`, `triad_dataset.py` | Load prompts and join traces to payloads |
| `prompt_builder.py` | Render prompts while recording source-region offsets |
| `token_spans.py` | Convert character offsets to tokenizer-grounded spans |
| `model_adapter.py` | Load local Hugging Face models and capture activations |
| `runner.py` | Execute conditions and persist run records |
| `scorer.py`, `evaluator.py` | Compute structured decision margins and output labels |
| `eacl_focused.py`, `latent_state.py` | Build controlled-conclusion and representation analyses |
| `interventions.py`, `patch_experiment.py` | Attention ablation and activation patching |
| `analysis.py`, `metrics.py` | Aggregate records and export tables/figures |
| `cache.py` | Persist large tensors outside JSON run records |

## Invariants

1. Join a harvested trace to its source payload by explicit identifiers. Never
   fall back to row order or filename similarity.
2. Compute token spans with the target tokenizer's offset mapping. Do not infer
   token boundaries from character counts after tokenization.
3. Preserve source records and create a new record for every transformed
   condition.
4. Compare controlled conditions only when their non-intervened fields are
   identical.
5. Record the model and tokenizer revision, prompt template, seed, generation
   settings, evaluator version, and input hashes with every run.

See the parent [`README.md`](../README.md) for executable reproductions and the
paper-to-script mapping.
