"""Deterministic command routing and plan construction. No user text is executed."""
import re
from pathlib import Path

from nova.architecture import ActionPlan, Capability, Domain, PlanStep


class CommandRouter:
    def route(self, text: str) -> ActionPlan | None:
        raw = text.strip()
        normalized = " ".join(raw.casefold().split())
        if normalized in {"system status", "system info", "computer status", "show system info"}:
            return ActionPlan(Domain.ENVIRONMENT, "Read basic system information", (
                PlanStep("system.info", "Read OS and runtime information", capability=Capability.SYSTEM_READ),
            ))
        match = re.fullmatch(r"(?:list|show) files(?: in)? (.+)", raw, re.I)
        if match:
            return ActionPlan(Domain.ENVIRONMENT, "List a directory", (
                PlanStep("files.list", "List directory entries", {"path": match.group(1).strip()}, Capability.FILESYSTEM_READ),
            ))
        match = re.fullmatch(r"find files? (.+?)(?: in (.+))?", raw, re.I)
        if match:
            pattern, path = match.group(1).strip(), (match.group(2) or ".").strip()
            return ActionPlan(Domain.ENVIRONMENT, "Find matching files", (
                PlanStep("files.find", "Search filenames without opening file contents",
                         {"pattern": pattern, "path": path}, Capability.FILESYSTEM_READ),
            ))
        match = re.fullmatch(r"inspect project (.+)", raw, re.I)
        if match:
            return ActionPlan(Domain.DEVELOPER, "Inspect a project without running its code", (
                PlanStep("project.inspect", "Summarize project structure and Git status",
                         {"path": match.group(1).strip()}, Capability.PROJECT_INSPECT),
            ))
        return None


class Planner:
    """Turns a routed request into an explicit, inspectable plan."""
    def build(self, text: str) -> ActionPlan | None:
        return CommandRouter().route(text)
