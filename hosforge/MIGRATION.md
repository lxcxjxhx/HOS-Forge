# HOS-Forge 迁移文档：从 OpenHands 到独立 Skill+插件架构

## 迁移原因

HOS-Forge 最初基于 OpenHands 二次开发，存在以下问题：
- **平台依赖性强**：与 OpenHands 深度耦合，难以独立演进
- **原创性不足**：核心能力受限于 OpenHands 架构
- **兼容性差**：无法便捷地被 VSCode、Cursor、Claude Code 等主流 AI IDE 调用

## 新架构概述

重构后的 HOS-Forge 采用 **IDE 无关的 Skill+插件架构**：

### 核心组件

1. **Skill 抽象层** (`hosforge/skills/`)
   - 统一的 `Skill` 基类，定义标准化接口
   - `SkillRegistry` 实现 skill 注册和发现
   - `SkillLoader` 支持动态加载 skill
   - 安全工具已重构为独立 skill：
     - `NucleiScanSkill` - 漏洞扫描
     - `SemgrepScanSkill` - 静态分析
     - `GitHubIntegrationSkill` - GitHub 集成

2. **IDE 适配器层** (`hosforge/adapters/`)
   - `IDEAdapter` 基类，定义适配接口
   - 已实现适配器：
     - `VSCodeAdapter` - VSCode 扩展集成
     - `CursorAdapter` - Cursor @mention 和命令
     - `ClaudeCodeAdapter` - Claude Code /command 格式
   - `AdapterRegistry` 管理多 IDE 适配器

3. **标准化 MCP Server** (`hosforge/mcp_server/`)
   - 自动将 skill 转换为 MCP tools
   - 提供 `/health`、`/skills`、`/tools` 端点
   - 支持 IDE 通过标准 MCP 协议调用

4. **CLI 命令** (`hosforge/cli/`)
   - `hos skill list` - 列出所有 skills
   - `hos skill info <name>` - 查看 skill 详情
   - `hos skill run <name>` - 执行 skill
   - 保留 `hos taskflow` 向后兼容

## 主要变更

### 移除的内容

- ❌ `openhands/` 目录及其所有依赖
- ❌ `pyproject.toml` 中的 OpenHands 依赖项
- ❌ 代码中所有 `import openhands` 和 `from openhands import ...` 语句
- ❌ 对 OpenHands agent/sandbox 的直接依赖

### 新增的内容

- ✅ 独立的 Skill 抽象层（`base_skill.py`, `registry.py`, `loader.py`）
- ✅ IDE 适配器框架（支持多 IDE 扩展）
- ✅ 标准化 MCP Server 实现
- ✅ Skill 自动注册和元数据提取
- ✅ CLI skill 管理命令
- ✅ Skill 市场（`marketplace/`）：远程 skill 发现、安装、更新、卸载
- ✅ 版本锁定机制（`lockfile.py`）：锁定 skill 版本防止意外更新
- ✅ Skill 管线编排（`pipeline.py`）：多 skill 串联执行，支持条件分支和错误策略
- ✅ 沙箱执行环境（`sandbox.py`）：进程级资源限制（CPU/内存）
- ✅ Skill 脚手架命令（`hos skill init`）：快速创建 skill 模板

### 迁移的功能

| 原 OpenHands 功能 | 新实现 | 位置 |
|------------------|--------|------|
| Agent 能力 | 独立 Skill | `hosforge/skills/` |
| Sandbox 集成 | 可选 Adapter | `hosforge/adapters/` |
| 工具调用 | MCP Tools | `hosforge/mcp_server/` |
| CLI 命令 | Skill 管理命令 | `hosforge/cli/` |

## 迁移指南

### 对于用户

1. **无需修改现有工作流**
   - `hos taskflow` 命令保持兼容
   - 现有 YAML 工作流继续可用

2. **使用新 Skill 命令**
   ```bash
   # 列出可用 skills
   hos skill list
   
   # 查看 skill 详情
   hos skill info nuclei_scan
   
   # 运行 skill
   hos skill run nuclei_scan target=https://example.com
   ```

3. **IDE 集成**
   - VSCode: 通过命令面板或快捷键调用
   - Cursor: 使用 @mention 引用 skill
   - Claude Code: 使用 `/hos-scan` 等斜杠命令

### 对于开发者

1. **创建新 Skill**
   ```python
   from hosforge.skills import Skill, SkillResult
   
   class MyCustomSkill(Skill):
       name = "my_skill"
       description = "自定义 skill"
       parameters = {
           "type": "object",
           "properties": {
               "input": {"type": "string"}
           }
       }
       
       def execute(self, **kwargs) -> SkillResult:
           # 实现逻辑
           return SkillResult(success=True, data={...})
   ```

2. **注册 Skill**
   ```python
   from hosforge.skills import SkillRegistry
   
   registry = SkillRegistry()
   registry.register(MyCustomSkill())
   ```

3. **创建 IDE 适配器**
   ```python
   from hosforge.adapters import IDEAdapter
   
   class MyIDEAdapter(IDEAdapter):
       def format_input(self, command, args):
           # 转换为内部格式
           pass
       
       def format_output(self, result):
           # 转换为 IDE 兼容格式
           pass
   ```

## 验证清单

- [x] 所有 OpenHands 代码引用已移除
- [x] `openhands/` 目录已删除
- [x] 依赖列表已清理
- [x] Skill 抽象层完整实现
- [x] IDE 适配器框架可用
- [x] MCP Server 正常运行
- [x] CLI 命令功能完整
- [x] 单元测试全部通过

## 总结

HOS-Forge 已成功从 OpenHands 迁移到独立的 Skill+插件架构，实现了：
- **平台无关**：不再依赖特定 AI 平台
- **高度兼容**：支持任意 AI IDE 调用
- **易于扩展**：标准化接口便于添加新 skill 和适配器
- **保持兼容**：现有工作流继续可用

迁移后的架构更加灵活、可维护，为未来发展奠定了坚实基础。
