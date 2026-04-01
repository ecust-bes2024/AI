# 12. 设计哲学与方法论

## 文档定位

本文档提炼 Claude Code Agent 编排系统的**设计哲学**和**可复用方法论**。不是具体实现细节,而是指导思想——为什么这样设计、权衡了什么、如何应用到其他 Agent 系统。

**目标读者**: 需要构建 Agent 编排系统的架构师和开发者。

---

## 1. 核心概念

### 1.1 什么是设计哲学

设计哲学是**架构决策背后的价值观和原则**。Claude Code 的设计哲学体现在:

- **上下文管理 > 模型能力**: 再强的模型也会被糟糕的上下文管理拖垮
- **React 组件即 Loop**: 声明式状态管理天然适合 Agent 循环
- **权限即管道**: 安全检查嵌入执行流,而非前置门卫
- **文件系统即数据库**: 简单、可审计、可手动修复
- **AbortController 树状传播**: 级联取消信号的优雅实现
- **错误类型即领域语言**: 错误继承树比日志更有表达力
- **渐进式自动化**: Manual → Plan → Auto → Speculation 的安全梯度

### 1.2 为什么需要设计哲学

Agent 系统的复杂度来自**不确定性**:

- LLM 输出不可预测
- 工具执行可能失败
- 用户随时可能中断
- 上下文随时可能爆炸

设计哲学提供**一致的决策框架**,让团队在面对新问题时能快速达成共识。

---

## 2. 七个核心原则

### 原则 1: 上下文管理 > 模型能力

**核心观点**: 再强的模型,如果上下文管理不当,也会表现糟糕。

#### 设计体现

Claude Code 的上下文管理是**三层防线**:

```
第一层: 预防 (contextSuggestions)
  ├─ checkNearCapacity() — 接近上限时警告
  ├─ checkLargeToolResults() — 检测工具输出膨胀
  ├─ checkReadResultBloat() — 检测文件读取膨胀
  └─ checkMemoryBloat() — 检测记忆膨胀

第二层: 压缩 (ToolResultStorage)
  ├─ 大工具输出替换为文件引用
  ├─ 持久化到 ~/.claude/sessions/{id}/tool-results/
  └─ reconstructContentReplacementState() 可重建

第三层: 兜底 (Compact)
  ├─ 对话历史压缩
  ├─ 保留关键转折点
  └─ 生成 CompactMessage 注入上下文
```

#### 方法论启示

**在设计 Agent 系统时**:

1. **预算先行**: 在架构设计阶段就考虑 token 预算,而非事后补救
2. **分层防御**: 预防 > 压缩 > 兜底,每层有明确的触发条件
3. **可观测性**: 提供 `contextSuggestions` 让用户感知上下文健康度
4. **可重建性**: 压缩后的状态必须能从持久化数据中恢复

#### 反模式

❌ **等到 API 报错才处理**: 此时已经浪费了一次 API 调用
❌ **简单截断**: 丢失关键上下文会导致 Agent 失忆
❌ **无差别压缩**: 工具输出、用户消息、系统提示的重要性不同

---

### 原则 2: React 组件即 Loop

**核心观点**: Agent Loop 不是 `while(true)`,而是 React 组件。

#### 设计体现

```typescript
// REPL.tsx 是一个 React 组件
function REPL({
  commands,
  initialTools,
  initialMessages,
  pendingHookMessages,  // ← Hook 消息异步注入
  onBeforeQuery,        // ← Loop 级 Hook
  onTurnComplete,       // ← Loop 级 Hook
  ...
}) {
  const [messages, setMessages] = useState(initialMessages)
  const [tools, setTools] = useState(initialTools)
  
  // 状态变化驱动渲染和执行
  useEffect(() => {
    // 消息变化时触发新的 Turn
  }, [messages])
  
  return <ReplUI messages={messages} tools={tools} />
}
```

#### 为什么 React 适合 Agent Loop

| React 特性 | Agent Loop 需求 | 匹配度 |
|-----------|----------------|--------|
| 声明式状态管理 | messages/tools 是不断变化的状态 | ✅ 完美 |
| 生命周期钩子 | onBeforeQuery/onTurnComplete | ✅ 完美 |
| 组件化 | Tool/Command/Hook 都是组件 | ✅ 完美 |
| 虚拟 DOM | 终端 UI 需要差量渲染 | ✅ Ink 实现 |

#### 方法论启示

**在设计 Agent 系统时**:

1. **状态驱动**: 不要写命令式的循环,让状态变化驱动执行
2. **生命周期**: 明确定义 Loop 的生命周期阶段 (init/query/execute/complete)
3. **可组合**: 每个能力(Tool/Hook)都应该是独立的组件
4. **可测试**: React 组件天然易于单元测试

#### 对比传统 while 循环

