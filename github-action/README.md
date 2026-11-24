# Nova Repository Guardian

Deterministic, LLM-free GitHub Action for repository hygiene and security-oriented static checks. No runtime Python dependencies, model calls, API keys, telemetry, or source-code uploads.

Static heuristics are indicators, not proof of exploitability. Findings require human review; a clean scan is not proof that a repository is secure.

## Local setup

Requires Python 3.11+.

~~~powershell
cd github-action
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
cd ..
python github-action/src/nova_action.py --path . --config github-action/.nova.json --output .nova-reports --fail-on never
~~~

## CLI

nova [--path PATH] [--config FILE] [--output DIR] [--fail-on critical|high|medium|low|never] [--summary true|false]

Exit codes: 0 no finding meets threshold; 1 threshold reached; 2 configuration/execution error. Default high threshold fails on critical/high. Never does not fail because of findings.

## Rules

| ID | Severity | Detection |
|---|---|---|
| NOVA001 | Critical | Credential-like literal assignments |
| NOVA002 | High | Certain shell-enabled subprocess / command construction patterns |
| NOVA003 | High | eval() / exec() calls |
| NOVA004 | High | TLS verification explicitly disabled |
| NOVA005 | Medium | Python pickle deserialization |
| NOVA006 | Medium | Some dynamic SQL construction patterns |
| NOVA007 | Low | Debug mode explicitly enabled |

## Configuration

Edit .nova.json. Supported keys: version, exclude, include_extensions, max_file_bytes, rules, ignore_fingerprints. Use a finding fingerprint from nova.json output to suppress a result. Prefer fixing the underlying issue.

## Security model

- Reads repository files and writes reports to the configured output directory.
- Does not need a GitHub token and does not execute repository scripts.
- The included workflow grants contents: read only.
- Avoid privileged tokens and persistent self-hosted runners for untrusted pull requests.
- Static scan output is not a complete security audit.

MIT licensed; see repository LICENSE.
