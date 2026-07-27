"""Generate search.py and indexer.py for knowledge vector search."""
import os

BASE = 'hosforge/knowledge'

SEARCH_PY = '''"""Semantic search API for knowledge base."""

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

INDEXER_PY = '''"""Index builder and persistence for knowledge base."""

from __future__ import annotations

import hashlib
import json
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
        files: list[Path] = []
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
            chunks = self._chunk_text(content)
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
        if self._hash_file.exists():
            with open(self._hash_file, "r", encoding="utf-8") as f:
                self._file_hashes = json.load(f)

    def _save_hashes(self) -> None:
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

for fname, content in [('search.py', SEARCH_PY), ('indexer.py', INDEXER_PY)]:
    fpath = os.path.join(BASE, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created {fpath}')

print('Done!')
