# Verification Loop 使用指南

## 概述

Agent Verification Loop 是 HOS-Forge 的安全验证闭环系统，实现了从漏洞发现到修复完成的完整生命周期管理。通过状态机驱动的多阶段验证流程，确保每个安全发现都经过严格验证、修复和审查。

### 核心价值

- **自动化验证**：从发现到修复的全流程自动化
- **质量保证**：多轮审查确保修复质量
- **状态追踪**：清晰的状态流转和审计轨迹
- **误报过滤**：在早期阶段过滤误报，节省资源

---

## 核心概念

### 1. 状态机（State Machine）

安全发现的生命周期由状态机管理，包含以下状态：

```
FINDING → CANDIDATE → VERIFIED → FIXED → CLOSED
              ↓           ↓
          REJECTED    REJECTED
```

| 状态 | 说明 | 后续状态 |
|------|------|----------|
| `FINDING` | 初始发现 | CANDIDATE |
| `CANDIDATE` | 候选验证 | VERIFIED, REJECTED |
| `VERIFIED` | 已验证漏洞 | FIXED |
| `FIXED` | 已修复 | CLOSED |
| `CLOSED` | 已关闭（终态） | FINDING（重置） |
| `REJECTED` | 已拒绝（终态） | FINDING（重置） |

### 2. 验证流水线（Pipeline）

Verification Pipeline 按以下 5 个阶段顺序执行：

```
┌─────────────────────────────────────────────────────────────┐
│  阶段 1: VerificationAgent - 误报检查                         │
│  ├─ 检查历史误报模式                                          │
│  ├─ 评估漏洞可信度                                            │
│  └─ 输出：verified (true/false)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段 2: ExploitAgent - 漏洞复现                              │
│  ├─ 生成漏洞利用代码                                          │
│  ├─ 执行复现测试                                              │
│  └─ 输出：reproducible (true/false)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段 3: PatchAgent - 生成修复代码                            │
│  ├─ 分析漏洞根因                                              │
│  ├─ 生成修复补丁                                              │
│  └─ 输出：patch_code, description                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段 4: ReviewAgent - 审查修复（最多 3 次重试）               │
│  ├─ 验证修复完整性                                            │
│  ├─ 检查是否引入新问题                                        │
│  └─ 输出：approved (true/false), score (0-100)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段 5: PRGeneratorAgent - 生成 PR 元数据                    │
│  ├─ 生成 PR 标题和描述                                        │
│  ├─ 关联 CVE/CWE 信息                                        │
│  └─ 输出：pr_title, pr_description, labels                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 基本使用

```python
import asyncio
from hosforge.verification import VerificationPipeline

async def main():
    # 创建流水线
    pipeline = VerificationPipeline()
    
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
    
    # 执行验证流水线
    result = await pipeline.run(finding)
    
    # 查看结果
    print(f"Final state: {result['final_state']}")
    print(f"Stages completed: {list(result['stages'].keys())}")

asyncio.run(main())
```

### 2. 集成 Security Memory

```python
from hosforge.verification import VerificationPipeline
from hosforge.memory import SecurityMemoryStore

# 创建共享的 Memory Store
memory = SecurityMemoryStore()

# 创建流水线（传入 memory_store）
pipeline = VerificationPipeline(memory_store=memory)

# 执行验证
result = await pipeline.run(finding)

# Memory 会自动：
# - 记录验证过程
# - 更新误报率统计
# - 保存修复历史
```

### 3. 查看流水线状态

```python
# 执行过程中查看状态
status = pipeline.get_pipeline_status()

print(f"Current state: {status['state']}")
print(f"Finding ID: {status['finding_id']}")

# 查看各阶段结果
for stage_name, stage_result in status['stage_results'].items():
    print(f"{stage_name}: {stage_result}")
```

---

## 核心组件

### 1. FindingStateMachine

状态机管理发现的生命周期。

```python
from hosforge.verification import FindingStateMachine, FindingState

# 创建状态机
sm = FindingStateMachine("VULN-001")

# 查看当前状态
print(sm.current_state)  # FindingState.FINDING

# 状态转换
sm.transition(FindingState.CANDIDATE)
print(sm.current_state)  # FindingState.CANDIDATE

# 查看允许的转换
allowed = sm.get_allowed_transitions()
print([s.value for s in allowed])  # ['verified', 'rejected', 'finding']

# 检查是否终止
print(sm.is_terminal())  # False

# 重置状态
sm.reset()
print(sm.current_state)  # FindingState.FINDING
```

### 2. VerificationAgent

误报检查 Agent。

```python
from hosforge.verification import VerificationAgent

agent = VerificationAgent(memory_store=memory)

result = await agent.execute(finding)

# 返回结果示例
{
    "verified": True,
    "confidence": 0.95,
    "false_positive_rate": 0.05,
    "reason": "Pattern matches known SQL injection vulnerability",
    "similar_findings": ["VULN-002", "VULN-003"]
}
```

### 3. ExploitAgent

漏洞复现 Agent。

```python
from hosforge.verification import ExploitAgent

