"""Unified Nova entry point: deterministic routing, planning, policy and execution."""
from nova.architecture import ActionPlan, Domain, ExecutionReport
from nova.app import NovaApp
from nova.execution import ActionExecutor, PermissionPolicy
from nova.planning import Planner


class NovaEngine:
    def __init__(self, personal_app: NovaApp | None = None,
                 executor: ActionExecutor | None = None) -> None:
        self.personal = personal_app or NovaApp()
        self.planner = Planner()
        self.executor = executor or ActionExecutor(PermissionPolicy())

    def handle(self, text: str) -> str:
        plan = self.planner.build(text)
        if plan is None:
            return self.personal.handle(text).message
        report = self.executor.execute(plan)
        self.personal.memory.audit("unified_action", f"{plan.domain.value}: {plan.goal}; success={report.success}")
        return self._format(report)

    @staticmethod
    def _format(report: ExecutionReport) -> str:
        lines = [f"Plan: {report.plan.goal}"]
        for outcome in report.outcomes:
            lines.append(outcome.message)
            if "os" in outcome.data:
                lines.extend(f"{key}: {value}" for key, value in outcome.data.items())
            if "entries" in outcome.data:
                lines.extend(f"{'📁' if item['type'] == 'directory' else '📄'} {item['name']}" for item in outcome.data["entries"])
            if "matches" in outcome.data:
                lines.extend(outcome.data["matches"])
                if outcome.data.get("truncated"):
                    lines.append("Result limit reached (100).")
            if "file_count" in outcome.data:
                data = outcome.data
                lines.append(f"Files: {data['file_count']}")
                lines.append("Extensions: " + ", ".join(f"{k}={v}" for k, v in data["extensions"].items()))
                lines.append("Sample: " + ", ".join(data["sample_files"]))
                if data["git_status"] is not None:
                    lines.append("Git status: " + (data["git_status"] or "clean"))
                lines.append("Project code was not executed or modified.")
        if report.blocked:
            lines.append("No action was performed.")
        return "\n".join(lines)
