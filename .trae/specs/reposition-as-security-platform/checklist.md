# HOS-Forge 重新定位验证清单

## Phase 1: 文档和定位更新

### Task 1: README.md 重写
- [ ] 项目标题从 "AI IDE" 改为 "AI Native Security Platform"
- [ ] 项目描述突出 Security Runtime 核心概念
- [ ] 包含 "Architecture" 章节
- [ ] 架构图展示以 HOS Security Runtime 为中心
- [ ] 架构图展示多入口：VSCode Plugin, Cursor Plugin, Claude Code Plugin, OpenHands Plugin, CLI, REST API, GitHub Action
- [ ] 架构图展示核心组件：Security Engine, Rule Engine, Knowledge Base, Detection Capabilities
- [ ] "Features" 章节强调核心安全能力
- [ ] 包含 "Use Cases" 章节
- [ ] Quick Start 展示 CLI/IDE/API 使用示例

### Task 2: 架构图
- [ ] 架构图清晰展示 Runtime 核心地位
- [ ] 架构图展示所有入口类型
- [ ] 架构图展示核心组件关系
- [ ] 架构图嵌入 README.md

### Task 3: 项目元数据
- [ ] `pyproject.toml` 中的项目描述已更新
- [ ] 相关文档中的项目定位描述已更新

### Task 4: PR 创建
- [ ] 分支名称为 `docs/reposition-as-security-platform`
- [ ] 所有文档变更已提交
- [ ] PR 描述清晰说明定位升级原因
- [ ] PR 描述包含架构图预览（如适用）

## 验证标准

### 用户视角验证
- [ ] 用户访问 GitHub 仓库后，立即理解这是一个 Security Platform，而非 IDE
- [ ] 用户能看到清晰的架构图
- [ ] 用户能理解核心资产是 Security Engine、Rule Engine、Knowledge Base
- [ ] 用户能理解 IDE 只是入口之一，核心能力可服务任何 IDE/CLI/CI

### 原创性评估验证
- [ ] 评审者关注点从 "是不是 OpenHands 二开" 转变为 "安全运行时、规则体系、检测引擎和知识库是否独有"
- [ ] 项目描述不再强调 "基于 OpenHands"，而是强调 HOS 独有的安全能力
- [ ] 即使底层 IDE 来源于 OpenHands，核心安全能力形成了独立价值

### 技术准确性验证
- [ ] 架构图准确反映当前代码结构
- [ ] 描述的功能与代码实现一致
- [ ] 未来规划（Phase 2）明确标注为 "未来" 或 "后续 PR"

## Phase 2: 核心模块独立化（后续验证）

### 未来任务（不在本次验证范围）
- [ ] Security Engine 提取为独立模块
- [ ] Rule Engine 提取为独立模块
- [ ] Knowledge Base 提取为独立模块
- [ ] REST API 和 SDK 提供
- [ ] 更多 IDE 插件开发
