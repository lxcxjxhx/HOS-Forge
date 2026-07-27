"""Verification Agents - 验证流水线中的各个专业 Agent。"""

from __future__ import annotations

import abc
import logging
from typing import Any, Dict, Optional

from hosforge.memory.store import SecurityMemoryStore

logger = logging.getLogger(__name__)


class BaseVerificationAgent(abc.ABC):
    """验证 Agent 抽象基类。"""

    def __init__(self, memory_store: Optional[SecurityMemoryStore] = None):
        """初始化 Agent。

        Args:
            memory_store: 可选的安全记忆存储，用于模式匹配和历史查询
        """
        self._memory_store = memory_store
        logger.info("Initialized %s", self.__class__.__name__)

    @abc.abstractmethod
    async def execute(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 的核心逻辑。

        Args:
            finding: 安全发现的详细信息

        Returns:
            Dict[str, Any]: Agent 的执行结果
        """
        ...


class VerificationAgent(BaseVerificationAgent):
    """验证 Agent - 检查误报，使用 Security Memory 模式匹配。"""

    async def execute(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """检查安全发现是否为误报。

        Args:
            finding: 安全发现信息，包含 cwe_id、file_path、code_snippet 等

        Returns:
            Dict 包含:
                - verified: bool - 是否为真实漏洞
                - confidence: float - 置信度 (0.0-1.0)
                - reason: str - 判断理由
        """
        cwe_id = finding.get("cwe_id", "")
        file_path = finding.get("file_path", "")
        code_snippet = finding.get("code_snippet", "")

        # 如果有记忆存储，查询历史误报率和相似模式
        if self._memory_store is not None:
            # 查询该 CWE 的历史误报率
            fp_rate = self._memory_store.get_false_positive_rate(cwe_id=cwe_id)

            # 查询相似的历史发现
            similar_findings = self._memory_store.search_findings(
                cwe_id=cwe_id,
                file_path=file_path,
            )

            # 如果有大量相似的历史发现且误报率高，则可能是误报
            if fp_rate > 0.7 and len(similar_findings) > 5:
                return {
                    "verified": False,
                    "confidence": 1.0 - fp_rate,
                    "reason": f"历史误报率过高 ({fp_rate:.1%})，且有 {len(similar_findings)} 个相似发现",
                }

            # 如果有确认的相似发现，则很可能是真实的
            confirmed_count = sum(
                1 for f in similar_findings if f.status == "confirmed"
            )
            if confirmed_count > 0:
                return {
                    "verified": True,
                    "confidence": min(0.9, 0.5 + confirmed_count * 0.1),
                    "reason": f"发现 {confirmed_count} 个已确认的相似历史发现",
                }

        # 默认情况下，基于代码片段长度和 CWE 类型给出初步判断
        has_code = len(code_snippet) > 20
        confidence = 0.6 if has_code else 0.4

        return {
            "verified": True,
            "confidence": confidence,
            "reason": "初步验证通过，建议进一步确认",
        }


class ExploitAgent(BaseVerificationAgent):
    """利用 Agent - 尝试复现漏洞。"""

    async def execute(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """尝试复现漏洞。

        Args:
            finding: 安全发现信息

        Returns:
            Dict 包含:
                - reproducible: bool - 是否可复现
                - exploit_code: str - 利用代码（如果可复现）
                - impact: str - 影响描述
        """
        cwe_id = finding.get("cwe_id", "")
        severity = finding.get("severity", "medium")
        code_snippet = finding.get("code_snippet", "")

        # 如果有记忆存储，查询已知的利用模式
        if self._memory_store is not None:
            patterns = self._memory_store.search_patterns(severity=severity)
            for pattern in patterns:
                if pattern.code_pattern in code_snippet:
                    return {
                        "reproducible": True,
                        "exploit_code": f"# 基于已知模式 {pattern.pattern_id} 生成利用代码\n# CWE: {cwe_id}\nprint('Exploit for {cwe_id}')",
                        "impact": f"已知漏洞模式，影响: {pattern.description}",
                    }

        # 根据 CWE 类型生成基础利用代码
        exploit_templates = {
            "CWE-89": "SQL 注入",
            "CWE-79": "XSS 跨站脚本",
            "CWE-78": "命令注入",
            "CWE-22": "路径遍历",
            "CWE-502": "反序列化",
        }

        vuln_type = exploit_templates.get(cwe_id, "未知类型")

        return {
            "reproducible": True,
            "exploit_code": f"# 漏洞类型: {vuln_type}\n# CWE: {cwe_id}\n# 严重程度: {severity}\nprint('Exploit placeholder for {cwe_id}')",
            "impact": f"{vuln_type}漏洞，可能导致未授权访问或数据泄露",
        }


class PatchAgent(BaseVerificationAgent):
    """补丁 Agent - 生成修复代码。"""

    async def execute(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """生成漏洞修复代码。

        Args:
            finding: 安全发现信息

        Returns:
            Dict 包含:
                - patch_code: str - 修复代码
                - description: str - 修复描述
                - files_changed: list - 修改的文件列表
        """
        cwe_id = finding.get("cwe_id", "")
        file_path = finding.get("file_path", "")
        code_snippet = finding.get("code_snippet", "")
        line_number = finding.get("line_number", 0)

        # 如果有记忆存储，查询历史补丁
        if self._memory_store is not None and finding.get("id"):
            history = self._memory_store.get_patches_for_finding(finding["id"])
            if history:
                # 使用成功率最高的历史补丁
                best_patch = max(history, key=lambda p: p.success_rate)
                return {
                    "patch_code": best_patch.patched_code,
                    "description": best_patch.patch_description,
                    "files_changed": [file_path],
                }

        # 根据 CWE 类型生成修复建议
        patch_templates = {
            "CWE-89": (
                "使用参数化查询替代字符串拼接",
                "# 修复 SQL 注入\n# 使用参数化查询\ncursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            ),
            "CWE-79": (
                "对输出进行 HTML 转义",
                "# 修复 XSS\nfrom html import escape\nsafe_output = escape(user_input)",
            ),
            "CWE-78": (
                "使用白名单验证命令参数",
                "# 修复命令注入\nimport shlex\nsafe_args = shlex.quote(user_input)",
            ),
            "CWE-22": (
                "验证文件路径不超出预期范围",
                "# 修复路径遍历\nimport os\nsafe_path = os.path.normpath(user_path)\nassert safe_path.startswith(allowed_base)",
            ),
        }

        description, patch_code = patch_templates.get(
            cwe_id,
            (
                "请根据具体漏洞类型进行修复",
                f"# TODO: 修复 {cwe_id}\n# 文件: {file_path}:{line_number}",
            ),
        )

        return {
            "patch_code": patch_code,
            "description": description,
            "files_changed": [file_path] if file_path else [],
        }


class ReviewAgent(BaseVerificationAgent):
    """审查 Agent - 审查补丁的正确性。"""

    async def execute(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """审查修复代码。

        Args:
            finding: 安全发现信息，应包含 patch_code 字段

        Returns:
            Dict 包含:
                - approved: bool - 是否批准
                - comments: list - 审查意见
                - score: int - 评分 (1-10)
        """
        patch_code = finding.get("patch_code", "")
        cwe_id = finding.get("cwe_id", "")

        comments = []
        score = 7  # 基础分

        # 检查补丁是否为空
        if not patch_code or patch_code.strip() == "":
            return {
                "approved": False,
                "comments": ["补丁代码为空"],
                "score": 1,
            }

        # 检查是否包含 TODO 占位符
        if "TODO" in patch_code:
            comments.append("补丁包含 TODO 占位符，需要完善")
            score -= 3

        # 检查是否针对 CWE 类型有相应的修复模式
        cwe_keywords = {
            "CWE-89": ["execute", "parameter", "query"],
            "CWE-79": ["escape", "sanitize", "html"],
            "CWE-78": ["quote", "shlex", "subprocess"],
            "CWE-22": ["normpath", "basename", "allowed"],
        }

        keywords = cwe_keywords.get(cwe_id, [])
        if keywords:
            has_keyword = any(kw in patch_code.lower() for kw in keywords)
            if has_keyword:
                comments.append(f"补丁包含 {cwe_id} 的典型修复模式")
                score += 2
            else:
                comments.append(f"补丁可能未针对 {cwe_id} 进行有效修复")
                score -= 2

        # 检查代码长度
        if len(patch_code) < 20:
            comments.append("补丁代码过短，可能不完整")
            score -= 2

        # 限制分数范围
        score = max(1, min(10, score))

        # 8 分及以上批准
        approved = score >= 8

        return {
            "approved": approved,
            "comments": comments,
            "score": score,
        }


class PRGeneratorAgent(BaseVerificationAgent):
    """PR 生成 Agent - 生成 Pull Request 描述和元数据。"""

    async def execute(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """生成 PR 元数据。

        Args:
            finding: 安全发现信息，应包含修复相关信息

        Returns:
            Dict 包含:
                - title: str - PR 标题
                - body: str - PR 描述
                - labels: list - 标签列表
                - branch_name: str - 分支名称
        """
        finding_id = finding.get("id", "unknown")
        cwe_id = finding.get("cwe_id", "unknown")
        severity = finding.get("severity", "medium")
        file_path = finding.get("file_path", "")
        description = finding.get("description", "")
        patch_description = finding.get("patch_description", "")

        # 生成标题
        title = f"Fix {cwe_id}: {description[:50]}..." if len(description) > 50 else f"Fix {cwe_id}: {description}"

        # 生成分支名称
        branch_name = f"fix/{finding_id}-{cwe_id.lower()}"

        # 生成标签
        labels = ["security", "bug"]
        severity_labels = {
            "critical": "severity:critical",
            "high": "severity:high",
            "medium": "severity:medium",
            "low": "severity:low",
        }
        if severity in severity_labels:
            labels.append(severity_labels[severity])

        # 生成 PR 描述
        body = f"""## 漏洞描述

{description}

## 修复内容

{patch_description or '已修复安全漏洞'}

## 漏洞信息

- **Finding ID**: {finding_id}
- **CWE**: {cwe_id}
- **严重程度**: {severity}
- **影响文件**: {file_path}

## 测试

- [ ] 单元测试通过
- [ ] 安全扫描通过
- [ ] 代码审查通过

## 参考

- [CWE-{cwe_id.split('-')[-1]}](https://cwe.mitre.org/data/definitions/{cwe_id.split('-')[-1]}.html)
"""

        return {
            "title": title,
            "body": body,
            "labels": labels,
            "branch_name": branch_name,
        }
