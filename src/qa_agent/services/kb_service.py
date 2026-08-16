"""Knowledge base service: upload → parse → split → vectorize → search orchestration."""

import asyncio
import os
import shutil
from datetime import datetime
from typing import Callable, Optional

from ..constants import DocStatus, SUPPORTED_FILE_TYPES
from ..data.parsers import parse_document
from ..data.splitter import split_text
from ..data.vector_store import VectorStore
from ..data.embeddings import create_embeddings
from ..data.repositories.document_repo import DocumentRepository
from ..services.config_service import ConfigService
from ..infra.logging import logger


class KnowledgeBaseService:
    """Orchestrates the knowledge base pipeline."""

    def __init__(self, config_service: ConfigService, data_dir: str = "kb_data"):
        self._config = config_service
        self._doc_repo = DocumentRepository()
        self._data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.on_progress: Optional[Callable[[str, str, float], None]] = None

    def _emit_progress(self, doc_id: str, status: str, progress: float):
        if self.on_progress:
            self.on_progress(doc_id, status, progress)

    async def upload_documents(self, file_paths: list[str]) -> list[dict]:
        """Upload and process multiple documents. Returns list of document records."""
        results = []
        for fp in file_paths:
            try:
                result = await self._ingest_single(fp)
                results.append(result)
            except Exception as e:
                logger.error("Failed to ingest %s: %s", fp, e)
                results.append({"file_name": os.path.basename(fp), "status": DocStatus.FAILED, "error": str(e)})
        return results

    async def _ingest_single(self, file_path: str) -> dict:
        """Process a single document through the full pipeline."""
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext not in SUPPORTED_FILE_TYPES:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        dest = os.path.join(self._data_dir, file_name)
        if os.path.abspath(file_path) != os.path.abspath(dest):
            shutil.copy2(file_path, dest)

        file_size = os.path.getsize(dest)
        doc_record = self._doc_repo.create(file_name, file_ext, dest, file_size)
        doc_id = doc_record["id"]

        try:
            # Parse
            self._doc_repo.update_status(doc_id, DocStatus.PARSING, progress=0.0)
            self._emit_progress(doc_id, DocStatus.PARSING, 0.0)

            pages = await asyncio.to_thread(parse_document, dest)
            if not pages:
                raise ValueError("文档内容为空")

            self._doc_repo.update_status(doc_id, DocStatus.PARSING, progress=0.5)
            self._emit_progress(doc_id, DocStatus.PARSING, 0.5)

            # Split
            kb_params = self._config.get_kb_params()
            chunk_size = kb_params.get("chunk_size", 500)
            chunk_overlap = kb_params.get("chunk_overlap", 0.15)

            all_chunks = []
            for page in pages:
                text = page.get("text", "")
                page_num = str(page.get("page", 1))
                chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                for seq, chunk in enumerate(chunks):
                    all_chunks.append({
                        "text": chunk,
                        "page": page_num,
                        "seq": seq,
                    })

            if not all_chunks:
                raise ValueError("文档切分后无有效内容")

            # Vectorize
            self._doc_repo.update_status(doc_id, DocStatus.VECTORIZING, progress=0.0)
            self._emit_progress(doc_id, DocStatus.VECTORIZING, 0.0)

            embedding_config = self._config.get_embedding_config()
            emb_client = create_embeddings(embedding_config)

            batch_size = 50
            vs = VectorStore()
            vs.init()

            total_batches = (len(all_chunks) + batch_size - 1) // batch_size
            for batch_idx in range(total_batches):
                start = batch_idx * batch_size
                end = min(start + batch_size, len(all_chunks))
                batch = all_chunks[start:end]

                texts = [c["text"] for c in batch]
                vectors = await emb_client.aembed_texts(texts)

                metadatas = []
                for c in batch:
                    metadatas.append({
                        "doc_id": doc_id,
                        "file_name": file_name,
                        "page_or_par": f"第{c['page']}页",
                        "chunk_seq": c["seq"],
                        "content": c["text"],
                        "uploaded_at": datetime.now().isoformat(),
                    })

                await vs.async_upsert(vectors, metadatas)
                progress = (batch_idx + 1) / total_batches
                self._doc_repo.update_status(doc_id, DocStatus.VECTORIZING, progress=progress)
                self._emit_progress(doc_id, DocStatus.VECTORIZING, progress)

            self._doc_repo.update_status(doc_id, DocStatus.DONE, progress=1.0, chunk_count=len(all_chunks))
            self._emit_progress(doc_id, DocStatus.DONE, 1.0)
            logger.info("Document ingested: %s (%d chunks)", file_name, len(all_chunks))
            return self._doc_repo.get(doc_id)

        except Exception as e:
            self._doc_repo.update_status(doc_id, DocStatus.FAILED, error=str(e))
            self._emit_progress(doc_id, DocStatus.FAILED, 0.0)
            logger.error("Document ingestion failed: %s - %s", file_name, e)
            return self._doc_repo.get(doc_id)

    async def delete_document(self, doc_id: str):
        """Delete a document and its vectors."""
        doc = self._doc_repo.get(doc_id)
        if not doc:
            return

        vs = VectorStore()
        vs.init()
        await vs.async_delete_by_doc_id(doc_id)

        file_path = doc.get("file_path", "")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        self._doc_repo.delete(doc_id)
        logger.info("Document deleted: %s", doc.get("file_name", ""))

    async def reparse_document(self, doc_id: str):
        """Re-parse and re-vectorize a document."""
        doc = self._doc_repo.get(doc_id)
        if not doc:
            return

        vs = VectorStore()
        vs.init()
        await vs.async_delete_by_doc_id(doc_id)

        file_path = doc.get("file_path", "")
        if file_path and os.path.exists(file_path):
            await self._ingest_single(file_path)

    def list_documents(self) -> list[dict]:
        return self._doc_repo.list_all()

    def get_stats(self) -> dict:
        return self._doc_repo.get_stats()

    def has_documents(self) -> bool:
        return self._doc_repo.has_documents()

    async def rebuild_index(self):
        """Rebuild entire vector index (e.g., after embedding model change)."""
        vs = VectorStore()
        vs.init()
        vs.drop_collection()
        vs.init()

        docs = self._doc_repo.list_all()
        for doc in docs:
            if doc["status"] == DocStatus.DONE:
                self._doc_repo.update_status(doc["id"], DocStatus.QUEUED)

        for doc in docs:
            file_path = doc.get("file_path", "")
            if file_path and os.path.exists(file_path):
                await self._ingest_single(file_path)

        logger.info("Index rebuilt with %d documents", len(docs))

    def close(self):
        self._doc_repo.close()


KBService = KnowledgeBaseService
