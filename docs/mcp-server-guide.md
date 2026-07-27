# MCP Server 开发指南

## 概述

HOS MCP Hub 提供了统一的安全工具生态，通过 Model Context Protocol (MCP) 将各类安全工具封装为可调用的服务。本指南介绍如何开发自定义 MCP Server。

## 核心概念

### 1. MCP 协议

MCP (Model Context Protocol) 是基于 JSON-RPC 2.0 的通信协议，使用 stdin/stdout 进行通信。

```
Client (HOS-Forge)                    Server (MCP Server)
     |                                       |
     |---- JSON-RPC Request (stdin) ------->|
     |                                       |
     |<--- JSON-RPC Response (stdout) ------|
     |                                       |
```

### 2. MCP Server 架构

每个 MCP Server 是一个独立的进程，提供一组工具（tools）供 Agent 调用。

```
MCP Server
├── 工具注册
├── 请求处理
├── 响应返回
└── 错误处理
```

## 快速开始

### 1. 创建 MCP Server

继承 `BaseMCPServer` 类：

```python
from hosforge.mcp.servers.base import BaseMCPServer
import asyncio

class MySecurityServer(BaseMCPServer):
    """自定义安全工具 MCP Server"""
    
    def __init__(self):
        super().__init__(name="my_security_server")
        
        # 注册工具
        self.register_tool(
            name="scan_vulnerability",
            handler=self.scan_vulnerability,
            description="Scan for vulnerabilities in target"
        )
        
        self.register_tool(
            name="get_report",
            handler=self.get_report,
            description="Get scan report"
        )
    
    async def scan_vulnerability(self, target: str, **kwargs) -> dict:
        """扫描漏洞"""
        # 实现扫描逻辑
        return {
            "status": "completed",
            "findings": [],
            "target": target
        }
    
    async def get_report(self, scan_id: str) -> dict:
        """获取扫描报告"""
        return {
            "scan_id": scan_id,
            "report": "..."
        }

if __name__ == "__main__":
    server = MySecurityServer()
    asyncio.run(server.run())
```

### 2. 配置 MCP Server

在 `mcp-config.yaml` 中配置：

```yaml
servers:
  - name: my_security_server
    command: python
    args:
      - -m
      - my_package.my_server
    env:
      API_KEY: "${MY_API_KEY}"
    enabled: true
```

### 3. 使用 MCP Server

在 Taskflow 工作流中引用：

```yaml
tasks:
  - name: security_scan
    agent: [sast_agent]
    tools: [my_security_server]
```

## BaseMCPServer API

### 构造函数

```python
class BaseMCPServer:
    def __init__(self, name: str, allowed_base_path: Optional[str] = None):
        """初始化 MCP Server
        
        Args:
            name: Server 名称
            allowed_base_path: 可选的基础路径，用于限制文件访问
        """
```

### 注册工具

```python
def register_tool(self, name: str, handler: Callable, description: str = "") -> None:
    """注册工具
    
    Args:
        name: 工具名称
        handler: 工具处理函数（async）
        description: 工具描述
    """
```

### 运行 Server

```python
async def run(self) -> None:
    """运行 MCP Server（stdin/stdout 循环）"""
```

## 工具开发最佳实践

### 1. 工具命名

- 使用小写字母和下划线：`scan_vulnerability`
- 名称应该反映工具功能
- 避免过于通用的名称

### 2. 参数设计

```python
async def scan_vulnerability(
    self,
    target: str,
    scan_type: str = "full",
    timeout: int = 3600,
    **kwargs
) -> dict:
    """扫描漏洞
    
    Args:
        target: 目标地址
        scan_type: 扫描类型 (full/quick/custom)
        timeout: 超时时间（秒）
        **kwargs: 其他参数
    
    Returns:
        扫描结果字典
    """
```

### 3. 返回值格式

统一返回字典格式：

```python
{
    "status": "success|error|partial",
    "data": {...},  # 主要数据
    "metadata": {   # 元数据
        "timestamp": "...",
        "duration": 123,
        "version": "1.0"
    },
    "errors": []  # 错误列表（如果有）
}
```

