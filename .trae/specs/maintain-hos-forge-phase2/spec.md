# HOS-Forge 仓库持续维护规范 - 第二阶段

## Why
第一阶段维护规范已完成基础机制建立（上游同步、commit 规范、构建验证）。本阶段聚焦于：
1. 识别并提交 OpenHands 框架问题的 PR
2. 确保代码持续可运行、可重启、可回滚
3. 处理日常维护中的具体问题和改进

## What Changes
- 执行上游同步检查，确认是否有新的上游更新需要合并
- 识别框架级问题并走 PR 流程提交
- 验证当前代码可构建、可运行
- 处理日常 commit 提交（HOS-Forge 自身改进）
- 确保代码质量（无冲突标记、lint 通过、测试通过）

## Impact
- Affected specs: maintain-hos-forge-repo（第一阶段）
- Affected code: 全仓库，重点为 `hosforge/`、`openhands/`、`frontend/`、`enterprise/`

## ADDED Requirements

### Requirement: 框架问题识别与 PR 提交
The system SHALL 识别 OpenHands 框架级问题，并通过独立分支 + PR 流程提交修复。

#### Scenario: 发现框架问题
- **WHEN** 在代码审查或运行中发现 OpenHands 框架问题（如 `openhands/` 目录下的 bug）
- **THEN** 创建独立分支 `fix/xxx`，提交修复后开 PR 到上游或 `main`

#### Scenario: PR 内容规范
- **WHEN** 提交框架问题 PR
- **THEN** PR 标题、描述、commit message 均为英文，包含问题描述、复现步骤、修复方案

### Requirement: 持续可运行性验证
The system SHALL 定期验证代码可构建、可启动、可回滚。

#### Scenario: 构建验证
- **WHEN** 执行维护任务
- **THEN** 运行 `make build` 通过，无编译错误或依赖缺失

#### Scenario: 服务启动验证
- **WHEN** 构建通过后
- **THEN** 运行 `make run`（或对应启动命令）服务正常启动，无致命错误

### Requirement: 上游同步检查
The system SHALL 定期检查上游更新，并在必要时执行同步。

#### Scenario: 检查上游更新
- **WHEN** 执行维护任务
- **THEN** 运行 `git fetch upstream` 检查是否有新的上游提交

#### Scenario: 执行同步
- **WHEN** 发现上游有新提交
- **THEN** 执行 `git rebase upstream/main`，解决冲突（如有），验证构建通过

### Requirement: 日常 commit 提交
The system SHALL 对 HOS-Forge 自身改进直接提交到 `main`，遵循 Conventional Commits 规范。

#### Scenario: 功能开发
- **WHEN** 开发 HOS-Forge 自身功能（如 `hosforge/` 目录下的改进）
- **THEN** commit message 格式为 `feat(scope): description`，直接提交到 `main`

#### Scenario: Bug 修复
- **WHEN** 修复 HOS-Forge 自身 bug
- **THEN** commit message 格式为 `fix(scope): description`，直接提交到 `main`

## MODIFIED Requirements
无

## REMOVED Requirements
无
