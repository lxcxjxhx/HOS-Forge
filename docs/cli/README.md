# CLI 使用指南

HOS-Forge 提供功能丰富的命令行界面（CLI），用于管理 Skills、执行安全扫描和查看系统状态。

## 目录

- [概述](#概述)
- [安装](#安装)
- [基本命令](#基本命令)
- [Skill 管理](#skill-管理)
- [扫描命令](#扫描命令)
- [配置选项](#配置选项)
- [输出格式](#输出格式)
- [高级用法](#高级用法)
- [常见问题](#常见问题)

## 概述

HOS-Forge CLI 是一个统一的命令行工具，提供以下功能：

- 列出和查看可用的 Skills
- 执行安全扫描任务
- 管理 Skill 配置
- 查看系统状态和日志

### 命令结构

```bash
hos <command> <subcommand> [options]
```

## 安装

### 验证安装

```bash
hos --version
```

### 更新 CLI

```bash
pip install --upgrade hosforge
```

## 基本命令

### 查看版本

```bash
hos --version
```

### 显示帮助

```bash
hos --help
hos <command> --help
```

### 查看系统状态

```bash
hos status
```

输出示例：

```
HOS-Forge Status
================
Version: 1.0.0
Python: 3.12.0
Skills Loaded: 5
MCP Server: Running (port 8321)
```

## Skill 管理

### 列出所有 Skills

```bash
hos skill list
```

输出示例：

```
Available Skills
================
1. nuclei_scan      - 使用 Nuclei 进行漏洞扫描
2. semgrep_scan     - 使用 Semgrep 进行静态代码分析
3. github_scan      - GitHub API 操作集成
4. trivy_scan       - 使用 Trivy 进行漏洞扫描
5. codeql_scan      - 使用 CodeQL 进行安全分析
```

### 查看 Skill 详情

```bash
hos skill info <skill_name>
```

示例：

```bash
hos skill info nuclei_scan
```

输出示例：

```
Skill: nuclei_scan
==================
Description: 使用 Nuclei 进行漏洞扫描
Version: 1.0.0
Author: HOS-Forge Team

Parameters:
  - target (required): 扫描目标 URL 或 IP
  - templates (optional): Nuclei 模板列表
  - severity (optional): 严重级别过滤

Examples:
  hos skill run nuclei_scan target=https://example.com
  hos skill run nuclei_scan target=https://example.com severity=high
```

### 执行 Skill

```bash
hos skill run <skill_name> [param1=value1] [param2=value2] ...
```

示例：

```bash
# 基础扫描
hos skill run nuclei_scan target=https://example.com

# 带参数扫描
hos skill run nuclei_scan target=https://example.com severity=high

# 多参数
hos skill run trivy_scan target=nginx:latest scan_type=image severity=HIGH,CRITICAL
```

## 扫描命令

### 快速扫描

提供常用扫描工具的快捷命令：

```bash
# Nuclei 漏洞扫描
hos scan nuclei --target https://example.com

# Semgrep 代码分析
hos scan semgrep --target ./my-project

# Trivy 镜像扫描
hos scan trivy --target nginx:latest

# CodeQL 安全分析
hos scan codeql --database ./my-database
```

### 扫描选项

所有扫描命令支持以下通用选项：

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--output`, `-o` | 输出文件路径 | stdout |
| `--format`, `-f` | 输出格式 (json, text, sarif) | json |
| `--severity`, `-s` | 严重级别过滤 | all |
| `--timeout`, `-t` | 超时时间（秒） | 600 |
| `--verbose`, `-v` | 详细输出 | false |

示例：

```bash
hos scan nuclei --target https://example.com \
  --output report.json \
  --format json \
  --severity high \
  --timeout 300
```

## 配置选项

### 全局配置

```bash
# 设置默认输出格式
hos config set output.format json

# 设置 MCP Server 端口
hos config set mcp.port 8321

# 设置日志级别
hos config set log.level INFO
```

### 查看配置

```bash
# 查看所有配置
hos config list

# 查看特定配置
hos config get output.format
```

### 配置文件位置

配置文件存储在：

- Linux/macOS: `~/.config/hosforge/config.yaml`
- Windows: `%APPDATA%\hosforge\config.yaml`

## 输出格式

### JSON 格式（默认）

```bash
hos skill run nuclei_scan target=https://example.com --format json
```

输出：

```json
{
  "success": true,
  "data": {
    "findings": [],
    "total": 0,
    "target": "https://example.com"
  },
  "metadata": {
    "duration": 12.5,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 文本格式

```bash
hos skill run nuclei_scan target=https://example.com --format text
```

输出：

```
Scan Results for https://example.com
=====================================
Total Findings: 0
Duration: 12.5s
Status: Success

No vulnerabilities found.
```

### SARIF 格式

```bash
hos skill run nuclei_scan target=https://example.com --format sarif
```

输出符合 SARIF 规范的 JSON，可导入其他安全工具。

## 高级用法

### 批量执行

创建任务列表文件 `tasks.txt`：

```
nuclei_scan target=https://example1.com
nuclei_scan target=https://example2.com
semgrep_scan target=./project1
semgrep_scan target=./project2
```

批量执行：

```bash
hos batch run tasks.txt --output results.json
```

### 管道集成

```bash
# 与其他工具集成
hos skill run nuclei_scan target=https://example.com --format json | jq '.data.findings'

# 导出到文件
hos scan nuclei --target https://example.com --format sarif > report.sarif

# 结合 grep 过滤
hos skill run nuclei_scan target=https://example.com --format text | grep "HIGH"
```

### 环境变量

```bash
# 设置 MCP Server 地址
export HOS_MCP_URL=http://localhost:8321

# 设置默认输出格式
export HOS_OUTPUT_FORMAT=json

# 设置日志级别
export HOS_LOG_LEVEL=DEBUG
```

### 脚本集成

```bash
#!/bin/bash

# 自动化扫描脚本
TARGETS=("https://example1.com" "https://example2.com")

for target in "${TARGETS[@]}"; do
    echo "Scanning $target..."
    hos scan nuclei --target "$target" --output "report_$(date +%s).json"
done

echo "All scans completed!"
```

## 常见问题

### Q: 命令未找到

```
Command 'hos' not found
```

**解决方案**:

```bash
# 重新安装
pip install -e .

# 检查 PATH
echo $PATH
```

### Q: 权限错误

```
Permission denied: 'hos'
```

**解决方案**:

```bash
# Linux/macOS
chmod +x $(which hos)

# 或使用 sudo
sudo pip install hosforge
```

### Q: Skill 执行失败

```
Error: Skill 'xxx' execution failed
```

**解决方案**:

1. 检查 Skill 是否存在：`hos skill list`
2. 查看 Skill 详情：`hos skill info xxx`
3. 检查参数是否正确
4. 查看详细错误：添加 `--verbose` 选项

### Q: 输出乱码

```bash
# 设置正确的编码
export PYTHONIOENCODING=utf-8

# 或使用 ASCII 输出
hos skill run xxx --format text --ascii
```

### Q: 如何调试 CLI？

```bash
# 启用详细日志
hos --verbose skill run nuclei_scan target=https://example.com

# 启用调试模式
export HOS_LOG_LEVEL=DEBUG
hos skill run nuclei_scan target=https://example.com
```

## 相关资源

- [Skill 系统文档](../skills/README.md)
- [MCP Server 文档](../mcp_server/README.md)
- [适配器系统文档](../adapters/README.md)
- [GitHub 仓库](https://github.com/lxcxjxhx/HOS-Forge)
