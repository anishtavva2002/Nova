# Nova v1.2 — Local Intelligence Layer

This milestone adds a separate SQLite intelligence store, short-lived contextual references, and a human-reviewed feedback queue.

## Guarantees

- No LLM, cloud call, telemetry, or background collection.
- Long-term facts are stored only through explicit `remember` calls.
- Facts can be searched, updated by key, and deleted by key.
- Context expires after 15 minutes by default and can be cleared.
- Pronoun resolution is intentionally conservative: only short follow-ups containing a supported reference word resolve to the most recent entity.
- Feedback is inert until reviewed. Approval does not execute code or mutate parser behavior by itself.
- SQL uses parameterized statements; limits are bounded.

## Integration

Create `IntelligenceStore(NovaConfig.load().home / "intelligence.db")` beside the existing `MemoryStore`. The existing `nova.db` schema is untouched. Feed explicit user-approved facts and turn summaries into this store. Do not persist raw microphone audio.

Before activating an approved correction as a learned alias, validate its target against `IntentParser.LEARNABLE` and ask the user to confirm the exact phrase-to-intent mapping.
