"""
HOS-Forge Security Dashboard API — 提供前端 Dashboard 所需的 REST 数据接口。

可作为 FastAPI 子路由挂载到 OpenHands 服务器。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query

from hosforge.dashboard.dashboard import (
    SecurityDashboard,
    VulnStatWidget,
    RiskScoreWidget,
    RecentFindingsWidget,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/hos/dashboard', tags=['HOS-Forge'])


@router.get('/overview')
async def dashboard_overview() -> dict[str, Any]:
    """Dashboard 概览数据"""
    dashboard = SecurityDashboard()
    return {
        'widgets': [
            {'type': 'risk-score', 'data': {'score': 0}},
            {'type': 'vuln-stats', 'data': {
                'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0,
            }},
        ],
        'status': 'ok',
    }


@router.get('/vulnerabilities')
async def vulnerability_list(
    severity: str = Query('', description='Filter by severity'),
    limit: int = Query(50, description='Max results'),
) -> list[dict[str, Any]]:
    """获取漏洞列表"""
    from hosforge.knowledge import LocalKnowledgeBase

    kb = LocalKnowledgeBase()
    cves = await kb.search_cve(severity=severity, limit=limit)
    return [c.to_dict() for c in cves]


@router.get('/mcp-services')
async def mcp_services() -> list[dict[str, Any]]:
    """获取 MCP 服务拓扑状态"""
    from hosforge.mcp_server.bridge.discovery import MCPDiscoveryEngine

    engine = MCPDiscoveryEngine()
    services = await engine.discover_all()
    return [s.to_dict() for s in services]


@router.get('/report')
async def generate_report(
    target: str = Query('', description='Report target'),
) -> str:
    """生成完整 HTML 报告"""
    from hosforge.reporter import SecurityHtmlReporter, ReportData, ReportMetadata

    reporter = SecurityHtmlReporter()
    data = ReportData(
        metadata=ReportMetadata(target=target),
    )
    return reporter.generate(data)
