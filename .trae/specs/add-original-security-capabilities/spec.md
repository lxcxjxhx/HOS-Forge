# HOS-Forge 原创安全能力增强 Spec

## Why
当前 HOS-Forge 过度依赖 OpenHands 的 AI 编码能力，缺乏独立的核心安全引擎。Taskflow、Personality、MCP Hub 等模块都是框架空壳，没有真正的安全分析算法。需要增加不依赖 OpenHands 的原创安全能力，提升项目 star 含金量和技术壁垒。

## What Changes
- **新增** Security Rule DSL（安全规则领域特定语言）- 自定义规则描述和执行引擎
- **新增** Lightweight AST Analyzer（轻量级 AST 分析引擎）- 基于 AST 的漏洞检测，不依赖外部工具
- **新增** CVE Knowledge Graph（CVE 知识图谱）- CVE/CWE/Exploit 关联分析和影响评估
- **新增** Vulnerability Exploitability Scorer（漏洞利用可行性评估器）- 自动评估漏洞利用条件

## Impact
- Affected specs: platform-upgrade-taskflow（补充核心能力）
- Affected code: 
  - 新增 `hosforge/rule_engine/` - 规则 DSL 解析和执行
  - 新增 `hosforge/ast_analyzer/` - AST 分析引擎
  - 新增 `hosforge/cve_graph/` - CVE 知识图谱
  - 新增 `hosforge/exploit_scorer/` - 利用可行性评估

## ADDED Requirements

### Requirement: Security Rule DSL
系统 SHALL 提供 YAML-based 的安全规则描述语言，支持：
- 规则定义：漏洞模式、检测条件、严重级别
- 规则组合：AND/OR/NOT 逻辑组合
- 规则继承：基础规则可以派生特定场景规则
- 规则参数化：支持变量和模板

#### Scenario: 定义 SQL 注入检测规则
- **WHEN** 用户创建 `rules/sql_injection.yaml`
- **THEN** 系统能够解析并执行该规则
- **AND** 规则可以检测 Python 代码中的 SQL 注入模式

```yaml
name: sql_injection_basic
type: vulnerability
severity: critical
patterns:
  - type: ast_match
    language: python
    pattern: "execute($USER_INPUT)"
    constraints:
      - $USER_INPUT not sanitized
  - type: regex
    pattern: "execute\\(.*\\+.*\\)"
conditions:
  - input_source: [request.params, request.form, request.args]
  - not_sanitized_by: [parameterize, escape, validate]
remediation:
  - use_parameterized_query
  - use_orm
```

### Requirement: Lightweight AST Analyzer
系统 SHALL 提供轻量级 AST 分析引擎，支持：
- Python/JavaScript AST 解析
- 基于模式匹配的漏洞检测
- 数据流追踪（taint analysis）
- 不依赖 Semgrep/CodeQL 等外部工具

#### Scenario: 检测 Python 代码中的命令注入
- **WHEN** 分析包含 `os.system(user_input)` 的代码
- **THEN** 系统识别出命令注入漏洞
- **AND** 报告漏洞位置、严重级别、修复建议

### Requirement: CVE Knowledge Graph
系统 SHALL 提供 CVE 知识图谱，支持：
- CVE/CWE/Exploit 关联存储
- 图数据库查询（NetworkX）
- 影响范围分析（哪些 CVE 影响我的项目）
- 修复优先级排序

#### Scenario: 查询 CVE-2024-1234 的影响
- **WHEN** 用户查询 `cve_graph.query("CVE-2024-1234")`
- **THEN** 返回关联的 CWE、Exploit、受影响版本
- **AND** 提供修复建议和优先级

### Requirement: Vulnerability Exploitability Scorer
系统 SHALL 提供漏洞利用可行性评估器，支持：
- 自动分析 CVE 的利用条件
- 评估环境匹配度（攻击向量、权限要求）
- 计算 CVSS 扩展评分
- 生成 PoC 框架建议

#### Scenario: 评估 CVE 利用可行性
- **WHEN** 输入 CVE 信息和目标环境
- **THEN** 输出利用可行性评分（0-100）
- **AND** 提供利用条件清单和 PoC 框架

## MODIFIED Requirements

### Requirement: Taskflow Engine 集成原创能力
Taskflow Engine SHALL 支持调用原创安全能力：
- 在 workflow 中引用 `rule_engine` 执行规则检测
- 在 workflow 中调用 `ast_analyzer` 进行代码分析
- 在 workflow 中查询 `cve_graph` 获取漏洞信息
- 在 workflow 中使用 `exploit_scorer` 评估漏洞

#### Scenario: 在安全审计工作流中使用原创能力
```yaml
tasks:
  - name: rule_based_scan
    engine: rule_engine
    rules: [sql_injection_basic, xss_basic]
  
  - name: ast_analysis
    engine: ast_analyzer
    languages: [python, javascript]
  
  - name: cve_impact_check
    engine: cve_graph
    query: affected_cves_for_project
  
  - name: exploitability_assessment
    engine: exploit_scorer
    input: verified_findings
```

## REMOVED Requirements
无删除，纯新增能力。
