# HOS-Forge Cursor 集成示例

本示例展示如何在 Cursor IDE 中集成 HOS-Forge 安全扫描技能（`nuclei_scan`、`semgrep_scan`）。

## 前置要求

| 依赖 | 安装方式 |
|------|---------|
| Cursor IDE | [cursor.com](https://cursor.com) |
| HOS-Forge MCP Server | `hos mcp-server --port 8000` |
| Nuclei CLI | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| Semgrep CLI | `pip install semgrep` |

## 文件说明

| 文件 | 用途 |
|------|------|
| `.cursorrules` | Cursor AI 规则配置，定义如何调用 nuclei_scan 和 semgrep_scan |
| `commands.json` | 斜杠命令定义，包含 nuclei-scan、semgrep-scan、full-scan |
| `README.md` | 本说明文件 |

## 快速开始

### 1. 配置 .cursorrules

将 `.cursorrules` 文件复制到你的项目根目录：

```bash
cp .cursorrules /path/to/your/project/.cursorrules
```

Cursor 会自动读取该文件，理解如何调用 HOS-Forge 的安全扫描技能。

### 2. 启动 MCP Server

```bash
hos mcp-server --port 8000
```

### 3. 在 Cursor 中使用

#### Nuclei 漏洞扫描

在 Cursor Chat 中直接对话：

```
Scan https://example.com for high severity vulnerabilities
```

Cursor 会根据 `.cursorrules` 中的规则，自动调用 `nuclei_scan`：

```json
{
  "tool": "nuclei_scan",
  "arguments": {
    "target": "https://example.com",
    "severity": "high"
  }
}
```

#### Semgrep 静态分析

```
Scan the src directory for Python security issues
```

Cursor 自动调用 `semgrep_scan`：

```json
{
  "tool": "semgrep_scan",
  "arguments": {
    "path": "./src",
    "language": "python",
    "config": "p/security-audit"
  }
}
```

### 4. 使用斜杠命令

如果配置了 `commands.json`，可以使用斜杠命令：

```
/nuclei-scan https://example.com --severity high
/semgrep-scan ./src --language python --config p/security-audit
/full-scan --target https://example.com --code-path ./src
```

## 关键配置

### .cursorrules 核心结构

```
## nuclei_scan
- 参数：target (必填), templates (可选), severity (可选)
- 用途：扫描外部 URL/IP 的漏洞

## semgrep_scan
- 参数：path (必填), language (可选), config (可选)
- 用途：扫描源代码的安全和质量问题
```

### commands.json 核心结构

每个命令包含：
- `name`: 命令名称
- `description`: 命令描述
- `arguments`: 参数定义（类型、是否必填、枚举值）
- `mcp_call`: MCP 调用配置（server_url、tool、path_template、body_template）
- `examples`: 使用示例

## MCP 调用方式

### nuclei_scan

```
POST http://localhost:8000/tools/nuclei_scan/execute
Content-Type: application/json

{
  "arguments": {
    "target": "https://example.com",
    "severity": "high"
  }
}
```

### semgrep_scan

```
POST http://localhost:8000/tools/semgrep_scan/execute
Content-Type: application/json

{
  "arguments": {
    "path": "./src",
    "language": "python",
    "config": "auto"
  }
}
```

## 返回结果处理

### nuclei_scan 返回

```json
{
  "findings": [
    {
      "templateID": "CVE-2021-44228",
      "info": { "name": "Log4Shell", "severity": "critical" },
      "host": "https://example.com",
      "matchedAt": "https://example.com/api"
    }
  ],
  "total": 1
}
```

### semgrep_scan 返回

```json
{
  "findings": [
    {
      "check_id": "python.lang.security.audit.eval-detected",
      "path": "src/main.py",
      "start": { "line": 42 },
      "extra": { "message": "Found use of eval()", "severity": "WARNING" }
    }
  ],
  "total": 1
}
```
