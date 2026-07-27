# Tasks

## 基础维护机制建立

- [x] Task 1: 配置上游 remote 并验证同步流程
  - [x] SubTask 1.1: 添加 OpenHands 上游 remote（`git remote add upstream https://github.com/All-Hands-AI/OpenHands.git`）
  - [x] SubTask 1.2: 执行 `git fetch upstream` 验证上游可访问
  - [x] SubTask 1.3: 记录上游同步命令到项目 README 或维护文档（可选）

- [x] Task 2: 建立 commit 规范检查
  - [x] SubTask 2.1: 确认 `.pre-commit-config.yaml` 已配置 commit-msg hook（如 commitlint）
  - [x] SubTask 2.2: 若无 hook，添加 commit-msg 模板或使用 `commitlint` + `husky`
  - [x] SubTask 2.3: 测试 commit 时是否符合 Conventional Commits 格式

- [x] Task 3: 验证当前代码可构建和运行
  - [x] SubTask 3.1: 运行 `make build` 确认构建通过
  - [x] SubTask 3.2: 运行 `make run`（或 `make start-backend` + `npm run dev`）确认服务可启动
  - [x] SubTask 3.3: 记录启动过程中发现的问题（如有），作为后续修复任务

## 日常维护流程

- [x] Task 4: 执行一次上游同步演练
  - [x] SubTask 4.1: 执行 `git fetch upstream && git rebase upstream/main`
  - [x] SubTask 4.2: 若有冲突，解决后运行 `make build` 验证
  - [x] SubTask 4.3: 同步完成后推送 `git push origin main`（如有更新）

- [x] Task 5: 建立问题分类和处理流程
  - [x] SubTask 5.1: 明确 HOS-Forge 自身问题 → 直接 commit 到 `main`
  - [x] SubTask 5.2: 明确 OpenHands 框架问题 → 创建 `fix/xxx` 分支 → 开 PR
  - [x] SubTask 5.3: 记录流程到维护文档（可选）

## 持续改进

- [x] Task 6: 定期健康检查（每周/每次大改动前）
  - [x] SubTask 6.1: 运行 `make build` + 基础测试
  - [x] SubTask 6.2: 检查 `git status` 无残留未提交文件
  - [x] SubTask 6.3: 检查 `git log` 确认 commit 历史清晰

# Task Dependencies
- [Task 2] depends on [Task 1]（先配置上游 remote，再建立 commit 规范）
- [Task 4] depends on [Task 1, 3]（先验证当前可构建，再执行上游同步）
- [Task 5] depends on [Task 2]（先有 commit 规范，再明确问题分类流程）
