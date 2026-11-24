# Nova

A local-first, LLM-free personal assistant built in Python.

## v0.1
- Text CLI
- Deterministic intent recognition
- Modular skill registry
- Policy gate with least-privilege defaults
- Local SQLite notes and explicitly approved intent corrections
- Unit tests

No LLM, cloud service, or arbitrary shell execution is required.

## Windows setup
```powershell
git clone https://github.com/anishtavva2002/Nova.git
cd Nova
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
nova
```
Alternatively run `python -m nova`.

## Commands
- `help`
- `what time is it`
- `remember <text>`
- `show my notes`
- `search notes for <text>`
- `exit`

Data is stored in `~/.nova/nova.db`. Set `NOVA_HOME` to change the location.

## Architecture
Text CLI → Intent Parser → Policy Gate → Skill Registry → Local SQLite Memory.

Learning is bounded: only explicit user-approved corrections are stored. Nova never modifies its own code. Voice, desktop automation, and Aegis integration are later milestones.
