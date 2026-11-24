from datetime import datetime
from urllib.parse import urlparse
from nova.calculator import calculate
from nova.learning import LearningEngine
from nova.memory import MemoryStore
from nova.models import Intent, Permission, SkillResult
from nova.skills.registry import SkillRegistry


class HelpSkill:
    name, permission = "help", Permission.NONE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, "Try: time, date, remember <text>, show my notes, search notes for <text>, delete note <id>, add task <text>, show my tasks, complete task <id>, calculate <expression>, open <https-url>, teach \"phrase\" as help, exit.")


class TimeSkill:
    name, permission = "time", Permission.NONE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, datetime.now().astimezone().strftime("It is %I:%M %p (%Z)."))


class DateSkill:
    name, permission = "date", Permission.NONE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, datetime.now().astimezone().strftime("Today is %A, %d %B %Y."))


class NoteAddSkill:
    name, permission = "note.add", Permission.MEMORY_WRITE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, f"Saved note #{memory.add_note(intent.entities['content'])}.")


class NoteListSkill:
    name, permission = "note.list", Permission.MEMORY_READ
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        rows = memory.list_notes()
        message = "\n".join(f"#{r['id']}: {r['content']}" for r in rows) if rows else "You have no saved notes."
        return SkillResult(True, message, {"notes": rows})


class NoteSearchSkill:
    name, permission = "note.search", Permission.MEMORY_READ
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        rows = memory.search_notes(intent.entities['query'])
        message = "\n".join(f"#{r['id']}: {r['content']}" for r in rows) if rows else "No matching notes found."
        return SkillResult(True, message, {"notes": rows})


class NoteDeleteSkill:
    name, permission = "note.delete", Permission.MEMORY_DELETE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        note_id = int(intent.entities['id'])
        existing = any(note["id"] == note_id for note in memory.list_notes(limit=500))
        if not existing:
            return SkillResult(False, f"No note found with ID #{note_id}.")
        return SkillResult(True, f"Delete note #{note_id}? Type yes to confirm or no to cancel.", {"note_id": note_id}, confirmation_required=True, confirmation_token="delete_note")


class TaskAddSkill:
    name, permission = "task.add", Permission.MEMORY_WRITE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        return SkillResult(True, f"Added task #{memory.add_task(intent.entities['content'])}.")


class TaskListSkill:
    name, permission = "task.list", Permission.MEMORY_READ
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        rows = memory.list_tasks("open")
        message = "\n".join(f"#{r['id']}: {r['content']}" for r in rows) if rows else "You have no open tasks."
        return SkillResult(True, message, {"tasks": rows})


class TaskListDoneSkill:
    name, permission = "task.list_done", Permission.MEMORY_READ
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        rows = memory.list_tasks("done")
        message = "\n".join(f"#{r['id']}: {r['content']}" for r in rows) if rows else "You have no completed tasks."
        return SkillResult(True, message, {"tasks": rows})


class TaskCompleteSkill:
    name, permission = "task.complete", Permission.MEMORY_WRITE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        task_id = int(intent.entities['id'])
        ok = memory.complete_task(task_id)
        return SkillResult(ok, f"Completed task #{task_id}." if ok else f"No open task found with ID #{task_id}.")


class CalculatorSkill:
    name, permission = "calculate", Permission.NONE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        try:
            value = calculate(intent.entities['expression'])
            return SkillResult(True, f"The result is {value}.", {"result": value})
        except ValueError as exc:
            return SkillResult(False, str(exc))


class OpenUrlSkill:
    name, permission = "open.url", Permission.EXTERNAL_OPEN
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        url = intent.entities['url']
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return SkillResult(False, "Only valid HTTP/HTTPS URLs without embedded credentials can be opened.")
        return SkillResult(True, f"Open this link? {url}", {"url": url}, confirmation_required=True, confirmation_token="open_url")


class AliasLearnSkill:
    name, permission = "learn.alias", Permission.MEMORY_WRITE
    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult:
        learner = LearningEngine(memory)
        try:
            learner.approve_alias(intent.entities['phrase'], intent.entities['target'])
        except ValueError as exc:
            return SkillResult(False, str(exc))
        return SkillResult(True, f"Learned that '{intent.entities['phrase']}' means '{intent.entities['target']}'.")


def build_registry() -> SkillRegistry:
    registry = SkillRegistry()
    skills = [HelpSkill(), TimeSkill(), DateSkill(), NoteAddSkill(), NoteListSkill(), NoteSearchSkill(), NoteDeleteSkill(), TaskAddSkill(), TaskListSkill(), TaskListDoneSkill(), TaskCompleteSkill(), CalculatorSkill(), OpenUrlSkill(), AliasLearnSkill()]
    for skill in skills:
        registry.register(skill)
    return registry
