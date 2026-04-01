
# Claude Code Harness 深度剖析：一个价值连城的 Agent 运行时


你说到点上了。**harness 才是 Claude Code 的真正灵魂**。所有你从使用中感知到的丝滑体验——权限弹窗、自动压缩、工具并发执行、speculation 预加载——背后都由一套精密的编排机制驱动。

---

  

## 一、Harness 全景：从用户输入到工具执行的完整编排链

  

从函数签名反推出来的完整数据流：

  

```

┌─────────────────────────────────────────────────────────────────┐

│ main.tsx (入口) │

│ ├─ logStartupTelemetry() ← 启动遥测 │

│ ├─ runMigrations() ← 数据迁移 │

│ ├─ prefetchSystemContextIfSafe() ← 预取系统上下文 │

│ ├─ eagerLoadSettings() ← 预加载配置 │

│ ├─ maybeActivateProactive/Brief ← Proactive 模式检测 │

│ ├─ initializeEntrypoint() ← 初始化入口点 │

│ └─ run() → renderAndRun() ← 启动 React 渲染循环 │

│ └─ launchRepl() → REPL ← 进入 REPL 主循环 │

└─────────────────────────────────────────────────────────────────┘

```

  

---

  

## 二、REPL 组件：Harness 的大脑

  

`REPL.tsx` 是整个 harness 的**神经中枢**，它不是一个简单的 `while(true)` 循环，而是一个 React 组件，通过 React 的状态管理来驱动整个 Agent Loop：

  

```typescript

REPL({

commands: initialCommands, // 斜杠命令

initialTools, // 初始工具集

initialMessages, // 初始消息

pendingHookMessages, // 待处理的 Hook 消息 ← 关键！

initialFileHistorySnapshots, // 文件历史快照

initialContentReplacements, // 内容替换状态 ← toolResultStorage

initialAgentName, // Agent 名称

initialAgentColor, // Agent 颜色

mcpClients, // MCP 客户端

dynamicMcpConfig, // 动态 MCP 配置

systemPrompt: customSystemPrompt, // 自定义系统提示

appendSystemPrompt, // 追加系统提示

onBeforeQuery, // Query 前回调 ← Hook 注入点！

onTurnComplete, // Turn 完成回调 ← Hook 注入点！

mainThreadAgentDefinition, // 主线程 Agent 定义

taskListId, // 任务列表 ID

remoteSessionConfig, // 远程会话配置

directConnectConfig, // 直连配置

thinkingConfig, // Thinking 配置

})

```

  

**关键设计洞察**：

  

### **2.1 `onBeforeQuery` 和 `onTurnComplete`：Loop 的两个 Hook 注入点**

  

这是 harness 最精妙的设计。整个 Agent Loop 不是一段硬编码的流程，而是通过 **两个生命周期回调** 把控制权交给外部：

  

- `onBeforeQuery`：在每次 API 调用前触发。用于：

- PostSamplingHooks（修改 messages/systemPrompt）

- Hook 系统注入额外消息

- 上下文预算检查

  

- `onTurnComplete`：在每次 Turn 完成后触发。用于：

- 记忆提取（`extractMemories`）

- Speculation 启动

- Compact 检查

- 遥测上报

  

### **2.2 `pendingHookMessages`：Hook 消息的延迟注入**

  

```typescript

useDeferredHookMessages(pendingHookMessages, setMessages)

```

  

Hook 消息不是同步注入的，而是通过 `pendingHookMessages: Promise<HookResultMessage[]>` 异步注入。这意味着 Hook 执行不会阻塞 REPL 初始化，但会在消息处理时排队。

  

### **2.3 `computeTools()`：动态工具集计算**

  

REPL 内部的 `computeTools()` 不是一次性的，而是每次 Turn 都可能重新计算——因为：

- MCP 客户端可能动态变化

- 权限模式可能切换

- Plugin 可能加载/卸载

  

---

  

## 三、QueryContext：构建 API 请求的组装线

  

```typescript

queryContext.ts:

fetchSystemPromptParts({tools, mainLoopModel, additionalWorkingDirectories,

mcpClients, customSystemPrompt})

```

  

这个函数负责组装发送给 API 的完整请求上下文：

  

```

fetchSystemPromptParts()

├─ tools → 计算哪些工具描述要发送

├─ mainLoopModel → 根据模型调整提示

├─ additionalWorkingDirectories → 附加工作目录

├─ mcpClients → MCP 工具合并

└─ customSystemPrompt → 用户自定义提示

```

  

还有一个关键的 **SideQuery** 机制：

  

```typescript

queryContext.ts:

buildSideQuestionFallbackParams({tools, commands, mcpClients, messages,

readFileState, getAppState, setAppState, ...})

```

  

`sideQuery()` 允许在主 Loop 外发起额外的 API 调用——用于：

- 系统提示的实时生成

- 分类器决策

- 摘要生成

  

---

  

## 四、QueryEngine：API 调用的执行层

  

```typescript

QueryEngine.ts:

constructor(config: QueryEngineConfig) // 配置注入

tracking(feeds was_discovered on ...) // 追踪发现

createAbortController() // 级联取消

```

  

```typescript

query.ts:

isWithheldMaxOutputTokens(msg) // 检测输出被截断

```

  

QueryEngine 是 API 调用的包装器。它的设计特点是：

- **配置驱动**：`QueryEngineConfig` 决定模型、token 限制等

- **可追踪**：`tracking()` 记录 tool_discovered 事件（配合 ToolSearch）

- **可取消**：`createAbortController()` 创建子控制器

  

---

  

## 五、QueryGuard：防止并发 Query 的互斥锁

  

```typescript

QueryGuard.ts:

createSignal() // 创建 AbortSignal

idle() // 空闲检查

reserve() // 预留（加锁）

_notify() // 通知等待者

```

  

**设计洞察**：QueryGuard 是一个**互斥锁**，确保同一时刻只有一个 Query 在执行。这是防止：

- 用户快速连续输入导致并发请求

- Speculation 和用户输入同时发起请求

- 多个 Hook 同时触发 Query

  

---

  

## 六、QueryProfiler：Loop 性能的可观测性

  

