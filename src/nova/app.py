from nova.config import NovaConfig
from nova.context import SessionContext
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
        self.parser = IntentParser(self.learning.aliases())
        self.policy = PolicyGate()
        self.skills = build_registry()
        self.context = SessionContext()
        self.running = True
        self.pending_confirmation: tuple[str, dict] | None = None

    def handle(self, text: str) -> SkillResult:
        raw = text.strip()
        if not raw:
            return SkillResult(False, "Please enter a command.")
        if self.pending_confirmation:
            return self._handle_confirmation(raw)
        intent = self.parser.parse(raw)
        if intent.name == "exit":
            self.running = False
            return SkillResult(True, "Goodbye. Your local memory is saved.")
        if intent.name == "unknown":
            self.memory.audit("unrecognized", raw)
            return SkillResult(False, "I don't recognize that command yet. Type 'help' for examples, or teach me a supported phrase.")
        skill = self.skills.get(intent.name)
        if skill is None:
            return SkillResult(False, "That capability is not installed.")
        if not self.policy.allows(skill.permission):
            self.memory.audit("denied", intent.name)
            return SkillResult(False, "Permission denied by Nova's local policy.")
        result = skill.execute(intent, self.memory)
        self.memory.audit("skill", f"{intent.name}: {'success' if result.success else 'failure'}")
        self.context.remember(intent.name, intent.entities)
        if result.confirmation_required:
            self.pending_confirmation = (intent.name, result.data)
        if intent.name == "learn.alias" and result.success:
            self.parser = IntentParser(self.learning.aliases())
        return result

    def _handle_confirmation(self, answer: str) -> SkillResult:
        pending = self.pending_confirmation
        self.pending_confirmation = None
        if answer.casefold() not in {"yes", "y", "confirm"}:
            self.memory.audit("confirmation_cancelled", pending[0])
            return SkillResult(True, "Cancelled. No action was taken.")
        if pending[0] == "open.url":
            import webbrowser
            url = pending[1]["url"]
            try:
                opened = webbrowser.open(url, new=2)
            except Exception:
                opened = False
            self.memory.audit("external_open", url if opened else "browser launch failed")
            return SkillResult(bool(opened), "Opening the link in your browser." if opened else "I couldn't open the link on this device.")
        if pending[0] == "note.delete":
            note_id = pending[1]["note_id"]
            deleted = self.memory.delete_note(note_id)
            self.memory.audit("note_delete", f"#{note_id}: {'deleted' if deleted else 'not found'}")
            return SkillResult(deleted, f"Deleted note #{note_id}." if deleted else f"Note #{note_id} no longer exists.")
        return SkillResult(False, "Confirmation expired or action is unsupported.")

    def run(self) -> None:
        print("Nova v1.0 | Local-first | LLM-free")
        print("Type 'help' for commands. Type 'exit' to quit.")
        while self.running:
            try:
                text = input("\nYou > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nNova > Goodbye.")
                break
            if text:
                result = self.handle(text)
                print(f"Nova > {result.message}")
