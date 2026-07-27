# Security Memory 使用指南

## 概述

Security Memory 是 HOS-Forge 的安全知识库系统，用于存储和管理 CVE 知识、漏洞模式、修复历史、误报记录等安全相关信息。它支持语义搜索、误报率统计和模式匹配，帮助 Agent 做出更智能的决策。

## 核心概念

### 1. 数据结构

Security Memory 包含以下核心数据类型：

- **VulnerabilityFinding**: 漏洞发现记录
- **CVEKnowledge**: CVE 漏洞知识
- **VulnerabilityPattern**: 漏洞模式
- **PatchHistory**: 修复历史

### 2. 核心功能

- **存储管理**: 添加、查询、更新安全数据
- **语义搜索**: 基于向量数据库的语义搜索
- **误报统计**: 统计和分析误报率
- **模式匹配**: 识别相似的漏洞模式
- **历史学习**: 从历史任务中学习

## 快速开始

### 1. 初始化 Security Memory

```python
from hosforge.memory import SecurityMemoryStore

# 创建存储实例
memory = SecurityMemoryStore()
```

### 2. 添加漏洞发现

```python
from hosforge.memory.schema import VulnerabilityFinding

# 创建漏洞发现
finding = VulnerabilityFinding(
    id="VULN-001",
    title="SQL Injection in login form",
    severity="critical",
    cwe_id="CWE-89",
    file_path="src/auth/login.py",
    line_number=42,
    description="User input not properly sanitized",
    status="verified",
    confidence=0.95,
    false_positive_rate=0.05
)

# 添加到存储
memory.add_finding(finding)
```

### 3. 查询漏洞发现

```python
# 获取单个发现
finding = memory.get_finding("VULN-001")

# 搜索发现
results = memory.search_findings(
    query="SQL injection",
    severity="critical"
)

# 列出所有发现
all_findings = memory.list_findings()
```

### 4. 添加 CVE 知识

```python
from hosforge.memory.schema import CVEKnowledge

cve = CVEKnowledge(
    cve_id="CVE-2024-12345",
    description="Critical vulnerability in Example Library",
    severity="critical",
    cvss_score=9.8,
    affected_versions=["1.0.0", "1.1.0", "1.2.0"],
    fixed_version="1.2.1",
    references=["https://nvd.nist.gov/vuln/detail/CVE-2024-12345"],
    patch_url="https://github.com/example/commit/abc123"
)

memory.add_cve_knowledge(cve)
```

### 5. 添加漏洞模式

```python
from hosforge.memory.schema import VulnerabilityPattern

pattern = VulnerabilityPattern(
    id="PATTERN-001",
    name="SQL Injection Pattern",
    description="Common SQL injection vulnerability pattern",
    cwe_id="CWE-89",
    code_snippets=[
        "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
        "cursor.execute(f\"DELETE FROM {table}\")"
    ],
    false_positive_rate=0.15,
    detection_rules=["rule1", "rule2"]
)

memory.add_pattern(pattern)
```

## 核心数据类型

### VulnerabilityFinding

漏洞发现记录。

```python
@dataclass
class VulnerabilityFinding:
    id: str                          # 唯一标识
    title: str                       # 标题
    severity: str                    # 严重程度 (critical/high/medium/low/info)
    cwe_id: str                      # CWE ID
    file_path: str                   # 文件路径
    line_number: int                 # 行号
    description: str                 # 描述
    status: str                      # 状态 (finding/verified/fixed/closed/rejected)
    confidence: float                # 置信度 (0.0-1.0)
    false_positive_rate: float       # 误报率 (0.0-1.0)
    created_at: str                  # 创建时间
    updated_at: str                  # 更新时间
    metadata: Dict[str, Any]         # 元数据
```

### CVEKnowledge

CVE 漏洞知识。

```python
@dataclass
class CVEKnowledge:
    cve_id: str                      # CVE ID
    description: str                 # 描述
    severity: str                    # 严重程度
    cvss_score: float                # CVSS 评分
    affected_versions: List[str]     # 受影响版本
    fixed_version: Optional[str]     # 修复版本
    references: List[str]            # 参考资料
    patch_url: Optional[str]         # 补丁 URL
    metadata: Dict[str, Any]         # 元数据
```

### VulnerabilityPattern

漏洞模式。

```python
@dataclass
class VulnerabilityPattern:
    id: str                          # 唯一标识
    name: str                        # 名称
    description: str                 # 描述
    cwe_id: str                      # CWE ID
    code_snippets: List[str]         # 代码片段示例
    false_positive_rate: float       # 误报率
    detection_rules: List[str]       # 检测规则
    metadata: Dict[str, Any]         # 元数据
```

