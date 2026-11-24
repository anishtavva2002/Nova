from nova.config import NovaConfig
from nova.intent import IntentParser
from nova.learning import LearningEngine
from nova.memory import MemoryStore
from nova.models import SkillResult
from nova.policy import PolicyGate
from nova.skills.builtin import build_registry

class NovaApp:
    def __init__(self) -> None:
        self.config = NovaConfig.load()
        self.memory = MemoryStore(self.config.database_path)
        self.learning = LearningEngine(self.memory)
        self.parser = IntentParser(self.learning.rules())
        self.policy = PolicyGate()
        self.skills = build_registry()
        self.running = True

    def handle(self, text: str) -> SkillResult:
        intent = self.parser.parse(text)
        if intent.name == "exit":
            self.running = False
            return SkillResult(True, "Goodbye.")
        if intent.name == "unknown":
            return SkillResult(False, "I don't understand that yet. Type 'help' to see available commands.")
        skill = self.skills.get(intent.name)
        if skill is None:
            return SkillResult(False, f"No skill is registered for '{intent.name}'.")
        if not self.policy.allows(skill.permission):
            return SkillResult(False, "Permission denied for this action.")
        return skill.execute(intent, self.memory)

    def run(self) -> None:
        print("Nova v0.1 — local, LLM-free assistant")
        print("Type 'help' for commands. Type 'exit' to quit.")
        while self.running:
            try:
                text = input("\nYou > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nNova > Goodbye.")
                break
            if text:
                print(f"Nova > {self.handle(text).message}")