```python
# ❌ 传统方式: 命令式循环
while True:
    user_input = input()
    response = llm.query(messages + [user_input])
    for tool_call in response.tool_calls:
        result = execute_tool(tool_call)
        messages.append(result)
```

问题:
- 状态散落在循环体内
- 难以注入 Hook
- 难以测试
- 难以可视化

```typescript
// ✅ React 方式: 声明式状态
function AgentLoop() {
  const [messages, setMessages] = useState([])
  
  useEffect(() => {
    // 消息变化时自动触发
    if (needsQuery(messages)) {
      queryLLM(messages).then(response => {
        setMessages([...messages, response])
      })
    }
  }, [messages])
  
  return <UI messages={messages} />
}
```

优势:
- 状态集中管理
- Hook 天然支持
- 易于测试
- 易于可视化

---

### 原则 3: 权限即管道

**核心观点**: 权限检查不是前置门卫,而是嵌入执行流水线的每个阶段。

#### 设计体现

```typescript
// 权限检查嵌入工具执行流
async function checkPermissionsAndCallTool(
  toolUse: ToolUse,
  canUseTool: CanUseToolFn,  // ← 权限函数作为参数
  tools: Tools,
  context: ToolUseContext
): Promise<ToolResult> {
  // 1. 权限检查
  const permission = await canUseTool(toolUse, context)
  
  if (permission === 'denied') {
    return { type: 'error', error: 'Permission denied' }
  }
  
  if (permission === 'ask') {
    // 2. 请求用户确认
    const approved = await askUser(toolUse)
    if (!approved) {
      return { type: 'error', error: 'User denied' }
    }
  }
  
  // 3. 执行工具
  return await executeTool(toolUse, tools, context)
}
```

#### 四级权限模式

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| Manual | 每次都问 | 新用户、敏感操作 |
| Plan | 批量审批 | 已知任务序列 |
| Auto (YOLO) | LLM 分类器自动决策 | 信任的工作流 |
| Speculation | 预执行 + 事后确认 | 高频操作优化 |

#### 方法论启示

**在设计 Agent 系统时**:

1. **管道化**: 权限检查是执行流的一部分,不是独立模块
2. **可配置**: 通过 `CanUseToolFn` 参数注入,支持不同策略
3. **分级**: 提供多级权限模式,让用户选择安全/效率平衡点
4. **可审计**: 所有权限决策都应该有日志

#### 反模式

❌ **前置门卫**: 在入口处一次性检查所有权限
```typescript
// ❌ 不好的设计
if (!hasPermission(user, 'write_file')) {
  throw new Error('No permission')
}
// ... 后续执行
```

问题:
- 权限检查和执行分离,难以维护
- 无法支持动态权限(如 YOLO 分类器)
- 无法支持细粒度权限(不同文件不同权限)

✅ **管道嵌入**: 权限检查在执行点
```typescript
// ✅ 好的设计
async function writeFile(path: string, content: string) {
  const permission = await canUseTool('write_file', { path })
  if (permission !== 'allowed') {
    return handlePermissionDenied()
  }
  // 执行
}
```

---

### 原则 4: 文件系统即数据库

**核心观点**: 用文件系统做状态持久化,不引入数据库依赖。

#### 设计体现

Claude Code 的所有持久化数据都在文件系统:

```
~/.claude/
├── sessions/{sessionId}/
│   ├── transcript.jsonl          # 对话历史
│   ├── tool-results/{id}.txt     # 工具输出
│   └── speculation-overlay/      # 预执行临时目录
├── tasks/{taskListId}/
│   ├── {taskId}.json             # 任务定义
│   └── high-water-marks.json    # 任务进度
├── plugins/
│   └── {pluginId}/{version}/     # 版本化插件缓存
└── settings.json                 # 用户配置
```

#### 为什么选择文件系统

| 需求 | 文件系统 | 数据库 |
|------|---------|--------|
| 简单性 | ✅ 无依赖 | ❌ 需要安装/配置 |
| 可审计 | ✅ 直接查看文件 | ❌ 需要查询工具 |
| 可修复 | ✅ 手动编辑 | ❌ 需要 SQL/工具 |
| 版本控制 | ✅ Git 友好 | ❌ 难以版本化 |
| 跨平台 | ✅ 所有 OS 支持 | ❌ 可能有兼容性问题 |

#### 方法论启示

**在设计 Agent 系统时**:

1. **目录即命名空间**: 用目录结构表达数据关系
2. **文件名即 ID**: `{taskId}.json` 比数据库主键更直观
3. **JSONL 即日志**: 追加式写入,天然支持时间序列
4. **版本化目录**: `{pluginId}/{version}/` 支持多版本共存

#### 适用场景

✅ **适合文件系统**:
- 配置文件
- 日志和历史记录
- 缓存数据
- 临时文件