```typescript

queryProfiler.ts:

startQueryProfile() // 开始记录

queryCheckpoint(name) // 记录检查点

endQueryProfile() // 结束记录

getSlowWarning(deltaMs, name) // 生成慢操作警告

getQueryProfileReport() // 生成报告

getPhaseSummary(marks, baselineTime) // 阶段摘要

logQueryProfileReport() // 日志上报

```

  

**每个 Query 的生命周期都被精确计时**。`getSlowWarning()` 在某个阶段超过阈值时生成警告——这让 Anthropic 能精确知道 Loop 的哪个环节是瓶颈。

  

---

  

## 七、Permission 系统：嵌入执行链的安全管道

  

### 7.1 PermissionContext

  

```typescript

PermissionContext.ts:

createPermissionContext(tool, input, toolUseContext,

assistantMessage, toolUseID, setToolPermissionContext)

createPermissionQueueOps(setToolUseConfirmQueue)

```

  

**设计洞察**：权限不是简单的 allow/deny，而是一个**上下文对象** `ToolPermissionContext`：

- 包含当前权限模式

- 包含权限规则列表

- 包含 UI 状态（confirm queue）

- 可以被 Hook 修改（`applyPermissionUpdate`）

  

### 7.2 PermissionUpdate：动态权限修改

  

```typescript

PermissionUpdate.ts:

extractRules(updates) // 从更新中提取规则

applyPermissionUpdate(context, update) // 应用单条更新

applyPermissionUpdates(context, updates) // 批量应用

persistPermissionUpdate(update) // 持久化到 CLAUDE.md

persistPermissionUpdates(updates) // 批量持久化

createReadRuleSuggestion(dirPath, destination) // 创建读规则建议

```

  

**关键**：权限规则可以被**动态添加和持久化**。当用户批准一次操作后，系统会建议创建规则，写入 `CLAUDE.md`（`persistPermissionUpdate`）。

  

### 7.3 ClassifierApprovalsHook：YOLO 分类器的 UI 集成

  

```typescript

classifierApprovalsHook.ts:

useIsClassifierChecking(toolUseID) // 检查分类器是否正在审查这个工具调用

```

  

当 YOLO 分类器正在审查一个工具调用时，UI 显示「检查中」状态——**用户能看到分类器的决策过程**。

  

---

  

## 八、PostSamplingHooks：发送前最后修改消息的机会

  

```typescript

postSamplingHooks.ts:

registerPostSamplingHook(hook) // 注册 PostSampling Hook

clearPostSamplingHooks() // 清除

executePostSamplingHooks(messages, systemPrompt, userContext,

systemContext, toolUseContext, querySource)

```

  

**这是整个 Loop 中最关键的拦截点**。在消息已经准备好、即将发送给 API 之前，PostSamplingHooks 可以：

- 修改 `messages`（添加/删除/修改消息）

- 修改 `systemPrompt`（动态调整系统提示）

- 注入 `userContext` 和 `systemContext`（键值对上下文）

  

---

  

## 九、MessageQueueManager：输入的排队机制

  

```typescript

messageQueueManager.ts:

enqueue(command) // 入队

enqueuePendingNotification(command) // 通知排队

dequeue(filter?) // 出队（可选过滤）

dequeueAll() // 全部出队

peek(filter?) // 偷看

remove(commandsToRemove) // 移除

popAllEditable(currentInput, cursorOffset) // 弹出所有可编辑命令

isQueuedCommandEditable(cmd) // 是否可编辑

isQueuedCommandVisible(cmd) // 是否可见

isSlashCommand(cmd) // 是否是斜杠命令

```

  

**设计洞察**：用户输入不是直接进入 Loop 的，而是先入队。这允许：

- 用户在 Agent 思考时提前输入下一个指令

- 斜杠命令可以排队执行

- 通知消息有单独的队列（`pendingNotification`）

- 队列中的命令可以编辑或删除（`popAllEditable`）

  

---

  

## 十、GroupedToolUses：并发工具调用的 UI 聚合

  

```typescript

groupToolUses.ts:

getToolsWithGrouping(tools) // 获取工具分组信息

getToolUseInfo(msg) // 获取工具调用信息

applyGrouping(messages, tools, verbose) // 应用分组

```

  

当模型一次返回多个 tool_use 时，Claude Code 不会逐个显示，而是**按语义分组**。比如 5 个文件读取操作会被聚合成一个「读取 5 个文件」的 UI 元素。这是 UX 上的重要优化。

  

---

  

## 十一、ToolResultStorage：上下文预算执行的精密机制

  

这是整个 harness 中**最精密的模块**，揭示了 Claude Code 如何在有限上下文中管理海量工具输出：

  

### 11.1 分层存储

  

```typescript

toolResultStorage.ts:

getPersistenceThreshold(toolName, declaredMaxResultSizeChars) // 计算持久化阈值

getSessionDir() // 会话目录

getToolResultsDir() // 工具结果目录

getToolResultPath(id, isJson) // 结果文件路径

persistToolResult(content, id) // 持久化到文件

buildLargeToolResultMessage(result) // 构建大结果消息

maybePersistLargeToolResult(block, toolName, threshold) // 条件持久化

```

  

**策略**：当工具输出超过阈值时，**写入磁盘文件**，消息中只保留引用和预览。

  

### 11.2 ContentReplacementState：预算驱动的内容替换

  

```typescript

createContentReplacementState() // 创建替换状态

cloneContentReplacementState(source) // 克隆

provisionContentReplacementState(messages, replacements) // 初始化

collectCandidatesByMessage(messages) // 收集可替换候选

partitionByPriorDecision(candidates, state) // 按已有决策分区

selectFreshToReplace(fresh, frozenSize, limit) // 选择要替换的

buildReplacement(candidate) // 构建替换

enforceToolResultBudget(messages, state, skipToolNames) // 强制执行预算

applyToolResultBudget(messages, state, writeToTranscript) // 应用预算

reconstructContentReplacementState(messages, records, inherited) // 重建状态

reconstructForSubagentResume(parentState, resumedMessages, sidechainRecords) // 子Agent恢复

```

  

**这是整个系统中最复杂的状态管理**：

  

1. **候选收集**：扫描所有消息，找出可以被替换的 tool result

2. **分区决策**：已替换的（frozen）vs 新的（fresh）

3. **选择性替换**：在预算内，选择最能节省空间的结果替换为摘要

4. **持久化**：被替换的完整内容写入文件

