# HOS-Forge VSCode 集成示例

本示例展示如何将 HOS-Forge 安全扫描技能（`nuclei_scan`、`semgrep_scan`）集成到 VSCode 扩展中。

## 前置要求

| 依赖 | 安装方式 |
|------|---------|
| VSCode | >= 1.85.0 |
| Node.js | >= 18 |
| HOS-Forge MCP Server | `hos mcp-server --port 8000` |
| Nuclei CLI | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| Semgrep CLI | `pip install semgrep` |

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 编译扩展
npm run compile

# 3. 按 F5 启动扩展开发宿主
```

## 功能说明

### Nuclei 漏洞扫描 (`hos.scan.nuclei`)

通过命令面板执行 **HOS: Run Nuclei Scan**：

1. 输入目标 URL 或 IP（如 `https://example.com`）
2. 选择最低严重级别过滤（info / low / medium / high / critical）
3. 扫描结果输出到 "HOS Nuclei" 输出通道

底层调用：

```
POST http://localhost:8000/tools/nuclei_scan/execute
{
  "arguments": {
    "target": "https://example.com",
    "severity": "high"
  }
}
```

### Semgrep 静态分析 (`hos.scan.semgrep`)

通过命令面板执行 **HOS: Run Semgrep Scan**：

1. 输入文件或目录路径（默认当前工作区根目录）
2. 选择编程语言（可选，不选则自动检测）
3. 扫描结果输出到 "HOS Semgrep" 输出通道

底层调用：

```
POST http://localhost:8000/tools/semgrep_scan/execute
{
  "arguments": {
    "path": "./src",
    "language": "python",
    "config": "auto"
  }
}
```

## 配置项

在 VSCode `settings.json` 中可配置：

```json
{
  "hos.forge.serverUrl": "http://localhost:8000"
}
```

## 项目结构

```
vscode-example/
├── extension.ts     # 扩展主文件，包含 nuclei_scan / semgrep_scan 调用逻辑
├── package.json     # 扩展清单，注册命令和配置项
├── tsconfig.json    # TypeScript 编译配置（需自行创建）
└── README.md        # 本文件
```

## 扩展开发提示

- 使用 `vscode.window.createOutputChannel` 将扫描结果输出到独立面板
- 使用 `vscode.window.showInputBox` 收集用户输入
- 使用 `vscode.window.showQuickPick` 提供选项列表
- 错误信息通过 `vscode.window.showErrorMessage` 展示
