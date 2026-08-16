"""Router node: intent classification via structured output."""

import asyncio
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

from ...agent.schema import QAState, RouterOutput
from ...constants import DEFAULT_MIN_CONFIDENCE, DEFAULT_ROUTER_TIMEOUT, Intent
from ...infra.llm_factory import create_chat_model
from ...infra.logging import logger
from ...utils.text_utils import summarize_messages


ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是意图路由器。基于用户问题、最近对话摘要、知识库状态，判断应走哪条链路。
- direct_qa：普通问答（常识/闲聊/创作/不依赖外部知识的任务）
- rag：需要检索本地知识库（含专有名词/明确指向文档/事实型且知识库有相关主题）
- reasoning：需多步拆解（对比/规划/多源汇总/多跳推理/因果链分析）
若知识库为空，禁止选 rag。
当前知识库状态：{kb_available}
已上传文档主题：{kb_topics}
最近对话：{history_summary}
用户问题：{user_query}"""),
    ("human", "请判断该问题的意图分类。"),
])


async def router_node(state: QAState) -> dict:
    """Classify user intent into direct_qa / rag / reasoning."""
    user_query = state.get("user_query", "")
    kb_available = state.get("kb_available", False)
    kb_topics = state.get("kb_topics", "")
    messages = state.get("messages", [])
    min_confidence = state.get("min_confidence", DEFAULT_MIN_CONFIDENCE)
    llm_config = state.get("llm_config", {})

    history_summary = summarize_messages(
        [{"role": m.type if hasattr(m, "type") else m.get("role", ""),
          "content": m.content if hasattr(m, "content") else m.get("content", "")}
         for m in messages[-10:]]
    )

    try:
        model = create_chat_model(llm_config)
        structured_model = model.with_structured_output(RouterOutput)
        prompt = ROUTER_PROMPT.invoke({
            "kb_available": "非空，已有文档" if kb_available else "为空",
            "kb_topics": kb_topics or "无",
            "history_summary": history_summary or "无",
            "user_query": user_query,
        })

        result = await asyncio.wait_for(
            structured_model.ainvoke(prompt),
            timeout=DEFAULT_ROUTER_TIMEOUT,
        )

        intent = result.intent
        confidence = result.confidence
        reason = result.reason

        if intent == Intent.RAG and not kb_available:
            intent = Intent.DIRECT_QA
            reason = "知识库为空，降级为直接回答"

        if confidence < min_confidence:
            if kb_available:
                intent = Intent.RAG
                reason = f"置信度较低({confidence:.2f})，优先检索知识库"
            else:
                intent = Intent.DIRECT_QA
                reason = f"置信度较低({confidence:.2f})，知识库为空，直接回答"

        logger.info("Router: intent=%s confidence=%.2f reason=%s", intent, confidence, reason)
        return {"intent": intent, "confidence": confidence, "route_reason": reason}

    except asyncio.TimeoutError:
        logger.warning("Router timeout, falling back to direct_qa")
        return {"intent": Intent.DIRECT_QA, "confidence": 0.0,
                "route_reason": "路由超时，降级为直接回答", "error": "路由超时"}
    except Exception as e:
        logger.warning("Router error: %s, falling back to direct_qa", e)
        return {"intent": Intent.DIRECT_QA, "confidence": 0.0,
                "route_reason": f"路由异常，降级为直接回答: {str(e)[:100]}", "error": str(e)[:200]}
