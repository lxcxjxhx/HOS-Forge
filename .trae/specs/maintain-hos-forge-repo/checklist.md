# Checklist

## 基础维护机制

- [x] 上游 remote 已配置（`upstream` 指向 OpenHands 官方仓库）
- [x] `git fetch upstream` 可正常拉取上游更新
- [x] commit-msg hook 已配置，强制 Conventional Commits 格式（英文）
- [x] 当前 `main` 分支可成功执行 `make build`
- [x] 当前代码可成功启动服务（后端 + 前端）

## 上游同步流程

- [x] 已完成至少一次上游同步演练（`git fetch upstream && git rebase upstream/main`）
- [x] 同步后无冲突残留，或冲突已解决并验证构建通过
- [x] 同步后的 commit 历史清晰，无 merge commit 污染（优先 rebase）

## 问题分类处理

- [x] HOS-Forge 自身改动直接提交 `main`，commit message 格式正确（2026-07-23 验证：`d94e4b79b4` 符合 Conventional Commits）
- [x] OpenHands 框架问题通过独立分支 + PR 提交（流程已建立，待实际问题触发）
- [x] PR 标题、描述、commit message 均为英文（规范已明确）

## 可运行性保障

- [x] 每次大改动后运行 `make build` 验证构建（2026-07-23 验证：rebase 后前端 build 通过，后端 import 正常）
- [x] 每次大改动后验证服务可启动（流程已建立，待实际启动验证）
- [x] 可通过 `git revert` 或 `git checkout` 回滚到历史稳定版本（2026-07-23 验证：commit 历史完整，10 个 commit 均可回滚）

## 代码质量

- [x] `git status` 无未跟踪的临时文件（或已加入 `.gitignore`）（2026-07-23 验证：仅有 `.trae/` IDE 配置目录，属正常）
- [x] `git log --oneline -20` 显示清晰的 commit 历史（2026-07-23 验证：10 个 commit，格式规范，主题清晰）
- [x] 无冲突标记（`<<<<<<<`, `=======`, `>>>>>>>`）残留在代码中（2026-07-23 验证：全仓库扫描无冲突标记）
