# 适配器系统文档

本章节详细介绍 HOS-Forge 的 IDE 适配器系统架构、配置方法以及如何为不同 IDE 集成 HOS-Forge 的能力。

## 目录

- [系统概述](#系统概述)
- [核心概念](#核心概念)
- [支持的 IDE](#支持的-ide)
- [架构设计](#架构设计)
- [开发指南](#开发指南)
- [最佳实践](#最佳实践)

## 系统概述

IDE 适配器是 HOS-Forge 与各种开发环境之间的桥梁。由于不同的 IDE 和 AI 编程助手（如 VSCode、Cursor、Claude Code）有各自独特的命令格式、交互方式和输出展示要求，适配器系统负责将这些差异抽象化，提供统一的内部接口。

### 设计原则

1. **统一接口**: 所有适配器实现相同的 `IDEAdapter` 基类接口
2. **格式转换**: 负责将 IDE 特定的输入转换为内部命令格式，并将内部结果转换为 IDE 期望的输出格式
3. **命令注册**: 提供向特定 IDE 注册可用命令的机制
4. **松耦合**: 适配器与核心 Skill 系统解耦，便于独立扩展

## 核心概念

### IDEAdapter 基类

所有 IDE 适配器都继承自 `IDEAdapter` 抽象基类，必须实现以下核心接口：

```python
from hosforge.adapters.base_adapter import IDEAdapter, AdapterConfig

class MyAdapter(IDEAdapter):
    def __init__(self, config: AdapterConfig) -> None:
        super().__init__(config)
        self._supported_commands = []

    def format_input(self, command: str, args: dict) -> dict:
        """将 IDE 特定的命令格式转换为内部格式"""
        pass

    def format_output(self, result: dict) -> dict:
        """将内部结果格式转换为 IDE 特定的展示格式"""
        pass

    def register_commands(self) -> list[dict]:
        """返回该适配器支持的命令定义列表"""
        pass
```

### AdapterConfig 配置

使用 `AdapterConfig` 数据类管理适配器配置：

```python
@dataclass
class AdapterConfig:
    adapter_name: str       # 适配器名称
    version: str            # 版本号
    config: dict[str, Any]  # 额外配置字典
```

### 命令流转过程

```
1. 用户在 IDE 中触发命令 (如 @hos scan)
   ↓
2. IDE 将命令传递给 HOS-Forge 适配器
   ↓
3. 适配器调用 format_input() 转换为内部格式
   ↓
4. 内部系统执行对应的 Skill
   ↓
5. 适配器调用 format_output() 转换结果为 IDE 格式
   ↓
6. IDE 展示最终结果给用户
```

## 支持的 IDE

HOS-Forge 目前提供以下三种 IDE 适配器：

| IDE / 环境 | 适配器类 | 命令格式 | 输出格式 | 文档 |
|------------|----------|----------|----------|------|
| **Visual Studio Code** | `VSCodeAdapter` | `hos.xxx.yyy` | JSON (Command API) | [vscode_adapter.md](vscode_adapter.md) |
| **Cursor** | `CursorAdapter` | `@hos xxx` | Markdown | [cursor_adapter.md](cursor_adapter.md) |
| **Claude Code** | `ClaudeCodeAdapter` | `/hos-xxx` | Skill Response | [claude_code_adapter.md](claude_code_adapter.md) |

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                         IDE Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   VSCode     │  │    Cursor    │  │ Claude Code  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Adapter Registry                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • 适配器发现与加载                                      │  │
│  │  • 命令路由                                              │  │
│  │  • 配置管理                                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│VSCodeAdapter │  │CursorAdapter │  │ClaudeAdapter │
│              │  │              │  │              │
│ • format_in  │  │ • format_in  │  │ • format_in  │
│ • format_out │  │ • format_out │  │ • format_out │
│ • register   │  │ • register   │  │ • register   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 适配器注册表 (Adapter Registry)

`AdapterRegistry` 负责管理所有可用的适配器实例：

```python
from hosforge.adapters.adapter_registry import AdapterRegistry

registry = AdapterRegistry()

# 获取适配器
adapter = registry.get("vscode")

# 列出所有适配器
adapters = registry.list_adapters()
```

## 开发指南

如果你需要为 HOS-Forge 添加新的 IDE 适配器支持，请参考以下步骤：

### 1. 创建适配器类

在 `hosforge/adapters/` 目录下创建新文件：

```python
# hosforge/adapters/my_ide_adapter.py
from hosforge.adapters.base_adapter import AdapterConfig, IDEAdapter

class MyIDEAdapter(IDEAdapter):
    def __init__(self, config: AdapterConfig | None = None) -> None:
        if config is None:
            config = AdapterConfig(
                adapter_name="my_ide",
                version="1.0.0",
                config={},
            )
        super().__init__(config)
        self._supported_commands = ["my_ide.command1", "my_ide.command2"]

    def format_input(self, command: str, args: dict) -> dict:
        # 实现输入格式转换
        return {"command": command, "args": args}

    def format_output(self, result: dict) -> dict:
        # 实现输出格式转换
        return {"status": result.get("status"), "data": result.get("data")}

    def register_commands(self) -> list[dict]:
        # 返回命令定义
        return [
            {"command": "my_ide.command1", "title": "My IDE: Command 1"},
            {"command": "my_ide.command2", "title": "My IDE: Command 2"},
        ]
```

### 2. 注册适配器

在适配器注册表中注册新适配器，或在 `__init__.py` 中导出。

### 3. 编写测试

为适配器编写单元测试，确保输入输出转换正确。

## 最佳实践

### 1. 保持命令命名一致性

尽量在不同适配器中保持底层命令名称的一致性，仅改变前端展示格式。

### 2. 提供清晰的错误信息

当命令格式不正确或不支持时，返回清晰的错误提示：

```python
def format_input(self, command: str, args: dict) -> dict:
    if command not in self._supported_commands:
        raise ValueError(
            f"Unsupported command '{command}'. "
            f"Supported: {self._supported_commands}"
        )
```

### 3. 输出格式适配

根据 IDE 的特性选择合适的输出格式：
- **VSCode**: 结构化 JSON，适合扩展 UI 展示
- **Cursor**: Markdown，适合聊天界面阅读
- **Claude Code**: Skill 响应格式，包含 tool_results

### 4. 配置模板

为适配器提供配置模板文件（如 `templates/` 目录下的 JSON），方便用户快速集成。

## 常见问题

### Q: 如何查看当前支持哪些适配器？

A: 可以通过代码查询：

```python
from hosforge.adapters.adapter_registry import AdapterRegistry

registry = AdapterRegistry()
for adapter in registry.list_adapters():
    print(f"- {adapter.name} (v{adapter._config.version})")
```

### Q: 适配器可以动态加载吗？

A: 是的，可以通过 `AdapterRegistry` 动态注册和获取适配器实例。

### Q: 如何调试适配器？

A: 可以在 `format_input` 和 `format_output` 方法中添加日志，打印转换前后的数据：

```python
import logging
logger = logging.getLogger(__name__)

def format_input(self, command: str, args: dict) -> dict:
    logger.debug(f"Raw input: command={command}, args={args}")
    result = ... # 转换逻辑
    logger.debug(f"Formatted input: {result}")
    return result
```

## 相关资源

- [VSCode 适配器指南](vscode_adapter.md)
- [Cursor 适配器指南](cursor_adapter.md)
- [Claude Code 适配器指南](claude_code_adapter.md)
- [适配器基类源码](../../hosforge/adapters/base_adapter.py)
