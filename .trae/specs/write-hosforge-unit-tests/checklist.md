# 检查清单

## 测试目录结构检查
- [ ] `hosforge/tests/__init__.py` 存在且内容正确
- [ ] `hosforge/tests/conftest.py` 存在且包含共享 fixtures
- [ ] `hosforge/tests/test_security_agents/__init__.py` 存在
- [ ] `hosforge/tests/test_security_tools/__init__.py` 存在
- [ ] `hosforge/tests/test_knowledge/__init__.py` 存在
- [ ] `hosforge/tests/test_reporter/__init__.py` 存在
- [ ] `hosforge/tests/test_mcp_server/__init__.py` 存在

## Pytest 配置检查
- [ ] `hosforge/pyproject.toml` 包含 pytest 配置
- [ ] 配置了 pytest-asyncio 支持
- [ ] 配置了 pytest-cov 覆盖率报告
- [ ] 测试发现规则正确设置

## 安全代理测试检查
- [ ] `test_audit_agent.py` 包含初始化测试
- [ ] `test_audit_agent.py` 包含 analyze 方法测试
- [ ] `test_audit_agent.py` 包含边界条件测试
- [ ] `test_audit_agent.py` 包含异常处理测试
- [ ] `test_defense_agent.py` 包含初始化测试
- [ ] `test_defense_agent.py` 包含修复生成测试
- [ ] `test_defense_agent.py` 包含修复验证测试
- [ ] `test_defense_agent.py` 包含多漏洞场景测试
- [ ] `test_attack_agent.py` 包含初始化测试
- [ ] `test_attack_agent.py` 包含工具注册测试
- [ ] `test_attack_agent.py` 包含渗透测试执行测试
- [ ] `test_attack_agent.py` 包含报告生成测试
- [ ] `test_attack_agent.py` 包含辅助方法测试

## 安全工具测试检查
- [ ] `test_nmap_tool.py` 包含初始化测试
- [ ] `test_nmap_tool.py` 包含命令构建测试
- [ ] `test_nmap_tool.py` 包含输出解析测试
- [ ] `test_nmap_tool.py` 正确 mock subprocess 调用
- [ ] `test_nmap_tool.py` 包含错误处理测试
- [ ] `test_semgrep_tool.py` 包含初始化测试
- [ ] `test_semgrep_tool.py` 包含规则配置测试
- [ ] `test_semgrep_tool.py` 包含 JSON 输出解析测试
- [ ] `test_semgrep_tool.py` 正确 mock subprocess 调用
- [ ] `test_semgrep_tool.py` 包含漏洞提取测试
- [ ] `test_nuclei_tool.py` 包含初始化测试
- [ ] `test_nuclei_tool.py` 包含模板加载测试
- [ ] `test_nuclei_tool.py` 包含扫描执行测试
- [ ] `test_nuclei_tool.py` 正确 mock subprocess 调用
- [ ] `test_nuclei_tool.py` 包含严重级别映射测试

## 知识库测试检查
- [ ] `test_vector_store.py` 包含初始化测试
- [ ] `test_vector_store.py` 包含向量添加测试
- [ ] `test_vector_store.py` 包含向量检索测试
- [ ] `test_vector_store.py` 包含相似度计算测试
- [ ] `test_vector_store.py` 正确 mock FAISS/ChromaDB
- [ ] `test_search.py` 包含语义搜索测试
- [ ] `test_search.py` 包含关键词搜索测试
- [ ] `test_search.py` 包含混合搜索测试
- [ ] `test_search.py` 包含结果排序测试
- [ ] `test_indexer.py` 包含文档索引测试
- [ ] `test_indexer.py` 包含批量索引测试
- [ ] `test_indexer.py` 包含索引更新测试
- [ ] `test_indexer.py` 包含索引删除测试

## 报告生成器测试检查
- [ ] `test_html_reporter.py` 包含初始化测试
- [ ] `test_html_reporter.py` 包含报告生成测试
- [ ] `test_html_reporter.py` 包含模板渲染测试
- [ ] `test_html_reporter.py` 包含数据格式化测试
- [ ] `test_html_reporter.py` 包含严重级别展示测试
- [ ] `test_html_reporter.py` 包含报告导出测试

## 测试执行检查
- [ ] 所有测试文件可以通过 pytest 发现
- [ ] 运行 `pytest hosforge/tests/ -v` 所有测试通过
- [ ] 运行 `pytest hosforge/tests/ --cov=hosforge` 生成覆盖率报告
- [ ] 核心模块覆盖率达到 80%+
- [ ] 没有测试失败或错误

## 代码质量检查
- [ ] 运行 `ruff check hosforge/tests/` 无错误
- [ ] 运行 `ruff format hosforge/tests/` 代码格式一致
- [ ] 所有测试文件有适当的类型注解
- [ ] 所有测试文件有 docstring 说明
- [ ] Mock 对象使用正确
- [ ] 异步测试使用 pytest-asyncio 正确标记

## Git 提交检查
- [ ] 创建了新分支 `test/hosforge-unit-tests`
- [ ] 所有测试文件已添加到 git
- [ ] 提交信息使用 Conventional Commits 格式
- [ ] 提交信息包含测试覆盖范围说明
- [ ] 没有未提交的更改
- [ ] 没有推送到远程仓库
- [ ] 没有创建 PR

## 文档检查
- [ ] `spec.md` 完整描述了所有需求
- [ ] `tasks.md` 列出了所有任务步骤
- [ ] `checklist.md` 包含所有检查点
- [ ] 规范文档语言与用户请求一致（中文）
