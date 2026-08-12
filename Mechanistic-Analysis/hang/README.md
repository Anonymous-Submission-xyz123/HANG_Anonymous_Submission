# Surrogated Reasoning Injection (HANG) Architecture & Mechanism Readme

## 1. Overview & Theoretical Framework

**Surrogated Reasoning Injection (HANG)** is an interpretability and jailbreak research pipeline studying how modern reasoning models behave when synthetic, pre-computed reasoning traces ("forged thinking") are injected into prompt contexts.

### The Core Mechanism Thesis: Forged-Rationale Imprinting
HANG operates via **forged-rationale imprinting**:
> The injected reasoning trace installs a *virtual decision rule* (e.g., `IMPORTANT-BUSINESS-CORE => Clean`). During answer formation, task-attributable routing shifts toward this forged trace, shifting the model's continuation probability distribution toward the attacker-desired output label (e.g., `Clean`).

Key mechanistic insights:
1. **Virtual Rule Installation**: The forged trace carries the primary attack payload by embedding a pre-computed rationale into the reasoning context.
2. **Routing Displacement**: Injected trace content captures task-attributable attention routing in middle-to-late transformer layers (specifically layers 10–16 in 20B parameters models), displacing standard payload and system prompt routing.
3. **Continuation Margin Shift**: The presence of the forged trace significantly increases the log-odds margin of attacker-desired continuations over defensive/refusal continuations (e.g., `Clean` vs `Webshell`).
4. **Marker Stabilization (Not Direct Grounding)**: Visible payload markers (e.g., `[IMPORTANT-BUSINESS-CORE]`) do not act as direct grounded attention targets; rather, they **stabilize** the attack by making the forged rationale self-consistent with visible input evidence. When the marker is omitted, the model still partially adopts the virtual rule, but final output construction may reject it via **consistency arbitration**.

---

## 2. Directory & Package Structure

The codebase is organized into a modular `hang/` library, standalone execution scripts in `scripts/`, and generated empirical outputs in `outputs/`.

```text
gpt_oss_lens/
├── README_HANG.md                       # HANG pipeline overview & LLM context guide (this file)
├── docs/
│   └── plans/                          # Historical execution and completion plans
├── hang/                                # Core HANG Python Library
│   ├── __init__.py                     # Package metadata
│   ├── schemas.py                      # Strongly-typed data contracts & dataclasses
│   ├── dataset.py                      # Dataset loading & strict control selection
│   ├── prompt_builder.py               # Pure prompt construction & character offset tracking
│   ├── token_spans.py                  # Tokenizer-grounded span alignment engine
│   ├── model_adapter.py                # PyTorch / Transformer activation & cache adapter
│   ├── runner.py                       # Condition runner (no_trace, matched_trace, unrelated_trace)
│   ├── evaluator.py                    # Evaluator harness for attack success metrics
│   ├── analysis.py                     # Attention mass, logit shifts, and representation probes
│   ├── interventions.py                # Attention ablation & activation patching engine
│   ├── cache.py                        # Activation cache disk-persistence manager
│   ├── metrics.py                      # Summary metric aggregators
│   └── configs/                        # Configuration YAMLs
│       ├── templates.yaml              # Prompt formatting templates
│       ├── targets.yaml                # Target model architectures & tokenizers
│       └── experiments.yaml            # Experiment execution parameters
├── scripts/                            # Runnable Experiment & Analysis Scripts
│   ├── run_hang_api_exact_6.py          # API-exact 6-case baseline runner
│   ├── run_hang_api_exact_mechanism_metrics.py # Computes attention & logit metrics
│   ├── run_hang_marker_ablation_6.py    # Marker vs no-marker trace ablation suite
│   ├── run_hang_marker_consistency_repr_probe.py # Representation probe analysis
│   ├── run_hang_missing_interventions.py# Targeted attention ablation & activation patching
│   ├── run_hang_mechanism_subset.py     # Execution across mechanism subsets
│   └── run_hang_1sample_demo.py         # End-to-end single sample demo verification
└── outputs/                            # Artifact Storage & Reports
    ├── README.md                       # Canonical output index and status guide
    ├── reports/                        # Cross-run audits and paper-facing reports
    ├── hang_api_exact_mechanism_package_20b/ # 20B model mechanism output package
    ├── hang_marker_ablation_6_20b/      # Marker ablation dataset & figures
    ├── hang_marker_consistency_repr_probe_20b/ # Probe results & plots
    └── _archive/                       # Superseded, smoke, and invalid artifacts
```

