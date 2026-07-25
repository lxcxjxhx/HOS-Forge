"""Vector store module using FAISS for similarity search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from hosforge.exceptions import KnowledgeBaseConnectionError, KnowledgeBaseError
from hosforge.logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    """FAISS-based vector store for similarity search.

    Attributes:
        embedding_dim: dimension of embedding vectors
        index_type: FAISS index type ('flat', 'ivf')
    """

    def __init__(
        self,
        embedding_dim: int,
        index_type: str = "flat",
        use_gpu: bool = False,
    ):
        """Initialize vector store.

        Args:
            embedding_dim: dimension of embedding vectors
            index_type: FAISS index type ('flat', 'ivf')
            use_gpu: whether to use GPU acceleration
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.use_gpu = use_gpu

        self._index: faiss.Index | None = None
        self._documents: list[dict[str, Any]] = []
        self._id_to_idx: dict[str, int] = {}

        self._create_index()

    def _create_index(self) -> None:
        """Create FAISS index."""
        if self.index_type == "flat":
            self._index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info(f"Created FlatL2 index with dim={self.embedding_dim}")
        elif self.index_type == "ivf":
            nlist = 100
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self._index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
            logger.info(f"Created IVFFlat index with dim={self.embedding_dim}, nlist={nlist}")
        else:
            raise KnowledgeBaseError(f"Unsupported index type: {self.index_type}")

        if self.use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self._index = faiss.index_cpu_to_gpu(res, 0, self._index)
                logger.info("Moved index to GPU")
            except Exception as e:
                logger.warning(f"Failed to move to GPU: {e}")

    def add(
        self,
        vectors: np.ndarray,
        documents: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> None:
        """Add vectors to index.

        Args:
            vectors: numpy array of shape (n, embedding_dim)
            documents: list of document metadata dicts
            ids: optional list of document IDs
        """
        if self._index is None:
            raise KnowledgeBaseConnectionError("Index not initialized")

        if len(vectors) != len(documents):
            raise KnowledgeBaseError("vectors and documents must have same length")

        if ids is None:
            ids = [str(i) for i in range(len(self._documents), len(self._documents) + len(vectors))]

        if self.index_type == "ivf" and not self._index.is_trained:
            logger.info("Training IVF index...")
            self._index.train(vectors)

        self._index.add(vectors.astype(np.float32))

        for doc, doc_id in zip(documents, ids, strict=False):
            idx = len(self._documents)
            self._documents.append(doc)
            self._id_to_idx[doc_id] = idx

        logger.info(f"Added {len(vectors)} vectors to index")

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: query vector of shape (embedding_dim,)
            top_k: number of results to return
            threshold: minimum similarity score (0-1)

        Returns:
            list of dicts with 'document', 'score', 'id' keys
        """
        if self._index is None:
            raise KnowledgeBaseConnectionError("Index not initialized")

        if len(self._documents) == 0:
            return []

        query_vector = query_vector.reshape(1, -1).astype(np.float32)

        k = min(top_k, len(self._documents))
        distances, indices = self._index.search(query_vector, k)

        results = []
        for idx, distance in zip(indices[0], distances[0], strict=False):
            if idx == -1:
                continue

            score = 1.0 / (1.0 + distance)

            if threshold is not None and score < threshold:
                continue

            doc = self._documents[idx]
            doc_id = self._get_id_by_idx(idx)

            results.append({
                "document": doc,
                "score": float(score),
                "id": doc_id,
            })

        return results

    def _get_id_by_idx(self, idx: int) -> str:
        """Get document ID by index."""
        for doc_id, doc_idx in self._id_to_idx.items():
            if doc_idx == idx:
                return doc_id
        return str(idx)

    def save(self, path: str | Path) -> None:
        """Save index and documents to disk.

        Args:
            path: directory path to save index
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if self._index is not None:
            index_path = path / "index.faiss"
            faiss.write_index(self._index, str(index_path))
            logger.info(f"Saved FAISS index to {index_path}")

        docs_path = path / "documents.json"
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump({
                "documents": self._documents,
                "id_to_idx": self._id_to_idx,
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved documents to {docs_path}")

    def load(self, path: str | Path) -> None:
        """Load index and documents from disk.

        Args:
            path: directory path to load index from
        """
        path = Path(path)

        index_path = path / "index.faiss"
        if index_path.exists():
            self._index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index from {index_path}")

        docs_path = path / "documents.json"
        if docs_path.exists():
            with open(docs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._documents = data["documents"]
                self._id_to_idx = data["id_to_idx"]
            logger.info(f"Loaded {len(self._documents)} documents from {docs_path}")

    @property
    def size(self) -> int:
        """Return number of vectors in index."""
        if self._index is None:
            return 0
        return self._index.ntotal

    def clear(self) -> None:
        """Clear all vectors and documents."""
        self._create_index()
        self._documents = []
        self._id_to_idx = {}
        logger.info("Cleared vector store")
