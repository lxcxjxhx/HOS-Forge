# SemgrepScanSkill

使用 Semgrep 进行静态代码分析的 Skill。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [参数说明](#参数说明)
- [使用示例](#使用示例)
- [返回格式](#返回格式)
- [错误处理](#错误处理)
- [常见问题](#常见问题)

## 概述

`SemgrepScanSkill` 封装了 [Semgrep](https://semgrep.dev/) 静态代码分析工具，通过调用 semgrep 命令行工具对指定路径执行代码扫描，解析 JSON 格式输出并返回结构化的分析结果。

### 功能特性

- 支持多语言代码分析
- 支持自定义规则配置
- 自动检测项目语言
- 结构化的分析结果
- 支持文件和目录扫描

## 前置要求

### 安装 Semgrep

```bash
# 使用 pip 安装
pip install semgrep

# 或使用 Homebrew (macOS)
brew install semgrep

# 或使用 Docker
docker pull returntocorp/semgrep
```

### 验证安装

```bash
semgrep --version
```

确保 `semgrep` 命令在系统 PATH 中可用。

## 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `path` | string | ✅ | 要扫描的文件或目录路径 |
| `language` | string | ❌ | 限定扫描的编程语言 |
| `config` | string | ❌ | Semgrep 规则配置 |

### 参数详情

#### path (必填)

要扫描的文件或目录路径，可以是：
- 单个文件: `./src/main.py`
- 目录路径: `./src`
- 相对路径或绝对路径

#### language (可选)

限定扫描的编程语言，常用值：
- `python`
- `javascript`
- `typescript`
- `java`
- `go`
- `rust`
- `ruby`
- `php`

如果不指定，Semgrep 会根据文件扩展名自动检测。

#### config (可选)

Semgrep 规则配置，支持以下格式：
- `auto`: 自动检测并应用推荐规则（默认）
- `p/default`: 使用默认规则集
- `p/security-audit`: 使用安全审计规则集
- `p/owasp-top-ten`: 使用 OWASP Top 10 规则
- 配置文件路径: `/path/to/rules.yaml`
- 规则 ID: `rules.python.security.xxx`

## 使用示例

### CLI 使用

```bash
# 基础扫描（自动检测配置）
hos skill run semgrep_scan path=./src

# 指定语言
hos skill run semgrep_scan path=./src language=python

# 使用特定规则集
hos skill run semgrep_scan path=./src config=p/security-audit

# 组合使用
hos skill run semgrep_scan path=./src language=python config=p/owasp-top-ten
```

### Python API 使用

```python
from hosforge.skills.security import SemgrepScanSkill

# 创建 Skill 实例
skill = SemgrepScanSkill()

# 执行扫描
result = skill.execute(
    path="./src",
    language="python",
    config="p/security-audit"
)

# 处理结果
print(f"发现 {result['total']} 个问题")
for finding in result["findings"]:
    print(f"- {finding['check_id']}: {finding['path']}:{finding['start']['line']}")
```

### MCP Server 使用

```bash
curl -X POST http://localhost:8000/tools/semgrep_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "path": "./src",
      "language": "python",
      "config": "auto"
    }
  }'
```

## 返回格式

### 成功响应

```json
{
  "findings": [
    {
      "check_id": "python.lang.security.audit.eval-detected.eval-detected",
      "path": "src/main.py",
      "start": {
        "line": 42,
        "col": 5
      },
      "end": {
        "line": 42,
        "col": 20
      },
      "extra": {
        "message": "Found use of eval(). This can be dangerous.",
        "severity": "WARNING",
        "metadata": {
          "category": "security",
          "technology": ["python"],
          "owasp": ["A03:2021 - Injection"]
        }
      }
    }
  ],
  "total": 1,
  "errors": [],
  "path": "./src"
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `findings` | array | 扫描发现的问题列表 |
| `total` | integer | 发现的问题总数 |
| `errors` | array | 扫描过程中的错误列表 |
| `path` | string | 扫描的目标路径 |

### findings 数组元素结构

每个 finding 包含以下主要字段：

- `check_id`: 规则 ID
- `path`: 文件路径
- `start`: 起始位置（行号、列号）
- `end`: 结束位置（行号、列号）
- `extra`: 额外信息
  - `message`: 问题描述
  - `severity`: 严重级别 (ERROR, WARNING, INFO)
  - `metadata`: 元数据（类别、技术栈、OWASP 分类等）

## 错误处理

### 常见错误

#### 1. Semgrep 未安装

```
FileNotFoundError: semgrep 命令未找到，请确认已安装 semgrep 并加入 PATH
```

**解决方案**: 安装 Semgrep 并确保其在系统 PATH 中。

#### 2. 路径不存在

```
ValueError: 无法访问指定路径
```

**解决方案**: 确认路径存在且有读取权限。

#### 3. JSON 解析失败

```
ValueError: 无法解析 semgrep JSON 输出
```

**解决方案**: 可能是 Semgrep 版本不兼容，尝试更新 Semgrep。

### 异常处理示例

```python
from hosforge.skills.security import SemgrepScanSkill
import subprocess

skill = SemgrepScanSkill()

try:
    result = skill.execute(path="./src")
    print(f"发现 {result['total']} 个问题")
    
    # 检查是否有错误
    if result["errors"]:
        print(f"扫描过程中出现 {len(result['errors'])} 个错误")
        
except FileNotFoundError as e:
    print(f"工具未安装: {e}")
except subprocess.TimeoutExpired:
    print("扫描超时")
except ValueError as e:
    print(f"参数错误: {e}")
```

## 常见问题

### Q: 扫描大型项目很慢怎么办？

A: 建议：
- 使用 `language` 参数限定扫描范围
- 使用更精确的 `config` 规则集
- 排除不需要扫描的目录（如 `node_modules`、`.git`）

### Q: 如何使用自定义规则？

A: 创建 YAML 格式的规则文件，然后通过 `config` 参数指定：

```yaml
# custom-rules.yaml
rules:
  - id: my-custom-rule
    pattern: eval(...)
    message: "Avoid using eval()"
    severity: WARNING
    languages: [python]
```

```bash
hos skill run semgrep_scan path=./src config=/path/to/custom-rules.yaml
```

### Q: 支持哪些编程语言？

A: Semgrep 支持 30+ 种编程语言，包括：
- Python, JavaScript, TypeScript, Java, Go
- Ruby, PHP, C/C++, Rust, Kotlin
- Scala, Swift, Bash, JSON, YAML 等

完整列表参考 [Semgrep 文档](https://semgrep.dev/docs/supported-languages)。

### Q: 如何忽略特定文件或规则？

A: 在项目根目录创建 `.semgrepignore` 文件：

```
# 忽略目录
node_modules/
.git/
dist/

# 忽略文件
*.min.js
```

或使用 `--exclude` 参数（需要修改 Skill 实现）。

### Q: 扫描结果太多如何过滤？

A: 可以：
1. 使用更严格的 `config` 规则集
2. 按严重级别过滤（需要后处理）
3. 使用 `.semgrepignore` 排除无关文件

```python
# 按严重级别过滤
high_severity = [
    f for f in result["findings"] 
    if f["extra"]["severity"] == "ERROR"
]
```

## 相关资源

- [Semgrep 官方文档](https://semgrep.dev/docs/)
- [Semgrep 规则库](https://semgrep.dev/r)
- [Semgrep CLI 参考](https://semgrep.dev/docs/cli-usage)
- [Skill 系统文档](README.md)
- [自定义 Skill 开发](custom_skill.md)
