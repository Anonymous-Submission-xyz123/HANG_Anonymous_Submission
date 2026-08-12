# Threat-Detection Evasion

Datasets and API experiment code for Sections 5-6 and Appendices A-B and D of
**Harvested Adversarial Neural Guidance: Borrowed Thoughts, Stolen Decisions**.

All evaluated source artifacts are malicious. HANG succeeds when the target
misclassifies a webshell, phishing email, or malicious PowerShell script as
benign. The same fixed inputs are reused across HANG and all baselines within a
domain.

## Data

The release mirrors the public sources listed in Appendix A:

| Domain | Public sources | Released location |
| --- | --- | --- |
| Webshell | `tennc/webshell`, `JohnTroony/php-webshells` | `dataset/php-webshells/` |
| Phishing email | `zefang-liu/phishing-email-dataset`, Nazario Phishing Corpus | `dataset/phishing/` |
| PowerShell | `dessertlab/offensive-powershell`, `das-lab/mpsd` | `experiment/Experiment_2_powershell/dataset/` |

When a domain contained more than 1,000 artifacts, the paper used a fixed-seed,
source-stratified 1,000-item subset. Smaller domains were used in full. Subset
manifests are stored beside the corresponding experiment and must be reused
across methods.

Dataset files may contain executable malware or live-looking phishing content.
Treat every sample as untrusted text and do not execute it.

## Experiment Layout

```text
Threat-Detection/
├── dataset/                     # Source and extended artifact collections
├── experiment/
│   ├── Experiment_1/            # Webshell trace-generation inputs, when generated
│   ├── Experiment_2/            # Webshell target evaluations and robustness variants
│   ├── Experiment_2_phishing/   # Phishing trace generation and evaluation
│   ├── Experiment_2_powershell/ # PowerShell trace generation and evaluation
│   ├── prompt/                  # Webshell target and surrogate prompts
│   └── phishing_prompt/         # Phishing target and surrogate prompts
├── src/                         # Shared provider request helpers
└── requirements.txt
```

`Experiment_1` and `Experiment_2` are retained as historical webshell run names
because generated result files depend on them. New documentation uses the
domain names instead of treating those numbers as experimental conditions.

## Setup

```bash
cd Threat-Detection
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure providers through environment variables only:

```bash
export NVIDIA_API_KEY=...
export MINIMAX_API_KEY=...
export OPENROUTER_API_KEY=...
export GEMINI_API_KEY=...
```

Some historical scripts support an OpenAI-compatible custom endpoint through
`CUSTOM_BASE_URL`, `CUSTOM_API_KEY`, and `CUSTOM_MODEL`. No private endpoint or
credential is embedded in the release.

## Reproduction Protocol

For each model, domain, and sample, the matched-model pipeline has two stages:

1. Run the surrogate under the permissive A2 policy at temperature `0.7` and
   retain its reasoning only when the attacker-selected benign conclusion is
   produced.
2. Append the marker and harvested trace to the original malicious artifact in
   the domain-native wrapper, then query the target at temperature `0.15` and
   `top_p=0.6`.

The original artifact must remain complete after insertion. Do not truncate the
source artifact or trace. API retries reuse the same prompt and settings and are
limited to transient failures.

Scripts are grouped by domain and model because providers expose reasoning in
different response fields. Before running a full matrix, use the script's
`--help` output where available, confirm its `MODEL` identifier and output path,
and run one sample. Raw responses should retain the model identifier, input,
reasoning field, final answer, token count, and condition tag.

## Baselines and Robustness Variants

The paper compares HANG against Direct Request, CoT Forgery, H-CoT, and
AutoRAN-3. Baseline generators live with the target-domain scripts and must use
the same fixed subset and insertion channel as HANG.

Appendix D evaluates three surface-form variants of the same harvested trace:
`Print`, `Function`, and `Pronoun-Free`. These are robustness variants, not new
attack names. Result and evaluation files containing `ablation_print`,
`function`, or `pronoun` correspond to that appendix.

## Results and Provenance

Raw result CSVs are immutable run records. `evaluate_summary*.csv` files are
derived summaries and should never replace the raw files. Keep checkpoint and
queue state local; they are operational artifacts, not research results.

For a paper-facing number, record:

- domain and fixed-subset manifest;
- attack method and payload format;
- source and target model identifiers;
- provider and evaluation date;
- temperature, `top_p`, token limit, and reasoning configuration;
- raw result file and evaluator script revision.
