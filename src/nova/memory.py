"""Local SQLite memory with parameterized queries."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MemoryStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL CHECK(length(trim(content)) > 0),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL CHECK(length(trim(content)) > 0),
                    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'done')),
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS aliases (
                    phrase TEXT PRIMARY KEY,
                    intent_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            db.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES ('schema_version', '1')")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_note(self, content: str) -> int:
        clean = content.strip()
        if not clean:
            raise ValueError("Note cannot be empty.")
        with self._connect() as db:
            cur = db.execute("INSERT INTO notes(content, created_at) VALUES (?, ?)", (clean, self._now()))
            return int(cur.lastrowid)

    def list_notes(self, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
        return [dict(row) for row in rows]

    def search_notes(self, query: str, limit: int = 50) -> list[dict]:
        clean = query.strip()
        if not clean:
            return []
        with self._connect() as db:
            rows = db.execute("SELECT id, content, created_at FROM notes WHERE content LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?", (self._like(clean), max(1, min(limit, 200)))).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _like(value: str) -> str:
        return "%" + value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    def delete_note(self, note_id: int) -> bool:
        with self._connect() as db:
            cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            return cur.rowcount > 0

    def add_task(self, content: str) -> int:
        clean = content.strip()
        if not clean:
            raise ValueError("Task cannot be empty.")
        with self._connect() as db:
            cur = db.execute("INSERT INTO tasks(content, created_at) VALUES (?, ?)", (clean, self._now()))
            return int(cur.lastrowid)

    def list_tasks(self, status: str = "open", limit: int = 100) -> list[dict]:
        if status not in {"open", "done", "all"}:
            raise ValueError("Invalid task status.")
        with self._connect() as db:
            if status == "all":
                rows = db.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
            else:
                rows = db.execute("SELECT * FROM tasks WHERE status = ? ORDER BY id DESC LIMIT ?", (status, max(1, min(limit, 500))).fetchall()
        return [dict(row) for row in rows]

    def complete_task(self, task_id: int) -> bool:
        with self._connect() as db:
            cur = db.execute("UPDATE tasks SET status='done', completed_at=? WHERE id=? AND status='open'", (self._now(), task_id))
            return cur.rowcount > 0

    def save_alias(self, phrase: str, intent_name: str) -> None:
        clean = " ".join(phrase.casefold().split())
        if not clean or len(clean) > 100:
            raise ValueError("Alias must contain 1–100 characters.")
        with self._connect() as db:
            db.execute("INSERT INTO aliases(phrase, intent_name, created_at) VALUES (?, ?, ?) ON CONFLICT(phrase) DO UPDATE SET intent_name=excluded.intent_name, created_at=excluded.created_at", (clean, intent_name, self._now()))

    def get_aliases(self) -> dict[str, str]:
        with self._connect() as db:
            rows = db.execute("SELECT phrase, intent_name FROM aliases").fetchall()
        return {row["phrase"]: row["intent_name"] for row in rows}

    def audit(self, event: str, detail: str) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO audit_events(event, detail, created_at) VALUES (?, ?, ?)", (event[:80], detail[:1000], self._now()))

    def recent_audit(self, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (max(1, min(limit, 200)),)).fetchall()
        return [dict(row) for row in rows]
