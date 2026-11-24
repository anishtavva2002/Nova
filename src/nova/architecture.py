"""Shared contracts for Nova's deterministic, domain-oriented core."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Domain(str, Enum):
    PERSONAL = "personal"
    ENVIRONMENT = "environment"
    DEVELOPER = "developer"
    SYSTEM = "system"


class Capability(str, Enum):
    PERSONAL = "personal"
    SYSTEM_READ = "system.read"
    FILESYSTEM_READ = "filesystem.read"
    PROJECT_INSPECT = "project.inspect"
    FILESYSTEM_WRITE = "filesystem.write"
    PROCESS_EXECUTE = "process.execute"
    NETWORK_ACCESS = "network.access"


@dataclass(frozen=True)
class PlanStep:
    action: str
    description: str
    arguments: dict[str, Any] = field(default_factory=dict)
    capability: Capability = Capability.PERSONAL


@dataclass(frozen=True)
class ActionPlan:
    domain: Domain
    goal: str
    steps: tuple[PlanStep, ...]
    requires_confirmation: bool = False


@dataclass
class ActionOutcome:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReport:
    plan: ActionPlan
    outcomes: list[ActionOutcome]
    blocked: bool = False

    @property
    def success(self) -> bool:
        return bool(self.outcomes) and all(item.success for item in self.outcomes) and not self.blocked
