from nova.intent import IntentParser
from nova.memory import MemoryStore


class LearningEngine:
    """User-approved aliases to a fixed allowlist; no self-modifying code."""
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def approve_alias(self, phrase: str, target: str) -> None:
        clean_target = target.casefold().strip()
        if clean_target not in IntentParser.LEARNABLE:
            raise ValueError(f"Target must be one of: {', '.join(sorted(IntentParser.LEARNABLE))}")
        self.memory.save_alias(phrase, clean_target)

    def aliases(self) -> dict[str, str]:
        return self.memory.get_aliases()
