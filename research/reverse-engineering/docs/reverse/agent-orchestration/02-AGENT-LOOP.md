# Agent 核心循环 — 从输入到输出的完整流程

## 1. 核心概念

### 1.1 什么是 Agent Loop

Agent Loop 是 Agent 运行时的心脏，负责：
- 接收用户输入
- 调用 LLM API
- 执行工具调用
- 管理消息历史
- 处理权限检查
- 返回响应

在 Claude Code 中，Agent Loop **不是一个简单的 `while(true)` 循环**，而是一个 **React 组件驱动的状态机**。

### 1.2 核心组件

| 组件 | 职责 | 关键特性 |
|------|------|----------|
| **REPL** | 主循环控制器 | React 组件，状态驱动 |
| **QueryEngine** | API 调用执行器 | 配置驱动，可追踪，可取消 |
| **StreamingToolExecutor** | 工具并发执行器 | 流式处理，并发控制 |
| **MessageQueueManager** | 输入队列管理 | 排队、过滤、编辑 |
| **QueryGuard** | 并发互斥锁 | 防止并发 Query |
| **QueryProfiler** | 性能监控 | 精确计时，慢操作警告 |

### 1.3 设计动机

**为什么用 React 组件而非传统循环？**

1. **声明式状态管理**：Agent 状态（messages, tools, permissions）天然适合 React 的声明式模型
2. **生命周期控制**：`useEffect` 自动处理初始化和清理
3. **UI 与逻辑统一**：渲染和执行在同一个组件中，无需同步
4. **可测试性**：React 组件比命令式循环更容易测试

**为什么需要 QueryGuard？**

防止以下并发场景：
- 用户快速连续输入
- Speculation 和用户输入同时发起
- 多个 Hook 同时触发 Query

---

## 2. 架构设计

### 2.1 REPL 循环状态机

```
┌─────────────────────────────────────────────────────────────┐
│                         REPL 状态机                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [IDLE] ──────────────────────────────────────────────────┐│
│    │                                                       ││
│    │ 用户输入 / Hook 触发                                   ││
│    ↓                                                       ││
│  [QUEUED] ← MessageQueueManager.enqueue()                 ││
│    │                                                       ││
│    │ QueryGuard.reserve() 成功                             ││
│    ↓                                                       ││
│  [PREPARING]                                              ││
│    ├─ onBeforeQuery() ← Hook 注入点                        ││
│    ├─ fetchSystemPromptParts() ← 组装系统提示              ││
│    ├─ enforceToolResultBudget() ← 上下文预算检查           ││
│    └─ computeTools() ← 动态工具集计算                      ││
│    │                                                       ││
│    ↓                                                       ││
│  [QUERYING] ← QueryEngine.query()                         ││
│    │                                                       ││
│    │ API 返回 tool_use                                     ││
│    ↓                                                       ││
│  [EXECUTING_TOOLS]                                        ││
│    ├─ partitionToolCalls() ← 工具调用分区                  ││
│    ├─ checkPermissionsAndCallTool() ← 权限检查             ││
│    └─ StreamingToolExecutor.execute() ← 并发执行           ││
│    │                                                       ││
│    │ 工具执行完成                                           ││
│    ↓                                                       ││
│  [PROCESSING_RESULTS]                                     ││
│    ├─ addToolResult() ← 结果注入                           ││
│    ├─ maybePersistLargeToolResult() ← 大结果持久化         ││
│    └─ applyToolResultBudget() ← 应用预算                   ││
│    │                                                       ││
│    │ 需要继续？                                             ││
│    ├─ Yes → 回到 [QUERYING]                               ││
│    └─ No → ↓                                              ││
│                                                            ││
│  [TURN_COMPLETE]                                          ││
│    ├─ onTurnComplete() ← Hook 注入点                       ││
│    ├─ extractMemories() ← 记忆提取                         ││
│    ├─ startSpeculation() ← 预执行                          ││
│    ├─ checkCompact() ← 压缩检查                            ││
│    └─ QueryGuard.release() ← 释放锁                        ││
│    │                                                       ││
│    └──────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Turn 生命周期

一个 **Turn** 是从用户输入到 Agent 完成响应的完整周期。

```
Turn 生命周期：

1. [开始] 用户输入 / Hook 触发
   ↓
