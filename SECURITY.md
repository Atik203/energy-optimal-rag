# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| `0.1.x` (current scaffold) | Yes |
| `< 0.1.0` | No |

This is a research repository, not a production service. Security fixes are applied to the
current `main` branch and the latest tagged release.

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Use GitHub's private vulnerability reporting:

1. Go to the repository's **Security** tab.
2. Choose **Report a vulnerability**.
3. Include the affected version or commit, a description, reproduction steps, and the impact.

If private reporting is unavailable, email **atikurrahaman0305@gmail.com** with the subject
line `SECURITY: energy-optimal-rag`.

## What to report

- A committed secret: API key, GitHub token, Hugging Face token, cloud credential, or
  private key.
- A data leak: raw SQuAD/HotpotQA text, private query logs, or personally identifying
  information in a tracked artifact.
- A dependency vulnerability that affects the package or CI.
- A workflow or supply-chain issue: an action pinned to a mutable tag, an unsafe script, or
  a path that could execute untrusted input.
- A prompt-injection or data-poisoning path in the experiment harness that could corrupt
  results.

## What not to report publicly

Do not paste a live secret into an issue, pull request, commit, or chat. Revoke and rotate it
first. If a secret was committed, assume it is compromised even after the commit is removed:
git history retains it.

## Our handling

- Acknowledge within **3 business days**.
- Triage and confirm within **10 business days**.
- For a valid secret leak, rotate the credential, purge the artifact, and publish a short
  advisory after remediation.
- For a dependency issue, patch or pin and note it in `CHANGELOG.md`.
- Credit reporters unless they ask to remain anonymous.

These are best-effort targets for a small research team, not a contractual SLA.

## Repository rules

- No secrets, tokens, `.env` files, or credentials are committed.
- No raw dataset text or model weights are committed.
- CI runs on GitHub-hosted runners with the default read-only `GITHUB_TOKEN`; no deployment
  secrets are exposed to pull requests.
- Third-party GitHub Actions should be pinned to a version tag at minimum; pinning to a
  commit SHA is preferred.
- Dependencies are declared in `pyproject.toml` and `environment.yml`; the lock file is
  generated on the target machine.

## Dataset licensing and redistribution

SQuAD v1.1 and HotpotQA are distributed under **CC BY-SA 4.0**. Their licenses remain in
force. This repository does not redistribute their raw text. It releases dataset IDs,
versions, checksums, prompts, configs, and model predictions only where the upstream license
permits. Do not add raw question/context files to the repository or to a release artifact.

If you believe a tracked file violates an upstream license, report it through the private
channel above.