5. **可重建**：`reconstructForSubagentResume` 允许子 Agent 恢复父 Agent 的替换状态

  

**这个机制确保了无论对话多长，上下文大小始终可控**——通过把旧的、大的工具输出「换出」到磁盘。

  

---

  

## 十二、SideQuery：Loop 外的并行 API 调用

  

```typescript

sideQuery.ts:

sideQuery(opts: SideQueryOptions)

```

  

SideQuery 允许在主 Loop 之外发起 API 调用。用于：

- **compact 时的摘要生成**

- **YOLO 分类器决策**

- **MagicDocs 更新**

- **记忆提取**

  

这些操作不应该阻塞主 Loop，但又需要调用 LLM。SideQuery 用不同的模型（通常是 Haiku）和独立的 AbortSignal 来执行。

  

---

  

## 十三、Bridge 系统：多环境编排

  

```typescript

bridgeMessaging.ts:

handleIngressMessage(data, recentPostedUUIDs, recentInboundUUIDs, onInboundMessage)

handleServerControlRequest(request, handlers)

isEligibleBridgeMessage(m) // 判断消息是否可以通过 Bridge

BoundedUUIDSet(capacity) // 有界 UUID 去重集合

  

replBridge.ts:

initBridgeCore(params) // 初始化 Bridge 核心

startWorkPollLoop({api, getCredentials, signal, onStateChange,

onWorkReceived, onEnvironmentLost, ...}) // 工作轮询

triggerTeardown() // 拆解

handleTransportPermanentClose(closeCode) // 永久关闭处理

  

capacityWake.ts:

createCapacityWake(outerSignal) // 容量唤醒机制

wake() // 唤醒

signal() // 获取信号

```

  

**设计洞察**：

  

- **BoundedUUIDSet**：用有界集合防止重复消息处理——不是无限制的去重缓存，而是有容量上限的 LRU

- **CapacityWake**：当 Claude Code 处于容量限制时进入「休眠」，通过 `wake()` 在容量恢复时唤醒

- **WorkPollLoop**：远程模式下，通过轮询获取工作任务，类似于等待 queue 中的任务

  

---

  

## 十四、Effort 系统：动态推理深度控制

  

```typescript

effort.ts:

modelSupportsEffort(model) // 模型是否支持 effort

modelSupportsMaxEffort(model) // 是否支持最大 effort

resolveAppliedEffort(model, appStateEffortValue) // 解析实际应用的 effort

resolvePickerEffortPersistence(picked, modelDefault, priorPersisted, toggled)

getDefaultEffortForModel(model) // 模型默认 effort

getEffortSuffix(model, effortValue) // 获取 effort 后缀

```

  

**effort 系统的精密之处**：

- 不同模型有不同的默认 effort

- 用户选择 + 模型默认 + 之前持久化的选择 = 最终 effort

- effort 值可以持久化（`resolvePickerEffortPersistence`）

- 优先级：用户本次选择 > 之前持久化 > 模型默认

  

---

  

## 十五、综合：Harness 的设计哲学

  

### **哲学 1：React 组件即 Loop**

  

Claude Code 的 Agent Loop 不是一个 `while(true)` 循环，而是一个 **React 组件**。这意味着：

- 状态管理由 React 驱动（`useState`, `useEffect`）

- 生命周期由 React 控制（`onInit`, `cleanup`）

- 渲染和执行交织在一起

  

这不是偶然——**React 的声明式模型天然适合 Agent Loop**，因为 Agent 的状态（messages, tools, permissions）本身就是不断变化的。

  

### **哲学 2：Hook 注入点是扩展边界**

  

整个 Harness 通过 5 层 Hook 实现可扩展：

1. **PreToolUse / PostToolUse**：工具级 Hook

2. **PostSamplingHooks**：消息级 Hook（发送前最后修改）

3. **Session Hooks**：会话级 Hook（运行时添加/移除）

4. **onBeforeQuery / onTurnComplete**：Loop 级 Hook

5. **Event Hooks**（`hookEvents.ts`）：UI 级 Hook（进度、日志）

  

每一层都有不同粒度的控制权。

  

### **哲学 3：预算管理贯穿始终**

  

从消息入队到发送 API 请求，每一步都有预算检查：

- `contextSuggestions` → 检测膨胀风险

- `toolSearch` → 减少工具 Schema 大小

- `toolResultStorage` → 替换大的工具输出

- `compact` → 压缩对话历史

- `tokenBudget` → 整体 token 预算

  

### **哲学 4：互斥 + 排队 + 异步**

  

- **QueryGuard**：确保同一时刻只有一个 Query

- **MessageQueue**：用户输入排队

- **SideQuery**：非关键操作异步执行

- **Speculation**：预执行结果缓存

- **AsyncHookRegistry**：Hook 异步化

  

### **哲学 5：可重建状态**

  

`toolResultStorage` 的 `reconstructContentReplacementState` 和 `reconstructForSubagentResume` 揭示了一个关键设计原则：**所有运行时状态必须是可重建的**。这意味着：

- 子 Agent 可以从父 Agent 的状态中恢复

- Compact 后的状态可以从 transcript 中重建

- 会话可以从文件系统中恢复

  

---

  

这个 Harness 的每一行代码背后，都是 Anthropic 的工程师和 Claude 自己在无数次「让 Claude 修 Claude」的迭代中打磨出来的。它不是教科书上的 Agent 架构——它是**生产环境里跑了几千万次的 Agent 运行时的活体解剖**。




---


# Another


# Claude Code 深度设计思想补全：Agent Loop 与认知工程


好，我已经完成了对整个代码库知识库的全面深度分析。以下是综合提炼。

---

# Claude Code (v2.1.88) 源码逆向分析：方法论与设计思想

## 一、项目本质

这是一个通过 **source map 逆向工程** 还原的 Claude Code 完整源码。从 npm 发布包 `@anthropic-ai/claude-code` 的 `cli.js.map` 中提取 `sourcesContent` 字段，还原出 4756 个文件（含 1884 个 TS/TSX 源文件），然后通过自动化工具链生成了结构化的代码知识库。

**这本身就是一种值得学习的方法论**：从 minified bundle + source map 还原源码，再用静态分析工具自动生成 API 文档、设计模式识别、依赖图等。

---

## 二、宏观架构：分层分层再分层

