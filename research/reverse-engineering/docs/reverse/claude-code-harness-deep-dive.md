# Claude Code Harness 深度剖析：Agent 运行时的核心机制

## 概述：为什么 Harness 是 Claude Code 的灵魂

在分析 Claude Code 源码时,我们发现了一个关键洞察:**Harness 才是 Claude Code 的真正灵魂**。所有你从使用中感知到的丝滑体验——权限弹窗、自动压缩、工具并发执行、speculation 预加载——背后都由一套精密的编排机制驱动。

本文档聚焦于我们之前文档中遗漏的核心机制,特别是:
- Harness 的完整数据流(从 main.tsx 到 REPL)
- Hook 系统的 5 层注入点
- 上下文管理的精密设计(ToolResultStorage、ContentReplacementState)
- 安全工程的细节(TreeSitter、YOLO Classifier)
- 设计哲学的提炼

这份文档与我们之前的《Claude Code 源码提取与架构分析》形成互补:前者侧重静态结构,本文聚焦动态运行时机制。

---

## 第一部分：Harness 全景 — 完整数据流

### 1.1 从启动到 REPL 的完整链路

```
┌─────────────────────────────────────────────────────────────────┐
│ main.tsx (入口)                                                  │
│ ├─ logStartupTelemetry() ← 启动遥测                             │
│ ├─ runMigrations() ← 数据迁移                                   │
│ ├─ prefetchSystemContextIfSafe() ← 预取系统上下文               │
│ ├─ eagerLoadSettings() ← 预加载配置                             │
│ ├─ maybeActivateProactive/Brief ← Proactive 模式检测            │
│ ├─ initializeEntrypoint() ← 初始化入口点                        │
│ └─ run() → renderAndRun() ← 启动 React 渲染循环                 │
│    └─ launchRepl() → REPL ← 进入 REPL 主循环                    │
└─────────────────────────────────────────────────────────────────┘
```

**关键文件**:
- `src/cli/main.tsx` - 启动入口
- `src/cli/repl.tsx` - REPL 组件
- `src/cli/state.ts` - 全局状态管理

### 1.2 REPL 组件：React 组件即 Loop

Claude Code 的 Agent Loop 不是传统的 `while(true)` 循环,而是一个 **React 组件**。这是整个架构最精妙的设计之一。

```typescript
// src/cli/repl.tsx
REPL({
  commands: initialCommands,        // 斜杠命令
  initialTools,                     // 初始工具集
  initialMessages,                  // 初始消息
  pendingHookMessages,              // 待处理的 Hook 消息 ← 关键！
  initialFileHistorySnapshots,      // 文件历史快照
  initialContentReplacements,       // 内容替换状态 ← toolResultStorage
  initialAgentName,                 // Agent 名称
  initialAgentColor,                // Agent 颜色
  mcpClients,                       // MCP 客户端
  dynamicMcpConfig,                 // 动态 MCP 配置
  systemPrompt: customSystemPrompt, // 自定义系统提示
  appendSystemPrompt,               // 追加系统提示
  onBeforeQuery,                    // Query 前回调 ← Hook 注入点！
  onTurnComplete,                   // Turn 完成回调 ← Hook 注入点！
  mainThreadAgentDefinition,        // 主线程 Agent 定义
  taskListId,                       // 任务列表 ID
  remoteSessionConfig,              // 远程会话配置
  directConnectConfig,              // 直连配置
  thinkingConfig,                   // Thinking 配置
})
```

**设计洞察**:
- 状态管理由 React 驱动(`useState`, `useEffect`)
- 生命周期由 React 控制(`onInit`, `cleanup`)
- 渲染和执行交织在一起
- **React 的声明式模型天然适合 Agent Loop**,因为 Agent 的状态(messages, tools, permissions)本身就是不断变化的

---

## 第二部分：核心机制深度解析

### 2.1 Hook 系统：5 层注入点的可编程中间件

Hook 系统是 Claude Code 最精妙的可扩展性设计,通过 5 层 Hook 实现完整的生命周期控制。

#### 2.1.1 Hook 层次结构

```
事件: PreToolUse → PostToolUse → Notification → Elicitation → StatusLine → FileSuggestion
      ↓              ↓              ↓              ↓              ↓              ↓
   匹配模式      匹配模式       匹配模式       匹配模式       匹配模式       匹配模式
      ↓              ↓              ↓              ↓              ↓              ↓
  Command Hook  Command Hook  Command Hook  Command Hook  Command Hook  Command Hook
  Function Hook Function Hook Function Hook Function Hook Function Hook Function Hook
  Callback Hook Callback Hook Callback Hook Callback Hook Callback Hook Callback Hook
      ↓              ↓
  AsyncHookRegistry ←→ 后台进程轮询
```

