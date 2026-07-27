# 快速入门指南

本指南将带你从零开始使用 HOS-Forge 完成一个完整的安全审计任务。

---

## 前置要求

- Python 3.10+
- Poetry 或 pip
- Git

---

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/lxcxjxhx/HOS-Forge.git
cd HOS-Forge
```

### 2. 安装依赖

```bash
# 使用 Poetry（推荐）
poetry install

# 或使用 pip
pip install -e .
```

### 3. 验证安装

```bash
# 检查 CLI 工具
hos --help

# 应该看到类似输出：
# Usage: hos [OPTIONS] COMMAND [ARGS]...
# HOS-Forge CLI - Security Agent Orchestration Framework
```

---

## 5 分钟快速体验

### 场景：对目标代码进行安全审计

我们将使用 HOS-Forge 的预定义工作流完成一次完整的安全审计。

#### 步骤 1: 查看可用工作流

```bash
hos taskflow list
```

输出示例：

```
可用工作流:
  security-audit.yaml - Complete security audit workflow
  cve-research.yaml - CVE vulnerability research workflow
  code-review.yaml - Code security review workflow
  ...
```

#### 步骤 2: 运行安全审计工作流

```bash
# 使用预定义的安全审计工作流
hos taskflow run hosforge/taskflow/workflows/security-audit.yaml
```

工作流将按以下顺序执行：

1. **static_scan** - 静态代码分析（使用 HOS-LS、Semgrep）
2. **codeql_analysis** - CodeQL 深度分析
3. **exploit_verify** - 漏洞利用验证（使用 Nuclei）
4. **patch_generation** - 生成修复补丁
5. **security_review** - 安全审查

#### 步骤 3: 查看结果

工作流完成后，结果保存在 `.hos-results/` 目录：

```bash
ls .hos-results/
# 输出：audit-20260726-143022/
```

---

## 15 分钟深入使用

### 场景：自定义安全工作流

让我们创建一个针对 Web 应用的自定义安全审计工作流。

#### 步骤 1: 创建工作流文件

创建 `my-web-audit.yaml`：

```yaml
hos:
  version: "1.0"

workflow:
  name: "Web Application Security Audit"
  description: "Custom security audit for web applications"
  
  tasks:
    # 阶段 1: 静态分析
    - name: dependency_check
      agent: [sast_agent]
      tools: [npm_audit, safety]
      depends_on: []
      timeout: 300
    
    - name: code_scan
      agent: [sast_agent]
      tools: [semgrep, hos_ls]
      depends_on: []
      timeout: 600
    
    # 阶段 2: 动态测试
    - name: api_testing
      agent: [dast_agent]
      tools: [nuclei, owasp_zap]
      depends_on: [code_scan]
      timeout: 900
    
    # 阶段 3: 漏洞验证
    - name: exploit_verification
      agent: [redteam_agent]
      tools: [nuclei, exploit_db]
      depends_on: [dependency_check, code_scan, api_testing]
      timeout: 600
    
    # 阶段 4: 修复生成
    - name: patch_generation
      agent: [developer_agent]
      tools: [code_fixer]
      depends_on: [exploit_verification]
      timeout: 300
    
    # 阶段 5: 审查
    - name: final_review
      agent: [security_reviewer]
      tools: [report_generator]
      depends_on: [patch_generation]
      timeout: 180
```

#### 步骤 2: 验证工作流

```bash
hos taskflow validate my-web-audit.yaml
```

如果验证通过，你会看到：

```
✓ 工作流验证成功
  名称: Web Application Security Audit
  任务数: 6
  依赖关系正确
```

#### 步骤 3: 干运行（预览执行计划）

```bash
hos taskflow run my-web-audit.yaml --dry-run
```

输出示例：

```
执行计划:
  并行组 1:
    - dependency_check (sast_agent)
    - code_scan (sast_agent)
  并行组 2:
    - api_testing (dast_agent) [依赖: code_scan]
  并行组 3:
    - exploit_verification (redteam_agent) [依赖: dependency_check, code_scan, api_testing]
  并行组 4:
    - patch_generation (developer_agent) [依赖: exploit_verification]
  并行组 5:
    - final_review (security_reviewer) [依赖: patch_generation]