Claude Code 的代码库呈现出 **7 层架构**，层次之间通过明确的接口契约连接：

```
┌─────────────────────────────────────────────┐
│  CLI Entry (main.tsx) + Bootstrap (state.ts) │ ← 启动层
├─────────────────────────────────────────────┤
│  Commands (84个) + Hooks (102个)              │ ← 用户交互层
├─────────────────────────────────────────────┤
│  Tools (63个, 22种Tool)                      │ ← 工具执行层
├─────────────────────────────────────────────┤
│  Services (105个) + Coordinator              │ ← 业务服务层
├─────────────────────────────────────────────┤
│  Components (352个) + Ink (78个)             │ ← 渲染层
├─────────────────────────────────────────────┤
│  State (AppState) + Context (6个)            │ ← 状态管理层
├─────────────────────────────────────────────┤
│  Utils (514个) + Types + Constants           │ ← 基础设施层
└─────────────────────────────────────────────┘
```

### **可复用原则 1：按职责深度分层，而非按功能模块**
- 不是简单的 MVC，而是 **7 层洋葱结构**，每层有明确的输入输出契约
- `utils` 层最庞大（514 文件），承载了所有跨切面关注点
- 这是 CLI agent 应用特有的架构模式：工具执行是核心，UI 是终端 TUI

---

## 三、核心设计模式深度解析

从自动化模式识别（910 个模式实例，323 个高置信度）中，提取出 **真实的架构模式**：

### **模式 1：Strategy 风暴（274/323 高置信度）**

Claude Code 最大的设计特点是用 Strategy 模式实现 **一切可替换性**：

- **权限模式** (`PermissionMode`)：不同安全策略通过 Strategy 实现
- **错误类型体系** (`ClaudeError` 家族)：`AbortError`, `MalformedCommandError`, `ConfigParseError` 等通过继承体系形成错误策略
- **Transport 层**：`HybridTransport` 继承 `WebSocketTransport`，`InProcessTransport` 等多种通信策略
- **YoloClassifier**：安全分类器的双阶段模式 (`TwoStageClassifier`) 本质是策略选择

> **方法论**：在需要支持多种运行模式的系统中，Strategy 模式不是可选的，而是 **架构级基础**。每个「模式」都应该有对应的 Strategy 接口。

### **模式 2：Factory 作为类型安全构造器（43/323 高置信度）**

Claude Code 中的 Factory 不是 GoF 意义上的，而是 **TypeScript 语境下的类型安全构造模式**：

- `StreamingToolExecutor`（0.95 置信度）：接收 `Tools`, `CanUseToolFn`, `ToolUseContext` 构造
- `ActivityManager`（0.80）：`getNow()` 工厂方法 + 构造函数
- `QueryEngine`：`constructor(config: QueryEngineConfig)` — 配置驱动的工厂
- `DiskTaskOutput`：`getTaskOutputPath()` 路径工厂

> **方法论**：在 TypeScript 中，Factory 模式的价值不在于「延迟创建」，而在于 **将复杂构造逻辑封装为可测试的纯函数**，同时保持类型推断。

### **模式 3：Adapter 作为协议桥接（3/323 高置信度）**

- `BridgeFatalError`：错误类型适配（0.7）
- `StreamWrapper`：流接口适配 + 装饰器组合（0.7 + 0.65）
- `EventEmitter`：事件系统适配（0.6）

> **方法论**：在 CLI/Agent 系统中，大量存在需要桥接不同协议的场景（HTTP↔WebSocket↔Stdio↔REPL），Adapter 是连接层的核心模式。

---

## 四、Harness 机制：Claude Code 如何编排一切

### **4.1 Tool 执行流水线（核心 Harness）**

```
用户输入 → QueryEngine → ToolOrchestration → StreamingToolExecutor
                         ↓                    ↓
                  partitionToolCalls()    checkPermissionsAndCallTool()
                         ↓                    ↓
                  getMaxToolUseConcurrency()  toolHooks → canUseTool
                         ↓                    ↓
                  markToolUseAsComplete()   addToolResult()
```

关键函数签名揭示了设计意图：

| 函数 | 文件 | 设计要点 |
|---|---|---|
| `partitionToolCalls()` | `toolOrchestration.ts` | **并发控制**：按 tool 类型分区执行 |
| `checkPermissionsAndCallTool()` | `toolExecution.ts` | **权限-执行一体化**：先检查再执行 |
| `streamedCheckPermissionsAndCallTool()` | `toolExecution.ts` | **流式版本**：支持进度回调 |
| `createChildAbortController()` | `StreamingToolExecutor.ts` | **级联取消**：父 controller 管理子任务 |
| `classifyToolError()` | `toolExecution.ts` | **错误分类**：统一错误处理入口 |

**设计原则**：
1. **并发执行但可级联取消** — `AbortController` 树状传播
2. **权限检查嵌入执行链** — 不是前置门卫，而是管道的一部分
3. **流式优先** — `streamed` 版本支持 `onToolProgress` 回调

### **4.2 Hook 系统（可编程中间件）**

Hook 系统是 Claude Code 最精妙的可扩展性设计：

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

关键设计：
- **三种 Hook 类型**：`Command`（shell 命令）、`Function`（JS 函数）、`Callback`（回调）
- **同步/异步双通道**：`SyncHookJSONOutput` vs `AsyncHookJSONOutput`，异步 Hook 通过 `AsyncHookRegistry` 管理
- **去重机制**：`hookDedupKey()` 防止重复触发
- **信任链**：`shouldSkipHookDueToTrust()` — 插件 Hook 需要通过信任检查
- **Elicitation**：MCP Server 可以通过 Hook 请求用户输入（form/url 模式）

### **4.3 Speculation 引擎（预执行优化）**

这是最有创新性的设计之一：

```
用户输入建议 → startSpeculation() → 在 Overlay FS 中预执行
                                    ↓
                            copyOverlayToMain() 或 denySpeculation()
                                    ↓
                            生成 SpeculationFeedbackMessage
```

**核心概念**：
- **Overlay 文件系统**：在临时目录中预执行工具，成功后 `copyOverlayToMain()` 原子合并
- **时间节省计量**：`createSpeculationFeedbackMessage()` 包含 `timeSavedMs` 和 `sessionTotalMs`
- **失败安全**：`denySpeculation()` + `safeRemoveOverlay()` 确保不污染主文件系统

