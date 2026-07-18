# HOS-Forge CLAUDE.md

## 项目概览

HOS-Forge (Hyacinth Of Security Forge) — 基于 OpenHands 二次开发的 **AI 原生信息安全 IDE**。

> 定位：**信息安全 (Information Security)** 全领域，而非仅网络安全。
> 覆盖：Web安全 | 数据安全 | 终端安全 | 密码学 | 云安全 | 应用安全 | 移动安全 | 工控安全

## 核心原则

1. **不删除 OpenHands 原有能力** — 保持 upstream 同步能力
2. **Fork + Extension Layer 模式** — 所有扩展放在 `hosforge/` 目录
3. **扩展而非替换** — 通过 Agent/Tool 体系扩展

## 目录结构

```
hosforge/                          # HOS-Forge 信息安全扩展层
├── __init__.py
├── security_agents/               # 安全 Agent 体系
│   ├── base.py                    # Agent 基类
│   ├── supervisor.py              # Security Supervisor 总控调度
│   ├── audit.py                   # Audit Agent 安全审计
│   ├── defense.py                 # Defense Agent 修复加固
│   └── attack.py                  # Attack Agent 渗透测试(PTES流程)
├── security_tools/                # MCP 安全工具集成
│   ├── base.py                    # 工具基类
│   ├── nmap_tool.py               # Nmap 网络扫描
│   ├── semgrep_tool.py            # Semgrep SAST 代码审计
│   ├── nuclei_tool.py             # Nuclei 漏洞扫描
│   └── burp_tool.py               # Burp Suite API 集成
├── knowledge/                     # 安全知识库 (CVE/CWE RAG)
│   └── base.py                    # SQLite 本地知识库 + 向量检索
├── model_optimizer/               # 本地模型微调 + RAG 打标强化
│   ├── rag_tagger.py              # RAG 打标引擎
│   ├── train.py                   # QLoRA/LoRA 微调
│   ├── inference.py               # 统一推理引擎
│   ├── quantize.py                # 模型量化 (GGUF/AWQ/GPTQ)
│   ├── config.py                  # 智能配置管理
│   └── deploy.py                  # 一键部署
├── reporter/                      # 安全报告生成 (固定格式 HTML)
│   ├── html_reporter.py           # HTML 报告生成器 (安全风信子风格)
│   └── models.py                  # 报告数据模型
├── mcp_server/                    # HOS MCP Server 包装层
│   ├── server.py                  # MCP 主服务器
│   ├── tools/                     # MCP 工具注册
│   └── router.py                  # MCP 路由
├── dashboard/                     # 前端安全 Dashboard
│   └── components/                # React 可视化组件
└── rules/                         # 安全规则集
    └── hos_rules.yaml             # HOS 信息安全规则 (15条)

openhands/                         # OpenHands 核心 (保持原样)
frontend/                          # OpenHands 前端 (保持原样)
```

## 信息安全全领域覆盖

| 领域 | 模块 | 状态 |
|------|------|------|
| 🌐 Web安全 | AuditAgent / BurpTool / NucleiTool | ✅ |
| 🔐 数据安全 | KnowledgeBase / CVE-DataLeak rules | ✅ |
| 💻 终端安全 | AttackAgent / Memory-Corruption rules | ✅ |
| 🔑 密码学 | DefenseAgent / Weak-Crypto rules | ✅ |
| ☁️ 云安全 | Rules: container/cloud-misconfig | ✅ |
| 📱 应用安全 | SemgrepTool / SAST rules | ✅ |
| 🧠 模型安全 | ModelOptimizer / RAGTagger | ✅ |
| 📊 安全报告 | Reporter / HTML Dashboard | ✅ |

## 关键决策记录

- OpenHands upstream 版本: 1.11.0
- HOS-Forge 当前版本: 0.1.0
- 远程仓库: https://github.com/lxcxjxhx/HOS-Forge
- 保持 MIT 开源协议
- 定位: 信息安全全领域 (Information Security)
