"""Small, explicit session context; no background collection."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class SessionContext:
    last_intent: str | None = None
    last_entities: dict[str, str] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: timedelta = timedelta(minutes=10)

    def remember(self, intent_name: str, entities: dict[str, str]) -> None:
        self.last_intent = intent_name
        self.last_entities = dict(entities)
        self.updated_at = datetime.now(timezone.utc)

    def active(self) -> bool:
        return datetime.now(timezone.utc) - self.updated_at < self.ttl

    def clear(self) -> None:
        self.last_intent = None
        self.last_entities.clear()
        self.updated_at = datetime.now(timezone.utc)
