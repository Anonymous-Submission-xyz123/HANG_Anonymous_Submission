# Bundled Six-Case Inputs

This directory contains the compact GPT-OSS-20B reproduction inputs documented
in the parent README.

- `api_exact_6.csv` contains one successful API record for each of six
  representative webshell payloads.
- `payloads/` contains the corresponding original malicious artifacts.
- `traces/` contains the harvested surrogate reasoning used in each API input.
- `system_prompt.txt` is the target webshell-classification prompt.

The rows and files are copied without semantic modification from the fixed
webshell experiment. They support an execution and instrumentation check; they
are not a substitute for the paper's 30-payload controlled-conclusion analysis.

Treat every payload as untrusted text. Do not execute these files.
