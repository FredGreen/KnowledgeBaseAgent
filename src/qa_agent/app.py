"""Application bootstrap: wires services, data layer, and UI together."""

import asyncio
import sys
from pathlib import Path

from .services.config_service import ConfigService
from .services.session_service import SessionService
from .services.chat_service import ChatService
from .services.kb_service import KBService
from .data.vector_store import VectorStore
from .data.repositories.session_repo import SessionRepository
from .data.repositories.message_repo import MessageRepository
from .data.repositories.document_repo import DocumentRepository
from .infra.llm_factory import LLMFactory
from .infra.embedding_factory import EmbeddingFactory
from .agent.graph_builder import build_graph
from .agent.streaming import StreamBridge
from .infra.logging import setup_logging
from .constants import APP_NAME


class Application:
    """Main application class: initializes all services and provides access."""

    def __init__(self, data_dir: Path | None = None):
        if data_dir is None:
            data_dir = Path.home() / ".intelligent_qa_agent"
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)

        setup_logging(self._data_dir / "logs")

        self._config = ConfigService(self._data_dir / "settings.json")
        self._session_repo = SessionRepository(self._data_dir / "sessions.db")
        self._message_repo = MessageRepository(self._data_dir / "sessions.db")
        self._doc_repo = DocumentRepository(self._data_dir / "documents.db")

        self._vector_store = VectorStore(self._data_dir / "milvus_data")
        self._llm_factory = LLMFactory()
        self._embedding_factory = EmbeddingFactory()

        self._session_service = SessionService(self._session_repo, self._message_repo)
        self._kb_service = KBService(
            self._doc_repo, self._vector_store,
            self._config, self._embedding_factory,
        )

        graph = build_graph(self._llm_factory, self._vector_store, self._config)
        self._chat_service = ChatService(
            graph=graph,
            llm_factory=self._llm_factory,
            config_service=self._config,
            session_service=self._session_service,
        )

    @property
    def config_service(self) -> ConfigService:
        return self._config

    @property
    def session_service(self) -> SessionService:
        return self._session_service

    @property
    def chat_service(self) -> ChatService:
        return self._chat_service

    @property
    def kb_service(self) -> KBService:
        return self._kb_service

    def rebuild_graph(self):
        graph = build_graph(self._llm_factory, self._vector_store, self._config)
        self._chat_service.update_graph(graph)

    async def shutdown(self):
        await self._vector_store.close()
