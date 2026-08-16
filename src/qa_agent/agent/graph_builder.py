"""LangGraph workflow builder: constructs the intent-routing StateGraph."""

from typing import Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..agent.schema import QAState
from ..agent.nodes.router import router_node
from ..agent.nodes.direct_qa import direct_qa_node
from ..agent.nodes.rag import rag_node
from ..agent.nodes.reasoning import reasoning_node
from ..agent.nodes.output import output_node
from ..constants import Intent
from ..infra.logging import logger


def _route_from_router(state: QAState) -> str:
    """Conditional edge: decide which branch from router output."""
    manual = state.get("manual_override", "")
    if manual and manual != "auto":
        return manual

    intent = state.get("intent", Intent.DIRECT_QA)
    kb = state.get("kb_available", False)
    conf = state.get("confidence", 0.0)
    min_conf = state.get("min_confidence", 0.6)

    if intent == Intent.RAG and not kb:
        return Intent.DIRECT_QA
    if conf < min_conf:
        return Intent.RAG if kb else Intent.DIRECT_QA
    return intent


def _route_from_rag(state: QAState) -> str:
    """Conditional edge: RAG fallback check."""
    if state.get("kb_miss", False):
        return "fallback_qa"
    return "output"


def build_graph() -> StateGraph:
    """Build and compile the QA agent workflow graph."""
    builder = StateGraph(QAState)

    builder.add_node("router", router_node)
    builder.add_node("direct_qa", direct_qa_node)
    builder.add_node("rag", rag_node)
    builder.add_node("reasoning", reasoning_node)
    builder.add_node("fallback_qa", direct_qa_node)
    builder.add_node("output", output_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        _route_from_router,
        {
            Intent.DIRECT_QA: "direct_qa",
            Intent.RAG: "rag",
            Intent.REASONING: "reasoning",
        },
    )
    builder.add_edge("direct_qa", "output")
    builder.add_conditional_edges(
        "rag",
        _route_from_rag,
        {
            "fallback_qa": "fallback_qa",
            "output": "output",
        },
    )
    builder.add_edge("fallback_qa", "output")
    builder.add_edge("reasoning", "output")
    builder.add_edge("output", END)

    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    logger.info("QA agent graph compiled successfully")
    return graph


_graph_instance = None


def get_graph():
    """Get or create the singleton graph instance."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance
