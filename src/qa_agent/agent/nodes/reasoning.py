"""Reasoning node: decompose → step-by-step processing → summarize."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ...agent.schema import QAState, ReasoningStep
from ...constants import DEFAULT_SYSTEM_PROMPT
from ...infra.llm_factory import create_chat_model
from ...infra.logging import logger


DECOMPOSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个任务分解专家。将用户的复杂问题分解为 2-5 个子问题。
每个子问题应该：
1. 具体、可回答
2. 标注是否需要检索知识库（needs_retrieval）
3. 按逻辑顺序排列

输出 JSON 格式的子问题列表。"""),
    ("human", "用户问题：{query}\n\n请分解为子问题："),
])

STEP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}\n\n{context}"),
    ("human", "子问题：{subtask}\n\n请回答这个子问题："),
])

SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}\n\n请综合以下子问题的答案，给出完整、结构化的最终回答。"),
    ("human", "原始问题：{query}\n\n子问题答案：\n{step_results}\n\n请给出最终回答："),
])


class SubQuestion(BaseModel):
    description: str = Field(description="子问题描述")
    needs_retrieval: bool = Field(default=False, description="是否需要检索知识库")


class DecomposeOutput(BaseModel):
    steps: list[SubQuestion] = Field(description="子问题列表，2-5个")


async def reasoning_node(state: QAState) -> dict:
    """Multi-step reasoning: decompose → process each → summarize."""
    llm_config = state.get("llm_config", {})
    embedding_config = state.get("embedding_config", {})
    system_prompt = state.get("system_prompt", "") or DEFAULT_SYSTEM_PROMPT
    user_query = state.get("user_query", "")
    top_k = state.get("top_k", 5)
    min_score = state.get("min_score", 0.55)

    model = create_chat_model(llm_config)

    # Step 1: Decompose
    structured_model = model.with_structured_output(DecomposeOutput)
    decompose_result = await structured_model.ainvoke(
        DECOMPOSE_PROMPT.invoke({"query": user_query})
    )
    steps = []
    for i, sq in enumerate(decompose_result.steps[:5]):
        steps.append({
            "order": i + 1,
            "description": sq.description,
            "status": "pending",
            "subtask_result": "",
            "needs_retrieval": sq.needs_retrieval,
            "citations": [],
        })

    logger.info("Reasoning: decomposed into %d steps", len(steps))

    # Step 2: Process each sub-step
    step_results = []
    for i, step in enumerate(steps):
        steps[i]["status"] = "running"
        context = ""

        if step["needs_retrieval"]:
            try:
                from ...data.vector_store import VectorStore
                from ...data.embeddings import create_embeddings
                emb_client = create_embeddings(embedding_config)
                query_vector = await emb_client.aembed_query(step["description"])
                vs = VectorStore()
                vs.init()
                results = await vs.async_search(query_vector, top_k=top_k)
                if results and any(r.get("score", 0) >= min_score for r in results):
                    context_parts = []
                    for j, r in enumerate(results):
                        if r.get("score", 0) >= min_score:
                            context_parts.append(f"[{j+1}] {r.get('file_name', '')}: {r.get('content', '')[:300]}")
                            step["citations"].append({
                                "index": j + 1,
                                "doc_id": r.get("doc_id", ""),
                                "file_name": r.get("file_name", ""),
                                "page_or_par": r.get("page_or_par", ""),
                                "score": r.get("score", 0.0),
                                "snippet": r.get("content", "")[:200],
                            })
                    context = "知识库检索结果：\n" + "\n".join(context_parts)
            except Exception as e:
                logger.warning("Step %d retrieval failed: %s", i + 1, e)

        try:
            prompt = STEP_PROMPT.invoke({
                "system_prompt": system_prompt,
                "context": context or "无需知识库检索。",
                "subtask": step["description"],
            })
            resp = await model.ainvoke(prompt)
            result_text = resp.content if hasattr(resp, "content") else str(resp)
            step["subtask_result"] = result_text
            step["status"] = "done"
            step_results.append(f"子问题{i+1}: {step['description']}\n答案: {result_text}")
        except Exception as e:
            step["status"] = "failed"
            step["subtask_result"] = f"处理失败: {str(e)[:100]}"
            step_results.append(f"子问题{i+1}: {step['description']}\n答案: 处理失败")

    # Step 3: Summarize
    try:
        prompt = SUMMARIZE_PROMPT.invoke({
            "system_prompt": system_prompt,
            "query": user_query,
            "step_results": "\n\n".join(step_results),
        })
        resp = await model.ainvoke(prompt)
        final_answer = resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:
        final_answer = "\n\n".join(step_results)
        logger.warning("Summarization failed: %s", e)

    logger.info("Reasoning: completed %d steps, answer %d chars", len(steps), len(final_answer))
    return {
        "decomposed_steps": steps,
        "final_answer": final_answer,
    }
