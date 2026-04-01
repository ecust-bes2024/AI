# Claude Code Agent 编排知识库 - 总索引

## 📖 文档体系概览

本知识库是对 Claude Code (v2.1.88) Agent 编排机制的完整逆向分析和抽象提炼。目标：**在新 session 中，AI 读取这些文档后能实现 99% 相似的 Agent 编排效果**。

### 设计定位
- **通用 Agent SDK/框架**：不绑定具体产品形态
- **语言无关**：设计原则 + 接口契约 + 伪代码
- **可落地实现**：完整的技术规格，包含状态机、数据流、接口定义

### 知识来源
1. Claude Code 源码逆向（1884 个 TS/TSX 文件）
2. 深度分析文档（Harness 机制、上下文管理、安全工程）
3. 设计模式提炼（910 个模式实例，323 个高置信度）

---

## 🗺️ 文档路由表

### 核心概念层（必读）

| 文档 | 主题 | 关键概念 | 阅读优先级 |
|------|------|----------|-----------|
| [01-OVERVIEW.md](01-OVERVIEW.md) | 全景：Agent 运行时核心概念 | Harness、REPL、Turn、消息生命周期 | ⭐⭐⭐⭐⭐ |
| [02-AGENT-LOOP.md](02-AGENT-LOOP.md) | 核心循环：从输入到输出的完整流程 | QueryEngine、StreamingToolExecutor、消息队列 | ⭐⭐⭐⭐⭐ |

### 能力层（核心机制）

| 文档 | 主题 | 关键概念 | 阅读优先级 |
|------|------|----------|-----------|
| [03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md) | 工具系统：LLM 的能力原子 | Tool 注册、并发执行、权限检查、错误分类 | ⭐⭐⭐⭐⭐ |
| [04-CONTEXT-ENGINE.md](04-CONTEXT-ENGINE.md) | 上下文管理：三层防线 | ToolResultStorage、Compact、Tool Search | ⭐⭐⭐⭐⭐ |
| [05-HOOK-SYSTEM.md](05-HOOK-SYSTEM.md) | Hook 系统：5 层注入点 | PreToolUse、PostSampling、onBeforeQuery | ⭐⭐⭐⭐ |
| [06-PERMISSION.md](06-PERMISSION.md) | 权限系统：安全管道 | 4 级模式、YOLO Classifier、权限即管道 | ⭐⭐⭐⭐ |

### 高级特性层

| 文档 | 主题 | 关键概念 | 阅读优先级 |
|------|------|----------|-----------|
| [07-MULTI-AGENT.md](07-MULTI-AGENT.md) | 多 Agent 编排 | Team/Swarm、任务系统、消息传递 | ⭐⭐⭐⭐ |
| [08-MEMORY.md](08-MEMORY.md) | 记忆系统 | 三层记忆、自动提取、MagicDocs | ⭐⭐⭐ |
| [09-SECURITY.md](09-SECURITY.md) | 安全工程 | TreeSitter AST、SSRF Guard、Stream Guard | ⭐⭐⭐ |
| [10-SPECULATION.md](10-SPECULATION.md) | 预执行优化 | Overlay FS、原子合并、时间节省计量 | ⭐⭐⭐ |
| [11-PLUGIN-SKILL.md](11-PLUGIN-SKILL.md) | 扩展系统 | Plugin 生命周期、Skill 声明式能力 | ⭐⭐⭐ |

### 哲学层（设计指导）

| 文档 | 主题 | 关键概念 | 阅读优先级 |
|------|------|----------|-----------|
| [12-DESIGN-PHILOSOPHY.md](12-DESIGN-PHILOSOPHY.md) | 设计哲学与方法论 | 7 个核心原则、可复用模式 | ⭐⭐⭐⭐ |

---

## 🎯 快速导航

### 按实现阶段导航

**阶段 1：理解核心概念**（1-2 天）
```
01-OVERVIEW.md → 02-AGENT-LOOP.md → 12-DESIGN-PHILOSOPHY.md
```
理解 Harness 是什么、Agent Loop 如何运转、设计哲学是什么。