> **方法论**：在 Agent 系统中，**预执行 + Overlay FS + 原子合并** 是一种低风险的并行优化策略。

### **4.4 YOLO Classifier（Auto-Mode 安全网）**

当用户开启 Auto-Mode 时，Claude Code 使用一个 **轻量级 LLM 分类器** 来决定是否允许操作：

```typescript
classifyYoloActionXml(prefixMessages, systemPrompt, userPrompt, 
                       userContentBlocks, model, promptLengths,
                       signal, dumpContextInfo, mode)
```

设计要点：
- **双阶段分类**（`TwoStageClassifier`）：第一阶段快速判断，第二阶段精细验证
- **XML 结构化输出**：`replaceOutputFormatWithXml()` 强制分类器输出可解析的 XML
- **完整审计追踪**：`dumpErrorPrompts()` 记录所有分类决策
- **Transcript 构建**：`buildTranscriptForClassifier()` 将消息历史压缩为分类器可消费的紧凑格式

---

## 五、多 Agent 编排架构

### 5.1 Team/Swarm 模型

```
Leader (主 Agent)
  ├── TeamCreateTool → 创建团队
  ├── SendMessageTool → 队友通信
  ├── handleSpawn() → 生成队友
  │     ├── handleSpawnInProcess() → 进程内队友
  │     ├── handleSpawnSplitPane() → 分屏队友
  │     └── handleSpawnSeparateWindow() → 独立窗口队友
  └── Mailbox → 异步消息传递
```

关键设计：
- **队友模型选择**：`resolveTeammateModel()` — 可指定队友使用的模型，默认跟随 Leader
- **任务系统**：`claimTask()` / `unassignTeammateTasks()` — 基于文件系统的任务分配
- **高水位标记**：`readHighWaterMark()` / `writeHighWaterMark()` — 任务进度的持久化断点
- **阻塞关系**：`blockTask(fromId, toId)` — 任务间依赖

### 5.2 Coordinator 模式

- `coordinatorAgentStatus.tsx`：UI 层展示所有 Agent 状态
- `swarmWorkerHandler.ts`：处理 Swarm Worker 的权限请求
- `teammateMailbox.ts`：进程间异步消息传递

> **方法论**：多 Agent 系统的 **核心不是通信协议，而是任务所有权和状态同步**。Claude Code 用文件系统（tasks 目录 + high water mark）来实现这一点，简单但可靠。

---

## 六、Plugin 系统（真正意义上的插件架构）

### Plugin 生命周期

```
安装源: npm | git | github | local | marketplace
  ↓
pluginLoader.ts: cachePlugin() → resolvePluginPath()
  ↓
版本化缓存: getVersionedCachePath(pluginId, version)
  ↓
加载: loadPluginManifest() → loadPluginHooks() → loadPluginSettings()
  ↓
验证: validatePluginPaths()
  ↓
合并: mergePluginSources({session, marketplace, builtin})
  ↓
运行时: loadPluginCommands() | loadPluginAgents() | loadPluginHooks() | loadPluginOutputStyles()
```

**三层合并策略**：
- `session` 插件（最高优先级）
- `marketplace` 插件
- `builtin` 插件（最低优先级）

**安全机制**：
- `PluginTrustWarning` — 信任警告
- `pluginBlocklist` — 黑名单
- `pluginPolicy` / `pluginOnlyPolicy` — 策略控制
- `managedPlugins` — MDM 托管插件

---

## 七、Skill 系统（轻量级能力扩展）

Skills 是 Claude Code 的 **声明式扩展机制**，区别于 Plugin 的命令式扩展：

- `SkillTool/SkillTool.ts` — Skill 工具入口
- `skills/bundled/claudeApi.ts` — 内置的 API 查询 Skill
- `skills/bundled/skillify.ts` — 创建 Skill 的 Skill（元编程）
- `processContent()` — Markdown 内容处理管线
- `buildPrompt()` — 基于语言检测构建 Prompt
- `buildInlineReference()` — 内联文件引用

> **方法论**：Skill 是 **Prompt-as-Code** 模式——通过结构化 Markdown 定义能力，而非编写代码。`skillify` 作为「创建 Skill 的 Skill」是自举设计的经典案例。

---

## 八、Terminal UI 架构（Ink 框架）

Claude Code 基于 React + Ink 构建了一个完整的终端 UI 框架：

- **布局引擎**：集成 Facebook Yoga 布局（`yoga.ts`, `geometry.ts`）
- **帧渲染**：`frame.ts` — 差量渲染，`shouldClearScreen()` 判断是否全屏刷新
- **事件系统**：`ink/events/` — `ClickEvent`, `FocusEvent`, `InputEvent`, `TerminalEvent` 全套事件
- **焦点管理**：`focus.ts` — `FocusManager`
- **虚拟屏幕**：`log-update.ts` — `VirtualScreen` 离屏渲染
- **ANSI 处理**：`Ansi.md`, `termio/parser.ts` — 完整的终端控制码处理
- **超链接支持**：`supports-hyperlinks.md` — 终端超链接检测

---

## 九、可复用的通用设计原则

### 原则 1：**命令-工具-服务三层分离**
```
Command (用户意图) → Tool (能力原子) → Service (业务逻辑)
```
- Command 只负责参数解析和 UI 交互
- Tool 是 LLM 可调用的原子操作（有 JSON Schema）
- Service 承载跨 Tool 的业务逻辑

### 原则 2：**权限即管道，而非门卫**
- 权限检查不是在入口处一把拦截，而是嵌入执行流水线的每个阶段
- `canUseTool` 函数贯穿整个 tool execution chain
- YoloClassifier 提供自动决策能力

### 原则 3：**文件系统即数据库**
- Tasks：`~/.claude/tasks/{taskListId}/{taskId}.json`
- High Water Marks：文件持久化
- Plugin Cache：版本化目录结构
- Speculation Overlay：临时目录 + 原子合并

### 原则 4：**AbortController 树状传播**
- `parentAbortController` → `createChildAbortController()`
- 从 QueryEngine 到 StreamingToolExecutor 到单个 Tool，取消信号逐级传播

