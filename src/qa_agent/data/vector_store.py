"""Milvus vector store: Lite (embedded) and Standalone support."""

import asyncio
from typing import Any

from ..constants import EMBEDDING_DIMENSION, MILVUS_DB_PATH
from ..infra.logging import logger


class VectorStore:
    """Milvus vector store wrapper."""

    def __init__(self, uri: str | None = None):
        self._uri = uri or MILVUS_DB_PATH
        self._client = None
        self._collection = "qa_documents"

    def init(self):
        """Initialize Milvus client and create collection if needed."""
        from pymilvus import MilvusClient
        self._client = MilvusClient(uri=self._uri)
        if not self._client.has_collection(self._collection):
            from pymilvus import CollectionSchema, DataType, FieldSchema
            schema = self._client.create_schema(auto_id=True, enable_dynamic_field=True)
            schema.add_field("id", DataType.INT64, is_primary=True)
            schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=EMBEDDING_DIMENSION)
            schema.add_field("doc_id", DataType.VARCHAR, max_length=64)
            schema.add_field("file_name", DataType.VARCHAR, max_length=256)
            schema.add_field("page_or_par", DataType.VARCHAR, max_length=64)
            schema.add_field("chunk_seq", DataType.INT64)
            schema.add_field("content", DataType.VARCHAR, max_length=65535)
            schema.add_field("uploaded_at", DataType.VARCHAR, max_length=32)

            index_params = self._client.prepare_index_params()
            index_params.add_index(
                field_name="embedding",
                metric_type="COSINE",
                index_type="FLAT",
            )
            self._client.create_collection(
                collection_name=self._collection,
                schema=schema,
                index_params=index_params,
            )
            logger.info("Created Milvus collection: %s", self._collection)
        else:
            logger.info("Milvus collection exists: %s", self._collection)

    def upsert(self, vectors: list[list[float]], metadatas: list[dict[str, Any]]):
        """Insert vectors with metadata."""
        if not vectors:
            return
        data = []
        for vec, meta in zip(vectors, metadatas):
            data.append({
                "embedding": vec,
                "doc_id": str(meta.get("doc_id", "")),
                "file_name": str(meta.get("file_name", "")),
                "page_or_par": str(meta.get("page_or_par", "")),
                "chunk_seq": int(meta.get("chunk_seq", 0)),
                "content": str(meta.get("content", ""))[:65000],
                "uploaded_at": str(meta.get("uploaded_at", "")),
            })
        self._client.insert(collection_name=self._collection, data=data)
        logger.info("Inserted %d vectors", len(data))

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Search for similar vectors."""
        results = self._client.search(
            collection_name=self._collection,
            data=[query_vector],
            limit=top_k,
            output_fields=["doc_id", "file_name", "page_or_par", "chunk_seq", "content"],
        )
        docs = []
        if results and results[0]:
            for hit in results[0]:
                entity = hit.get("entity", {})
                docs.append({
                    "doc_id": entity.get("doc_id", ""),
                    "file_name": entity.get("file_name", ""),
                    "page_or_par": entity.get("page_or_par", ""),
                    "chunk_seq": entity.get("chunk_seq", 0),
                    "content": entity.get("content", ""),
                    "score": hit.get("distance", 0.0),
                })
        return docs

    def delete_by_doc_id(self, doc_id: str):
        """Delete all vectors for a document."""
        self._client.delete(
            collection_name=self._collection,
            filter=f'doc_id == "{doc_id}"',
        )
        logger.info("Deleted vectors for doc_id: %s", doc_id)

    def count(self) -> int:
        """Count total vectors in collection."""
        stats = self._client.get_collection_stats(self._collection)
        return int(stats.get("row_count", 0))

    def drop_collection(self):
        """Drop the entire collection."""
        if self._client.has_collection(self._collection):
            self._client.drop_collection(self._collection)
            logger.info("Dropped collection: %s", self._collection)

    async def async_upsert(self, vectors: list[list[float]], metadatas: list[dict]):
        return await asyncio.to_thread(self.upsert, vectors, metadatas)

    async def async_search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        return await asyncio.to_thread(self.search, query_vector, top_k)

    async def async_delete_by_doc_id(self, doc_id: str):
        return await asyncio.to_thread(self.delete_by_doc_id, doc_id)

    async def async_count(self) -> int:
        return await asyncio.to_thread(self.count)
