from nova.app import NovaApp


def test_note_task_and_alias_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    app = NovaApp()
    assert app.handle("remember project Nova").success
    assert "project Nova" in app.handle("show my notes").message
    assert app.handle("add task write tests").success
    assert "write tests" in app.handle("show my tasks").message
    assert app.handle('teach "start Nova" as help').success
    assert app.handle("start Nova").success


def test_confirmation_cancelled(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    app = NovaApp()
    pending = app.handle("open https://example.com")
    assert pending.confirmation_required
    assert app.handle("no").success
    assert app.pending_confirmation is None


def test_note_deletion_requires_confirmation(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    app = NovaApp()
    app.handle("remember private test note")
    request = app.handle("delete note 1")
    assert request.confirmation_required
    app.handle("no")
    assert len(app.memory.list_notes()) == 1
    request = app.handle("delete note 1")
    assert request.confirmation_required
    assert app.handle("yes").success
    assert app.memory.list_notes() == []


def test_exit(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    app = NovaApp()
    assert app.handle("exit").success
    assert not app.running
