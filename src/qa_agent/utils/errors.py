"""Unified exception types for the QA agent."""


class QAAgentError(Exception):
    """Base exception for all QA agent errors."""


class LLMCallError(QAAgentError):
    def __init__(self, category: str, message: str):
        self.category = category
        self.message = message
        super().__init__(f"[{category}] {message}")


class AuthenticationError(LLMCallError):
    def __init__(self, message: str = "API Key 无效或已过期"):
        super().__init__("auth", message)


class RateLimitError(LLMCallError):
    def __init__(self, message: str = "API 调用频率超限，请稍后重试"):
        super().__init__("rate_limit", message)


class NetworkError(LLMCallError):
    def __init__(self, message: str = "网络连接异常，请检查网络设置"):
        super().__init__("network", message)


class RouterError(LLMCallError):
    def __init__(self, message: str = "意图路由异常，已降级为直接回答"):
        super().__init__("router", message)


class DocumentParseError(QAAgentError):
    def __init__(self, file_name: str, reason: str):
        self.file_name = file_name
        self.reason = reason
        super().__init__(f"文档解析失败 [{file_name}]: {reason}")


class VectorStoreError(QAAgentError):
    pass


class ConfigError(QAAgentError):
    pass


class UnsupportedProviderError(QAAgentError):
    def __init__(self, provider: str):
        super().__init__(f"不支持的模型供应商: {provider}")
