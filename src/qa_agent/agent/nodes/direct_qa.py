"""Direct QA node: simple LLM generation without retrieval."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ...agent.schema import QAState
from ...infra.llm_factory import create_chat_model
from ...infra.logging import logger
from ...constants import DEFAULT_SYSTEM_PROMPT


async def direct_qa_node(state: QAState) -> dict:
    """Generate answer directly from LLM without knowledge base."""
    llm_config = state.get("llm_config", {})
    system_prompt = state.get("system_prompt", "") or DEFAULT_SYSTEM_PROMPT
    messages = state.get("messages", [])
    user_query = state.get("user_query", "")
    context_rounds = state.get("context_rounds", 10)

    chat_messages = [SystemMessage(content=system_prompt)]

    history = messages[-(context_rounds * 2):]
    for msg in history:
        if isinstance(msg, (HumanMessage, AIMessage)):
            chat_messages.append(msg)
        elif hasattr(msg, "type"):
            if msg.type == "human":
                chat_messages.append(HumanMessage(content=msg.content))
            elif msg.type == "ai":
                chat_messages.append(AIMessage(content=msg.content))

    if not any(isinstance(m, HumanMessage) and m.content == user_query for m in chat_messages):
        chat_messages.append(HumanMessage(content=user_query))

    model = create_chat_model(llm_config)
    response = await model.ainvoke(chat_messages)
    answer = response.content if hasattr(response, "content") else str(response)

    logger.info("DirectQA: generated answer (%d chars)", len(answer))
    return {"final_answer": answer}