agent = ExploitAgent(memory_store=memory)

result = await agent.execute(finding)

# 返回结果示例
{
    "reproducible": True,
    "exploit_code": "import requests\n...",
    "proof_of_concept": "curl -X POST ...",
    "impact": "Database compromise",
    "cvss_score": 9.8
}
```

### 4. PatchAgent

修复代码生成 Agent。

```python
from hosforge.verification import PatchAgent

agent = PatchAgent(memory_store=memory)

result = await agent.execute(finding)

# 返回结果示例
{
    "patch_code": "def login(username, password):\n    # Use parameterized query\n    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))",
    "description": "Use parameterized query to prevent SQL injection",
    "files_changed": ["src/auth/login.py"],
    "lines_changed": 5
}
```

### 5. ReviewAgent

修复审查 Agent。

```python
from hosforge.verification import ReviewAgent

agent = ReviewAgent(memory_store=memory)

review_input = {**finding, **patch_result}
result = await agent.execute(review_input)

# 返回结果示例
{
    "approved": True,
    "score": 92,
    "feedback": "Fix properly addresses the SQL injection vulnerability",
    "issues": [],
    "recommendations": ["Add unit tests for the fix"]
}
```

### 6. PRGeneratorAgent

PR 元数据生成 Agent。

```python
from hosforge.verification import PRGeneratorAgent

agent = PRGeneratorAgent(memory_store=memory)

pr_input = {**finding, **patch_result}
result = await agent.execute(pr_input)

# 返回结果示例
{
    "pr_title": "Fix SQL injection vulnerability in login form",
    "pr_description": "## Summary\nFixes SQL injection...",
    "labels": ["security", "bug", "critical"],
    "cve_id": "CVE-2024-12345",
    "cwe_id": "CWE-89"
}
```

---

## 状态流转详解

### 1. FINDING → CANDIDATE

```python
# 进入候选池
state_machine.transition(FindingState.CANDIDATE)
```

**触发条件**：
- 新发现进入验证流水线
- 开始误报检查

### 2. CANDIDATE → VERIFIED

```python
# 漏洞验证成功
state_machine.transition(FindingState.VERIFIED)
```

**触发条件**：
- VerificationAgent 确认非误报
- ExploitAgent 成功复现漏洞

### 3. CANDIDATE → REJECTED

```python
# 判定为误报
state_machine.transition(FindingState.REJECTED)
```

**触发条件**：
- VerificationAgent 判定为误报
- ExploitAgent 无法复现

### 4. VERIFIED → FIXED

```python
# 修复完成
state_machine.transition(FindingState.FIXED)
```

**触发条件**：
- PatchAgent 生成修复代码
- ReviewAgent 审查通过（最多 3 次重试）

### 5. FIXED → CLOSED

```python
# 流程关闭
state_machine.transition(FindingState.CLOSED)
```

**触发条件**：
- PRGeneratorAgent 生成 PR 元数据
- 所有阶段完成

---

## 与 Taskflow 集成

在 Taskflow 工作流中使用 Verification Loop：

```yaml
# workflow.yaml
tasks:
  - name: static_scan
    agent: [sast_agent]
    tools: [hos_ls, semgrep]
  
  - name: verify_findings
    agent: [redteam_agent]
    tools: [nuclei]
    depends_on: [static_scan]
    # 这里会调用 VerificationPipeline
  
  - name: generate_patches
    agent: [developer_agent]
    depends_on: [verify_findings]
  
  - name: review_patches
    agent: [security_reviewer]
    depends_on: [generate_patches]
```

在任务处理器中调用：

```python
from hosforge.verification import VerificationPipeline

async def handle_verify_findings(task, context):
    findings = context.get("scan_findings", [])
    
    pipeline = VerificationPipeline(memory_store=context.memory_store)
    
    verified_findings = []
    for finding in findings:
        result = await pipeline.run(finding)
        if result["final_state"] == "closed":
            verified_findings.append(result)
    
    context["verified_findings"] = verified_findings
    return verified_findings
```

---

## 高级特性

### 1. 自定义重试次数

```python
from hosforge.verification import VerificationPipeline

# 修改最大重试次数（默认 3 次）
import hosforge.verification.pipeline as pipeline_module
pipeline_module.MAX_PATCH_RETRIES = 5

pipeline = VerificationPipeline()
```

### 2. 阶段结果追踪

```python
# 获取所有阶段结果
status = pipeline.get_pipeline_status()

# 访问特定阶段
verification_result = status["stage_results"]["verification"]
exploit_result = status["stage_results"]["exploit"]
patch_result = status["stage_results"]["patch"]
review_result = status["stage_results"]["review"]
pr_result = status["stage_results"]["pr"]

# 查看重试历史
for i in range(1, 4):
    attempt_key = f"patch_attempt_{i}"
    if attempt_key in status["stage_results"]:
        print(f"Patch attempt {i}: {status['stage_results'][attempt_key]}")