2. [入队] MessageQueueManager.enqueue()
   ↓
3. [加锁] QueryGuard.reserve()
   ↓
4. [准备] onBeforeQuery() + fetchSystemPromptParts()
   ↓
5. [查询] QueryEngine.query() → API 调用
   ↓
6. [执行] StreamingToolExecutor.execute() → 工具并发执行
   ↓
7. [注入] addToolResult() → 结果注入消息历史
   ↓
8. [循环] 如果 API 返回 tool_use，回到步骤 5
   ↓
9. [完成] onTurnComplete() + 释放锁
   ↓
10. [结束] 回到 IDLE 状态
```

### 2.3 数据流图

```
用户输入
  │
  ↓
MessageQueueManager ──→ [队列]
  │                       │
  │                       ↓
  │                   dequeue()
  │                       │
  ↓                       ↓
QueryGuard.reserve() ←────┘
  │
  ↓
onBeforeQuery() ──→ [Hook 修改 messages/systemPrompt]
  │
  ↓
fetchSystemPromptParts() ──→ [组装完整请求]
  │                             │
  │                             ├─ tools
  │                             ├─ systemPrompt
  │                             ├─ messages
  │                             └─ mcpClients
  ↓                             │
QueryEngine.query() ←───────────┘
  │
  ↓
API 响应 (tool_use)
  │
  ↓
partitionToolCalls() ──→ [分区：并发 vs 串行]
  │
  ↓
checkPermissionsAndCallTool() ──→ [权限检查]
  │                                  │
  │                                  ├─ Auto-Mode → YOLO Classifier
  │                                  ├─ Plan-Mode → 用户确认
  │                                  └─ Default → 智能默认
  ↓                                  │
StreamingToolExecutor.execute() ←───┘
  │
  ↓
Tool 结果
  │
  ↓
maybePersistLargeToolResult() ──→ [大结果写入磁盘]
  │
  ↓
addToolResult() ──→ [注入消息历史]
  │
  ↓
applyToolResultBudget() ──→ [应用上下文预算]
  │
  ↓
[需要继续？] ──Yes──→ 回到 QueryEngine.query()
  │
  No
  ↓
onTurnComplete() ──→ [Hook 后处理]
  │
  ↓
QueryGuard.release()
  │
  ↓
回到 IDLE
```

---

## 3. 接口契约

### 3.1 REPL 组件接口

```typescript
interface REPLProps {
  // 命令系统
  commands: Command[]
  
  // 工具系统
  initialTools: Tool[]
  
  // 消息历史
  initialMessages: Message[]
  
  // Hook 系统
  pendingHookMessages: Promise<HookResultMessage[]>
  onBeforeQuery?: (context: QueryContext) => Promise<void>
  onTurnComplete?: (context: TurnContext) => Promise<void>
  
  // 上下文管理
  initialFileHistorySnapshots: FileHistorySnapshot[]
  initialContentReplacements: ContentReplacementState
  
  // Agent 配置
  initialAgentName?: string
  initialAgentColor?: string
  
  // MCP 集成
  mcpClients: McpClient[]
  dynamicMcpConfig?: DynamicMcpConfig
  
  // 系统提示
  systemPrompt?: string
  appendSystemPrompt?: string
  
  // 多 Agent
  mainThreadAgentDefinition?: AgentDefinition
  taskListId?: string
  
  // 远程会话
  remoteSessionConfig?: RemoteSessionConfig
  directConnectConfig?: DirectConnectConfig
  
  // 推理配置
  thinkingConfig?: ThinkingConfig
}
```

### 3.2 QueryEngine 接口

```typescript
interface QueryEngineConfig {
  model: string
  maxTokens?: number
  temperature?: number
  topP?: number
  topK?: number
  effort?: EffortValue
  thinkingConfig?: ThinkingConfig
}

class QueryEngine {
  constructor(config: QueryEngineConfig)
  
  // 核心查询方法
  async query(params: QueryParams): Promise<QueryResponse>
  
  // 追踪工具发现
  tracking(event: 'tool_discovered', toolName: string): void
  
  // 创建子 AbortController
  createAbortController(parent?: AbortController): AbortController
}

interface QueryParams {
  messages: Message[]
  systemPrompt: string
  tools: Tool[]
  signal?: AbortSignal
  onChunk?: (chunk: StreamChunk) => void
}