❌ **不适合文件系统**:
- 高频写入 (>1000 QPS)
- 复杂查询 (JOIN/聚合)
- 事务性操作
- 大规模数据 (>100GB)

---

### 原则 5: AbortController 树状传播

**核心观点**: 取消信号应该从父任务级联传播到所有子任务。

#### 设计体现

```typescript
class StreamingToolExecutor {
  private parentAbortController: AbortController
  
  async execute(toolUses: ToolUse[]) {
    for (const toolUse of toolUses) {
      // 为每个工具创建子 AbortController
      const childController = this.createChildAbortController()
      
      try {
        await executeTool(toolUse, childController.signal)
      } catch (error) {
        if (error.name === 'AbortError') {
          // 取消信号传播
        }
      }
    }
  }
  
  private createChildAbortController(): AbortController {
    const child = new AbortController()
    
    // 父取消时,子也取消
    this.parentAbortController.signal.addEventListener('abort', () => {
      child.abort()
    })
    
    return child
  }
}
```

#### 取消传播树

```
QueryEngine (根 AbortController)
  ├─ StreamingToolExecutor (子 AbortController)
  │   ├─ Tool 1 (孙 AbortController)
  │   ├─ Tool 2 (孙 AbortController)
  │   └─ Tool 3 (孙 AbortController)
  └─ SideQuery (子 AbortController)
      └─ Background Task (孙 AbortController)
```

用户按 Ctrl+C → 根 AbortController.abort() → 所有子孙任务级联取消

#### 方法论启示

**在设计 Agent 系统时**:

1. **树状结构**: 每个异步任务都应该有父子关系
2. **信号传播**: 父取消时,所有子任务自动取消
3. **清理资源**: 监听 `abort` 事件,及时释放资源
4. **优雅降级**: 取消不是错误,而是正常流程

#### 实现模式

```typescript
// 通用的子 AbortController 创建函数
function createChildAbortController(
  parent: AbortController
): AbortController {
  const child = new AbortController()
  
  parent.signal.addEventListener('abort', () => {
    child.abort()
  })
  
  return child
}

// 使用示例
async function parentTask(signal: AbortSignal) {
  const childSignal = createChildAbortController(signal)
  
  await Promise.all([
    childTask1(childSignal),
    childTask2(childSignal),
    childTask3(childSignal),
  ])
}
```

---

### 原则 6: 错误类型即领域语言

**核心观点**: 错误继承树是领域建模的一部分，比日志更有表达力。

#### 设计体现

Claude Code 的错误类型体系：

```typescript
// 基类
class ClaudeError extends Error {
  constructor(message: string, public code: string) {
    super(message)
  }
}

// 领域错误
class AbortError extends ClaudeError {}
class MalformedCommandError extends ClaudeError {}
class ConfigParseError extends ClaudeError {}
class McpAuthError extends ClaudeError {}
class RipgrepTimeoutError extends ClaudeError {}
class ImageSizeError extends ClaudeError {}
class BridgeFatalError extends ClaudeError {}

// 统一分类入口
function classifyToolError(error: Error): ErrorCategory {
  if (error instanceof AbortError) return 'user_cancelled'
  if (error instanceof McpAuthError) return 'auth_failed'
  if (error instanceof RipgrepTimeoutError) return 'timeout'
  // ...
}
```

#### 为什么错误类型重要

| 方式 | 表达力 | 可处理性 | 可测试性 |
|------|--------|---------|---------|
| 字符串错误 | ❌ 弱 | ❌ 难以分类 | ❌ 难以 mock |
| 错误码 | ⚠️ 中等 | ⚠️ 需要查表 | ⚠️ 魔法数字 |
| 错误类型 | ✅ 强 | ✅ instanceof | ✅ 易于 mock |

#### 方法论启示

**在设计 Agent 系统时**:

1. **领域建模**: 每个领域有自己的错误子类
2. **统一分类**: 提供 `classifyError()` 统一入口
3. **携带上下文**: 错误对象包含足够的调试信息
4. **可恢复性**: 区分可恢复错误和致命错误

#### 错误设计清单

```typescript
// ✅ 好的错误设计
class ToolExecutionError extends ClaudeError {
  constructor(
    message: string,
    public toolName: string,
    public toolUse: ToolUse,
    public cause?: Error
  ) {
    super(message, 'TOOL_EXECUTION_ERROR')
  }
  
  // 提供恢复建议
  getRecoverySuggestion(): string {
    return `Try re-running ${this.toolName} with different parameters`
  }
}

// ❌ 不好的错误设计
throw new Error('Tool failed')  // 信息不足
```

---

### 原则 7: 渐进式自动化

**核心观点**: 从手动到全自动，提供安全梯度，让用户选择信任级别。

