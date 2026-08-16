"""Output node: finalize the answer and assemble message metadata."""

from langchain_core.messages import AIMessage

from ...agent.schema import QAState
from ...infra.logging import logger


async def output_node(state: QAState) -> dict:
    """Finalize: append AIMessage with answer + route metadata."""
    final_answer = state.get("final_answer", "")
    intent = state.get("intent", "direct_qa")
    confidence = state.get("confidence", 0.0)
    route_reason = state.get("route_reason", "")

    if not final_answer and state.get("error"):
        final_answer = f"抱歉，处理过程中出现错误：{state['error']}"

    ai_message = AIMessage(content=final_answer)
    logger.info("Output: finalized answer (%d chars), intent=%s", len(final_answer), intent)

    return {"messages": [ai_message]}
