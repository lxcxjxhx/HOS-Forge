# HOS-Forge 持续维护 Phase 3 Spec

## Why
Phase 2 已完成基础维护机制建立、Windows 兼容性修复（PR #17 已合并）、代码质量检查。Phase 3 目标是持续跟进维护完善仓库，**所有改进通过 PR 提交**（避免直接覆盖仓库，便于检查冲突和代码审查），确保代码不冲突、能运行、能重启、能倒档、易于维护。

## What Changes
- **策略调整**：HOS-Forge 自身改进不再直接提交 `main`，而是通过独立分支 + PR 提交
- **改进实施**：基于 `hosforge-improvements.md` 识别的 12 项改进机会，分阶段实施
- **PR 流程标准化**：每个改进创建独立分支 `feat/xxx` 或 `fix/xxx`，开 PR 到 `main`
- **持续同步**：定期执行 `git fetch upstream && git rebase upstream/main` 保持与上游同步

## Impact
- Affected specs: `maintain-hos-forge-phase2`（已完成基础建设）
- Affected code: `hosforge/` 目录（核心功能代码）、`openhands/`（框架问题）、`frontend/`（前端问题）
- Affected workflow: 所有改动通过 PR 流程，便于代码审查和冲突检查

## MODIFIED Requirements

### Requirement: 问题分类和处理流程
**Phase 2 流程**：
- HOS-Forge 自身问题 → 直接 commit 到 `main`
- OpenHands 框架问题 → 创建 `fix/xxx` 分支 → 开 PR

**Phase 3 流程（修改后）**：
- **所有改进**（包括 HOS-Forge 自身改进和 OpenHands 框架问题）→ 创建独立分支 → 开 PR
- 分支命名规范：
  - `feat/xxx` - 新功能
  - `fix/xxx` - Bug 修复
  - `docs/xxx` - 文档改进
  - `refactor/xxx` - 代码重构
  - `test/xxx` - 测试相关
  - `chore/xxx` - 配置/工具相关
- PR 标题、描述、commit message 均为英文
- PR 合并前需验证构建通过、lint 通过、无冲突

### Requirement: 持续改进实施
**Phase 2 状态**：已识别 12 项改进机会（见 `hosforge-improvements.md`），Task 7 未完成

**Phase 3 计划**：
- 按优先级分阶段实施改进
- 每个改进通过独立 PR 提交
- 优先实施高优先级、低风险的改进
- 实施顺序：基础建设 → 核心功能 → 质量保障 → 文档完善

## ADDED Requirements

### Requirement: PR 驱动的开发流程
The system SHALL ensure all code changes go through PR workflow:
- 每个改进创建独立分支
- 分支命名遵循规范（`feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`）
- PR 标题、描述、commit message 均为英文
- PR 合并前需通过：
  - `make build` 构建验证
  - 后端 lint 检查（`pre-commit run --config ./dev_config/python/.pre-commit-config.yaml`）
  - 前端 lint 检查（`cd frontend && npm run lint`）
  - 无冲突标记残留

#### Scenario: 实施 HOS-Forge 自身改进
- **WHEN** 实施 `hosforge/` 目录的改进（如添加依赖管理、完善测试、改进文档等）
- **THEN** 创建独立分支（如 `feat/add-pyproject-toml`）
- **AND** 提交代码到该分支
- **AND** 开 PR 到 `main`
- **AND** PR 标题、描述、commit message 均为英文
- **AND** PR 合并前验证构建和 lint 通过

#### Scenario: 实施 OpenHands 框架问题修复
- **WHEN** 修复 `openhands/` 或 `frontend/` 目录的框架级问题
- **THEN** 创建独立分支（如 `fix/xxx`）
- **AND** 提交代码到该分支
- **AND** 开 PR 到 `main`
- **AND** PR 标题、描述、commit message 均为英文
- **AND** PR 合并前验证构建和 lint 通过

### Requirement: 持续上游同步
The system SHALL maintain synchronization with upstream OpenHands:
- 定期执行 `git fetch upstream` 检查上游更新
- 如有新提交，评估是否需要 rebase
- Rebase 后验证构建通过、服务可启动
- 同步后推送 `git push origin main`

#### Scenario: 上游有新提交
- **WHEN** 执行 `git fetch upstream` 发现新提交
- **THEN** 执行 `git rebase upstream/main`
- **AND** 解决冲突（如有）
- **AND** 运行 `make build` 验证构建
- **AND** 验证服务可启动
- **AND** 推送 `git push origin main`

### Requirement: 可运行性保障
The system SHALL ensure code is always runnable:
- 每次大改动后验证 `make build` 通过
- 每次大改动后验证服务可启动
- 启动日志无致命错误
- 可通过 `git revert` 或 `git checkout` 回滚到历史稳定版本

#### Scenario: 大改动后验证
- **WHEN** 完成一个 PR 的合并
- **THEN** 运行 `make build` 验证构建
- **AND** 启动服务验证可正常运行
- **AND** 检查启动日志无致命错误
- **AND** 确认 `git log` 历史清晰

## REMOVED Requirements
无删除的需求，仅修改流程策略。
