"""Policy-mediated execution for Nova's built-in read-only actions."""
from pathlib import Path
import os
import platform
import subprocess
from collections import Counter

from nova.architecture import ActionOutcome, ActionPlan, Capability, ExecutionReport


class PermissionPolicy:
    DEFAULT_GRANTED = {
        Capability.PERSONAL, Capability.SYSTEM_READ,
        Capability.FILESYSTEM_READ, Capability.PROJECT_INSPECT,
    }

    def __init__(self, granted: set[Capability] | None = None) -> None:
        self.granted = set(self.DEFAULT_GRANTED if granted is None else granted)

    def allows(self, capability: Capability) -> bool:
        return capability in self.granted


class ActionExecutor:
    SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}

    def __init__(self, policy: PermissionPolicy | None = None) -> None:
        self.policy = policy or PermissionPolicy()

    def execute(self, plan: ActionPlan) -> ExecutionReport:
        outcomes: list[ActionOutcome] = []
        for step in plan.steps:
            if not self.policy.allows(step.capability):
                outcomes.append(ActionOutcome(False, f"Blocked by policy: {step.capability.value}"))
                return ExecutionReport(plan, outcomes, blocked=True)
            try:
                outcomes.append(self._dispatch(step.action, step.arguments))
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                outcomes.append(ActionOutcome(False, f"Action failed safely: {exc}"))
                return ExecutionReport(plan, outcomes)
        return ExecutionReport(plan, outcomes)

    def _dispatch(self, action: str, args: dict) -> ActionOutcome:
        if action == "system.info":
            return ActionOutcome(True, "System information collected.", {
                "os": platform.platform(), "python": platform.python_version(),
                "architecture": platform.machine(), "processor": platform.processor() or "unknown",
            })
        if action == "files.list":
            path = self._directory(args["path"])
            entries = []
            for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))[:200]:
                if item.name in self.SKIP_DIRS or item.name.startswith("."):
                    continue
                entries.append({"name": item.name, "type": "directory" if item.is_dir() else "file"})
            return ActionOutcome(True, f"Found {len(entries)} visible entries in {path}.", {"path": str(path), "entries": entries})
        if action == "files.find":
            path = self._directory(args["path"])
            pattern = args["pattern"]
            if not pattern or len(pattern) > 120 or any(c in pattern for c in ("/", "\\\\")):
                raise ValueError("Use a filename or glob pattern of at most 120 characters.")
            matches = []
            for current, dirs, names in os.walk(path):
                dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")]
                for name in names:
                    if Path(name).match(pattern):
                        matches.append(str(Path(current) / name))
                        if len(matches) >= 100:
                            break
                if len(matches) >= 100:
                    break
            return ActionOutcome(True, f"Found {len(matches)} matching file(s).", {"matches": matches, "truncated": len(matches) == 100})
        if action == "project.inspect":
            root = self._directory(args["path"])
            counts: Counter[str] = Counter()
            files = []
            for current, dirs, names in os.walk(root):
                dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")]
                for name in names:
                    suffix = Path(name).suffix.lower() or "[no extension]"
                    counts[suffix] += 1
                    if len(files) < 30:
                        files.append(str((Path(current) / name).relative_to(root)))
            git_status = None
            if (root / ".git").exists():
                completed = subprocess.run(
                    ["git", "status", "--short"], cwd=root, capture_output=True,
                    text=True, timeout=8, check=False, shell=False,
                )
                git_status = completed.stdout.strip() if completed.returncode == 0 else "Git status unavailable."
            return ActionOutcome(True, f"Inspected {root}: {sum(counts.values())} file(s).",
                {"root": str(root), "file_count": sum(counts.values()),
                 "extensions": dict(counts.most_common()), "sample_files": files,
                 "sample_truncated": sum(counts.values()) > len(files), "git_status": git_status,
                 "execution_performed": False})
        raise ValueError(f"Unknown action: {action}")

    @staticmethod
    def _directory(value: str) -> Path:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Expected a directory: {path}")
        return path
