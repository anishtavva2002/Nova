from typing import Protocol
from nova.memory import MemoryStore
from nova.models import Intent, Permission, SkillResult


class Skill(Protocol):
    name: str
    permission: Permission

    def execute(self, intent: Intent, memory: MemoryStore) -> SkillResult: ...
