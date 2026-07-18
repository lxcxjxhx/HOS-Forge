# HOS-Forge Release

## v0.1.0 (2026-07-18)

HOS-Forge 第一个公开发行版本。

### 安装方式

#### 从 PyPI 安装
```bash
pip install hos-forge
```

#### 从源码安装
```bash
git clone https://github.com/lxcxjxhx/HOS-Forge.git
cd HOS-Forge
pip install -e .
```

#### 使用 Docker
```bash
docker pull ghcr.io/lxcxjxhx/hos-forge:latest
```

### CLI 工具

| 命令 | 说明 |
|------|------|
| `hos-mcp` | 启动 HOS MCP Server |
| `hos-ci` | CI/CD 安全检查工具 |
| `hos-report` | 安全报告生成 |
| `hos-dashboard` | 启动 Dashboard API |

### 模块组成

- **security_agents** — 4 个安全 Agent (Supervisor/Audit/Attack/Defense)
- **security_tools** — 4 个工具适配器 (Nmap/Semgrep/Nuclei/Burp)
- **knowledge** — CVE/CWE RAG 知识库
- **model_optimizer** — 本地模型微调 + RAG 打标
- **mcp_server** — 19 个 MCP 工具 + 桥接层 + 编排引擎
- **dashboard** — 态势仪表盘
- **reporter** — React 报告生成器
- **ci** — CI/CD 质量门禁
