# Personality 定义指南

## 概述

Security Personality 系统定义了安全专家角色的 YAML 配置，包括技能、规则、工具访问权限等。每个 Personality 代表一个特定领域的安全专家，可以在 Taskflow 工作流中被分配给不同的任务。

## 核心概念

### 1. Personality（人格/角色）

Personality 是一个 YAML 文件，定义了安全专家的身份、技能和行为规则。

```yaml
name: cve_researcher
role: CVE vulnerability researcher
description: Specialized in CVE analysis and exploit reproduction
skills:
  - CVE analysis
  - CWE mapping
  - exploit reproduction
  - patch analysis
rules:
  - provide evidence
  - never guess vulnerability
  - require reproduction
tools:
  - cve_database
  - nvd_api
  - exploit_db
  - debugger
```

### 2. 核心属性

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Personality 唯一标识 |
| `role` | string | ✅ | 角色名称 |
| `description` | string | ❌ | 角色描述 |
| `skills` | list[string] | ❌ | 技能列表 |
| `rules` | list[string] | ❌ | 行为规则列表 |
| `tools` | list[string] | ❌ | 可访问的 MCP 工具列表 |
| `metadata` | dict | ❌ | 自定义元数据 |

## 快速开始

### 1. 创建 Personality 文件

创建 `personalities/my_expert.yaml`：

```yaml
name: my_expert
role: Security Expert
description: Custom security expert specialized in web applications
skills:
  - web security
  - OWASP Top 10
  - penetration testing
rules:
  - follow OWASP testing guide
  - document all findings
  - verify before reporting
tools:
  - nuclei
  - owasp_zap
  - burp_suite
```

### 2. 加载 Personality

```bash
# 列出所有可用 Personality
hos personality list

# 在任务中使用
# 在 workflow.yaml 中引用
tasks:
  - name: web_scan
    personality: my_expert
    tools: [nuclei, owasp_zap]
```

### 3. Python API 使用

```python
from hosforge.personalities import PersonalityLoader

# 加载所有 Personality
loader = PersonalityLoader("personalities/")
all_personalities = loader.list_personalities()

# 获取特定 Personality
expert = loader.get_personality("my_expert")
print(expert.role)  # "Security Expert"
print(expert.skills)  # ["web security", "OWASP Top 10", ...]
```

## 预定义 Personality

HOS-Forge 提供了多个预定义的安全专家角色：

### 1. CVE Researcher

专注于 CVE 漏洞研究和利用复现。

```yaml
name: cve_researcher
role: CVE vulnerability researcher
description: Specialized in CVE analysis, CWE mapping, and exploit reproduction
skills:
  - CVE analysis
  - CWE mapping
  - exploit reproduction
  - patch analysis
  - vulnerability research
rules:
  - provide evidence for all claims
  - never guess vulnerability existence
  - require reproduction steps
  - document all findings
  - verify CVE IDs against official databases
tools:
  - cve_database
  - nvd_api
  - exploit_db
  - debugger
  - disassembler
```

**使用场景**：
- CVE 漏洞研究
- 漏洞利用开发
- 补丁分析

### 2. Red Team

红队攻击专家，专注于渗透测试和攻击验证。

```yaml
name: red_team
role: Red team operator
description: Expert in penetration testing and attack verification
skills:
  - penetration testing
  - exploit development
  - attack simulation
  - privilege escalation
  - lateral movement
rules:
  - follow rules of engagement
  - document all attack paths
  - verify exploit success
  - report all findings
  - minimize impact on target systems
tools:
  - nuclei
  - metasploit
  - exploit_db
  - burp_suite
  - sqlmap
```

**使用场景**：
- 渗透测试
- 攻击路径验证
- 漏洞利用开发

### 3. Blue Team

蓝队防御专家，专注于安全检测和响应。

```yaml
name: blue_team
role: Blue team defender
description: Expert in security detection, monitoring, and incident response
skills:
  - security monitoring
  - incident response
  - threat hunting
  - log analysis
  - security hardening
rules:
  - monitor all suspicious activities
  - document all incidents
  - follow incident response procedures
  - minimize false positives
  - provide actionable recommendations
tools:
  - siem
  - log_analyzer
  - ids_ips
  - threat_intel
```

**使用场景**：
- 安全监控
- 事件响应
- 威胁狩猎

### 4. Code Reviewer

代码审查专家，专注于安全代码审计。

