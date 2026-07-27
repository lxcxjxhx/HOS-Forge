<a name="readme-top"></a>
<div align="center">
  <h1>🔐 HOS-Forge</h1>
  <p align="center">
    <strong>AI Native Security Platform</strong>
  </p>
  <p align="center">
    Security Runtime + Rule Engine + Knowledge Base
  </p>
  <p align="center">
    <em>跨 IDE 的 AI 安全运行时平台 — 统一安全检测、规则引擎与知识库</em>
  </p>
</div>

---

## 🚀 项目简介

**HOS-Forge（Hyacinth Of Security Forge）** 是 AI 原生安全平台，提供**安全运行时（Security Runtime）**、**规则引擎（Rule Engine）**、**知识库（Knowledge Base）**和**检测能力（Detection Capabilities）**。

### 核心定位

> **不是另一个 AI IDE**
> **而是 AI Native Security Platform**

HOS-Forge 的核心资产是**安全运行时、规则体系、检测引擎和知识库**，这些能力可以服务任何 IDE、CLI 和 CI/CD 系统：

- ✅ **HOS Security Runtime** — 统一安全执行引擎
- ✅ **Security Engine** — 漏洞检测与分析引擎
- ✅ **Rule Engine** — 安全规则定义与执行
- ✅ **Knowledge Base** — CVE/CWE/漏洞模式知识库
- ✅ **Detection Capabilities** — 多维度安全检测能力

### 多入口架构

IDE 只是入口之一。HOS Security Runtime 支持多种接入方式：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HOS Security Runtime                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐│
│  │Security Engine│  │ Rule Engine  │  │Knowledge Base│  │Detection ││
│  │              │  │              │  │              │  │Capabilities│
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                ▲
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   ┌────┴────┐             ┌────┴────┐             ┌────┴────┐
   │IDE Plugin│             │   CLI   │             │REST API │
   └─────────┘             └─────────┘             └─────────┘
        │                       │                       │
   ┌────┴────┐             ┌────┴────┐             ┌────┴────┐
   │ VSCode  │             │   hos   │             │GitHub   │
   │ Cursor  │             │ 命令    │             │ Action  │
   │ Claude  │             │         │             │         │
   │OpenHands│             │         │             │         │
   └─────────┘             └─────────┘             └─────────┘
```

**入口列表：**
- 🔌 **IDE Plugin** — VSCode、Cursor、Claude Code、OpenHands
- 💻 **CLI** — `hos` 命令行工具
- 🌐 **REST API** — 供其他系统集成
- ⚙️ **GitHub Action** — CI/CD 集成

### 核心组件

| 组件 | 职责 |
|------|------|
| **Security Runtime** | 统一安全执行引擎，协调所有安全能力 |
| **Security Engine** | 漏洞检测与分析引擎，支持 SAST/DAST/IAST |
| **Rule Engine** | 安全规则定义与执行，支持自定义规则 |
| **Knowledge Base** | CVE/CWE/漏洞模式知识库，支持 RAG 检索 |
| **Detection Capabilities** | 多维度安全检测能力，覆盖 OWASP Top 10 |
| **Taskflow Engine** | YAML 声明式工作流编排，支持多 Agent 协作 |
| **MCP Hub** | 统一安全工具生态，封装各类安全工具为 MCP Server |

---

## ✨ 核心能力

### 🔒 Security Engine（安全引擎）
- **SAST 静态分析**：代码级漏洞检测，支持 CWE/OWASP Top 10
- **DAST 动态测试**：运行时漏洞扫描，集成 Nuclei、Nmap
- **依赖安全扫描**：第三方组件漏洞检测，CVE 关联分析
- **代码审计**：AI 驱动的安全代码审查，自动识别风险模式

### 📋 Rule Engine（规则引擎）
- **声明式规则定义**：YAML 格式，易于编写和维护
- **规则组合与继承**：支持规则模板和参数化
- **实时规则执行**：毫秒级规则匹配和触发
- **自定义规则扩展**：Python/JavaScript 规则插件

### 🧠 Knowledge Base（知识库）
- **CVE 漏洞库**：实时同步最新 CVE 数据
- **CWE 弱点分类**：完整的弱点分类体系
- **修复方案库**：经过验证的漏洞修复建议
- **误报学习**：基于历史数据的误报识别

### 🔧 Detection Capabilities（检测能力）
- **多语言支持**：Python、JavaScript、Java、Go、Rust 等
- **框架感知**：React、Vue、Spring、Django 等主流框架
- **上下文理解**：AI 辅助的漏洞上下文分析
- **优先级排序**：基于 CVSS 和业务影响的漏洞排序

### 🔄 Taskflow Engine（任务流引擎）
- **YAML 声明式编排**：可视化工作流定义
- **多 Agent 协作**：支持并行和串行任务执行
- **状态管理**：Checkpoint/Resume 机制
- **结果聚合**：统一的执行结果收集

### 🔌 MCP Hub（MCP 工具中心）
- **标准协议**：基于 MCP 协议的工具集成
- **工具市场**：预置安全工具插件
- **动态加载**：运行时工具热插拔
- **统一接口**：标准化的工具调用 API

---

## 📦 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/lxcxjxhx/HOS-Forge.git
cd HOS-Forge

# 安装依赖（使用Poetry）
poetry install

# 或者使用pip
pip install -e .
```

