"""Chat service: orchestrates message sending, streaming, stop/regenerate."""

import asyncio
from typing import Any, Callable, Optional

from ..agent.graph_builder import get_graph
from ..agent.streaming import StreamBridge
from ..constants import Intent, MessageStatus, INTENT_DISPLAY
from ..infra.logging import logger
from ..services.config_service import ConfigService
from ..services.session_service import SessionService
from ..data.repositories.document_repo import DocumentRepository


class ChatService:
    """Orchestrates chat interactions between UI and Agent workflow."""

    def __init__(self, config_service: ConfigService, session_service: SessionService):
        self._config = config_service
        self._sessions = session_service
        self._doc_repo = DocumentRepository()
        self._bridge: Optional[StreamBridge] = None
        self._task: Optional[asyncio.Task] = None
        self._generating = False

        self.on_token: Optional[Callable[[str], None]] = None
        self.on_route: Optional[Callable[[dict], None]] = None
        self.on_step: Optional[Callable[[int, int, str], None]] = None
        self.on_done: Optional[Callable[[dict], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status: Optional[Callable[[str], None]] = None

    @property
    def is_generating(self) -> bool:
        return self._generating

    def _build_inputs(self, user_query: str) -> dict:
        llm_config = self._config.get_llm_config()
        embedding_config = self._config.get_embedding_config()
        gen = self._config.get_generation_params()
        kb = self._config.get_kb_params()
        routing = self._config.get_routing_params()

        session_id = self._sessions.active_session_id
        messages = self._sessions.get_messages(session_id) if session_id else []

        from langchain_core.messages import HumanMessage, AIMessage
        lc_messages = []
        context_rounds = gen.get("context_rounds", 10)
        for msg in messages[-(context_rounds * 2):]:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        kb_available = self._doc_repo.has_documents()
        kb_topics = self._doc_repo.get_topics_summary() if kb_available else ""

        return {
            "messages": lc_messages,
            "user_query": user_query,
            "intent": "",
            "confidence": 0.0,
            "route_reason": "",
            "manual_override": "",
            "kb_available": kb_available,
            "retrieved_docs": [],
            "min_score": kb.get("similarity_threshold", 0.55),
            "min_confidence": routing.get("min_confidence", 0.6),
            "decomposed_steps": [],
            "final_answer": "",
            "kb_miss": False,
            "error": "",
            "system_prompt": self._config.get_system_prompt(),
            "llm_config": llm_config,
            "embedding_config": embedding_config,
            "top_k": kb.get("top_k", 5),
            "context_rounds": gen.get("context_rounds", 10),
            "kb_topics": kb_topics,
            "stream_writer": None,
        }

    async def send_message(self, user_query: str) -> str:
        """Send a message and start the agent workflow. Returns assistant msg_id."""
        session_id = self._sessions.ensure_session()

        user_msg = self._sessions.append_message(
            session_id=session_id, role="user", content=user_query
        )
        assistant_msg = self._sessions.append_message(
            session_id=session_id, role="assistant", content="",
            status=MessageStatus.GENERATING,
        )

        self._generating = True
        if self.on_status:
            self.on_status(MessageStatus.GENERATING)

        inputs = self._build_inputs(user_query)
        config = {"configurable": {"thread_id": session_id}}

        graph = get_graph()
        self._bridge = StreamBridge()

        collected_text = []
        route_info = {}

        if self.on_token:
            self._bridge.on_token(lambda t: (collected_text.append(t), self.on_token(t)))
        else:
            self._bridge.on_token(lambda t: collected_text.append(t))

        if self.on_route:
            self._bridge.on_route(lambda r: (route_info.update(r), self.on_route(r)))
        else:
            self._bridge.on_route(route_info.update)

        if self.on_step:
            self._bridge.on_step(self.on_step)

        final_data = {}

        def on_done(data):
            final_data.update(data)
            if self.on_done:
                self.on_done(data)

        self._bridge.on_done(on_done)

        if self.on_error:
            self._bridge.on_error(self.on_error)

        try:
            await self._bridge.run_stream(graph, inputs, config)
        except Exception as e:
            logger.error("Chat workflow error: %s", e)
            if self.on_error:
                self.on_error(str(e))

        full_text = "".join(collected_text) or final_data.get("full_text", "")
        stopped = final_data.get("stopped", False)
        status = MessageStatus.STOPPED if stopped else MessageStatus.DONE

        self._sessions.update_message(
            assistant_msg["id"],
            content=full_text,
            status=status,
            intent=route_info.get("intent", ""),
            confidence=route_info.get("confidence", 0.0),
            route_reason=route_info.get("route_reason", ""),
        )

        self._generating = False
        if self.on_status:
            self.on_status(status)

        return assistant_msg["id"]

    def stop_generation(self):
        """Stop the current generation."""
        if self._bridge:
            self._bridge.cancel()
        self._generating = False
        if self.on_status:
            self.on_status(MessageStatus.STOPPED)
        logger.info("Generation stopped by user")

    async def regenerate(self) -> Optional[str]:
        """Regenerate the last assistant message."""
        session_id = self._sessions.active_session_id
        if not session_id:
            return None

        messages = self._sessions.get_messages(session_id)
        last_user_msg = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_msg = msg
                break

        if not last_user_msg:
            return None

        last_assistant = self._sessions.get_last_message(session_id)
        if last_assistant and last_assistant["role"] == "assistant":
            self._sessions.update_message(last_assistant["id"], content="", status=MessageStatus.GENERATING)

        return await self.send_message(last_user_msg["content"])

    def close(self):
        if self._bridge:
            self._bridge.cancel()
        self._doc_repo.close()
