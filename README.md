# Nova

Nova Repository Guardian is an independent, deterministic, LLM-free GitHub Action for repository hygiene and security-oriented static checks.

The implementation is in github-action/. The workflow at .github/workflows/nova-guardian.yml runs it on pushes, pull requests, and manual dispatch.

Local setup (Python 3.11+):
~~~powershell
cd github-action
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
cd ..
python github-action/src/nova_action.py --path . --config github-action/.nova.json --output .nova-reports --fail-on never
~~~

See github-action/README.md for the full guide. Nova is LLM-free and local-first; static heuristics require human review and do not prove exploitability. MIT licensed.
