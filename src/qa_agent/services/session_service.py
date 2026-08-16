"""Session service: CRUD operations for chat sessions."""

from typing import Optional

from ..data.repositories.session_repo import SessionRepository
from ..data.repositories.message_repo import MessageRepository
from ..infra.logging import logger


class SessionService:
    """Manages chat sessions and their messages."""

    def __init__(self, db_path: str = ""):
        kwargs = {"db_path": db_path} if db_path else {}
        self._session_repo = SessionRepository(**kwargs)
        self._message_repo = MessageRepository(**kwargs)
        self._active_session_id: Optional[str] = None

    @property
    def active_session_id(self) -> Optional[str]:
        return self._active_session_id

    def create_session(self, title: str = "新会话", model_key: str = "", system_prompt: str = "") -> dict:
        session = self._session_repo.create(title, model_key, system_prompt)
        self._active_session_id = session["id"]
        logger.info("Created session: %s (%s)", session["id"], title)
        return session

    def list_sessions(self) -> list[dict]:
        return self._session_repo.list_all()

    def get_session(self, session_id: str) -> Optional[dict]:
        return self._session_repo.get(session_id)

    def switch_session(self, session_id: str) -> Optional[dict]:
        session = self._session_repo.get(session_id)
        if session:
            self._active_session_id = session_id
            logger.info("Switched to session: %s", session_id)
        return session

    def rename_session(self, session_id: str, new_title: str):
        self._session_repo.rename(session_id, new_title)

    def delete_session(self, session_id: str):
        self._message_repo.delete_by_session(session_id)
        self._session_repo.delete(session_id)
        if self._active_session_id == session_id:
            sessions = self._session_repo.list_all()
            self._active_session_id = sessions[0]["id"] if sessions else None

    def get_messages(self, session_id: str = None, limit: int = 100) -> list[dict]:
        sid = session_id or self._active_session_id
        if not sid:
            return []
        return self._message_repo.get_by_session(sid, limit)

    def append_message(self, session_id: str = None, role: str = "user",
                       content: str = "", **kwargs) -> dict:
        sid = session_id or self._active_session_id
        if not sid:
            raise ValueError("No active session")
        return self._message_repo.append(sid, role, content, **kwargs)

    def update_message(self, msg_id: str, content: str = None, status: str = None, **kwargs):
        if content is not None:
            self._message_repo.update_content(msg_id, content, status or "done")
        if kwargs:
            self._message_repo.update_metadata(msg_id, **kwargs)

    def get_last_message(self, session_id: str = None) -> Optional[dict]:
        sid = session_id or self._active_session_id
        if not sid:
            return None
        return self._message_repo.get_last(sid)

    def ensure_session(self) -> str:
        """Ensure there's an active session, create one if needed."""
        if self._active_session_id:
            session = self._session_repo.get(self._active_session_id)
            if session:
                return self._active_session_id
        sessions = self._session_repo.list_all()
        if sessions:
            self._active_session_id = sessions[0]["id"]
        else:
            session = self.create_session()
            self._active_session_id = session["id"]
        return self._active_session_id

    def close(self):
        self._session_repo.close()
        self._message_repo.close()
