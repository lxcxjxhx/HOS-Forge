# HOS-Forge Claude Code 集成示例

本示例展示如何在 Claude Code 中集成 HOS-Forge 安全扫描技能（`nuclei_scan`、`semgrep_scan`）。

## 前置要求

| 依赖 | 安装方式 |
|------|---------|
| Claude Code | [claude.ai](https://claude.ai) 或 CLI |
| HOS-Forge MCP Server | `hos mcp-server --port 8000` |
| Nuclei CLI | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| Semgrep CLI | `pip install semgrep` |

## 文件说明

| 文件 | 用途 |
|------|------|
| `skills.json` | Skill 定义文件，包含 nuclei_scan 和 semgrep_scan 的完整参数和调用配置 |
| `commands.md` | 命令说明文档，展示如何在 Claude Code 中调用这两个技能 |
| `README.md` | 本说明文件 |

## 快速开始

### 1. 启动 MCP Server

```bash
hos mcp-server --port 8000
```

### 2. 配置 Claude Code Skill

将 `skills.json` 中的内容添加到 Claude Code 的 skill 配置中。Claude Code 会根据 skill 定义自动识别何时调用这些技能。

### 3. 在 Claude Code 中使用

#### Nuclei 漏洞扫描

直接对话即可触发：

```
请对 https://example.com 执行漏洞扫描，只关注 high 和 critical 级别
```

Claude Code 会调用 `nuclei_scan`：

```json
{
  "target": "https://example.com",
  "severity": "high"
}
```

#### Semgrep 静态分析

```
请扫描 ./src 目录的 Python 代码，使用 OWASP Top 10 规则
```

Claude Code 会调用 `semgrep_scan`：

```json
{
  "path": "./src",
  "language": "python",
  "config": "p/owasp-top-ten"
}
```

## 关键配置

### skills.json 结构

```json
{
  "skills": [
    {
      "name": "nuclei_scan",
      "description": "技能描述，Claude Code 根据此判断何时调用",
      "parameters": {
        "type": "object",
        "properties": { ... },
        "required": ["target"]
      },
      "mcp_endpoint": {
        "url": "http://localhost:8000/tools/nuclei_scan/execute",
        "method": "POST"
      }
    }
  ]
}
```

关键字段：
- `name`: 技能名称，用于 CLI 调用（`hos skill run nuclei_scan`）
- `description`: 技能描述，Claude Code 根据此判断调用时机
- `parameters`: JSON Schema 格式的参数定义
- `mcp_endpoint`: MCP 服务端点配置
- `usage_examples`: 使用示例

### commands.md 内容

提供人类可读的命令说明，包括：
- 参数表格
- 自然语言使用示例
- MCP 调用格式
- 返回结果格式

## MCP 调用方式

两个技能都通过 HTTP POST 调用 MCP Server：

### nuclei_scan

```bash
curl -X POST http://localhost:8000/tools/nuclei_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "target": "https://example.com",
      "severity": "high"
    }
  }'
```

### semgrep_scan

```bash
curl -X POST http://localhost:8000/tools/semgrep_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "path": "./src",
      "language": "python",
      "config": "auto"
    }
  }'
```

## CLI 调用方式

也可以通过 HOS-Forge CLI 直接调用：

```bash
# Nuclei 扫描
hos skill run nuclei_scan target=https://example.com severity=high

# Semgrep 扫描
hos skill run semgrep_scan path=./src language=python config=p/security-audit
```

## Python API 调用

```python
from hosforge.skills.security import NucleiScanSkill, SemgrepScanSkill

# Nuclei
nuclei = NucleiScanSkill()
result = nuclei.execute(target="https://example.com", severity="high")
print(f"Found {result['total']} vulnerabilities")

# Semgrep
semgrep = SemgrepScanSkill()
result = semgrep.execute(path="./src", language="python", config="auto")
print(f"Found {result['total']} issues")
```