interface QueryResponse {
  message: AssistantMessage
  usage: TokenUsage
  stopReason: StopReason
}
```

### 3.3 StreamingToolExecutor 接口

```typescript
class StreamingToolExecutor {
  // 并发执行工具调用
  async execute(
    toolCalls: ToolCall[],
    options: ExecutionOptions
  ): AsyncIterator<ToolResult>
}

interface ExecutionOptions {
  // 并发控制
  maxConcurrency: number
  
  // 权限检查
  canUseTool: (tool: Tool, input: any) => Promise<boolean>
  
  // 进度回调
  onProgress?: (progress: ExecutionProgress) => void
  
  // 取消信号
  signal?: AbortSignal
}

interface ToolResult {
  toolUseId: string
  content: ToolResultContent
  isError: boolean
}
```

### 3.4 MessageQueueManager 接口

```typescript
class MessageQueueManager {
  // 入队
  enqueue(command: QueuedCommand): void
  enqueuePendingNotification(command: QueuedCommand): void
  
  // 出队
  dequeue(filter?: (cmd: QueuedCommand) => boolean): QueuedCommand | null
  dequeueAll(): QueuedCommand[]
  
  // 查看
  peek(filter?: (cmd: QueuedCommand) => boolean): QueuedCommand | null
  
  // 移除
  remove(commandsToRemove: QueuedCommand[]): void
  
  // 编辑
  popAllEditable(currentInput: string, cursorOffset: number): QueuedCommand[]
  
  // 判断
  isQueuedCommandEditable(cmd: QueuedCommand): boolean
  isQueuedCommandVisible(cmd: QueuedCommand): boolean
  isSlashCommand(cmd: QueuedCommand): boolean
}

interface QueuedCommand {
  id: string
  type: 'user_input' | 'slash_command' | 'hook_message'
  content: string
  timestamp: number
  editable: boolean
  visible: boolean
}
```

### 3.5 QueryGuard 接口

```typescript
class QueryGuard {
  // 创建 AbortSignal
  createSignal(): AbortSignal
  
  // 检查是否空闲
  idle(): boolean
  
  // 预留（加锁）
  async reserve(): Promise<void>
  
  // 释放（解锁）
  release(): void
  
  // 内部通知机制
  private _notify(): void
}
```

---

## 4. 实现要点

### 4.1 QueryGuard 互斥锁实现

**核心算法：基于 Promise 的等待队列**

```typescript
class QueryGuard {
  private _active: boolean = false
  private _waiters: Array<() => void> = []
  
  async reserve(): Promise<void> {
    // 如果已有活跃 Query，加入等待队列
    while (this._active) {
      await new Promise<void>(resolve => {
        this._waiters.push(resolve)
      })
    }
    // 获得锁
    this._active = true
  }
  
  release(): void {
    this._active = false
    // 唤醒下一个等待者
    this._notify()
  }
  
  private _notify(): void {
    const next = this._waiters.shift()
    if (next) next()
  }
  
  idle(): boolean {
    return !this._active
  }
}
```

**设计要点：**
- 使用 Promise 队列而非轮询，避免 CPU 浪费
- FIFO 顺序保证公平性
- `idle()` 方法用于 UI 状态显示

### 4.2 MessageQueueManager 队列管理

**关键特性：可编辑队列**

```typescript
class MessageQueueManager {
  private _queue: QueuedCommand[] = []
  private _pendingNotifications: QueuedCommand[] = []
  
  enqueue(command: QueuedCommand): void {
    this._queue.push(command)
  }
  
  // 弹出所有可编辑命令（用户可以修改排队的输入）
  popAllEditable(currentInput: string, cursorOffset: number): QueuedCommand[] {
    const editable = this._queue.filter(cmd => this.isQueuedCommandEditable(cmd))
    this._queue = this._queue.filter(cmd => !this.isQueuedCommandEditable(cmd))
    return editable
  }
  