```

#### 步骤 4: 执行工作流

```bash
hos taskflow run my-web-audit.yaml
```

实时输出：

```
[14:30:22] 开始执行工作流: Web Application Security Audit
[14:30:22] [dependency_check] 启动 sast_agent...
[14:30:22] [code_scan] 启动 sast_agent...
[14:32:15] [dependency_check] ✓ 完成 (发现 3 个问题)
[14:35:40] [code_scan] ✓ 完成 (发现 7 个问题)
[14:35:41] [api_testing] 启动 dast_agent...
[14:42:18] [api_testing] ✓ 完成 (发现 2 个问题)
[14:42:19] [exploit_verification] 启动 redteam_agent...
[14:48:33] [exploit_verification] ✓ 完成 (验证 5 个漏洞)
[14:48:34] [patch_generation] 启动 developer_agent...
[14:51:22] [patch_generation] ✓ 完成 (生成 5 个补丁)
[14:51:23] [final_review] 启动 security_reviewer...
[14:53:45] [final_review] ✓ 完成 (审查通过)
[14:53:45] 工作流执行完成
```

---

## 30 分钟进阶使用

### 场景：使用 Personality 和 Verification Loop

让我们深入了解如何使用安全专家角色和验证闭环。

#### 步骤 1: 查看可用 Personality

```bash
hos personality list
```

输出示例：

```
可用 Personality:
  cve_researcher - CVE vulnerability researcher
  red_team - Red team operator
  blue_team - Blue team defender
  code_reviewer - Security code reviewer
  exploit_validator - Exploit verification specialist
  senior_security_engineer - Senior security engineer
```

#### 步骤 2: 在 Python 中使用 Verification Loop

创建 `verify_finding.py`：

```python
import asyncio
from hosforge.verification import VerificationPipeline
from hosforge.memory import SecurityMemoryStore

async def main():
    # 创建共享的 Memory Store
    memory = SecurityMemoryStore()
    
    # 创建验证流水线
    pipeline = VerificationPipeline(memory_store=memory)
    
    # 定义安全发现
    finding = {
        "id": "VULN-001",
        "title": "SQL Injection in login form",
        "severity": "critical",
        "cwe_id": "CWE-89",
        "file_path": "src/auth/login.py",
        "line_number": 42,
        "description": "User input not properly sanitized"
    }
    
    # 执行完整验证流水线
    print("开始验证流水线...")
    result = await pipeline.run(finding)
    
    # 查看结果
    print(f"\n最终状态: {result['final_state']}")
    print(f"完成阶段: {list(result['stages'].keys())}")
    
    # 查看各阶段详情
    for stage_name, stage_result in result['stages'].items():
        print(f"\n[{stage_name}]")
        if stage_name == "verification":
            print(f"  验证结果: {stage_result.get('verified')}")
            print(f"  置信度: {stage_result.get('confidence')}")
        elif stage_name == "exploit":
            print(f"  可复现: {stage_result.get('reproducible')}")
            print(f"  CVSS: {stage_result.get('cvss_score')}")
        elif stage_name == "patch":
            print(f"  修复描述: {stage_result.get('description')}")
            print(f"  修改文件: {stage_result.get('files_changed')}")
        elif stage_name == "review":
            print(f"  审查通过: {stage_result.get('approved')}")
            print(f"  评分: {stage_result.get('score')}")
        elif stage_name == "pr":
            print(f"  PR 标题: {stage_result.get('pr_title')}")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python verify_finding.py
```

输出示例：

```
开始验证流水线...

最终状态: closed
完成阶段: ['verification', 'exploit', 'patch', 'review', 'pr']

[verification]
  验证结果: True
  置信度: 0.95

[exploit]
  可复现: True
  CVSS: 9.8

[patch]
  修复描述: Use parameterized query to prevent SQL injection
  修改文件: ['src/auth/login.py']

[review]
  审查通过: True
  评分: 92

[pr]
  PR 标题: Fix SQL injection vulnerability in login form
```

#### 步骤 3: 使用 Security Memory 查询历史

创建 `query_memory.py`：

```python
from hosforge.memory import SecurityMemoryStore

# 创建 Memory Store
memory = SecurityMemoryStore()

# 搜索相似的漏洞模式
print("搜索 SQL 注入相关模式...")
patterns = memory.search_patterns(
    query="SQL injection user input",
    top_k=5
)

for pattern in patterns:
    print(f"\n模式: {pattern.name}")
    print(f"  CWE: {pattern.cwe_id}")
    print(f"  误报率: {pattern.false_positive_rate:.2%}")
    print(f"  检测规则: {len(pattern.detection_rules)} 条")

