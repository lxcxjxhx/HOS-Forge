# Taskflow Engine 使用指南

## 概述

HOS Taskflow Engine 是一个 YAML 声明式安全工作流编排引擎，支持多 Agent 协作、任务依赖管理、条件分支和 checkpoint/resume 机制。

## 核心概念

### 1. Workflow（工作流）

工作流是一个 YAML 文件，定义了完整的安全任务执行流程。

```yaml
version: "1.0"
name: security-audit
description: Complete security audit workflow
tasks:
  - name: static_scan
    agent: [sast_agent]
    tools: [hos_ls, semgrep]
    depends_on: []
  
  - name: dynamic_scan
    agent: [dast_agent]
    tools: [nuclei]
    depends_on: [static_scan]
  
  - name: verify_findings
    agent: [redteam_agent]
    tools: [nuclei, exploit_db]
    depends_on: [static_scan, dynamic_scan]
```

### 2. Task（任务）

任务是工作流中的最小执行单元，包含以下属性：

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 任务唯一标识 |
| `agent` | list[string] | ✅ | 执行该任务的 Agent 列表 |
| `tools` | list[string] | ❌ | 任务可用的 MCP 工具列表 |
| `depends_on` | list[string] | ❌ | 依赖的前置任务列表 |
| `condition` | string | ❌ | 执行条件表达式 |
| `timeout` | int | ❌ | 超时时间（秒） |

### 3. Agent（智能体）

Agent 是任务的执行者，每个 Agent 具有特定的安全技能和工具访问权限。

预定义 Agent 类型：
- `sast_agent`: 静态代码分析
- `dast_agent`: 动态应用测试
- `redteam_agent`: 红队攻击验证
- `blueteam_agent`: 蓝队防御检测
- `developer_agent`: 代码修复
- `security_reviewer`: 安全审查

## 快速开始

### 1. 创建工作流文件

创建 `my-workflow.yaml`：

```yaml
version: "1.0"
name: vulnerability-assessment
description: Automated vulnerability assessment workflow

tasks:
  - name: code_analysis
    agent: [sast_agent]
    tools: [hos_ls, semgrep]
    depends_on: []
  
  - name: dependency_check
    agent: [sast_agent]
    tools: [npm_audit, safety]
    depends_on: []
  
  - name: exploit_verification
    agent: [redteam_agent]
    tools: [nuclei, metasploit]
    depends_on: [code_analysis, dependency_check]
  
  - name: generate_report
    agent: [security_reviewer]
    tools: [report_generator]
    depends_on: [exploit_verification]
```

### 2. 验证工作流

```bash
hos taskflow validate my-workflow.yaml
```

### 3. 运行工作流

```bash
# 基本运行
hos taskflow run my-workflow.yaml

# 从 checkpoint 恢复
hos taskflow run my-workflow.yaml --checkpoint latest

# 干运行（只显示执行计划）
hos taskflow run my-workflow.yaml --dry-run
```

### 4. 列出可用工作流

```bash
hos taskflow list
```

## 高级特性

### 1. 任务依赖

通过 `depends_on` 字段定义任务执行顺序：

```yaml
tasks:
  - name: task_a
    agent: [agent_1]
  
  - name: task_b
    agent: [agent_2]
    depends_on: [task_a]  # task_b 在 task_a 完成后执行
  
  - name: task_c
    agent: [agent_3]
    depends_on: [task_a, task_b]  # 等待多个前置任务
```

### 2. 并行执行

没有依赖关系的任务会自动并行执行：

```yaml
tasks:
  - name: scan_1
    agent: [sast_agent]
    # 无依赖，立即执行
  
  - name: scan_2
    agent: [dast_agent]
    # 无依赖，与 scan_1 并行执行
  
  - name: merge_results
    agent: [aggregator_agent]
    depends_on: [scan_1, scan_2]  # 等待两个扫描完成
```

### 3. 条件执行

使用 `condition` 字段控制任务是否执行：

```yaml
tasks:
  - name: critical_scan
    agent: [redteam_agent]
    condition: "severity == 'critical'"
  
  - name: full_audit
    agent: [security_reviewer]
    condition: "findings_count > 10"
```

### 4. Checkpoint/Resume

工作流支持中断后恢复：

```bash
# 运行工作流（自动保存 checkpoint）
hos taskflow run workflow.yaml

# 如果中断，从最新 checkpoint 恢复
hos taskflow run workflow.yaml --checkpoint latest

# 从指定 checkpoint 恢复
hos taskflow run workflow.yaml --checkpoint checkpoint-20260726-114500
```

Checkpoint 文件保存在 `.checkpoints/` 目录下。

### 5. 超时控制

为任务设置超时时间：

```yaml
tasks:
  - name: long_scan
    agent: [sast_agent]
    timeout: 3600  # 1 小时超时
```

