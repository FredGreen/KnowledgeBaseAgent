"""Multi-provider LLM factory: creates unified BaseChatModel instances."""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from ..constants import Provider, PROVIDER_DEFAULT_BASE_URL
from ..infra.logging import logger
from ..infra.security import load_secret
from ..utils.errors import UnsupportedProviderError


def create_chat_model(cfg: dict[str, Any]) -> BaseChatModel:
    """Create a chat model instance based on provider config.

    Args:
        cfg: dict with keys: provider, base_url, api_key_ref, model,
             temperature, max_tokens, streaming
    """
    provider = cfg.get("provider", "openai")
    model_name = cfg.get("model", "gpt-4o")
    api_key = load_secret(cfg.get("api_key_ref", ""))
    temperature = cfg.get("temperature", 0.7)
    max_tokens = cfg.get("max_tokens", 2048)
    streaming = cfg.get("streaming", True)

    if provider in (Provider.CUSTOM, Provider.OPENAI):
        from langchain_openai import ChatOpenAI
        base_url = cfg.get("base_url") or PROVIDER_DEFAULT_BASE_URL[Provider.OPENAI]
        return ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key=api_key or "not-set",
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )

    if provider == Provider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=api_key or "not-set",
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )

    if provider in (Provider.QWEN, Provider.ZHIPU, Provider.DEEPSEEK):
        from langchain_openai import ChatOpenAI
        base_url = cfg.get("base_url") or PROVIDER_DEFAULT_BASE_URL[Provider(provider)]
        return ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key=api_key or "not-set",
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )

    raise UnsupportedProviderError(provider)


class LLMFactory:
    """Factory for creating and managing LLM instances."""

    @staticmethod
    def create(provider: str, cfg: dict[str, Any]) -> BaseChatModel:
        """Create a chat model for the given provider."""
        model_cfg = {
            "provider": provider,
            "base_url": cfg.get("base_url", ""),
            "api_key_ref": "",
            "model": cfg.get("model", ""),
            "temperature": cfg.get("temperature", 0.7),
            "max_tokens": cfg.get("max_tokens", 2048),
            "streaming": True,
        }
        api_key = cfg.get("api_key", "")
        if api_key:
            from ..infra.security import store_secret
            ref = f"{provider}_key"
            store_secret(ref, api_key)
            model_cfg["api_key_ref"] = ref
        return create_chat_model(model_cfg)

    @staticmethod
    def create_from_config(config_service) -> BaseChatModel:
        """Create a chat model from ConfigService."""
        active = config_service.get_active_provider()
        pcfg = config_service.get_provider_config(active)
        gen = config_service.get_generation_params()
        return LLMFactory.create(active, {**pcfg, **gen})


async def test_connection(cfg: dict[str, Any]) -> dict[str, Any]:
    """Test LLM connection with a minimal request.

    Returns:
        {"success": bool, "latency_ms": float, "error": str|None}
    """
    import time
    try:
        model = create_chat_model(cfg)
        start = time.time()
        resp = await model.ainvoke(
            [{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        latency = (time.time() - start) * 1000
        return {"success": True, "latency_ms": round(latency, 1), "error": None}
    except Exception as e:
        err_str = str(e)
        if "authentication" in err_str.lower() or "401" in err_str or "invalid" in err_str.lower():
            category = "认证失败：API Key 无效"
        elif "rate" in err_str.lower() or "429" in err_str:
            category = "频率限制：请稍后重试"
        elif "connect" in err_str.lower() or "timeout" in err_str.lower():
            category = "网络连接异常"
        else:
            category = f"连接失败: {err_str[:200]}"
        logger.warning("Connection test failed: %s", category)
        return {"success": False, "latency_ms": 0, "error": category}
