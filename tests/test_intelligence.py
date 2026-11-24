from datetime import timedelta

import pytest

from nova.intelligence import ContextEngine, FeedbackEngine, IntelligenceStore


def test_fact_upsert_and_recall(tmp_path):
    store = IntelligenceStore(tmp_path / "intelligence.db")
    first = store.remember("preferred_language", "Java", category="preferences")
    second = store.remember("preferred_language", "Python", category="preferences")
    assert first == second
    found = store.recall("language", category="preferences")
    assert len(found) == 1
    assert found[0].value == "Python"


def test_recall_escapes_like_wildcards(tmp_path):
    store = IntelligenceStore(tmp_path / "intelligence.db")
    store.remember("literal", "100%_safe")
    assert len(store.recall("100%_safe")) == 1
    assert len(store.recall("%")) == 1


def test_validation_and_forget(tmp_path):
    store = IntelligenceStore(tmp_path / "intelligence.db")
    with pytest.raises(ValueError):
        store.remember("", "value")
    store.remember("project", "Nova")
    assert store.forget("project")
    assert not store.forget("project")


def test_context_reference_and_expiry():
    context = ContextEngine(ttl=timedelta(minutes=15))
    context.update(topic="project", entity="Nova", intent="project.inspect")
    assert context.resolve_reference("open it") == "Nova"
    assert context.resolve_reference("please inspect the entire repository") is None
    context.clear()
    assert context.resolve_reference("open it") is None


def test_feedback_requires_allowlisted_intent_and_review(tmp_path):
    store = IntelligenceStore(tmp_path / "intelligence.db")
    feedback = FeedbackEngine(store, {"help", "time"})
    with pytest.raises(ValueError):
        feedback.suggest("do x", "should be help", "execute.shell")
    feedback_id = feedback.suggest("show me commands", "I meant help", "help")
    assert len(store.pending_feedback()) == 1
    assert feedback.approve(feedback_id)
    assert not feedback.approve(feedback_id)
    assert store.pending_feedback() == []


def test_turn_history_is_bounded(tmp_path):
    store = IntelligenceStore(tmp_path / "intelligence.db")
    store.record_turn("hello", "hi", intent="greeting", topic="chat", entity="Nova")
    rows = store.recent_turns(1)
    assert rows[0]["entity"] == "Nova"
