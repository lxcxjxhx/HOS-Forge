# HOS-Forge 原创安全能力增强验收清单

## Security Rule DSL 验收

- [ ] 规则 YAML schema 定义完整，支持 patterns、conditions、remediation 字段
- [ ] 规则解析器能正确加载并验证 rules/ 目录下的 YAML 规则文件
- [ ] 规则引擎执行器能匹配 AST 模式和正则模式
- [ ] 规则组合逻辑（AND/OR/NOT）正确工作
- [ ] 至少 5 个预定义规则可用：SQL 注入、XSS、命令注入、路径遍历、硬编码密钥
- [ ] 单元测试覆盖规则解析、匹配、组合逻辑，通过率 100%

## Lightweight AST Analyzer 验收

- [ ] Python AST 解析器能解析 .py 文件并提取函数调用、赋值等节点
- [ ] JavaScript AST 解析器能解析 .js 文件并提取关键节点
- [ ] 模式匹配引擎能根据规则中的 pattern 匹配 AST 节点
- [ ] 数据流追踪（taint analysis）能追踪用户输入到危险函数的路径
- [ ] 漏洞检测报告包含：漏洞位置、严重级别、修复建议
- [ ] `hos ast scan <file>` 命令能正确输出检测结果
- [ ] 单元测试覆盖 Python/JS 解析、模式匹配、数据流追踪

## CVE Knowledge Graph 验收 ✅ 已完成

- [x] 图数据库 schema 定义 CVE、CWE、Exploit 节点类型及关联边
- [x] NetworkX 图存储支持节点和边的增删改查
- [x] CVE 数据导入功能可从 NVD JSON 格式导入
- [x] 图查询 API 支持：按 CVE ID 查询、关联查询、影响范围查询
- [x] 影响分析功能可根据项目依赖列表匹配受影响 CVE
- [x] `hos cve query ` 命令能返回关联信息
- [x] 单元测试覆盖图操作、查询、导入

## Vulnerability Exploitability Scorer 验收

- [ ] 评分模型基于 CVSS 向量，输出 0-100 评分
- [ ] 利用条件分析器能解析攻击向量、权限要求、复杂度
- [ ] 环境匹配评估能对比目标环境与利用条件
- [ ] PoC 框架生成器能输出基础利用代码模板
- [ ] `hos exploit score <cve_id>` 命令能输出评分和条件清单
- [ ] 单元测试覆盖评分计算、条件分析、环境匹配

## Taskflow 集成验收

- [ ] Taskflow 支持 `engine: rule_engine` 任务类型
- [ ] Taskflow 支持 `engine: ast_analyzer` 任务类型
- [ ] Taskflow 支持 `engine: cve_graph` 任务类型
- [ ] Taskflow 支持 `engine: exploit_scorer` 任务类型
- [ ] 集成测试工作流能串联所有 4 种引擎执行
- [ ] 工作流执行结果正确输出各引擎的分析报告

## CLI 工具验收

- [ ] `hos rule list` 列出所有可用规则
- [ ] `hos rule validate <rule.yaml>` 验证规则文件合法性
- [ ] `hos ast scan <file>` 对指定文件执行 AST 分析
- [ ] `hos cve query <cve_id>` 查询 CVE 信息
- [ ] `hos exploit score <cve_id>` 评估漏洞利用可行性
- [ ] 所有命令包含 --help 帮助信息

## 文档验收

- [ ] Security Rule DSL 使用指南包含规则定义示例和 API 参考
- [ ] AST Analyzer 使用指南包含支持语言、模式定义、使用方法
- [ ] CVE Knowledge Graph 使用指南包含数据导入、查询示例
- [ ] Exploitability Scorer 使用指南包含评分模型说明和使用示例
- [ ] rules/ 目录包含至少 10 个预定义规则文件
- [ ] README.md 突出展示 4 大原创安全能力
