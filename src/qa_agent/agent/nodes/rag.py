"""RAG node: query rewrite → vector search → threshold check → citation-augmented generation."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from ...agent.schema import QAState, RetrievedDoc, Citation
from ...constants import DEFAULT_SIMILARITY_THRESHOLD, DEFAULT_SYSTEM_PROMPT
from ...infra.llm_factory import create_chat_model
from ...infra.logging import logger


QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个查询改写助手。根据对话历史，将用户的追问改写为一个独立完整的查询语句。只输出改写后的查询，不要解释。"),
    ("human", "对话历史：\n{history}\n\n用户追问：{query}\n\n请改写为独立完整的查询："),
])

RAG_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """{system_prompt}

请基于以下知识库检索结果回答用户问题。回答中必须使用 [1]、[2] 等上标标注引用来源。
如果检索结果中没有相关信息，请说明未找到相关内容。

知识库检索结果：
{context}"""),
    ("human", "{query}"),
])


async def _rewrite_query(state: QAState) -> str:
    """Rewrite user query to be self-contained using conversation history."""
    messages = state.get("messages", [])
    user_query = state.get("user_query", "")
    llm_config = state.get("llm_config", {})

    if len(messages) < 2:
        return user_query

    history_parts = []
    for msg in messages[-6:]:
        role = msg.type if hasattr(msg, "type") else "unknown"
        content = msg.content if hasattr(msg, "content") else ""
        if role in ("human", "ai") and content:
            history_parts.append(f"{'用户' if role == 'human' else '助手'}: {content[:200]}")

    if not history_parts:
        return user_query

    try:
        model = create_chat_model(llm_config)
        prompt = QUERY_REWRITE_PROMPT.invoke({
            "history": "\n".join(history_parts),
            "query": user_query,
        })
        rewritten = await model.ainvoke(prompt)
        result = rewritten.content if hasattr(rewritten, "content") else str(rewritten)
        return result.strip() if result.strip() else user_query
    except Exception as e:
        logger.warning("Query rewrite failed: %s, using original query", e)
        return user_query


async def rag_node(state: QAState) -> dict:
    """RAG pipeline: rewrite → search → check threshold → generate with citations."""
    from ...data.vector_store import VectorStore
    from ...data.embeddings import create_embeddings

    llm_config = state.get("llm_config", {})
    embedding_config = state.get("embedding_config", {})
    system_prompt = state.get("system_prompt", "") or DEFAULT_SYSTEM_PROMPT
    user_query = state.get("user_query", "")
    top_k = state.get("top_k", 5)
    min_score = state.get("min_score", DEFAULT_SIMILARITY_THRESHOLD)

    rewritten_query = await _rewrite_query(state)
    logger.info("RAG: rewritten query: %s", rewritten_query[:100])

    emb_client = create_embeddings(embedding_config)
    query_vector = await emb_client.aembed_query(rewritten_query)

    vs = VectorStore()
    vs.init()
    results = await vs.async_search(query_vector, top_k=top_k)

    if not results or all(r.get("score", 0) < min_score for r in results):
        logger.info("RAG: no results above threshold %.2f, falling back", min_score)
        return {"kb_miss": True, "retrieved_docs": [], "final_answer": ""}

    docs = []
    citations = []
    context_parts = []
    for i, r in enumerate(results):
        if r.get("score", 0) >= min_score:
            docs.append(r)
            citations.append({
                "index": i + 1,
                "doc_id": r.get("doc_id", ""),
                "file_name": r.get("file_name", ""),
                "page_or_par": r.get("page_or_par", ""),
                "score": r.get("score", 0.0),
                "snippet": r.get("content", "")[:200],
            })
            context_part = f"[{i+1}] 来源: {r.get('file_name', '未知')} ({r.get('page_or_par', '')})\n内容: {r.get('content', '')}"
            context_parts.append(context_part)

    context = "\n\n---\n\n".join(context_parts)

    chat_messages = []
    history = state.get("messages", [])
    context_rounds = state.get("context_rounds", 10)
    for msg in history[-(context_rounds * 2):]:
        role = msg.type if hasattr(msg, "type") else ""
        content = msg.content if hasattr(msg, "content") else ""
        if role == "human":
            chat_messages.append(HumanMessage(content=content))
        elif role == "ai":
            chat_messages.append(AIMessage(content=content))

    prompt = RAG_GENERATION_PROMPT.invoke({
        "system_prompt": system_prompt,
        "context": context,
        "query": user_query,
    })

    model = create_chat_model(llm_config)
    response = await model.ainvoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    logger.info("RAG: generated answer with %d citations (%d chars)", len(citations), len(answer))
    return {
        "retrieved_docs": docs,
        "final_answer": answer,
        "kb_miss": False,
    }
