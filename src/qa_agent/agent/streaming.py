"""Stream bridge: converts LangGraph async stream events to Qt-compatible signals."""

import asyncio
from typing import Any, AsyncGenerator, Callable

from ..infra.logging import logger


class TokenBuffer:
    """Accumulates streamed tokens for display."""

    def __init__(self):
        self._buffer: list[str] = []
        self._full_text: str = ""

    def append(self, token: str):
        self._buffer.append(token)
        self._full_text += token

    def flush(self) -> str:
        text = "".join(self._buffer)
        self._buffer.clear()
        return text

    @property
    def full_text(self) -> str:
        return self._full_text

    def reset(self):
        self._buffer.clear()
        self._full_text = ""


class StreamBridge:
    """Bridges LangGraph async stream to callback-based events."""

    def __init__(self):
        self._token_callback: Callable[[str], None] | None = None
        self._route_callback: Callable[[dict], None] | None = None
        self._step_callback: Callable[[int, int, str], None] | None = None
        self._done_callback: Callable[[dict], None] | None = None
        self._error_callback: Callable[[str], None] | None = None
        self._cancelled = False
        self._task: asyncio.Task | None = None

    def on_token(self, callback: Callable[[str], None]):
        self._token_callback = callback

    def on_route(self, callback: Callable[[dict], None]):
        self._route_callback = callback

    def on_step(self, callback: Callable[[int, int, str], None]):
        self._step_callback = callback

    def on_done(self, callback: Callable[[dict], None]):
        self._done_callback = callback

    def on_error(self, callback: Callable[[str], None]):
        self._error_callback = callback

    def cancel(self):
        self._cancelled = True
        if self._task and not self._task.done():
            self._task.cancel()

    async def run_stream(self, graph, inputs: dict, config: dict):
        """Execute the graph stream and dispatch events."""
        self._cancelled = False
        buffer = TokenBuffer()

        try:
            self._task = asyncio.current_task()

            async for chunk in graph.astream(
                inputs,
                config=config,
                stream_mode=["updates"],
            ):
                if self._cancelled:
                    break

                if isinstance(chunk, tuple) and len(chunk) == 2:
                    node_name, node_data = chunk
                elif isinstance(chunk, dict):
                    node_name = chunk.get("__node__", "")
                    node_data = chunk
                else:
                    continue

                if node_name == "router" and self._route_callback:
                    self._route_callback({
                        "intent": node_data.get("intent", ""),
                        "confidence": node_data.get("confidence", 0.0),
                        "route_reason": node_data.get("route_reason", ""),
                    })

                if node_name == "reasoning" and self._step_callback:
                    steps = node_data.get("decomposed_steps", [])
                    for step in steps:
                        self._step_callback(
                            step.get("order", 0),
                            len(steps),
                            step.get("description", ""),
                        )

                if node_name == "output":
                    messages = node_data.get("messages", [])
                    for msg in messages:
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        if content:
                            for char in content:
                                buffer.append(char)
                                if self._token_callback:
                                    self._token_callback(char)

            if self._done_callback:
                self._done_callback({
                    "full_text": buffer.full_text,
                })

        except asyncio.CancelledError:
            logger.info("Stream cancelled by user")
            if self._done_callback:
                self._done_callback({"full_text": buffer.full_text, "stopped": True})
        except Exception as e:
            logger.error("Stream error: %s", e)
            if self._error_callback:
                self._error_callback(str(e))
