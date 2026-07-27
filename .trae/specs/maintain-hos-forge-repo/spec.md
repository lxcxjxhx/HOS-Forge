# HOS-Forge 仓库持续维护规范

## Why
HOS-Forge 是基于 OpenHands 上游的安全扩展层仓库（`hosforge/` 目录），需要持续跟进上游更新、修复框架级问题、保持代码可运行可回滚，并以规范 commit 记录演进历史。当前仓库已有 10 个 commit，最新为 `ac135ac deploy: OpenHands 同等部署体系`，需建立长期维护机制而非一次性改动。

## What Changes
- 建立上游同步机制：定期从 OpenHands 上游拉取更新并 rebase 到 `main`
- 区分两类改动：
  - **正常 commit**：HOS-Forge 自身功能开发、bug 修复、文档完善 → 直接提交到 `main`
  - **框架问题 PR**：OpenHands 本身框架检查出的问题 → 走 PR 流程提交到上游或独立 PR 分支
- 保证代码可运行：每次改动后确保 `make build` 通过、服务可启动、可回滚到历史版本
- 易于维护：保持 commit 历史清晰、分支结构简洁、无冲突残留

## Impact
- Affected specs: 无现有 spec 匹配（首次维护类 spec）
- Affected code: 全仓库，重点为 `hosforge/`、`openhands/`、`frontend/`、`enterprise/`

## ADDED Requirements

### Requirement: 上游同步流程
The system SHALL 提供从 OpenHands 上游同步更新的标准流程，确保 HOS-Forge 扩展层与上游保持兼容。

#### Scenario: 定期同步上游更新
- **WHEN** 维护者执行 `git fetch upstream && git rebase upstream/main`
- **THEN** HOS-Forge 的 `main` 分支包含最新上游代码，且 `hosforge/` 扩展层无冲突

#### Scenario: 冲突解决
- **WHEN** rebase 过程中出现冲突
- **THEN** 维护者手动解决冲突后，运行 `make build` 验证构建通过，再完成 rebase

### Requirement: Commit 规范
The system SHALL 遵循 Conventional Commits 规范，commit message 使用英文，清晰描述改动类型和范围。

#### Scenario: 正常功能开发
- **WHEN** 开发 HOS-Forge 自身功能（如 `hosforge/security_agents/` 新增 agent）
- **THEN** commit message 格式为 `feat(security): add XXX agent`，直接提交到 `main`

#### Scenario: 框架问题修复
- **WHEN** 发现 OpenHands 框架级问题（如 `openhands/app_server/` 中的 bug）
- **THEN** 创建独立分支 `fix/xxx`，提交修复后开 PR 到上游或 `main`（视问题归属而定）

### Requirement: 可运行性保障
The system SHALL 确保每次改动后代码可构建、可启动、可回滚。

#### Scenario: 构建验证
- **WHEN** 完成代码改动
- **THEN** 运行 `make build` 通过，无编译错误或依赖缺失

#### Scenario: 服务启动验证
- **WHEN** 构建通过后
- **THEN** 运行 `make run`（或对应启动命令）服务正常启动，无致命错误

#### Scenario: 回滚能力
- **WHEN** 某次改动引入严重问题
- **THEN** 可通过 `git revert <commit>` 或 `git checkout <previous-tag>` 回滚到稳定版本

### Requirement: PR 提交流程
The system SHALL 对框架级问题采用 PR 流程提交，确保改动经过 review。

#### Scenario: 框架问题 PR
- **WHEN** 修复 OpenHands 框架问题
- **THEN** 创建 PR，标题和描述使用英文，包含问题描述、复现步骤、修复方案

#### Scenario: PR 合并前验证
- **WHEN** PR 提交后
- **THEN** CI 检查（lint、test、build）全部通过，reviewer approve 后方可合并

## MODIFIED Requirements
无（首次建立维护规范）

## REMOVED Requirements
无
