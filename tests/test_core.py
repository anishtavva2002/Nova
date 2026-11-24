from nova.app import NovaApp
from nova.intent import IntentParser
from nova.memory import MemoryStore
from nova.models import Permission
from nova.policy import PolicyGate

def test_intent_parser():
    parser = IntentParser()
    assert parser.parse("help").name == "help"
    assert parser.parse("what time is it").name == "time"
    assert parser.parse("remember call the team").entities["content"] == "call the team"
    assert parser.parse("show my notes").name == "note.list"
    assert parser.parse("nonsense").name == "unknown"

def test_memory_notes_and_learning(tmp_path):
    memory = MemoryStore(tmp_path / "nova.db")
    memory.add_note("Nova assistant project")
    assert memory.search_notes("assistant")[0]["content"] == "Nova assistant project"
    memory.approve_correction("start Nova", "help")
    assert memory.get_corrections() == {"start nova": "help"}

def test_policy_is_least_privilege():
    policy = PolicyGate()
    assert policy.allows(Permission.MEMORY_READ)
    assert not policy.allows(Permission.SYSTEM_WRITE)
    assert not policy.allows(Permission.NETWORK)

def test_app_note_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    app = NovaApp()
    assert app.handle("remember build Nova").success
    assert "build Nova" in app.handle("show my notes").message
    assert app.handle("exit").success
    assert not app.running
