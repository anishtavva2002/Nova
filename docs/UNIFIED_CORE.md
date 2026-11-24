# Nova Unified Core (v1.1)

Nova is organized around three domains sharing one deterministic core:

- **Personal:** notes, tasks, approved phrase learning, time/date and calculator.
- **Environment:** read-only system information, directory listing and filename search.
- **Developer:** read-only project inventory and Git status inspection.

## Request lifecycle

`text -> deterministic planner -> typed ActionPlan -> permission policy -> executor -> report -> local audit`

Unrecognized commands fall through to the original personal assistant. User text is parsed as data; it is never passed to a shell, eval, exec, or an LLM.

## Safety model

- Capabilities are explicit and default grants are limited to personal memory and read-only inspection.
- File operations are bounded (200 directory entries, 100 search results).
- Searches skip hidden folders and common dependency/cache directories.
- Project inspection may invoke only a fixed `git status --short` argument vector, with `shell=False` and a timeout.
- No project code is run, edited, deleted, uploaded, or committed.
- Process execution, filesystem writes, network access, browser automation and application launching are not enabled.

## Extending Nova

Add a typed action to the planner, declare the minimum capability, implement a narrow handler in the executor, and test both the allowed and denied paths. Do not give skills direct access to arbitrary shell commands. Aegis remains a separate isolation service; a future adapter may request isolated execution through an explicit contract.

## Commands

- `system status`
- `list files <directory>`
- `find files *.py in <directory>`
- `inspect project <directory>`

Run `nova --unified` to use the unified router. Existing `nova` commands remain available.