#### 四级自动化梯度

```
Manual Mode (手动)
  ↓ 用户熟悉后
Plan Mode (批量审批)
  ↓ 建立信任后
Auto Mode (YOLO 分类器)
  ↓ 高频操作优化
Speculation (预执行)
```

#### 每级的安全机制

| 级别 | 执行前 | 执行中 | 执行后 |
|------|--------|--------|--------|
| Manual | 每次询问 | 可中断 | 显示结果 |
| Plan | 批量审批 | 可中断 | 显示结果 |
| Auto | LLM 分类器 | 可中断 | 显示结果 + 审计日志 |
| Speculation | 预执行 | Overlay FS 隔离 | 用户确认后合并 |

#### YOLO Classifier 设计

```typescript
// 轻量级 LLM 分类器
async function classifyYoloAction(
  toolUse: ToolUse,
  context: Context,
  model: 'haiku'  // 使用快速模型
): Promise<'allow' | 'deny' | 'ask'> {
  const prompt = buildClassifierPrompt(toolUse, context)
  const response = await llm.query(prompt, { 
    model,
    max_tokens: 10,  // 只需要简单分类
    output_format: 'xml'  // 结构化输出
  })
  
  return parseClassifierResponse(response)
}
```

#### 方法论启示

**在设计 Agent 系统时**:

1. **默认保守**: 新用户默认 Manual Mode
2. **渐进升级**: 提供明确的升级路径
3. **随时降级**: 用户可以随时回到更安全的模式
4. **透明审计**: Auto/Speculation 模式必须有完整日志

#### Speculation 的安全设计

```typescript
// Overlay FS 隔离
async function startSpeculation(toolUse: ToolUse) {
  const overlayDir = createTempDir()
  
  try {
    // 在隔离环境中预执行
    const result = await executeInOverlay(toolUse, overlayDir)
    
    // 请求用户确认
    const approved = await askUser(`Apply speculation result?`)
    
    if (approved) {
      // 原子合并到主文件系统
      await copyOverlayToMain(overlayDir)
      return { success: true, timeSaved: result.duration }
    } else {
      // 丢弃预执行结果
      await safeRemoveOverlay(overlayDir)
      return { success: false }
    }
  } catch (error) {
    // 失败安全：不污染主文件系统
    await safeRemoveOverlay(overlayDir)
    throw error
  }
}
```

---

## 3. 可复用设计模式

### 模式 1: Strategy 风暴

**问题**: 系统需要支持多种运行模式（权限模式、传输协议、错误处理策略）。

**解决方案**: 用 Strategy 模式实现一切可替换性。

#### 应用场景

| 场景 | Strategy 接口 | 实现类 |
|------|--------------|--------|
| 权限模式 | `CanUseToolFn` | Manual/Plan/Auto/Speculation |
| 传输协议 | `Transport` | WebSocket/HTTP/InProcess |
| 错误处理 | `ErrorHandler` | Retry/Fallback/Abort |
| 分类器 | `Classifier` | TwoStage/SingleStage |

#### 实现模板

```typescript
// 1. 定义 Strategy 接口
interface PermissionStrategy {
  canUseTool(toolUse: ToolUse, context: Context): Promise<Permission>
}

// 2. 实现具体策略
class ManualPermission implements PermissionStrategy {
  async canUseTool(toolUse, context) {
    return await askUser(toolUse)
  }
}

class AutoPermission implements PermissionStrategy {
  async canUseTool(toolUse, context) {
    return await yoloClassifier.classify(toolUse, context)
  }
}

// 3. 上下文使用策略
class ToolExecutor {
  constructor(private strategy: PermissionStrategy) {}
  
  async execute(toolUse: ToolUse) {
    const permission = await this.strategy.canUseTool(toolUse, context)
    if (permission === 'allowed') {
      return await executeTool(toolUse)
    }
  }
}
```

#### 何时使用

✅ **适合 Strategy**:
- 需要运行时切换行为
- 多种算法可互换
- 避免大量 if/else

❌ **不适合 Strategy**:
- 只有一种实现
- 行为固定不变
- 过度抽象

---

### 模式 2: Hook 注入点

**问题**: 系统需要可扩展，但不想暴露内部实现。

**解决方案**: 在关键生命周期点提供 Hook 注入。

#### Claude Code 的 5 层 Hook

```
Layer 1: Tool 级 Hook
  ├─ PreToolUse: 工具执行前
  └─ PostToolUse: 工具执行后

Layer 2: Message 级 Hook
  └─ PostSamplingHooks: API 调用前修改消息

Layer 3: Loop 级 Hook
  ├─ onBeforeQuery: Query 前
  └─ onTurnComplete: Turn 完成后

Layer 4: Session 级 Hook
  ├─ onSessionStart
  └─ onSessionEnd

Layer 5: UI 级 Hook
  ├─ StatusLine: 状态栏更新
  ├─ FileSuggestion: 文件建议
  └─ Elicitation: 请求用户输入
```

