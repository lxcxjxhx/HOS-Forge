# HOS-Forge CLAUDE.md

## 项目概览

HOS-Forge (Hyacinth Of Security Forge) — 基于 OpenHands 二次开发的 AI 原生网络安全 IDE。

## 核心原则

1. **不删除 OpenHands 原有能力** — 保持 upstream 同步能力
2. **Fork + Extension Layer 模式** — 所有扩展放在 `hosforge/` 目录
3. **扩展而非替换** — 通过 Agent/Tool 体系扩展

## 目录结构

```
hosforge/                  # HOS-Forge 安全扩展层
├── __init__.py
├── security_agents/       # 安全 Agent 体系
│   ├── base.py            # Agent 基类
│   ├── supervisor.py      # 总控调度 Agent
│   ├── audit.py           # 安全审计 Agent
│   └── defense.py         # 防御/修复 Agent
├── security_tools/        # 安全工具集成
│   └── base.py            # 工具基类
├── knowledge/             # 安全知识库 (RAG)
│   └── base.py            # 知识库基类
└── rules/                 # 安全规则
    └── hos_rules.yaml     # HOS 安全规则集

openhands/                 # OpenHands 核心 (保持原样)
frontend/                  # OpenHands 前端 (保持原样)
enterprise/                # OpenHands 企业版 (保持原样)
```

## 开发命令

```bash
# 安装
pip install -e .

# 运行
python -m openhands.server.main
```

## 关键决策记录

- OpenHands upstream 版本: 1.11.0
- HOS-Forge 初始版本: 0.1.0
- 远程仓库: https://github.com/lxcxjxhx/HOS-Forge
- 保持 MIT 开源协议
