# 重构为 IDE 无关的 Skill+插件架构 Spec

## Why
当前 HOS-Forge 基于 OpenHands 二次开发，存在平台依赖性强、原创性不足的问题。需要重构为兼容任何 AI IDE 的独立 skill+插件模式，使其能够被 VSCode、Cursor、Claude Code 等任意 AI IDE 便捷调用，实现高度兼容的平台无关架构。

## What Changes
- **BREAKING**: 移除对 OpenHands 的直接依赖，将核心能力抽象为独立的 skill 层
- **BREAKING**: 重构插件架构为标准化的 skill 接口，支持多 IDE 适配
- 创建统一的 skill 注册和发现机制
- 实现 IDE 适配器层（VSCode、Cursor、Claude Code 等）
- 保留并增强现有安全工具集成能力（Nuclei、Semgrep、GitHub 等）
- 提供标准化的 MCP Server 接口供 IDE 调用
- 创建 skill 市场/注册表机制

## Impact
- Affected specs: CLI 集成、Taskflow Engine、MCP Server、安全工具集成
- Affected code: 
  - `hosforge/skills/` - 新增 skill 定义层
  - `hosforge/adapters/` - 新增 IDE 适配器
  - `hosforge/mcp_server/` - 增强 MCP Server 标准化
  - `hosforge/cli/` - 调整 CLI 命令结构
  - 移除 `openhands/` 目录依赖

## ADDED Requirements

### Requirement: Skill 抽象层
系统 SHALL 提供统一的 skill 抽象接口，使安全工具能力能够以标准化方式暴露。

#### Scenario: Skill 注册与发现
- **WHEN** 定义一个新的安全工具 skill
- **THEN** 系统自动注册到 skill 注册表，并可通过标准接口调用

#### Scenario: Skill 元数据管理
- **WHEN** skill 包含名称、描述、输入参数、输出格式
- **THEN** 系统能够生成 skill 文档和 IDE 可用的配置

### Requirement: IDE 适配器层
系统 SHALL 提供 IDE 适配器接口，使 skill 能够被不同 AI IDE 调用。

#### Scenario: VSCode 适配器
- **WHEN** 用户在 VSCode 中通过命令面板或快捷键触发
- **THEN** 适配器调用对应的 skill 并返回结果到 VSCode UI

#### Scenario: Cursor 适配器
- **WHEN** 用户在 Cursor 中通过 @mention 或命令调用
- **THEN** 适配器以 Cursor 兼容的格式返回 skill 执行结果

#### Scenario: Claude Code 适配器
- **WHEN** 用户在 Claude Code 中通过 /command 调用
- **THEN** 适配器以 Claude Code skill 格式暴露能力

### Requirement: 标准化 MCP Server
系统 SHALL 提供标准化的 MCP Server 实现，遵循 MCP 协议规范。

#### Scenario: MCP Server 启动
- **WHEN** IDE 或 CLI 启动 MCP Server
- **THEN** Server 暴露所有已注册的 skill 为 MCP tools

#### Scenario: MCP Tool 调用
- **WHEN** 客户端调用 MCP tool
- **THEN** Server 路由到对应的 skill 执行并返回标准化结果

### Requirement: Skill 市场/注册表
系统 SHALL 提供 skill 注册表机制，支持 skill 的分发和复用。

#### Scenario: Skill 列表查询
- **WHEN** 用户或 IDE 查询可用 skills
- **THEN** 返回所有已注册 skill 的列表及其元数据

#### Scenario: Skill 动态加载
- **WHEN** 从远程或本地加载 skill 定义
- **THEN** 系统动态注册并使其可用

## MODIFIED Requirements

### Requirement: CLI 命令结构
CLI SHALL 支持 skill 管理和调用命令，而非仅依赖 taskflow。

修改后的命令结构：
```bash
# Skill 管理
hos skill list                    # 列出所有可用 skills
hos skill info <skill-name>       # 查看 skill 详情
hos skill run <skill-name>        # 运行指定 skill

# 保持现有命令
hos taskflow run <workflow.yaml>  # 运行工作流
hos validate                      # 验证配置
```

### Requirement: 安全工具集成
安全工具 SHALL 以 skill 形式暴露，而非直接集成在工具类中。

修改后的集成方式：
- `NucleiTool` → `nuclei-scan` skill
- `SemgrepTool` → `semgrep-scan` skill
- `GitHubServer` → `github-integration` skill
- 每个 skill 包含完整的输入输出定义和执行逻辑

## REMOVED Requirements

### Requirement: OpenHands 直接依赖
**Reason**: 移除平台依赖，实现 IDE 无关架构
**Migration**: 
- 将 OpenHands 的 agent 能力抽象为独立 skill
- 将 OpenHands 的 sandbox 能力可选集成（作为 adapter 之一）
- 保留 OpenHands 作为可选的 backend 之一，而非核心依赖