#### 实现模板

```typescript
// 1. 定义 Hook 接口
interface Hook<T> {
  name: string
  execute(context: T): Promise<void> | void
}

// 2. Hook 注册表
class HookRegistry<T> {
  private hooks: Map<string, Hook<T>[]> = new Map()
  
  register(event: string, hook: Hook<T>) {
    if (!this.hooks.has(event)) {
      this.hooks.set(event, [])
    }
    this.hooks.get(event)!.push(hook)
  }
  
  async trigger(event: string, context: T) {
    const hooks = this.hooks.get(event) || []
    for (const hook of hooks) {
      await hook.execute(context)
    }
  }
}

// 3. 在关键点触发
class AgentLoop {
  constructor(private hooks: HookRegistry<Context>) {}
  
  async executeTurn() {
    await this.hooks.trigger('beforeQuery', context)
    const response = await this.query()
    await this.hooks.trigger('afterQuery', { ...context, response })
  }
}
```

#### 何时使用

✅ **适合 Hook**:
- 需要第三方扩展
- 不想暴露内部实现
- 多个扩展点需要协调

❌ **不适合 Hook**:
- 核心逻辑（不应该可被覆盖）
- 性能敏感路径
- 简单的回调就够了

---

### 模式 3: 分层存储

**问题**: 工具输出可能很大，全部放内存会爆炸。

**解决方案**: 根据大小分层存储（内存 → 文件 → 引用）。

#### 三层存储策略

```typescript
class ToolResultStorage {
  // 阈值配置
  private readonly INLINE_THRESHOLD = 4000      // 4KB 以下内联
  private readonly PERSIST_THRESHOLD = 100000   // 100KB 以上持久化
  
  async store(toolResult: ToolResult): Promise<StoredResult> {
    const size = toolResult.content.length
    
    if (size < this.INLINE_THRESHOLD) {
      // 小结果：直接内联
      return { type: 'inline', content: toolResult.content }
    }
    
    if (size < this.PERSIST_THRESHOLD) {
      // 中等结果：压缩后内联
      const compressed = await compress(toolResult.content)
      return { type: 'compressed', content: compressed }
    }
    
    // 大结果：持久化到文件，返回引用
    const path = await this.persistToFile(toolResult)
    return { 
      type: 'reference', 
      path,
      summary: toolResult.content.slice(0, 500) + '...'
    }
  }
  
  private async persistToFile(result: ToolResult): Promise<string> {
    const path = this.getToolResultPath(result.id)
    await fs.writeFile(path, result.content)
    return path
  }
}
```

#### 重建机制

```typescript
// 从持久化数据重建状态
async function reconstructContentReplacementState(
  messages: Message[]
): Promise<Map<string, StoredResult>> {
  const state = new Map()
  
  for (const msg of messages) {
    if (msg.type === 'tool_result' && msg.content.type === 'reference') {
      // 从文件恢复
      const content = await fs.readFile(msg.content.path, 'utf-8')
      state.set(msg.id, { type: 'inline', content })
    }
  }
  
  return state
}
```

#### 何时使用

✅ **适合分层存储**:
- 数据大小差异大（KB 到 GB）
- 内存有限
- 需要持久化

❌ **不适合分层存储**:
- 数据大小均匀
- 内存充足
- 不需要持久化

---

### 模式 4: 消息队列管理

**问题**: 用户可能在 Agent 思考时输入下一个指令，需要排队处理。

**解决方案**: 输入消息先入队，支持编辑、删除、优先级。

#### 队列设计

```typescript
class MessageQueueManager {
  private queue: QueuedCommand[] = []
  private pendingNotifications: QueuedCommand[] = []
  
  // 入队
  enqueue(command: Command) {
    this.queue.push({ command, timestamp: Date.now() })
  }
  
  // 通知单独队列
  enqueuePendingNotification(command: Command) {
    this.pendingNotifications.push({ command, timestamp: Date.now() })
  }
  
  // 出队（支持过滤）
  dequeue(filter?: (cmd: Command) => boolean): Command | null {
    const index = filter 
      ? this.queue.findIndex(item => filter(item.command))
      : 0
    
    if (index >= 0) {
      return this.queue.splice(index, 1)[0].command
    }
    return null
  }
  
  // 弹出所有可编辑命令
  popAllEditable(currentInput: string, cursorOffset: number): Command[] {
    const editable = this.queue.filter(item => 
      this.isQueuedCommandEditable(item.command)
    )
    this.queue = this.queue.filter(item => 
      !this.isQueuedCommandEditable(item.command)
    )
    return editable.map(item => item.command)
  }
  
  // 移除指定命令
  remove(commandsToRemove: Command[]) {
    this.queue = this.queue.filter(item => 
      !commandsToRemove.includes(item.command)
    )
  }
}
```

