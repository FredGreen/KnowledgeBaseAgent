"""Configuration service: read/write settings, manage API keys."""

import json
import os
from pathlib import Path
from typing import Any

from ..constants import (
    Provider, PROVIDER_DEFAULT_BASE_URL, PROVIDER_DEFAULT_MODELS,
    DEFAULT_SYSTEM_PROMPT, DEFAULT_TEMPERATURE, DEFAULT_TOP_P,
    DEFAULT_MAX_TOKENS, DEFAULT_CONTEXT_ROUNDS, DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP, DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_MIN_CONFIDENCE, EMBEDDING_PROVIDER, EMBEDDING_MODEL,
    EMBEDDING_DIMENSION, CONFIG_PATH,
)
from ..infra.security import store_secret, load_secret
from ..infra.llm_factory import test_connection
from ..infra.logging import logger


class ConfigService:
    """Manages application configuration."""

    def __init__(self, config_path: str = CONFIG_PATH):
        self._config_path = config_path
        self._config: dict = {}
        self._load()

    def _load(self):
        """Load config from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except Exception as e:
                logger.warning("Failed to load config: %s, using defaults", e)
                self._config = self._default_config()
        else:
            self._config = self._default_config()
            self._save()

    def _save(self):
        """Persist config to file."""
        os.makedirs(os.path.dirname(self._config_path) or ".", exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def _default_config(self) -> dict:
        return {
            "active_provider": Provider.OPENAI,
            "active_model": "gpt-4o",
            "providers": {},
            "embedding": {
                "provider": EMBEDDING_PROVIDER,
                "model": EMBEDDING_MODEL,
                "dimension": EMBEDDING_DIMENSION,
                "base_url": PROVIDER_DEFAULT_BASE_URL.get(Provider.QWEN, ""),
                "api_key_ref": "",
            },
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "generation": {
                "temperature": DEFAULT_TEMPERATURE,
                "top_p": DEFAULT_TOP_P,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "context_rounds": DEFAULT_CONTEXT_ROUNDS,
            },
            "knowledge_base": {
                "chunk_size": DEFAULT_CHUNK_SIZE,
                "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
                "top_k": DEFAULT_TOP_K,
                "similarity_threshold": DEFAULT_SIMILARITY_THRESHOLD,
            },
            "routing": {
                "min_confidence": DEFAULT_MIN_CONFIDENCE,
            },
            "general": {
                "language": "zh",
                "http_proxy": "",
                "log_level": "INFO",
                "data_dir": "",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value
        self._save()

    def get_llm_config(self, provider: str | None = None) -> dict:
        """Get active LLM config for model creation."""
        provider = provider or self._config.get("active_provider", Provider.OPENAI)
        prov_cfg = self._config.get("providers", {}).get(provider, {})
        gen = self._config.get("generation", {})
        return {
            "provider": provider,
            "base_url": prov_cfg.get("base_url", PROVIDER_DEFAULT_BASE_URL.get(Provider(provider), "")),
            "api_key_ref": prov_cfg.get("api_key_ref", ""),
            "model": prov_cfg.get("model", self._config.get("active_model", "gpt-4o")),
            "temperature": gen.get("temperature", DEFAULT_TEMPERATURE),
            "max_tokens": gen.get("max_tokens", DEFAULT_MAX_TOKENS),
            "streaming": True,
        }

    def get_embedding_config(self) -> dict:
        return self._config.get("embedding", {
            "provider": EMBEDDING_PROVIDER,
            "model": EMBEDDING_MODEL,
            "dimension": EMBEDDING_DIMENSION,
        })

    def get_generation_params(self) -> dict:
        return self._config.get("generation", {})

    def get_kb_params(self) -> dict:
        return self._config.get("knowledge_base", {})

    def get_routing_params(self) -> dict:
        return self._config.get("routing", {})

    def get_system_prompt(self) -> str:
        return self._config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

    def set_system_prompt(self, prompt: str):
        self._config["system_prompt"] = prompt
        self._save()

    def get_active_provider(self) -> str:
        return self._config.get("active_provider", Provider.OPENAI)

    def get_active_model(self) -> str:
        return self._config.get("active_model", "gpt-4o")

    def set_active_model(self, provider: str, model: str):
        self._config["active_provider"] = provider
        self._config["active_model"] = model
        self._save()

    def get_provider_config(self, provider: str) -> dict:
        return self._config.get("providers", {}).get(provider, {
            "base_url": PROVIDER_DEFAULT_BASE_URL.get(Provider(provider) if provider in [e.value for e in Provider] else "", ""),
            "model": PROVIDER_DEFAULT_MODELS.get(Provider(provider) if provider in [e.value for e in Provider] else "", [""])[0] if PROVIDER_DEFAULT_MODELS.get(Provider(provider) if provider in [e.value for e in Provider] else "", []) else "",
            "api_key_ref": "",
            "enabled": False,
        })

    def set_provider_config(self, provider: str, base_url: str, model: str, api_key: str):
        if "providers" not in self._config:
            self._config["providers"] = {}
        key_ref = f"{provider}_api_key"
        if api_key:
            store_secret(key_ref, api_key)
        self._config["providers"][provider] = {
            "base_url": base_url,
            "model": model,
            "api_key_ref": key_ref,
            "enabled": True,
        }
        self._save()

    def set_embedding_config(self, provider: str, model: str, api_key: str, base_url: str = ""):
        key_ref = "embedding_api_key"
        if api_key:
            store_secret(key_ref, api_key)
        self._config["embedding"] = {
            "provider": provider,
            "model": model,
            "dimension": EMBEDDING_DIMENSION,
            "base_url": base_url or PROVIDER_DEFAULT_BASE_URL.get(Provider.QWEN, ""),
            "api_key_ref": key_ref,
        }
        self._save()

    def set_generation_params(self, temperature: float = None, top_p: float = None,
                               max_tokens: int = None, context_rounds: int = None):
        gen = self._config.get("generation", {})
        if temperature is not None:
            gen["temperature"] = temperature
        if top_p is not None:
            gen["top_p"] = top_p
        if max_tokens is not None:
            gen["max_tokens"] = max_tokens
        if context_rounds is not None:
            gen["context_rounds"] = context_rounds
        self._config["generation"] = gen
        self._save()

    def set_kb_params(self, chunk_size: int = None, chunk_overlap: float = None,
                      top_k: int = None, similarity_threshold: float = None):
        kb = self._config.get("knowledge_base", {})
        if chunk_size is not None:
            kb["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            kb["chunk_overlap"] = chunk_overlap
        if top_k is not None:
            kb["top_k"] = top_k
        if similarity_threshold is not None:
            kb["similarity_threshold"] = similarity_threshold
        self._config["knowledge_base"] = kb
        self._save()

    def is_provider_configured(self, provider: str) -> bool:
        prov = self._config.get("providers", {}).get(provider, {})
        return prov.get("enabled", False) and bool(prov.get("api_key_ref", ""))

    def get_configured_providers(self) -> list[str]:
        return [p for p, cfg in self._config.get("providers", {}).items() if cfg.get("enabled")]

    async def test_provider_connection(self, provider: str) -> dict:
        cfg = self.get_llm_config(provider)
        return await test_connection(cfg)

    def get_all_config(self) -> dict:
        return self._config.copy()