---

## 3. Core Data Contracts (`hang/schemas.py`)

All HANG operations use immutable, JSON-serializable dataclasses to maintain provenance and prevent state corruption across runs.

- `TraceRecord`: Represents synthetic/extracted reasoning traces with explicit provenance (`trace_id`, `source_model`, `source_payload_id`, `trace_text_used`, `original_token_count`).
- `BasePromptRecord`: Base evaluation item (`base_prompt_id`, `task_id`, `payload_id`, `payload_text`, `task_context`).
- `PromptRecord`: Formatted input condition (`condition`, `rendered_prompt`, `region_character_spans`, `trace_id`, `template_id`). Supported conditions:
  - `no_trace`: Baseline prompt containing only task context and payload.
  - `matched_trace`: Prompt with valid matched forged reasoning trace inserted.
  - `unrelated_trace`: Control prompt with a length-matched, authentic but semantically unrelated reasoning trace.
- `TokenSpans`: Exact token boundaries for prompt sub-regions (`system_span`, `task_context_span`, `trace_span`, `payload_span`, `final_prompt_token_index`, `generated_token_span`).
- `RunRecord`: Complete execution record for a single run including prompt token IDs, generated tokens, evaluator scores, and activation cache file paths.
- `AnalysisMetrics`: Calculated metrics per condition (trace attention mass, continuation cosine similarities, layerwise logit shifts).
- `InterventionConfig`: Configuration for causal interventions (`ablation` or `patching`, target layers, target heads, donor/recipient conditions).

---

## 4. HANG Library Components

### Data Loading & Control Pairing (`hang/dataset.py`)
- `HANGDatasetLoader`: Loads base prompts and trace sets.
- **Strict Matched Lookup**: `get_matched_trace()` enforces strict dataset joins by `source_payload_id` / `matched_trace_id`, preventing accidental fallback joins.
- **Strict Length Matching**: `get_unrelated_trace()` selects cross-task control traces within a hard token-length tolerance window (`length_tolerance_tokens`). Rejects non-matching controls to guarantee experimental validity.

### Pure Prompt Builder (`hang/prompt_builder.py`)
- `HANGPromptBuilder`: Formats prompts using template YAML definitions.
- Uses accumulative string parsing (`_build_and_annotate_spans`) to record exact character offsets for `{system_prompt}`, `{task_context}`, `{trace}`, and `{payload}` without using fragile substring searches.

### Tokenizer-Grounded Span Alignment (`hang/token_spans.py`)
- `HANGTokenSpanAligner`: Translates character spans into exact token index ranges (`TokenSpans`) using tokenizer offset mappings (`char_to_token`).
- Validates non-overlapping contiguous token spans and flags truncation or alignment errors before model execution.

### Model Adapter & Activation Caching (`hang/model_adapter.py`, `hang/cache.py`)
- `HANGModelAdapter`: Encapsulates Hugging Face / PyTorch models for forward-pass execution.
- Captures residual stream representations, attention matrices, MLP outputs, and unnormalized logits across specified layer ranges.
- Caches activation tensors to disk using `ActivationCacheManager` for reproducible offline post-hoc analysis.

### Condition Runner & Evaluators (`hang/runner.py`, `hang/evaluator.py`)
- `HANGConditionRunner`: Orchestrates batch execution of `no_trace`, `matched_trace`, and `unrelated_trace` conditions on target models.
- `HANGEvaluator`: Standardized evaluation wrapper verifying attack success (e.g., determining whether the generated text reflects the attacker-desired output label).

