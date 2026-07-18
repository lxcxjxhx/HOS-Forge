"""
HOS-Forge RAG Tagging Engine — 安全知识 RAG 打标与向量强化引擎。

核心功能:
    1. 对 CVE/CWE/ExploitDB 知识做向量嵌入与打标
    2. 用微调模型对安全知识做语义增强
    3. 生成 RAG 可检索的知识索引
    4. 支持本地模型离线打标

适用场景:
    - 企业私有安全知识库的 RAG 向量化
    - 用 LoRA 微调模型做特定领域的知识增强
    - 自动化安全知识打标分类
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TaggedChunk:
    """打标后的知识块"""
    chunk_id: str = ''
    content: str = ''
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    source: str = ''        # cve|cwe|exploitdb|custom
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'content': self.content[:300],
            'tags': self.tags,
            'source': self.source,
            'confidence': self.confidence,
        }


@dataclass
class TaggingConfig:
    """RAG 打标配置"""
    chunk_size: int = 512
    chunk_overlap: int = 64
    min_confidence: float = 0.5
    enable_embedding: bool = True
    model_path: str = ''        # 本地模型路径
    device: str = 'auto'        # auto|cpu|cuda
    batch_size: int = 32


class SecurityRAGTagger:
    """
    安全知识 RAG 打标器。

    将 CVE/CWE/ExploitDB 等安全知识进行:
        1. 文本分块 (chunking)
        2. 安全标签提取 (tagging)
        3. 向量嵌入生成 (embedding)
        4. 置信度评分 (confidence)
    """

    def __init__(self, config: TaggingConfig | None = None):
        self.config = config or TaggingConfig()
        self._model = None
        self._tokenizer = None

    async def tag_cve_entry(
        self,
        cve_id: str,
        description: str,
        severity: str = '',
    ) -> TaggedChunk:
        """
        对 CVE 条目打标。

        Args:
            cve_id: CVE 编号
            description: CVE 描述
            severity: 严重级别

        Returns:
            TaggedChunk: 打标结果
        """
        tags = self._extract_security_tags(description)
        if severity:
            tags.append(f'severity:{severity.lower()}')

        return TaggedChunk(
            chunk_id=f'cve-{cve_id}',
            content=description,
            tags=list(set(tags)),
            source='cve',
            confidence=0.85 if severity else 0.6,
            metadata={'cve_id': cve_id, 'severity': severity},
        )

    async def tag_cwe_entry(
        self,
        cwe_id: str,
        name: str,
        description: str,
    ) -> TaggedChunk:
        """
        对 CWE 分类打标。
        """
        tags = self._extract_security_tags(f'{name} {description}')
        tags.append(f'cwe:{cwe_id}')

        # 推断缺陷类型
        weakness_types = self._classify_weakness(description)
        tags.extend(weakness_types)

        return TaggedChunk(
            chunk_id=f'cwe-{cwe_id}',
            content=f'{name}: {description}',
            tags=list(set(tags)),
            source='cwe',
            confidence=0.9,
            metadata={'cwe_id': cwe_id, 'name': name},
        )

    async def chunk_knowledge_base(
        self,
        entries: list[dict[str, Any]],
        source: str = 'custom',
    ) -> list[TaggedChunk]:
        """
        将知识库条目分块并打标。

        Args:
            entries: 知识条目列表 [{id, title, content, ...}]
            source: 来源标识

        Returns:
            list[TaggedChunk]: 打标后的知识块
        """
        chunks: list[TaggedChunk] = []
        for entry in entries:
            content = entry.get('content', '') or entry.get('description', '')
            title = entry.get('title', '') or entry.get('name', '')
            entry_id = entry.get('id', '')

            if not content:
                continue

            # 简单分块
            text_parts = self._split_text(
                f'{title}\n\n{content}',
                self.config.chunk_size,
                self.config.chunk_overlap,
            )

            for i, part in enumerate(text_parts):
                tags = self._extract_security_tags(part)
                chunks.append(TaggedChunk(
                    chunk_id=f'{source}-{entry_id}-{i}' if entry_id else f'{source}-{i}',
                    content=part,
                    tags=tags,
                    source=source,
                    confidence=0.7,
                    metadata={'entry_id': entry_id, 'title': title, 'chunk_idx': i},
                ))

        logger.info('Chunked %d entries into %d tagged chunks', len(entries), len(chunks))
        return chunks

    async def export_to_jsonl(
        self,
        chunks: list[TaggedChunk],
        output_path: str,
    ) -> str:
        """
        导出打标结果为 JSONL 格式（用于微调训练）。

        Args:
            chunks: 打标后的知识块
            output_path: 输出路径

        Returns:
            str: 输出文件路径
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                record = {
                    'id': chunk.chunk_id,
                    'instruction': 'Classify and explain this security vulnerability',
                    'input': chunk.content[:1000],
                    'output': json.dumps({
                        'tags': chunk.tags,
                        'confidence': chunk.confidence,
                        'source': chunk.source,
                    }, ensure_ascii=False),
                    'metadata': chunk.metadata,
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        logger.info('Exported %d tagged chunks to %s', len(chunks), output_path)
        return str(path)

    def _extract_security_tags(self, text: str) -> list[str]:
        """
        从文本中提取安全标签。

        覆盖信息安全全领域:
            - Web 安全: sql-injection, xss, ssrf, csrf
            - 数据安全: data-leak, encryption, privacy
            - 终端安全: malware, ransomware, privilege-escalation
            - 密码学: cryptographic, hashing, signing
            - 云安全: cloud-misconfig, iam, container
            - 应用安全: auth-bypass, logic-flaw, race-condition
        """
        text_lower = text.lower()
        tags: list[str] = []

        # 注入类
        if any(w in text_lower for w in ['sql', 'injection', 'sqli']):
            tags.append('sql-injection')
        if any(w in text_lower for w in ['cross-site', 'xss', 'script']):
            tags.append('xss')
        if 'command injection' in text_lower or 'command_injection' in text_lower:
            tags.append('command-injection')
        if 'ssrf' in text_lower or 'server-side request' in text_lower:
            tags.append('ssrf')

        # 认证与授权
        if any(w in text_lower for w in ['authentication', 'auth bypass', 'authn']):
            tags.append('authentication')
        if any(w in text_lower for w in ['authorization', 'privilege', 'permission', 'access control']):
            tags.append('authorization')
        if 'privilege escalation' in text_lower or 'priv esc' in text_lower:
            tags.append('privilege-escalation')

        # 数据安全
        if any(w in text_lower for w in ['data leak', 'information disclosure', 'sensitive data']):
            tags.append('data-leakage')
        if any(w in text_lower for w in ['encryption', 'cryptographic', 'cipher']):
            tags.append('cryptography')
        if any(w in text_lower for w in ['privacy', 'pii', 'personal data']):
            tags.append('privacy')

        # 终端安全
        if any(w in text_lower for w in ['malware', 'ransomware', 'trojan']):
            tags.append('malware')
        if any(w in text_lower for w in ['buffer overflow', 'heap overflow', 'stack overflow']):
            tags.append('buffer-overflow')
        if any(w in text_lower for w in ['memory corruption', 'use-after-free', 'dangling pointer']):
            tags.append('memory-corruption')

        # 云安全
        if any(w in text_lower for w in ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'k8s']):
            tags.append('cloud-security')
        if any(w in text_lower for w in ['container', 'docker', 'pod']):
            tags.append('container-security')
        if 'iam' in text_lower or 'identity' in text_lower:
            tags.append('identity-access')

        # 网络与协议
        if any(w in text_lower for w in ['dns', 'tcp', 'udp', 'network']):
            tags.append('network-security')
        if any(w in text_lower for w in ['man-in-the-middle', 'mitm', 'spoofing']):
            tags.append('network-attack')

        # 通用安全分类
        if any(w in text_lower for w in ['denial of service', 'dos', 'ddos']):
            tags.append('denial-of-service')
        if any(w in text_lower for w in ['race condition', 'race_condition', 'time-of-check']):
            tags.append('race-condition')
        if 'deserialization' in text_lower or 'pickle' in text_lower:
            tags.append('insecure-deserialization')
        if 'path traversal' in text_lower or 'directory traversal' in text_lower:
            tags.append('path-traversal')

        return tags

    def _classify_weakness(self, description: str) -> list[str]:
        """对漏洞类型分类"""
        desc_lower = description.lower()
        types = []

        if any(w in desc_lower for w in ['input validation', 'sanitization', 'filtering']):
            types.append('input-validation')
        if any(w in desc_lower for w in ['resource management', 'memory leak', 'resource leak']):
            types.append('resource-management')
        if any(w in desc_lower for w in ['error handling', 'exception', 'error message']):
            types.append('error-handling')
        if any(w in desc_lower for w in ['configuration', 'misconfig', 'settings']):
            types.append('misconfiguration')

        return types

    @staticmethod
    def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
        """将文本分割为重叠块"""
        if len(text) <= chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                # 在最后一个空格处断开
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            chunks.append(text[start:end].strip())
            start = end - overlap
            if start < 0:
                start = 0

        return chunks


