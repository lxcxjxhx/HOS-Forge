<a name="readme-top"></a>
<div align="center">
  <h1>🔐 HOS-Forge</h1>
  <p align="center">
    <strong>AI Native Information Security IDE</strong>
  </p>
  <p align="center">
    基于 <a href="https://github.com/OpenHands/OpenHands">OpenHands</a> 二次开发的 AI 原生信息安全 IDE
  </p>
  <p align="center">
    <em>覆盖 Web安全 · 数据安全 · 终端安全 · 密码学 · 云安全 · 应用安全 · 移动安全</em>
  </p>
</div>

---

## 🚀 项目简介

**HOS-Forge（Hyacinth Of Security Forge）** 是新一代 AI Native 网络安全 IDE，
在 OpenHands 强大的 AI Agent 框架基础上，深入集成网络安全领域能力。

### 核心原则

> **OpenHands = AI IDE 操作系统**
> **HOS-Forge = 面向网络安全领域的专业发行版**

我们不替代 OpenHands，而是在其之上构建安全领域能力：

- ✅ **完整继承** OpenHands 全部功能（Agent SDK、CLI、GUI、Sandbox、Tool 体系）
- ✅ **扩展而非替换** — 保持 upstream 同步能力
- ✅ **安全领域深度集成** — SAST、渗透、防御、知识库、MCP 安全工具

---

## 🏗️ 架构

```
HOS-Forge IDE
│
├── OpenHands Core           ← 完整保留上游能力
│   ├── Agent Runtime
│   ├── Reasoning Loop
│   ├── Tool Manager
│   ├── Sandbox
│   └── Memory
│
├── HOS Security Layer       ← 安全扩展层
│   ├── Security Agents
│   │   ├── Supervisor Agent     (总控调度)
│   │   ├── Audit Agent          (安全审计)
│   │   ├── Attack Agent         (渗透测试)
│   │   └── Defense Agent        (修复加固)
│   │
│   ├── Security Tools
│   │   ├── SAST 引擎集成
│   │   ├── MCP 安全工具
│   │   └── 外部工具适配器
│   │
│   ├── Knowledge Base (RAG)
│   │   ├── CVE 漏洞库
│   │   ├── CWE 分类库
│   │   └── ExploitDB
│   │
│   └── Security Rules
│       ├── OWASP Top 10 规则集
│       └── 自定义安全策略
```

---

## ✨ 核心功能

### 🤖 AI Security Coding Agent
安全增强的 AI 编程 Agent，自动检测生成代码中的安全漏洞并修复。

### 🔍 Security Code Review Agent
代码提交前自动分析 CWE/CVE/OWASP Top 10 安全风险。

### 🛡️ 安全知识大脑 (RAG + CVE/CWE)
基于 SQLite + 向量检索的安全知识库，支持 CVE/CWE 查询、ExploitDB PoC、KEV 检测。

### 🔧 MCP 安全工具生态 (MCP Server)
集成 Nmap、Semgrep、Nuclei、Burp Suite 的 MCP 服务，任何 AI Agent 均可通过 MCP 协议调用。

### 🧠 本地模型微调 (Model Optimizer)
QLoRA/LoRA 微调 + RAG 打标强化，8GB VRAM 可用，支持离线安全模型定制与企业知识注入。

### 📊 安全报告引擎 (HTML Reporter)
固定格式 HTML 报告生成，安全风信子设计风格，支持打印/PDF 导出，便于复盘转发。

---

## 📦 快速开始

```bash
# 克隆仓库
git clone https://github.com/lxcxjxhx/HOS-Forge.git
cd HOS-Forge

# 安装依赖
pip install -e .

# 启动
python -m openhands.server.main
```

---

## 🗺️ 版本规划

| 版本 | 目标 |
|------|------|
| **v0.1** | OpenHands + HOS 品牌，基础安全分析 |
| **v0.3** | Attack Agent + MCP工具 + CVE/CWE RAG + HTML报告 |
| **v0.5** | Model Optimizer本地微调 + RAG打标 + Dashboard可视化 |
| **v0.7** | HOS MCP Server + 三方MCP桥接 (Burp/SecurityHub) |
| **v1.0** | 完整 AI 信息安全 IDE (全领域覆盖) |

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
