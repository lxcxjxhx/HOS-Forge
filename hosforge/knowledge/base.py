"""
HOS-Forge Knowledge Base — 安全知识大脑 (增强版)。

管理 CVE/CWE/ExploitDB/KEV 等安全知识数据，
提供 RAG 检索接口 + 本地 CVE 数据库 + ExploitDB PoC 查询。
"""

from __future__ import annotations

import abc
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
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

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content[:500] if self.content else '',
            'source': self.source,
            'tags': self.tags,
            'metadata': self.metadata,
        }


@dataclass
class CVERecord:
    """CVE 漏洞记录"""
    cve_id: str = ''
    description: str = ''
    severity: str = ''         # CRITICAL/HIGH/MEDIUM/LOW
    cvss_score: float = 0.0
    cvss_vector: str = ''
    cwe_ids: list[str] = field(default_factory=list)
    affected_products: list[str] = field(default_factory=list)
    exploit_available: bool = False
    kev: bool = False          # Known Exploited Vulnerabilities
    poc: str = ''              # PoC 代码/链接
    references: list[str] = field(default_factory=list)
    published_date: str = ''
    last_modified: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'cve_id': self.cve_id,
            'description': self.description[:300] if self.description else '',
            'severity': self.severity,
            'cvss_score': self.cvss_score,
            'cwe_ids': self.cwe_ids,
            'exploit_available': self.exploit_available,
            'kev': self.kev,
        }


@dataclass
class CWERecord:
    """CWE 弱分类记录"""
    cwe_id: str = ''
    name: str = ''
    description: str = ''
    extended_description: str = ''
    detection_methods: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    related_cwes: list[str] = field(default_factory=list)
    related_cves: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'cwe_id': self.cwe_id,
            'name': self.name,
            'description': self.description[:300] if self.description else '',
        }


class SecurityKnowledgeBase(abc.ABC):
    """
    安全知识库抽象基类。

    提供：
        - RAG 知识检索
        - CVE 数据库查询
        - CWE 分类查询
        - ExploitDB PoC 检索
        - KEV 已知利用漏洞查询
        - 漏洞上下文解释
    """

    def __init__(self, db_path: str = ''):
        self._db_path = db_path
        self._db: sqlite3.Connection | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    async def query(self, question: str, top_k: int = 5) -> list[KnowledgeEntry]:
        """
        检索安全知识 (RAG)。

        Args:
            question: 自然语言查询
            top_k: 返回结果数

        Returns:
            list[KnowledgeEntry]: 相关知识条目
        """
        ...

    @abc.abstractmethod
    async def get_cve(self, cve_id: str) -> CVERecord | None:
        """获取 CVE 详情"""
        ...

    @abc.abstractmethod
    async def get_cwe(self, cwe_id: str) -> CWERecord | None:
        """获取 CWE 详情"""
        ...

    async def search_cve(
        self,
        keyword: str = '',
        severity: str = '',
        limit: int = 20,
    ) -> list[CVERecord]:
        """
        搜索 CVE 漏洞。

        Args:
            keyword: 关键词搜索
            severity: 按严重级别过滤
            limit: 返回条数

        Returns:
            list[CVERecord]: CVE 记录列表
        """
        raise NotImplementedError

    async def search_cwe(
        self,
        keyword: str = '',
        limit: int = 20,
    ) -> list[CWERecord]:
        """搜索 CWE 分类"""
        raise NotImplementedError

    async def get_exploit_poc(self, cve_id: str) -> str:
        """
        获取 CVE 对应的 PoC 利用代码。

        Args:
            cve_id: CVE 编号

        Returns:
            str: PoC 代码/描述
        """
        return ''

    async def check_kev(self, cve_id: str) -> bool:
        """
        检查 CVE 是否在 KEV (已知利用漏洞) 目录中。
        """
        return False

    async def explain_vulnerability(
        self,
        cwe_id: str = '',
        cve_id: str = '',
        code_context: str = '',
    ) -> str:
        """
        解释漏洞原理。

        结合 CWE 描述、CVE 详情和代码上下文生成安全解释。

        Args:
            cwe_id: CWE 编号 (可选)
            cve_id: CVE 编号 (可选)
            code_context: 代码上下文

        Returns:
            str: 解释文本
        """
        parts: list[str] = []

        if cve_id:
            cve = await self.get_cve(cve_id)
            if cve:
                parts.append(
                    f'## {cve.cve_id}\n\n'
                    f'- **严重程度**: {cve.severity} (CVSS: {cve.cvss_score})\n'
                    f'- **描述**: {cve.description}\n'
                    f'- **CWE**: {", ".join(cve.cwe_ids) if cve.cwe_ids else "N/A"}\n'
                    f'- **可利用**: {"是" if cve.exploit_available else "否"}\n'
                    f'- **KEV**: {"是" if cve.kev else "否"}\n'
                )

        if cwe_id:
            cwe = await self.get_cwe(cwe_id)
            if cwe:
                parts.append(
                    f'## {cwe.cwe_id}: {cwe.name}\n\n'
                    f'{cwe.description}\n\n'
                )
                if cwe.mitigations:
                    parts.append('### 缓解措施\n')
                    for m in cwe.mitigations:
                        parts.append(f'- {m}\n')

        if code_context:
            parts.append(f'### 代码上下文\n```\n{code_context}\n```\n')

        return '\n'.join(parts) if parts else '未找到相关漏洞知识。'