  isQueuedCommandEditable(cmd: QueuedCommand): boolean {
    // 用户输入可编辑，Hook 消息不可编辑
    return cmd.type === 'user_input' && cmd.editable
  }
}
```

**设计洞察：**
- 用户可以在 Agent 思考时提前输入下一个指令
- 排队的输入可以被编辑或删除
- 通知消息有独立队列，不干扰主队列

### 4.3 StreamingToolExecutor 并发执行

**并发控制算法：信号量 + 流式输出**

```typescript
class StreamingToolExecutor {
  async* execute(
    toolCalls: ToolCall[],
    options: ExecutionOptions
  ): AsyncIterator<ToolResult> {
    const { maxConcurrency, canUseTool, signal } = options
    
    // 分区：并发 vs 串行
    const { concurrent, sequential } = partitionToolCalls(toolCalls)
    
    // 并发执行（信号量控制）
    const semaphore = new Semaphore(maxConcurrency)
    const concurrentResults = concurrent.map(async (call) => {
      await semaphore.acquire()
      try {
        // 权限检查
        const allowed = await canUseTool(call.tool, call.input)
        if (!allowed) {
          return { toolUseId: call.id, content: 'Permission denied', isError: true }
        }
        
        // 执行工具
        const result = await call.tool.execute(call.input, signal)
        return { toolUseId: call.id, content: result, isError: false }
      } finally {
        semaphore.release()
      }
    })
    
    // 流式返回结果（先到先得）
    for await (const result of yieldAsCompleted(concurrentResults)) {
      yield result
    }
    
    // 串行执行
    for (const call of sequential) {
      const allowed = await canUseTool(call.tool, call.input)
      if (!allowed) {
        yield { toolUseId: call.id, content: 'Permission denied', isError: true }
        continue
      }
      const result = await call.tool.execute(call.input, signal)
      yield { toolUseId: call.id, content: result, isError: false }
    }
  }
}
```

**设计要点：**
- 使用信号量控制并发数（默认 5）
- 流式返回结果，不等待所有工具完成
- 权限检查嵌入执行流水线
- 支持取消（AbortSignal）

### 4.4 onBeforeQuery Hook 注入

**Hook 执行时机：API 调用前的最后机会**

```typescript
async function executeBeforeQueryHooks(context: QueryContext): Promise<void> {
  // 1. 执行 PostSamplingHooks（修改 messages/systemPrompt）
  const { messages, systemPrompt } = await executePostSamplingHooks(
    context.messages,
    context.systemPrompt,
    context.userContext,
    context.systemContext
  )
  
  // 2. 注入 Hook 消息
  const hookMessages = await context.pendingHookMessages
  messages.push(...hookMessages)
  
  // 3. 上下文预算检查
  await enforceToolResultBudget(messages, context.contentReplacements)
  
  // 4. 更新 context
  context.messages = messages
  context.systemPrompt = systemPrompt
}
```

**设计洞察：**
- Hook 可以修改即将发送的消息
- Hook 可以注入额外的系统提示
- Hook 可以添加新消息（如记忆、上下文）
- 预算检查在 Hook 之后，确保最终消息符合限制

### 4.5 onTurnComplete Hook 后处理

**Turn 完成后的清理和优化**

```typescript
async function executeTurnCompleteHooks(context: TurnContext): Promise<void> {
  // 1. 记忆提取
  if (shouldExtractMemory(context.messages)) {
    await extractMemories(context.messages, context.memoryDir)
  }
  
  // 2. 启动 Speculation（预执行）
  if (context.speculationEnabled && context.suggestions.length > 0) {
    await startSpeculation(context.suggestions[0])
  }
  
  // 3. 检查是否需要 Compact
  const needsCompact = await checkCompactNeed(context.messages, context.tokenBudget)
  if (needsCompact) {
    await compactConversation(context.messages)
  }
  
  // 4. 遥测上报
  await logTurnMetrics(context.metrics)
  
  // 5. 释放 QueryGuard 锁
  context.queryGuard.release()
}
```

**设计要点：**
- 记忆提取不阻塞主循环（异步执行）
- Speculation 在 Turn 完成后启动，利用空闲时间
- Compact 检查基于 token 预算和消息数量
- 遥测数据包含完整的 Turn 性能指标

---

## 5. 设计决策

### 5.1 为什么用 React 组件而非传统循环？

**决策：React 组件 > 命令式循环**

**理由：**

1. **状态管理自动化**
   - React 的 `useState` 自动触发重渲染
   - 不需要手动管理状态同步
   - 状态变更自动反映到 UI

2. **生命周期清晰**
   - `useEffect` 处理初始化和清理
   - 依赖数组自动追踪变化
   - 避免内存泄漏

3. **可组合性**
   - REPL 可以嵌套子组件
   - Hook 可以复用逻辑
   - 测试更容易

**权衡：**
- 学习曲线：需要理解 React 模型
- 性能开销：React 渲染有额外成本
- 但收益远大于成本

### 5.2 为什么需要 QueryGuard 互斥锁？

**决策：互斥锁 > 无锁并发**

**理由：**

1. **防止状态竞争**
   - 两个 Query 同时修改 messages 会导致不一致
   - API 响应顺序不确定

2. **简化错误处理**
   - 单线程执行，错误处理简单
   - 不需要考虑并发异常

3. **用户体验**
   - 用户期望 Agent 一次只做一件事
   - 并发执行会让 UI 混乱

**权衡：**
- 吞吐量降低：不能并发处理多个请求
- 但 Agent 场景下，串行执行更符合预期

### 5.3 为什么 MessageQueueManager 支持编辑？

**决策：可编辑队列 > 只读队列**

**理由：**

1. **用户体验优化**
   - 用户可能在排队后改变主意
   - 可以修改或删除排队的输入

2. **减少无效请求**
   - 避免执行用户不再需要的命令
   - 节省 API 调用成本

3. **灵活性**
   - 支持批量操作（`popAllEditable`）
   - 支持条件过滤（`dequeue(filter)`）

**权衡：**
- 实现复杂度增加
- 但用户体验提升显著

### 5.4 为什么 StreamingToolExecutor 流式返回？

**决策：流式返回 > 批量返回**

**理由：**

1. **降低延迟**
   - 工具完成后立即返回，不等待其他工具
   - 用户更快看到进度

2. **并发优化**
   - 先完成的工具先返回给 LLM
   - LLM 可以提前开始下一轮思考

3. **内存效率**
   - 不需要缓存所有结果
   - 流式处理减少内存峰值

**权衡：**
- 实现复杂度：需要 AsyncIterator
- 但性能提升明显

### 5.5 为什么 Hook 分为 onBeforeQuery 和 onTurnComplete？

**决策：两阶段 Hook > 单一 Hook**

**理由：**

1. **职责分离**
   - `onBeforeQuery`：修改输入（messages, systemPrompt）
   - `onTurnComplete`：后处理（记忆、压缩、遥测）

2. **性能优化**
   - `onBeforeQuery` 必须同步执行（阻塞 API 调用）
   - `onTurnComplete` 可以异步执行（不阻塞下一个 Turn）

3. **扩展性**
   - 不同 Hook 有不同的上下文需求
   - 两阶段设计更灵活

**权衡：**
- API 复杂度增加
- 但扩展性和性能都得到提升

---

## 6. 参考实现

### 6.1 Claude Code 源码位置

| 组件 | 文件路径 | 关键函数 |
|------|----------|----------|
| **REPL** | `src/cli/repl.tsx` | `REPL()`, `useDeferredHookMessages()`, `computeTools()` |
| **QueryEngine** | `src/QueryEngine.ts` | `constructor()`, `query()`, `tracking()` |
| **Query 执行** | `src/query.ts` | `isWithheldMaxOutputTokens()` |
| **QueryGuard** | `src/QueryGuard.ts` | `reserve()`, `release()`, `idle()`, `_notify()` |
| **QueryProfiler** | `src/queryProfiler.ts` | `startQueryProfile()`, `queryCheckpoint()`, `getSlowWarning()` |
| **MessageQueue** | `src/messageQueueManager.ts` | `enqueue()`, `dequeue()`, `popAllEditable()` |
| **QueryContext** | `src/queryContext.ts` | `fetchSystemPromptParts()`, `buildSideQuestionFallbackParams()` |
| **PostSamplingHooks** | `src/postSamplingHooks.ts` | `executePostSamplingHooks()`, `registerPostSamplingHook()` |
| **GroupedToolUses** | `src/groupToolUses.ts` | `applyGrouping()`, `getToolUseInfo()` |

### 6.2 关键函数签名

**REPL 组件**

```typescript
// src/cli/repl.tsx
function REPL(props: REPLProps): JSX.Element

