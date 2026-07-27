"""Security Memory Store - In-memory storage for security knowledge base."""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from .schema import VulnerabilityFinding, CVEKnowledge, VulnerabilityPattern, PatchHistory


class SecurityMemoryStore:
    """安全记忆存储 - 管理漏洞发现、CVE 知识、漏洞模式和补丁历史。

    当前使用内存存储，后续可扩展为数据库持久化。
    """

    def __init__(self) -> None:
        self._findings: Dict[str, VulnerabilityFinding] = {}
        self._cve_knowledge: Dict[str, CVEKnowledge] = {}
        self._patterns: Dict[str, VulnerabilityPattern] = {}
        self._patch_history: Dict[str, PatchHistory] = {}

    # ------------------------------------------------------------------
    # VulnerabilityFinding 操作
    # ------------------------------------------------------------------

    def add_finding(self, finding: Union[VulnerabilityFinding, Dict[str, Any]]) -> None:
        """添加漏洞发现记录
        
        Args:
            finding: VulnerabilityFinding 对象或字典
        """
        if isinstance(finding, dict):
            # 从字典创建 VulnerabilityFinding 对象
            finding = VulnerabilityFinding.from_dict(finding)
        
        finding.updated_at = datetime.now().isoformat()
        self._findings[finding.id] = finding

    def get_finding(self, finding_id: str) -> Optional[VulnerabilityFinding]:
        """根据 ID 获取漏洞发现"""
        return self._findings.get(finding_id)

    def search_findings(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        cwe_id: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> List[VulnerabilityFinding]:
        """搜索漏洞发现，支持按严重级别、状态、CWE ID 和文件路径过滤"""
        results = list(self._findings.values())

        if severity is not None:
            results = [f for f in results if f.severity == severity]
        if status is not None:
            results = [f for f in results if f.status == status]
        if cwe_id is not None:
            results = [f for f in results if f.cwe_id == cwe_id]
        if file_path is not None:
            results = [f for f in results if f.file_path == file_path]

        return results

    def delete_finding(self, finding_id: str) -> bool:
        """删除漏洞发现记录"""
        if finding_id in self._findings:
            del self._findings[finding_id]
            return True
        return False

    def get_false_positive_rate(self, cwe_id: Optional[str] = None, pattern_id: Optional[str] = None) -> float:
        """计算误报率。

        如果提供 cwe_id，则计算该 CWE 类型下所有 finding 的误报率。
        如果提供 pattern_id，则查找对应 pattern 的误报率。
        否则返回所有 finding 的整体误报率。
        """
        if pattern_id is not None:
            pattern = self._patterns.get(pattern_id)
            return pattern.false_positive_rate if pattern else 0.0

        findings = list(self._findings.values())
        if cwe_id is not None:
            findings = [f for f in findings if f.cwe_id == cwe_id]

        if not findings:
            return 0.0

        total = len(findings)
        fp_count = sum(1 for f in findings if f.status == "false_positive")
        return fp_count / total

    # ------------------------------------------------------------------
    # CVEKnowledge 操作
    # ------------------------------------------------------------------

    def add_cve_knowledge(self, cve: CVEKnowledge) -> None:
        """添加 CVE 知识条目"""
        self._cve_knowledge[cve.cve_id] = cve

    def get_cve_knowledge(self, cve_id: str) -> Optional[CVEKnowledge]:
        """根据 CVE ID 获取知识条目"""
        return self._cve_knowledge.get(cve_id)

    def search_cve_knowledge(
        self,
        min_cvss: Optional[float] = None,
        max_cvss: Optional[float] = None,
    ) -> List[CVEKnowledge]:
        """搜索 CVE 知识，支持按 CVSS 分数范围过滤"""
        results = list(self._cve_knowledge.values())

        if min_cvss is not None:
            results = [c for c in results if c.cvss_score >= min_cvss]
        if max_cvss is not None:
            results = [c for c in results if c.cvss_score <= max_cvss]

        return results

    def delete_cve_knowledge(self, cve_id: str) -> bool:
        """删除 CVE 知识条目"""
        if cve_id in self._cve_knowledge:
            del self._cve_knowledge[cve_id]
            return True
        return False

    # ------------------------------------------------------------------
    # VulnerabilityPattern 操作
    # ------------------------------------------------------------------

    def add_pattern(self, pattern: VulnerabilityPattern) -> None:
        """添加漏洞模式"""
        pattern.updated_at = datetime.now().isoformat()
        self._patterns[pattern.pattern_id] = pattern

    def get_pattern(self, pattern_id: str) -> Optional[VulnerabilityPattern]:
        """根据 ID 获取漏洞模式"""
        return self._patterns.get(pattern_id)

    def search_patterns(
        self,
        severity: Optional[str] = None,
        max_false_positive_rate: Optional[float] = None,
    ) -> List[VulnerabilityPattern]:
        """搜索漏洞模式，支持按严重级别和误报率过滤"""
        results = list(self._patterns.values())

        if severity is not None:
            results = [p for p in results if p.severity == severity]
        if max_false_positive_rate is not None:
            results = [p for p in results if p.false_positive_rate <= max_false_positive_rate]

        return results

    def increment_pattern_detection(self, pattern_id: str) -> None:
        """增加模式检测计数"""
        pattern = self._patterns.get(pattern_id)
        if pattern is not None:
            pattern.detection_count += 1
            pattern.updated_at = datetime.now().isoformat()

    def delete_pattern(self, pattern_id: str) -> bool:
        """删除漏洞模式"""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False

    # ------------------------------------------------------------------
    # PatchHistory 操作
    # ------------------------------------------------------------------

    def add_patch_history(self, patch: PatchHistory) -> None:
        """添加补丁历史记录"""
        self._patch_history[patch.patch_id] = patch

    def get_patch_history(self, patch_id: str) -> Optional[PatchHistory]:
        """根据 ID 获取补丁历史"""
        return self._patch_history.get(patch_id)

    def get_patches_for_finding(self, finding_id: str) -> List[PatchHistory]:
        """获取某个漏洞的所有补丁历史"""
        return [p for p in self._patch_history.values() if p.finding_id == finding_id]

    def get_patch_success_rate(self, finding_id: Optional[str] = None) -> float:
        """计算补丁成功率。

        如果提供 finding_id，则计算该漏洞相关补丁的成功率。
        否则返回所有补丁的整体成功率。
        """
        patches = list(self._patch_history.values())
        if finding_id is not None:
            patches = [p for p in patches if p.finding_id == finding_id]

        if not patches:
            return 0.0

        return sum(p.success_rate for p in patches) / len(patches)

    def delete_patch_history(self, patch_id: str) -> bool:
        """删除补丁历史记录"""
        if patch_id in self._patch_history:
            del self._patch_history[patch_id]
            return True
        return False

    # ------------------------------------------------------------------
    # 统计与导出
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_findings": len(self._findings),
            "findings_by_severity": self._count_by_field(self._findings, "severity"),
            "findings_by_status": self._count_by_field(self._findings, "status"),
            "total_cve_knowledge": len(self._cve_knowledge),
            "total_patterns": len(self._patterns),
            "total_patch_history": len(self._patch_history),
            "overall_false_positive_rate": self.get_false_positive_rate(),
            "overall_patch_success_rate": self.get_patch_success_rate(),
        }

    def clear(self) -> None:
        """清空所有存储数据"""
        self._findings.clear()
        self._cve_knowledge.clear()
        self._patterns.clear()
        self._patch_history.clear()

    @staticmethod
    def _count_by_field(items: Dict[str, Any], field_name: str) -> Dict[str, int]:
        """按字段值统计计数"""
        counts: Dict[str, int] = {}
        for item in items.values():
            value = getattr(item, field_name, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