```yaml
name: code_reviewer
role: Security code reviewer
description: Expert in secure code review and vulnerability detection
skills:
  - code review
  - static analysis
  - vulnerability detection
  - secure coding practices
  - code quality assessment
rules:
  - review all code changes
  - identify security vulnerabilities
  - provide remediation suggestions
  - follow secure coding standards
  - document all findings
tools:
  - semgrep
  - codeql
  - hos_ls
  - sonarqube
```

**使用场景**：
- 代码安全审计
- 静态分析
- 漏洞检测

### 5. SAST Agent

静态应用安全测试专家。

```yaml
name: sast_agent
role: SAST specialist
description: Expert in static application security testing
skills:
  - static analysis
  - code scanning
  - vulnerability detection
  - false positive reduction
rules:
  - scan all source code
  - minimize false positives
  - provide accurate line numbers
  - suggest remediation
tools:
  - semgrep
  - codeql
  - hos_ls
  - bandit
  - eslint-security
```

### 6. DAST Agent

动态应用安全测试专家。

```yaml
name: dast_agent
role: DAST specialist
description: Expert in dynamic application security testing
skills:
  - dynamic testing
  - web application scanning
  - API testing
  - vulnerability verification
rules:
  - test all endpoints
  - verify vulnerabilities
  - document attack vectors
  - provide reproduction steps
tools:
  - nuclei
  - owasp_zap
  - burp_suite
  - sqlmap
```

### 7. Developer Agent

开发专家，专注于安全修复和补丁生成。

```yaml
name: developer_agent
role: Security developer
description: Expert in secure coding and vulnerability remediation
skills:
  - secure coding
  - vulnerability remediation
  - patch development
  - code refactoring
rules:
  - follow secure coding practices
  - test all patches
  - minimize code changes
  - document all modifications
tools:
  - code_editor
  - git
  - test_framework
  - code_fixer
```

### 8. Security Reviewer

安全审查专家，负责最终审查和报告生成。

```yaml
name: security_reviewer
role: Security reviewer
description: Expert in security assessment and report generation
skills:
  - security assessment
  - report generation
  - risk evaluation
  - recommendation development
rules:
  - review all findings
  - verify evidence
  - assess risk levels
  - provide actionable recommendations
  - generate comprehensive reports
tools:
  - report_generator
  - risk_assessor
  - review_assistant
```

## 自定义 Personality

### 1. 设计原则

- **专注性**：每个 Personality 应该专注于特定领域
- **最小权限**：只分配必要的工具访问权限
- **明确规则**：定义清晰的行为规则
- **可复用性**：设计可被多个工作流复用的 Personality

### 2. 创建步骤

#### 步骤 1: 定义角色

确定 Personality 的专业领域和职责：

```yaml
name: api_security_expert
role: API Security Specialist
description: Specialized in API security testing and vulnerability assessment
```

#### 步骤 2: 定义技能

列出该角色需要的技能：

```yaml
skills:
  - API security testing
  - OWASP API Top 10
  - authentication bypass
  - authorization flaws
  - injection attacks
```

#### 步骤 3: 定义规则

定义该角色的行为规则：

```yaml
rules:
  - test all API endpoints
  - verify authentication mechanisms
  - check authorization controls
  - test for injection vulnerabilities
  - document all findings with evidence
  - provide remediation suggestions
```

#### 步骤 4: 分配工具

分配该角色需要的 MCP 工具：

```yaml
tools:
  - nuclei
  - postman
  - burp_suite
  - api_scanner
```

#### 步骤 5: 完整示例

```yaml
name: api_security_expert
role: API Security Specialist
description: Specialized in API security testing and vulnerability assessment
skills:
  - API security testing
  - OWASP API Top 10
  - authentication bypass
  - authorization flaws
  - injection attacks
rules:
  - test all API endpoints
  - verify authentication mechanisms
  - check authorization controls
  - test for injection vulnerabilities
  - document all findings with evidence
  - provide remediation suggestions
tools:
  - nuclei
  - postman
  - burp_suite
  - api_scanner
metadata:
  version: "1.0"
  author: "HOS-Forge Team"
  tags: ["api", "security", "testing"]
```

### 3. 目录结构

```
personalities/
├── cve_researcher.yaml
├── red_team.yaml
├── blue_team.yaml
├── code_reviewer.yaml
├── sast_agent.yaml
├── dast_agent.yaml
├── developer_agent.yaml
├── security_reviewer.yaml
└── custom/
    └── my_expert.yaml
```

## 高级特性

### 1. 工具权限控制

通过 `tools` 字段精确控制 Personality 可访问的工具：

