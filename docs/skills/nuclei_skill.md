# NucleiScanSkill

使用 Nuclei 进行漏洞扫描的 Skill。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [参数说明](#参数说明)
- [使用示例](#使用示例)
- [返回格式](#返回格式)
- [错误处理](#错误处理)
- [常见问题](#常见问题)

## 概述

`NucleiScanSkill` 封装了 [Nuclei](https://github.com/projectdiscovery/nuclei) 漏洞扫描工具，通过调用 nuclei 命令行工具对目标执行漏洞扫描，解析 JSON 格式输出并返回结构化的扫描结果。

### 功能特性

- 支持单目标扫描
- 支持自定义模板
- 支持严重级别过滤
- 自动解析 JSON 输出
- 结构化的扫描结果

## 前置要求

### 安装 Nuclei

```bash
# 使用 Go 安装
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# 或使用 Homebrew (macOS)
brew install nuclei

# 或使用 Docker
docker pull projectdiscovery/nuclei
```

### 验证安装

```bash
nuclei -version
```

确保 `nuclei` 命令在系统 PATH 中可用。

## 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `target` | string | ✅ | 扫描目标 URL 或 IP |
| `templates` | array | ❌ | 要使用的 nuclei 模板列表 |
| `severity` | string | ❌ | 过滤严重级别 (info, low, medium, high, critical) |

### 参数详情

#### target (必填)

扫描的目标地址，可以是：
- URL: `https://example.com`
- IP 地址: `192.168.1.1`
- 域名: `example.com`

#### templates (可选)

指定要使用的 Nuclei 模板列表。如果不指定，将使用 Nuclei 的默认模板。

```python
templates=["cves/2021/CVE-2021-44228.yaml"]
```

#### severity (可选)

按严重级别过滤结果，可选值：
- `info`: 信息级别
- `low`: 低危
- `medium`: 中危
- `high`: 高危
- `critical`: 严重

## 使用示例

### CLI 使用

```bash
# 基础扫描
hos skill run nuclei_scan target=https://example.com

# 指定严重级别
hos skill run nuclei_scan target=https://example.com severity=high

# 使用特定模板
hos skill run nuclei_scan target=https://example.com templates='["cves/2021/CVE-2021-44228.yaml"]'
```

### Python API 使用

```python
from hosforge.skills.security import NucleiScanSkill

# 创建 Skill 实例
skill = NucleiScanSkill()

# 执行扫描
result = skill.execute(target="https://example.com")

# 处理结果
if result["total"] > 0:
    print(f"发现 {result['total']} 个问题")
    for finding in result["findings"]:
        print(f"- {finding.get('info', {}).get('name', 'Unknown')}")
```

### MCP Server 使用

```bash
curl -X POST http://localhost:8000/tools/nuclei_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "target": "https://example.com",
      "severity": "high"
    }
  }'
```

## 返回格式

### 成功响应

```json
{
  "findings": [
    {
      "templateID": "CVE-2021-44228",
      "info": {
        "name": "Log4Shell",
        "severity": "critical",
        "description": "Apache Log4j2 <=2.14.1 JNDI features..."
      },
      "host": "https://example.com",
      "matchedAt": "https://example.com/api",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "target": "https://example.com"
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `findings` | array | 扫描发现的安全问题列表 |
| `total` | integer | 发现的问题总数 |
| `target` | string | 扫描的目标地址 |

### findings 数组元素结构

每个 finding 包含 Nuclei 输出的完整 JSON 对象，主要字段包括：

- `templateID`: 模板 ID
- `info`: 漏洞信息对象
  - `name`: 漏洞名称
  - `severity`: 严重级别
  - `description`: 描述
- `host`: 目标主机
- `matchedAt`: 匹配的具体位置
- `timestamp`: 发现时间

## 错误处理

### 常见错误

#### 1. Nuclei 未安装

```
FileNotFoundError: nuclei 命令未找到，请确认已安装 nuclei 并加入 PATH
```

**解决方案**: 安装 Nuclei 并确保其在系统 PATH 中。

#### 2. 目标不可达

扫描可能超时或返回空结果。建议：
- 检查目标是否可访问
- 增加超时时间
- 检查网络连接

#### 3. 模板不存在

```
subprocess.CalledProcessError: 命令返回非零退出码
```

**解决方案**: 确认模板路径正确，可使用 `nuclei -tl` 列出可用模板。

### 异常处理示例

```python
from hosforge.skills.security import NucleiScanSkill
import subprocess

skill = NucleiScanSkill()

try:
    result = skill.execute(target="https://example.com")
    print(f"发现 {result['total']} 个问题")
except FileNotFoundError as e:
    print(f"工具未安装: {e}")
except subprocess.TimeoutExpired:
    print("扫描超时")
except subprocess.CalledProcessError as e:
    print(f"扫描失败: {e}")
```

## 常见问题

### Q: 扫描超时怎么办？

A: NucleiScanSkill 默认设置 600 秒（10 分钟）超时。对于大型目标，可以考虑：
- 使用更精确的模板
- 使用严重级别过滤
- 分批扫描多个小目标

### Q: 如何使用自定义模板？

A: 将模板文件放在 Nuclei 可访问的目录，然后通过 `templates` 参数指定：

```bash
hos skill run nuclei_scan \
  target=https://example.com \
  templates='["/path/to/custom/template.yaml"]'
```

### Q: 扫描结果不完整？

A: 可能的原因：
1. 目标有防护机制（WAF、限流等）
2. 模板不匹配目标技术栈
3. 网络问题导致部分请求失败

建议检查 Nuclei 的详细日志输出。

### Q: 如何更新 Nuclei 模板？

A: 运行以下命令更新模板：

```bash
nuclei -update-templates
```

### Q: 支持并发扫描吗？

A: Nuclei 本身支持并发，可以通过环境变量或配置文件调整：

```bash
# 设置并发度
nuclei -target https://example.com -c 50
```

当前 Skill 封装使用默认并发设置，如需自定义可修改源码。

## 相关资源

- [Nuclei 官方文档](https://nuclei.projectdiscovery.io/)
- [Nuclei 模板仓库](https://github.com/projectdiscovery/nuclei-templates)
- [Skill 系统文档](README.md)
- [自定义 Skill 开发](custom_skill.md)
