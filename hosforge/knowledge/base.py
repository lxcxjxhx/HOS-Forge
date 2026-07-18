"""
HOS-Forge Knowledge Base — 安全知识库基类。

管理CVE/CWE/ExploitDB等安全知识数据，
提供RAG检索接口供Agent查询。
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """知识条目"""
    id: str = ''
    title: str = ''
    content: str = ''
    source: str = ''       # cve|cwe|exploitdb|kev|custom
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None  # 向量嵌入


class SecurityKnowledgeBase(abc.ABC):
    """
    安全知识库抽象基类。

    提供：
        - 知识检索 (RAG)
        - 向量搜索
        - CVE/CWE 查询
        - 漏洞上下文关联
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    async def query(self, question: str, top_k: int = 5) -> list[KnowledgeEntry]:
        """
        检索安全知识。

        Args:
            question: 自然语言查询
            top_k: 返回结果数

        Returns:
            list[KnowledgeEntry]: 相关知识条目
        """
        ...

    @abc.abstractmethod
    async def get_cve(self, cve_id: str) -> KnowledgeEntry | None:
        """获取CVE详情"""
        ...

    @abc.abstractmethod
    async def get_cwe(self, cwe_id: str) -> KnowledgeEntry | None:
        """获取CWE详情"""
        ...

    async def explain_vulnerability(
        self,
        cwe_id: str,
        code_context: str = '',
    ) -> str:
        """
        解释漏洞原理。

        结合CWE描述和代码上下文生成安全解释。
        """
        cwe = await self.get_cwe(cwe_id)
        if not cwe:
            return f'No knowledge found for CWE {cwe_id}'

        explanation = f'## {cwe.title}\n\n{cwe.content}\n\n'
        if code_context:
            explanation += f'### 代码上下文\n```\n{code_context}\n```\n'
        return explanation
