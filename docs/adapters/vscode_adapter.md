# VSCode 适配器配置指南

本文档详细介绍如何配置和使用 HOS-Forge 的 VSCode 适配器，将安全扫描能力集成到 Visual Studio Code 中。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [安装与配置](#安装与配置)
- [支持的命令](#支持的命令)
- [输入输出格式](#输入输出格式)
- [开发扩展](#开发扩展)
- [常见问题](#常见问题)

## 概述

VSCode 适配器 (`VSCodeAdapter`) 将 HOS-Forge 的功能映射为 VSCode 命令（Commands），通过 VSCode 的 `executeCommand` API 进行调用。它负责将 VSCode 的命令调用格式转换为 HOS-Forge 内部格式，并将执行结果转换为 VSCode 扩展友好的 JSON 结构。

### 功能特性

- 支持 VSCode 命令面板调用
- 结构化 JSON 输出，便于扩展 UI 展示
- 支持后续操作（actions）提示
- 完整的命令注册机制

## 前置要求

- Visual Studio Code 1.60+
- Python 3.10+ (运行 HOS-Forge MCP Server)
- HOS-Forge 已安装并配置好 MCP Server

## 安装与配置

### 1. 启动 MCP Server

VSCode 扩展需要通过 MCP Server 与 HOS-Forge 通信：

```bash
# 启动 MCP Server
python -m hosforge.mcp_server.server
# 或
uvicorn hosforge.mcp_server.server:app --host 0.0.0.0 --port 8000
```

### 2. 配置 VSCode 扩展

在你的 VSCode 扩展的 `package.json` 中注册 HOS-Forge 命令：

```json
{
  "name": "your-vscode-extension",
  "version": "1.0.0",
  "engines": {
    "vscode": "^1.60.0"
  },
  "activationEvents": [],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "hos.skill.run",
        "title": "HOS: Run Skill",
        "category": "HOS"
      },
      {
        "command": "hos.skill.list",
        "title": "HOS: List Skills",
        "category": "HOS"
      },
      {
        "command": "hos.skill.info",
        "title": "HOS: Skill Info",
        "category": "HOS"
      },
      {
        "command": "hos.scan.nuclei",
        "title": "HOS: Run Nuclei Scan",
        "category": "HOS"
      },
      {
        "command": "hos.scan.semgrep",
        "title": "HOS: Run Semgrep Scan",
        "category": "HOS"
      }
    ]
  }
}
```

### 3. 实现命令处理

在扩展的 `extension.ts` (或 `extension.js`) 中注册命令处理器：

```typescript
import * as vscode from 'vscode';
import axios from 'axios';

const MCP_SERVER_URL = 'http://localhost:8000';

export function activate(context: vscode.ExtensionContext) {
    // 注册 Nuclei 扫描命令
    let nucleiCmd = vscode.commands.registerCommand('hos.scan.nuclei', async () => {
        const target = await vscode.window.showInputBox({
            prompt: '请输入扫描目标 URL 或 IP',
            placeHolder: 'https://example.com'
        });

        if (!target) return;

        try {
            const response = await axios.post(
                `${MCP_SERVER_URL}/tools/nuclei_scan/execute`,
                { arguments: { target } }
            );

            // 处理并展示结果
            vscode.window.showInformationMessage(
                `扫描完成，发现 ${response.data.data?.total || 0} 个问题`
            );
            
            // 可以在 Output Channel 或 Webview 中展示详细结果
        } catch (error) {
            vscode.window.showErrorMessage(`扫描失败: ${error.message}`);
        }
    });

    context.subscriptions.push(nucleiCmd);
}
```

## 支持的命令

VSCode 适配器支持以下命令：

| 命令 ID | 标题 | 描述 |
|---------|------|------|
| `hos.skill.run` | HOS: Run Skill | 执行指定的 Skill |
| `hos.skill.list` | HOS: List Skills | 列出所有可用的 Skills |
| `hos.skill.info` | HOS: Skill Info | 查看指定 Skill 的详细信息 |
| `hos.scan.nuclei` | HOS: Run Nuclei Scan | 执行 Nuclei 漏洞扫描 |
| `hos.scan.semgrep` | HOS: Run Semgrep Scan | 执行 Semgrep 代码分析 |

## 输入输出格式

### 输入格式 (format_input)

VSCode 适配器将命令转换为以下内部格式：

```json
{
  "command": "hos.scan.nuclei",
  "args": {
    "target": "https://example.com",
    "severity": "high"
  }
}
```

### 输出格式 (format_output)

执行结果被转换为以下 VSCode 友好的格式：

```json
{
  "status": "success",
  "message": "扫描完成",
  "data": {
    "findings": [...],
    "total": 5,
    "target": "https://example.com"
  },
  "actions": [
    {
      "title": "查看详细报告",
      "command": "hos.report.show",
      "arguments": ["report_id_123"]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `status` | string | 执行状态 (`success`, `error`) |
| `message` | string | 状态描述信息 |
| `data` | any | 主要结果数据 |
| `actions` | array | 可选的后续操作列表 |

## 开发扩展

### 使用适配器类

如果你需要在代码中直接使用 VSCode 适配器：

```python
from hosforge.adapters.vscode_adapter import VSCodeAdapter
from hosforge.adapters.base_adapter import AdapterConfig

# 创建适配器实例
config = AdapterConfig(
    adapter_name="vscode",
    version="1.0.0",
    config={}
)
adapter = VSCodeAdapter(config)

# 格式化输入
input_data = adapter.format_input("hos.scan.nuclei", {"target": "https://example.com"})
print(input_data)
# 输出: {"command": "hos.scan.nuclei", "args": {"target": "https://example.com"}}

# 格式化输出
result = {
    "status": "success",
    "message": "Done",
    "data": {"total": 0}
}
output_data = adapter.format_output(result)
print(output_data)

# 获取命令注册信息
commands = adapter.register_commands()
for cmd in commands:
    print(f"{cmd['command']}: {cmd['title']}")
```

### 自定义命令映射

可以通过继承 `VSCodeAdapter` 添加自定义命令：

```python
class CustomVSCodeAdapter(VSCodeAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        # 添加自定义命令
        self._supported_commands.append("hos.custom.command")
        self._COMMAND_TITLES["hos.custom.command"] = "HOS: Custom Command"
```

## 常见问题

### Q: 命令面板中看不到 HOS 命令？

A: 确保：
1. 扩展已正确安装并激活
2. `package.json` 中的 `contributes.commands` 配置正确
3. 重启 VSCode 使配置生效

### Q: 如何传递复杂参数给 Skill？

A: 通过 `args` 对象传递，支持嵌套结构：

```typescript
vscode.commands.executeCommand('hos.skill.run', {
    skill_name: 'nuclei_scan',
    args: {
        target: 'https://example.com',
        templates: ['cves/2021/CVE-2021-44228.yaml'],
        severity: 'high'
    }
});
```

### Q: 如何处理长时间运行的扫描？

A: 建议使用 VSCode 的进度通知：

```typescript
await vscode.window.withProgress({
    location: vscode.ProgressLocation.Notification,
    title: "正在执行安全扫描...",
    cancellable: true
}, async (progress, token) => {
    const response = await axios.post(`${MCP_SERVER_URL}/tools/nuclei_scan/execute`, {
        arguments: { target }
    });
    return response.data;
});
```

### Q: 如何在结果中展示富文本？

A: 可以使用 VSCode 的 Webview API 创建自定义面板展示 HTML 结果，或使用 Markdown 字符串在 Output Channel 中展示。

## 相关资源

- [VSCode 扩展开发文档](https://code.visualstudio.com/api)
- [VSCode 命令 API](https://code.visualstudio.com/api/references/commands)
- [适配器系统文档](README.md)
- [MCP Server 文档](../mcp_server/README.md)