**阶段 2：实现基础引擎**（3-5 天）
```
03-TOOL-SYSTEM.md → 04-CONTEXT-ENGINE.md → 06-PERMISSION.md
```
实现工具注册执行、上下文管理、权限系统。

**阶段 3：增强可扩展性**（2-3 天）
```
05-HOOK-SYSTEM.md → 11-PLUGIN-SKILL.md
```
实现 Hook 注入点、Plugin/Skill 扩展机制。

**阶段 4：高级特性**（3-5 天）
```
07-MULTI-AGENT.md → 08-MEMORY.md → 09-SECURITY.md → 10-SPECULATION.md
```
实现多 Agent 编排、记忆系统、安全防护、预执行优化。

### 按问题导航

**Q: 如何设计 Agent 的主循环？**
→ `02-AGENT-LOOP.md` 第 2 节：REPL 循环设计

**Q: 如何管理上下文不爆炸？**
→ `04-CONTEXT-ENGINE.md` 第 3 节：三层防线架构

**Q: 如何让 Agent 可扩展？**
→ `05-HOOK-SYSTEM.md` + `11-PLUGIN-SKILL.md`

**Q: 如何实现多 Agent 协作？**
→ `07-MULTI-AGENT.md` 第 4 节：Team 编排模式

**Q: 如何保证 Agent 安全？**
→ `06-PERMISSION.md` + `09-SECURITY.md`

**Q: 如何优化 Agent 性能？**
→ `04-CONTEXT-ENGINE.md` 第 5 节：Tool Search + `10-SPECULATION.md`

---

## 📐 文档结构规范

每份文档遵循统一结构：

```markdown
# 标题

## 1. 核心概念
- 定义关键术语
- 解释设计动机

## 2. 架构设计
- 整体架构图
- 数据流图
- 状态机定义

## 3. 接口契约
- 核心接口定义（伪代码）
- 输入输出规范
- 错误处理

## 4. 实现要点
- 关键算法
- 边界情况处理
- 性能优化

## 5. 设计决策
- 为什么这样设计
- 权衡取舍
- 可选方案

## 6. 参考实现
- Claude Code 源码位置
- 关键函数签名
- 设计模式应用

## 7. 实现检查清单
- 必须实现的功能
- 可选的优化
- 测试验证点
```

---

## 🔧 使用指南

### 给 AI 的使用说明

当你在新 session 中需要实现 Agent 编排时：

1. **先读索引**：`00-INDEX.md`（本文档）
2. **理解全景**：`01-OVERVIEW.md` 了解整体架构
3. **按需深入**：根据当前实现阶段，读取对应文档
4. **交叉引用**：文档间有超链接，可跳转查看相关内容

### 给人类的使用说明

- **学习路径**：按"阶段 1 → 2 → 3 → 4"顺序阅读
- **问题驱动**：遇到具体问题时，用"按问题导航"快速定位
- **实现验证**：每份文档末尾有"实现检查清单"，用于自检

---

## 📊 知识库统计

- **文档总数**：12 份核心文档 + 1 份索引
- **预计总字数**：约 80,000 - 100,000 字
- **覆盖源码**：1884 个 TS/TSX 文件
- **设计模式**：323 个高置信度模式实例
- **核心机制**：15+ 个关键子系统

---

## 🔄 版本信息

- **知识库版本**：v1.0
- **基于 Claude Code 版本**：v2.1.88
- **最后更新**：2026-04-01
- **维护者**：Reverse Engineering Lab

---

## 📝 贡献指南

本知识库基于 Claude Code 源码逆向分析，如发现：
- 设计理解偏差
- 实现细节遗漏
- 更优的抽象方式

欢迎补充和修正。

---

**下一步**：阅读 [01-OVERVIEW.md](01-OVERVIEW.md) 了解 Agent 运行时的核心概念。
