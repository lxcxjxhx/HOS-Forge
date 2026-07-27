# Tasks

## 已完成

- [x] Task 1: 创建统一异常体系 `hosforge/exceptions.py`
- [x] Task 2: 创建标准化日志配置 `hosforge/logging_config.py`
- [x] Task 3: 更新 `security_tools/base.py` 使用统一异常和日志
- [x] Task 4: 更新 `security_tools/nmap_tool.py` 使用统一异常和日志

## 待完成

- [ ] Task 5: 更新 `security_tools/` 剩余模块
  - [ ] SubTask 5.1: 更新 `nuclei_tool.py` — 替换 `logging.getLogger` 为 `get_logger`，使用 `ToolNotFoundError`/`ToolTimeoutError`/`ToolExecutionError`
  - [ ] SubTask 5.2: 更新 `semgrep_tool.py` — 同上模式
  - [ ] SubTask 5.3: 更新 `burp_tool.py` — 同上模式，使用 `SecurityToolError`

- [ ] Task 6: 更新 `knowledge/` 模块
  - [ ] SubTask 6.1: 更新 `base.py` — 替换 `logging.getLogger` 为 `get_logger`，使用 `KnowledgeBaseError`/`DataImportError`
  - [ ] SubTask 6.2: 更新 `embeddings.py` — 替换日志，使用 `KnowledgeBaseError`
  - [ ] SubTask 6.3: 更新 `indexer.py` — 替换日志，使用 `KnowledgeBaseError`
  - [ ] SubTask 6.4: 更新 `search.py` — 替换日志，使用 `KnowledgeQueryError`
  - [ ] SubTask 6.5: 更新 `vector_store.py` — 替换日志，使用 `KnowledgeBaseConnectionError`

- [ ] Task 7: 更新 `mcp_server/` 模块
  - [ ] SubTask 7.1: 更新 `server.py` — 替换日志，使用 `MCPError`
  - [ ] SubTask 7.2: 更新 `orchestrator.py` — 替换日志，使用 `WorkflowError`/`MCPError`
  - [ ] SubTask 7.3: 更新 `tools/security_tools.py` — 替换日志
  - [ ] SubTask 7.4: 更新 `bridge/adapter.py` — 替换日志，使用 `MCPConnectionError`
  - [ ] SubTask 7.5: 更新 `bridge/discovery.py` — 替换日志，使用 `MCPServiceError`
  - [ ] SubTask 7.6: 更新 `bridge/connectors/burp.py` — 替换日志，使用 `MCPConnectionError`
  - [ ] SubTask 7.7: 更新 `bridge/connectors/security_hub.py` — 替换日志，使用 `MCPConnectionError`

- [ ] Task 8: 更新 `security_agents/` 模块
  - [ ] SubTask 8.1: 更新 `base.py` — 替换日志，使用 `SecurityAgentError`
  - [ ] SubTask 8.2: 更新 `attack.py` — 替换日志，使用 `AnalysisError`
  - [ ] SubTask 8.3: 更新 `audit.py` — 替换日志，使用 `AnalysisError`
  - [ ] SubTask 8.4: 更新 `defense.py` — 替换日志，使用 `RemediationError`
  - [ ] SubTask 8.5: 更新 `supervisor.py` — 替换日志，使用 `SecurityAgentError`

- [ ] Task 9: 运行 ruff 检查并修复格式问题
- [ ] Task 10: 创建分支 `refactor/standardize-error-handling` 并提交代码

# Task Dependencies
- [Task 5-8] 可并行执行，互不依赖
- [Task 9] depends on [Task 5, 6, 7, 8]
- [Task 10] depends on [Task 9]
