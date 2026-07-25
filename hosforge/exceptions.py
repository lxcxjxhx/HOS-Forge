"""
HOS-Forge Unified Exception Hierarchy — 统一异常层次体系。

所有 HOS-Forge 模块应使用此异常体系，确保错误处理的一致性
和可追溯性。
"""

from __future__ import annotations

from typing import Any


class HOSForgeError(Exception):
    """
    HOS-Forge 所有异常的基类。

    提供统一的异常接口，包含上下文信息用于调试和日志记录。

    Attributes:
        message: 错误消息
        context: 错误上下文信息（可选）
        cause: 原始异常（可选）
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        base = self.message
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            base = f"{base} [{ctx_str}]"
        return base

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, context={self.context!r})"


# ── 配置相关异常 ──────────────────────────────────────────────


class ConfigurationError(HOSForgeError):
    """
    配置相关错误。

    用于配置文件加载失败、配置项缺失、配置值无效等场景。
    """

    pass


class EnvironmentVariableError(ConfigurationError):
    """
    环境变量相关错误。

    用于必需的环境变量未设置或值无效的场景。
    """

    pass


# ── 工具执行相关异常 ──────────────────────────────────────────


class ToolExecutionError(HOSForgeError):
    """
    工具执行失败。

    用于安全工具（Nmap、Nuclei、Semgrep 等）执行失败的场景。

    Attributes:
        tool_name: 工具名称
        exit_code: 退出码（如果有）
        stderr: 标准错误输出（如果有）
    """

    def __init__(
        self,
        message: str,
        tool_name: str = "",
        exit_code: int | None = None,
        stderr: str = "",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message, context, cause)
        self.tool_name = tool_name
        self.exit_code = exit_code
        self.stderr = stderr


class ToolNotFoundError(ToolExecutionError):
    """
    工具未找到。

    用于工具二进制文件不存在或不在 PATH 中的场景。
    """

    pass


class ToolTimeoutError(ToolExecutionError):
    """
    工具执行超时。

    用于工具执行超过预设时间限制的场景。
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        tool_name: str = "",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message,
            tool_name=tool_name,
            context=context,
            cause=cause,
        )
        self.timeout_seconds = timeout_seconds


# ── 安全工具特定异常 ──────────────────────────────────────────


class SecurityToolError(HOSForgeError):
    """
    安全工具通用异常。

    用于安全工具特有的错误场景（区别于通用工具执行错误）。
    """

    pass


class SecurityToolValidationError(SecurityToolError):
    """
    安全工具验证失败。

    用于工具可用性检查失败（如缺少依赖、权限不足等）。
    """

    pass


# ── 知识库相关异常 ────────────────────────────────────────────


class KnowledgeBaseError(HOSForgeError):
    """
    知识库操作错误。

    用于知识库初始化、查询、数据导入等失败的场景。
    """

    pass


class KnowledgeBaseConnectionError(KnowledgeBaseError):
    """
    知识库连接错误。

    用于数据库连接失败、向量存储不可用等场景。
    """

    pass


class KnowledgeQueryError(KnowledgeBaseError):
    """
    知识库查询错误。

    用于查询执行失败、结果解析错误等场景。
    """

    pass


class DataImportError(KnowledgeBaseError):
    """
    数据导入错误。

    用于 CVE/CWE/Exploit 数据导入失败的场景。
    """

    def __init__(
        self,
        message: str,
        source_file: str = "",
        record_id: str = "",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message, context, cause)
        self.source_file = source_file
        self.record_id = record_id


# ── MCP 相关异常 ──────────────────────────────────────────────


class MCPError(HOSForgeError):
    """
    MCP (Model Context Protocol) 相关错误。

    用于 MCP 服务器、连接器、工具注册等失败的场景。
    """

    pass


class MCPConnectionError(MCPError):
    """
    MCP 连接错误。

    用于 MCP 服务器连接失败、超时、断开等场景。
    """

    pass


class MCPToolNotFoundError(MCPError):
    """
    MCP 工具未找到。

    用于请求的 MCP 工具不存在或未注册的场景。
    """

    def __init__(
        self,
        tool_name: str,
        service_name: str = "",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        message = f"MCP tool not found: {tool_name}"
        if service_name:
            message += f" in service {service_name}"
        super().__init__(message, context, cause)
        self.tool_name = tool_name
        self.service_name = service_name


class MCPServiceError(MCPError):
    """
    MCP 服务错误。

    用于 MCP 服务发现失败、服务不可用等场景。
    """

    def __init__(
        self,
        service_name: str,
        message: str = "",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        if not message:
            message = f"MCP service error: {service_name}"
        super().__init__(message, context, cause)
        self.service_name = service_name


# ── 安全 Agent 相关异常 ───────────────────────────────────────


class SecurityAgentError(HOSForgeError):
    """
    安全 Agent 执行错误。

    用于安全 Agent（AttackAgent、AuditAgent 等）执行失败的场景。
    """

    pass


class AnalysisError(SecurityAgentError):
    """
    安全分析错误。

    用于安全分析过程失败的场景。
    """

    pass


class RemediationError(SecurityAgentError):
    """
    修复建议生成错误。

    用于自动修复或修复建议生成失败的场景。
    """

    pass


# ── 工作流相关异常 ────────────────────────────────────────────


class WorkflowError(HOSForgeError):
    """
    工作流执行错误。

    用于工作流编排、步骤执行失败的场景。
    """

    pass


class WorkflowStepError(WorkflowError):
    """
    工作流步骤错误。

    用于工作流单个步骤执行失败的场景。
    """

    def __init__(
        self,
        step_name: str,
        message: str = "",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        if not message:
            message = f"Workflow step failed: {step_name}"
        super().__init__(message, context, cause)
        self.step_name = step_name


class WorkflowDeadlockError(WorkflowError):
    """
    工作流死锁错误。

    用于工作流依赖关系无法满足的场景。
    """

    def __init__(
        self,
        blocked_steps: list[str],
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        message = f"Workflow deadlock: steps {blocked_steps} waiting on unmet dependencies"
        super().__init__(message, context, cause)
        self.blocked_steps = blocked_steps


# ── 报告生成相关异常 ──────────────────────────────────────────


class ReportGenerationError(HOSForgeError):
    """
    报告生成错误。

    用于渗透测试报告、审计报告等生成失败的场景。
    """

    pass


class TemplateError(ReportGenerationError):
    """
    模板错误。

    用于报告模板加载、渲染失败的场景。
    """

    pass
