# Claude Code 适配器配置指南

本文档详细介绍如何配置和使用 HOS-Forge 的 Claude Code 适配器，将安全扫描能力作为 Skill 集成到 Claude Code 环境中。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [安装与配置](#安装与配置)
- [支持的命令](#支持的命令)
- [输入输出格式](#输入输出格式)
- [Skill 定义模板](#skill-定义模板)
- [常见问题](#常见问题)

## 概述

Claude Code 适配器 (`ClaudeCodeAdapter`) 专门为 Claude Code 环境设计，支持 `/hos-xxx` 斜杠命令格式。它将斜杠命令映射为内部命令名称，并将执行结果转换为 Claude Code 兼容的 Skill 响应格式，包含人类可读的摘要和工具调用结果。

### 功能特性

- 支持 `/hos-xxx` 斜杠命令
- 命令映射机制，简化内部调用
- 输出包含 `response` 摘要和 `tool_results`
- 从模板文件加载 Skill 定义

## 前置要求

- Claude Code 访问权限
- Python 3.10+ (运行 HOS-Forge MCP Server)
- HOS-Forge 已安装

## 安装与配置

### 1. 启动 MCP Server

```bash
python -m hosforge.mcp_server.server
```

### 2. 配置 Claude Code Skills

在 Claude Code 的配置中添加 HOS-Forge Skills。可以通过适配器自动生成 Skill 定义：

```python
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter

adapter = ClaudeCodeAdapter()
skills = adapter.register_commands()

# 将 skills 列表添加到 Claude Code 的配置中
import json
print(json.dumps(skills, indent=2))
```

### 3. 手动配置

在 Claude Code 的 skill 配置文件中添加：

```json
{
  "skills": [
    {
      "name": "hos-scan",
      "description": "Run security scan using HOS-Forge",
      "parameters": {
        "type": "object",
        "properties": {
          "target": {"type": "string", "description": "Scan target"}
        },
        "required": ["target"]
      },
      "handler": "hos.scan"
    },
    {
      "name": "hos-nuclei",
      "description": "Run Nuclei vulnerability scanner",
      "parameters": {
        "type": "object",
        "properties": {
          "target": {"type": "string", "description": "Scan target URL or IP"},
          "severity": {"type": "string", "description": "Filter by severity"}
        },
        "required": ["target"]
      },
      "handler": "hos.nuclei"
    }
  ]
}
```

## 支持的命令

Claude Code 适配器支持以下斜杠命令：

| 斜杠命令 | 内部命令名 | 描述 |
|----------|------------|------|
| `/hos-scan` | `scan` | 运行安全扫描 |
| `/hos-nuclei` | `nuclei` | 运行 Nuclei 漏洞扫描 |
| `/hos-semgrep` | `semgrep` | 运行 Semgrep 静态分析 |
| `/hos-skill-list` | `skill_list` | 列出可用 Skills |
| `/hos-skill-info` | `skill_info` | 查看 Skill 详情 |

### 命令映射机制

适配器内部维护一个命令映射表：

```python
_COMMAND_MAP = {
    "/hos-scan": "scan",
    "/hos-nuclei": "nuclei",
    "/hos-semgrep": "semgrep",
    "/hos-skill-list": "skill_list",
    "/hos-skill-info": "skill_info",
}
```

## 输入输出格式

### 输入格式 (format_input)

将斜杠命令转换为内部命令格式：

```python
# 输入
command = "/hos-nuclei"
args = {"target": "https://example.com"}

# 转换后
{
    "command": "nuclei",
    "args": {"target": "https://example.com"}
}
```

### 输出格式 (format_output)

执行结果被转换为 Claude Code Skill 响应格式：

```json
{
  "response": "扫描完成，发现 5 个安全问题",
  "tool_results": [
    {
      "tool": "nuclei_scan",
      "status": "success",
      "data": {...}
    }
  ],
  "data": {
    "findings": [...],
    "total": 5
  }
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `response` | string | 人类可读的结果摘要 |
| `tool_results` | array | 工具调用结果列表 |
| `data` | any | 原始结果数据 |

## Skill 定义模板

Claude Code 适配器从 `templates/claude_skills.json` 文件加载 Skill 定义。

### 模板文件结构

```json
[
  {
    "name": "hos-scan",
    "description": "Run security scan on the codebase",
    "parameters": {
      "type": "object",
      "properties": {
        "target": {
          "type": "string",
          "description": "The target to scan"
        }
      },
      "required": ["target"]
    },
    "handler": "handle_scan"
  },
  {
    "name": "hos-nuclei",
    "description": "Run Nuclei vulnerability scanner",
    "parameters": {
      "type": "object",
      "properties": {
        "target": {
          "type": "string",
          "description": "Target URL or IP"
        },
        "severity": {
          "type": "string",
          "description": "Severity filter (info, low, medium, high, critical)"
        }
      },
      "required": ["target"]
    },
    "handler": "handle_nuclei"
  }
]
```

### 自定义 Skill 定义

可以通过修改 `templates/claude_skills.json` 文件来添加或修改 Skill 定义：

```bash
# 编辑模板文件
vim hosforge/adapters/templates/claude_skills.json
```

或者通过代码动态生成：

```python
import json

custom_skills = [
    {
        "name": "hos-custom",
        "description": "Custom security scan",
        "parameters": {...},
        "handler": "handle_custom"
    }
]

# 保存到模板文件
with open("hosforge/adapters/templates/claude_skills.json", "w") as f:
    json.dump(custom_skills, f, indent=2)
```

## 开发扩展

### 使用适配器类

```python
from hosforge.adapters.claude_code_adapter import ClaudeCodeAdapter

adapter = ClaudeCodeAdapter()

# 格式化输入
input_data = adapter.format_input("/hos-nuclei", {"target": "https://example.com"})
print(input_data)
# 输出: {"command": "nuclei", "args": {"target": "https://example.com"}}

# 格式化输出
result = {
    "status": "success",
    "message": "扫描完成",
    "data": {"total": 3}
}
output_data = adapter.format_output(result)
print(output_data)
# 输出: {"response": "扫描完成", "tool_results": [], "data": {"total": 3}}
```

### 自定义响应格式

可以通过继承 `ClaudeCodeAdapter` 自定义响应生成逻辑：

```python
class CustomClaudeAdapter(ClaudeCodeAdapter):
    def format_output(self, result: dict) -> dict:
        status = result.get("status", "unknown")
        message = result.get("message", "")
        data = result.get("data", {})
        
        # 生成更详细的摘要
        if status == "success" and "total" in data:
            response = f"✅ 扫描成功！共发现 {data['total']} 个安全问题。"
            if data["total"] > 0:
                response += " 建议查看详细报告以获取详细信息。"
        else:
            response = f"[{status}] {message}"
        
        return {
            "response": response,
            "tool_results": result.get("tool_results", []),
            "data": data
        }
```

## 常见问题

### Q: 斜杠命令没有反应？

A: 确保：
1. Skill 定义已正确加载到 Claude Code 配置中
2. MCP Server 正在运行
3. 命令拼写正确（如 `/hos-nuclei` 而不是 `/hos_nuclei`）

### Q: 如何添加新的斜杠命令？

A: 需要修改两个地方：
1. 在 `ClaudeCodeAdapter` 类中添加命令映射：
   ```python
   _COMMAND_MAP["/hos-new"] = "new_command"
   self._supported_commands.append("/hos-new")
   ```
2. 在 `templates/claude_skills.json` 中添加对应的 Skill 定义。

### Q: tool_results 是什么？

A: `tool_results` 是 Claude Code 用于追踪工具调用历史的字段。当 Skill 执行过程中调用了外部工具（如 Nuclei、Semgrep），调用结果会被记录在这里。

### Q: 如何传递复杂参数？

A: 通过 `args` 字典传递，支持所有 JSON 兼容的数据类型：

```python
adapter.format_input("/hos-nuclei", {
    "target": "https://example.com",
    "templates": ["cves/2021/CVE-2021-44228.yaml"],
    "severity": "high"
})
```

### Q: 响应摘要 (response) 可以自定义吗？

A: 可以。通过继承 `ClaudeCodeAdapter` 并重写 `format_output` 方法，你可以根据执行结果生成任意格式的摘要文本。

## 相关资源

- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [Skill 系统文档](../skills/README.md)
- [适配器系统文档](README.md)
- [MCP 协议规范](https://modelcontextprotocol.io/)
