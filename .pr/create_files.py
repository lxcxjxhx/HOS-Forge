"""Script to create knowledge vector search module files."""
import os

BASE = 'hosforge/knowledge'

files = {}

files['vector_store.py'] = '''"""Vector store module using FAISS for similarity search."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for similarity search."""

    def __init__(
        self,
        embedding_dim: int,
        index_type: str = "flat",
        use_gpu: bool = False,
    ):
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.use_gpu = use_gpu
        self._index: faiss.Index | None = None
        self._documents: list[dict[str, Any]] = []
        self._id_to_idx: dict[str, int] = {}
        self._create_index()

    def _create_index(self) -> None:
        if self.index_type == "flat":
            self._index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info(f"Created FlatL2 index with dim={self.embedding_dim}")
        elif self.index_type == "ivf":
            nlist = 100
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self._index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
            logger.info(f"Created IVFFlat index with dim={self.embedding_dim}, nlist={nlist}")
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

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
        if self._index is None:
            raise RuntimeError("Index not initialized")
        if len(vectors) != len(documents):
            raise ValueError("vectors and documents must have same length")
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
        if self._index is None:
            raise RuntimeError("Index not initialized")
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
            results.append({"document": doc, "score": float(score), "id": doc_id})
        return results

    def _get_id_by_idx(self, idx: int) -> str:
        for doc_id, doc_idx in self._id_to_idx.items():
            if doc_idx == idx:
                return doc_id
        return str(idx)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        if self._index is not None:
            faiss.write_index(self._index, str(path / "index.faiss"))
            logger.info(f"Saved FAISS index to {path / 'index.faiss'}")
        with open(path / "documents.json", "w", encoding="utf-8") as f:
            json.dump({"documents": self._documents, "id_to_idx": self._id_to_idx}, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved documents to {path / 'documents.json'}")

    def load(self, path: str | Path) -> None:
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
            logger.info(f"Loaded {len(self._documents)} documents")

    @property
    def size(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal

    def clear(self) -> None:
        self._create_index()
        self._documents = []
        self._id_to_idx = {}
        logger.info("Cleared vector store")
'''

files['search.py'] = '''"""Semantic search API for knowledge base."""

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
'''

files['indexer.py'] = '''"""Index builder and persistence for knowledge base."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

from hosforge.knowledge.embeddings import EmbeddingGenerator
from hosforge.knowledge.search import SemanticSearcher
from hosforge.knowledge.vector_store import VectorStore

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".yaml", ".yml",
    ".json", ".html", ".css", ".sh", ".bash", ".toml",
    ".cfg", ".ini", ".xml", ".rst",
}


class KnowledgeIndexer:
    """Build and manage knowledge base index from files/directories."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_dir: str = "~/.hosforge/vector_index",
        device: str = "cpu",
        index_type: str = "flat",
    ):
        self._index_dir = Path(index_dir).expanduser()
        self._generator = EmbeddingGenerator(model_name=model_name, device=device)
        self._store = VectorStore(
            embedding_dim=self._generator.embedding_dim,
            index_type=index_type,
        )
        self._searcher = SemanticSearcher(self._generator, self._store)
        self._hash_file = self._index_dir / "file_hashes.json"
        self._file_hashes: dict[str, str] = {}

    @property
    def searcher(self) -> SemanticSearcher:
        return self._searcher

    @property
    def store(self) -> VectorStore:
        return self._store

    def build_from_directory(
        self,
        directory: str | Path,
        extensions: set[str] | None = None,
        batch_size: int = 64,
        recursive: bool = True,
    ) -> int:
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        exts = extensions or SUPPORTED_EXTENSIONS
        files = []
        if recursive:
            for root, _, filenames in os.walk(directory):
                for fname in filenames:
                    fpath = Path(root) / fname
                    if fpath.suffix.lower() in exts:
                        files.append(fpath)
        else:
            for fpath in directory.iterdir():
                if fpath.is_file() and fpath.suffix.lower() in exts:
                    files.append(fpath)
        logger.info(f"Found {len(files)} files to index in {directory}")
        return self._index_files(files, batch_size)

    def build_from_files(
        self,
        files: list[str | Path],
        batch_size: int = 64,
    ) -> int:
        file_paths = [Path(f) for f in files]
        return self._index_files(file_paths, batch_size)

    def _index_files(self, files: list[Path], batch_size: int) -> int:
        import json
        self._load_hashes()
        texts: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []
        new_count = 0
        for fpath in files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to read {fpath}: {e}")
                continue
            file_hash = hashlib.md5(content.encode()).hexdigest()
            str_path = str(fpath)
            if str_path in self._file_hashes and self._file_hashes[str_path] == file_hash:
                continue
            chunks = self._chunk_text(content, fpath.name)
            for i, chunk in enumerate(chunks):
                doc_id = f"{str_path}::chunk_{i}"
                meta = {
                    "source": str_path,
                    "filename": fpath.name,
                    "extension": fpath.suffix,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                texts.append(chunk)
                metadatas.append(meta)
                ids.append(doc_id)
            self._file_hashes[str_path] = file_hash
            new_count += 1
        if texts:
            self._searcher.add_documents(texts, metadatas, ids, batch_size=batch_size)
        self._save_hashes()
        logger.info(f"Indexed {new_count} new/updated files, {len(texts)} chunks total")
        return len(texts)

    def _chunk_text(
        self,
        text: str,
        filename: str = "",
        chunk_size: int = 512,
        overlap: int = 64,
    ) -> list[str]:
        if len(text) <= chunk_size:
            return [text]
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
        return chunks

    def _load_hashes(self) -> None:
        import json
        if self._hash_file.exists():
            with open(self._hash_file, "r", encoding="utf-8") as f:
                self._file_hashes = json.load(f)

    def _save_hashes(self) -> None:
        import json
        self._index_dir.mkdir(parents=True, exist_ok=True)
        with open(self._hash_file, "w", encoding="utf-8") as f:
            json.dump(self._file_hashes, f, ensure_ascii=False, indent=2)

    def save(self) -> None:
        self._store.save(self._index_dir)
        self._save_hashes()
        logger.info(f"Saved index to {self._index_dir}")

    def load(self) -> None:
        if self._index_dir.exists():
            self._store.load(self._index_dir)
            self._load_hashes()
            logger.info(f"Loaded index from {self._index_dir}")

    def update_incremental(
        self,
        directory: str | Path,
        batch_size: int = 64,
    ) -> int:
        return self.build_from_directory(directory, batch_size=batch_size)
'''

for fname, content in files.items():
    fpath = os.path.join(BASE, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created {fpath}')

print('All files created successfully!')