### PatchHistory

修复历史。

```python
@dataclass
class PatchHistory:
    id: str                          # 唯一标识
    finding_id: str                  # 关联的漏洞 ID
    patch_description: str           # 补丁描述
    code_changes: Dict[str, Any]     # 代码变更
    verification_status: str         # 验证状态
    verification_result: Optional[Dict[str, Any]]  # 验证结果
    created_at: str                  # 创建时间
    metadata: Dict[str, Any]         # 元数据
```

## 高级功能

### 1. 语义搜索

使用向量数据库进行语义搜索：

```python
# 搜索相似的漏洞模式
similar_patterns = memory.search_patterns(
    query="User input not sanitized in SQL query",
    severity="critical",
    top_k=5
)

# 搜索相关的 CVE
related_cves = memory.search_cve(
    query="Remote code execution in web framework",
    min_score=7.0
)
```

### 2. 误报率统计

```python
# 获取特定模式的误报率
pattern = memory.get_pattern("PATTERN-001")
if pattern:
    print(f"False positive rate: {pattern.false_positive_rate:.2%}")

# 搜索高误报率模式
high_fp_patterns = memory.search_patterns(
    query="injection",
    max_fp_rate=0.5  # 误报率低于 50%
)
```

### 3. 模式匹配

```python
# 查找相似的历史发现
similar_findings = memory.search_findings(
    query="Authentication bypass in API endpoint",
    similarity_threshold=0.8
)

# 基于历史数据评估新发现
for finding in similar_findings:
    print(f"Found similar: {finding.title}")
    print(f"  Status: {finding.status}")
    print(f"  FP rate: {finding.false_positive_rate:.2%}")
```

### 4. 历史学习

```python
# 获取特定类型漏洞的修复历史
patches = memory.list_patches()
sql_injection_patches = [
    p for p in patches 
    if memory.get_finding(p.finding_id).cwe_id == "CWE-89"
]

# 分析修复模式
for patch in sql_injection_patches[:5]:
    print(f"Patch: {patch.patch_description}")
    print(f"  Status: {patch.verification_status}")
```

### 5. 统计分析

```python
# 统计各严重程度的发现数量
from collections import Counter

findings = memory.list_findings()
severity_counts = Counter(f.severity for f in findings)

print("Findings by severity:")
for severity, count in severity_counts.items():
    print(f"  {severity}: {count}")

# 统计各状态的发现数量
status_counts = Counter(f.status for f in findings)

print("\nFindings by status:")
for status, count in status_counts.items():
    print(f"  {status}: {count}")
```

## API 参考

### SecurityMemoryStore

```python
class SecurityMemoryStore:
    """安全内存存储"""
    
    def __init__(self):
        """初始化存储"""
    
    # Finding 操作
    def add_finding(self, finding: VulnerabilityFinding) -> None:
        """添加漏洞发现"""
    
    def get_finding(self, finding_id: str) -> Optional[VulnerabilityFinding]:
        """获取漏洞发现"""
    
    def list_findings(self) -> List[VulnerabilityFinding]:
        """列出所有漏洞发现"""
    
    def search_findings(
        self,
        query: str = "",
        severity: Optional[str] = None,
        status: Optional[str] = None,
        cwe_id: Optional[str] = None,
        similarity_threshold: float = 0.0,
        top_k: int = 10
    ) -> List[VulnerabilityFinding]:
        """搜索漏洞发现"""
    
    # CVE 知识操作
    def add_cve_knowledge(self, cve: CVEKnowledge) -> None:
        """添加 CVE 知识"""
    
    def get_cve_knowledge(self, cve_id: str) -> Optional[CVEKnowledge]:
        """获取 CVE 知识"""
    
    def list_cve_knowledge(self) -> List[CVEKnowledge]:
        """列出所有 CVE 知识"""
    
    def search_cve(
        self,
        query: str = "",
        severity: Optional[str] = None,
        min_score: Optional[float] = None,
        top_k: int = 10
    ) -> List[CVEKnowledge]:
        """搜索 CVE 知识"""
    
    # Pattern 操作
    def add_pattern(self, pattern: VulnerabilityPattern) -> None:
        """添加漏洞模式"""
    
    def get_pattern(self, pattern_id: str) -> Optional[VulnerabilityPattern]:
        """获取漏洞模式"""
    
    def list_patterns(self) -> List[VulnerabilityPattern]:
        """列出所有漏洞模式"""
    
    def search_patterns(
        self,
        query: str = "",
        cwe_id: Optional[str] = None,
        max_fp_rate: Optional[float] = None,
        top_k: int = 10
    ) -> List[VulnerabilityPattern]:
        """搜索漏洞模式"""
    
    # Patch 操作
    def add_patch(self, patch: PatchHistory) -> None:
        """添加修复历史"""
    
    def get_patch(self, patch_id: str) -> Optional[PatchHistory]:
        """获取修复历史"""
    
    def list_patches(self) -> List[PatchHistory]:
        """列出所有修复历史"""
```

