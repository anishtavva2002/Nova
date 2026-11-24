# Nova v1.1 — Unified Local Assistant

Nova is a local-first, deterministic assistant with three connected domains: personal productivity, operating-environment awareness and developer project inspection. The core requires no LLM, cloud account or network connection.

## Current capabilities

**Personal**
- SQLite notes, tasks, approved aliases and audit history.
- Time/date, safe arithmetic, notes, tasks and confirmation-gated URL opening/deletion.
- Optional offline speech recognition through Vosk.

**Environment**
- Read-only OS/runtime information.
- Bounded directory listing and filename search.

**Developer**
- Read-only project inventory, file-extension summary and Git status.
- Project code is never executed or modified by inspection.

## Install on Windows

```powershell
git clone https://github.com/anishtavva2002/Nova.git
cd Nova
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the original personal assistant with `nova`, or the unified router with:

```powershell
nova --unified
```

Run tests:

```powershell
python -m pytest
```

## Unified commands

- `system status`
- `list files .`
- `find files *.py in .`
- `inspect project .`

All original personal commands remain available in unified mode. See [docs/UNIFIED_CORE.md](docs/UNIFIED_CORE.md), [architecture](docs/ARCHITECTURE.md), [commands](docs/COMMANDS.md) and [roadmap](docs/ROADMAP.md).

## Architecture and safety

`Interface -> deterministic planner -> typed plan -> permission policy -> executor -> structured report`

Unknown commands are delegated to the existing personal assistant. Read operations are bounded. No LLM, arbitrary shell execution, autonomous code edits, background monitoring or network actions are enabled. Higher-risk capabilities require dedicated adapters, explicit permission and tests before they are added.

Aegis remains a separate security/isolation project; future integration will use a narrow adapter contract.
