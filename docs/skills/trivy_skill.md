# TrivyScanSkill

使用 Trivy 进行漏洞扫描的 Skill。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [参数说明](#参数说明)
- [使用示例](#使用示例)
- [返回格式](#返回格式)
- [错误处理](#错误处理)
- [常见问题](#常见问题)

## 概述

`TrivyScanSkill` 封装了 [Trivy](https://github.com/aquasecurity/trivy) 漏洞扫描工具，支持对容器镜像、文件系统和代码仓库进行安全扫描，解析 JSON 格式输出并返回结构化的漏洞列表。

### 功能特性

- 支持多种扫描类型（镜像、文件系统、仓库）
- 自动检测容器镜像漏洞
- 支持 IaC（基础设施即代码）扫描
- 支持严重级别过滤
- 结构化的漏洞结果

## 前置要求

### 安装 Trivy

```bash
# 使用 Go 安装
go install github.com/aquasecurity/trivy/cmd/trivy@latest

# 或使用 Homebrew (macOS)
brew install trivy

# 或使用 Docker
docker pull aquasec/trivy
```

### 验证安装

```bash
trivy --version
```

确保 `trivy` 命令在系统 PATH 中可用。

## 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `target` | string | ✅ | 扫描目标（镜像名、文件路径或仓库地址） |
| `scan_type` | string | ❌ | 扫描类型：image, fs, repo（默认：image） |
| `severity` | string | ❌ | 过滤严重级别（UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL） |

### 参数详情

#### target (必填)

扫描的目标，根据 `scan_type` 不同可以是：
- **image**: Docker 镜像名称（如 `nginx:latest`、`python:3.10`）
- **fs**: 文件系统路径（如 `./my-project`）
- **repo**: Git 仓库地址（如 `https://github.com/user/repo`）

#### scan_type (可选)

指定扫描类型，默认为 `image`：
- `image`: 扫描容器镜像
- `fs`: 扫描本地文件系统
- `repo`: 扫描远程 Git 仓库

#### severity (可选)

按严重级别过滤结果，可选值：
- `UNKNOWN`: 未知
- `LOW`: 低危
- `MEDIUM`: 中危
- `HIGH`: 高危
- `CRITICAL`: 严重

可以组合多个级别，如 `HIGH,CRITICAL`。

## 使用示例

### CLI 使用

```bash
# 扫描容器镜像
hos skill run trivy_scan target=nginx:latest

# 扫描文件系统
hos skill run trivy_scan target=./my-project scan_type=fs

# 扫描 Git 仓库
hos skill run trivy_scan target=https://github.com/user/repo scan_type=repo

# 只扫描高危和严重漏洞
hos skill run trivy_scan target=nginx:latest severity=HIGH,CRITICAL
```

### Python API 使用

```python
from hosforge.skills.security import TrivyScanSkill

# 创建 Skill 实例
skill = TrivyScanSkill()

# 扫描容器镜像
result = skill.execute(target="nginx:latest")

# 处理结果
print(f"发现 {result['total']} 个漏洞")
for vuln in result["vulnerabilities"]:
    print(f"- {vuln.get('VulnerabilityID')}: {vuln.get('Title')}")
```

### MCP Server 使用

```bash
curl -X POST http://localhost:8000/tools/trivy_scan/execute \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "target": "nginx:latest",
      "scan_type": "image",
      "severity": "HIGH,CRITICAL"
    }
  }'
```

## 返回格式

### 成功响应

```json
{
  "vulnerabilities": [
    {
      "VulnerabilityID": "CVE-2021-44228",
      "PkgName": "log4j-core",
      "InstalledVersion": "2.14.1",
      "FixedVersion": "2.15.0",
      "Severity": "CRITICAL",
      "Title": "Apache Log4j2 远程代码执行漏洞",
      "Description": "Apache Log4j2 <=2.14.1 JNDI features...",
      "References": [
        "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"
      ]
    }
  ],
  "total": 1,
  "target": "nginx:latest",
  "scan_type": "image"
}
```

### 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `vulnerabilities` | array | 扫描发现的漏洞列表 |
| `total` | integer | 发现的漏洞总数 |
| `target` | string | 扫描的目标 |
| `scan_type` | string | 使用的扫描类型 |

### vulnerabilities 数组元素结构

每个漏洞对象包含以下主要字段：

- `VulnerabilityID`: CVE 编号
- `PkgName`: 受影响的包名
- `InstalledVersion`: 已安装版本
- `FixedVersion`: 修复版本（如果有）
- `Severity`: 严重级别
- `Title`: 漏洞标题
- `Description`: 漏洞描述
- `References`: 参考资料链接

## 错误处理

### 常见错误

#### 1. Trivy 未安装

```
FileNotFoundError: trivy 命令未找到，请确认已安装 trivy 并加入 PATH
```

**解决方案**: 安装 Trivy 并确保其在系统 PATH 中。

#### 2. 镜像不存在

```
subprocess.CalledProcessError: 命令返回非零退出码
```

**解决方案**: 确认镜像名称正确，或先使用 `docker pull` 拉取镜像。

#### 3. 扫描超时

Trivy 默认设置 600 秒（10 分钟）超时。对于大型镜像或仓库，可能需要更长时间。

### 异常处理示例

```python
from hosforge.skills.security import TrivyScanSkill
import subprocess

skill = TrivyScanSkill()

try:
    result = skill.execute(target="nginx:latest")
    print(f"发现 {result['total']} 个漏洞")
except FileNotFoundError as e:
    print(f"工具未安装: {e}")
except subprocess.TimeoutExpired:
    print("扫描超时")
except subprocess.CalledProcessError as e:
    print(f"扫描失败: {e}")
```

## 常见问题

### Q: 扫描超时怎么办？

A: TrivyScanSkill 默认设置 600 秒超时。对于大型目标，可以考虑：
- 使用严重级别过滤减少扫描范围
- 先拉取镜像到本地再扫描
- 使用 `--timeout` 参数调整超时时间（需修改源码）

### Q: 如何扫描私有镜像仓库？

A: 需要先登录到私有仓库：

```bash
docker login registry.example.com
trivy image registry.example.com/myimage:tag
```

### Q: 如何忽略特定漏洞？

A: 可以使用 `.trivyignore` 文件：

```bash
# 在项目根目录创建 .trivyignore
CVE-2021-44228
CVE-2021-45046
```

### Q: 支持哪些包管理器？

A: Trivy 支持多种包管理器和锁文件：
- npm/yarn (package-lock.json, yarn.lock)
- pip (requirements.txt, Pipfile.lock)
- Maven (pom.xml)
- Gradle (build.gradle)
- Go (go.sum)
- Rust (Cargo.lock)
- 等等

### Q: 如何更新漏洞数据库？

A: Trivy 会自动从 Trivy DB 下载最新的漏洞数据。可以手动更新：

```bash
trivy image --download-db-only
```

## 相关资源

- [Trivy 官方文档](https://aquasecurity.github.io/trivy/)
- [Trivy GitHub 仓库](https://github.com/aquasecurity/trivy)
- [Skill 系统文档](README.md)
- [自定义 Skill 开发](custom_skill.md)
