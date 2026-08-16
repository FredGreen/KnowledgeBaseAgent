"""Embedding factory: creates embedding client for vectorization."""

from typing import Any

from ..constants import EMBEDDING_MODEL, EMBEDDING_DIMENSION, PROVIDER_DEFAULT_BASE_URL, Provider
from ..infra.security import load_secret
from ..infra.logging import logger


class EmbeddingClient:
    """Unified embedding client wrapping LangChain embeddings."""

    def __init__(self, cfg: dict[str, Any]):
        self._cfg = cfg
        self._embeddings = self._create(cfg)

    def _create(self, cfg: dict[str, Any]):
        provider = cfg.get("provider", "qwen")
        model = cfg.get("model", EMBEDDING_MODEL)
        api_key = load_secret(cfg.get("api_key_ref", ""))

        if provider in (Provider.QWEN, Provider.CUSTOM, Provider.OPENAI):
            from langchain_openai import OpenAIEmbeddings
            base_url = cfg.get("base_url") or PROVIDER_DEFAULT_BASE_URL.get(
                Provider.QWEN if provider == Provider.QWEN else Provider.OPENAI, ""
            )
            return OpenAIEmbeddings(
                model=model,
                openai_api_key=api_key or "not-set",
                openai_api_base=base_url if base_url else None,
            )

        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key or "not-set",
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    async def aembed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._embeddings.aembed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)


def create_embeddings(cfg: dict[str, Any]) -> EmbeddingClient:
    """Create an EmbeddingClient from config."""
    return EmbeddingClient(cfg)


class EmbeddingFactory:
    """Factory for creating embedding clients."""

    @staticmethod
    def create(cfg: dict[str, Any]) -> EmbeddingClient:
        return EmbeddingClient(cfg)

    @staticmethod
    def create_from_config(config_service) -> EmbeddingClient:
        emb_cfg = config_service.get_embedding_config()
        return EmbeddingClient(emb_cfg)
