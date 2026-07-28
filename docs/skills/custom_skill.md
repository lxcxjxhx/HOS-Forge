# 自定义 Skill 开发指南

本指南将帮助你开发自定义 Skill，扩展 HOS-Forge 的功能。

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [Skill 结构](#skill-结构)
- [参数定义](#参数定义)
- [实现 execute 方法](#实现-execute-方法)
- [错误处理](#错误处理)
- [注册 Skill](#注册-skill)
- [测试 Skill](#测试-skill)
- [最佳实践](#最佳实践)
- [完整示例](#完整示例)

## 概述

HOS-Forge 的 Skill 系统采用插件化架构，允许开发者轻松添加新的功能模块。每个 Skill 都是一个独立的 Python 类，继承自 `Skill` 基类并实现统一的接口。

### 开发流程

```
1. 创建 Skill 类 → 2. 定义参数 → 3. 实现逻辑 → 4. 注册 Skill → 5. 测试验证
```

## 快速开始

### 最小可运行示例

```python
from hosforge.skills.base_skill import Skill

class HelloSkill(Skill):
    def __init__(self) -> None:
        super().__init__(
            name="hello",
            description="一个简单的问候 Skill",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要问候的名字",
                    },
                },
                "required": ["name"],
            },
        )

    def execute(self, **kwargs) -> dict:
        name = kwargs["name"]
        return {
            "success": True,
            "data": {"message": f"Hello, {name}!"},
        }
```

### 使用 Skill

```bash
# CLI 使用
hos skill run hello name=World

# Python API
from hosforge.skills.registry import SkillRegistry

registry = SkillRegistry()
registry.register(HelloSkill())
result = registry.execute_skill("hello", name="World")
print(result.data)  # {"message": "Hello, World!"}
```

## Skill 结构

### 目录结构

建议将自定义 Skill 放在以下位置之一：

```
hosforge/
├── skills/
│   ├── security/          # 安全相关 skills
│   │   ├── nuclei_skill.py
│   │   ├── semgrep_skill.py
│   │   └── github_skill.py
│   ├── custom/            # 自定义 skills
│   │   └── my_skill.py
│   └── base_skill.py
```

### 文件命名规范

- 使用小写字母和下划线：`my_custom_skill.py`
- 类名使用 PascalCase：`MyCustomSkill`
- 文件名应与类名对应：`my_custom_skill.py` → `MyCustomSkill`

## 参数定义

### 参数 Schema

使用 JSON Schema 格式定义参数：

```python
parameters={
    "type": "object",
    "properties": {
        "param_name": {
            "type": "string",      # 参数类型
            "description": "参数描述",
            "default": "value",    # 默认值（可选）
            "enum": ["a", "b"],    # 可选值（可选）
        },
    },
    "required": ["param_name"],    # 必填参数列表
}
```

### 支持的类型

| 类型 | Python 类型 | 示例 |
|------|------------|------|
| `string` | `str` | `"hello"` |
| `integer` | `int` | `42` |
| `number` | `int` 或 `float` | `3.14` |
| `boolean` | `bool` | `true` |
| `array` | `list` | `[1, 2, 3]` |
| `object` | `dict` | `{"key": "value"}` |

### 参数验证

基类提供自动参数验证：

```python
def validate_input(self, **kwargs) -> bool:
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

## 实现 execute 方法

### 方法签名

```python
def execute(self, **kwargs) -> dict:
    """执行 Skill 的核心逻辑。
    
    Args:
        **kwargs: 传递给 Skill 的参数
        
    Returns:
        包含执行结果的字典
        
    Raises:
        Exception: 当执行失败时
    """
    pass
```

### 返回值格式

推荐返回以下格式：

```python
return {
    "success": True,           # 执行是否成功
    "data": result_data,       # 主要结果数据
    "error": None,             # 错误信息（如果有）
    "metadata": {              # 额外元数据（可选）
        "duration": 10.5,
        "timestamp": "2024-01-15T10:30:00Z",
    },
}
```

### 调用外部工具

使用 `subprocess` 调用外部命令行工具：

```python
import subprocess

def execute(self, **kwargs) -> dict:
    target = kwargs["target"]
    cmd = ["tool-name", "-target", target, "-json"]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        
        if proc.returncode != 0:
            return {
                "success": False,
                "error": f"Tool failed: {proc.stderr}",
            }
        
        # 解析输出
        result = json.loads(proc.stdout)
        return {
            "success": True,
            "data": result,
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Tool not found in PATH",
        }
```

### 调用 API

使用 `requests` 或 `httpx` 调用外部 API：

```python
import httpx

def execute(self, **kwargs) -> dict:
    url = kwargs["url"]
    
    try:
        response = httpx.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "data": data,
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": str(e),
        }
```

## 错误处理

### 异常类型

根据错误类型选择合适的异常：

| 异常类型 | 使用场景 |
|---------|---------|
| `ValueError` | 参数无效或缺失 |
| `FileNotFoundError` | 外部工具未找到 |
| `subprocess.TimeoutExpired` | 命令执行超时 |
| `subprocess.CalledProcessError` | 命令执行失败 |
| `RuntimeError` | 运行时错误 |

### 错误处理示例

```python
def execute(self, **kwargs) -> dict:
    try:
        # 参数验证
        if "required_param" not in kwargs:
            raise ValueError("Missing required parameter: required_param")
        
        # 执行逻辑
        result = do_something()
        
        return {
            "success": True,
            "data": result,
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid input: {e}",
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"Tool not found: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
        }
```

## 注册 Skill

### 方式一：手动注册

```python
from hosforge.skills.registry import SkillRegistry
from hosforge.skills.custom.my_skill import MyCustomSkill

registry = SkillRegistry()
registry.register(MyCustomSkill())
```

### 方式二：自动注册

在 `hosforge/skills/__init__.py` 中添加：

```python
from hosforge.skills.custom.my_skill import MyCustomSkill

__all__ = [
    "MyCustomSkill",
    # ... 其他 skills
]
```

### 方式三：使用装饰器（高级）

创建自动注册机制：

```python
# hosforge/skills/auto_register.py
_skill_registry = []

def register_skill(cls):
    """装饰器：自动注册 Skill"""
    _skill_registry.append(cls)
    return cls

# 使用
@register_skill
class MyCustomSkill(Skill):
    # ...
    pass
```

## 测试 Skill

### 单元测试

```python
# tests/unit/test_my_skill.py
import pytest
from hosforge.skills.custom.my_skill import MyCustomSkill

class TestMyCustomSkill:
    def test_execute_success(self):
        skill = MyCustomSkill()
        result = skill.execute(param1="test")
        
        assert result["success"] is True
        assert "data" in result
    
    def test_execute_missing_param(self):
        skill = MyCustomSkill()
        
        with pytest.raises(ValueError):
            skill.execute()  # 缺少必填参数
    
    def test_validate_input(self):
        skill = MyCustomSkill()
        
        # 有效输入
        assert skill.validate_input(param1="test") is True
        
        # 无效输入
        assert skill.validate_input() is False
```

### 集成测试

```python
def test_skill_integration():
    """测试 Skill 在 Registry 中的完整流程"""
    from hosforge.skills.registry import SkillRegistry
    
    registry = SkillRegistry()
    registry.register(MyCustomSkill())
    
    # 列出 skills
    skills = registry.list_skills()
    assert any(s.name == "my_custom" for s in skills)
    
    # 执行 skill
    result = registry.execute_skill("my_custom", param1="test")
    assert result.success is True
```

## 最佳实践

### 1. 清晰的文档

为类和每个公共方法添加 docstring：

```python
class MyCustomSkill(Skill):
    """Skill 的简短描述。
    
    详细说明这个 Skill 的功能、用途和使用场景。
    
    Examples:
        >>> skill = MyCustomSkill()
        >>> result = skill.execute(param1="value")
        >>> print(result)
    """

    def execute(self, **kwargs) -> dict:
        """执行 Skill 的核心逻辑。
        
        Args:
            **kwargs: 参数说明
            
        Returns:
            返回值说明
            
        Raises:
            ValueError: 何时抛出此异常
        """
```

### 2. 类型注解

使用类型注解提高代码可读性：

```python
from typing import Any, Dict, List, Optional

def execute(self, **kwargs) -> Dict[str, Any]:
    target: str = kwargs["target"]
    timeout: int = kwargs.get("timeout", 600)
    items: Optional[List[str]] = kwargs.get("items")
```

### 3. 合理的默认值

为可选参数提供合理的默认值：

```python
timeout: int = kwargs.get("timeout", 600)  # 10 分钟
limit: int = kwargs.get("limit", 30)
format: str = kwargs.get("format", "json")
```

### 4. 日志记录

使用日志记录关键操作：

```python
import logging

logger = logging.getLogger(__name__)

def execute(self, **kwargs) -> dict:
    logger.info(f"Executing {self.name} with params: {kwargs}")
    
    try:
        result = do_something()
        logger.info(f"Execution successful: {result}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return {"success": False, "error": str(e)}
```

### 5. 配置管理

使用环境变量或配置文件管理敏感信息：

```python
import os

def execute(self, **kwargs) -> dict:
    api_key = os.getenv("MY_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "MY_API_KEY environment variable not set",
        }
```

## 完整示例

### 示例：Docker 扫描 Skill

```python
"""Docker 镜像漏洞扫描 Skill。"""

import json
import subprocess
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill


class DockerScanSkill(Skill):
    """使用 Trivy 扫描 Docker 镜像漏洞。
    
    通过调用 trivy 命令行工具对 Docker 镜像执行漏洞扫描，
    返回结构化的扫描结果。
    """

    def __init__(self) -> None:
        super().__init__(
            name="docker_scan",
            description="使用 Trivy 扫描 Docker 镜像漏洞",
            parameters={
                "type": "object",
                "properties": {
                    "image": {
                        "type": "string",
                        "description": "Docker 镜像名称（如 nginx:latest）",
                    },
                    "severity": {
                        "type": "string",
                        "description": "严重级别过滤 (UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)",
                        "enum": ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    },
                    "ignore_unfixed": {
                        "type": "boolean",
                        "description": "是否忽略未修复的漏洞",
                        "default": False,
                    },
                },
                "required": ["image"],
            },
        )

    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行 Docker 镜像扫描。
        
        Args:
            **kwargs: 包含 image, severity, ignore_unfixed 的参数
            
        Returns:
            包含漏洞列表和统计信息的字典
            
        Raises:
            FileNotFoundError: trivy 命令不可用
            subprocess.TimeoutExpired: 扫描超时
        """
        image: str = kwargs["image"]
        severity: Optional[str] = kwargs.get("severity")
        ignore_unfixed: bool = kwargs.get("ignore_unfixed", False)

        # 构建命令
        cmd: List[str] = [
            "trivy", "image",
            "--format", "json",
            "--quiet",
        ]

        if severity:
            cmd.extend(["--severity", severity])

        if ignore_unfixed:
            cmd.append("--ignore-unfixed")

        cmd.append(image)

        # 执行命令
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "trivy 命令未找到，请确认已安装 trivy 并加入 PATH"
            ) from exc

        if proc.returncode not in (0, 1):
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, proc.stdout, proc.stderr
            )

        # 解析结果
        try:
            output = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析 trivy JSON 输出: {exc}") from exc

        vulnerabilities = output.get("Results", [])
        
        # 统计信息
        severity_count = {
            "UNKNOWN": 0,
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }
        
        for result in vulnerabilities:
            for vuln in result.get("Vulnerabilities", []):
                sev = vuln.get("Severity", "UNKNOWN")
                severity_count[sev] = severity_count.get(sev, 0) + 1

        return {
            "success": True,
            "data": {
                "image": image,
                "vulnerabilities": vulnerabilities,
                "total": sum(severity_count.values()),
                "severity_count": severity_count,
            },
        }
```

### 使用示例

```bash
# 扫描镜像
hos skill run docker_scan image=nginx:latest

# 只扫描高危漏洞
hos skill run docker_scan image=nginx:latest severity=HIGH

# 忽略未修复的漏洞
hos skill run docker_scan image=nginx:latest ignore_unfixed=true
```

## 相关资源

- [Skill 系统文档](README.md)
- [内置 Skills 实现](../../hosforge/skills/security/)
- [Skill 基类源码](../../hosforge/skills/base_skill.py)
- [Registry 源码](../../hosforge/skills/registry.py)
