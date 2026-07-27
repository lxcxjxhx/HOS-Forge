# Checklist

## 上游同步

- [x] 已执行 `git fetch upstream` 检查上游更新
- [x] 已评估是否需要 rebase 同步（如有新提交）- 发现 5 个新提交，需要 rebase
- [ ] 同步后代码无冲突，或冲突已解决并验证构建通过

## 代码质量

- [ ] `make build` 成功通过，无编译错误
- [ ] 后端 lint 检查通过（`pre-commit run --config ./dev_config/python/.pre-commit-config.yaml`）
- [ ] 前端 lint 检查通过（`cd frontend && npm run lint`）
- [ ] 无冲突标记（`<<<<<<<`, `=======`, `>>>>>>>`）残留在代码中

## 框架问题处理

- [ ] 已识别 OpenHands 框架级问题（如有）
- [ ] 框架问题通过独立分支 + PR 提交（如有）
- [ ] PR 标题、描述、commit message 均为英文

## HOS-Forge 自身改进

- [ ] 已识别 HOS-Forge 自身改进点（如有）
- [ ] 自身改进直接提交到 `main`，commit message 遵循 Conventional Commits 格式（英文）

## 可运行性保障

- [ ] 服务可成功启动（`make run` 或对应命令）
- [ ] 启动日志无致命错误
- [ ] 可通过 `git revert` 或 `git checkout` 回滚到历史稳定版本

## 代码整洁度

- [ ] `git status` 无未跟踪的临时文件（或已加入 `.gitignore`）
- [ ] `git log --oneline -10` 显示清晰的 commit 历史
- [ ] commit message 格式规范，主题清晰