class LocalKnowledgeBase(SecurityKnowledgeBase):
    """
    本地安全知识库实现。

    使用 SQLite 存储 CVE/CWE 数据，支持关键词搜索。
    适用于离线环境或轻量级部署。
    """

    CVE_TABLE = '''
        CREATE TABLE IF NOT EXISTS cve (
            cve_id TEXT PRIMARY KEY,
            description TEXT,
            severity TEXT,
            cvss_score REAL,
            cvss_vector TEXT,
            exploit_available INTEGER DEFAULT 0,
            kev INTEGER DEFAULT 0,
            published_date TEXT,
            last_modified TEXT,
            raw_json TEXT
        )
    '''
    CWE_TABLE = '''
        CREATE TABLE IF NOT EXISTS cwe (
            cwe_id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            extended_description TEXT,
            mitigations TEXT,
            raw_json TEXT
        )
    '''
    CVE_CWE_TABLE = '''
        CREATE TABLE IF NOT EXISTS cve_cwe (
            cve_id TEXT,
            cwe_id TEXT,
            PRIMARY KEY (cve_id, cwe_id)
        )
    '''
    EXPLOIT_TABLE = '''
        CREATE TABLE IF NOT EXISTS exploit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cve_id TEXT,
            title TEXT,
            type TEXT,
            platform TEXT,
            port INTEGER,
            description TEXT,
            code TEXT,
            url TEXT
        )
    '''

    def __init__(self, db_path: str = '~/.hosforge/knowledge.db'):
        resolved = str(Path(db_path).expanduser())
        super().__init__(db_path=resolved)
        self._init_database()

    def _init_database(self) -> None:
        """初始化 SQLite 数据库表结构"""
        db_dir = Path(self._db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self._db = sqlite3.connect(self._db_path)
        self._db.row_factory = sqlite3.Row
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.execute('PRAGMA synchronous=NORMAL')

        for ddl in [self.CVE_TABLE, self.CWE_TABLE, self.CVE_CWE_TABLE, self.EXPLOIT_TABLE]:
            self._db.execute(ddl)
        self._db.commit()

        logger.info('Knowledge DB initialized: %s', self._db_path)

    async def get_cve(self, cve_id: str) -> CVERecord | None:
        if not self._db:
            return None
        row = self._db.execute(
            'SELECT * FROM cve WHERE cve_id = ?',
            (cve_id.upper(),),
        ).fetchone()
        if row is None:
            return None

        # 获取关联 CWE
        cwe_rows = self._db.execute(
            'SELECT cwe_id FROM cve_cwe WHERE cve_id = ?',
            (cve_id.upper(),),
        ).fetchall()
        cwe_ids = [r['cwe_id'] for r in cwe_rows]

        return CVERecord(
            cve_id=row['cve_id'],
            description=row['description'] or '',
            severity=row['severity'] or '',
            cvss_score=row['cvss_score'] or 0.0,
            cvss_vector=row['cvss_vector'] or '',
            cwe_ids=cwe_ids,
            exploit_available=bool(row['exploit_available']),
            kev=bool(row['kev']),
        )

    async def get_cwe(self, cwe_id: str) -> CWERecord | None:
        if not self._db:
            return None
        cwe_id = cwe_id.upper()
        if not cwe_id.startswith('CWE-'):
            cwe_id = f'CWE-{cwe_id}'

        row = self._db.execute(
            'SELECT * FROM cwe WHERE cwe_id = ?',
            (cwe_id,),
        ).fetchone()
        if row is None:
            return None

        mitigations = json.loads(row['mitigations']) if row['mitigations'] else []

        return CWERecord(
            cwe_id=row['cwe_id'],
            name=row['name'] or '',
            description=row['description'] or '',
            extended_description=row['extended_description'] or '',
            mitigations=mitigations,
        )

    async def search_cve(
        self,
        keyword: str = '',
        severity: str = '',
        limit: int = 20,
    ) -> list[CVERecord]:
        if not self._db:
            return []

        query = 'SELECT * FROM cve WHERE 1=1'
        params: list[Any] = []

        if keyword:
            query += ' AND (cve_id LIKE ? OR description LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        if severity:
            if severity.upper() == 'CRITICAL':
                query += ' AND cvss_score >= 9.0'
            elif severity.upper() == 'HIGH':
                query += ' AND cvss_score >= 7.0'
            elif severity.upper() == 'MEDIUM':
                query += ' AND cvss_score >= 4.0'

        query += ' ORDER BY cvss_score DESC LIMIT ?'
        params.append(limit)

        rows = self._db.execute(query, params).fetchall()
        results = []
        for row in rows:
            cwe_rows = self._db.execute(
                'SELECT cwe_id FROM cve_cwe WHERE cve_id = ?',
                (row['cve_id'],),
            ).fetchall()
            results.append(CVERecord(
                cve_id=row['cve_id'],
                description=row['description'] or '',
                severity=row['severity'] or '',
                cvss_score=row['cvss_score'] or 0.0,
                cwe_ids=[r['cwe_id'] for r in cwe_rows],
                exploit_available=bool(row['exploit_available']),
                kev=bool(row['kev']),
            ))
        return results

    async def import_cve_json(self, json_path: str) -> int:
        """
        从 NVD JSON 文件导入 CVE 数据。
        """
        if not self._db:
            return 0

        with open(json_path, 'r') as f:
            data = json.load(f)

        count = 0
        for item in data.get('vulnerabilities', []):
            cve_data = item.get('cve', {})
            cve_id = cve_data.get('id', '')
            if not cve_id:
                continue

            metrics = cve_data.get('metrics', {})
            cvss_v31 = metrics.get('cvssMetricV31', [])
            cvss_score = 0.0
            cvss_vector = ''
            severity = ''
            if cvss_v31:
                cvss_score = cvss_v31[0].get('cvssData', {}).get('baseScore', 0.0)
                cvss_vector = cvss_v31[0].get('cvssData', {}).get('vectorString', '')
                severity = cvss_v31[0].get('cvssData', {}).get('baseSeverity', '')

            description = ''
            for desc in cve_data.get('descriptions', []):
                if desc.get('lang') == 'en':
                    description = desc.get('value', '')
                    break

            cwe_ids = []
            for weakness in cve_data.get('weaknesses', []):
                for w_desc in weakness.get('description', []):
                    cwe_val = w_desc.get('value', '')
                    if cwe_val.startswith('CWE-'):
                        cwe_ids.append(cwe_val)

            try:
                self._db.execute('''
                    INSERT OR REPLACE INTO cve
                    (cve_id, description, severity, cvss_score, cvss_vector, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    cve_id, description, severity,
                    cvss_score, cvss_vector,
                    json.dumps(cve_data),
                ))

                for cwe_id in cwe_ids:
                    self._db.execute(
                        'INSERT OR IGNORE INTO cve_cwe (cve_id, cwe_id) VALUES (?, ?)',
                        (cve_id, cwe_id),
                    )

                count += 1
            except Exception as e:
                logger.error('Failed to import %s: %s', cve_id, e)

        self._db.commit()
        logger.info('Imported %d CVE records from %s', count, json_path)
        return count

    async def import_cwe_json(self, json_path: str) -> int:
        """从 CWE JSON 文件导入数据"""
        if not self._db:
            return 0

        with open(json_path, 'r') as f:
            data = json.load(f)

        count = 0
        for weakness in data.get('weaknesses', []):
            cwe_id = weakness.get('id', '')
            if not cwe_id:
                continue

            name = weakness.get('name', '')
            description = ''
            ext_desc = ''
            mitigations: list[str] = []

            for desc in weakness.get('description', []):
                if desc.get('lang') == 'en':
                    description = desc.get('value', '')
                    break

            for ext in weakness.get('extended_description', []):
                if ext.get('lang') == 'en':
                    ext_desc = ext.get('value', '')

            for mitigation in weakness.get('potential_mitigations', []):
                for desc in mitigation.get('description', []):
                    if desc.get('lang') == 'en':
                        mitigations.append(desc.get('value', ''))

            try:
                self._db.execute('''
                    INSERT OR REPLACE INTO cwe
                    (cwe_id, name, description, extended_description, mitigations, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    f'CWE-{cwe_id}', name, description, ext_desc,
                    json.dumps(mitigations),
                    json.dumps(weakness),
                ))
                count += 1
            except Exception as e:
                logger.error('Failed to import CWE %s: %s', cwe_id, e)

        self._db.commit()
        logger.info('Imported %d CWE records from %s', count, json_path)
        return count

    async def query(self, question: str, top_k: int = 5) -> list[KnowledgeEntry]:
        """
        关键词搜索知识库。
        """
        if not self._db:
            return []

        results: list[KnowledgeEntry] = []

        # 搜索 CVE
        cve_results = await self.search_cve(keyword=question, limit=top_k)
        for cve in cve_results:
            results.append(KnowledgeEntry(
                id=cve.cve_id,
                title=f'CVE: {cve.cve_id} (CVSS: {cve.cvss_score})',
                content=cve.description,
                source='cve',
                tags=['vulnerability', cve.severity.lower()],
                metadata={'cvss': cve.cvss_score, 'cwe_ids': cve.cwe_ids},
            ))

        # 搜索 CWE
        if not self._db:
            return results
        cwe_rows = self._db.execute(
            'SELECT * FROM cwe WHERE description LIKE ? LIMIT ?',
            (f'%{question}%', top_k),
        ).fetchall()
        for row in cwe_rows:
            results.append(KnowledgeEntry(
                id=row['cwe_id'],
                title=f'CWE: {row["cwe_id"]} - {row["name"]}',
                content=row['description'] or '',
                source='cwe',
                tags=['weakness'],
            ))

        return results[:top_k]

    async def get_exploit_poc(self, cve_id: str) -> str:
        if not self._db:
            return ''
        row = self._db.execute(
            'SELECT code, description FROM exploit WHERE cve_id = ? LIMIT 1',
            (cve_id.upper(),),
        ).fetchone()
        if row and row['code']:
            return f'# PoC for {cve_id}\n\n{row["code"]}'
        return ''

    async def check_kev(self, cve_id: str) -> bool:
        if not self._db:
            return False
        row = self._db.execute(
            'SELECT kev FROM cve WHERE cve_id = ?',
            (cve_id.upper(),),
        ).fetchone()
        return bool(row and row['kev'])

    def close(self) -> None:
        if self._db:
            self._db.close()
            self._db = None