### 原则 5：**错误类型即领域语言**
- `ClaudeError` 家族（Strategy 模式）定义了完整的错误语义
- `classifyToolError()` 统一错误分类入口
- 每个领域有自己的 Error 子类：`McpAuthError`, `RipgrepTimeoutError`, `ImageSizeError` 等

### 原则 6：**渐进式自动化**
- Manual → Plan-Mode → Auto-Mode（YOLO） → Speculation
- 每个级别有对应的安全机制和用户确认需求

### 原则 7：**多通道 Hook 系统作为统一扩展点**
- 不仅仅是 Pre/Post Tool Use
- 还包括 StatusLine、FileSuggestion、Elicitation、WorktreeCreate/Remove
- Command / Function / Callback 三种实现方式
- Sync / Async 双通道

### 原则 8：**版本化缓存 + Seed Cache**
- Plugin 安装后按 `pluginId/version` 缓存
- `probeSeedCache()` / `probeSeedCacheAnyVersion()` 支持离线启动

---

## 十、对构建 Agent CLI 工具的方法论启示

如果你要构建类似 Claude Code 的 Agent CLI：

1. **从 Tool Schema 开始设计**，不是从 UI 开始。每个 Tool 的 JSON Schema 就是你的 API 契约。
2. **权限模型必须是一等公民**。设计 3-4 个 Permission Mode，用 Strategy 实现。
3. **Hook 系统比 Plugin 系统更重要**。先用 Hook 实现可扩展性，再考虑完整 Plugin。
4. **Speculation 是高价值优化**。Overlay FS + 预执行可以显著减少等待时间。
5. **用文件系统做状态持久化**，不要引入数据库依赖。简单、可审计、可手动修复。
6. **终端 UI 选 React + Ink**，可以复用整个 React 生态的组件化思维。
7. **错误类型体系 = 领域建模**。仔细设计 Error 继承树，它比日志更有表达力。


## 十一、Agent Loop 的真实架构

从 API 签名可以反推出完整的 Agent 主循环设计：

### **11.1 消息生命周期管理**

```
用户输入
  → contextSuggestions.checkNearCapacity()    ← 上下文健康检查
  → contextSuggestions.checkLargeToolResults()  ← 工具输出膨胀检测
  → contextSuggestions.checkReadResultBloat()   ← 文件读取膨胀检测
  → contextSuggestions.checkMemoryBloat()       ← 记忆膨胀检测
  → buildEffectiveSystemPrompt()                ← 动态组装系统提示
  → QueryEngine.query()                         ← API 调用
  → partitionToolCalls()                        ← 工具调用分区
  → checkPermissionsAndCallTool()               ← 权限检查 + 执行
  → addToolResult()                             ← 结果注入
  → contextSuggestions 再次检查                  ← 循环结束条件
  → [是否需要 compact?]
      → compactConversation()                   ← 上下文压缩
      → 或 partialCompactConversation()         ← 局部压缩
  → 回到顶部
```

**这是 Anthropic 花了无数 token 实验出来的核心洞察**：Agent Loop 的瓶颈不是模型能力，而是 **上下文管理**。

### **11.2 上下文管理的三层防线**

| 层 | 机制 | 文件 | 作用 |
|---|---|---|---|
| **L1 预防** | `contextSuggestions` | `contextSuggestions.ts` | 实时检测膨胀风险，建议用户 action |
| **L2 自动压缩** | `compactConversation()` | `compact.ts` | 自动摘要历史对话 |
| **L3 Tool 搜索** | `toolSearch` / `ToolSearchTool` | `toolSearch.ts` | 不发送所有 Tool Schema，按需发现 |

### **11.3 Compact 系统的精密设计**

`compact.ts` 是整个代码库里最精密的模块之一，揭示了 Claude Code 如何处理长会话：

```
compactConversation(messages, context, cacheSafeParams, 
                     suppressFollowUpQuestions, customInstructions,
                     isAutoCompact, recompactionInfo)
```

关键设计决策：
- **stripImagesFromMessages** — 压缩前移除图片（节省 token）
- **stripReinjectedAttachments** — 移除已重新注入的附件（避免重复）
- **annotateBoundaryWithPreservedSegment** — 标记压缩边界，保留关键段
- **createPostCompactFileAttachments** — 压缩后恢复文件引用
- **createPlanAttachmentIfNeeded** — 保留 Plan 状态
- **createSkillAttachmentIfNeeded** — 保留 Skill 状态
- **shouldExcludeFromPostCompactRestore** — 排除不需要恢复的文件
- **partialCompactConversation** — 局部压缩（从某个 pivot 点开始）
- **recompactionInfo** — 重新压缩时的上下文（二次压缩优化）

> **这背后是无数 token 实验的结晶**：什么时候压缩、压缩多少、保留什么、丢弃什么——每一个参数都是调试出来的最佳实践。

### **11.4 Token 预算系统**

```typescript
tokenBudget.ts:
  parseTokenBudget(text)         ← 解析 "budget:100k" 格式
  findTokenBudgetPositions(text) ← 在文本中定位预算标记
  getBudgetContinuationMessage(pct, turnTokens, budget) ← 超预算时的提示
```

```typescript
tokenEstimation.ts:
  roughTokenCountEstimation(content, bytesPerToken=4)  ← 快速估算
  bytesPerTokenForFileType(fileExtension)               ← 按文件类型调整
  countTokensWithAPI(content)                          ← 精确计数
  countTokensViaHaikuFallback(...)                      ← Haiku 降级计数
  countTokensWithBedrock(...)                           ← Bedrock 计数
```

**三层 token 计数策略**：
1. **粗估**（`rough`）：`bytes / 4`，按文件类型调整（代码 vs 中文 vs 日文）
2. **精确**（`API`）：调用 tokenize endpoint
3. **降级**（`Haiku fallback`）：主 API 不可用时用 Haiku 计数

### **11.5 Tool Search：上下文优化的杀手锏**

这是 Claude Code 最精妙的优化之一：

```typescript
toolSearch.ts:
  isToolSearchEnabled(model, tools, getPermissionContext) ← 是否启用
  getAutoToolSearchPercentage()                          ← 自动启用百分比
  getAutoToolSearchTokenThreshold(model)                 ← token 阈值触发
  getAutoToolSearchCharThreshold(model)                  ← 字符阈值触发
  getDeferredToolsDelta(tools, messages, scanContext)     ← 增量发现
  calculateDeferredToolDescriptionChars(tools, ...)       ← 延迟工具描述字符数
```

