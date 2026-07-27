# 任务列表

## 任务 1: 完善测试目录结构和配置文件
- [ ] 1.1 检查并补全所有测试子目录的 `__init__.py` 文件
  - `hosforge/tests/__init__.py` (已存在)
  - `hosforge/tests/test_security_agents/__init__.py` (已存在)
  - `hosforge/tests/test_security_tools/__init__.py` (已存在)
  - `hosforge/tests/test_knowledge/__init__.py` (已存在)
  - `hosforge/tests/test_reporter/__init__.py` (需要创建)
  - `hosforge/tests/test_mcp_server/__init__.py` (需要创建)
- [ ] 1.2 完善 `conftest.py` 共享 fixtures
  - 添加更多通用的 mock 对象和测试数据
  - 添加异步测试支持配置
- [ ] 1.3 在 `hosforge/pyproject.toml` 中配置 pytest
  - 添加 pytest 和 pytest-asyncio 配置
  - 配置 pytest-cov 覆盖率报告
  - 设置测试发现规则

## 任务 2: 完成安全代理单元测试
- [ ] 2.1 完善 `test_security_agents/test_audit_agent.py`
  - 验证现有测试用例完整性
  - 添加边界条件测试
  - 添加异常处理测试
- [ ] 2.2 完善 `test_security_agents/test_defense_agent.py`
  - 验证现有测试用例完整性
  - 添加修复验证测试
  - 添加多漏洞场景测试
- [ ] 2.3 完善 `test_security_agents/test_attack_agent.py`
  - 验证现有测试用例完整性
  - 添加工具集成测试
  - 添加报告生成测试

## 任务 3: 编写安全工具单元测试
- [ ] 3.1 创建 `test_security_tools/test_nmap_tool.py`
  - 测试 NmapTool 初始化
  - 测试命令构建逻辑
  - 测试 XML/JSON 输出解析
  - Mock subprocess 调用
  - 测试错误处理（超时、命令失败）
- [ ] 3.2 创建 `test_security_tools/test_semgrep_tool.py`
  - 测试 SemgrepTool 初始化
  - 测试规则配置加载
  - 测试 JSON 输出解析
  - Mock subprocess 调用
  - 测试漏洞提取逻辑
- [ ] 3.3 创建 `test_security_tools/test_nuclei_tool.py`
  - 测试 NucleiTool 初始化
  - 测试模板加载
  - 测试扫描执行和结果解析
  - Mock subprocess 调用
  - 测试严重级别映射

## 任务 4: 编写知识库单元测试
- [ ] 4.1 创建 `test_knowledge/test_vector_store.py`
  - 测试向量存储初始化
  - 测试向量添加和检索
  - 测试相似度计算
  - Mock FAISS/ChromaDB 依赖
  - 测试持久化操作
- [ ] 4.2 创建 `test_knowledge/test_search.py`
  - 测试语义搜索功能
  - 测试关键词搜索
  - 测试混合搜索
  - 测试结果排序和过滤
  - Mock embedding 生成
- [ ] 4.3 创建 `test_knowledge/test_indexer.py`
  - 测试文档索引
  - 测试批量索引操作
  - 测试索引更新和删除
  - Mock 外部数据源

## 任务 5: 编写报告生成器单元测试
- [ ] 5.1 创建 `test_reporter/test_html_reporter.py`
  - 测试 HTMLReporter 初始化
  - 测试报告生成流程
  - 测试模板渲染
  - 测试漏洞数据格式化
  - 测试不同严重级别展示
  - 测试报告导出功能

## 任务 6: 运行测试并验证覆盖率
- [ ] 6.1 运行完整测试套件
  - 执行 `pytest hosforge/tests/ -v`
  - 验证所有测试通过
- [ ] 6.2 生成覆盖率报告
  - 执行 `pytest hosforge/tests/ --cov=hosforge --cov-report=term-missing`
  - 验证核心模块覆盖率达到 80%+
- [ ] 6.3 修复测试问题
  - 修复失败的测试用例
  - 补充缺失的测试覆盖
  - 优化测试性能

## 任务 7: 代码质量检查
- [ ] 7.1 运行 ruff 检查
  - 执行 `ruff check hosforge/tests/`
  - 修复所有 lint 错误
- [ ] 7.2 运行类型检查（如果配置了 mypy）
  - 执行类型检查
  - 修复类型错误
- [ ] 7.3 代码格式化
  - 执行 `ruff format hosforge/tests/`
  - 确保代码风格一致

## 任务 8: 创建分支并提交代码
- [ ] 8.1 创建新分支
  - 执行 `git checkout -b test/hosforge-unit-tests`
- [ ] 8.2 提交代码
  - 添加所有测试文件
  - 使用 Conventional Commits 格式：`test: add comprehensive unit tests for HOS-Forge modules`
  - 提交信息包含测试覆盖范围说明
- [ ] 8.3 验证提交
  - 检查 git status
  - 确认所有文件已提交

## 任务依赖关系
- 任务 1 是基础任务，其他任务依赖它完成
- 任务 2-5 可以并行执行
- 任务 6 依赖任务 2-5 完成
- 任务 7 可以与任务 6 并行
- 任务 8 依赖任务 6-7 完成