## 工作流示例

### 示例 1: 完整安全审计

```yaml
version: "1.0"
name: full-security-audit
description: Comprehensive security audit with verification

tasks:
  - name: static_analysis
    agent: [sast_agent]
    tools: [hos_ls, semgrep, codeql]
    depends_on: []
  
  - name: dependency_audit
    agent: [sast_agent]
    tools: [npm_audit, safety, snyk]
    depends_on: []
  
  - name: dynamic_testing
    agent: [dast_agent]
    tools: [nuclei, owasp_zap]
    depends_on: [static_analysis]
  
  - name: exploit_verification
    agent: [redteam_agent]
    tools: [nuclei, metasploit, exploit_db]
    depends_on: [static_analysis, dependency_audit, dynamic_testing]
  
  - name: patch_generation
    agent: [developer_agent]
    tools: [code_fixer]
    depends_on: [exploit_verification]
  
  - name: security_review
    agent: [security_reviewer]
    tools: [review_assistant]
    depends_on: [patch_generation]
  
  - name: pr_creation
    agent: [developer_agent]
    tools: [github_api]
    depends_on: [security_review]
```

### 示例 2: CVE 研究工作流

```yaml
version: "1.0"
name: cve-research
description: CVE vulnerability research and analysis

tasks:
  - name: cve_lookup
    agent: [cve_researcher]
    tools: [cve_database, nvd_api]
    depends_on: []
  
  - name: affected_code_analysis
    agent: [sast_agent]
    tools: [hos_ls, codeql]
    depends_on: [cve_lookup]
  
  - name: exploit_development
    agent: [redteam_agent]
    tools: [exploit_framework, debugger]
    depends_on: [affected_code_analysis]
  
  - name: patch_analysis
    agent: [cve_researcher]
    tools: [diff_analyzer]
    depends_on: [exploit_development]
  
  - name: report_generation
    agent: [security_reviewer]
    tools: [report_generator]
    depends_on: [patch_analysis]
```

## API 使用

### Python API

```python
from hosforge.taskflow import WorkflowParser, TaskScheduler, CheckpointManager

# 解析工作流
workflow = WorkflowParser.parse_file("workflow.yaml")

# 创建调度器
scheduler = TaskScheduler(workflow)

# 注册任务处理器
async def handle_static_scan(task, context):
    # 执行静态扫描逻辑
    return {"findings": []}

scheduler.register_task_handler("static_scan", handle_static_scan)

# 执行工作流
results = await scheduler.execute_workflow()

# 保存 checkpoint
checkpoint_mgr = CheckpointManager(workflow)
checkpoint_mgr.save_checkpoint("latest")

# 恢复 checkpoint
checkpoint_mgr.load_checkpoint("latest")
```

## 最佳实践

### 1. 任务粒度

- ✅ 每个任务应该是一个独立的、可测试的单元
- ❌ 避免将过多逻辑放在单个任务中

### 2. 依赖设计

- ✅ 明确定义任务间的依赖关系
- ❌ 避免循环依赖

### 3. 错误处理

- 为关键任务设置合理的超时时间
- 使用 checkpoint 机制确保可恢复性
- 在任务处理器中实现适当的错误处理逻辑

### 4. 工具分配

- 只为任务分配必要的工具
- 遵循最小权限原则
- 在 Personality 中定义工具访问权限

### 5. 测试

- 使用 `--dry-run` 验证执行计划
- 为工作流编写单元测试
- 在 CI/CD 中集成工作流验证

## 故障排查

### 问题 1: 工作流验证失败

```bash
hos taskflow validate workflow.yaml
```

检查错误信息，常见问题：
- 任务名称重复
- 依赖的任务不存在
- YAML 语法错误

### 问题 2: 任务死锁

如果工作流卡在某个状态，可能是死锁：

```bash
# 查看执行计划
hos taskflow run workflow.yaml --dry-run
```

检查依赖关系是否存在循环。

### 问题 3: Checkpoint 恢复失败

确保 checkpoint 文件完整：

```bash
# 列出可用 checkpoint
ls .checkpoints/

# 删除损坏的 checkpoint
rm .checkpoints/corrupted.json
```

## 参考资源

- [工作流 Schema 定义](../hosforge/taskflow/schema.py)
- [解析器实现](../hosforge/taskflow/parser.py)
- [调度器实现](../hosforge/taskflow/scheduler.py)
- [Checkpoint 管理](../hosforge/taskflow/checkpoint.py)
- [示例工作流](../hosforge/taskflow/workflows/)
- [Personality 定义](personality-guide.md)
- [Verification Loop](verification-loop.md)
- [Security Memory](security-memory-guide.md)
- [快速入门](getting-started.md)
