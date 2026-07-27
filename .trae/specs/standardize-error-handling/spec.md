# 标准化错误处理和日志系统 Spec

## Why
HOS-Forge 仓库当前缺乏统一的错误处理和日志系统，各模块使用不同的异常类型和日志格式，导致问题定位困难、错误处理不一致、维护成本高。需要建立统一的异常体系和日志规范，提升代码质量和可维护性。

## What Changes
- 创建 `hosforge/exceptions.py`，定义统一的异常基类 `HOSForgeError` 及常见异常子类
- 创建 `hosforge/logging_config.py`，配置标准化日志格式和级别，提供 `get_logger(name)` 工厂函数
- 更新 `hosforge/security_tools/` 下所有工具模块使用统一异常和日志
- 更新 `hosforge/knowledge/` 下所有模块使用统一异常和日志
- 更新 `hosforge/mcp_server/` 下所有模块使用统一异常和日志
- 更新 `hosforge/security_agents/` 下所有模块使用统一异常和日志
- 确保所有异常都有清晰的错误信息和上下文
- 保持向后兼容，不破坏现有 API

## Impact
- Affected specs: maintain-hos-forge-phase3 (Task 7)
- Affected code: 
  - `hosforge/exceptions.py` (新增)
  - `hosforge/logging_config.py` (新增)
  - `hosforge/security_tools/base.py`
  - `hosforge/security_tools/nmap_tool.py`
  - `hosforge/security_tools/nuclei_tool.py`
  - `hosforge/security_tools/semgrep_tool.py`
  - `hosforge/security_tools/burp_tool.py`
  - `hosforge/knowledge/base.py`
  - `hosforge/knowledge/embeddings.py`
  - `hosforge/knowledge/indexer.py`
  - `hosforge/knowledge/search.py`
  - `hosforge/knowledge/vector_store.py`
  - `hosforge/mcp_server/server.py`
  - `hosforge/mcp_server/orchestrator.py`
  - `hosforge/mcp_server/tools/security_tools.py`
  - `hosforge/mcp_server/bridge/discovery.py`
  - `hosforge/mcp_server/bridge/adapter.py`
  - `hosforge/mcp_server/bridge/connectors/burp.py`
  - `hosforge/mcp_server/bridge/connectors/security_hub.py`
  - `hosforge/security_agents/base.py`
  - `hosforge/security_agents/attack.py`
  - `hosforge/security_agents/audit.py`
  - `hosforge/security_agents/defense.py`
  - `hosforge/security_agents/supervisor.py`

## ADDED Requirements

### Requirement: 统一异常体系
系统 SHALL 提供统一的异常基类和子类，所有模块使用一致的异常处理方式。

#### Scenario: 异常定义
- **WHEN** 定义异常类
- **THEN** 所有异常继承自 `HOSForgeError` 基类
- **AND** 异常包含清晰的错误消息、上下文信息和原始异常引用
- **AND** 常见异常类型包括：`ConfigurationError`, `ToolExecutionError`, `SecurityToolError`, `KnowledgeBaseError`, `MCPError` 等

#### Scenario: 异常使用
- **WHEN** 模块抛出异常
- **THEN** 使用统一的异常类型
- **AND** 提供足够的上下文信息用于问题定位
- **AND** 保留原始异常链（cause）

### Requirement: 标准化日志系统
系统 SHALL 提供统一的日志配置和格式，所有模块使用一致的日志记录方式。

#### Scenario: 日志配置
- **WHEN** 配置日志系统
- **THEN** 日志格式包含时间戳、模块名、日志级别、消息
- **AND** 提供 `get_logger(name)` 工厂函数
- **AND** 定义日志级别使用规范（DEBUG/INFO/WARNING/ERROR/CRITICAL）

#### Scenario: 日志使用
- **WHEN** 模块记录日志
- **THEN** 使用 `get_logger(__name__)` 获取 logger 实例
- **AND** 日志格式统一，包含必要的上下文信息
- **AND** 支持结构化日志（可选的额外字段）

### Requirement: 模块级错误处理
所有模块 SHALL 应用一致的错误处理模式。

#### Scenario: 安全工具模块
- **WHEN** 安全工具执行失败
- **THEN** 抛出 `ToolExecutionError` 或相关子类
- **AND** 记录错误日志，包含工具名称、执行参数、错误详情
- **AND** 返回统一的错误结果格式

#### Scenario: 知识库模块
- **WHEN** 知识库操作失败
- **THEN** 抛出 `KnowledgeBaseError` 或相关子类
- **AND** 记录错误日志，包含操作类型、目标数据、错误详情

#### Scenario: MCP 服务器模块
- **WHEN** MCP 服务调用失败
- **THEN** 抛出 `MCPError` 或相关子类
- **AND** 记录错误日志，包含服务名称、调用方法、错误详情

#### Scenario: 安全代理模块
- **WHEN** 安全代理执行失败
- **THEN** 抛出相应的异常类型
- **AND** 记录错误日志，包含代理类型、任务信息、错误详情

## MODIFIED Requirements
无

## REMOVED Requirements
无

## 技术约束
- 保持向后兼容，不破坏现有 API
- 代码通过 ruff 检查
- 添加必要的类型注解
- 日志格式：`%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- 时间格式：`%Y-%m-%d %H:%M:%S`
- 默认日志级别：INFO
- Commit message 使用英文，遵循 Conventional Commits 格式
- 创建分支 `refactor/standardize-error-handling`
- 不推送，不创建 PR
