# CodeQLScanSkill

使用 CodeQL 进行安全分析的 Skill。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [参数说明](#参数说明)
- [使用示例](#使用示例)
- [返回格式](#返回格式)
- [错误处理](#错误处理)
- [常见问题](#常见问题)

## 概述

`CodeQLScanSkill` 封装了 [CodeQL](https://codeql.github.com/) 安全分析工具，通过执行 CodeQL 查询对代码数据库进行静态分析，解析 SARIF 格式输出并返回结构化的安全告警列表。

### 功能特性

- 支持多种编程语言的代码分析
- 使用 CodeQL 查询套件进行安全检测
- 支持自定义查询
- SARIF 格式标准化输出
- 结构化的告警结果

## 前置要求

### 安装 CodeQL CLI

```bash
# 下载 CodeQL CLI
# 访问 https://github.com/github/codeql-cli-binaries/releases
# 下载对应平台的版本

# 或使用 GitHub CLI
gh release download --repo github/codeql-cli-binaries --pattern 'codeql-*-bundle.zip'
```

### 验证安装

```bash
codeql --version
```

确保 `codeql` 命令在系统 PATH 中可用。

### 创建 CodeQL 数据库

在使用 CodeQL 分析之前，需要先创建代码数据库：

```bash
# 为 JavaScript 项目创建数据库
codeql database create my-database --language=javascript --source-root=./my-project

# 为 Python 项目创建数据库
codeql database create my-database --language=python --source-root=./my-project

# 为 Java 项目创建数据库
codeql database create my-database --language=java --source-root=./my-project
```

## 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `database` | string | ✅ | CodeQL 数据库路径 |
| `query_suite` | string | ❌ | 查询套件路径或名称（如 security-extended） |
| `language` | string | ❌ | 查询语言（如 javascript, python, java） |

### 参数详情

#### database (必填)

CodeQL 数据库的路径，该数据库需要通过 `codeql database create` 命令预先创建。

```bash
codeql database create ./my-database --language=javascript --source-root=./my-project
```

#### query_suite (可选)

指定要执行的查询套件。如果不指定，将使用默认的安全查询套件。

常用的查询套件：
- `security-extended`: 扩展安全查询
- `security-and-quality`: 安全和质量查询
- 自定义查询套件路径

#### language (可选)

指定查询语言。如果提供了 `language` 但未提供 `query_suite`，将使用 `{language}-security-extended` 查询套件。

支持的语言：
- `javascript` / `typescript`
- `python`
- `java` / `kotlin`
- `cpp` (C/C++)
- `csharp` (C#)
- `go`
- `ruby`
- `swift`

## 使用示例

### CLI 使用

```bash
# 使用默认安全查询
hos skill run codeql_scan database=./my-database

# 指定查询套件
hos skill run codeql_scan database=./my-database query_suite=security-extended

# 指定语言
hos skill run codeql_scan database=./my-database language=javascript
```

### Python API 使用

```python
from hosforge.skills.security import CodeQLScanSkill

# 创建 Skill 实例
skill = CodeQLScanSkill()

# 执行分析
result = skill.execute(
    database="./my-database",
    language="javascript"
)

# 处理结果
print(f"发现 {result['total']} 个告警")
for alert in result["alerts"]:
    print(f"- {alert['rule_id']}: {alert['message']}")
```

### MCP Server 使用

```bash
curl -X POST http://localhost:8000/tools/codeql_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "database": "./my-database",
      "language": "javascript"
    }
  }'
```

## 返回格式

### 成功响应

```json
{
  "alerts": [
    {
      "rule_id": "js/sql-injection",
      "message": "SQL 注入漏洞",
      "level": "error",
      "locations": [
        {
          "physicalLocation": {
            "artifactLocation": {
              "uri": "src/database.js"
            },
            "region": {
              "startLine": 42,
              "startColumn": 10
            }
          }
        }
      ]
    }
  ],
  "total": 1,
  "database": "./my-database"
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `alerts` | array | 扫描发现的安全告警列表 |
| `total` | integer | 发现的告警总数 |
| `database` | string | 分析的 CodeQL 数据库路径 |

### alerts 数组元素结构

每个告警对象包含以下字段：

- `rule_id`: 规则 ID（如 `js/sql-injection`）
- `message`: 告警消息
- `level`: 严重级别（error, warning, note）
- `locations`: 告警位置列表，包含文件和行号信息

## 错误处理

### 常见错误

#### 1. CodeQL 未安装

```
FileNotFoundError: codeql 命令未找到，请确认已安装 codeql 并加入 PATH
```

**解决方案**: 安装 CodeQL CLI 并确保其在系统 PATH 中。

#### 2. 数据库不存在

```
subprocess.CalledProcessError: 命令返回非零退出码
```

**解决方案**: 确认数据库路径正确，且数据库已成功创建。

#### 3. 分析超时

CodeQL 默认设置 1800 秒（30 分钟）超时。对于大型项目，可能需要更长时间。

### 异常处理示例

```python
from hosforge.skills.security import CodeQLScanSkill
import subprocess

skill = CodeQLScanSkill()

try:
    result = skill.execute(database="./my-database")
    print(f"发现 {result['total']} 个告警")
except FileNotFoundError as e:
    print(f"工具未安装: {e}")
except subprocess.TimeoutExpired:
    print("分析超时")
except subprocess.CalledProcessError as e:
    print(f"分析失败: {e}")
```

## 常见问题

### Q: 如何创建 CodeQL 数据库？

A: 使用 `codeql database create` 命令：

```bash
# 为 JavaScript 项目
codeql database create ./my-database --language=javascript --source-root=./my-project

# 为 Python 项目
codeql database create ./my-database --language=python --source-root=./my-project
```

### Q: 支持哪些编程语言？

A: CodeQL 支持以下语言：
- JavaScript / TypeScript
- Python
- Java / Kotlin
- C / C++
- C#
- Go
- Ruby
- Swift

### Q: 如何使用自定义查询？

A: 可以指定自定义查询文件路径：

```bash
hos skill run codeql_scan \
  database=./my-database \
  query_suite=/path/to/custom-query.ql
```

### Q: 分析超时怎么办？

A: CodeQLScanSkill 默认设置 1800 秒超时。对于大型项目，可以：
- 使用更精确的查询套件
- 只分析特定目录
- 增加超时时间（需修改源码）

### Q: 如何查看可用的查询套件？

A: 使用以下命令列出可用的查询套件：

```bash
codeql resolve qlpacks
codeql resolve queries
```

### Q: SARIF 格式是什么？

A: SARIF（Static Analysis Results Interchange Format）是静态分析结果交换格式的标准，被许多工具支持。CodeQL 使用 SARIF 格式输出分析结果，便于与其他工具集成。

## 相关资源

- [CodeQL 官方文档](https://codeql.github.com/docs/)
- [CodeQL CLI 文档](https://docs.github.com/en/code-security/codeql-cli)
- [CodeQL 查询包](https://github.com/github/codeql)
- [SARIF 规范](https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=sarif)
- [Skill 系统文档](README.md)
- [自定义 Skill 开发](custom_skill.md)
