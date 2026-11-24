"""Local, explicit long-term memory and contextual intelligence for Nova.

No model calls, telemetry, background collection, or code execution occur here.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MemoryFact:
    id: int
    key: str
    value: str
    category: str
    confidence: float
    source: str
    updated_at: str


@dataclass(frozen=True)
class ConversationContext:
    topic: str | None = None
    entity: str | None = None
    intent: str | None = None
    updated_at: datetime | None = None


class IntelligenceStore:
    """Separate SQLite store for facts, conversation history and feedback."""

    def __init__(self, database_path: Path) -> None:
        self.path = Path(database_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    value TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0 AND confidence <= 1),
                    source TEXT NOT NULL DEFAULT 'user-approved',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_text TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    intent TEXT NOT NULL DEFAULT 'unknown',
                    topic TEXT,
                    entity TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_turns_created ON turns(created_at DESC);
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_text TEXT NOT NULL,
                    correction TEXT NOT NULL,
                    target_intent TEXT,
                    approved INTEGER NOT NULL DEFAULT 0 CHECK(approved IN (0,1)),
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT
                );
            """)

    def remember(self, key: str, value: str, *, category: str = "general",
                 confidence: float = 1.0, source: str = "user-approved") -> int:
        key, value, category = key.strip(), value.strip(), category.strip().casefold()
        if not key or len(key) > 160:
            raise ValueError("Memory key must contain 1–160 characters.")
        if not value or len(value) > 4000:
            raise ValueError("Memory value must contain 1–4000 characters.")
        if not category or len(category) > 80:
            raise ValueError("Memory category must contain 1–80 characters.")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1.")
        timestamp = _now()
        with self._connect() as db:
            db.execute("""INSERT INTO facts(key,value,category,confidence,source,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET
                value=excluded.value, category=excluded.category,
                confidence=excluded.confidence, source=excluded.source,
                updated_at=excluded.updated_at""",
                (key, value, category, confidence, source[:80], timestamp, timestamp))
            row = db.execute("SELECT id FROM facts WHERE key=?", (key,)).fetchone()
            return int(row["id"])

    def recall(self, query: str, *, category: str | None = None, limit: int = 10) -> list[MemoryFact]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 50))
        pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        with self._connect() as db:
            if category:
                rows = db.execute("""SELECT * FROM facts WHERE category=? AND
                    (key LIKE ? ESCAPE '\\' OR value LIKE ? ESCAPE '\\')
                    ORDER BY confidence DESC, updated_at DESC LIMIT ?""",
                    (category.casefold(), pattern, pattern, limit)).fetchall()
            else:
                rows = db.execute("""SELECT * FROM facts WHERE
                    key LIKE ? ESCAPE '\\' OR value LIKE ? ESCAPE '\\'
                    ORDER BY confidence DESC, updated_at DESC LIMIT ?""",
                    (pattern, pattern, limit)).fetchall()
            ids = [int(row["id"]) for row in rows]
            if ids:
                db.executemany("UPDATE facts SET access_count=access_count+1 WHERE id=?", [(i,) for i in ids])
        return [MemoryFact(int(r["id"]), r["key"], r["value"], r["category"],
                           float(r["confidence"]), r["source"], r["updated_at"]) for r in rows]

    def forget(self, key: str) -> bool:
        with self._connect() as db:
            cur = db.execute("DELETE FROM facts WHERE key=?", (key.strip(),))
            return cur.rowcount == 1

    def record_turn(self, user_text: str, response_text: str, *, intent: str = "unknown",
                    topic: str | None = None, entity: str | None = None) -> int:
        if not user_text.strip():
            raise ValueError("User text cannot be empty.")
        with self._connect() as db:
            cur = db.execute("""INSERT INTO turns(user_text,response_text,intent,topic,entity,created_at)
                VALUES(?,?,?,?,?,?)""", (user_text[:4000], response_text[:4000], intent[:80],
                topic[:160] if topic else None, entity[:240] if entity else None, _now()))
            return int(cur.lastrowid)

    def recent_turns(self, limit: int = 20) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        with self._connect() as db:
            rows = db.execute("SELECT * FROM turns ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def submit_feedback(self, original_text: str, correction: str,
                        target_intent: str | None = None) -> int:
        if not original_text.strip() or not correction.strip():
            raise ValueError("Both the original request and correction are required.")
        with self._connect() as db:
            cur = db.execute("""INSERT INTO feedback(original_text,correction,target_intent,created_at)
                VALUES(?,?,?,?)""", (original_text[:4000], correction[:1000],
                target_intent[:80] if target_intent else None, _now()))
            return int(cur.lastrowid)

    def review_feedback(self, feedback_id: int, *, approve: bool) -> bool:
        with self._connect() as db:
            cur = db.execute("UPDATE feedback SET approved=?, reviewed_at=? WHERE id=? AND reviewed_at IS NULL",
                             (1 if approve else 0, _now(), feedback_id))
            return cur.rowcount == 1

    def pending_feedback(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        with self._connect() as db:
            rows = db.execute("SELECT * FROM feedback WHERE reviewed_at IS NULL ORDER BY id LIMIT ?",
                              (limit,)).fetchall()
        return [dict(row) for row in rows]


class ContextEngine:
    """Short-lived conversational context with explicit TTL and safe resolution."""
    FOLLOW_UPS = {"it", "that", "this", "there", "those", "them", "the same", "same one"}

    def __init__(self, ttl: timedelta = timedelta(minutes=15)) -> None:
        self.ttl = ttl
        self._context = ConversationContext()

    def update(self, *, topic: str | None, entity: str | None, intent: str | None) -> None:
        self._context = ConversationContext(topic, entity, intent, datetime.now(timezone.utc))

    def current(self) -> ConversationContext:
        stamp = self._context.updated_at
        if stamp is None or datetime.now(timezone.utc) - stamp > self.ttl:
            self.clear()
        return self._context

    def resolve_reference(self, text: str) -> str | None:
        """Return the recent entity only for an obvious short follow-up."""
        clean = " ".join(text.casefold().strip().split())
        if not clean or len(clean.split()) > 8:
            return None
        words = set(clean.replace("?", "").replace(".", "").split())
        if not (words & self.FOLLOW_UPS):
            return None
        return self.current().entity

    def clear(self) -> None:
        self._context = ConversationContext()


class FeedbackEngine:
    """Collects corrections for review; never changes parser behavior automatically."""
    def __init__(self, store: IntelligenceStore, allowed_intents: Iterable[str]) -> None:
        self.store = store
        self.allowed_intents = frozenset(allowed_intents)

    def suggest(self, original_text: str, correction: str, target_intent: str | None = None) -> int:
        if target_intent is not None and target_intent not in self.allowed_intents:
            raise ValueError("The suggested intent is not in Nova's approved intent catalogue.")
        return self.store.submit_feedback(original_text, correction, target_intent)

    def approve(self, feedback_id: int) -> bool:
        return self.store.review_feedback(feedback_id, approve=True)

    def reject(self, feedback_id: int) -> bool:
        return self.store.review_feedback(feedback_id, approve=False)
