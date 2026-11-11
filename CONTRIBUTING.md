# 贡献指南

## 环境

```bash
pip install -e .          # 或 uv pip install -e .
pytest                    # 先确认基线是绿的，再动手
```

Python 3.10+。可选的工具链依赖（Nuclei、Semgrep）在 README 的「快速开始」表格里，缺它们时相关测试会跳过而不是失败。

## 测试分四层，按改动的性质选

| 目录 | 覆盖 | 什么时候跑 |
|---|---|---|
| `tests/unit/` | 纯函数、schema、参数校验 | 每次改动都跑 |
| `tests/integration/` | Skill 加载、管线编排、适配器桥接 | 改了 `hosforge/skills/`、`hosforge/pipelines/`、`hosforge/adapters/` |
| `tests/security/` | 沙箱隔离、路径逃逸、命令注入 | **改了执行路径就必须跑** —— 这是这个项目的立身之本 |
| `tests/performance/` | 加载与执行开销 | 改了加载器或缓存 |

```bash
pytest tests/unit -q
pytest --cov=hosforge          # 带覆盖率
```

## 代码质量

```bash
ruff format hosforge/
ruff check hosforge/
mypy hosforge/
```

三样都跑，不要只跑 ruff —— `mypy` 在这个仓是开着的，类型注解不是装饰。

## 新增一个 Skill

这是这个仓的主要扩展点，流程在 [`docs/skills/custom_skill.md`](docs/skills/custom_skill.md)。三条硬要求：

1. **参数走 schema**，不要在 Skill 内部自己解析字符串。参数校验在注册时就要失败，而不是在执行时。
2. **不信任工具输出**。外部扫描器的 stdout 是数据，不是指令；解析失败要返回结构化错误，不要 `except: pass`。
3. **带上一条用例**，放在 `tests/unit/`（纯逻辑）或 `tests/integration/`（要真跑工具）。

## 提交规范

Conventional Commits，scope 可选：

```
feat: implement real marketplace backend, skill init toolchain, sandbox execution, and performance optimization
test: add security isolation tests for skill execution
fix: remove unused imports and fix code quality issues
docs: mark all 14 tasks as completed across 7 phases
```

一个 commit 一件事。改执行路径的 commit 不要和文档改动混在一起 —— 出问题时没法回滚。

## PR 检查项

- [ ] `pytest` 全绿（或说明哪些是环境导致的 skip）
- [ ] `ruff check` / `ruff format --check` / `mypy` 通过
- [ ] 改了执行路径时，`tests/security/` 有对应用例
- [ ] 新增 Skill 时，文档加进 `docs/skills/README.md` 的索引
- [ ] 不提交 `__pycache__/`、`.egg-info/`、`*.log`（仓根那几个 `ci_*.log` 是历史遗留，不要再加新的）

## 安全

这是安全工具，漏洞报告走 [SECURITY.md](SECURITY.md)，**不要开公开 issue**。