## 与 Verification Loop 集成

Security Memory 与 Verification Loop 紧密集成，提供历史数据支持：

```python
from hosforge.memory import SecurityMemoryStore
from hosforge.verification import VerificationPipeline

# 创建共享的 Memory Store
memory = SecurityMemoryStore()

# 创建验证 Pipeline
pipeline = VerificationPipeline(memory_store=memory)

# 运行验证
finding = {
    "id": "VULN-001",
    "title": "SQL Injection",
    "severity": "critical",
    "description": "User input not sanitized"
}

result = await pipeline.run(finding)

# 验证过程中会自动查询 Memory
# - 检查相似模式的误报率
# - 查找历史修复方案
# - 评估漏洞可信度
```

### 验证流程中的 Memory 使用

1. **初始验证阶段**
   - 查询相似漏洞模式
   - 计算历史误报率
   - 评估漏洞可信度

2. **漏洞利用阶段**
   - 查找历史利用案例
   - 获取相关 CVE 信息
   - 评估利用难度

3. **修复阶段**
   - 查找历史修复方案
   - 获取最佳实践
   - 评估修复效果

4. **审查阶段**
   - 对比历史修复
   - 验证修复完整性
   - 生成审查报告

## 持久化存储

### 1. JSON 文件存储

```python
import json
from pathlib import Path

class PersistentMemoryStore(SecurityMemoryStore):
    """持久化内存存储"""
    
    def __init__(self, storage_dir: str = ".memory"):
        super().__init__()
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_all()
    
    def _load_all(self):
        """从文件加载所有数据"""
        findings_file = self.storage_dir / "findings.json"
        if findings_file.exists():
            with open(findings_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    finding = VulnerabilityFinding(**item)
                    self.add_finding(finding)
        
        # 加载其他数据...
    
    def save_all(self):
        """保存所有数据到文件"""
        findings_file = self.storage_dir / "findings.json"
        data = [f.__dict__ for f in self.findings.values()]
        with open(findings_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 保存其他数据...
```

### 2. 数据库集成（计划中）

未来版本将支持数据库后端：

```python
class DatabaseMemoryStore(SecurityMemoryStore):
    """数据库内存存储"""
    
    def __init__(self, db_url: str):
        super().__init__()
        self.db_url = db_url
        # 初始化数据库连接
```

## 最佳实践

### 1. 数据质量

- 确保数据准确性
- 定期更新 CVE 知识
- 验证漏洞模式
- 清理过期数据

### 2. 性能优化

- 使用批量操作
- 合理设置搜索阈值
- 定期清理旧数据
- 使用索引加速查询

### 3. 安全管理

- 限制敏感数据访问
- 加密存储敏感信息
- 审计数据访问日志
- 定期备份数据

### 4. 数据更新

```python
# 定期更新 CVE 知识
def update_cve_database():
    """从 NVD 更新 CVE 数据"""
    memory = SecurityMemoryStore()
    
    # 从 NVD API 获取最新 CVE
    # ...
    
    # 更新到 Memory
    for cve_data in nvd_data:
        cve = CVEKnowledge(**cve_data)
        memory.add_cve_knowledge(cve)
```

## 故障排查

### 问题 1: 搜索结果为空

检查搜索条件是否过于严格：

```python
# 放宽搜索条件
results = memory.search_findings(
    query="injection",
    similarity_threshold=0.5,  # 降低阈值
    top_k=20  # 增加返回数量
)
```

### 问题 2: 误报率计算不准确

确保有足够的历史数据：

```python
# 检查样本数量
patterns = memory.search_patterns(query="injection")
for pattern in patterns:
    print(f"{pattern.name}: FP rate = {pattern.false_positive_rate:.2%}")
    # 如果样本量小，误报率可能不准确
```

### 问题 3: 内存占用过高

定期清理旧数据：

```python
# 清理 6 个月前的数据
from datetime import datetime, timedelta

cutoff_date = (datetime.now() - timedelta(days=180)).isoformat()

old_findings = [
    f for f in memory.list_findings()
    if f.created_at < cutoff_date and f.status == "closed"
]

for finding in old_findings:
    del memory.findings[finding.id]
```

## 参考资源

- [Memory Schema](../hosforge/memory/schema.py)
- [Memory Store](../hosforge/memory/store.py)
- [Verification Loop](verification-loop.md)
- [Taskflow Engine](taskflow-guide.md)
