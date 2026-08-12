# Security and Responsible Disclosure

This repository is a controlled research artifact for evaluating
reasoning-channel injection. It contains adversarial prompts, malicious code
samples, phishing content, and simulated unauthorized tool-use objectives.

## Safe Handling

- Run experiments only on systems and model endpoints you own or are authorized
  to test.
- Keep threat-detection samples as inert text. Do not execute, serve, or deploy
  them.
- Keep the agentic benchmark connected only to simulated tools and synthetic
  accounts.
- Store provider credentials in environment variables or an ignored `.env`
  file. Never place credentials in scripts, notebooks, logs, or result files.
- Review generated outputs before sharing them; reasoning traces and provider
  responses may reproduce sensitive input text.

## Credential Exposure

If a credential is committed, revoke and replace it immediately. Removing the
credential from the latest commit is insufficient because it remains in Git
history and in any existing clone. Rewrite the affected history before public
release and invalidate all exposed values.

## Reporting a Vulnerability

During anonymous review, report artifact vulnerabilities through the venue's
confidential author-contact mechanism. Do not open a public issue containing a
credential, unredacted exploit against a live service, or identifying author
information. Replace this section with the maintainers' security contact after
de-anonymization.
