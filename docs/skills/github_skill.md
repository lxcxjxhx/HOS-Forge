# GitHubIntegrationSkill

GitHub 集成操作的 Skill，通过 gh CLI 工具执行 GitHub API 操作。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [参数说明](#参数说明)
- [支持的操作](#支持的操作)
- [使用示例](#使用示例)
- [返回格式](#返回格式)
- [错误处理](#错误处理)
- [常见问题](#常见问题)

## 概述

`GitHubIntegrationSkill` 封装了 [GitHub CLI](https://cli.github.com/) 工具，提供 GitHub API 的常用操作，包括创建 Issue、创建 Pull Request 和列出 Issue 等功能。

### 功能特性

- 创建 GitHub Issue
- 创建 Pull Request
- 列出 GitHub Issue
- 支持标签管理
- 支持状态过滤

## 前置要求

### 安装 GitHub CLI

```bash
# macOS
brew install gh

# Windows
winget install GitHub.cli

# Linux (Debian/Ubuntu)
sudo apt install gh

# 或使用 npm
npm install -g @github-cli/cli
```

### 认证配置

```bash
# 登录 GitHub
gh auth login

# 验证认证状态
gh auth status
```

确保 `gh` 命令在系统 PATH 中可用，且已完成认证。

## 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `action` | string | ✅ | 要执行的 GitHub 操作 |
| `repo` | string | ✅ | GitHub 仓库 (格式: owner/repo) |
| `title` | string | ❌ | Issue 或 PR 的标题 |
| `body` | string | ❌ | Issue 或 PR 的正文内容 |
| `head` | string | ❌ | PR 的源分支 |
| `base` | string | ❌ | PR 的目标分支 |
| `labels` | array | ❌ | Issue 的标签列表 |
| `state` | string | ❌ | 列出 Issue 时的状态过滤 |
| `limit` | integer | ❌ | 列出 Issue 时的最大返回数量 |

### action 可选值

- `create_issue`: 创建 Issue
- `create_pr`: 创建 Pull Request
- `list_issues`: 列出 Issue

### 参数详情

#### repo (必填)

GitHub 仓库标识，格式为 `owner/repo`：
- `facebook/react`
- `microsoft/vscode`
- `my-org/my-repo`

#### state (可选)

列出 Issue 时的状态过滤，可选值：
- `open`: 开放的 Issue（默认）
- `closed`: 已关闭的 Issue
- `all`: 所有 Issue

#### limit (可选)

列出 Issue 时的最大返回数量，默认 30。

## 支持的操作

### 1. 创建 Issue (create_issue)

**必需参数**:
- `action`: "create_issue"
- `repo`: 仓库标识
- `title`: Issue 标题

**可选参数**:
- `body`: Issue 正文
- `labels`: 标签列表

### 2. 创建 Pull Request (create_pr)

**必需参数**:
- `action`: "create_pr"
- `repo`: 仓库标识
- `title`: PR 标题
- `head`: 源分支

**可选参数**:
- `body`: PR 正文
- `base`: 目标分支（默认为仓库默认分支）

### 3. 列出 Issue (list_issues)

**必需参数**:
- `action`: "list_issues"
- `repo`: 仓库标识

**可选参数**:
- `state`: 状态过滤
- `limit`: 返回数量限制

## 使用示例

### CLI 使用

#### 创建 Issue

```bash
# 基础创建
hos skill run github_integration \
  action=create_issue \
  repo=owner/repo \
  title="Bug report"

# 带正文和标签
hos skill run github_integration \
  action=create_issue \
  repo=owner/repo \
  title="Feature request" \
  body="详细描述..." \
  labels='["enhancement", "priority:high"]'
```

#### 创建 Pull Request

```bash
# 基础创建
hos skill run github_integration \
  action=create_pr \
  repo=owner/repo \
  title="Fix bug" \
  head=feature-branch

# 指定目标分支
hos skill run github_integration \
  action=create_pr \
  repo=owner/repo \
  title="Add feature" \
  head=feature-branch \
  base=develop \
  body="PR 描述..."
```

#### 列出 Issue

```bash
# 列出开放的 Issue
hos skill run github_integration \
  action=list_issues \
  repo=owner/repo

# 列出已关闭的 Issue
hos skill run github_integration \
  action=list_issues \
  repo=owner/repo \
  state=closed

# 限制返回数量
hos skill run github_integration \
  action=list_issues \
  repo=owner/repo \
  limit=10
```

### Python API 使用

```python
from hosforge.skills.security import GitHubIntegrationSkill

skill = GitHubIntegrationSkill()

# 创建 Issue
result = skill.execute(
    action="create_issue",
    repo="owner/repo",
    title="Bug report",
    body="Bug 详细描述",
    labels=["bug", "priority:high"]
)
print(f"Issue 创建成功: {result['output']}")

# 列出 Issue
result = skill.execute(
    action="list_issues",
    repo="owner/repo",
    state="open",
    limit=10
)
print(f"共 {result['total']} 个 Issue")
for issue in result["issues"]:
    print(f"- #{issue['number']}: {issue['title']}")
```

### MCP Server 使用

```bash
curl -X POST http://localhost:8000/tools/github_integration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "action": "list_issues",
      "repo": "owner/repo",
      "state": "open"
    }
  }'
```

## 返回格式

### 创建 Issue 响应

```json
{
  "action": "create_issue",
  "repo": "owner/repo",
  "output": "https://github.com/owner/repo/issues/123"
}
```

### 创建 PR 响应

```json
{
  "action": "create_pr",
  "repo": "owner/repo",
  "output": "https://github.com/owner/repo/pull/456"
}
```

### 列出 Issue 响应

```json
{
  "action": "list_issues",
  "repo": "owner/repo",
  "issues": [
    {
      "number": 123,
      "title": "Bug report",
      "state": "open",
      "labels": [
        {"name": "bug"},
        {"name": "priority:high"}
      ],
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

## 错误处理

### 常见错误

#### 1. GitHub CLI 未安装

```
FileNotFoundError: gh 命令未找到，请确认已安装 GitHub CLI 并加入 PATH
```

**解决方案**: 安装 GitHub CLI 并确保其在系统 PATH 中。

#### 2. 未认证

```
subprocess.CalledProcessError: 命令返回非零退出码
```

**解决方案**: 运行 `gh auth login` 完成认证。

#### 3. 仓库不存在或无权限

```
subprocess.CalledProcessError: HTTP 404
```

**解决方案**: 
- 确认仓库路径正确
- 确认有访问权限
- 检查认证状态

#### 4. 缺少必要参数

```
ValueError: 创建 Issue 需要提供 title 参数
```

**解决方案**: 根据操作类型提供所有必需参数。

### 异常处理示例

```python
from hosforge.skills.security import GitHubIntegrationSkill
import subprocess

skill = GitHubIntegrationSkill()

try:
    result = skill.execute(
        action="create_issue",
        repo="owner/repo",
        title="Test Issue"
    )
    print(f"Issue 创建成功: {result['output']}")
    
except FileNotFoundError as e:
    print(f"GitHub CLI 未安装: {e}")
except ValueError as e:
    print(f"参数错误: {e}")
except subprocess.CalledProcessError as e:
    print(f"GitHub API 错误: {e.stderr}")
```

## 常见问题

### Q: 如何查看 gh CLI 的认证状态？

A: 运行以下命令：

```bash
gh auth status
```

### Q: 支持哪些 GitHub 操作？

A: 当前支持：
- 创建 Issue
- 创建 Pull Request
- 列出 Issue

更多操作可以通过扩展 Skill 实现，或直接使用 `gh` 命令。

### Q: 如何添加更多标签？

A: 使用 JSON 数组格式：

```bash
labels='["bug", "enhancement", "priority:high"]'
```

### Q: 创建 PR 时 head 和 base 有什么区别？

A: 
- `head`: 源分支，即你要合并的分支
- `base`: 目标分支，即你要合并到的分支（默认为仓库的默认分支）

### Q: 如何查看 Issue 的详细信息？

A: 使用 `list_issues` 操作会返回 Issue 的 JSON 数据，包含：
- `number`: Issue 编号
- `title`: 标题
- `state`: 状态
- `labels`: 标签
- `createdAt`: 创建时间

### Q: 是否支持评论、分配等操作？

A: 当前版本不支持，但可以通过以下方式扩展：
1. 修改 `GitHubIntegrationSkill` 添加新操作
2. 直接使用 `gh` 命令：`gh issue comment <number>`

## 相关资源

- [GitHub CLI 文档](https://cli.github.com/manual/)
- [GitHub API 文档](https://docs.github.com/en/rest)
- [gh 命令参考](https://cli.github.com/manual/gh)
- [Skill 系统文档](README.md)
- [自定义 Skill 开发](custom_skill.md)
