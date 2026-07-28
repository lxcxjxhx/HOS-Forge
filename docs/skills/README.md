# Skill 系统文档

本章节详细介绍 HOS-Forge 的 Skill 系统架构、内置 Skills 以及开发自定义 Skill 的方法。

## 目录

- [系统概述](#系统概述)
- [核心概念](#核心概念)
- [内置 Skills](#内置-skills)
- [开发指南](#开发指南)
- [最佳实践](#最佳实践)

## 系统概述

Skill 系统是 HOS-Forge 的核心组件，负责封装各类安全工具和自动化任务。每个 Skill 都是一个独立的、可复用的功能单元，通过统一的接口与上层应用交互。

### 设计原则

1. **模块化**: 每个 Skill 独立封装一个特定功能，职责单一
2. **可扩展**: 通过继承基类轻松添加新 Skill
3. **类型安全**: 完整的类型注解和参数验证
4. **动态加载**: 支持运行时自动发现和注册 Skill
5. **统一接口**: 所有 Skill 遵循相同的执行和结果格式

### 架构组件

```
┌─────────────────────────────────────────────────────────┐
│                    Skill Registry                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • 注册表管理                                      │  │
│  │  • 动态加载                                        │  │
│  │  • 生命周期管理                                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Skill Base Class                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • 统一接口定义                                    │  │
│  │  • 参数验证                                        │  │
│  │  • 结果格式化                                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Concrete Skills                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Nuclei  │  │ Semgrep  │  │  GitHub  │  ...        │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

## 核心概念

### Skill 基类

所有 Skill 都继承自 `Skill` 抽象基类，必须实现以下接口：

```python
from hosforge.skills.base_skill import Skill, SkillResult

class MySkill(Skill):
    def __init__(self) -> None:
        super().__init__(
            name="my_skill",
            description="Skill 描述",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "参数描述"},
                },
                "required": ["param1"],
            },
        )

    def execute(self, **kwargs) -> dict:
        # 实现核心逻辑
        pass
```

### SkillResult 数据结构

所有 Skill 执行后返回统一的结果格式：

```python
@dataclass
class SkillResult:
    success: bool           # 执行是否成功
    data: Any = None        # 返回的数据
    error: Optional[str] = None  # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
```

### 参数验证

Skill 基类提供内置的参数验证功能：

```python
def validate_input(self, **kwargs) -> bool:
    """验证输入参数是否符合 schema 定义"""
    # 检查必填参数
    required = self.parameters.get("required", [])
    for param in required:
        if param not in kwargs:
            return False
    
    # 检查参数类型
    properties = self.parameters.get("properties", {})
    for key, value in kwargs.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type:
                if not self._check_type(value, expected_type):
                    return False
    
    return True
```

### Skill Registry

SkillRegistry 负责管理所有已注册的 Skills：

```python
from hosforge.skills.registry import SkillRegistry

# 创建注册表
registry = SkillRegistry()

# 注册 Skill
registry.register(MySkill())

# 获取 Skill
skill = registry.get("my_skill")

# 列出所有 Skills
skills = registry.list_skills()

# 执行 Skill
result = registry.execute_skill("my_skill", param1="value")
```

## 内置 Skills

HOS-Forge 提供以下内置 Skills：

### 安全扫描类

| Skill | 描述 | 文档 |
|-------|------|------|
| **NucleiScanSkill** | 使用 Nuclei 进行漏洞扫描 | [nuclei_skill.md](nuclei_skill.md) |
| **SemgrepScanSkill** | 使用 Semgrep 进行静态代码分析 | [semgrep_skill.md](semgrep_skill.md) |
| **TrivyScanSkill** | 使用 Trivy 进行漏洞扫描 | [trivy_skill.md](trivy_skill.md) |
| **CodeQLScanSkill** | 使用 CodeQL 进行安全分析 | [codeql_skill.md](codeql_skill.md) |
| **HOSLSScanSkill** | 使用 HOS-LS 引擎进行安全扫描 | [hosls_skill.md](hosls_skill.md) |

### 集成类

| Skill | 描述 | 文档 |
|-------|------|------|
| **GitHubIntegrationSkill** | GitHub API 操作集成 | [github_skill.md](github_skill.md) |

## 开发指南

开发自定义 Skill 的详细步骤和最佳实践，请参考：

- [自定义 Skill 开发指南](custom_skill.md)

## 最佳实践

### 1. 参数设计

- 使用清晰的参数名称
- 提供详细的参数描述
- 明确标识必填和可选参数
- 使用合适的类型约束

```python
parameters={
    "type": "object",
    "properties": {
        "target": {
            "type": "string",
            "description": "扫描目标 URL 或 IP 地址",
        },
        "timeout": {
            "type": "integer",
            "description": "超时时间（秒），默认 600",
            "default": 600,
        },
    },
    "required": ["target"],
}
```

### 2. 错误处理

- 捕获并转换外部工具的错误
- 提供有意义的错误信息
- 使用适当的异常类型

```python
try:
    result = subprocess.run(cmd, ...)
except FileNotFoundError as exc:
    raise FileNotFoundError(
        "nuclei 命令未找到，请确认已安装 nuclei 并加入 PATH"
    ) from exc
```

### 3. 结果格式化

- 返回结构化的数据
- 包含必要的元信息
- 保持结果的一致性

```python
return {
    "findings": results,      # 主要结果数据
    "total": len(results),    # 统计信息
    "target": target,         # 上下文信息
}
```

### 4. 文档编写

- 为类和方法添加 docstring
- 说明参数、返回值和异常
- 提供使用示例

```python
class MySkill(Skill):
    """Skill 的简短描述。
    
    详细说明这个 Skill 的功能和用途。
    """

    def execute(self, **kwargs) -> dict:
        """执行 Skill 的核心逻辑。
        
        Args:
            **kwargs: 参数说明
            
        Returns:
            返回值说明
            
        Raises:
            ExceptionType: 异常说明
        """
```

### 5. 测试

- 编写单元测试
- 覆盖正常和异常场景
- 使用 mock 避免外部依赖

```python
def test_my_skill():
    skill = MySkill()
    result = skill.execute(param1="test")
    assert result["success"] is True
```

## 常见问题

### Q: 如何调试 Skill？

A: 可以在 `execute` 方法中添加日志，或使用 Python 的 `logging` 模块：

```python
import logging

logger = logging.getLogger(__name__)

def execute(self, **kwargs):
    logger.debug(f"Executing with params: {kwargs}")
    # ...
```

### Q: 如何处理长时间运行的任务？

A: 设置合理的超时时间，并考虑异步执行：

```python
proc = subprocess.run(
    cmd,
    timeout=600,  # 10 分钟超时
    capture_output=True,
)
```

### Q: 如何访问外部配置？

A: 可以通过环境变量或配置文件：

```python
import os

api_key = os.getenv("MY_API_KEY")
```

## 相关资源

- [Skill 基类源码](../../hosforge/skills/base_skill.py)
- [Registry 源码](../../hosforge/skills/registry.py)
- [内置 Skills 实现](../../hosforge/skills/security/)
