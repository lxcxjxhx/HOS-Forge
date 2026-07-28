# HOS-Forge

**AI Native Security Platform** - 面向 AI 原生开发环境的安全工具集成平台

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 项目简介

HOS-Forge 是一个模块化的安全工具集成平台，通过 **Skill 系统** 封装各类安全扫描工具（Nuclei、Semgrep 等），并通过 **IDE 适配器** 将这些能力无缝集成到主流 AI 原生开发环境中（VSCode、Cursor、Claude Code）。

### 核心特性

- 🔧 **Skill 系统**: 模块化封装安全工具，支持动态加载和自动注册
- 🔌 **IDE 适配器**: 统一接口适配多种 IDE，提供一致的用户体验
- 🌐 **MCP Server**: 基于 HTTP 的 Model Context Protocol 服务，支持远程调用
- ⚡ **CLI 工具**: 命令行界面快速执行安全扫描
- 🎯 **类型安全**: 完整的类型注解和参数验证

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      IDE / AI Agent                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   VSCode     │  │    Cursor    │  │ Claude Code  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    IDE Adapter Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │VSCodeAdapter │  │CursorAdapter │  │ClaudeAdapter │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │  FastAPI HTTP Server  |  Skill Bridge  |  Tools    │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       Skill Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │NucleiSkill   │  │SemgrepSkill  │  │ GitHubSkill  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Custom Skill │  │ Custom Skill │  │     ...      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Tools                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Nuclei  │  │ Semgrep  │  │  gh CLI  │  │   ...    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-org/hos-forge.git
cd hos-forge

# 安装依赖
pip install -e .

# 或使用 uv (推荐)
uv pip install -e .
```

#### 验证安装

```bash
# 检查 CLI 是否可用
hos --version

