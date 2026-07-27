# HOS-Forge Release

## v2.0.0 (Unreleased)

**定位升级：AI Native Cybersecurity Engineering Platform**

HOS-Forge v2.0 实现了从"OpenHands + 安全增强插件"到"AI 原生安全工程平台"的架构升级，核心定位为 **Security Agent Orchestration Framework**。

### 🎯 核心特性

#### HOS Taskflow Engine
- YAML 声明式安全工作流编排引擎
- 支持多 Agent 协作、checkpoint/resume 机制
- 内置 7 个示例工作流：安全审计、CVE 研究、依赖扫描、容器安全、代码审查、事件响应、API 安全测试

#### Security Personality System
- 安全专家角色定义系统
- 预定义 6 个 Personality：cve_researcher、red_team、blue_team、code_reviewer、senior_security_engineer、exploit_validator
- 支持自定义 Personality 扩展

#### HOS MCP Hub
- 统一安全工具生态框架
- 核心 MCP Server：hos-ls-server、semgrep-server、nuclei-server、codeql-server、github-server
- 支持动态加载和配置管理

#### Security Memory
- 安全知识库：CVE、漏洞模式、修复历史、误报记录
- 向量数据库集成，支持语义搜索
- 误报率统计和模式匹配

#### Agent Verification Loop
- 漏洞验证闭环：Finding → Candidate → Verified → Fixed → Closed
- 自动 PR 生成和修复审查

### 📦 安装方式

#### 从源码安装
```bash
git clone https://github.com/lxcxjxhx/HOS-Forge.git
cd HOS-Forge
pip install -e .
```

### 🚀 快速开始

```bash
# 运行安全审计工作流
hos taskflow run hosforge/taskflow/workflows/security-audit.yaml

# 列出可用工作流
hos taskflow list

# 列出可用 Personality
hos personality list

# 列出 MCP Server
hos mcp list
```

### 📚 文档

- [Taskflow Engine 使用指南](docs/taskflow-guide.md)
- [Personality 定义指南](docs/personality-guide.md)
- [MCP Server 开发指南](docs/mcp-server-guide.md)
- [Security Memory 使用指南](docs/security-memory-guide.md)

### 🔄 迁移说明

从 v1.0 升级到 v2.0：
- 新增 `hosforge/taskflow/` 目录，包含工作流引擎
- 新增 `hosforge/mcp/` 目录，包含 MCP Hub 框架
- 新增 `hosforge/memory/` 目录，包含安全知识库
- 原有安全 Agent 功能保持兼容

---

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
| `hos` | HOS-Forge 主 CLI（taskflow/personality/mcp 命令） |
| `hos-mcp` | 启动 HOS MCP Server |

### 模块组成

- **security_agents** — 4 个安全 Agent (Supervisor/Audit/Attack/Defense)
- **security_tools** — 4 个工具适配器 (Nmap/Semgrep/Nuclei/Burp)
- **knowledge** — CVE/CWE RAG 知识库
- **model_optimizer** — 本地模型微调 + RAG 打标
- **mcp_server** — 19 个 MCP 工具 + 桥接层 + 编排引擎
- **dashboard** — 态势仪表盘
- **reporter** — React 报告生成器
- **ci** — CI/CD 质量门禁
