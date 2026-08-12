# Harvested Adversarial Neural Guidance

Anonymous artifact for **Harvested Adversarial Neural Guidance: Borrowed
Thoughts, Stolen Decisions**.

HANG is a reasoning-channel injection attack. An attacker operates a
trace-exposing surrogate reasoning model under an attacker-defined permissive
policy, retains the reasoning trace from a successful surrogate run, and
transplants that trace into attacker-controlled context processed by a target
model. The target is not queried while the attack payload is constructed.

This repository contains the code and data used for the paper's two evaluation
settings:

- **Threat-detection evasion:** webshell, phishing-email, and PowerShell
  classifiers are steered toward benign verdicts.
- **Active execution hijacking:** tool-integrated agents are steered toward
  benchmark-specified unauthorized tool trajectories.

It also contains the white-box analyses used to study controlled conclusion
effects, marker ablations, answer-state alignment, and attention reallocation.

## Terminology

The following names are used consistently throughout this artifact:

- **HANG trace / harvested trace:** reasoning emitted by a surrogate during a
  successful attacker-aligned task completion.
- **Surrogate:** the trace-exposing model operated under the attacker's policy.
- **Target:** the model evaluated after the harvested trace is transplanted.
- **Matched-model evaluation:** surrogate and target use the same model version
  under different policies. This is an experimental control, not a requirement
  of HANG.
- **Cross-model transfer:** a harvested trace is replayed unchanged against a
  target from another model family.
- **CoT Forgery:** the synthesized-trace baseline from prior work. It is not an
  alternate name for HANG.

## Artifact Map

| Paper component | Artifact location | Purpose |
| --- | --- | --- |
| Sections 5-6, Appendices A-B and D | [`Threat-Detection/`](Threat-Detection/) | Datasets, trace harvesting, baselines, target evaluation, and robustness variants |
| Section 7 and Appendix C | [`Mechanistic-Analysis/`](Mechanistic-Analysis/) | Controlled conclusion interventions and white-box diagnostics |
| Section 8 and Appendix E | [`Active-Execution-Hijacking/`](Active-Execution-Hijacking/) | HANG adaptation of the InjecAgent benchmark |

Each module has its own setup, data map, and reproduction instructions. Run
commands from the module directory unless its README says otherwise.

## Quick Start

Python 3.10 or newer is recommended. Create separate environments for the
mechanistic and API-based experiments because the former requires a local
PyTorch model while the latter uses several provider SDKs.

```bash
git clone https://github.com/Anonymous-Submission-xyz123/HANG_Anonymous_Submission.git
cd HANG_Anonymous_Submission

python -m venv .venv
source .venv/bin/activate
pip install -r Mechanistic-Analysis/requirements.txt

cd Mechanistic-Analysis
python scripts/run_hang_api_exact_6.py --help
```

The bundled six-case data supports a local smoke reproduction of the
GPT-OSS-20B analysis. Full API evaluations require the relevant provider
credentials; copy [`.env.example`](.env.example) to a local `.env` or export the
variables in your shell. Never commit credentials.

## Reproducibility Scope

The repository distinguishes three kinds of artifact:

- **Source data and fixed subsets** are stored under `dataset/`, `data/`, or
  module-specific subset files.
- **Harvested traces and raw model responses** are stored alongside their
  corresponding experiment when redistribution is permitted.
- **Generated outputs** are written to `outputs/` or `results/` and are not
  treated as source code.

Remote-provider model behavior can change after the paper's June-July 2026
evaluation window. The paper records provider model identifiers, temperatures,
token limits, and other inference settings in Appendix B. A reproduction should
record the date and resolved provider model version in addition to those
settings.

## Safety and Responsible Use

This artifact contains malicious code samples, phishing content, adversarial
prompts, and examples of unauthorized tool-use objectives. Experiments must be
run in an isolated research environment. Do not execute dataset artifacts, aim
the attack at deployed services without authorization, or connect the agentic
benchmark to tools that can affect real accounts or systems. See
[`SECURITY.md`](SECURITY.md) for handling and disclosure guidance.

## Attribution and License

The active-execution module is derived from InjecAgent and retains its upstream
MIT license and attribution in
[`Active-Execution-Hijacking/LICENCE`](Active-Execution-Hijacking/LICENCE).
No project-wide license is asserted by this anonymous artifact. Add the final
project license before the archival release.

For anonymous review, cite the submitted paper by title. Author metadata and a
final citation record should be added only after the review process permits
de-anonymization.