### 4. 错误处理

```python
async def safe_tool(self, **kwargs) -> dict:
    """安全的工具实现"""
    try:
        # 实现逻辑
        result = await self.do_something(**kwargs)
        return {
            "status": "success",
            "data": result
        }
    except ValueError as e:
        return {
            "status": "error",
            "errors": [{"code": "INVALID_INPUT", "message": str(e)}]
        }
    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return {
            "status": "error",
            "errors": [{"code": "INTERNAL_ERROR", "message": "Internal error occurred"}]
        }
```

## 预定义 MCP Server

### 1. HOS-LS Server

HOS-LS 扫描器集成。

```python
class HOSLSServer(BaseMCPServer):
    """HOS-LS 扫描器 MCP Server"""
    
    def __init__(self):
        super().__init__(name="hos_ls")
        self.register_tool("scan", self.scan, "Scan code for vulnerabilities")
        self.register_tool("analyze", self.analyze, "Analyze scan results")
    
    async def scan(self, target_path: str, **kwargs) -> dict:
        """扫描代码"""
        # 验证路径
        if not self._validate_path(target_path):
            return {"status": "error", "errors": [{"message": "Invalid path"}]}
        
        # 执行扫描
        # ...
        return {"status": "success", "data": findings}
```

**工具列表**：
- `scan`: 扫描代码漏洞
- `analyze`: 分析扫描结果
- `get_stats`: 获取扫描统计

### 2. Semgrep Server

Semgrep SAST 集成。

```python
class SemgrepServer(BaseMCPServer):
    """Semgrep MCP Server"""
    
    def __init__(self):
        super().__init__(name="semgrep")
        self.register_tool("scan", self.scan, "Run Semgrep scan")
        self.register_tool("list_rules", self.list_rules, "List available rules")
```

**工具列表**：
- `scan`: 运行 Semgrep 扫描
- `list_rules`: 列出可用规则
- `custom_scan`: 自定义扫描配置

### 3. Nuclei Server

Nuclei 漏洞扫描集成。

```python
class NucleiServer(BaseMCPServer):
    """Nuclei MCP Server"""
    
    def __init__(self):
        super().__init__(name="nuclei")
        self.register_tool("scan", self.scan, "Run Nuclei scan")
        self.register_tool("list_templates", self.list_templates, "List templates")
```

**工具列表**：
- `scan`: 运行 Nuclei 扫描
- `list_templates`: 列出模板
- `verify`: 验证漏洞

### 4. CodeQL Server

CodeQL 集成。

```python
class CodeQLServer(BaseMCPServer):
    """CodeQL MCP Server"""
    
    def __init__(self):
        super().__init__(name="codeql")
        self.register_tool("create_database", self.create_database, "Create CodeQL database")
        self.register_tool("run_query", self.run_query, "Run CodeQL query")
```

**工具列表**：
- `create_database`: 创建 CodeQL 数据库
- `run_query`: 运行 CodeQL 查询
- `analyze`: 分析结果

### 5. GitHub Server

GitHub API 集成。

```python
class GitHubServer(BaseMCPServer):
    """GitHub API MCP Server"""
    
    def __init__(self):
        super().__init__(name="github")
        self.register_tool("create_pr", self.create_pr, "Create pull request")
        self.register_tool("get_repo", self.get_repo, "Get repository info")
```

**工具列表**：
- `create_pr`: 创建 Pull Request
- `get_repo`: 获取仓库信息
- `list_issues`: 列出 Issues
- `create_issue`: 创建 Issue

## 自定义 MCP Server 示例

### 示例 1: Docker 安全扫描