### 使用CLI工具

HOS-Forge提供了`hos`命令行工具来管理安全工作流：

```bash
# 查看帮助
hos --help

# 查看版本
hos --version

# 列出可用工作流
hos taskflow list

# 验证工作流（不执行）
hos taskflow validate examples/workflows/demo_quick_scan.yaml

# Dry-run模式（验证但不执行）
hos taskflow run examples/workflows/demo_quick_scan.yaml --dry-run

# 运行安全审计工作流
hos taskflow run examples/workflows/security_audit.yaml

# 启用checkpoint的工作流
hos taskflow run examples/workflows/security_audit.yaml --checkpoint

# 列出可用Personality
hos personality list

# 列出可用MCP服务器
hos mcp list
```

### 验证安装

运行安装验证脚本，确保所有组件正常工作：

```bash
# 验证安装
python verify_installation.py

# 验证脚本会检查：
# - Python版本和pip
# - hos命令是否安装
# - taskflow命令功能
# - 核心模块导入
```

### 演示工作流

运行演示脚本，体验Taskflow Engine和Agent/Tool Registry：

```bash
# 运行演示工作流
python demo_workflow.py

# 演示内容包括：
# - Agent和Tool注册表
# - 工作流解析和执行
# - 任务依赖关系展示
```

### 示例工作流

```yaml
# security-audit.yaml
version: "1.0"
name: "Security Audit"
description: "Complete security audit workflow"

tasks:
  - name: static_scan
    agent: [sast_agent]
    tools: [hos_ls, semgrep]
  
  - name: exploit_verify
    agent: [redteam_agent]
    tools: [nuclei]
    depends_on: [static_scan]
  
  - name: patch_generation
    agent: [developer_agent]
    depends_on: [exploit_verify]
  
  - name: security_review
    agent: [security_reviewer]
    depends_on: [patch_generation]
```

### 通过 IDE 使用

安装对应的 IDE 插件后，HOS Security Runtime 会自动激活：

1. **VSCode**：安装 HOS Security 插件，打开项目即可自动检测
2. **Cursor**：在 Cursor 中启用 HOS MCP Server
3. **Claude Code**：配置 HOS MCP Hub 集成
4. **OpenHands**：HOS-Forge 本身就是基于 OpenHands 的 Reference IDE

### 通过 REST API 使用

启动 HOS Security Runtime 服务：

```bash
# 启动服务
hos server start --port 8000

# 执行扫描
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "./code", "rules": ["sql_injection", "xss"]}'

# 查询知识库
curl http://localhost:8000/api/v1/knowledge/CVE-2024-1234
```

### 📖 快速入门

详细的快速入门指南请参考 [Quick Start Guide](docs/getting-started.md)。

---

## 💡 Use Cases

### 场景 1：IDE 内实时安全检测
**入口**：VSCode / Cursor / Claude Code / OpenHands 插件

开发者在 IDE 中编写代码时，HOS Security Runtime 实时检测安全漏洞：
- 自动识别 SQL 注入、XSS、命令注入等风险模式
- 提供修复建议和代码示例
- 与代码审查流程无缝集成

### 场景 2：CLI 批量安全扫描
**入口**：`hos` 命令行工具

安全工程师对代码库进行批量扫描：
```bash
# 扫描整个项目
hos scan --target ./my-project

# 执行特定安全工作流
hos taskflow run hosforge/taskflow/workflows/security-audit.yaml

# 生成安全报告
hos report generate --format html --output ./security-report.html
```

### 场景 3：CI/CD 集成
**入口**：GitHub Action

在 CI/CD 流程中自动执行安全检查：
```yaml
# .github/workflows/security-check.yml
name: Security Check
on: [push, pull_request]
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run HOS Security Scan
        uses: lxcxjxhx/hos-security-action@v1
        with:
          workflow: security-audit
          fail-on: high,critical
```

### 场景 4：REST API 集成
**入口**：REST API

其他系统通过 API 调用 HOS 安全能力：
```bash
# 执行代码扫描
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "./code", "rules": ["sql_injection", "xss"]}'

# 查询漏洞知识库
curl http://localhost:8000/api/v1/knowledge/CVE-2024-1234
```

