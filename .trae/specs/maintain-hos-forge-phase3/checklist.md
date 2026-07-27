# Checklist

## PR 流程规范

- [ ] 所有改动（包括 HOS-Forge 自身改进和框架问题修复）通过独立分支 + PR 提交
- [ ] 分支命名遵循规范（`feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`）
- [ ] PR 标题、描述、commit message 均为英文
- [ ] PR 合并前验证 `make build` 通过
- [ ] PR 合并前后端 lint 检查通过
- [ ] PR 合并前前端 lint 检查通过
- [ ] 无冲突标记（`<<<<<<<`, `=======`, `>>>>>>>`）残留

## 基础建设（阶段一）

- [ ] `hosforge/pyproject.toml` 已创建，声明所有运行时依赖和开发依赖
- [ ] `hosforge/` 代码格式化和 lint 配置完成（ruff、isort）
- [ ] `hosforge/` 核心模块已添加类型注解，mypy 检查通过

## 核心功能完善（阶段二）

- [ ] MCP Server 硬编码服务名称已提取到配置文件，支持环境变量覆盖
- [ ] 安全工具（Nmap、Semgrep、Nuclei、Burp）实际调用逻辑已实现
- [ ] 知识库向量搜索功能已实现（集成 FAISS/ChromaDB）

## 质量保障（阶段三）

- [ ] 错误处理和日志已标准化，统一的错误处理基类已定义
- [ ] `hosforge/tests/` 目录已创建，核心模块有单元测试覆盖
- [ ] pytest 和覆盖率报告已配置

## 文档和用户体验（阶段四）

- [ ] `hosforge/README.md` 已创建（项目介绍、安装步骤、快速开始）
- [ ] CLI 工具已增强（使用 click/typer，添加 scan/report/config/tools 命令）
- [ ] 报告生成器支持自定义选项（多模板、主题配置、PDF/Markdown 导出）

## 核心功能实现（阶段五）

- [ ] AuditAgent 已集成实际安全分析引擎
- [ ] DefenseAgent 已集成 AI 模型生成修复代码
- [ ] AttackAgent 已集成 exploit 验证框架
- [ ] 配置开关控制是否启用实际 exploit 验证

## 上游同步

- [ ] 已执行 `git fetch upstream` 检查上游更新
- [ ] 如有新提交，已执行 rebase 同步并验证构建通过

## 可运行性保障

- [ ] `make build` 成功通过，无编译错误
- [ ] 服务可成功启动，启动日志无致命错误
- [ ] 可通过 `git revert` 或 `git checkout` 回滚到历史稳定版本

## 代码整洁度

- [ ] `git status` 无未跟踪的临时文件（或已加入 `.gitignore`）
- [ ] `git log --oneline -10` 显示清晰的 commit 历史
- [ ] commit message 格式规范，主题清晰