---

## 5. Experimental Methodology & Key Findings

### Behavior Ground Truth
- **API Setting**: High Attack Success Rate (ASR) observed (e.g., 553 / 594 Clean = 93.1% overall ASR in benchmark API outputs).
- **Key Mechanism Cases**: 6 representative cases exhibit 100% attack success (6/6 Clean outputs under local API-exact execution mode).

### Mechanistic Findings (GPT-OSS-20B Analysis)
1. **Routing Displacement (Layers 10–16)**:
   - For content-bearing generated tokens (steps 4–9), adding a forged trace shifts attention mass away from payload (0.141 -> 0.0018) and toward trace tokens (0.213 mass).
   - In full-context attention layers, system prompt access is reduced but not fully erased (system mass 0.460 -> 0.331; payload mass 0.301 -> 0.096; trace mass 0.238). Sink/unattributed attention mass remains significant.
2. **Continuation Margin Shift**:
   - Continuation probes at answer generation steps demonstrate a mean `Clean` vs `Webshell` logit margin of **+8.92** across all test cases, proving the model treats the trace as positive decision evidence.
3. **Marker Role vs. Trace Role**:
   - **Trace alone (No Marker)**: Achieves **4/6 ASR** with a mean Clean margin of **+8.02** logit points. The trace installs the core virtual rule.
   - **Trace + Marker**: Achieves **6/6 ASR** with a mean Clean margin of **+8.73** logit points. The marker acts as a stabilization anchor.
4. **Consistency Arbitration in Failures**:
   - Representation probing reveals that no-marker failures still exhibit high similarity between the answer state and the forged rule (+0.092 margin), confirming that failure is caused by output-stage consistency arbitration rather than trace ignoring.

---

## 6. How to Run & Reproduce

### Prerequisites & Setup
Activate the environment and set `PYTHONPATH`:
```bash
export PYTHONPATH=.
conda activate gpt-oss-env
```

### Running Core Experiment Scripts

1. **API-Exact Baseline Execution**:
   ```bash
   PYTHONPATH=. python scripts/run_hang_api_exact_6.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_api_exact_6_20b
   ```

2. **Mechanism Metrics Computation**:
   ```bash
   PYTHONPATH=. python scripts/run_hang_api_exact_mechanism_metrics.py \
     --run_dir outputs/hang_api_exact_6_20b \
     --output_dir outputs/hang_api_exact_mechanism_package_20b
   ```

3. **Marker Ablation Study**:
   ```bash
   PYTHONPATH=. python scripts/run_hang_marker_ablation_6.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_marker_ablation_6_20b
   ```

4. **Representation & Consistency Probing**:
   ```bash
   PYTHONPATH=. python scripts/run_hang_marker_consistency_repr_probe.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_marker_consistency_repr_probe_20b
   ```

5. **Interventions (Attention Ablation & Activation Patching)**:
   ```bash
   PYTHONPATH=. python scripts/run_hang_missing_interventions.py \
     --model_path /path/to/gpt-oss-20b \
     --output_dir outputs/hang_missing_interventions_20b
   ```

---

## 7. Strict Rules for AI Planners & Code Contributors

1. **Decoupled Architecture**: Do not use the Streamlit visualization interface (`app.py`, `logit_lens.py`) as an experiment runner. Experiment runners must remain pure command-line scripts.
2. **Tokenizer-Based Spans**: Never infer prompt token spans using character substring searching (`find()`) after tokenization. Always use fast tokenizer character offset mappings (`char_to_token`).
3. **Immutable Datasets**: Do not mutate `TraceRecord` or `BasePromptRecord` objects in place during dataset loading or control pairing.
4. **Strict Control Matching**: Reject unrelated control traces if their token length falls outside the configured length tolerance window (`length_tolerance_tokens`).
5. **Evaluator Integrity**: Never substitute ad-hoc string comparisons for evaluator-backed attack success verification (`EvaluationRecord`).
