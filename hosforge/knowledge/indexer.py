"""Index builder and persistence for knowledge base."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from hosforge.exceptions import KnowledgeBaseError
from hosforge.knowledge.embeddings import EmbeddingGenerator
from hosforge.knowledge.search import SemanticSearcher
from hosforge.knowledge.vector_store import VectorStore
from hosforge.logging_config import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".js",
    ".ts",
    ".yaml",
    ".yml",
    ".json",
    ".html",
    ".css",
    ".sh",
    ".bash",
    ".toml",
    ".cfg",
    ".ini",
    ".xml",
    ".rst",
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
            raise KnowledgeBaseError(f"Directory not found: {directory}")
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
