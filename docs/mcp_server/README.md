# MCP Server 文档

HOS-Forge MCP Server 提供基于 HTTP 的 Model Context Protocol 服务，支持远程调用安全扫描工具。

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [API 端点](#api-端点)
- [工具执行](#工具执行)
- [配置选项](#配置选项)
- [集成示例](#集成示例)
- [错误处理](#错误处理)

## 概述

MCP Server 是 HOS-Forge 的核心服务组件，它将所有注册的 Skills 转换为 MCP tools，通过 HTTP API 提供远程调用能力。

### 功能特性

- 动态 Skill 注册和发现
- 标准化的 HTTP API 接口
- 健康检查和监控端点
- 支持多种传输模式（HTTP/stdio）
- 完整的错误处理和日志

## 快速开始

### 启动服务器

```bash
# 使用默认配置启动（端口 8321）
hos-mcp

# 指定端口
hos-mcp --port 8080

# 使用 stdio 模式（适用于 Claude Desktop）
hos-mcp --stdio

# 验证工具注册
hos-mcp --verify
```

### 验证服务

```bash
# 健康检查
curl http://localhost:8321/health

# 列出可用工具
curl http://localhost:8321/tools
```

## API 端点

### 健康检查

**端点**: `GET /health`

检查服务器状态和已注册的 Skills 数量。

**响应示例**:

```json
{
  "status": "ok",
  "skills_count": 5
}
```

### 列出 Skills

**端点**: `GET /skills`

获取所有已注册的 Skills 列表。

**响应示例**:

```json
{
  "skills": [
    {
      "name": "nuclei_scan",
      "description": "使用 Nuclei 进行漏洞扫描"
    },
    {
      "name": "semgrep_scan",
      "description": "使用 Semgrep 进行静态代码分析"
    }
  ]
}
```

### 列出 MCP Tools

**端点**: `GET /tools`

获取所有可用的 MCP tools 定义。

**响应示例**:

```json
{
  "tools": [
    {
      "name": "nuclei_scan",
      "description": "使用 Nuclei 进行漏洞扫描",
      "inputSchema": {
        "type": "object",
        "properties": {
          "target": {
            "type": "string",
            "description": "扫描目标 URL 或 IP"
          }
        },
        "required": ["target"]
      }
    }
  ]
}
```

### 执行工具

**端点**: `POST /tools/{tool_name}/execute`

执行指定的 MCP tool。

**请求体**:

```json
{
  "arguments": {
    "target": "https://example.com",
    "severity": "high"
  }
}
```

**响应示例**:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"findings\": [], \"total\": 0, \"target\": \"https://example.com\"}"
    }
  ]
}
```

## 工具执行

### 执行流程

1. 客户端发送 POST 请求到 `/tools/{tool_name}/execute`
2. 服务器验证 tool 是否存在
3. 验证输入参数
4. 执行对应的 Skill
5. 返回执行结果

### 示例：执行 Nuclei 扫描

```bash
curl -X POST http://localhost:8321/tools/nuclei_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "target": "https://example.com",
      "severity": "high"
    }
  }'
```

### 示例：执行 Semgrep 分析

```bash
curl -X POST http://localhost:8321/tools/semgrep_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "target": "./my-project",
      "config": "p/security-audit"
    }
  }'
```

## 配置选项

### 命令行参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--port` | HTTP 服务端口 | 8321 |
| `--stdio` | 使用 stdio 传输模式 | false |
| `--verify` | 验证工具注册并退出 | false |
| `--help` | 显示帮助信息 | - |

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `HOS_MCP_PORT` | HTTP 服务端口 | 8321 |
| `HOS_LOG_LEVEL` | 日志级别 | INFO |
| `HOS_LOG_FORMAT` | 日志格式 | standard |

## 集成示例

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "hos-forge": {
      "command": "hos-mcp",
      "args": ["--stdio"]
    }
  }
}
```

### VSCode 扩展集成

```typescript
import axios from 'axios';

const MCP_SERVER_URL = 'http://localhost:8321';

async function runNucleiScan(target: string) {
    const response = await axios.post(
        `${MCP_SERVER_URL}/tools/nuclei_scan/execute`,
        { arguments: { target } }
    );
    return response.data;
}
```

### Python 客户端

```python
import httpx

MCP_SERVER_URL = "http://localhost:8321"

def run_skill(skill_name: str, **kwargs):
    response = httpx.post(
        f"{MCP_SERVER_URL}/tools/{skill_name}/execute",
        json={"arguments": kwargs}
    )
    return response.json()

# 使用示例
result = run_skill("nuclei_scan", target="https://example.com")
print(result)
```

## 错误处理

### HTTP 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 404 | Tool 不存在 |
| 400 | 参数验证失败 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "Tool 'invalid_tool' not found"
}
```

### 常见错误

#### 1. Tool 不存在

```
HTTP 404
{"detail": "Tool 'invalid_tool' not found"}
```

**解决方案**: 使用 `GET /tools` 查看可用的 tools。

#### 2. 参数验证失败

```
HTTP 400
{"detail": "Missing required parameter: target"}
```

**解决方案**: 检查 tool 的参数定义，确保提供所有必填参数。

#### 3. 执行超时

```
HTTP 500
{"detail": "Execution timeout"}
```

**解决方案**: 对于长时间运行的任务，考虑增加超时时间或分批处理。

## 监控和日志

### 日志配置

MCP Server 使用标准 Python logging 模块：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

### 日志级别

- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 访问日志

所有 API 请求都会被记录，包括：
- 请求方法
- 请求路径
- 响应状态码
- 执行时间

## 高级用法

### 自定义 Skill 注册

```python
from hosforge.mcp_server.server import create_app
from hosforge.skills.registry import SkillRegistry
from my_custom_skill import MyCustomSkill

# 创建自定义注册表
registry = SkillRegistry()
registry.register(MyCustomSkill())

# 创建应用
app = create_app(registry)
```

### 批量执行

```python
import asyncio
import httpx

async def batch_execute():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post(
                "http://localhost:8321/tools/nuclei_scan/execute",
                json={"arguments": {"target": f"https://target{i}.com"}}
            )
            for i in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

results = asyncio.run(batch_execute())
```

## 相关资源

- [Skill 系统文档](../skills/README.md)
- [适配器系统文档](../adapters/README.md)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
