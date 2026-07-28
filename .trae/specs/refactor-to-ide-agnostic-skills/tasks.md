# Tasks

## Phase 1: 基础架构准备

- [ ] Task 1: 创建 Skill 抽象层基础接口
  - [ ] 1.1 创建 `hosforge/skills/__init__.py` 和 `base_skill.py`
  - [ ] 1.2 定义 `Skill` 基类，包含 `name`, `description`, `parameters`, `execute()` 接口
  - [ ] 1.3 创建 `SkillRegistry` 类用于 skill 注册和发现
  - [ ] 1.4 编写单元测试验证 skill 注册和调用流程

- [ ] Task 2: 重构现有安全工具为 Skill 形式
  - [ ] 2.1 将 `NucleiTool` 重构为 `NucleiScanSkill`
  - [ ] 2.2 将 `SemgrepTool` 重构为 `SemgrepScanSkill`
  - [ ] 2.3 将 `GitHubServer` 重构为 `GitHubIntegrationSkill`
  - [ ] 2.4 为每个 skill 添加完整的输入输出定义
  - [ ] 2.5 编写集成测试验证 skill 执行

## Phase 2: IDE 适配器层

- [ ] Task 3: 创建 IDE 适配器基础架构
  - [ ] 3.1 创建 `hosforge/adapters/__init__.py` 和 `base_adapter.py`
  - [ ] 3.2 定义 `IDEAdapter` 基类，包含 `format_input()`, `format_output()`, `register_commands()` 接口
  - [ ] 3.3 创建 `AdapterRegistry` 用于管理多个 IDE 适配器
  - [ ] 3.4 编写单元测试验证适配器注册和调用

- [ ] Task 4: 实现 VSCode 适配器
  - [ ] 4.1 创建 `hosforge/adapters/vscode_adapter.py`
  - [ ] 4.2 实现 VSCode 命令格式化和输出格式化
  - [ ] 4.3 创建 VSCode 扩展配置文件模板 (`package.json` 片段)
  - [ ] 4.4 编写测试验证 VSCode 适配器功能

- [ ] Task 5: 实现 Cursor 适配器
  - [ ] 5.1 创建 `hosforge/adapters/cursor_adapter.py`
  - [ ] 5.2 实现 Cursor @mention 和命令格式
  - [ ] 5.3 编写测试验证 Cursor 适配器功能

- [ ] Task 6: 实现 Claude Code 适配器
  - [ ] 6.1 创建 `hosforge/adapters/claude_code_adapter.py`
  - [ ] 6.2 实现 Claude Code /command 格式
  - [ ] 6.3 生成 Claude Code skill 定义文件
  - [ ] 6.4 编写测试验证 Claude Code 适配器功能

## Phase 3: MCP Server 标准化

- [ ] Task 7: 增强 MCP Server 标准化
  - [ ] 7.1 更新 `hosforge/mcp_server/server.py` 以支持动态 skill 注册
  - [ ] 7.2 实现 skill 到 MCP tool 的自动转换
  - [ ] 7.3 添加 MCP Server 健康检查和状态端点
  - [ ] 7.4 编写集成测试验证 MCP Server 与 skill 注册表交互

- [ ] Task 8: 实现 MCP Server 与 IDE 适配器的集成
  - [ ] 8.1 创建适配器启动 MCP Server 的接口
  - [ ] 8.2 实现 IDE 通过适配器调用 MCP tools 的流程
  - [ ] 8.3 编写端到端测试验证完整调用链

## Phase 4: CLI 命令重构

- [ ] Task 9: 重构 CLI 命令结构
  - [ ] 9.1 更新 `hosforge/cli/main.py` 添加 `skill` 子命令组
  - [ ] 9.2 实现 `hos skill list` 命令
  - [ ] 9.3 实现 `hos skill info <skill-name>` 命令
  - [ ] 9.4 实现 `hos skill run <skill-name>` 命令
  - [ ] 9.5 保留 `hos taskflow` 命令兼容性
  - [ ] 9.6 编写 CLI 命令测试

## Phase 5: Skill 注册表和文档

- [ ] Task 10: 创建 Skill 注册表机制
  - [ ] 10.1 实现 skill 元数据加载和索引
  - [ ] 10.2 支持从本地目录动态加载 skills
  - [ ] 10.3 创建 skill 文档自动生成工具
  - [ ] 10.4 编写注册表 API 测试

- [ ] Task 11: 更新项目文档
  - [ ] 11.1 更新 README.md 反映新的 skill+插件架构
  - [ ] 11.2 创建 `docs/skills/` 目录，为每个 skill 编写使用文档
  - [ ] 11.3 创建 `docs/adapters/` 目录，为每个 IDE 适配器编写配置指南
  - [ ] 11.4 更新安装和快速开始指南

## Phase 6: 移除 OpenHands 依赖

- [ ] Task 12: 清理 OpenHands 相关代码
  - [ ] 12.1 识别并列出所有对 OpenHands 的引用
  - [ ] 12.2 将必要的 OpenHands 功能迁移到独立模块
  - [ ] 12.3 移除 `openhands/` 目录和相关依赖
  - [ ] 12.4 更新 `pyproject.toml` 移除 OpenHands 依赖
  - [ ] 12.5 运行完整测试套件确保无回归

## Phase 7: 集成测试和验证

- [ ] Task 13: 端到端集成测试
  - [ ] 13.1 创建完整的 skill 注册、调用、结果返回测试流程
  - [ ] 13.2 测试各 IDE 适配器与 MCP Server 的交互
  - [ ] 13.3 测试 CLI 命令与 skill 系统的集成
  - [ ] 13.4 验证向后兼容性（taskflow 工作流）

- [ ] Task 14: 性能和安全验证
  - [ ] 14.1 测试 skill 注册表在大量 skill 下的性能
  - [ ] 14.2 验证 skill 执行的安全隔离
  - [ ] 14.3 测试 MCP Server 的并发处理能力

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 4, 5, 6] depends on [Task 3]
- [Task 7] depends on [Task 1, 2]
- [Task 8] depends on [Task 3, 7]
- [Task 9] depends on [Task 1, 2]
- [Task 10] depends on [Task 1]
- [Task 11] depends on [Task 1-10]
- [Task 12] depends on [Task 1-11]
- [Task 13] depends on [Task 1-12]
- [Task 14] depends on [Task 13]