"""SQLite session repository."""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from ...constants import SQLITE_DB_PATH
from ...infra.logging import logger


class SessionRepository:
    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._init_tables()
        return self._conn

    def _init_tables(self):
        conn = self._get_conn() if self._conn else sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '新会话',
                model_key TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                mode_override TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()

    def create(self, title: str = "新会话", model_key: str = "", system_prompt: str = "") -> dict:
        conn = self._get_conn()
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO sessions (id, title, model_key, system_prompt, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, title, model_key, system_prompt, now, now),
        )
        conn.commit()
        logger.debug("Created session: %s", session_id)
        return {"id": session_id, "title": title, "created_at": now, "updated_at": now}

    def get(self, session_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def list_all(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    def rename(self, session_id: str, new_title: str):
        conn = self._get_conn()
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (new_title, datetime.now().isoformat(), session_id),
        )
        conn.commit()

    def update(self, session_id: str, **kwargs):
        conn = self._get_conn()
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [datetime.now().isoformat(), session_id]
        conn.execute(f"UPDATE sessions SET {sets}, updated_at = ? WHERE id = ?", vals)
        conn.commit()

    def delete(self, session_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        logger.debug("Deleted session: %s", session_id)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
