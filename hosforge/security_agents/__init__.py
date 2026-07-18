"""
HOS-Forge Security Agents — AI驱动的安全分析Agent体系。

提供以下安全Agent类型：
    - SecuritySupervisorAgent: 总控调度，负责任务拆分和结果审核
    - AuditAgent: 安全审计，SAST/代码审查/漏洞定位
    - AttackAgent: 渗透测试（授权环境）
    - DefenseAgent: 安全修复和加固
"""

from hosforge.security_agents.base import (
    BaseSecurityAgent,
    SecurityAgentConfig,
    SecurityVulnerability,
    Severity,
    SecurityFinding,
)
from hosforge.security_agents.supervisor import SecuritySupervisorAgent
from hosforge.security_agents.audit import AuditAgent
from hosforge.security_agents.defense import DefenseAgent
from hosforge.security_agents.attack import (
    AttackAgent,
    PentestReport,
    PentestTarget,
    PentestPhase,
    PhaseResult,
    ReconResult,
    ScanResult,
)

__all__ = [
    'BaseSecurityAgent',
    'SecurityAgentConfig',
    'SecurityVulnerability',
    'Severity',
    'SecurityFinding',
    'SecuritySupervisorAgent',
    'AuditAgent',
    'DefenseAgent',
    'AttackAgent',
    'PentestReport',
    'PentestTarget',
    'PentestPhase',
    'PhaseResult',
    'ReconResult',
    'ScanResult',
]