# 列出可用的 skills
hos skill list
```

### 前置依赖

HOS-Forge 需要以下外部工具（根据使用的 skill 不同）：

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| [Nuclei](https://github.com/projectdiscovery/nuclei) | 漏洞扫描 | `go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| [Semgrep](https://semgrep.dev/) | 静态代码分析 | `pip install semgrep` |
| [GitHub CLI](https://cli.github.com/) | GitHub 集成 | 参考 [官方文档](https://cli.github.com/manual/installation) |

## 📚 使用指南

### CLI 使用

#### 列出所有 Skills

```bash
# 表格格式输出
hos skill list

# JSON 格式输出
hos skill list --format json
```

#### 查看 Skill 详情

```bash
# 查看 nuclei_scan skill 的详细信息
hos skill info nuclei_scan

# JSON 格式输出
hos skill info nuclei_scan --format json
```

#### 执行 Skill

```bash
# 执行 Nuclei 扫描
hos skill run nuclei_scan target=https://example.com

# 指定严重级别过滤
hos skill run nuclei_scan target=https://example.com severity=high

# 执行 Semgrep 扫描
hos skill run semgrep_scan path=./src

# 指定语言和配置
hos skill run semgrep_scan path=./src language=python config=auto

# GitHub 操作
hos skill run github_integration action=list_issues repo=owner/repo state=open
```

### MCP Server 使用

启动 MCP Server：

```bash
# 启动服务（默认端口 8000）
python -m hosforge.mcp_server.server

# 或使用 uvicorn
uvicorn hosforge.mcp_server.server:app --host 0.0.0.0 --port 8000
```

#### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/skills` | GET | 列出所有已注册的 skills |
| `/tools` | GET | 列出所有可用的 MCP tools |
| `/tools/{tool_name}/execute` | POST | 执行指定的 MCP tool |

#### 示例请求

```bash
# 健康检查
curl http://localhost:8000/health

# 列出 skills
curl http://localhost:8000/skills

# 执行扫描
curl -X POST http://localhost:8000/tools/nuclei_scan/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"target": "https://example.com"}}'
```

## 🔌 IDE 适配器配置

### VSCode 适配器

VSCode 适配器将 HOS-Forge 的功能映射为 VSCode 命令，可在 `package.json` 中注册：

```json
{
  "contributes": {
    "commands": [
      {
        "command": "hos.skill.run",
        "title": "HOS: Run Skill",
        "category": "HOS"
      },
      {
        "command": "hos.scan.nuclei",
        "title": "HOS: Run Nuclei Scan",
        "category": "HOS"
      }
    ]
  }
}
```

支持的命令：
- `hos.skill.run` - 执行 Skill
- `hos.skill.list` - 列出 Skills
- `hos.skill.info` - Skill 详情
- `hos.scan.nuclei` - Nuclei 扫描
- `hos.scan.semgrep` - Semgrep 扫描

### Cursor 适配器

Cursor 适配器支持 `@mention` 命令格式：

```
@hos scan          # 运行安全扫描
@hos nuclei        # 运行 Nuclei 扫描
@hos semgrep       # 运行 Semgrep 分析
@hos skill list    # 列出可用 skills
@hos skill info    # 查看 skill 详情
```

输出格式为 Markdown，适合在 Cursor 聊天界面展示。

### Claude Code 适配器

Claude Code 适配器支持 `/hos-xxx` 斜杠命令：

```
/hos-scan          # 运行安全扫描
/hos-nuclei        # 运行 Nuclei 扫描
/hos-semgrep       # 运行 Semgrep 分析
/hos-skill-list    # 列出可用 skills
/hos-skill-info    # 查看 skill 详情
```

详细配置指南请参考 [适配器文档](docs/adapters/README.md)。

## 🛠️ Skill 系统

### 内置 Skills

| Skill 名称 | 描述 | 参数 |
|------------|------|------|
| `nuclei_scan` | 使用 Nuclei 进行漏洞扫描 | `target` (必填), `templates`, `severity` |
| `semgrep_scan` | 使用 Semgrep 进行静态代码分析 | `path` (必填), `language`, `config` |
| `github_integration` | GitHub 集成操作 | `action` (必填), `repo` (必填), 其他可选参数 |

### 创建自定义 Skill

继承 `Skill` 基类并实现 `execute` 方法：

```python
from hosforge.skills.base_skill import Skill, SkillResult

class MyCustomSkill(Skill):
    def __init__(self) -> None:
        super().__init__(
            name="my_custom_skill",
            description="我的自定义 Skill",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "参数1 的描述",
                    },
                    "param2": {
                        "type": "integer",
                        "description": "参数2 的描述",
                    },
                },
                "required": ["param1"],
            },
        )

    def execute(self, **kwargs) -> dict:
        param1 = kwargs["param1"]
        param2 = kwargs.get("param2", 10)
        
        # 实现你的逻辑
        result = do_something(param1, param2)
        
        return {
            "success": True,
            "data": result,
        }
```

详细开发指南请参考 [Skill 开发文档](docs/skills/README.md)。

## 📁 项目结构

```
hos-forge/
├── hosforge/
│   ├── adapters/           # IDE 适配器
│   │   ├── base_adapter.py
│   │   ├── vscode_adapter.py
│   │   ├── cursor_adapter.py
│   │   ├── claude_code_adapter.py
│   │   └── templates/      # 适配器配置模板
│   ├── cli/                # 命令行界面
│   │   └── main.py
│   ├── mcp_server/         # MCP Server
│   │   ├── server.py
│   │   └── skill_bridge.py
│   ├── skills/             # Skill 系统
│   │   ├── base_skill.py
│   │   ├── registry.py
│   │   ├── loader.py
│   │   └── security/       # 安全相关 skills
│   │       ├── nuclei_skill.py
│   │       ├── semgrep_skill.py
│   │       └── github_skill.py
│   └── tests/              # 测试
├── docs/                   # 文档
│   ├── skills/             # Skill 文档
│   └── adapters/           # 适配器文档
└── README.md
```

## 🧪 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_skills.py

# 带覆盖率报告
pytest --cov=hosforge
```

### 代码质量

```bash
# 格式化代码
ruff format hosforge/

# 检查代码
ruff check hosforge/

# 类型检查
mypy hosforge/
```

## 📖 文档

- [Skill 系统文档](docs/skills/README.md)
  - [Nuclei Scan Skill](docs/skills/nuclei_skill.md)
  - [Semgrep Scan Skill](docs/skills/semgrep_skill.md)
  - [GitHub Integration Skill](docs/skills/github_skill.md)
  - [自定义 Skill 开发指南](docs/skills/custom_skill.md)
- [适配器文档](docs/adapters/README.md)
  - [VSCode 适配器](docs/adapters/vscode_adapter.md)
  - [Cursor 适配器](docs/adapters/cursor_adapter.md)
  - [Claude Code 适配器](docs/adapters/claude_code_adapter.md)

## 🤝 贡献

欢迎贡献！请参考 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [Nuclei](https://github.com/projectdiscovery/nuclei) - 快速可定制的漏洞扫描器
- [Semgrep](https://semgrep.dev/) - 静态代码分析工具
- [GitHub CLI](https://cli.github.com/) - GitHub 命令行工具
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 协议规范
