"""Inspectable deterministic intent parser; no generative model."""
import re
from nova.models import Intent

class IntentParser:
    def __init__(self, corrections: dict[str, str] | None = None) -> None:
        self.corrections = corrections or {}

    def parse(self, text: str) -> Intent:
        raw = text.strip()
        normalized = " ".join(raw.casefold().split())
        if not normalized:
            return Intent("unknown", 0.0)
        corrected = self.corrections.get(normalized)
        if corrected:
            return Intent(corrected, 0.99, source="approved-learning")
        if normalized in {"exit", "quit", "goodbye", "stop nova"}:
            return Intent("exit", 1.0)
        if normalized in {"help", "what can you do", "show commands"}:
            return Intent("help", 1.0)
        if normalized in {"what time is it", "tell me the time", "current time", "time"}:
            return Intent("time", 0.98)
        match = re.match(r"^(?:remember|save note|note)\s+(.+)$", raw, re.I)
        if match:
            return Intent("note.create", 0.98, {"content": match.group(1).strip()})
        if normalized in {"show my notes", "list notes", "read my notes", "my notes"}:
            return Intent("note.list", 0.98)
        match = re.match(r"^(?:search notes for|find note about)\s+(.+)$", raw, re.I)
        if match:
            return Intent("note.search", 0.96, {"query": match.group(1).strip()})
        return Intent("unknown", 0.0)
