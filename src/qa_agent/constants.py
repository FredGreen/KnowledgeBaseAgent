"""Constants for the intelligent QA agent application."""

from enum import Enum


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"
    ZHIPU = "zhipu"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


PROVIDER_DISPLAY = {
    Provider.OPENAI: "OpenAI",
    Provider.ANTHROPIC: "Anthropic",
    Provider.QWEN: "通义千问",
    Provider.ZHIPU: "智谱AI",
    Provider.DEEPSEEK: "DeepSeek",
    Provider.CUSTOM: "自定义兼容",
}

PROVIDER_DEFAULT_BASE_URL = {
    Provider.OPENAI: "https://api.openai.com/v1",
    Provider.ANTHROPIC: "",
    Provider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    Provider.ZHIPU: "https://open.bigmodel.cn/api/paas/v4",
    Provider.DEEPSEEK: "https://api.deepseek.com/v1",
    Provider.CUSTOM: "",
}

PROVIDER_DEFAULT_MODELS = {
    Provider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    Provider.ANTHROPIC: ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    Provider.QWEN: ["qwen-max", "qwen-plus", "qwen-turbo"],
    Provider.ZHIPU: ["glm-4-plus", "glm-4", "glm-4-flash"],
    Provider.DEEPSEEK: ["deepseek-chat", "deepseek-reasoner"],
    Provider.CUSTOM: [],
}


class Intent(str, Enum):
    DIRECT_QA = "direct_qa"
    RAG = "rag"
    REASONING = "reasoning"


INTENT_DISPLAY = {
    Intent.DIRECT_QA: "⚡ 直接回答",
    Intent.RAG: "📚 知识库检索",
    Intent.REASONING: "🔄 多步推理",
}

INTENT_ICON = {
    Intent.DIRECT_QA: "⚡",
    Intent.RAG: "📚",
    Intent.REASONING: "🔄",
}


class DocStatus(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    VECTORIZING = "vectorizing"
    DONE = "done"
    FAILED = "failed"


DOC_STATUS_DISPLAY = {
    DocStatus.QUEUED: "等待中",
    DocStatus.PARSING: "解析中",
    DocStatus.VECTORIZING: "向量化中",
    DocStatus.DONE: "完成",
    DocStatus.FAILED: "失败",
}


class MessageStatus(str, Enum):
    GENERATING = "generating"
    DONE = "done"
    STOPPED = "stopped"
    ERROR = "error"


SUPPORTED_FILE_TYPES = {".txt", ".md", ".pdf", ".docx", ".csv", ".xlsx", ".json"}

DEFAULT_SYSTEM_PROMPT = (
    "你是一个智能助手，能够回答用户的各种问题。"
    "如果提供了知识库检索结果，请优先基于这些内容回答，并标注引用来源。"
    "回答应当准确、简洁、有条理。"
)

DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CONTEXT_ROUNDS = 10
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 0.15
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.55
DEFAULT_MIN_CONFIDENCE = 0.6
DEFAULT_ROUTER_TIMEOUT = 5.0

EMBEDDING_PROVIDER = "qwen"
EMBEDDING_MODEL = "text-embedding-v3"
EMBEDDING_DIMENSION = 1024

MILVUS_DB_PATH = "milvus_data.db"
SQLITE_DB_PATH = "qa_agent.db"
CONFIG_PATH = "config/settings.json"

APP_NAME = "智能问答 Agent"


class NavPage(str, Enum):
    CHAT = "chat"
    KB = "kb"
    SETTINGS = "settings"
