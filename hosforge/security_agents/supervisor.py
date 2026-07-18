"""
HOS-Forge Security Supervisor Agent — 安全Agent总控调度器。

负责任务理解、拆分、Agent调度和结果汇聚审核。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from hosforge.security_agents.base import (
    BaseSecurityAgent,
    SecurityAgentConfig,
    SecurityFinding,
    SecurityVulnerability,
    Severity,
)

logger = logging.getLogger(__name__)


@dataclass
class SupervisorPlan:
    """安全分析任务计划"""
    goal: str = ''
    sub_tasks: list[dict[str, Any]] = field(default_factory=list)
    agents_required: list[str] = field(default_factory=list)


@dataclass
class SupervisorReport:
    """安全分析综合报告"""
    summary: str = ''
    total_vulnerabilities: int = 0
    critical: list[SecurityVulnerability] = field(default_factory=list)
    high: list[SecurityVulnerability] = field(default_factory=list)
    medium: list[SecurityVulnerability] = field(default_factory=list)
    low: list[SecurityVulnerability] = field(default_factory=list)
    agent_reports: list[SecurityFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'summary': self.summary,
            'total_vulnerabilities': self.total_vulnerabilities,
            'critical_count': len(self.critical),
            'high_count': len(self.high),
            'medium_count': len(self.medium),
            'low_count': len(self.low),
            'recommendations': self.recommendations,
            'agent_reports': [r.to_dict() for r in self.agent_reports],
        }


class SecuritySupervisorAgent(BaseSecurityAgent):
    """
    Security Supervisor Agent — 总控级安全Agent。

    工作流程:
        1. 分析用户需求
        2. 拆分为子任务
        3. 调度子Agent执行
        4. 汇聚和审核结果
        5. 生成综合报告
    """

    def __init__(
        self,
        config: SecurityAgentConfig | None = None,
    ):
        super().__init__(config)
        self._agents: dict[str, BaseSecurityAgent] = {}

    @property
    def name(self) -> str:
        return 'SecuritySupervisor'

    def register_agent(self, agent: BaseSecurityAgent) -> None:
        """注册子Agent到调度器"""
        self._agents[agent.name] = agent
        logger.info('Registered sub-agent: %s', agent.name)

    async def create_plan(self, goal: str) -> SupervisorPlan:
        """
        根据用户目标创建安全分析计划。

        Args:
            goal: 用户目标描述

        Returns:
            SupervisorPlan: 分析计划
        """
        plan = SupervisorPlan(goal=goal)

        # 基础任务分解逻辑
        goal_lower = goal.lower()

        if any(kw in goal_lower for kw in ['审计', 'review', 'audit', 'scan']):
            plan.sub_tasks.append({
                'type': 'audit',
                'target': goal,
                'priority': 1,
                'description': '执行代码安全审计',
            })
            plan.agents_required.append('AuditAgent')

        if any(kw in goal_lower for kw in ['修复', 'fix', 'repair', '加固', 'harden']):
            plan.sub_tasks.append({
                'type': 'defense',
                'target': goal,
                'priority': 2,
                'description': '生成安全修复方案',
            })
            plan.agents_required.append('DefenseAgent')

        if any(kw in goal_lower for kw in ['渗透', 'attack', 'pentest', '测试']):
            plan.sub_tasks.append({
                'type': 'attack',
                'target': goal,
                'priority': 3,
                'description': '执行授权安全测试',
            })
            plan.agents_required.append('AttackAgent')

        # 默认添加审计
        if not plan.sub_tasks:
            plan.sub_tasks.append({
                'type': 'audit',
                'target': goal,
                'priority': 1,
                'description': '执行默认安全审计',
            })
            plan.agents_required.append('AuditAgent')

        return plan

    async def analyze(self, target: str, **kwargs: Any) -> SecurityFinding:
        """
        总控调度分析流程。

        自动创建计划并调度子Agent执行。
        """
        goal = kwargs.get('goal', target)
        plan = await self.create_plan(goal)

        logger.info(
            'Supervisor plan for "%s": %d sub-tasks, agents=%s',
            goal, len(plan.sub_tasks), plan.agents_required,
        )

        report = SupervisorReport(summary=f'分析目标: {goal}')
        all_vulns: list[SecurityVulnerability] = []

        for task in plan.sub_tasks:
            agent_type = task['type']
            agent = self._get_agent_for_type(agent_type)
            if agent is None:
                logger.warning('No agent available for task type: %s', agent_type)
                continue

            try:
                logger.info('Dispatching %s for task: %s', agent.name, task['description'])
                finding = await agent.analyze(task['target'])
                report.agent_reports.append(finding)
                all_vulns.extend(finding.vulnerabilities)
            except Exception as e:
                logger.error('Agent %s failed: %s', agent.name, e)
                report.agent_reports.append(SecurityFinding(
                    target=task['target'],
                    agent_name=agent.name,
                    success=False,
                    error_message=str(e),
                ))

        # 按严重程度分类
        for vuln in all_vulns:
            if vuln.severity == Severity.CRITICAL:
                report.critical.append(vuln)
            elif vuln.severity == Severity.HIGH:
                report.high.append(vuln)
            elif vuln.severity == Severity.MEDIUM:
                report.medium.append(vuln)
            else:
                report.low.append(vuln)

        report.total_vulnerabilities = len(all_vulns)
        report.recommendations = self._generate_recommendations(report)

        logger.info(
            'Supervisor report complete: %d vulns found (%d critical, %d high)',
            report.total_vulnerabilities,
            len(report.critical),
            len(report.high),
        )

        return SecurityFinding(
            target=target,
            agent_name=self.name,
            summary=report.summary,
            vulnerabilities=all_vulns,
        )

    async def fix(self, vulnerability: SecurityVulnerability) -> str:
        """委托给合适的Agent进行修复"""
        agent = self._get_agent_for_type('defense')
        if agent is None:
            raise RuntimeError('No DefenseAgent registered for fix')
        return await agent.fix(vulnerability)

    def _get_agent_for_type(self, agent_type: str) -> BaseSecurityAgent | None:
        """根据任务类型获取合适的Agent"""
        type_map = {
            'audit': 'AuditAgent',
            'defense': 'DefenseAgent',
            'attack': 'AttackAgent',
        }
        agent_name = type_map.get(agent_type)
        if agent_name and agent_name in self._agents:
            return self._agents[agent_name]
        return None

    def _generate_recommendations(self, report: SupervisorReport) -> list[str]:
        """基于分析结果生成建议"""
        recommendations: list[str] = []

        if report.critical:
            recommendations.append(
                f'立即修复 {len(report.critical)} 个严重漏洞'
            )
        if report.high:
            recommendations.append(
                f'尽快修复 {len(report.high)} 个高危漏洞'
            )
        if report.medium:
            recommendations.append(
                f'安排修复 {len(report.medium)} 个中危漏洞'
            )

        recommendations.append('建议对所有修复运行回归测试')
        recommendations.append('建议持续集成SAST扫描到CI/CD流水线')

        return recommendations