```python
from hosforge.mcp.servers.base import BaseMCPServer
import asyncio
import subprocess

class DockerSecurityServer(BaseMCPServer):
    """Docker 安全扫描 MCP Server"""
    
    def __init__(self):
        super().__init__(name="docker_security")
        self.register_tool(
            name="scan_image",
            handler=self.scan_image,
            description="Scan Docker image for vulnerabilities"
        )
        self.register_tool(
            name="check_config",
            handler=self.check_config,
            description="Check Docker configuration"
        )
    
    async def scan_image(self, image: str, **kwargs) -> dict:
        """扫描 Docker 镜像"""
        try:
            # 使用 trivy 扫描
            result = subprocess.run(
                ["trivy", "image", "--format", "json", image],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "data": {
                        "image": image,
                        "vulnerabilities": data.get("Results", []),
                        "summary": {
                            "critical": len([v for v in data.get("Results", []) if v.get("Severity") == "CRITICAL"]),
                            "high": len([v for v in data.get("Results", []) if v.get("Severity") == "HIGH"]),
                        }
                    }
                }
            else:
                return {
                    "status": "error",
                    "errors": [{"message": result.stderr}]
                }
        except Exception as e:
            logger.error(f"Scan error: {e}", exc_info=True)
            return {
                "status": "error",
                "errors": [{"code": "SCAN_ERROR", "message": str(e)}]
            }
    
    async def check_config(self, dockerfile: str, **kwargs) -> dict:
        """检查 Dockerfile 配置"""
        # 实现配置检查逻辑
        return {
            "status": "success",
            "data": {
                "issues": [],
                "recommendations": []
            }
        }

if __name__ == "__main__":
    server = DockerSecurityServer()
    asyncio.run(server.run())
```

### 示例 2: API 安全测试

```python
class APISecurityServer(BaseMCPServer):
    """API 安全测试 MCP Server"""
    
    def __init__(self):
        super().__init__(name="api_security")
        self.register_tool(
            name="test_auth",
            handler=self.test_auth,
            description="Test API authentication"
        )
        self.register_tool(
            name="test_injection",
            handler=self.test_injection,
            description="Test for injection vulnerabilities"
        )
    
    async def test_auth(self, api_url: str, **kwargs) -> dict:
        """测试 API 认证"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                # 测试无认证访问
                async with session.get(api_url) as response:
                    if response.status == 200:
                        return {
                            "status": "success",
                            "data": {
                                "vulnerable": True,
                                "issue": "API accessible without authentication"
                            }
                        }
                
                # 测试无效 token
                headers = {"Authorization": "Bearer invalid_token"}
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        return {
                            "status": "success",
                            "data": {
                                "vulnerable": True,
                                "issue": "API accepts invalid tokens"
                            }
                        }
                
                return {
                    "status": "success",
                    "data": {
                        "vulnerable": False,
                        "message": "Authentication properly enforced"
                    }
                }
        except Exception as e:
            return {
                "status": "error",
                "errors": [{"message": str(e)}]
            }
    
    async def test_injection(self, endpoint: str, **kwargs) -> dict:
        """测试注入漏洞"""
        # 实现注入测试逻辑
        return {
            "status": "success",
            "data": {
                "tested": [],
                "vulnerable": []
            }
        }
```

## MCP Hub 配置

### 配置文件格式

`mcp-config.yaml`：

```yaml
# MCP Hub 配置
default_timeout: 30
max_retries: 3

servers:
  - name: hos_ls
    command: python
    args:
      - -m
      - hosforge.mcp.servers.hos_ls
    env:
      HOS_LS_CONFIG: "/path/to/config.yaml"
    enabled: true
  
  - name: semgrep
    command: semgrep
    args:
      - mcp-server
    enabled: true
  
  - name: nuclei
    command: python
    args:
      - -m
      - hosforge.mcp.servers.nuclei
    env:
      NUCLEI_TEMPLATES: "/path/to/templates"
    enabled: true
  
  - name: custom_server
    command: python
    args:
      - /path/to/custom_server.py
    enabled: false  # 禁用
```

### 环境变量

支持在配置中使用环境变量：

```yaml
env:
  API_KEY: "${MY_API_KEY}"
  DATABASE_URL: "${DB_URL}"
```

### 动态加载

