# HOS-Forge 安全工程平台升级任务列表

## 阶段一：核心引擎（S 优先级）

- [ ] Task 1: 实现 HOS Taskflow Engine 核心
  - [ ] SubTask 1.1: 设计 YAML 工作流 schema（workflows/*.yaml）
  - [ ] SubTask 1.2: 实现工作流解析器（YAML → 执行图）
  - [ ] SubTask 1.3: 实现 Agent 调度器（支持顺序、并行、条件分支）
  - [ ] SubTask 1.4: 实现 checkpoint/resume 机制
  - [ ] SubTask 1.5: 编写单元测试和示例工作流

- [ ] Task 2: 实现 Security Personality 系统
  - [ ] SubTask 2.1: 设计 Personality YAML schema
  - [ ] SubTask 2.2: 实现 Personality 加载器
  - [ ] SubTask 2.3: 创建预定义 Personality（cve_researcher、red_team、blue_team、code_reviewer）
  - [ ] SubTask 2.4: 实现 Personality 与 Agent 的绑定机制

## 阶段二：MCP 生态（S 优先级）

- [ ] Task 3: 构建 HOS MCP Hub 框架
  - [ ] SubTask 3.1: 设计 MCP Server 注册和发现机制
  - [ ] SubTask 3.2: 实现 MCP 客户端统一接口
  - [ ] SubTask 3.3: 实现动态加载和配置管理

- [ ] Task 4: 实现核心 MCP Server
  - [ ] SubTask 4.1: hos-ls-server（HOS-LS 扫描器集成）
  - [ ] SubTask 4.2: semgrep-server（Semgrep SAST 集成）
  - [ ] SubTask 4.3: nuclei-server（Nuclei 漏洞扫描集成）
  - [ ] SubTask 4.4: codeql-server（CodeQL 集成）
  - [ ] SubTask 4.5: github-server（GitHub API 集成）

## 阶段三：知识与验证（S 优先级）

- [ ] Task 5: 实现 Security Memory
  - [ ] SubTask 5.1: 设计知识库 schema（CVE、漏洞模式、修复历史、误报记录）
  - [ ] SubTask 5.2: 实现向量数据库集成（语义搜索）
  - [ ] SubTask 5.3: 实现误报率统计和模式匹配
  - [ ] SubTask 5.4: 实现历史任务学习机制

- [ ] Task 6: 实现 Agent Verification Loop
  - [ ] SubTask 6.1: 设计状态机（Finding → Candidate → Verified → Fixed → Closed）
  - [ ] SubTask 6.2: 实现验证 Agent（误报检查）
  - [ ] SubTask 6.3: 实现 Exploit Agent（漏洞复现）
  - [ ] SubTask 6.4: 实现 Patch Agent（修复代码生成）
  - [ ] SubTask 6.5: 实现 Review Agent（修复审查）
  - [ ] SubTask 6.6: 实现 PR 自动生成

## 阶段四：集成与测试（A 优先级）

- [ ] Task 7: 端到端工作流集成
  - [ ] SubTask 7.1: 创建完整的安全审计工作流示例
  - [ ] SubTask 7.2: 集成所有 MCP Server
  - [ ] SubTask 7.3: 测试多 Agent 协作场景
  - [ ] SubTask 7.4: 验证 checkpoint/resume 功能

- [ ] Task 8: CLI 工具开发
  - [ ] SubTask 8.1: 实现 `hos taskflow run <workflow.yaml>` 命令
  - [ ] SubTask 8.2: 实现 `hos taskflow list` 命令
  - [ ] SubTask 8.3: 实现 `hos personality list` 命令
  - [ ] SubTask 8.4: 实现 `hos mcp list` 命令
  - [ ] SubTask 8.5: 添加命令补全和帮助文档

## 阶段五：文档与发布（A 优先级）

- [ ] Task 9: 编写平台文档
  - [ ] SubTask 9.1: 编写 Taskflow Engine 使用指南
  - [ ] SubTask 9.2: 编写 Personality 定义指南
  - [ ] SubTask 9.3: 编写 MCP Server 开发指南
  - [ ] SubTask 9.4: 编写 Security Memory 使用指南
  - [ ] SubTask 9.5: 创建示例工作流库

- [ ] Task 10: 发布准备
  - [ ] SubTask 10.1: 更新 README.md（新定位、架构图、快速开始）
  - [ ] SubTask 10.2: 创建 CHANGELOG.md
  - [ ] SubTask 10.3: 准备 v2.0 发布说明
  - [ ] SubTask 10.4: 创建演示视频/文档

## 任务依赖关系

- Task 2 依赖 Task 1（Personality 需要 Taskflow 引擎支持）
- Task 4 依赖 Task 3（MCP Server 需要 Hub 框架）
- Task 6 依赖 Task 5（Verification Loop 需要 Security Memory）
- Task 7 依赖 Task 1-6（端到端集成需要所有组件）
- Task 8 可与 Task 7 并行（CLI 工具独立开发）
- Task 9 依赖 Task 7（文档需要基于完整功能）
- Task 10 依赖 Task 9（发布需要完整文档）