**关键文件**:
- `src/hooks/hookRegistry.ts` - Hook 注册表
- `src/hooks/asyncHookRegistry.ts` - 异步 Hook 管理
- `src/hooks/hookEvents.ts` - Hook 事件定义
- `src/hooks/hookExecution.ts` - Hook 执行逻辑

#### 2.1.2 三种 Hook 类型

| 类型 | 实现方式 | 用途 |
|------|----------|------|
| **Command Hook** | Shell 命令 | 调用外部工具、脚本 |
| **Function Hook** | JavaScript 函数 | 内部逻辑处理 |
| **Callback Hook** | 回调函数 | 异步通知 |

#### 2.1.3 onBeforeQuery 和 onTurnComplete：Loop 的两个关键注入点

```typescript
// src/cli/repl.tsx
onBeforeQuery: async (context) => {
  // 在每次 API 调用前触发
  // 用于:
  // - PostSamplingHooks (修改 messages/systemPrompt)
  // - Hook 系统注入额外消息
  // - 上下文预算检查
}

onTurnComplete: async (context) => {
  // 在每次 Turn 完成后触发
  // 用于:
  // - 记忆提取 (extractMemories)
  // - Speculation 启动
  // - Compact 检查
  // - 遥测上报
}
```

**设计原则**: 整个 Agent Loop 不是一段硬编码的流程,而是通过两个生命周期回调把控制权交给外部。

#### 2.1.4 pendingHookMessages：延迟注入机制

```typescript
// src/hooks/hookMessages.ts
useDeferredHookMessages(pendingHookMessages, setMessages)
```

Hook 消息不是同步注入的,而是通过 `pendingHookMessages: Promise<HookResultMessage[]>` 异步注入。这意味着:
- Hook 执行不会阻塞 REPL 初始化
- 消息在处理时排队
- 支持后台 Hook 的结果延迟到达

### 2.2 上下文管理：三层防线

Claude Code 最大的投资不在 prompt engineering,而在**上下文管理基础设施**。

#### 2.2.1 三层防线架构

| 层 | 机制 | 文件 | 作用 |
|---|---|---|---|
| **L1 预防** | `contextSuggestions` | `contextSuggestions.ts` | 实时检测膨胀风险,建议用户 action |
| **L2 自动压缩** | `compactConversation()` | `compact.ts` | 自动摘要历史对话 |
| **L3 Tool 搜索** | `toolSearch` / `ToolSearchTool` | `toolSearch.ts` | 不发送所有 Tool Schema,按需发现 |

#### 2.2.2 ToolResultStorage：上下文预算执行的精密机制

这是整个 harness 中**最精密的模块**,揭示了 Claude Code 如何在有限上下文中管理海量工具输出。

**分层存储策略**:

```typescript
// src/tools/toolResultStorage.ts
getPersistenceThreshold(toolName, declaredMaxResultSizeChars) // 计算持久化阈值
getSessionDir()                                                // 会话目录
getToolResultsDir()                                            // 工具结果目录
getToolResultPath(id, isJson)                                  // 结果文件路径
persistToolResult(content, id)                                 // 持久化到文件
buildLargeToolResultMessage(result)                            // 构建大结果消息
maybePersistLargeToolResult(block, toolName, threshold)        // 条件持久化
```

**策略**: 当工具输出超过阈值时,**写入磁盘文件**,消息中只保留引用和预览。

**ContentReplacementState：预算驱动的内容替换**:

```typescript
createContentReplacementState()                                // 创建替换状态
cloneContentReplacementState(source)                           // 克隆
provisionContentReplacementState(messages, replacements)       // 初始化
collectCandidatesByMessage(messages)                           // 收集可替换候选
partitionByPriorDecision(candidates, state)                    // 按已有决策分区
selectFreshToReplace(fresh, frozenSize, limit)                 // 选择要替换的
buildReplacement(candidate)                                    // 构建替换
enforceToolResultBudget(messages, state, skipToolNames)        // 强制执行预算
applyToolResultBudget(messages, state, writeToTranscript)      // 应用预算
reconstructContentReplacementState(messages, records, inherited) // 重建状态
reconstructForSubagentResume(parentState, resumedMessages, sidechainRecords) // 子Agent恢复
```

**这是整个系统中最复杂的状态管理**:

1. **候选收集**: 扫描所有消息,找出可以被替换的 tool result
2. **分区决策**: 已替换的(frozen) vs 新的(fresh)
3. **选择性替换**: 在预算内,选择最能节省空间的结果替换为摘要
4. **持久化**: 被替换的完整内容写入文件
5. **可重建**: `reconstructForSubagentResume` 允许子 Agent 恢复父 Agent 的替换状态

**这个机制确保了无论对话多长,上下文大小始终可控**——通过把旧的、大的工具输出「换出」到磁盘。

