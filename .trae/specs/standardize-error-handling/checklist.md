# 标准化错误处理和日志系统 - 验证清单

## 基础设施验证
- [ ] `hosforge/exceptions.py` 文件存在且包含 `HOSForgeError` 基类
- [ ] 异常基类包含 `message`、`context`、`cause` 属性
- [ ] 定义了 `ConfigurationError` 异常类
- [ ] 定义了 `ToolExecutionError`、`ToolNotFoundError`、`ToolTimeoutError` 异常类
- [ ] 定义了 `SecurityToolError` 异常类
- [ ] 定义了 `KnowledgeBaseError`、`KnowledgeBaseConnectionError`、`KnowledgeQueryError`、`DataImportError` 异常类
- [ ] 定义了 `MCPError`、`MCPConnectionError`、`MCPServiceError`、`WorkflowError` 异常类
- [ ] 定义了 `SecurityAgentError`、`AnalysisError`、`RemediationError` 异常类
- [ ] `hosforge/logging_config.py` 文件存在且包含 `get_logger(name)` 函数
- [ ] 日志格式为 `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- [ ] 时间格式为 `%Y-%m-%d %H:%M:%S`
- [ ] 默认日志级别为 `INFO`
- [ ] 提供了 `StructuredLogger` 类支持额外上下文字段

## security_tools 模块验证
- [ ] `security_tools/base.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_tools/base.py` 导入并使用统一异常类
- [ ] `security_tools/nmap_tool.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_tools/nmap_tool.py` 在文件未找到时抛出 `ToolNotFoundError`
- [ ] `security_tools/nmap_tool.py` 在超时时抛出 `ToolTimeoutError`
- [ ] `security_tools/nmap_tool.py` 在执行失败时抛出 `ToolExecutionError`
- [ ] `security_tools/nuclei_tool.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_tools/nuclei_tool.py` 使用统一异常类
- [ ] `security_tools/semgrep_tool.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_tools/semgrep_tool.py` 使用统一异常类
- [ ] `security_tools/burp_tool.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_tools/burp_tool.py` 使用统一异常类

## knowledge 模块验证
- [ ] `knowledge/base.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `knowledge/base.py` 导入并使用 `KnowledgeBaseError` 相关异常
- [ ] `knowledge/embeddings.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `knowledge/embeddings.py` 使用统一异常类
- [ ] `knowledge/indexer.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `knowledge/indexer.py` 使用统一异常类
- [ ] `knowledge/search.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `knowledge/search.py` 使用 `KnowledgeQueryError` 异常
- [ ] `knowledge/vector_store.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `knowledge/vector_store.py` 使用 `KnowledgeBaseConnectionError` 异常

## mcp_server 模块验证
- [ ] `mcp_server/server.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/server.py` 使用 `MCPError` 相关异常
- [ ] `mcp_server/orchestrator.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/orchestrator.py` 使用 `WorkflowError`/`MCPError` 异常
- [ ] `mcp_server/tools/security_tools.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/bridge/adapter.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/bridge/adapter.py` 使用 `MCPConnectionError` 异常
- [ ] `mcp_server/bridge/discovery.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/bridge/discovery.py` 使用 `MCPServiceError` 异常
- [ ] `mcp_server/bridge/connectors/burp.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/bridge/connectors/burp.py` 使用统一异常类
- [ ] `mcp_server/bridge/connectors/security_hub.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `mcp_server/bridge/connectors/security_hub.py` 使用统一异常类

## security_agents 模块验证
- [ ] `security_agents/base.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_agents/base.py` 使用 `SecurityAgentError` 异常
- [ ] `security_agents/attack.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_agents/attack.py` 使用 `AnalysisError` 异常
- [ ] `security_agents/audit.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_agents/audit.py` 使用 `AnalysisError` 异常
- [ ] `security_agents/defense.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_agents/defense.py` 使用 `RemediationError` 异常
- [ ] `security_agents/supervisor.py` 使用 `get_logger(__name__)` 获取 logger
- [ ] `security_agents/supervisor.py` 使用 `SecurityAgentError` 异常

## 代码质量验证
- [ ] 所有修改的文件通过 `ruff check` 检查
- [ ] 所有修改的文件通过 `ruff format --check` 格式检查
- [ ] 所有异常类都有完整的类型注解
- [ ] 所有日志调用使用统一的 logger 实例
- [ ] 异常信息包含足够的上下文（工具名称、操作类型、错误详情等）
- [ ] 保留了原始异常链（使用 `cause` 参数）

## Git 验证
- [ ] 创建了分支 `refactor/standardize-error-handling`
- [ ] 所有修改已提交到该分支
- [ ] Commit message 使用英文
- [ ] Commit message 遵循 Conventional Commits 格式（如 `refactor: standardize error handling and logging`）
- [ ] 未推送到远程仓库
- [ ] 未创建 Pull Request

## 向后兼容性验证
- [ ] 现有 API 签名未改变
- [ ] 现有功能未被破坏
- [ ] 所有模块仍可正常导入和使用
