# 编写 HOS-Forge 单元测试规范

## Why
HOS-Forge 项目需要完整的单元测试套件来确保代码质量、防止回归错误，并为后续开发提供信心。当前已有部分测试文件创建，但需要完成所有核心模块的测试覆盖。

## What Changes
- 创建完整的测试目录结构，包括 `test_security_tools/`, `test_knowledge/`, `test_mcp_server/`, `test_security_agents/`, `test_reporter/`
- 为安全代理（AuditAgent, DefenseAgent, AttackAgent）编写单元测试
- 为安全工具（NmapTool, SemgrepTool, NucleiTool）编写单元测试
- 为知识库模块（vector_store, search, indexer）编写单元测试
- 为报告生成器（html_reporter）编写单元测试
- 配置 pytest 和覆盖率报告，目标覆盖率 80%+
- 创建新分支 `test/hosforge-unit-tests` 并提交代码

## Impact
- Affected specs: maintain-hos-forge-phase3 (Task 8)
- Affected code: 
  - `hosforge/tests/` - 测试目录
  - `hosforge/security_agents/` - 安全代理测试
  - `hosforge/security_tools/` - 安全工具测试
  - `hosforge/knowledge/` - 知识库测试
  - `hosforge/reporter/` - 报告生成器测试
  - `hosforge/pyproject.toml` - pytest 配置

## ADDED Requirements

### Requirement: 测试目录结构
系统 SHALL 提供完整的测试目录结构，包含所有必要的 `__init__.py` 文件和共享 fixtures。

#### Scenario: 测试目录初始化
- **WHEN** 测试套件加载
- **THEN** 所有测试目录应包含 `__init__.py` 文件
- **AND** `conftest.py` 应提供共享 fixtures

### Requirement: 安全代理测试
系统 SHALL 为所有安全代理提供完整的单元测试覆盖。

#### Scenario: AuditAgent 测试
- **WHEN** 测试 AuditAgent
- **THEN** 应测试初始化、analyze 方法、规则加载、漏洞检测
- **AND** 应覆盖正常路径和异常路径

#### Scenario: DefenseAgent 测试
- **WHEN** 测试 DefenseAgent
- **THEN** 应测试修复生成、验证方法
- **AND** 应测试已知和未知 CWE 模板

#### Scenario: AttackAgent 测试
- **WHEN** 测试 AttackAgent
- **THEN** 应测试初始化、工具注册、渗透测试执行、报告生成
- **AND** 应测试辅助方法（风险评分计算、漏洞去重）

### Requirement: 安全工具测试
系统 SHALL 为所有安全工具提供单元测试，mock 外部命令执行。

#### Scenario: NmapTool 测试
- **WHEN** 测试 NmapTool
- **THEN** 应测试命令构建、输出解析、错误处理
- **AND** 应 mock subprocess 调用

#### Scenario: SemgrepTool 测试
- **WHEN** 测试 SemgrepTool
- **THEN** 应测试规则配置、扫描执行、结果解析
- **AND** 应处理 JSON 输出格式

#### Scenario: NucleiTool 测试
- **WHEN** 测试 NucleiTool
- **THEN** 应测试模板加载、扫描执行、漏洞检测
- **AND** 应处理多种输出格式

### Requirement: 知识库测试
系统 SHALL 为知识库模块提供完整的测试覆盖。

#### Scenario: VectorStore 测试
- **WHEN** 测试 VectorStore
- **THEN** 应测试向量存储、检索、相似度计算
- **AND** 应测试批量操作和持久化

#### Scenario: Search 测试
- **WHEN** 测试搜索功能
- **THEN** 应测试语义搜索、关键词搜索、混合搜索
- **AND** 应测试搜索结果排序和过滤

#### Scenario: Indexer 测试
- **WHEN** 测试索引器
- **THEN** 应测试文档索引、更新、删除
- **AND** 应测试批量索引操作

### Requirement: 报告生成器测试
系统 SHALL 为报告生成器提供测试覆盖。

#### Scenario: HTMLReporter 测试
- **WHEN** 测试 HTMLReporter
- **THEN** 应测试报告生成、模板渲染、数据格式化
- **AND** 应测试不同严重级别的漏洞展示

### Requirement: Pytest 配置
系统 SHALL 配置 pytest 和覆盖率报告。

#### Scenario: Pytest 配置
- **WHEN** 运行 pytest
- **THEN** 应自动发现所有测试文件
- **AND** 应支持异步测试（pytest-asyncio）
- **AND** 应生成覆盖率报告

#### Scenario: 覆盖率目标
- **WHEN** 运行覆盖率报告
- **THEN** 核心模块覆盖率应达到 80%+
- **AND** 应生成 HTML 和终端报告

## MODIFIED Requirements

### Requirement: 代码质量
所有测试代码 SHALL 通过 ruff 检查，遵循项目代码风格。

#### Scenario: 代码风格
- **WHEN** 运行 ruff 检查
- **THEN** 所有测试文件应无错误
- **AND** 应遵循项目的 import 排序规则

## REMOVED Requirements
无移除的需求。
