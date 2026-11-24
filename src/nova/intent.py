"""Deterministic intent recognition; user text is never treated as code."""
import re
from nova.models import Intent


class IntentParser:
    LEARNABLE = {"help", "time", "date", "note.list", "task.list"}

    def __init__(self, aliases: dict[str, str] | None = None) -> None:
        self.aliases = aliases or {}

    def parse(self, text: str) -> Intent:
        raw = text.strip()
        normalized = " ".join(raw.casefold().split())
        if not normalized:
            return Intent("unknown", 0.0)
        if normalized in self.aliases:
            target = self.aliases[normalized]
            if target in self.LEARNABLE:
                return Intent(target, 0.99, source="approved-alias")
        if normalized in {"exit", "quit", "goodbye", "stop nova", "close nova"}:
            return Intent("exit", 1.0)
        if normalized in {"help", "what can you do", "show commands", "commands"}:
            return Intent("help", 1.0)
        if normalized in {"what time is it", "tell me the time", "current time", "time", "time now"}:
            return Intent("time", 0.98)
        if normalized in {"what is today's date", "what is the date", "today's date", "date today", "what day is it"}:
            return Intent("date", 0.98)
        match = re.match(r"^(?:remember|save note|note|make a note)\s+(.+)$", raw, re.I)
        if match:
            return Intent("note.add", 0.98, {"content": match.group(1).strip()})
        if normalized in {"show my notes", "list notes", "read my notes", "my notes", "show notes"}:
            return Intent("note.list", 0.98)
        match = re.match(r"^(?:search notes for|find note about|search my notes for)\s+(.+)$", raw, re.I)
        if match:
            return Intent("note.search", 0.96, {"query": match.group(1).strip()})
        match = re.match(r"^(?:delete|remove) note\s+#?(\d+)$", normalized)
        if match:
            return Intent("note.delete", 0.99, {"id": match.group(1)})
        match = re.match(r"^(?:add task|create task|remind me to|new task)\s+(.+)$", raw, re.I)
        if match:
            return Intent("task.add", 0.97, {"content": match.group(1).strip()})
        if normalized in {"show my tasks", "list tasks", "my tasks", "show tasks", "what are my tasks"}:
            return Intent("task.list", 0.98)
        match = re.match(r"^(?:complete|finish|done with) task\s+#?(\d+)$", normalized)
        if match:
            return Intent("task.complete", 0.99, {"id": match.group(1)})
        if normalized in {"show completed tasks", "list completed tasks"}:
            return Intent("task.list_done", 0.98)
        match = re.match(r"^(?:calculate|compute|what is)\s+(.+)$", raw, re.I)
        if match:
            return Intent("calculate", 0.95, {"expression": match.group(1).strip()})
        match = re.match(r"^open\s+(https?://\S+)$", raw, re.I)
        if match:
            return Intent("open.url", 0.99, {"url": match.group(1).rstrip(".,!?;:")})
        match = re.match(r'^teach\s+["\'](.+)["\']\s+as\s+([a-z.]+)$', raw, re.I)
        if match:
            return Intent("learn.alias", 0.99, {"phrase": match.group(1), "target": match.group(2).casefold()})
        return Intent("unknown", 0.0)