```

### 3. 错误处理

```python
try:
    result = await pipeline.run(finding)
    
    if result["final_state"] == "rejected":
        rejected_at = result.get("rejected_at")
        print(f"Finding rejected at stage: {rejected_at}")
        
        if rejected_at == "verification":
            print("Failed verification check")
        elif rejected_at == "exploit":
            print("Could not reproduce vulnerability")
        elif rejected_at == "review":
            print("Patch review failed after 3 attempts")
    
except Exception as e:
    print(f"Pipeline error: {e}")
```

---

## 最佳实践

### 1. 状态机使用

```python
# ✅ 正确：检查允许的转换
allowed = sm.get_allowed_transitions()
if FindingState.VERIFIED in allowed:
    sm.transition(FindingState.VERIFIED)

# ❌ 错误：直接转换而不检查
sm.transition(FindingState.CLOSED)  # 可能抛出 ValueError
```

### 2. Memory 集成

```python
# ✅ 正确：共享 Memory Store
memory = SecurityMemoryStore()
pipeline = VerificationPipeline(memory_store=memory)

# ❌ 错误：每次创建新的 Memory Store
pipeline1 = VerificationPipeline(memory_store=SecurityMemoryStore())
pipeline2 = VerificationPipeline(memory_store=SecurityMemoryStore())
# 数据不会共享！
```

### 3. 批量处理

```python
# ✅ 正确：批量处理多个发现
async def process_findings(findings):
    pipeline = VerificationPipeline(memory_store=memory)
    results = []
    
    for finding in findings:
        result = await pipeline.run(finding)
        results.append(result)
    
    return results

# ❌ 错误：为每个发现创建新的 pipeline
for finding in findings:
    pipeline = VerificationPipeline()  # 重复创建
    result = await pipeline.run(finding)
```

### 4. 结果验证

```python
# ✅ 正确：验证最终状态
result = await pipeline.run(finding)

if result["final_state"] == "closed":
    print("Successfully processed")
    pr_data = result["stages"]["pr"]
    # 使用 PR 数据
else:
    print(f"Processing failed: {result.get('rejected_at')}")
```

---

## 故障排查

### 问题 1: 状态转换失败

```python
# 检查当前状态和允许的转换
print(f"Current state: {sm.current_state}")
print(f"Allowed transitions: {[s.value for s in sm.get_allowed_transitions()]}")

# 捕获异常
try:
    sm.transition(FindingState.VERIFIED)
except ValueError as e:
    print(f"Transition failed: {e}")
```

### 问题 2: 流水线卡在某个阶段

```python
# 查看流水线状态
status = pipeline.get_pipeline_status()
print(f"Current state: {status['state']}")
print(f"Completed stages: {list(status['stage_results'].keys())}")

# 检查是否有异常
import logging
logging.basicConfig(level=logging.DEBUG)
# 重新运行流水线查看详细日志
```

### 问题 3: 审查多次失败

```python
# 查看每次审查的评分
status = pipeline.get_pipeline_status()

for i in range(1, 4):
    review_key = f"review_attempt_{i}"
    if review_key in status["stage_results"]:
        review = status["stage_results"][review_key]
        print(f"Attempt {i}: score={review.get('score')}, approved={review.get('approved')}")
        if not review.get("approved"):
            print(f"  Feedback: {review.get('feedback')}")
            print(f"  Issues: {review.get('issues')}")
```

---

## API 参考

### VerificationPipeline

```python
class VerificationPipeline:
    """安全发现验证流水线"""
    
    def __init__(self, memory_store: Optional[SecurityMemoryStore] = None):
        """初始化流水线
        
        Args:
            memory_store: 可选的安全记忆存储
        """
    
    async def run(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整验证流水线
        
        Args:
            finding: 安全发现信息字典
        
        Returns:
            Dict 包含流水线结果
        """
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取流水线当前状态
        
        Returns:
            Dict 包含状态和各阶段结果
        """
```

### FindingStateMachine

```python
class FindingStateMachine:
    """安全发现状态机"""
    
    def __init__(self, finding_id: str):
        """初始化状态机
        
        Args:
            finding_id: 发现 ID
        """
    
    @property
    def current_state(self) -> FindingState:
        """获取当前状态"""
    
    def transition(self, new_state: FindingState) -> bool:
        """转换到新状态
        
        Args:
            new_state: 目标状态
        
        Returns:
            bool: 转换是否成功
        
        Raises:
            ValueError: 当转换不被允许时
        """
    
    def get_allowed_transitions(self) -> List[FindingState]:
        """获取允许的所有转换目标"""
    
    def reset(self) -> None:
        """重置状态到 FINDING"""
    
    def is_terminal(self) -> bool:
        """检查是否处于终止状态"""
```

---

## 参考资源

- [State Machine 实现](../hosforge/verification/state_machine.py)
- [Pipeline 实现](../hosforge/verification/pipeline.py)
- [Agents 实现](../hosforge/verification/agents.py)
- [Security Memory](security-memory-guide.md)
- [Taskflow Engine](taskflow-guide.md)
- [Personality 定义](personality-guide.md)
- [MCP Server 开发](mcp-server-guide.md)
- [快速入门](getting-started.md)
