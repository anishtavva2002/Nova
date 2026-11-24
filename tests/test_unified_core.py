from pathlib import Path

from nova.architecture import Capability
from nova.execution import ActionExecutor, PermissionPolicy
from nova.orchestrator import NovaEngine
from nova.planning import Planner


def test_router_builds_environment_plan():
    plan = Planner().build("system status")
    assert plan is not None
    assert plan.steps[0].action == "system.info"


def test_unknown_command_falls_through_to_personal_app(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    engine = NovaEngine()
    assert "don't recognize" in engine.handle("do something impossible").lower()


def test_project_inspection_is_read_only(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    plan = Planner().build(f"inspect project {tmp_path}")
    report = ActionExecutor().execute(plan)
    assert report.success
    assert report.outcomes[0].data["file_count"] == 1
    assert report.outcomes[0].data["execution_performed"] is False


def test_policy_blocks_ungranted_capability(tmp_path):
    plan = Planner().build(f"inspect project {tmp_path}")
    executor = ActionExecutor(PermissionPolicy(granted={Capability.PERSONAL}))
    report = executor.execute(plan)
    assert report.blocked
    assert not report.success


def test_file_search_skips_virtual_environment(tmp_path):
    (tmp_path / "main.py").write_text("", encoding="utf-8")
    hidden = tmp_path / ".venv"
    hidden.mkdir()
    (hidden / "secret.py").write_text("", encoding="utf-8")
    plan = Planner().build(f"find files *.py in {tmp_path}")
    report = ActionExecutor().execute(plan)
    assert report.success
    assert len(report.outcomes[0].data["matches"]) == 1


def test_path_must_exist():
    plan = Planner().build("list files Z:/this/path/should/not/exist")
    report = ActionExecutor().execute(plan)
    assert not report.success
