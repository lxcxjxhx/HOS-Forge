"""Semantic search API for knowledge base."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from hosforge.knowledge.embeddings import EmbeddingGenerator
from hosforge.knowledge.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Structured search result."""

    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    doc_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "doc_id": self.doc_id,
        }


class SemanticSearcher:
    """Semantic search engine combining embeddings with FAISS."""

    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        vector_store: VectorStore,
    ):
        self._generator = embedding_generator
        self._store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[SearchResult]:
        if not query.strip():
            return []
        query_vec = self._generator.encode_query(query)
        raw_results = self._store.search(query_vec, top_k=top_k, threshold=threshold)
        results = []
        for r in raw_results:
            doc = r["document"]
            results.append(
                SearchResult(
                    content=doc.get("content", ""),
                    score=r["score"],
                    metadata=doc.get("metadata", {}),
                    doc_id=r.get("id", ""),
                )
            )
        return results

    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        batch_size: int = 64,
    ) -> int:
        if not texts:
            return 0
        if metadatas is None:
            metadatas = [{} for _ in texts]
        if ids is None:
            ids = [str(i) for i in range(len(texts))]
        total = len(texts)
        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            batch_texts = texts[start:end]
            batch_metas = metadatas[start:end]
            batch_ids = ids[start:end]
            vectors = self._generator.encode(batch_texts)
            documents = [
                {"content": text, "metadata": meta}
                for text, meta in zip(batch_texts, batch_metas, strict=False)
            ]
            self._store.add(vectors, documents, batch_ids)
        return total
