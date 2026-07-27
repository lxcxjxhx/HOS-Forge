# 核心功能迭代验收清单

## PR 1: CLI 可执行入口修复

- [ ] `hos --help` 输出完整命令列表（taskflow, personality, mcp, scan, report）
- [ ] `hosforge/pyproject.toml` 正确配置入口点 `hos = "hosforge.cli.main:app"`
- [ ] `hos taskflow list` 能扫描并列出所有 YAML 工作流
- [ ] `hos personality list` 能扫描并列出所有角色定义
- [ ] `hos mcp list` 能列出所有已注册的 MCP Server
- [ ] 单元测试 `test_cli_entry.py` 验证各子命令可正常调用
- [ ] 分支 `feat/cli-entry-fix` 已提交 PR

## PR 2: 安全工具真实调用实现

### NmapTool
- [ ] `NmapTool.scan(target)` 实际执行 nmap 命令（subprocess）
- [ ] 解析 nmap XML/JSON 输出，返回结构化结果
- [ ] 工具可用性检测（`shutil.which("nmap")`）
- [ ] 未安装时返回明确错误提示和安装指南
- [ ] 单元测试 `test_nmap_tool.py` 使用 mock subprocess 验证解析逻辑
- [ ] 分支 `feat/nmap-real-impl` 已提交 PR

### SemgrepTool
- [ ] `SemgrepTool.analyze(path)` 实际执行 semgrep 命令
- [ ] 解析 semgrep JSON 输出，返回结构化结果（漏洞位置、严重性、CWE）
- [ ] 工具可用性检测
- [ ] 未安装时返回明确错误提示
- [ ] 单元测试 `test_semgrep_tool.py` 验证解析逻辑
- [ ] 分支 `feat/semgrep-real-impl` 已提交 PR

### NucleiTool
- [ ] `NucleiTool.scan(target)` 实际执行 nuclei 命令
- [ ] 解析 nuclei JSONl 输出，返回结构化结果（模板、严重性、CVE）
- [ ] 工具可用性检测
- [ ] 未安装时返回明确错误提示
- [ ] 单元测试 `test_nuclei_tool.py` 验证解析逻辑
- [ ] 分支 `feat/nuclei-real-impl` 已提交 PR

## PR 3: Taskflow Engine 可执行化

- [ ] YAML 解析和依赖图构建（拓扑排序）
- [ ] 任务调度支持顺序、并行执行
- [ ] 单任务执行调用 Agent + Tool
- [ ] 执行结果收集和状态跟踪
- [ ] 单元测试 `test_taskflow_engine.py` 验证解析和调度逻辑
- [ ] 分支 `feat/taskflow-executable` 已提交 PR
- [ ] `hos taskflow run <workflow.yaml>` 完整执行流程
- [ ] 执行进度实时输出（当前任务、完成状态）
- [ ] 执行完成后自动生成 HTML 报告
- [ ] 端到端测试 `test_e2e_workflow.py` 使用 mock 工具验证完整流程
- [ ] 分支 `feat/taskflow-cli-integration` 已提交 PR

## PR 4: MCP Server 可启动可用

- [ ] 标准 MCP Server 启动逻辑（基于 fastmcp）
- [ ] `semgrep_server.py` 真实调用 SemgrepTool 并返回 MCP 格式结果
- [ ] `nuclei_server.py` 真实调用 NucleiTool 并返回 MCP 格式结果
- [ ] `hos mcp start <server>` CLI 命令可启动服务
- [ ] 单元测试 `test_mcp_servers.py` 验证服务启动和调用
- [ ] 分支 `feat/mcp-server-runnable` 已提交 PR

## PR 5: 安装验证和快速演示

- [ ] 演示脚本 `scripts/demo_workflow.py` 展示完整流程
- [ ] 简化工作流 `demo-scan.yaml` 仅需基础工具即可运行
- [ ] CI 添加安装验证步骤（`pip install -e .` + `hos --help` + `hos taskflow list`）
- [ ] 分支 `feat/install-verification` 已提交 PR

## 端到端验证

- [ ] 新环境执行 `git clone` + `pip install -e .` 成功
- [ ] 执行 `hos --help` 看到完整命令列表
- [ ] 执行 `hos taskflow list` 看到可用工作流
- [ ] 执行 `hos taskflow run demo-scan.yaml` 完成完整流程
- [ ] 生成 HTML 报告并可查看
- [ ] 所有 PR 标题、描述、commit message 均为英文
- [ ] 所有 PR 通过 CI 测试和代码审查
