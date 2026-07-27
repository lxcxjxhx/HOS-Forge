# HOS-Forge 核心功能迭代 Spec

## Why
HOS-Forge 已有 31 星但缺少真正可用的 install/usage 说明和核心功能实现。当前太多"装修"工作（文档美化、结构调整），缺少实质性的核心贡献。需要通过真实可用的功能迭代来提升项目价值，让每个 PR 都能带来实际能力增长。

## What Changes
- 实现真正可运行的安装流程，确保 `pip install -e .` 或 `poetry install` 后立即可用
- 完善 CLI 工具的实际功能，让 `hos` 命令能真正执行安全工作流
- 实现核心安全工具的真实调用（不是 mock）
- 提供可验证的使用示例和端到端演示
- 每个改动都是独立可合并的 PR，聚焦核心能力

## Impact
- Affected specs: maintain-hos-forge-phase3, platform-upgrade-taskflow
- Affected code: 
  - `hosforge/cli/` - CLI 工具实际功能
  - `hosforge/security_tools/` - 安全工具真实实现
  - `hosforge/taskflow/` - 工作流执行引擎
  - `hosforge/mcp/` - MCP Server 实际集成
  - `hosforge/tests/` - 功能验证测试

## ADDED Requirements

### Requirement: 可验证的安装流程
系统 SHALL 提供完整可验证的安装流程，用户按照文档操作后能够：
1. 成功安装所有依赖
2. 运行 `hos --help` 看到完整命令列表
3. 执行至少一个完整的工作流示例
4. 看到实际的输出结果（不是错误）

#### Scenario: 新用户安装验证
- **WHEN** 用户执行 `git clone` + `pip install -e .`
- **THEN** 可以立即运行 `hos taskflow list` 看到可用工作流
- **AND** 可以运行 `hos taskflow run <workflow>` 执行完整流程
- **AND** 输出显示真实的执行结果和报告

### Requirement: 真实的安全工具集成
安全工具（Nmap、Semgrep、Nuclei）SHALL 提供真实的命令行调用实现，而不是 mock 或占位符。

#### Scenario: Nmap 扫描执行
- **WHEN** 调用 `NmapTool.scan(target)`
- **THEN** 实际执行 nmap 命令并解析输出
- **AND** 返回结构化的漏洞信息
- **IF** nmap 未安装，THEN 返回明确的错误提示和安装指南

#### Scenario: Semgrep 代码分析
- **WHEN** 调用 `SemgrepTool.analyze(path)`
- **THEN** 实际执行 semgrep 扫描指定路径
- **AND** 返回发现的安全问题列表
- **AND** 包含 CWE 分类和修复建议

### Requirement: 可执行的工作流引擎
Taskflow Engine SHALL 能够真正解析和执行 YAML 工作流，支持：
1. 任务依赖解析
2. Agent 调度执行
3. 工具调用集成
4. 结果收集和报告生成

#### Scenario: 完整工作流执行
- **WHEN** 执行 `hos taskflow run security-audit.yaml`
- **THEN** 按依赖顺序执行所有任务
- **AND** 每个任务调用对应的 Agent 和 Tool
- **AND** 生成包含所有发现的 HTML 报告
- **AND** 报告可通过浏览器查看

### Requirement: MCP Server 实际可用
MCP Server SHALL 提供真实可用的安全工具服务，支持：
1. 通过 MCP 协议调用安全工具
2. 返回标准化的结果格式
3. 错误处理和状态报告

#### Scenario: MCP Server 启动和调用
- **WHEN** 启动 `hos mcp start semgrep-server`
- **THEN** 服务在指定端口监听
- **AND** 可以通过 MCP 客户端调用分析接口
- **AND** 返回符合 MCP 协议的分析结果

## MODIFIED Requirements

### Requirement: CLI 工具增强
CLI 工具 SHALL 提供完整的命令行体验，包括：
- `hos taskflow run/list/status` - 工作流管理
- `hos personality list/use` - 角色管理
- `hos mcp start/list/test` - MCP 服务管理
- `hos scan <target>` - 快速扫描命令
- `hos report <id>` - 报告查看和导出

#### Scenario: CLI 命令执行
- **WHEN** 用户运行 `hos scan example.com --type=nuclei`
- **THEN** 执行 nuclei 扫描
- **AND** 实时显示进度
- **AND** 完成后生成报告并输出路径

## REMOVED Requirements

无移除，仅增强现有功能的实际可用性。
