# Cursor 适配器配置指南

本文档详细介绍如何配置和使用 HOS-Forge 的 Cursor 适配器，在 Cursor IDE 的聊天界面中集成安全扫描能力。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [安装与配置](#安装与配置)
- [支持的命令](#支持的命令)
- [输入输出格式](#输入输出格式)
- [Cursor Rules 配置](#cursor-rules-配置)
- [常见问题](#常见问题)

## 概述

Cursor 适配器 (`CursorAdapter`) 专门为 Cursor IDE 设计，支持 `@mention` 命令格式。它解析用户在聊天界面中输入的 `@hos` 命令，将其转换为内部格式，并将执行结果格式化为 Markdown，以便在 Cursor 的聊天界面中美观展示。

### 功能特性

- 支持 `@mention` 命令解析
- Markdown 格式输出，完美适配聊天界面
- 状态图标（✅ / ❌）直观展示
- 结构化数据自动转换为列表或键值对

## 前置要求

- Cursor IDE 最新版
- Python 3.10+ (运行 HOS-Forge MCP Server)
- HOS-Forge 已安装

## 安装与配置

### 1. 启动 MCP Server

```bash
python -m hosforge.mcp_server.server
```

### 2. 配置 Cursor Rules

在 Cursor 中，你可以通过 Cursor Rules 来定义 `@hos` 命令的行为。

创建或编辑项目根目录下的 `.cursorrules` 文件：

```
# .cursorrules

# HOS-Forge Security Commands
When the user types @hos, provide the following security scanning capabilities:

- @hos scan: Run a general security scan on the codebase
- @hos nuclei: Run Nuclei vulnerability scanner on a target
- @hos semgrep: Run Semgrep static analysis on code
- @hos skill list: List all available security skills
- @hos skill info: Get detailed information about a specific skill

Always format the results in Markdown with clear headings and bullet points.
```

### 3. 集成 MCP 工具

在 Cursor 的 MCP 配置中添加 HOS-Forge Server：

```json
{
  "mcpServers": {
    "hos-forge": {
      "command": "python",
      "args": ["-m", "hosforge.mcp_server.server"],
      "env": {}
    }
  }
}
```

## 支持的命令

Cursor 适配器支持以下 `@mention` 命令：

| 命令 | 描述 | 处理器 |
|------|------|--------|
| `@hos scan` | 运行代码库安全扫描 | `handle_scan` |
| `@hos nuclei` | 运行 Nuclei 漏洞扫描器 | `handle_nuclei` |
| `@hos semgrep` | 运行 Semgrep 静态分析 | `handle_semgrep` |
| `@hos skill list` | 列出可用安全技能 | `handle_skill_list` |
| `@hos skill info` | 查看特定技能详情 | `handle_skill_info` |

## 输入输出格式

### 输入格式 (format_input)

Cursor 适配器解析 `@mention` 格式的命令：

```python
# 输入示例
command = "@hos nuclei"
args = {"target": "https://example.com"}

# 解析后的内部格式
{
    "command": "nuclei",
    "args": {"target": "https://example.com"}
}
```

解析规则：
- 使用正则 `^@hos\s+(\w+)(?:\s+(\w+))?` 匹配命令
- 提取主命令和子命令
- 组合为内部命令格式

### 输出格式 (format_output)

执行结果被转换为 Markdown 格式，适合在聊天界面展示：

```markdown
✅ **Success**

扫描完成，以下是详细结果：

**Results**:
- **target**: https://example.com
- **total**: 5
- **findings**: [...]
```

### 输出结构

```json
{
  "content": "✅ **Success**\n\n扫描完成...",
  "metadata": {
    "format": "markdown",
    "status": "success",
    "adapter": "cursor"
  }
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `content` | string | Markdown 格式的文本内容 |
| `metadata.format` | string | 格式类型，固定为 "markdown" |
| `metadata.status` | string | 执行状态 |
| `metadata.adapter` | string | 适配器名称 |

## Cursor Rules 配置

### 高级配置示例

你可以通过更详细的 Cursor Rules 来控制 AI 如何调用 HOS-Forge：

```
# .cursorrules

## HOS-Forge Integration

You have access to HOS-Forge security tools via MCP.

### Available Tools
1. `nuclei_scan`: Run Nuclei vulnerability scanner
   - Required: target (URL or IP)
   - Optional: templates, severity

2. `semgrep_scan`: Run Semgrep static analysis
   - Required: path (file or directory)
   - Optional: language, config

3. `github_integration`: GitHub API operations
   - Required: action, repo
   - Optional: title, body, labels, state, limit

### Usage Guidelines
- When user asks to "scan for vulnerabilities", use `nuclei_scan`
- When user asks to "analyze code quality", use `semgrep_scan`
- Always present results in a clear, structured Markdown format
- Highlight critical and high severity findings prominently
```

### 使用示例

在 Cursor 聊天界面中：

```
User: @hos nuclei 扫描一下 https://example.com 的高危漏洞

Cursor: [调用 nuclei_scan skill]
        [格式化结果为 Markdown]
        
✅ **Success**

Nuclei 扫描完成，目标: https://example.com

**Results**:
- **total**: 2
- **findings**: 
  - [CRITICAL] Log4Shell (CVE-2021-44228)
  - [HIGH] SQL Injection in /api/login
```

## 开发扩展

### 使用适配器类

```python
from hosforge.adapters.cursor_adapter import CursorAdapter

adapter = CursorAdapter()

# 格式化输入
input_data = adapter.format_input("@hos nuclei", {"target": "https://example.com"})
print(input_data)
# 输出: {"command": "nuclei", "args": {"target": "https://example.com"}}

# 格式化输出
result = {
    "status": "success",
    "data": {"total": 3, "findings": [...]}
}
output_data = adapter.format_output(result)
print(output_data["content"])
# 输出: Markdown 格式的文本
```

### 自定义 Markdown 模板

可以通过继承 `CursorAdapter` 自定义输出格式：

```python
class CustomCursorAdapter(CursorAdapter):
    def format_output(self, result: dict) -> dict:
        # 自定义 Markdown 生成逻辑
        status = result.get("status", "unknown")
        data = result.get("data", {})
        
        # 添加自定义头部
        content = f"# HOS-Forge 扫描报告\n\n"
        content += f"**状态**: {'✅ 成功' if status == 'success' else '❌ 失败'}\n\n"
        
        # 添加自定义内容
        if "findings" in data:
            content += "## 发现的安全问题\n\n"
            for finding in data["findings"]:
                content += f"- [{finding.get('severity', 'UNKNOWN')}] {finding.get('name', 'Unknown')}\n"
        
        return {
            "content": content,
            "metadata": {"format": "markdown", "status": status, "adapter": "cursor"}
        }
```

## 常见问题

### Q: @hos 命令没有响应？

A: 确保：
1. MCP Server 正在运行
2. Cursor 的 MCP 配置正确指向 HOS-Forge Server
3. `.cursorrules` 文件存在于项目根目录

### Q: 结果展示格式不对？

A: Cursor 适配器默认输出 Markdown。如果格式异常，检查：
1. 返回数据是否包含特殊字符
2. 是否正确设置了 `metadata.format = "markdown"`

### Q: 如何传递多个参数？

A: 在 `@mention` 后直接附加参数，或通过聊天上下文传递：

```
User: @hos semgrep 扫描 ./src 目录，只看 Python 代码

Cursor: [解析参数: path="./src", language="python"]
```

### Q: 支持子命令吗？

A: 支持。例如 `@hos skill list` 会被解析为 `command="skill list"`：

```python
# 输入
"@hos skill list"

# 解析结果
{"command": "skill list", "args": {}}
```

## 相关资源

- [Cursor 官方文档](https://docs.cursor.com/)
- [Cursor Rules 指南](https://docs.cursor.com/context/rules)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [适配器系统文档](README.md)