#### 何时使用

✅ **适合消息队列**:
- 异步输入（用户可能连续输入）
- 需要优先级排序
- 需要编辑/撤销

❌ **不适合消息队列**:
- 同步处理就够了
- 不需要排队
- 简单的 FIFO 就够了

---

### 模式 5: 并发工具调用分组

**问题**: LLM 一次返回多个工具调用，如何优雅地展示和执行？

**解决方案**: 按语义分组，UI 聚合显示，执行时控制并发度。

#### 分组策略

```typescript
// 工具调用分组
function groupToolUses(toolUses: ToolUse[]): ToolGroup[] {
  const groups: ToolGroup[] = []
  
  // 按工具类型分组
  const byType = new Map<string, ToolUse[]>()
  for (const toolUse of toolUses) {
    const type = toolUse.name
    if (!byType.has(type)) {
      byType.set(type, [])
    }
    byType.get(type)!.push(toolUse)
  }
  
  // 生成分组描述
  for (const [type, uses] of byType) {
    if (uses.length === 1) {
      groups.push({ 
        description: `${type}`, 
        toolUses: uses 
      })
    } else {
      groups.push({ 
        description: `${type} (${uses.length} files)`, 
        toolUses: uses 
      })
    }
  }
  
  return groups
}

// 并发执行控制
async function executeToolGroups(
  groups: ToolGroup[],
  maxConcurrency: number = 3
): Promise<ToolResult[]> {
  const results: ToolResult[] = []
  
  for (const group of groups) {
    // 每组内并发执行
    const groupResults = await Promise.all(
      group.toolUses.slice(0, maxConcurrency).map(executeTool)
    )
    results.push(...groupResults)
    
    // 剩余的串行执行
    for (let i = maxConcurrency; i < group.toolUses.length; i++) {
      const result = await executeTool(group.toolUses[i])
      results.push(result)
    }
  }
  
  return results
}
```

#### 何时使用

✅ **适合分组**:
- 批量操作（读取多个文件）
- 需要 UI 聚合
- 需要控制并发度

❌ **不适合分组**:
- 单个操作
- 不需要 UI 优化
- 必须严格串行

---

## 4. 方法论启示

### 4.1 构建 Agent CLI 的十条原则

从 Claude Code 的设计中提炼出的通用原则：

1. **从 Tool Schema 开始设计**
   - Tool 的 JSON Schema 就是你的 API 契约
   - 先定义工具能力，再考虑 UI 和交互

2. **权限模型是一等公民**
   - 设计 3-4 个 Permission Mode
   - 用 Strategy 模式实现
   - 提供渐进式自动化路径

3. **Hook 系统比 Plugin 系统更重要**
   - 先用 Hook 实现可扩展性
   - 再考虑完整的 Plugin 架构
   - 5 层 Hook 覆盖所有扩展点

4. **上下文管理是核心竞争力**
   - 三层防线：预防 → 压缩 → 兜底
   - 分层存储：内存 → 文件 → 引用
   - 可重建性：所有状态可从持久化数据恢复

5. **用文件系统做状态持久化**
   - 不引入数据库依赖
   - 简单、可审计、可手动修复
   - 版本化目录结构

6. **终端 UI 选 React + Ink**
   - 复用 React 生态的组件化思维
   - 声明式状态管理
   - 差量渲染优化

7. **错误类型体系 = 领域建模**
   - 每个领域有自己的错误子类
   - 提供统一的 `classifyError()` 入口
   - 错误对象携带足够的调试信息

8. **AbortController 树状传播**
   - 从根任务到叶子任务的级联取消
   - 每个异步操作都应该支持取消
   - 清理资源和优雅降级

9. **Speculation 是高价值优化**
   - Overlay FS + 预执行
   - 原子合并到主文件系统
   - 可显著减少等待时间

10. **渐进式自动化**
    - Manual → Plan → Auto → Speculation
    - 每级有明确的安全机制
    - 用户可随时升级或降级

---

### 4.2 架构决策记录（ADR）模板

基于 Claude Code 的设计经验，提供 ADR 模板：

```markdown
# ADR-001: 选择 React 作为 Agent Loop 实现

## 状态
已采纳

## 背景
Agent Loop 需要管理复杂的状态（messages, tools, permissions），
传统的 while 循环难以维护和测试。

## 决策
使用 React 组件实现 Agent Loop，用 useState/useEffect 管理状态。

## 理由
1. 声明式状态管理，代码更清晰
2. 生命周期钩子天然支持扩展
3. 组件化设计，易于测试
4. Ink 框架提供终端 UI 支持

## 后果
- 正面：代码可维护性提升，测试覆盖率提高
- 负面：引入 React 依赖，学习曲线
- 中性：需要团队熟悉 React Hooks

## 替代方案
1. 传统 while 循环：简单但难以扩展
2. 状态机：过于复杂，不适合 Agent 场景
```

