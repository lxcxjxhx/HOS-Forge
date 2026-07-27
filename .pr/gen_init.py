"""Generate __init__.py for knowledge module."""
import os

content = '''\
"""
HOS-Forge Knowledge - Security Knowledge Base (Enhanced).

Based on SQLite/vector database security knowledge management:
    - CVE vulnerability database (with CVSS scores)
    - CWE classification database (with mitigations)
    - ExploitDB exploitation database
    - KEV known exploited vulnerabilities
    - RAG retrieval interface
    - Vector search (FAISS)
"""

from hosforge.knowledge.base import (
    CVERecord,
    CWERecord,
    KnowledgeEntry,
    LocalKnowledgeBase,
    SecurityKnowledgeBase,
)
from hosforge.knowledge.embeddings import EmbeddingGenerator
from hosforge.knowledge.indexer import KnowledgeIndexer
from hosforge.knowledge.search import SearchResult, SemanticSearcher
from hosforge.knowledge.vector_store import VectorStore

__all__ = [
    "SecurityKnowledgeBase",
    "LocalKnowledgeBase",
    "KnowledgeEntry",
    "CVERecord",
    "CWERecord",
    "EmbeddingGenerator",
    "VectorStore",
    "SemanticSearcher",
    "SearchResult",
    "KnowledgeIndexer",
]
'''

fpath = os.path.join('hosforge', 'knowledge', '__init__.py')
with open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Updated {fpath}')
