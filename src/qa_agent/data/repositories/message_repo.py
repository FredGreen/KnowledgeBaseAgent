"""SQLite message repository."""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from ...constants import SQLITE_DB_PATH
from ...infra.logging import logger


class MessageRepository:
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
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT DEFAULT '',
                status TEXT DEFAULT 'done',
                intent TEXT DEFAULT '',
                confidence REAL DEFAULT 0.0,
                route_reason TEXT DEFAULT '',
                citations TEXT DEFAULT '[]',
                steps TEXT DEFAULT '[]',
                error TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

    def append(self, session_id: str, role: str, content: str = "",
               status: str = "done", intent: str = "", confidence: float = 0.0,
               route_reason: str = "", citations: list = None, steps: list = None,
               error: str = "") -> dict:
        conn = self._get_conn()
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO messages
               (id, session_id, role, content, status, intent, confidence,
                route_reason, citations, steps, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, session_id, role, content, status, intent, confidence,
             route_reason, json.dumps(citations or [], ensure_ascii=False),
             json.dumps(steps or [], ensure_ascii=False), error, now),
        )
        conn.commit()
        return {"id": msg_id, "session_id": session_id, "role": role, "content": content,
                "status": status, "created_at": now}

    def get_by_session(self, session_id: str, limit: int = 100) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["citations"] = json.loads(d.get("citations", "[]"))
            d["steps"] = json.loads(d.get("steps", "[]"))
            results.append(d)
        return results

    def update_content(self, msg_id: str, content: str, status: str = "done"):
        conn = self._get_conn()
        conn.execute(
            "UPDATE messages SET content = ?, status = ? WHERE id = ?",
            (content, status, msg_id),
        )
        conn.commit()

    def update_metadata(self, msg_id: str, **kwargs):
        conn = self._get_conn()
        if "citations" in kwargs:
            kwargs["citations"] = json.dumps(kwargs["citations"], ensure_ascii=False)
        if "steps" in kwargs:
            kwargs["steps"] = json.dumps(kwargs["steps"], ensure_ascii=False)
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [msg_id]
        conn.execute(f"UPDATE messages SET {sets} WHERE id = ?", vals)
        conn.commit()

    def delete_by_session(self, session_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()

    def get_last(self, session_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if row:
            d = dict(row)
            d["citations"] = json.loads(d.get("citations", "[]"))
            d["steps"] = json.loads(d.get("steps", "[]"))
            return d
        return None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
