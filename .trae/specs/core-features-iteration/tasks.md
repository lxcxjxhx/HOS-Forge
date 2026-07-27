# HOS-Forge 核心功能迭代任务列表

## PR 1: CLI 可执行入口修复

- [ ] Task 1: 修复 `hos` CLI 入口，确保安装后可立即执行
  - [ ] SubTask 1.1: 检查 `hosforge/cli/main.py` 的入口逻辑，确保 `hos --help` 输出完整命令列表
  - [ ] SubTask 1.2: 在 `hosforge/pyproject.toml` 中正确配置 `[project.scripts]` 或 `[tool.poetry.scripts]` 入口点（`hos = "hosforge.cli.main:app"`）
  - [ ] SubTask 1.3: 确保 `hos taskflow list` 能扫描 `hosforge/taskflow/workflows/` 并列出所有 YAML 工作流
  - [ ] SubTask 1.4: 确保 `hos personality list` 能扫描 `hosforge/personalities/definitions/` 并列出所有角色
  - [ ] SubTask 1.5: 确保 `hos mcp list` 能列出所有已注册的 MCP Server
  - [ ] SubTask 1.6: 编写验证测试 `tests/unit/test_cli_entry.py`，验证各子命令可正常调用
  - [ ] SubTask 1.7: 创建分支 `feat/cli-entry-fix`，提交 PR

## PR 2: 安全工具真实调用实现

- [ ] Task 2: 实现 NmapTool 真实命令行调用
  - [ ] SubTask 2.1: 在 `hosforge/security_tools/nmap_tool.py` 中实现 `subprocess` 调用 nmap 命令
  - [ ] SubTask 2.2: 实现 nmap XML/JSON 输出解析，返回结构化结果（开放端口、服务版本、OS 检测）
  - [ ] SubTask 2.3: 实现工具可用性检测（`shutil.which("nmap")`），未安装时返回明确错误和安装指南
  - [ ] SubTask 2.4: 编写单元测试 `tests/unit/test_nmap_tool.py`，mock subprocess 验证解析逻辑
  - [ ] SubTask 2.5: 创建分支 `feat/nmap-real-impl`，提交 PR

- [ ] Task 3: 实现 SemgrepTool 真实命令行调用
  - [ ] SubTask 3.1: 在 `hosforge/security_tools/semgrep_tool.py` 中实现 `subprocess` 调用 semgrep 命令
  - [ ] SubTask 3.2: 实现 semgrep JSON 输出解析，返回结构化结果（漏洞位置、严重性、CWE 分类）
  - [ ] SubTask 3.3: 实现工具可用性检测，未安装时返回明确错误
  - [ ] SubTask 3.4: 编写单元测试 `tests/unit/test_semgrep_tool.py`
  - [ ] SubTask 3.5: 创建分支 `feat/semgrep-real-impl`，提交 PR

- [ ] Task 4: 实现 NucleiTool 真实命令行调用
  - [ ] SubTask 4.1: 在 `hosforge/security_tools/nuclei_tool.py` 中实现 `subprocess` 调用 nuclei 命令
  - [ ] SubTask 4.2: 实现 nuclei JSONL 输出解析，返回结构化结果（模板匹配、严重性、CVE 关联）
  - [ ] SubTask 4.3: 实现工具可用性检测，未安装时返回明确错误
  - [ ] SubTask 4.4: 编写单元测试 `tests/unit/test_nuclei_tool.py`
  - [ ] SubTask 4.5: 创建分支 `feat/nuclei-real-impl`，提交 PR

## PR 3: Taskflow Engine 可执行化

- [ ] Task 5: 实现工作流解析器的完整执行逻辑
  - [ ] SubTask 5.1: 在 `hosforge/taskflow/parser.py` 中实现 YAML 解析和依赖图构建（拓扑排序）
  - [ ] SubTask 5.2: 在 `hosforge/taskflow/scheduler.py` 中实现任务调度（支持顺序、并行执行）
  - [ ] SubTask 5.3: 在 `hosforge/taskflow/executor.py` 中实现单任务执行（调用 Agent + Tool）
  - [ ] SubTask 5.4: 实现执行结果收集和状态跟踪
  - [ ] SubTask 5.5: 编写单元测试 `tests/unit/test_taskflow_engine.py`
  - [ ] SubTask 5.6: 创建分支 `feat/taskflow-executable`，提交 PR

- [ ] Task 6: 实现 CLI 与 Taskflow Engine 的端到端集成
  - [ ] SubTask 6.1: 实现 `hos taskflow run <workflow.yaml>` 完整执行流程
  - [ ] SubTask 6.2: 添加执行进度实时输出（显示当前任务、完成状态）
  - [ ] SubTask 6.3: 执行完成后自动生成 HTML 报告并输出路径
  - [ ] SubTask 6.4: 创建端到端测试 `tests/unit/test_e2e_workflow.py`，使用 mock 工具验证完整流程
  - [ ] SubTask 6.5: 创建分支 `feat/taskflow-cli-integration`，提交 PR

## PR 4: MCP Server 可启动可用

- [ ] Task 7: 实现 MCP Server 启动和调用
  - [ ] SubTask 7.1: 在 `hosforge/mcp/servers/base.py` 中实现标准 MCP Server 启动逻辑（基于 fastmcp）
  - [ ] SubTask 7.2: 实现 `semgrep_server.py` 的真实调用（调用 SemgrepTool 并返回 MCP 格式结果）
  - [ ] SubTask 7.3: 实现 `nuclei_server.py` 的真实调用
  - [ ] SubTask 7.4: 实现 `hos mcp start <server>` CLI 命令
  - [ ] SubTask 7.5: 编写单元测试 `tests/unit/test_mcp_servers.py`
  - [ ] SubTask 7.6: 创建分支 `feat/mcp-server-runnable`，提交 PR

## PR 5: 安装验证和快速演示

- [ ] Task 8: 端到端安装验证和演示工作流
  - [ ] SubTask 8.1: 创建 `scripts/demo_workflow.py` 演示脚本，展示完整安装→执行→报告流程
  - [ ] SubTask 8.2: 创建一个简化的 `demo-scan.yaml` 工作流，仅需基础工具即可运行
  - [ ] SubTask 8.3: 在 CI 中添加安装验证步骤（`pip install -e .` + `hos --help` + `hos taskflow list`）
  - [ ] SubTask 8.4: 创建分支 `feat/install-verification`，提交 PR

# Task Dependencies
- [Task 3, 4] 可与 [Task 2] 并行（工具实现互相独立）
- [Task 5] 可与 [Task 2, 3, 4] 并行（引擎实现不依赖具体工具）
- [Task 6] 依赖 [Task 1, 5]（CLI 集成需要入口修复和引擎实现）
- [Task 7] 依赖 [Task 3, 4]（MCP Server 需要工具实现）
- [Task 8] 依赖 [Task 1, 5, 6]（安装验证需要核心功能可用）
