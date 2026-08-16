"""Agent schema definitions: QAState, RouterOutput, ReasoningStep, etc."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


class RouterOutput(BaseModel):
    """Structured output from the Router node."""
    intent: Literal["direct_qa", "rag", "reasoning"] = Field(description="意图分类")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0~1")
    reason: str = Field(description="一句话判断理由")


class RetrievedDoc(BaseModel):
    """A retrieved document chunk."""
    doc_id: str = ""
    file_name: str = ""
    page_or_par: str = ""
    content: str = ""
    score: float = 0.0


class ReasoningStep(BaseModel):
    """A step in multi-step reasoning."""
    order: int = 0
    description: str = ""
    status: Literal["pending", "running", "done", "failed"] = "pending"
    subtask_result: str = ""
    needs_retrieval: bool = False
    citations: list[dict] = []


class Citation(BaseModel):
    """A citation reference in the answer."""
    index: int = 0
    doc_id: str = ""
    file_name: str = ""
    page_or_par: str = ""
    score: float = 0.0
    snippet: str = ""


class QAState(MessagesState):
    """Main state for the QA agent workflow."""
    user_query: str
    intent: str
    confidence: float
    route_reason: str
    manual_override: str
    kb_available: bool
    retrieved_docs: list[dict]
    min_score: float
    min_confidence: float
    decomposed_steps: list[dict]
    final_answer: str
    kb_miss: bool
    error: str
    system_prompt: str
    llm_config: dict
    embedding_config: dict
    top_k: int
    context_rounds: int
    kb_topics: str
    stream_writer: Any
