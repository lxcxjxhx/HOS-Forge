# HOS-Forge 重新定位任务列表

## Phase 1: 文档和定位更新（当前 PR）

- [x] Task 1: 重写 README.md，明确 Platform 定位
  - [x] SubTask 1.1: 更新项目标题和描述，从 "AI IDE" 改为 "AI Native Security Platform"
  - [x] SubTask 1.2: 重写项目简介，突出 Security Runtime 核心概念
  - [x] SubTask 1.3: 添加 "Architecture" 章节，展示多入口架构图
  - [x] SubTask 1.4: 更新 "Features" 章节，强调核心安全能力
  - [x] SubTask 1.5: 添加 "Use Cases" 章节，展示不同入口的使用场景
  - [x] SubTask 1.6: 更新 Quick Start，展示通过 CLI/IDE/API 使用的示例

- [x] Task 2: 创建架构图
  - [x] SubTask 2.1: 设计以 HOS Security Runtime 为中心的架构图
  - [x] SubTask 2.2: 展示多入口：VSCode Plugin, Cursor Plugin, Claude Code Plugin, OpenHands Plugin, CLI, REST API, GitHub Action
  - [x] SubTask 2.3: 展示核心组件：Security Engine, Rule Engine, Knowledge Base, Detection Capabilities
  - [x] SubTask 2.4: 将架构图嵌入 README.md

- [x] Task 3: 更新项目元数据
  - [x] SubTask 3.1: 更新 `pyproject.toml` 中的项目描述
  - [x] SubTask 3.2: 更新 `hosforge/pyproject.toml` 中的项目描述
  - [x] SubTask 3.3: 更新相关文档中的项目定位描述

- [ ] Task 4: 提交并合并到 main
  - [ ] SubTask 4.1: 清理调试临时文件
  - [ ] SubTask 4.2: 提交所有文档和代码变更
  - [ ] SubTask 4.3: 合并到 main 分支并推送

## Phase 2: 核心模块独立化（后续 PR，不在本次范围）

- [ ] Task 5: 提取 Security Engine 为独立模块（未来）
- [ ] Task 6: 提取 Rule Engine 为独立模块（未来）
- [ ] Task 7: 提取 Knowledge Base 为独立模块（未来）
- [ ] Task 8: 提供 REST API 和 SDK（未来）
- [ ] Task 9: 开发更多 IDE 插件（Cursor、Claude Code 等）（未来）

# Task Dependencies
- [Task 2] 可与 [Task 1] 并行（架构图设计独立）
- [Task 3] 依赖 [Task 1]（元数据更新需要明确新定位）
- [Task 4] 依赖 [Task 1, 2, 3]（提交需要所有变更完成）
- [Phase 2] 依赖 [Phase 1] 完成
