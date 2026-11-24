# Nova architecture

## Request lifecycle
1. Interface receives text or an offline speech transcript.
2. Router checks approved aliases and deterministic intent patterns.
3. Ambiguous or unsupported requests are not executed.
4. Skill is resolved from the registry.
5. Policy gate checks the declared permission.
6. Skill performs bounded work through explicit interfaces.
7. Result and execution metadata are written to local audit history.

## Modules
- intent.py: deterministic phrase and entity recognition.
- context.py: short-lived session context.
- memory.py: SQLite schema and repository methods.
- learning.py: explicitly approved aliases to fixed built-in intents.
- policy.py: permission grants.
- calculator.py: restricted arithmetic AST evaluator.
- skills/: isolated skill implementations.
- app.py: application coordinator and CLI.
- voice.py: optional Vosk offline speech adapter.

## Extending Nova
Implement the Skill protocol, declare the minimum permission, register it in build_registry, and add tests. Keep side effects bounded. Never call a shell or evaluate user-provided code. Sensitive actions should require confirmation.
