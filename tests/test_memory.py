from nova.memory import MemoryStore


def test_notes_tasks_aliases_and_audit(tmp_path):
    store = MemoryStore(tmp_path / "nova.db")
    note_id = store.add_note("Nova is local-first")
    assert store.search_notes("local")[0]["id"] == note_id
    assert store.delete_note(note_id)
    task_id = store.add_task("Ship Nova v1")
    assert store.complete_task(task_id)
    assert store.list_tasks("done")[0]["id"] == task_id
    store.save_alias("start nova", "help")
    assert store.get_aliases() == {"start nova": "help"}
    store.audit("test", "ok")
    assert store.recent_audit()[0]["detail"] == "ok"


def test_search_escapes_like_wildcards(tmp_path):
    store = MemoryStore(tmp_path / "nova.db")
    store.add_note("100% ready")
    assert len(store.search_notes("%")) == 1
    assert store.search_notes("_not_present_") == []