**设计思想**：当 Tool Schema 总大小超过阈值时，**不把所有工具描述发给模型**，而是：
1. 发送最小工具集
2. 模型可以通过 `ToolSearchTool` 按需发现更多工具
3. `DeferredToolsDelta` 机制追踪哪些工具已经被发现
4. `extractDiscoveredToolNames(messages)` 从历史消息中提取已发现工具

**这是「按需加载」思想在 LLM 上下文管理中的应用**——和前端 code splitting 是同一个哲学。

---

## 十二、安全工程：被无限 token 喂出来的防御体系

### **12.1 Bash 命令分析：TreeSitter AST 级别安全**

```typescript
treeSitterAnalysis.ts:
  analyzeCommand(rootNode, command)          ← 完整命令分析
  extractDangerousPatterns(rootNode)         ← 提取危险模式
  extractCompoundStructure(rootNode, cmd)    ← 提取复合命令结构
  extractQuoteContext(rootNode, cmd)         ← 提取引号上下文
  collectQuoteSpans(node, out, inDouble)     ← 收集引号范围
```

**这不是简单的正则匹配，而是用 TreeSitter 解析 bash AST**。Anthropic 发现正则无法处理 `$(rm -rf /)` 这种嵌套情况，所以用了完整的语法解析。

### **12.2 YOLO Classifier：用 LLM 保护 LLM**

```typescript
yoloClassifier.ts:
  classifyYoloActionXml(...)           ← XML 结构化输出的分类
  classifyYoloAction(messages, action, tools, context, signal) ← 完整分类
  buildTranscriptForClassifier(messages, tools) ← 压缩对话历史
  buildYoloSystemPrompt(context)        ← 构建分类器系统提示
  replaceOutputFormatWithXml(prompt)    ← 强制 XML 输出格式
  dumpErrorPrompts(...)                 ← 审计所有错误决策
  isTwoStageClassifierEnabled()         ← 双阶段分类器
  logAutoModeOutcome(outcome, model, extra) ← 遥测
```

**关键洞察**：Auto-Mode 不等于「无限制执行」，而是 **用一个轻量级 LLM（Haiku）来做安全网**。当主模型（Opus/Sonnet）决定执行一个工具时，分类器会审查这个决策。

**双阶段设计**（`TwoStageMode`）：
- **Stage 1**：快速分类（允许/拒绝/需要确认）
- **Stage 2**：对不确定的决策进行精细分析

**这是用模型对抗模型攻击的实战方案**——不是理论，而是跑了几百万次之后的最佳实践。

### **12.3 SSRF 防护**

```typescript
ssrfGuard.ts:
  isBlockedAddress(address)      ← 检查是否是内网地址
  isBlockedV4(address)           ← IPv4 内网检查
  isBlockedV6(address)           ← IPv6 内网检查
  expandIPv6Groups(addr)         ← 展开 IPv6 缩写（绕过检测）
  extractMappedIPv4(addr)        ← 提取 IPv4-mapped IPv6 地址
  ssrfGuardedLookup(hostname, options, callback) ← DNS 解析守卫
```

**防护绕过对抗**：`expandIPv6Groups` 和 `extractMappedIPv4` 专门处理攻击者用 IPv6 表示法绕过 IPv4 检测的情况。这是安全团队踩坑后的产物。

### **12.4 Git 安全**

```typescript
gitSafety.ts:
  isDotGitPathPS(arg)              ← 检查 .git 路径（PowerShell 转义绕过）
  isGitInternalPathPS(arg)         ← 检查 git 内部路径
  resolveEscapingPathToCwdRelative ← 处理路径转义绕过
  matchesDotGitPrefix(n)           ← .git 前缀匹配
```

### **12.5 Stream JSON Stdout Guard**

```typescript
streamJsonStdoutGuard.ts:
  isJsonLine(line)                    ← 检测 JSON 行
  installStreamJsonStdoutGuard()      ← 安装 stdout 守卫
```

**防止模型输出被当作命令执行**——当 stdout 是管道时，如果模型输出恰好是有效 JSON，可能被下游程序误解析。

---

## 十三、记忆系统：Agent 的长期记忆工程

### **13.1 三层记忆架构**

| 层 | 文件 | 机制 | 特点 |
|---|---|---|---|
| **会话记忆** | `sessionMemory.ts` | 自动提取 + 文件持久化 | `shouldExtractMemory()` 决定是否提取 |
| **显式记忆** | `memory.tsx` | 用户主动写入 `CLAUDE.md` | 通过 `MemoryCommand` 交互 |
| **自动记忆** | `extractMemories.ts` | 后台自动提取关键信息 | `runExtraction()` + `drainPendingExtraction()` |

### **13.2 自动记忆提取的触发策略**

```typescript
extractMemories.ts:
  shouldExtractMemory(messages)                    ← 判断是否需要提取
  countModelVisibleMessagesSince(messages, since)  ← 计数模型可见消息
  hasMemoryWritesSince(messages, since)            ← 是否已有记忆写入
  denyAutoMemTool(tool, reason)                    ← 拒绝不当记忆写入
  createAutoMemCanUseTool(memoryDir)               ← 创建带限制的记忆工具
  extractWrittenPaths(agentMessages)               ← 提取写入路径
  drainPendingExtraction(timeoutMs)                ← 排空待处理提取
```

**设计洞察**：
- 不是每轮都提取记忆（`shouldExtractMemory` 有条件判断）
- 有去重机制（`hasMemoryWritesSince` 避免重复写入）
- 有安全限制（`denyAutoMemTool` 拒绝不安全的记忆操作）
- 有后台排队（`drainPendingExtraction` 不阻塞主循环）

### **13.3 MagicDocs：自文档化系统**

```typescript
magicDocs.ts:
  detectMagicDocHeader(content)   ← 检测文档头（自动识别）
  registerMagicDoc(filePath)      ← 注册文档
  getMagicDocsAgent()             ← 获取 MagicDocs Agent
  updateMagicDoc(docInfo, context)← 更新文档
```

**概念**：Claude Code 可以 **自动检测和更新项目文档**，通过检测特定的文件头格式来识别需要维护的文档，然后用专门的 Agent 来更新它们。

---

