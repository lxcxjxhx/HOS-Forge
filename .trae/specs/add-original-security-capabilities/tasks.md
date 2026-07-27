# HOS-Forge 原创安全能力增强任务列表

## 阶段一：Security Rule DSL（S 优先级）

- [x] Task 1: 实现 Security Rule DSL 核心
  - [x] SubTask 1.1: 设计规则 YAML schema（rules/*.yaml）
  - [x] SubTask 1.2: 实现规则解析器（YAML → Rule 对象）
  - [x] SubTask 1.3: 实现规则引擎执行器（规则匹配和评估）
  - [x] SubTask 1.4: 实现规则组合逻辑（AND/OR/NOT）
  - [x] SubTask 1.5: 创建 5 个预定义规则（SQL 注入、XSS、命令注入、路径遍历、硬编码密钥）
  - [x] SubTask 1.6: 编写单元测试

## 阶段二：Lightweight AST Analyzer（S 优先级）

- [ ] Task 2: 实现轻量级 AST 分析引擎
  - [ ] SubTask 2.1: 实现 Python AST 解析器（基于 ast 模块）
  - [ ] SubTask 2.2: 实现 JavaScript AST 解析器（基于 esprima 或 acorn）
  - [ ] SubTask 2.3: 实现模式匹配引擎（AST 节点匹配）
  - [ ] SubTask 2.4: 实现数据流追踪（taint analysis 基础版）
  - [ ] SubTask 2.5: 实现漏洞检测报告生成
  - [ ] SubTask 2.6: 编写单元测试和示例代码

## 阶段三：CVE Knowledge Graph（A 优先级）✅ 已完成

- [x] Task 3: 实现 CVE 知识图谱
  - [x] SubTask 3.1: 设计图数据库 schema（CVE/CWE/Exploit 节点和边）
  - [x] SubTask 3.2: 实现图数据库存储（基于标准库，无 NetworkX 依赖）
  - [x] SubTask 3.3: 实现 CVE 数据导入（从 NVD JSON 导入 + 10 个内置示例 CVE）
  - [x] SubTask 3.4: 实现图查询 API（查询关联、影响范围）
  - [x] SubTask 3.5: 实现影响分析（项目依赖 → 受影响 CVE）
  - [x] SubTask 3.6: 编写单元测试（28 个测试全部通过）

## 阶段四：Vulnerability Exploitability Scorer（A 优先级）

- [ ] Task 4: 实现漏洞利用可行性评估器
  - [ ] SubTask 4.1: 设计评分模型（基于 CVSS 扩展）
  - [ ] SubTask 4.2: 实现利用条件分析器（攻击向量、权限、复杂度）
  - [ ] SubTask 4.3: 实现环境匹配评估（目标环境 vs 利用条件）
  - [ ] SubTask 4.4: 实现 PoC 框架生成器
  - [ ] SubTask 4.5: 编写单元测试

## 阶段五：集成与测试（S 优先级）

- [ ] Task 5: 集成原创能力到 Taskflow
  - [ ] SubTask 5.1: 在 Taskflow 中添加 rule_engine 任务类型
  - [ ] SubTask 5.2: 在 Taskflow 中添加 ast_analyzer 任务类型
  - [ ] SubTask 5.3: 在 Taskflow 中添加 cve_graph 任务类型
  - [ ] SubTask 5.4: 在 Taskflow 中添加 exploit_scorer 任务类型
  - [ ] SubTask 5.5: 创建集成测试工作流（使用所有原创能力）

- [ ] Task 6: CLI 工具扩展
  - [ ] SubTask 6.1: 实现 `hos rule list` 命令
  - [ ] SubTask 6.2: 实现 `hos rule validate <rule.yaml>` 命令
  - [ ] SubTask 6.3: 实现 `hos ast scan <file>` 命令
  - [ ] SubTask 6.4: 实现 `hos cve query <cve_id>` 命令
  - [ ] SubTask 6.5: 实现 `hos exploit score <cve_id>` 命令

## 阶段六：文档与示例（A 优先级）

- [ ] Task 7: 编写原创能力文档
  - [ ] SubTask 7.1: 编写 Security Rule DSL 使用指南
  - [ ] SubTask 7.2: 编写 AST Analyzer 使用指南
  - [ ] SubTask 7.3: 编写 CVE Knowledge Graph 使用指南
  - [ ] SubTask 7.4: 编写 Exploitability Scorer 使用指南
  - [ ] SubTask 7.5: 创建规则库（rules/ 目录，至少 10 个规则）
  - [ ] SubTask 7.6: 更新 README.md（突出原创能力）

## 任务依赖关系

- Task 2 依赖 Task 1（AST Analyzer 需要 Rule DSL 支持）
- Task 5 依赖 Task 1-4（集成需要所有原创能力）
- Task 6 依赖 Task 5（CLI 需要集成后的功能）
- Task 7 依赖 Task 5-6（文档需要基于完整功能）

## 预期成果

完成后 HOS-Forge 将具备：
1. **独立的安全规则引擎** - 不依赖外部 SAST 工具
2. **自主的 AST 分析能力** - 轻量级代码分析
3. **CVE 知识图谱** - 漏洞关联和影响分析
4. **利用可行性评估** - 自动化漏洞优先级排序

这些能力将使 HOS-Forge 从"OpenHands 插件"升级为"独立安全平台"。
