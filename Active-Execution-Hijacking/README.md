# Active Execution Hijacking

HANG evaluation on tool-integrated agents, corresponding to Section 8 and
Appendix E of **Harvested Adversarial Neural Guidance: Borrowed Thoughts,
Stolen Decisions**.

This module adapts the [InjecAgent benchmark](https://arxiv.org/abs/2403.02691).
It is not the upstream InjecAgent repository: the evaluation harness adds
action-specific surrogate-trace harvesting, one-time transplantation into the
first attacker-controlled observation, reasoning-aware output parsing, and
model adapters used by the paper.

## Evaluation Setting

The release uses both InjecAgent base splits:

- `test_cases_dh_base.json`: 510 one-phase direct-harm cases.
- `test_cases_ds_base.json`: 544 two-phase data-stealing cases.

For each attacker instruction and first attacker tool, the surrogate receives a
benign interaction context, the attacker-controlled observation, and the
intended action. A trace is retained only when the surrogate emits the required
tool call and arguments. At target-evaluation time, that harvested trace is
inserted once into the first attacker-controlled observation. The target then
continues without target-side search, feedback, or payload refinement.

For the data-stealing split, the same first-step trace remains in context while
the agent attempts the second exfiltration action. No second injection is made.

## Layout

```text
Active-Execution-Hijacking/
├── data/                       # InjecAgent cases, tools, and trace manifests
├── src/
│   ├── build_trace_manifest.py # Build the action-specific trace template
│   ├── harvest_traces_*.py     # Surrogate trace-harvesting entry points
│   ├── evaluate_prompted_agent.py
│   ├── models.py               # Provider adapters
│   ├── output_parsing.py       # Tool-trajectory parser and scorer
│   └── prompts/                # Agent and surrogate prompt templates
├── requirements.txt
└── LICENCE                     # Upstream InjecAgent MIT license
```

## Setup

```bash
cd Active-Execution-Hijacking
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
```

Provider credentials must be supplied through environment variables. The
GPT-OSS and Nemotron scripts use `NVIDIA_API_KEY`; MiniMax scripts use
`MINIMAX_API_KEY`; OpenRouter-backed models use `OPENROUTER_API_KEY`; and a
custom OpenAI-compatible endpoint uses `CUSTOM_BASE_URL` and `CUSTOM_API_KEY`.

## Build the Trace Manifest

The manifest is derived deterministically from the released InjecAgent attacker
cases:

```bash
python -m src.build_trace_manifest \
  --output data/harvested_traces_template.json
```

Each entry is keyed by `attacker_tool|attacker_instruction` and records the
split, intended first action, and empty trace fields. Trace-harvesting scripts
copy this template and fill `thought_step1` only after a successful surrogate
action. Each blank entry receives one model generation; the action is
validated, and a mismatch aborts the run instead of triggering candidate
selection. Up to five transient transport retries reuse the identical prompt
and inference settings.

## Harvest Traces

For example, to harvest GPT-OSS-20B traces:

```bash
export NVIDIA_API_KEY=...
python -m src.harvest_traces_gpt20b
```

The default output is `data/harvested_traces_gpt20b.json`. Other
`harvest_traces_*.py` scripts preserve the provider/model combinations from the
paper. Generation uses temperature `0.7`; retries must reuse the same prompt and
inference configuration.

The generated provider traces are not committed to this anonymous code release.
Regeneration therefore tests the released construction pipeline but cannot
guarantee byte-identical traces from a mutable remote model. For the Appendix E
protocol, select one completed trace mapping and replay that same file unchanged
across the target-model matrix.

## Evaluate HANG

```bash
python -m src.evaluate_prompted_agent \
  --model_type GPT \
  --model_name openai/gpt-oss-20b \
  --setting base \
  --prompt_type InjecAgent \
  --attack_method hang \
  --harvested_trace_path data/harvested_traces_gpt20b.json \
  --num_workers 4 \
  --use_cache
```

`--attack_method hang` requires a non-empty matching harvested trace for every
evaluated case and fails on missing entries. This prevents a static fallback
trace from being silently scored as HANG. Generated JSONL files and aggregate
scores are written under `results/`.

The harness also exposes `direct_request` and `h_cot` modes for local checks.
The paper's CoT-Forgery and AutoRAN-3 baselines use separately generated
payloads; do not label `h_cot` output as either baseline.

## Scoring

Only the externally emitted action or structured tool call is scored. For
models that return reasoning separately, the reasoning field is excluded. For
shared-field ReAct output, incidental action-like text inside reasoning is
sanitized before parsing. Success requires the benchmark-specified tool and
arguments; the data-stealing split additionally requires the second
exfiltration action.

## Upstream Attribution

Benchmark data, prompts, tool definitions, and portions of the evaluation code
originate from InjecAgent by Qiusi Zhan and collaborators. The upstream MIT
license is retained in [`LICENCE`](LICENCE). HANG-specific modifications should
be clearly identified in any redistributed derivative.