---

### 4.3 设计检查清单

在设计 Agent 系统时，用这个清单自检：

#### 核心能力
- [ ] Tool 系统：JSON Schema 定义、注册、执行
- [ ] 权限系统：多级模式、Strategy 实现
- [ ] 上下文管理：三层防线、分层存储
- [ ] Hook 系统：5 层注入点、同步/异步

#### 可扩展性
- [ ] Plugin 架构：加载、验证、生命周期
- [ ] Skill 系统：声明式能力扩展
- [ ] Hook 注册：运行时添加/移除
- [ ] 配置系统：用户级/项目级配置

#### 安全性
- [ ] 权限检查：嵌入执行流水线
- [ ] 错误处理：类型化错误、统一分类
- [ ] 取消机制：AbortController 树状传播
- [ ] 审计日志：所有关键操作可追溯

#### 性能优化
- [ ] 并发控制：工具调用分组、限流
- [ ] 上下文压缩：Compact、ToolResultStorage
- [ ] 预执行：Speculation + Overlay FS
- [ ] 缓存策略：版本化缓存、Seed Cache

#### 用户体验
- [ ] 渐进式自动化：Manual → Plan → Auto → Speculation
- [ ] 消息队列：支持编辑、删除、优先级
- [ ] UI 聚合：工具调用分组显示
- [ ] 错误提示：清晰的错误信息和恢复建议

---

## 5. 常见反模式

### 反模式 1: 过早优化上下文

**症状**: 在没有遇到上下文问题前就引入复杂的压缩机制。

**问题**:
- 增加系统复杂度
- 可能引入 bug
- 维护成本高

**正确做法**:
1. 先实现基础功能
2. 监控上下文使用情况
3. 遇到问题时再优化
4. 从简单方案开始（如简单截断）

---

### 反模式 2: 权限检查前置门卫

**症状**: 在系统入口处一次性检查所有权限。

**问题**:
- 无法支持动态权限
- 无法支持细粒度控制
- 权限逻辑和业务逻辑分离

**正确做法**:
- 权限检查嵌入执行流水线
- 每个工具执行前检查
- 支持运行时权限策略切换

---

### 反模式 3: 同步阻塞的 Hook

**症状**: Hook 执行阻塞主流程，导致 Agent 卡顿。

**问题**:
- 用户体验差
- 一个慢 Hook 拖累整个系统
- 难以调试性能问题

**正确做法**:
- 提供异步 Hook 支持
- 关键路径的 Hook 设置超时
- 非关键 Hook 在后台执行

---

### 反模式 4: 字符串错误消息

**症状**: 用字符串表示错误，没有类型化。

**问题**:
- 难以分类处理
- 难以测试
- 难以国际化

**正确做法**:
- 定义错误类型继承树
- 提供统一的错误分类函数
- 错误对象携带上下文信息

---

### 反模式 5: 无限制的工具并发

**症状**: 允许 LLM 返回的所有工具调用同时执行。

**问题**:
- 资源耗尽（文件句柄、网络连接）
- 难以调试
- 用户难以理解发生了什么

**正确做法**:
- 设置并发上限（如 3-5 个）
- 按工具类型分组
- 提供 UI 聚合显示

---

## 6. 参考实现

### 6.1 Claude Code 源码位置

| 概念 | 源码文件 | 关键函数 |
|------|---------|---------|
| REPL 循环 | `REPL.tsx` | `REPL()` 组件 |
| 工具执行 | `StreamingToolExecutor.ts` | `execute()` |
| 权限检查 | `toolExecution.ts` | `checkPermissionsAndCallTool()` |
| 上下文管理 | `toolResultStorage.ts` | `persistToolResult()` |
| Hook 系统 | `hookRegistry.ts` | `registerHook()`, `triggerHook()` |
| 消息队列 | `messageQueueManager.ts` | `enqueue()`, `dequeue()` |
| 错误分类 | `toolExecution.ts` | `classifyToolError()` |
| Speculation | `speculation.ts` | `startSpeculation()` |

### 6.2 设计模式应用

从自动化模式识别（910 个实例，323 个高置信度）中提取：

| 模式 | 实例数 | 置信度 | 典型应用 |
|------|--------|--------|---------|
| Strategy | 274 | 0.85-0.95 | 权限模式、传输协议、错误处理 |
| Factory | 43 | 0.80-0.95 | StreamingToolExecutor、QueryEngine |
| Adapter | 3 | 0.60-0.70 | BridgeFatalError、StreamWrapper |
| Hook | 102 | - | PreToolUse、PostSampling、onBeforeQuery |

