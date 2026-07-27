# HOS-Forge 示例工作流库

本目录包含 HOS-Forge Taskflow Engine 的示例工作流，展示了不同安全场景下的自动化工作流编排。

## 工作流列表

### 1. security-audit.yaml - 安全审计工作流
**用途**: 完整的安全审计流程，包括静态分析、漏洞验证、补丁生成和安全审查

**流程**:
```
静态扫描 (SAST Agent) → 漏洞验证 (RedTeam Agent) → 补丁生成 (Developer Agent) → 安全审查 (Security Reviewer)
```

**使用场景**:
- 代码提交前的安全检查
- 定期安全审计
- 发布前安全验证

**运行命令**:
```bash
hos taskflow run workflows/security-audit.yaml
```

---

### 2. cve-research.yaml - CVE 研究工作流
**用途**: 自动化 CVE 漏洞研究，包括漏洞查询、代码分析、PoC 开发和补丁分析

**流程**:
```
CVE 查询 → 代码分析 → PoC 开发 → 补丁分析 → 报告生成
```

**使用场景**:
- CVE 漏洞深度研究
- 漏洞利用开发
- 补丁对比分析

**运行命令**:
```bash
hos taskflow run workflows/cve-research.yaml
```

---

### 3. api-security-test.yaml - API 安全测试工作流
**用途**: 全面的 API 安全测试，包括认证、授权和注入测试

**流程**:
```
API 发现 → 认证测试 → 注入测试 → 授权测试 → 报告生成
```

**使用场景**:
- REST API 安全测试
- GraphQL API 安全测试
- 微服务 API 安全验证

**运行命令**:
```bash
hos taskflow run workflows/api-security-test.yaml
```

---

### 4. dependency-scan.yaml - 依赖漏洞扫描工作流
**用途**: 扫描项目依赖中的已知漏洞并生成修复计划

**流程**:
```
npm 审计 + pip 审计 + cargo 审计 → 漏洞分析 → 修复计划 → 依赖更新
```

**使用场景**:
- 开源依赖安全检查
- 供应链安全审计
- 依赖版本升级规划

**运行命令**:
```bash
hos taskflow run workflows/dependency-scan.yaml
```

---

### 5. container-security.yaml - 容器安全审计工作流
**用途**: 全面的容器安全审计，包括镜像扫描和配置检查

**流程**:
```
镜像扫描 + Dockerfile 分析 → 配置检查 → 漏洞验证 → 修复 → 安全报告
```

**使用场景**:
- Docker 镜像安全检查
- Kubernetes 配置审计
- 容器运行时安全验证

**运行命令**:
```bash
hos taskflow run workflows/container-security.yaml
```

---

### 6. code-review.yaml - 安全代码审查工作流
**用途**: 自动化安全代码审查，包括漏洞检测和修复建议

**流程**:
```
静态分析 + 模式匹配 → 漏洞检测 → 误报检查 → 修复建议 → 审查报告
```

**使用场景**:
- Pull Request 安全审查
- 代码提交前检查
- 安全编码规范验证

**运行命令**:
```bash
hos taskflow run workflows/code-review.yaml
```

---

### 7. incident-response.yaml - 事件响应工作流
**用途**: 自动化安全事件响应流程

**流程**:
```
事件检测 → 威胁分析 → 影响评估 → 遏制 → 根除 → 恢复 → 事后审查
```

**使用场景**:
- 安全事件自动响应
- 入侵检测与响应
- 安全事件取证分析

**运行命令**:
```bash
hos taskflow run workflows/incident-response.yaml
```

---

## 工作流结构说明

所有工作流遵循统一的 YAML 结构：

```yaml
hos:
  version: "1.0"

workflow:
  name: "工作流名称"
  description: "工作流描述"
  
  tasks:
    - name: 任务名称
      agent:
        - agent_type
      tools:
        - tool_name
      depends_on:
        - 依赖任务
      timeout: 超时时间（秒）
```

### 关键字段说明

- **name**: 任务唯一标识符
- **agent**: 执行任务的 Agent 类型（如 sast_agent, redteam_agent, developer_agent）
- **tools**: 任务可用的 MCP 工具列表
- **depends_on**: 依赖的前置任务列表（支持并行执行）
- **timeout**: 任务超时时间（秒）

## 自定义工作流

您可以基于这些示例创建自定义工作流：

1. 复制现有工作流文件
2. 修改任务定义和依赖关系
3. 调整 Agent 和工具配置
4. 设置合适的超时时间

### 最佳实践

- **任务粒度**: 每个任务应该是一个独立的、可测试的单元
- **依赖设计**: 明确定义任务间的依赖关系，避免循环依赖
- **超时设置**: 为关键任务设置合理的超时时间
- **工具分配**: 只为任务分配必要的工具，遵循最小权限原则

## 相关文档

- [Taskflow Engine 使用指南](../../../docs/taskflow-guide.md)
- [Personality 定义指南](../../../docs/personality-guide.md)
- [MCP Server 开发指南](../../../docs/mcp-server-guide.md)

## 贡献

欢迎贡献更多示例工作流！请确保：
- 工作流结构符合规范
- 包含清晰的描述和注释
- 提供使用场景说明
- 测试验证工作流可正常运行