// Hook 消息延迟注入
function useDeferredHookMessages(
  pendingHookMessages: Promise<HookResultMessage[]>,
  setMessages: (messages: Message[]) => void
): void

// 动态工具集计算
function computeTools(
  initialTools: Tool[],
  mcpClients: McpClient[],
  permissionMode: PermissionMode
): Tool[]
```

**QueryEngine**

```typescript
// src/QueryEngine.ts
class QueryEngine {
  constructor(config: QueryEngineConfig)
  
  async query(params: QueryParams): Promise<QueryResponse>
  
  tracking(event: 'tool_discovered', toolName: string): void
  
  createAbortController(parent?: AbortController): AbortController
}
```

**QueryGuard**

```typescript
// src/QueryGuard.ts
class QueryGuard {
  createSignal(): AbortSignal
  idle(): boolean
  async reserve(): Promise<void>
  release(): void
  private _notify(): void
}
```

**MessageQueueManager**

```typescript
// src/messageQueueManager.ts
class MessageQueueManager {
  enqueue(command: QueuedCommand): void
  enqueuePendingNotification(command: QueuedCommand): void
  dequeue(filter?: (cmd: QueuedCommand) => boolean): QueuedCommand | null
  dequeueAll(): QueuedCommand[]
  peek(filter?: (cmd: QueuedCommand) => boolean): QueuedCommand | null
  remove(commandsToRemove: QueuedCommand[]): void
  popAllEditable(currentInput: string, cursorOffset: number): QueuedCommand[]
  isQueuedCommandEditable(cmd: QueuedCommand): boolean
  isQueuedCommandVisible(cmd: QueuedCommand): boolean
  isSlashCommand(cmd: QueuedCommand): boolean
}
```

**QueryContext**

```typescript
// src/queryContext.ts
async function fetchSystemPromptParts(params: {
  tools: Tool[]
  mainLoopModel: string
  additionalWorkingDirectories: string[]
  mcpClients: McpClient[]
  customSystemPrompt?: string
}): Promise<SystemPromptParts>

