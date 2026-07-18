"""
HOS-Forge Reporter CLI — 报告生成命令行工具。

用法:
    hos-report --input results.json --output report.html
    hos-report --help
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hosforge.reporter.html_reporter import SecurityHtmlReporter
from hosforge.reporter.models import ReportData, ReportMetadata, VulnerabilityEntry


def main() -> None:
    """CLI 入口"""
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print('用法: hos-report --input <data.json> --output <report.html>')
        print('')
        print('选项:')
        print('  --input   扫描结果 JSON 文件')
        print('  --output  输出 HTML 报告路径 (默认: report.html)')
        print('  --title   报告标题 (可选)')
        print('  --target  报告目标 (可选)')
        sys.exit(0)

    input_path = ''
    output_path = 'report.html'
    title = 'HOS-Forge Security Report'
    target = ''

    for i, arg in enumerate(args):
        if arg == '--input' and i + 1 < len(args):
            input_path = args[i + 1]
        elif arg == '--output' and i + 1 < len(args):
            output_path = args[i + 1]
        elif arg == '--title' and i + 1 < len(args):
            title = args[i + 1]
        elif arg == '--target' and i + 1 < len(args):
            target = args[i + 1]

    if not input_path:
        print('错误: 需要 --input 指定输入文件')
        sys.exit(1)

    with open(input_path, 'r') as f:
        data = json.load(f)

    vulnerabilities = []
    for item in data.get('vulnerabilities', []):
        vulnerabilities.append(VulnerabilityEntry(
            id=item.get('id', ''),
            name=item.get('name', item.get('title', '')),
            severity=item.get('severity', 'medium'),
            description=item.get('description', ''),
            cve_id=item.get('cve_id', ''),
            cwe_id=item.get('cwe_id', ''),
            remediation=item.get('fixSuggestion', item.get('remediation', '')),
        ))

    report_data = ReportData(
        metadata=ReportMetadata(title=title, target=target),
        vulnerabilities=vulnerabilities,
    )

    reporter = SecurityHtmlReporter()
    html = reporter.generate(report_data)

    output = Path(output_path)
    output.write_text(html, encoding='utf-8')
    print(f'报告已生成: {output.resolve()}')


if __name__ == '__main__':
    main()
