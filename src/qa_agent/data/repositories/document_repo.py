"""SQLite document metadata repository."""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from ...constants import SQLITE_DB_PATH, DocStatus
from ...infra.logging import logger


class DocumentRepository:
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
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'queued',
                progress REAL DEFAULT 0.0,
                error TEXT DEFAULT '',
                chunk_count INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL
            )
        """)
        conn.commit()

    def create(self, file_name: str, file_type: str, file_path: str, size: int) -> dict:
        conn = self._get_conn()
        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO documents (id, file_name, file_type, file_path, size, status, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, file_name, file_type, file_path, size, DocStatus.QUEUED, now),
        )
        conn.commit()
        logger.debug("Created document record: %s (%s)", doc_id, file_name)
        return {"id": doc_id, "file_name": file_name, "status": DocStatus.QUEUED, "uploaded_at": now}

    def get(self, doc_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update_status(self, doc_id: str, status: str, progress: float = 0.0, error: str = "", chunk_count: int = 0):
        conn = self._get_conn()
        conn.execute(
            "UPDATE documents SET status = ?, progress = ?, error = ?, chunk_count = ? WHERE id = ?",
            (status, progress, error, chunk_count, doc_id),
        )
        conn.commit()

    def delete(self, doc_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        logger.debug("Deleted document record: %s", doc_id)

    def get_stats(self) -> dict:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as doc_count, COALESCE(SUM(chunk_count), 0) as total_chunks, COALESCE(SUM(size), 0) as total_size FROM documents WHERE status = ?",
            (DocStatus.DONE,),
        ).fetchone()
        return dict(row) if row else {"doc_count": 0, "total_chunks": 0, "total_size": 0}

    def has_documents(self) -> bool:
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM documents WHERE status = ?", (DocStatus.DONE,)).fetchone()
        return row["cnt"] > 0 if row else False

    def get_topics_summary(self) -> str:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT file_name FROM documents WHERE status = ? LIMIT 20",
            (DocStatus.DONE,),
        ).fetchall()
        return ", ".join(r["file_name"] for r in rows)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