### 场景 5：自定义安全工作流
**入口**：Taskflow Engine

定义和执行复杂的安全工作流：
```yaml
# custom-security-workflow.yaml
version: "1.0"
name: "Custom Security Audit"
tasks:
  - name: dependency_scan
    agent: [dependency_agent]
    tools: [npm_audit, pip_audit]
  
  - name: code_audit
    agent: [audit_agent]
    tools: [semgrep, hos_ls]
    depends_on: [dependency_scan]
  
  - name: vulnerability_verify
    agent: [redteam_agent]
    tools: [nuclei]
    depends_on: [code_audit]
```

---

## 🗺️ 版本规划

| 版本 | 定位 | 目标 |
|------|------|------|
| **v1.0** | AI Coding Agent | 基础安全编码助手 |
| **v2.0** | Security Agent Framework | Taskflow + Personality + MCP Hub + Verification Loop |
| **v3.0** | AI Security Engineer | 自动化安全工程全流程（输入 GitHub Repo → 输出安全报告 + PR） |

### v2.0 核心特性（当前开发中）

- ✅ HOS Taskflow Engine — YAML 声明式安全工作流编排
- ✅ Security Personality System — 安全专家角色定义
- ✅ HOS MCP Hub — 统一安全工具生态
- ✅ Security Memory — 安全知识库与误报学习
- ✅ Agent Verification Loop — 漏洞发现→验证→修复→审查闭环
- ✅ CLI 工具 (`hos` 命令行)
- ✅ 端到端工作流集成测试
- 🔄 文档完善与发布准备

---

## 📚 文档

### 核心文档

- [快速入门指南](docs/getting-started.md) — 从零开始使用 HOS-Forge
- [Taskflow Engine 使用指南](docs/taskflow-guide.md) — YAML 声明式安全工作流编排
- [Personality 定义指南](docs/personality-guide.md) — 安全专家角色定义系统
- [MCP Server 开发指南](docs/mcp-server-guide.md) — 统一安全工具生态
- [Security Memory 使用指南](docs/security-memory-guide.md) — 安全知识库与误报学习
- [Verification Loop 使用指南](docs/verification-loop.md) — 漏洞发现→验证→修复→审查闭环

### 示例工作流

HOS-Forge 提供了多个预定义的安全工作流：

| 工作流 | 说明 | 文件 |
|--------|------|------|
| Security Audit | 完整安全审计流程 | `hosforge/taskflow/workflows/security-audit.yaml` |
| CVE Research | CVE 漏洞研究工作流 | `hosforge/taskflow/workflows/cve-research.yaml` |
| Code Review | 代码安全审查流程 | `hosforge/taskflow/workflows/code-review.yaml` |
| API Security Test | API 安全测试流程 | `hosforge/taskflow/workflows/api-security-test.yaml` |
| Container Security | 容器安全检查流程 | `hosforge/taskflow/workflows/container-security.yaml` |
| Dependency Scan | 依赖漏洞扫描流程 | `hosforge/taskflow/workflows/dependency-scan.yaml` |
| Incident Response | 安全事件响应流程 | `hosforge/taskflow/workflows/incident-response.yaml` |

### 预定义 Personality

HOS-Forge 提供了多个预定义的安全专家角色：

| Personality | 职责 | 文件 |
|-------------|------|------|
| CVE Researcher | CVE 漏洞研究 | `hosforge/personalities/definitions/cve_researcher.yaml` |
| Red Team | 红队攻击验证 | `hosforge/personalities/definitions/red_team.yaml` |
| Blue Team | 蓝队防御检测 | `hosforge/personalities/definitions/blue_team.yaml` |
| Code Reviewer | 代码安全审查 | `hosforge/personalities/definitions/code_reviewer.yaml` |
| Exploit Validator | 漏洞利用验证 | `hosforge/personalities/definitions/exploit_validator.yaml` |
| Senior Security Engineer | 高级安全工程师 | `hosforge/personalities/definitions/senior_security_engineer.yaml` |

---

## 🤝 贡献指南

HOS-Forge 基于 OpenHands 二次开发，我们的开发策略：

1. **不修改 OpenHands 核心代码** — 所有安全扩展放在 `hosforge/` 目录
2. **定期同步 upstream** — 保持社区最新能力
3. **扩展优先** — 通过 Agent 和 Tool 体系扩展，而非 fork 魔改

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

OpenHands 部分遵循其原始 [MIT License](https://github.com/OpenHands/OpenHands/blob/main/LICENSE)。

---

<div align="center">
  <sub>Built with ❤️ by HOS-Forge Team | 基于 OpenHands 构建</sub>
</div>
