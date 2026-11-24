# Nova v1.0

A local-first, LLM-free personal assistant built in Python. No LLM, cloud account, or network connection is required for core features.

## Features
- Interactive text CLI and deterministic intent parser with natural phrase variants.
- Local SQLite memory for notes, tasks, approved aliases, and audit history.
- User-approved learning: teach a phrase to map to a fixed supported intent.
- Skills for time/date, notes, tasks, safe arithmetic, and validated URL opening.
- Permission checks and confirmation before deleting notes or opening external links.
- Restricted AST calculator; no eval or exec.
- Optional offline speech recognition through Vosk and sounddevice.
- No arbitrary shell execution or autonomous code modification.

## Requirements
Python 3.11+. Optional voice requires the voice extras and a local Vosk model.

## Windows installation
    git clone https://github.com/anishtavva2002/Nova.git
    cd Nova
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    nova

Alternatively run: python -m nova

## Example commands
- help
- what time is it
- what is today's date
- remember My Nova project is local-first
- show my notes
- search notes for Nova
- delete note 1 (confirmation required)
- add task Finish Nova v1 tests
- show my tasks
- complete task 1
- calculate (12 * 8) + 4
- teach "launch nova" as help
- open https://github.com/anishtavva2002/Nova (confirmation required)
- exit

## Optional offline voice
Install with python -m pip install -e ".[voice]". Download a Vosk model from https://alphacephei.com/vosk/models, extract it, set NOVA_VOSK_MODEL to that directory, then run nova --voice. Microphone capture only occurs while voice mode is active. Speech output remains text in this release.

## Local data
SQLite database: ~/.nova/nova.db by default. Set NOVA_HOME to use another directory. Notes, tasks, aliases, and audit events remain on the local machine.

## Safety
Skills declare permissions. External URL opening and note deletion require explicit confirmation. URLs must use HTTP or HTTPS and cannot contain embedded credentials. Arithmetic accepts only numeric constants and approved arithmetic operators. User phrases are data, never code. Learning is restricted to a small allowlist of parameter-free intents.

## Architecture
Interface -> deterministic intent parser -> policy gate -> skill registry -> SQLite memory.
Optional offline voice feeds transcripts into the same command path.

## Development
Run tests with python -m pytest. See docs/ARCHITECTURE.md, docs/COMMANDS.md, and docs/ROADMAP.md.
