from datetime import datetime
from nova.memory import MemoryStore
from nova.models import Intent, Permission, SkillResult
from nova.skills.registry import SkillRegistry

class HelpSkill:
    name, permission = "help", Permission.NONE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, "Commands: help, what time is it, remember <text>, show my notes, search notes for <text>, exit.")

class TimeSkill:
    name, permission = "time", Permission.NONE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, datetime.now().astimezone().strftime("It is %I:%M %p on %A, %d %B %Y."))

class NoteCreateSkill:
    name, permission = "note.create", Permission.MEMORY_WRITE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        note_id = memory.add_note(intent.entities["content"])
        return SkillResult(True, f"Saved note #{note_id}.")

class NoteListSkill:
    name, permission = "note.list", Permission.MEMORY_READ
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        notes = memory.list_notes()
        return SkillResult(True, "\n".join(f"#{n['id']}: {n['content']}" for n in notes) if notes else "You do not have any notes yet.", {"notes": notes})

class NoteSearchSkill:
    name, permission = "note.search", Permission.MEMORY_READ
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        notes = memory.search_notes(intent.entities["query"])
        return SkillResult(True, "\n".join(f"#{n['id']}: {n['content']}" for n in notes) if notes else "I couldn't find a matching note.", {"notes": notes})

def build_registry() -> SkillRegistry:
    registry = SkillRegistry()
    for skill in (HelpSkill(), TimeSkill(), NoteCreateSkill(), NoteListSkill(), NoteSearchSkill()):
        registry.register(skill)
    return registry
