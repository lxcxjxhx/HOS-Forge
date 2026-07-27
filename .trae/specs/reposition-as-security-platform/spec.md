# HOS-Forge 重新定位为 AI Native Security Platform

## Why
当前 HOS-Forge 的 README 和项目结构给人"AI IDE"的印象，容易被视为 OpenHands 的二开项目。这会导致：
1. 原创性被低估 — 核心安全能力（Runtime、Rule Engine、Knowledge Base）的价值被忽视
2. 技术壁垒不清晰 — 别人看不出 HOS 独有的技术资产
3. 扩展性受限 — 被绑定在单一 IDE 形态上

重新定位为 **AI Native Security Platform** 可以：
- 突出核心资产：Security Runtime、Security Engine、Rule Engine、Knowledge Base
- 明确多入口架构：IDE 只是入口之一，核心能力可服务任何 IDE/CLI/CI
- 建立技术壁垒：安全运行时、规则体系、检测引擎和知识库是 HOS 独有的

## What Changes

### 架构层面
- **BREAKING**: 项目定位从 "AI IDE" 改为 "AI Native Security Platform"
- 引入 "HOS Security Runtime" 作为核心概念
- HOS-Forge = Reference IDE，只是官方实现之一
- IDE 插件化：VSCode、Cursor、Claude Code、OpenHands 都作为 Runtime 的入口
- CLI、REST API、GitHub Action 作为其他入口

### 文档层面
- 重写 README.md，突出 Platform 定位和架构图
- 更新项目描述，强调 Security Runtime 而非 IDE
- 添加 "Architecture" 章节，展示多入口 + 核心引擎的架构
- 添加 "Use Cases" 章节，展示不同入口的使用场景
- 更新 Quick Start，展示通过 CLI/IDE/API 使用的示例

### 代码层面（后续 PR）
- 提取 Security Engine、Rule Engine、Knowledge Base 为独立模块
- 提供 REST API 和 SDK，支持跨 IDE 调用

## Impact
- Affected specs: 无（这是顶层定位变更）
- Affected code: README.md, pyproject.toml, 项目文档
- Affected perception: 从 "OpenHands 二开" 转变为 "AI 安全运行时平台"

## MODIFIED Requirements

### Requirement: 项目定位
**Before**: HOS-Forge 是一个 AI IDE，基于 OpenHands 扩展安全能力
**After**: HOS-Forge 是一个 AI Native Security Platform，提供安全运行时、规则引擎、知识库和检测能力，支持多种入口（IDE 插件、CLI、REST API、GitHub Action）

#### Scenario: 用户理解项目定位
- **WHEN** 用户访问 GitHub 仓库或阅读 README
- **THEN** 立即理解这是一个 Security Platform，而非 IDE
- **THEN** 看到清晰的架构图：Runtime 为核心，多个入口
- **THEN** 明白核心资产是 Security Engine、Rule Engine、Knowledge Base

#### Scenario: 评估原创性
- **WHEN** 评审者或用户评估项目原创性
- **THEN** 关注点从 "是不是 OpenHands 二开" 转变为 "安全运行时、规则体系、检测引擎和知识库是否独有"
- **THEN** 认识到即使底层 IDE 来源于 OpenHands，核心安全能力形成了独立价值

### Requirement: 架构展示
**Before**: 架构隐含为单一 IDE 应用
**After**: 架构明确展示为 "核心 Runtime + 多入口" 模式

#### Scenario: 架构图展示
- **WHEN** 用户查看 README 的 Architecture 章节
- **THEN** 看到以 HOS Security Runtime 为中心的架构图
- **THEN** 看到多个入口：VSCode Plugin, Cursor Plugin, Claude Code Plugin, OpenHands Plugin, CLI, REST API, GitHub Action
- **THEN** 看到核心组件：Security Engine, Rule Engine, Knowledge Base, Detection Capabilities

## ADDED Requirements

### Requirement: 多入口支持
系统 SHALL 支持多种入口访问 Security Runtime 的能力：
- IDE 插件（VSCode, Cursor, Claude Code, OpenHands）
- CLI 工具（`hos` 命令）
- REST API（供其他系统集成）
- GitHub Action（CI/CD 集成）

### Requirement: 核心资产独立化
Security Engine、Rule Engine、Knowledge Base SHALL 作为独立模块，可被任何入口调用。

## REMOVED Requirements
无（这是定位升级，不是功能删除）

## Migration Plan
1. **Phase 1 (当前 PR)**: 更新 README 和项目文档，明确 Platform 定位
2. **Phase 2 (后续 PR)**: 提取 Security Engine、Rule Engine、Knowledge Base 为独立模块
3. **Phase 3 (未来)**: 提供 REST API 和 SDK，支持跨 IDE 调用
4. **Phase 4 (长期)**: 开发更多 IDE 插件（Cursor、Claude Code 等）
