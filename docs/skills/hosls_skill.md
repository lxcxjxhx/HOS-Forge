# HOSLSScanSkill

使用 HOS-LS 引擎进行安全扫描的 Skill。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [参数说明](#参数说明)
- [使用示例](#使用示例)
- [返回格式](#返回格式)
- [错误处理](#错误处理)
- [常见问题](#常见问题)

## 概述

`HOSLSScanSkill` 封装了 [HOS-LS](https://github.com/lxcxjxhx/HOS-LS) 安全扫描引擎，通过调用 hos-ls 命令行工具对指定目标执行安全扫描，解析 JSON 格式输出并返回结构化的安全告警列表。

### 功能特性

- 支持多种扫描类型（漏洞、恶意软件、配置）
- 支持严重级别过滤
- 多种输出格式（JSON, SARIF, 文本）
- 结构化的扫描结果

## 前置要求

### 安装 HOS-LS

```bash
# 从源码安装
git clone https://github.com/lxcxjxhx/HOS-LS.git
cd HOS-LS
pip install -e .

# 或使用 pip
pip install hos-ls
```

### 验证安装

```bash
hos-ls --version
```

确保 `hos-ls` 命令在系统 PATH 中可用。

## 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `target` | string | ✅ | 扫描目标（文件路径、目录或 URL） |
| `scan_type` | string | ❌ | 扫描类型（vulnerability, malware, config）（默认：vulnerability） |
| `severity` | string | ❌ | 最低严重级别过滤（critical, high, medium, low） |
| `output_format` | string | ❌ | 输出格式（json, sarif, text）（默认：json） |

### 参数详情

#### target (必填)

扫描的目标，可以是：
- 文件路径：`./config.yaml`
- 目录路径：`./my-project`
- URL：`https://example.com`

#### scan_type (可选)

指定扫描类型，默认为 `vulnerability`：
- `vulnerability`: 漏洞扫描
- `malware`: 恶意软件检测
- `config`: 配置安全检查

#### severity (可选)

按最低严重级别过滤结果，可选值：
- `critical`: 严重
- `high`: 高危
- `medium`: 中危
- `low`: 低危

#### output_format (可选)

指定输出格式，默认为 `json`：
- `json`: JSON 格式
- `sarif`: SARIF 格式
- `text`: 文本格式

## 使用示例

### CLI 使用

```bash
# 基础漏洞扫描
hos skill run hosls_scan target=./my-project

# 恶意软件检测
hos skill run hosls_scan target=./my-project scan_type=malware

# 配置安全检查
hos skill run hosls_scan target=./config.yaml scan_type=config

# 只扫描高危和严重漏洞
hos skill run hosls_scan target=./my-project severity=high

# 使用 SARIF 格式输出
hos skill run hosls_scan target=./my-project output_format=sarif
```

### Python API 使用

```python
from hosforge.skills.security import HOSLSScanSkill

# 创建 Skill 实例
skill = HOSLSScanSkill()

# 执行扫描
result = skill.execute(
    target="./my-project",
    scan_type="vulnerability",
    severity="high"
)

# 处理结果
print(f"发现 {result['total']} 个问题")
for alert in result["alerts"]:
    print(f"- {alert['rule_id']}: {alert['message']}")
```

### MCP Server 使用

```bash
curl -X POST http://localhost:8000/tools/hosls_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "target": "./my-project",
      "scan_type": "vulnerability",
      "severity": "high"
    }
  }'
```

## 返回格式

### 成功响应

```json
{
  "alerts": [
    {
      "rule_id": "HOS-001",
      "message": "发现硬编码密码",
      "severity": "high",
      "location": {
        "file": "config/settings.py",
        "line": 42
      },
      "description": "在配置文件中发现了硬编码的密码，建议使用环境变量或密钥管理服务"
    }
  ],
  "total": 1,
  "target": "./my-project",
  "scan_type": "vulnerability"
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `alerts` | array | 扫描发现的安全告警列表 |
| `total` | integer | 发现的告警总数 |
| `target` | string | 扫描的目标 |
| `scan_type` | string | 使用的扫描类型 |

### alerts 数组元素结构

每个告警对象包含以下字段：

- `rule_id`: 规则 ID
- `message`: 告警消息
- `severity`: 严重级别
- `location`: 告警位置（文件和行号）
- `description`: 详细描述

## 错误处理

### 常见错误

#### 1. HOS-LS 未安装

```
FileNotFoundError: hos-ls 命令未找到，请确认已安装 hos-ls 并加入 PATH
```

**解决方案**: 安装 HOS-LS 并确保其在系统 PATH 中。

#### 2. 目标不存在

```
subprocess.CalledProcessError: 命令返回非零退出码
```

**解决方案**: 确认目标路径或 URL 正确且可访问。

#### 3. 扫描超时

HOSLSScanSkill 默认设置 600 秒（10 分钟）超时。对于大型项目，可能需要更长时间。

### 异常处理示例

```python
from hosforge.skills.security import HOSLSScanSkill
import subprocess

skill = HOSLSScanSkill()

try:
    result = skill.execute(target="./my-project")
    print(f"发现 {result['total']} 个问题")
except FileNotFoundError as e:
    print(f"工具未安装: {e}")
except subprocess.TimeoutExpired:
    print("扫描超时")
except subprocess.CalledProcessError as e:
    print(f"扫描失败: {e}")
```

## 常见问题

### Q: HOS-LS 支持哪些扫描类型？

A: HOS-LS 支持三种主要扫描类型：
- **vulnerability**: 漏洞扫描，检测代码中的安全漏洞
- **malware**: 恶意软件检测，识别潜在的恶意代码
- **config**: 配置安全检查，验证配置文件的安全性

### Q: 如何自定义扫描规则？

A: HOS-LS 支持自定义规则文件。可以在项目根目录创建 `.hosls-rules.yaml` 文件定义自定义规则。

### Q: 扫描超时怎么办？

A: HOSLSScanSkill 默认设置 600 秒超时。对于大型项目，可以：
- 使用更精确的扫描类型
- 使用严重级别过滤减少扫描范围
- 增加超时时间（需修改源码）

### Q: 如何忽略特定告警？

A: 可以使用 `.hosls-ignore` 文件：

```bash
# 在项目根目录创建 .hosls-ignore
HOS-001
HOS-002
```

### Q: SARIF 格式输出如何使用？

A: 使用 `output_format=sarif` 参数：

```bash
hos skill run hosls_scan target=./my-project output_format=sarif
```

SARIF 格式可以被许多 IDE 和安全工具解析，便于集成到 CI/CD 流程中。

### Q: HOS-LS 与其他工具的区别？

A: HOS-LS 是一个综合性的安全扫描引擎，结合了多种扫描能力：
- 漏洞扫描：类似 Semgrep、CodeQL
- 恶意软件检测：类似 ClamAV
- 配置安全检查：类似 Checkov、Terrascan

## 相关资源

- [HOS-LS GitHub 仓库](https://github.com/lxcxjxhx/HOS-LS)
- [HOS-LS 文档](https://github.com/lxcxjxhx/HOS-LS#readme)
- [Skill 系统文档](README.md)
- [自定义 Skill 开发](custom_skill.md)
