# HOS-Forge Claude Code 命令说明

本文档定义了在 Claude Code 中可用的 HOS-Forge 安全扫描命令。

## 可用命令

### 1. nuclei_scan — Nuclei 漏洞扫描

**用途**：对目标 URL、IP 或域名执行漏洞扫描。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target` | string | 是 | 扫描目标（URL、IP 或域名） |
| `templates` | string[] | 否 | Nuclei 模板路径或标签列表 |
| `severity` | string | 否 | 最低严重级别过滤：info, low, medium, high, critical |

**使用方式**：

```
# 基础扫描
请对 https://example.com 执行 nuclei 漏洞扫描

# 指定严重级别
请扫描 https://example.com，只报告 high 及以上级别的漏洞

# 使用特定模板
请对 192.168.1.1 使用 cves/2021/CVE-2021-44228.yaml 模板进行扫描
```

**MCP 调用**：

```json
POST http://localhost:8000/tools/nuclei_scan/execute
{
  "arguments": {
    "target": "https://example.com",
    "severity": "high"
  }
}
```

**返回格式**：

```json
{
  "findings": [
    {
      "templateID": "CVE-2021-44228",
      "info": {
        "name": "Log4Shell",
        "severity": "critical",
        "description": "Apache Log4j2 <=2.14.1 JNDI features..."
      },
      "host": "https://example.com",
      "matchedAt": "https://example.com/api",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "target": "https://example.com"
}
```

---

### 2. semgrep_scan — Semgrep 静态代码分析

**用途**：对源代码文件或目录执行静态安全分析。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | 是 | 要扫描的文件或目录路径 |
| `language` | string | 否 | 编程语言过滤（python, javascript, typescript, java, go, rust 等） |
| `config` | string | 否 | 规则配置：auto（默认）、p/security-audit、p/owasp-top-ten、自定义规则文件路径 |

**使用方式**：

```
# 自动扫描
请对 ./src 目录执行 semgrep 代码分析

# 指定语言和规则
请扫描 ./src 中的 Python 代码，使用 security-audit 规则集

# OWASP Top 10 检查
请对 ./src 执行 OWASP Top 10 安全检查
```

**MCP 调用**：

```json
POST http://localhost:8000/tools/semgrep_scan/execute
{
  "arguments": {
    "path": "./src",
    "language": "python",
    "config": "p/security-audit"
  }
}
```

**返回格式**：

```json
{
  "findings": [
    {
      "check_id": "python.lang.security.audit.eval-detected.eval-detected",
      "path": "src/main.py",
      "start": { "line": 42, "col": 5 },
      "end": { "line": 42, "col": 20 },
      "extra": {
        "message": "Found use of eval(). This can be dangerous.",
        "severity": "WARNING",
        "metadata": {
          "category": "security",
          "technology": ["python"],
          "owasp": ["A03:2021 - Injection"]
        }
      }
    }
  ],
  "total": 1,
  "errors": [],
  "path": "./src"
}
```

---

## 组合使用

可以同时调用两个技能进行全面安全评估：

```
请对 https://example.com 执行完整安全评估：
1. 使用 nuclei_scan 扫描外部漏洞
2. 使用 semgrep_scan 分析 ./src 目录的代码安全
```

## 前置条件

- HOS-Forge MCP Server 运行在 `http://localhost:8000`
- `nuclei` CLI 已安装并在 PATH 中
- `semgrep` CLI 已安装并在 PATH 中

启动 MCP Server：

```bash
hos mcp-server --port 8000
```
