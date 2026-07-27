"""Embedding generation module using sentence-transformers."""

from __future__ import annotations

from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from hosforge.exceptions import KnowledgeBaseError
from hosforge.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Text embedding generator using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        cache_folder: str | None = None,
    ):
        """Initialize embedding generator.

        Args:
            model_name: sentence-transformers model name
            device: compute device ('cpu', 'cuda', 'mps')
            cache_folder: model cache directory
        """
        self.model_name = model_name
        self.device = device
        self._cache_folder = cache_folder

        logger.info(f"Loading embedding model: {model_name} on {device}")
        self._model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_folder,
        )
        self._embedding_dim = self._model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded, embedding dimension: {self._embedding_dim}")

    @property
    def embedding_dim(self) -> int:
        """Return embedding vector dimension."""
        return self._embedding_dim

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> np.ndarray:
        """Encode text list to vectors.

        Args:
            texts: text list to encode
            batch_size: batch size for processing
            show_progress: show progress bar
            normalize: normalize vectors for cosine similarity

        Returns:
            np.ndarray: shape (len(texts), embedding_dim) float array
        """
        if not texts:
            raise KnowledgeBaseError("texts list cannot be empty")

        processed_texts = [t if t.strip() else " " for t in texts]

        embeddings = self._model.encode(
            processed_texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
        )

        return np.array(embeddings, dtype=np.float32)

    def encode_single(
        self,
        text: str,
        normalize: bool = True,
    ) -> np.ndarray:
        """Encode single text to vector.

        Args:
            text: text to encode
            normalize: normalize vector

        Returns:
            np.ndarray: shape (embedding_dim,) 1D array
        """
        if not text.strip():
            text = " "

        embedding = self._model.encode(
            [text],
            normalize_embeddings=normalize,
        )
        return np.array(embedding[0], dtype=np.float32)

    def encode_query(
        self,
        query: str,
        normalize: bool = True,
    ) -> np.ndarray:
        """Encode query text for search.

        Args:
            query: query text
            normalize: normalize vector

        Returns:
            np.ndarray: query vector
        """
        return self.encode_single(query, normalize=normalize)

    def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            dict: model name, dimension, device info
        """
        return {
            "model_name": self.model_name,
            "embedding_dim": self._embedding_dim,
            "device": self.device,
            "max_seq_length": self._model.max_seq_length,
        }
