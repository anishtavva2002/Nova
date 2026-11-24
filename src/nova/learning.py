from nova.memory import MemoryStore

class LearningEngine:
    """Only explicit user-approved corrections are retained; code is never self-modified."""
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def approve_intent_correction(self, phrase: str, intent_name: str) -> None:
        self.memory.approve_correction(phrase, intent_name)

    def rules(self) -> dict[str, str]:
        return self.memory.get_corrections()
