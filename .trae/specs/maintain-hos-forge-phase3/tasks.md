# Tasks

## 阶段一：基础建设（低风险，快速见效）

- [x] Task 1: 创建 `hosforge/pyproject.toml` 声明依赖
  - [x] SubTask 1.1: 分析 `hosforge/` 代码中使用的第三方库（httpx, aiohttp, pydantic 等）
  - [x] SubTask 1.2: 创建 `hosforge/pyproject.toml`，声明运行时依赖和开发依赖
  - [x] SubTask 1.3: 配置构建系统（setuptools 或 poetry）
  - [x] SubTask 1.4: 创建分支 `chore/hosforge-code-quality`，提交 PR (#18)

- [x] Task 2: 配置 `hosforge/` 代码格式化和 lint
  - [x] SubTask 2.1: 在 `hosforge/pyproject.toml` 中配置 ruff、isort
  - [x] SubTask 2.2: 运行格式化工具统一代码风格
  - [x] SubTask 2.3: 创建分支 `chore/hosforge-code-quality`，提交 PR (#18)

- [x] Task 3: 为 `hosforge/` 添加类型注解
  - [x] SubTask 3.1: 为核心模块添加类型注解（security_agents/, security_tools/, knowledge/）
  - [x] SubTask 3.2: 配置 mypy 检查
  - [x] SubTask 3.3: 创建分支 `chore/hosforge-code-quality`，提交 PR (#18)

## 阶段二：核心功能完善（中风险，提升功能完整性）

- [x] Task 4: 实现 MCP Server 配置化
  - [x] SubTask 4.1: 将 `WORKFLOW_TEMPLATES` 中的硬编码服务名称提取到配置文件
  - [x] SubTask 4.2: 支持环境变量覆盖
  - [x] SubTask 4.3: 创建分支 `feat/mcp-server-config`，提交 PR (#19)

- [x] Task 5: 完善安全工具实际调用
  - [x] SubTask 5.1: 实现 NmapTool 的完整命令行调用逻辑
  - [x] SubTask 5.2: 实现 SemgrepTool 的完整命令行调用逻辑
  - [x] SubTask 5.3: 实现 NucleiTool 的完整命令行调用逻辑
  - [x] SubTask 5.4: 添加工具可用性检测和错误处理
  - [x] SubTask 5.5: 创建分支 `feat/security-tools-impl`，提交 PR (#28)

- [x] Task 6: 实现知识库向量搜索
  - [x] SubTask 6.1: 集成向量数据库（FAISS 或 ChromaDB）
  - [x] SubTask 6.2: 实现 embedding 生成
  - [x] SubTask 6.3: 添加语义搜索 API
  - [x] SubTask 6.4: 创建分支 `feat/security-tools-impl`，提交 PR (#28)

## 阶段三：质量保障（中风险，提升代码质量）

- [ ] Task 7: 标准化错误处理和日志
  - [ ] SubTask 7.1: 定义统一的错误处理基类
  - [ ] SubTask 7.2: 标准化日志格式和级别
  - [ ] SubTask 7.3: 在所有模块中应用一致的错误处理模式
  - [ ] SubTask 7.4: 创建分支 `refactor/standardize-error-handling`，提交 PR

- [ ] Task 8: 编写单元测试
  - [ ] SubTask 8.1: 创建 `hosforge/tests/` 目录结构
  - [ ] SubTask 8.2: 为安全代理编写单元测试（test_audit_agent.py, test_defense_agent.py, test_attack_agent.py）
  - [ ] SubTask 8.3: 为安全工具编写单元测试（test_security_tools.py）
  - [ ] SubTask 8.4: 为知识库和报告生成器编写测试
  - [ ] SubTask 8.5: 配置 pytest 和覆盖率报告
  - [ ] SubTask 8.6: 创建分支 `test/hosforge-unit-tests`，提交 PR

## 阶段四：文档和用户体验（低风险，提升可用性）

- [ ] Task 9: 编写 `hosforge/` 使用文档
  - [ ] SubTask 9.1: 创建 `hosforge/README.md`（项目介绍、安装步骤、快速开始）
  - [ ] SubTask 9.2: 为每个核心模块创建使用文档
  - [ ] SubTask 9.3: 添加代码示例和教程
  - [ ] SubTask 9.4: 创建分支 `docs/hosforge-usage`，提交 PR

- [ ] Task 10: 增强 CLI 工具
  - [ ] SubTask 10.1: 使用 click 或 typer 重构 CLI
  - [ ] SubTask 10.2: 添加常用命令（scan, report, config, tools）
  - [ ] SubTask 10.3: 添加命令补全和帮助文档
  - [ ] SubTask 10.4: 创建分支 `feat/cli-enhancement`，提交 PR

- [ ] Task 11: 添加报告自定义选项
  - [ ] SubTask 11.1: 支持多模板选择
  - [ ] SubTask 11.2: 添加主题配置（颜色、字体等）
  - [ ] SubTask 11.3: 实现 PDF 和 Markdown 导出
  - [ ] SubTask 11.4: 创建分支 `feat/report-customization`，提交 PR

## 阶段五：核心功能实现（高风险，需要大量测试）

- [ ] Task 12: 实现安全代理功能
  - [ ] SubTask 12.1: 为 AuditAgent 集成实际的安全分析引擎
  - [ ] SubTask 12.2: 为 DefenseAgent 集成 AI 模型生成修复代码
  - [ ] SubTask 12.3: 为 AttackAgent 集成 exploit 验证框架
  - [ ] SubTask 12.4: 添加配置开关控制是否启用实际 exploit 验证
  - [ ] SubTask 12.5: 创建分支 `feat/security-agents-impl`，提交 PR

## 持续维护任务

- [ ] Task 13: 检查上游 OpenHands 是否有新更新
  - [ ] SubTask 13.1: 执行 `git fetch upstream` 拉取最新上游代码
  - [ ] SubTask 13.2: 对比 `git log HEAD..upstream/main` 查看是否有新提交
  - [ ] SubTask 13.3: 如有新提交，执行 rebase 同步并验证构建

- [ ] Task 14: 验证当前代码可构建和运行
  - [ ] SubTask 14.1: 运行 `make build` 验证构建通过
  - [ ] SubTask 14.2: 启动服务验证可正常运行
  - [ ] SubTask 14.3: 检查启动日志无致命错误

# Task Dependencies
- [Task 2] depends on [Task 1]（先有 pyproject.toml，再配置 lint）
- [Task 3] depends on [Task 1]（先有 pyproject.toml，再配置 mypy）
- [Task 8] depends on [Task 1, 2]（先有依赖配置和 lint 配置，再编写测试）
- [Task 13, 14] 可与其他任务并行执行