```yaml
name: limited_reviewer
role: Limited Reviewer
skills:
  - code review
tools:
  - semgrep  # 只能使用 semgrep
  # 不能访问 nuclei, metasploit 等危险工具
```

### 2. 规则引擎

规则可以包含条件逻辑：

```yaml
rules:
  - if severity == 'critical': require_evidence()
  - if tool == 'nuclei': verify_findings()
  - always: document_findings()
```

### 3. 元数据扩展

使用 `metadata` 字段添加自定义信息：

```yaml
metadata:
  version: "1.0"
  author: "Security Team"
  tags: ["web", "api", "security"]
  created: "2026-07-26"
  updated: "2026-07-26"
```

### 4. Personality 继承（计划中）

未来版本将支持 Personality 继承：

```yaml
name: senior_red_team
extends: red_team  # 继承 red_team 的所有属性
additional_skills:
  - advanced exploit development
  - zero-day research
additional_tools:
  - custom_exploit_framework
```

## 在 Taskflow 中使用

### 1. 在任务中引用 Personality

```yaml
tasks:
  - name: api_testing
    personality: api_security_expert
    tools: [nuclei, postman]
    depends_on: []
```

### 2. 多 Personality 协作

```yaml
tasks:
  - name: initial_scan
    personality: sast_agent
    tools: [semgrep, codeql]
  
  - name: exploit_verification
    personality: red_team
    tools: [nuclei, metasploit]
    depends_on: [initial_scan]
  
  - name: patch_development
    personality: developer_agent
    tools: [code_editor]
    depends_on: [exploit_verification]
  
  - name: final_review
    personality: security_reviewer
    tools: [report_generator]
    depends_on: [patch_development]
```

### 3. 动态 Personality 选择

根据任务类型动态选择 Personality：

```python
from hosforge.personalities import PersonalityLoader
from hosforge.taskflow import WorkflowParser

# 加载工作流
workflow = WorkflowParser.parse_file("workflow.yaml")

# 加载 Personality
loader = PersonalityLoader("personalities/")

# 为每个任务分配 Personality
for task in workflow.tasks:
    if task.personality:
        personality = loader.get_personality(task.personality)
        # 根据 personality 配置执行任务
```

## 最佳实践

### 1. 命名规范

- 使用小写字母和下划线：`cve_researcher`
- 名称应该反映角色职责
- 避免过于通用的名称

### 2. 技能定义

- 使用具体的技能名称
- 避免重叠技能
- 保持技能列表简洁

### 3. 规则设计

- 规则应该明确、可执行
- 避免矛盾的规则
- 优先考虑安全性

### 4. 工具分配

- 遵循最小权限原则
- 只分配必要的工具
- 考虑工具的安全风险

### 5. 版本控制

- 使用 `metadata.version` 跟踪变更
- 记录变更历史
- 保持向后兼容

## API 参考

### PersonalityLoader

```python
class PersonalityLoader:
    """Personality 加载器"""
    
    def __init__(self, personalities_dir: str = "personalities/"):
        """初始化加载器"""
    
    def get_personality(self, name: str) -> Personality:
        """获取指定 Personality"""
    
    def list_personalities(self) -> List[Personality]:
        """列出所有 Personality"""
    
    def reload(self):
        """重新加载所有 Personality"""
```

### Personality

```python
@dataclass
class Personality:
    """Personality 数据类"""
    name: str
    role: str
    description: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_skill(self, skill: str) -> bool:
        """检查是否具有指定技能"""
    
    def has_tool_access(self, tool: str) -> bool:
        """检查是否具有工具访问权限"""
    
    def validate_rules(self) -> List[str]:
        """验证规则列表"""
```

## 故障排查

### 问题 1: Personality 加载失败

```bash
# 检查文件是否存在
ls personalities/my_expert.yaml

# 验证 YAML 语法
hos personality validate my_expert.yaml
```

### 问题 2: 工具访问被拒绝

确保 Personality 的 `tools` 列表包含所需工具：

```yaml
tools:
  - nuclei  # 确保包含
```

### 问题 3: Personality 未找到

确保 Personality 文件在正确的目录下：

```bash
# 列出可用 Personality
hos personality list
```

## 参考资源

- [Personality Schema](../hosforge/personalities/schema.py)
- [Personality Loader](../hosforge/personalities/loader.py)
- [预定义 Personality](../hosforge/personalities/definitions/)
- [Taskflow 使用指南](taskflow-guide.md)
- [Verification Loop](verification-loop.md)
- [Security Memory](security-memory-guide.md)
- [MCP Server 开发](mcp-server-guide.md)
- [快速入门](getting-started.md)