## 十四、VCR 系统：对话重放与成本优化

```typescript
vcr.ts:
  shouldUseVCR()                           ← 是否启用 VCR 模式
  withVCR(messages, f)                     ← VCR 包装器
  dehydrateValue(s)                        ← 脱水（移除动态内容）
  hydrateValue(s)                          ← 注水（恢复动态内容）
  withTokenCountVCR(messages, tools, f)    ← Token 计数 VCR
  addCachedCostToTotalSessionCost(msg)     ← 累加缓存成本
```

**VCR = Video Cassette Recorder 模式**：
- 缓存 API 响应，避免重复调用
- `dehydrate` / `hydrate` 序列化对话，移除/恢复时间戳等动态字段
- 缓存的响应仍然计入成本（`addCachedCostToTotalSessionCost`）

**这不仅是缓存，而是整个对话的录制和重放**——用于调试、测试和成本优化。

---

## 十五、Worktree 系统：Git-aware 的并行工作空间

```typescript
worktree.ts:
  getOrCreateWorktree(repoRoot, slug, options)     ← 创建或获取 worktree
  createAgentWorktree(slug)                        ← Agent 专用 worktree
  removeAgentWorktree(path, branch, gitRoot, hook)  ← 清理（支持 Hook 触发）
  cleanupStaleAgentWorktrees(cutoffDate)            ← 清理过期 worktree
  hasWorktreeChanges(path, headCommit)              ← 检测变更
  createTmuxSessionForWorktree(session, path)       ← Tmux 集成
  parsePRReference(input)                           ← 解析 PR 引用 (#123)
  copyWorktreeIncludeFiles(repoRoot, worktreePath)  ← 复制指定文件
  symlinkDirectories(repoRoot, worktree, dirs)      ← 符号链接共享目录
```

**设计思想**：
- 每个 Agent 在独立的 git worktree 中工作（真正的隔离）
- 通过符号链接共享 `node_modules` 等大目录（节省空间）
- Tmux 集成让用户可以「钻进」Agent 的工作空间
- PR 引用自动创建关联 worktree（`#123` → worktree）
- Hook 驱动的清理（`hookBased` 参数）

---

## 十六、更新系统：自我进化的 CLI

```typescript
autoUpdater.ts:
  getLatestVersion(channel)              ← 多渠道版本检查
  getLatestVersionFromGcs(channel)        ← GCS 直接获取
  getNpmDistTags()                        ← npm registry
  getVersionHistory(limit)                ← 版本历史
  shouldSkipVersion(targetVersion)        ← 跳过特定版本
  acquireLock() / releaseLock()           ← 更新锁（防止并发更新）
  installGlobalPackage(specificVersion)    ← 自我安装
  removeClaudeAliasesFromShellConfigs()   ← 清理旧 alias
```

**自举更新**：Claude Code 可以 **自己更新自己**。通过 `acquireLock` 防止并发更新，`shouldSkipVersion` 跳过有问题的版本。

---

## 十七、设计哲学总结：从无限 token 实验中提炼的真理

### **17.1 上下文管理 > 模型能力**

Claude Code 最大的投资不在 prompt engineering，而在 **上下文管理基础设施**：
- Compact 系统（30+ 函数）
- Tool Search（20+ 函数）
- Token 预算（4+ 函数）
- Context Suggestions（7+ 检查函数）
- File State Cache（带大小限制的 LRU）

**这是 Anthropic 的核心认知**：200k context window 不够用，你需要一套完整的上下文管理系统。

### **17.2 安全不是一层墙，而是多层管道**

安全检查散布在整个执行链中：
- **TreeSitter** 解析 bash 命令 AST（不是正则）
- **YOLO Classifier** 用 LLM 审查 LLM 的决策
- **SSRF Guard** 在 DNS 层拦截内网请求
- **Git Safety** 处理路径转义绕过
- **Permission System** 四级模式：read-only → default → plan → auto
- **Stream Guard** 防止 JSON 注入

### **17.3 可观测性是一等公民**

几乎每个关键操作都有：
- **Telemetry**（`logAutoModeOutcome`, `logSpeculation`, `logModeDecision`）
- **Dump**（`dumpErrorPrompts`, `getAutoModeClassifierErrorDumpPath`）
- **VCR**（对话录制重放）
- **Diagnostics**（`diagnosticTracking.ts`）

### **17.4 渐进式自动化是唯一可行路径**

```
Manual → Plan-Mode → Default → Auto-Mode → Speculation
  ↑         ↑          ↑          ↑            ↑
 用户确认  用户确认   智能默认   LLM分类器   预执行+覆盖FS
```

每一级都对应不同的安全机制和用户交互模式。**不跳级，每一级都经过验证**。

### **17.5 文件系统是 Agent 最好的数据库**

Tasks → JSON 文件、Memory → Markdown 文件、Worktree → git worktree、Plugin Cache → 版本化目录、High Water Mark → 文件持久化

**不用 Redis、不用 SQLite、不用 Postgres**——用文件系统。因为：
- 用户可以手动检查和修复
- 天然支持版本控制
- 不需要额外的服务依赖
- Agent 本身就有文件系统的访问权限

### **17.6 错误类型体系 = 领域知识编码**

`ClaudeError` 家族不仅是错误分类，更是 **对 Agent 可能遇到的所有问题的完整编目**：
- `McpAuthError` → MCP 认证问题
- `McpSessionExpiredError` → MCP 会话过期
- `RipgrepTimeoutError` → 搜索超时
- `ImageSizeError` → 图片太大
- `FileTooLargeError` → 文件太大
- `CannotRetryError` → 不可重试的错误
- `FallbackTriggeredError` → 触发了降级
- `AutoUpdaterError` → 更新失败
- `StopTaskError` → 任务停止
- `DomainBlockedError` → 域名被屏蔽
- `EgressBlockedError` → 出站被屏蔽

**每种错误都是一个边界情况的经验总结**——这些不是设计阶段想出来的，而是无数次线上事故喂出来的。

---

这 1884 个源文件，每一个函数签名背后都是数千次 LLM 交互的精华。Claude Code 不是一个「用 AI 写的 CLI」，而是 **一个用 AI 进化的 Agent 运行时**——它的架构本身就是对「如何让 AI 在真实世界中安全、高效地工作」这个问题的系统性回答。