---

## 7. 实现检查清单

### 阶段 1: 核心 Loop（必须）

- [ ] React 组件实现 Agent Loop
- [ ] 消息状态管理（useState）
- [ ] 生命周期钩子（useEffect）
- [ ] 基础工具注册和执行
- [ ] 简单的权限检查（Manual Mode）

### 阶段 2: 上下文管理（必须）

- [ ] 上下文大小监控
- [ ] 工具输出分层存储
- [ ] 大文件持久化到磁盘
- [ ] 内容替换状态管理
- [ ] 基础的 Compact 机制

### 阶段 3: 可扩展性（推荐）

- [ ] Hook 注册表
- [ ] 5 层 Hook 注入点
- [ ] 同步/异步 Hook 支持
- [ ] Plugin 加载机制
- [ ] Skill 声明式扩展

### 阶段 4: 高级特性（可选）

- [ ] 多级权限模式（Plan/Auto）
- [ ] YOLO 分类器
- [ ] Speculation 预执行
- [ ] Overlay FS 隔离
- [ ] 多 Agent 编排

### 阶段 5: 优化（可选）

- [ ] 工具调用分组
- [ ] 并发控制
- [ ] 消息队列管理
- [ ] 版本化缓存
- [ ] 性能监控

---

## 8. 总结

### 核心洞察

Claude Code 的设计哲学可以总结为：

1. **上下文是瓶颈**: 再强的模型也会被糟糕的上下文管理拖垮
2. **声明式优于命令式**: React 组件比 while 循环更适合 Agent Loop
3. **安全嵌入流程**: 权限检查是执行流水线的一部分，不是独立模块
4. **简单即可靠**: 文件系统比数据库更适合 Agent 状态持久化
5. **级联取消**: AbortController 树状传播是优雅的取消机制
6. **类型即文档**: 错误类型继承树比日志更有表达力
7. **渐进式信任**: 从手动到全自动，提供安全梯度

### 可复用价值

这些设计原则不仅适用于 Claude Code，也适用于：

- **Agent CLI 工具**: 任何需要 LLM + 工具执行的命令行工具
- **Agent 框架**: 如 LangChain、AutoGPT 的底层运行时
- **IDE 插件**: 如 Cursor、Copilot 的 Agent 模式
- **自动化系统**: 任何需要 AI 驱动的自动化流程

### 下一步

- 阅读 [01-OVERVIEW.md](01-OVERVIEW.md) 了解整体架构
- 阅读 [02-AGENT-LOOP.md](02-AGENT-LOOP.md) 了解核心循环
- 阅读 [03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md) 了解工具系统
- 阅读 [04-CONTEXT-ENGINE.md](04-CONTEXT-ENGINE.md) 了解上下文管理

---

## 附录 A: 术语表

| 术语 | 定义 |
|------|------|
| Harness | Agent 运行时的编排机制，包括 Loop、Tool、Hook、Permission 等 |
| REPL | Read-Eval-Print Loop，Agent 的主循环 |
| Turn | 一次完整的交互周期：用户输入 → LLM 响应 → 工具执行 → 结果返回 |
| Tool | LLM 可调用的原子能力，有 JSON Schema 定义 |
| Hook | 在关键生命周期点注入的扩展机制 |
| Strategy | 可替换的算法或策略，如权限模式、传输协议 |
| Compact | 对话历史压缩机制 |
| Speculation | 预执行优化，在 Overlay FS 中提前执行工具 |
| YOLO | Auto Mode 的 LLM 分类器，自动决策是否允许操作 |
| Overlay FS | 临时文件系统，用于隔离预执行的副作用 |

---

## 附录 B: 延伸阅读

### 设计哲学

- **Unix 哲学**: "Do one thing and do it well" — 工具的原子性
- **React 哲学**: "UI as a function of state" — 声明式状态管理
- **Erlang 哲学**: "Let it crash" — 错误隔离和恢复

### 相关论文

- **ReAct**: Reasoning and Acting in Language Models (Yao et al., 2022)
- **Toolformer**: Language Models Can Teach Themselves to Use Tools (Schick et al., 2023)
- **Gorilla**: Large Language Model Connected with Massive APIs (Patil et al., 2023)

### 开源项目

- **LangChain**: Agent 框架，提供工具调用和记忆管理
- **AutoGPT**: 自主 Agent，展示了 Loop 和工具编排
- **Ink**: React 终端 UI 框架，Claude Code 的 UI 基础

---

**文档版本**: v1.0  
**最后更新**: 2026-04-01  
**维护者**: Reverse Engineering Lab  
**基于**: Claude Code v2.1.88 源码逆向分析