function buildSideQuestionFallbackParams(params: {
  tools: Tool[]
  commands: Command[]
  mcpClients: McpClient[]
  messages: Message[]
  readFileState: FileState
  getAppState: () => AppState
  setAppState: (state: AppState) => void
}): SideQueryParams
```

**PostSamplingHooks**

```typescript
// src/postSamplingHooks.ts
function registerPostSamplingHook(hook: PostSamplingHook): void

function clearPostSamplingHooks(): void

async function executePostSamplingHooks(
  messages: Message[],
  systemPrompt: string,
  userContext: Record<string, string>,
  systemContext: Record<string, string>,
  toolUseContext: ToolUseContext,
  querySource: QuerySource
): Promise<{
  messages: Message[]
  systemPrompt: string
}>
```

### 6.3 设计模式应用

**1. 状态机模式（State Machine）**

REPL 循环本身就是一个状态机，状态转换清晰：

```
IDLE → QUEUED → PREPARING → QUERYING → EXECUTING_TOOLS 
  → PROCESSING_RESULTS → TURN_COMPLETE → IDLE
```

**2. 观察者模式（Observer）**

Hook 系统是观察者模式的实现：
- `onBeforeQuery` 和 `onTurnComplete` 是观察点
- 外部可以注册回调函数
- 状态变化时自动通知

**3. 策略模式（Strategy）**

权限检查使用策略模式：
- `canUseTool` 函数是策略接口
- 不同权限模式（Auto/Plan/Default）是不同策略
- 运行时动态切换

**4. 生产者-消费者模式（Producer-Consumer）**

MessageQueueManager 实现生产者-消费者：
- 用户输入是生产者
- REPL 循环是消费者
- 队列解耦生产和消费

**5. 互斥锁模式（Mutex）**

QueryGuard 是经典的互斥锁：
- `reserve()` 加锁
- `release()` 解锁
- Promise 队列实现等待

---

## 7. 实现检查清单

### 7.1 必须实现的功能

**核心循环**
- [ ] REPL 组件（React 或等效状态管理）
- [ ] Turn 生命周期管理
- [ ] 状态机转换逻辑
- [ ] 消息历史管理

**QueryEngine**
- [ ] API 调用封装
- [ ] 配置驱动（model, maxTokens, temperature 等）
- [ ] AbortController 支持
- [ ] 流式响应处理

**QueryGuard**
- [ ] 互斥锁实现
- [ ] Promise 等待队列
- [ ] `reserve()` 和 `release()` 方法
- [ ] `idle()` 状态查询

**MessageQueueManager**
- [ ] 入队/出队操作
- [ ] 可编辑队列支持
- [ ] 条件过滤
- [ ] 通知队列分离

**StreamingToolExecutor**
- [ ] 并发执行控制
- [ ] 流式结果返回
- [ ] 权限检查集成
- [ ] AbortSignal 支持

**Hook 系统**
- [ ] `onBeforeQuery` 注入点
- [ ] `onTurnComplete` 注入点
- [ ] Hook 注册机制
- [ ] Hook 执行顺序保证

### 7.2 可选的优化

**性能优化**
- [ ] QueryProfiler 性能监控
- [ ] 慢操作警告
- [ ] 分阶段计时
- [ ] 性能报告生成

**用户体验**
- [ ] 工具调用分组显示
- [ ] 进度实时更新
- [ ] 可编辑队列 UI
- [ ] 取消操作支持

**扩展性**
- [ ] PostSamplingHooks 支持
- [ ] 动态工具集计算
- [ ] MCP 客户端集成
- [ ] 多 Agent 支持

**可观测性**
- [ ] 遥测数据收集
- [ ] 错误追踪
- [ ] 调试日志
- [ ] VCR 录制重放

### 7.3 测试验证点

**单元测试**
- [ ] QueryGuard 互斥锁正确性
- [ ] MessageQueueManager 队列操作
- [ ] StreamingToolExecutor 并发控制
- [ ] Hook 执行顺序

**集成测试**
- [ ] 完整 Turn 生命周期
- [ ] 多轮对话流程
- [ ] 工具调用链
- [ ] 错误恢复

**性能测试**
- [ ] 并发工具执行延迟
- [ ] 队列吞吐量
- [ ] 内存使用峰值
- [ ] 长会话稳定性

**边界测试**
- [ ] 快速连续输入
- [ ] 大量工具并发
- [ ] 超长消息历史
- [ ] 网络中断恢复

---

## 8. 总结

### 8.1 核心洞察

1. **React 组件即 Loop**
   - Agent Loop 不是命令式循环，而是声明式状态机
   - React 的状态管理天然适合 Agent 场景

2. **Hook 注入点是扩展边界**
   - `onBeforeQuery` 和 `onTurnComplete` 提供完整的扩展能力
   - 外部可以修改输入、处理输出、注入逻辑

3. **互斥锁保证一致性**
   - QueryGuard 防止并发 Query 导致的状态竞争
   - 简化错误处理，提升用户体验

4. **流式处理降低延迟**
   - StreamingToolExecutor 流式返回结果
   - 不等待所有工具完成，先完成先返回

5. **队列解耦生产消费**
   - MessageQueueManager 解耦用户输入和 Agent 执行
   - 支持编辑、过滤、批量操作

### 8.2 实现建议

**从简单到复杂**
1. 先实现基础 REPL 循环（无 Hook）
2. 添加 QueryGuard 互斥锁
3. 实现 MessageQueueManager
4. 添加 StreamingToolExecutor
5. 最后实现 Hook 系统

**关键难点**
- QueryGuard 的 Promise 等待队列
- StreamingToolExecutor 的并发控制
- Hook 的执行时机和顺序
- 状态机的正确转换

**调试技巧**
- 使用 QueryProfiler 定位性能瓶颈
- 记录完整的状态转换日志
- 使用 VCR 录制重放调试
- 单元测试覆盖边界情况

### 8.3 与其他文档的关联

- **前置阅读**：[01-OVERVIEW.md](01-OVERVIEW.md) — 理解 Harness 和 Turn 的概念
- **后续阅读**：
  - [03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md) — 工具系统的详细设计
  - [04-CONTEXT-ENGINE.md](04-CONTEXT-ENGINE.md) — 上下文管理的三层防线
  - [05-HOOK-SYSTEM.md](05-HOOK-SYSTEM.md) — Hook 系统的完整设计
  - [06-PERMISSION.md](06-PERMISSION.md) — 权限系统的安全管道

---

**文档版本**：v1.0  
**最后更新**：2026-04-01  
**维护者**：Reverse Engineering Lab