# 查询 CVE 知识
print("\n\n查询 CVE-2024 相关漏洞...")
cves = memory.search_cve(
    query="web framework remote code execution",
    min_score=7.0,
    top_k=3
)

for cve in cves:
    print(f"\n{cve.cve_id}: {cve.description[:60]}...")
    print(f"  CVSS: {cve.cvss_score}")
    print(f"  修复版本: {cve.fixed_version}")

# 统计信息
print("\n\n统计信息:")
findings = memory.list_findings()
print(f"总发现数: {len(findings)}")

from collections import Counter
severity_counts = Counter(f.severity for f in findings)
print("按严重程度:")
for severity, count in severity_counts.items():
    print(f"  {severity}: {count}")
```

---

## 实际项目集成

### 场景：在 CI/CD 中集成 HOS-Forge

#### GitHub Actions 示例

创建 `.github/workflows/security-audit.yml`：

```yaml
name: Security Audit

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-audit:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install HOS-Forge
        run: |
          pip install poetry
          poetry install
      
      - name: Run Security Audit
        run: |
          poetry run hos taskflow run hosforge/taskflow/workflows/security-audit.yaml
      
      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-audit-results
          path: .hos-results/
      
      - name: Check for Critical Issues
        run: |
          # 检查是否有严重漏洞
          poetry run python scripts/check_critical.py
```

#### 自定义检查脚本

创建 `scripts/check_critical.py`：

```python
import json
import sys
from pathlib import Path

def check_results():
    """检查审计结果，如果有严重漏洞则返回非零退出码"""
    results_dir = Path(".hos-results")
    
    if not results_dir.exists():
        print("未找到审计结果")
        return 1
    
    # 查找最新的结果
    latest = max(results_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    result_file = latest / "summary.json"
    
    if not result_file.exists():
        print("未找到结果摘要")
        return 1
    
    with open(result_file) as f:
        summary = json.load(f)
    
    critical_count = summary.get("critical", 0)
    high_count = summary.get("high", 0)
    
    print(f"发现 {critical_count} 个严重漏洞，{high_count} 个高危漏洞")
    
    if critical_count > 0:
        print("❌ 存在严重漏洞，请修复后再合并")
        return 1
    elif high_count > 0:
        print("⚠️  存在高危漏洞，建议修复")
        return 0
    else:
        print("✓ 未发现严重或高危漏洞")
        return 0

if __name__ == "__main__":
    sys.exit(check_results())
```

---

## 下一步

恭喜你完成了快速入门！现在你可以：

1. **探索更多工作流**
   - 查看 `hosforge/taskflow/workflows/` 目录下的所有预定义工作流
   - 根据你的需求修改或创建新工作流

2. **自定义 Personality**
   - 查看 `hosforge/personalities/definitions/` 下的角色定义
   - 创建适合你团队的安全专家角色

3. **开发 MCP Server**
   - 参考 [MCP Server 开发指南](mcp-server-guide.md)
   - 集成你常用的安全工具

4. **深入理解架构**
   - 阅读 [Taskflow Engine](taskflow-guide.md) 了解工作流编排
   - 阅读 [Verification Loop](verification-loop.md) 了解验证闭环
   - 阅读 [Security Memory](security-memory-guide.md) 了解知识库

5. **贡献代码**
   - 提交 Issue 报告问题或建议
   - 提交 PR 贡献新功能或修复

---

## 常见问题

### Q: 如何查看工作流执行的详细日志？

```bash
# 设置日志级别
export HOS_LOG_LEVEL=DEBUG
hos taskflow run workflow.yaml
```

### Q: 工作流中断后如何恢复？

```bash
# 从最新 checkpoint 恢复
hos taskflow run workflow.yaml --checkpoint latest

# 列出可用 checkpoint
ls .checkpoints/
```

### Q: 如何并行执行多个工作流？

```bash
# 在后台运行多个工作流
hos taskflow run workflow1.yaml &
hos taskflow run workflow2.yaml &
wait
```

### Q: 如何集成自定义工具？

参考 [MCP Server 开发指南](mcp-server-guide.md) 创建自定义 MCP Server，然后在工作流中引用：

```yaml
tasks:
  - name: custom_scan
    agent: [sast_agent]
    tools: [my_custom_server]
```

---

## 获取帮助

- 📚 查看[完整文档](../README.md#文档)
- 💬 提交 [GitHub Issue](https://github.com/lxcxjxhx/HOS-Forge/issues)
- 🤝 参与 [Discussion](https://github.com/lxcxjxhx/HOS-Forge/discussions)
