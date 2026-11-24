from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Permission(str, Enum):
    NONE = "none"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    SYSTEM_READ = "system.read"
    SYSTEM_WRITE = "system.write"
    NETWORK = "network"

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