class RAGTaggingEngine:
    """
    RAG 打标引擎 — 批量处理安全知识库的完整流水线。

    流程:
        1. 从知识库读取条目
        2. 用 SecurityRAGTagger 打标
        3. 生成向量嵌入 (可选)
        4. 导出为微调/检索格式
    """

    def __init__(self, tagger: SecurityRAGTagger | None = None):
        self.tagger = tagger or SecurityRAGTagger()
        self._chunks: list[TaggedChunk] = []

    async def process_cve_database(
        self,
        db_path: str,
        output_path: str = '',
    ) -> str:
        """
        批量处理 CVE 数据库。

        Args:
            db_path: CVE JSON 文件路径
            output_path: JSONL 输出路径

        Returns:
            str: 输出文件路径
        """
        with open(db_path, 'r') as f:
            data = json.load(f)

        entries = data if isinstance(data, list) else data.get('vulnerabilities', [])
        processed = []

        for item in entries[:1000]:  # 批量限制
            cve = item.get('cve', item)
            cve_id = cve.get('id', '')
            description = ''
            for desc in cve.get('descriptions', []):
                if desc.get('lang') == 'en':
                    description = desc.get('value', '')
                    break

            if cve_id and description:
                chunk = await self.tagger.tag_cve_entry(cve_id, description)
                self._chunks.append(chunk)
                processed.append({
                    'id': cve_id,
                    'content': description,
                    'tags': chunk.tags,
                })

        logger.info('Processed %d CVE entries', len(processed))

        if output_path:
            return await self.tagger.export_to_jsonl(self._chunks, output_path)

        return str(len(processed))

    async def process_knowledge_base(
        self,
        entries: list[dict[str, Any]],
        source: str = 'custom',
        output_path: str = '',
    ) -> str:
        """
        批量处理知识库条目。
        """
        self._chunks = await self.tagger.chunk_knowledge_base(entries, source)

        if output_path:
            return await self.tagger.export_to_jsonl(self._chunks, output_path)

        return f'Tagged {len(self._chunks)} chunks'

    def get_statistics(self) -> dict[str, Any]:
        """获取打标统计"""
        tag_count: dict[str, int] = {}
        source_count: dict[str, int] = {}

        for chunk in self._chunks:
            source_count[chunk.source] = source_count.get(chunk.source, 0) + 1
            for tag in chunk.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1

        return {
            'total_chunks': len(self._chunks),
            'unique_tags': len(tag_count),
            'sources': source_count,
            'top_tags': sorted(tag_count.items(), key=lambda x: -x[1])[:20],
        }