```python
from hosforge.mcp import MCPConfig, MCPServerRegistry

# 从文件加载配置
config = MCPConfig.from_yaml_file("mcp-config.yaml")

# 创建注册表
registry = MCPServerRegistry(config)

# 列出可用 Server
servers = registry.list_servers()
for server in servers:
    print(f"{server.name}: {server.enabled}")
```

## 安全最佳实践

### 1. 路径验证

限制文件访问范围：

```python
class SafeServer(BaseMCPServer):
    def __init__(self, allowed_path: str):
        super().__init__(
            name="safe_server",
            allowed_base_path=allowed_path
        )
    
    def _validate_path(self, path: str) -> bool:
        """验证路径是否在允许范围内"""
        from pathlib import Path
        
        target = Path(path).resolve()
        base = self.allowed_base_path
        
        if not base:
            return True
        
        return base in target.parents or target == base
```

### 2. 输入验证

```python
async def safe_tool(self, target: str, **kwargs) -> dict:
    """安全的工具实现"""
    # 验证输入
    if not target or len(target) > 1000:
        return {
            "status": "error",
            "errors": [{"code": "INVALID_INPUT", "message": "Invalid target"}]
        }
    
    # 防止命令注入
    import shlex
    safe_target = shlex.quote(target)
    
    # 执行操作
    # ...
```

### 3. 错误处理

不要向客户端暴露敏感信息：

```python
async def tool_handler(self, **kwargs) -> dict:
    try:
        # 实现逻辑
        pass
    except Exception as e:
        # 记录详细错误到日志
        logger.error(f"Tool error: {e}", exc_info=True)
        
        # 返回通用错误消息
        return {
            "status": "error",
            "errors": [{"code": "INTERNAL_ERROR", "message": "Internal error occurred"}]
        }
```

### 4. 超时控制

```python
async def tool_with_timeout(self, **kwargs) -> dict:
    """带超时的工具"""
    try:
        result = await asyncio.wait_for(
            self.do_something(**kwargs),
            timeout=300  # 5 分钟超时
        )
        return {"status": "success", "data": result}
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "errors": [{"code": "TIMEOUT", "message": "Operation timed out"}]
        }
```

## 测试 MCP Server

### 1. 单元测试

```python
import pytest
from my_server import MySecurityServer

@pytest.mark.asyncio
async def test_scan_vulnerability():
    server = MySecurityServer()
    result = await server.scan_vulnerability(target="example.com")
    
    assert result["status"] == "success"
    assert "findings" in result["data"]

@pytest.mark.asyncio
async def test_invalid_input():
    server = MySecurityServer()
    result = await server.scan_vulnerability(target="")
    
    assert result["status"] == "error"
```

### 2. 集成测试

```python
import subprocess
import json

def test_mcp_server_integration():
    # 启动 Server
    process = subprocess.Popen(
        ["python", "-m", "my_package.my_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # 发送请求
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "scan_vulnerability",
                "arguments": {"target": "example.com"}
            },
            "id": 1
        }
        
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        
        # 读取响应
        response = process.stdout.readline()
        data = json.loads(response)
        
        assert "result" in data
    finally:
        process.terminate()
```

## 调试技巧

### 1. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

class MyServer(BaseMCPServer):
    async def my_tool(self, **kwargs) -> dict:
        logger.debug(f"Tool called with: {kwargs}")
        
        try:
            result = await self.do_something(**kwargs)
            logger.info(f"Tool completed successfully")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Tool failed: {e}", exc_info=True)
            return {"status": "error", "errors": [{"message": str(e)}]}
```

### 2. 手动测试

```bash
# 启动 Server
python -m my_package.my_server

# 在另一个终端发送请求
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m my_package.my_server
```

### 3. 使用 MCP Inspector

```bash
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 运行 Inspector
mcp-inspector python -m my_package.my_server
```

## 参考资源

- [BaseMCPServer 实现](../hosforge/mcp/servers/base.py)
- [MCP 配置](../hosforge/mcp/config.py)
- [MCP 注册表](../hosforge/mcp/registry.py)
- [MCP 客户端](../hosforge/mcp/client.py)
- [预定义 Server](../hosforge/mcp/servers/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
