import sqlite3
from datetime import datetime, timezone
from pathlib import Path

class MemoryStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS corrections (phrase TEXT PRIMARY KEY, intent_name TEXT NOT NULL, created_at TEXT NOT NULL)")

    def _connect(self):
        db = sqlite3.connect(self.database_path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_note(self, content: str) -> int:
        content = content.strip()
        if not content:
            raise ValueError("Note cannot be empty.")
        with self._connect() as db:
            cur = db.execute("INSERT INTO notes(content, created_at) VALUES (?, ?)", (content, self._now()))
            return int(cur.lastrowid)

    def list_notes(self, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def search_notes(self, query: str, limit: int = 20) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT id, content, created_at FROM notes WHERE content LIKE ? ORDER BY id DESC LIMIT ?", (f"%{query.strip()}%", limit)).fetchall()
        return [dict(row) for row in rows]

    def approve_correction(self, phrase: str, intent_name: str) -> None:
        phrase = " ".join(phrase.casefold().split())
        if not phrase or not intent_name.strip():
            raise ValueError("Phrase and intent are required.")
        with self._connect() as db:
            db.execute("INSERT INTO corrections VALUES (?, ?, ?) ON CONFLICT(phrase) DO UPDATE SET intent_name=excluded.intent_name, created_at=excluded.created_at", (phrase, intent_name.strip(), self._now()))

    def get_corrections(self) -> dict[str, str]:
        with self._connect() as db:
            rows = db.execute("SELECT phrase, intent_name FROM corrections").fetchall()
        return {r["phrase"]: r["intent_name"] for r in rows}
