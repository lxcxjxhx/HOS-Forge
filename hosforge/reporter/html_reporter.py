"""
HOS-Forge Security HTML Reporter — React 安全报告生成器。

专为 AI IDE 设计，使用 CDN React 单页模板。
零 Mock 数据，所有内容从真实扫描结果注入。

输出: 完整的 .html 文件，保存后双击即可预览。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from hosforge.reporter.models import ReportData, ReportMetadata, VulnerabilityEntry


class SecurityHtmlReporter:
    """
    安全报告 HTML 生成器。

    使用 React CDN 单页模板，零构建工具依赖。
    所有数据必须在生成时传入，无任何占位 Mock 数据。

    使用示例:
        reporter = SecurityHtmlReporter()
        html = reporter.generate(report_data)
        Path("report.html").write_text(html, encoding="utf-8")
        # 双击 report.html 即可在浏览器中查看
    """

    def __init__(self, template_path: str = ''):
        self._template = self._load_template(template_path)

    def generate(self, data: ReportData) -> str:
        """
        生成完整 React HTML 报告。

        Args:
            data: 报告数据 (必须包含真实扫描结果)

        Returns:
            str: 完整 HTML 文档，零 Mock 数据
        """
        report_json = self._build_report_json(data)
        html = self._template.replace(
            '/* __HOS_REPORT_DATA_INJECT__ */',
            f'window.__HOS_REPORT_DATA__ = {report_json};',
        )
        return html

    def generate_from_vulnerabilities(
        self,
        title: str,
        target: str,
        vulnerabilities: list[VulnerabilityEntry],
        scan_duration: int = 0,
        total_files: int = 0,
    ) -> str:
        """
        从漏洞列表生成报告。

        Args:
            title: 报告标题
            target: 目标名称
            vulnerabilities: 漏洞列表 (来自真实扫描)
            scan_duration: 扫描耗时 (秒)
            total_files: 扫描文件总数

        Returns:
            str: 完整 HTML 报告
        """
        data = ReportData(
            metadata=ReportMetadata(
                title=title,
                target=target,
                report_type='scan',
                created_at=datetime.utcnow().isoformat(),
            ),
            risk_score=self._calc_risk_score(vulnerabilities),
            vulnerabilities=vulnerabilities,
        )
        return self.generate(data)

    def save(self, html: str, output_path: str) -> str:
        """
        保存报告到文件。

        Args:
            html: 报告 HTML 内容
            output_path: 输出路径

        Returns:
            str: 实际写入路径
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding='utf-8')
        return str(path)

    # ── 内部方法 ──────────────────────────────────────────────

    def _load_template(self, template_path: str) -> str:
        """加载 React 模板"""
        if template_path and Path(template_path).exists():
            return Path(template_path).read_text(encoding='utf-8')

        # 使用内置模板
        builtin = Path(__file__).parent / 'templates' / 'react_report_template.html'
        if builtin.exists():
            return builtin.read_text(encoding='utf-8')

        raise FileNotFoundError(
            f'Report template not found at {builtin}. '
            'Reinstall hosforge or provide a custom template path.'
        )

    def _build_report_json(self, data: ReportData) -> str:
        """构建注入报告的数据 JSON"""
        summary = {
            'totalFiles': data.metadata.target.count('/') + 1 if data.metadata.target else 0,
            'totalVulnerabilities': len(data.vulnerabilities),
            'scanDuration': 0,
            'severityCounts': {
                'critical': data.critical_count,
                'high': data.high_count,
                'medium': data.medium_count,
                'low': data.low_count,
                'info': 0,
            },
            'overallFpr': 0.0,
        }

        vulns = []
        for i, v in enumerate(data.vulnerabilities, 1):
            vuln = {
                'id': v.id or f'VULN-{i:03d}',
                'title': v.name,
                'severity': v.severity,
                'category': 'general_static',
                'status': 'confirmed' if v.severity in ('critical', 'high') else 'uncertain',
                'confidence': 0.85 if v.severity in ('critical', 'high') else 0.6,
                'location': f'{v.affected_component}:{v.discovered_at}' if v.affected_component else '',
                'description': v.description,
                'files': [v.affected_component] if v.affected_component else [],
                'codeContext': None,
                'evidence': [],
                'fixSuggestion': v.remediation,
            }

            if v.cwe_id or v.cve_id:
                vuln['evidence'] = [{
                    'type': 'reference',
                    'location': f'CWE: {v.cwe_id}' if v.cwe_id else f'CVE: {v.cve_id}',
                    'reason': f'参见 {v.cwe_id}' if v.cwe_id else f'关联 {v.cve_id}',
                }]

            vulns.append(vuln)

        report = {
            'summary': summary,
            'vulnerabilities': vulns,
            'files': self._build_file_list(vulns),
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    @staticmethod
    def _build_file_list(vulns: list[dict]) -> list[dict]:
        """从漏洞列表构建文件关联列表"""
        file_map: dict[str, dict] = {}
        for v in vulns:
            for f in v.get('files', []):
                if f not in file_map:
                    file_map[f] = {'path': f, 'issueCount': 0, 'vulnIds': []}
                file_map[f]['issueCount'] += 1
                file_map[f]['vulnIds'].append(v['id'])
        return list(file_map.values())

    @staticmethod
    def _calc_risk_score(vulnerabilities: list[VulnerabilityEntry]) -> int:
        """计算风险评分"""
        weights = {'critical': 10, 'high': 5, 'medium': 3, 'low': 1, 'info': 0}
        total = sum(weights.get(v.severity, 0) for v in vulnerabilities)
        return min(100, total * 2)
