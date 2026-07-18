"""
HOS-Forge Knowledge — 安全知识大脑 (增强版)。

基于 SQLite/向量数据库的安全知识管理：
    - CVE 漏洞库 (含 CVSS 评分)
    - CWE 分类库 (含缓解措施)
    - ExploitDB 利用库
    - KEV 已知利用漏洞
    - RAG 检索接口
"""

from hosforge.knowledge.base import (
    SecurityKnowledgeBase,
    LocalKnowledgeBase,
    KnowledgeEntry,
    CVERecord,
    CWERecord,
)

__all__ = [
    'SecurityKnowledgeBase',
    'LocalKnowledgeBase',
    'KnowledgeEntry',
    'CVERecord',
    'CWERecord',
]
