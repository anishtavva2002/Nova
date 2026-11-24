from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Permission(str, Enum):
    NONE = "none"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    MEMORY_DELETE = "memory.delete"
    EXTERNAL_OPEN = "external.open"


@dataclass(frozen=True)
class Intent:
    name: str
    confidence: float
    entities: dict[str, str] = field(default_factory=dict)
    source: str = "builtin"


@dataclass
class SkillResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    confirmation_required: bool = False
    confirmation_token: str | None = None
