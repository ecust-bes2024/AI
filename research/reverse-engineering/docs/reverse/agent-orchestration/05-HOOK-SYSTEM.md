# Hook 系统：5 层注入点设计

## 1. 核心概念

### 1.1 什么是 Hook 系统

Hook 系统是 Claude Code 最精妙的可扩展性设计，提供了 **5 层注入点**，允许在 Agent 执行的不同阶段插入自定义逻辑。这不是简单的回调机制，而是一个完整的 **可编程中间件架构**。

**设计动机**：
- **可扩展性**：无需修改核心代码即可扩展功能
- **解耦**：Plugin/Skill 通过 Hook 与核心系统交互
- **灵活性**：支持同步/异步、命令/函数/回调三种实现方式
- **安全性**：Hook 有信任检查和去重机制

### 1.2 Hook vs Plugin vs Skill

| 机制 | 定位 | 实现方式 | 典型用途 |
|------|------|----------|----------|
| **Hook** | 注入点 | Command/Function/Callback | 拦截和修改执行流程 |
| **Plugin** | 扩展包 | npm/git/local 包 | 添加新命令、工具、Agent |
| **Skill** | 能力声明 | Markdown + Prompt | 声明式能力扩展 |

**关系**：Plugin 和 Skill 都通过 Hook 系统与核心交互。Hook 是底层机制，Plugin/Skill 是上层抽象。

### 1.3 5 层 Hook 架构

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Loop 级 Hook                                   │
│  - onBeforeQuery: Query 开始前                           │
│  - onTurnComplete: Turn 完成后                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Session 级 Hook                                │
│  - 运行时动态添加/移除                                    │
│  - 跨 Turn 持久化                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Sampling 级 Hook                               │
│  - PostSamplingHooks: 消息发送前最后修改                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Tool 级 Hook                                   │
│  - PreToolUse: 工具执行前                                │
│  - PostToolUse: 工具执行后                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Event 级 Hook (UI)                             │
│  - Progress: 进度更新                                    │
│  - Log: 日志输出                                         │
│  - StatusLine: 状态栏更新                                │
│  - FileSuggestion: 文件建议                              │
│  - Notification: 通知                                    │
│  - Elicitation: 用户输入请求                             │
└─────────────────────────────────────────────────────────┘
```

**每一层都有不同粒度的控制权**：
- Layer 1 (Event) 控制 UI 交互
- Layer 2 (Tool) 控制工具执行
- Layer 3 (Sampling) 控制消息内容
- Layer 4 (Session) 控制会话状态
- Layer 5 (Loop) 控制整体流程

---

## 2. 架构设计

### 2.1 Hook 类型体系

Claude Code 支持三种 Hook 实现方式：

#### 2.1.1 Command Hook

**定义**：通过 shell 命令实现的 Hook。

```typescript
interface CommandHook {
  type: 'command'
  command: string           // shell 命令
  args?: string[]          // 命令参数
  cwd?: string             // 工作目录
  env?: Record<string, string>  // 环境变量
}
```

**执行流程**：
```
Hook 触发 → 构造命令 → 执行 shell → 捕获 stdout/stderr → 解析输出
```

**典型用途**：
- 调用外部工具（linter、formatter）
- 执行脚本（Python、Ruby、Node.js）
- 集成现有工具链

**示例**：
```json
{
  "preToolUse": {
    "bash": {
      "command": "shellcheck",
      "args": ["--format=json", "${toolInput}"]
    }
  }
}
```

#### 2.1.2 Function Hook

**定义**：通过 JavaScript 函数实现的 Hook。

```typescript
interface FunctionHook {
  type: 'function'
  function: string         // 函数代码（字符串形式）
  async?: boolean          // 是否异步
}
```

**执行流程**：
```
Hook 触发 → eval 函数代码 → 调用函数 → 返回结果
```

**典型用途**：
- 轻量级逻辑（不需要外部依赖）
- 数据转换和过滤
- 快速原型验证

**示例**：
```json
{
  "postToolUse": {
    "read": {
      "function": "(result) => { return result.content.toUpperCase(); }"
    }
  }
}
```

#### 2.1.3 Callback Hook

**定义**：通过注册的回调函数实现的 Hook（仅限内部使用）。

```typescript
interface CallbackHook {
  type: 'callback'
  callback: (context: HookContext) => Promise<HookResult>
}
```

**执行流程**：
```
Hook 触发 → 查找注册的回调 → 调用回调 → 返回结果
```

**典型用途**：
- 核心系统内部 Hook
- Plugin 注册的 Hook
- 需要访问内部 API 的 Hook

---

### 2.2 Hook 注册与匹配

#### 2.2.1 注册机制

Hook 通过 **模式匹配** 注册到特定事件：

```typescript
interface HookRegistration {
  event: HookEvent           // 事件类型
  pattern?: string | RegExp  // 匹配模式（可选）
  hook: Hook                 // Hook 实现
  priority?: number          // 优先级（默认 0）
  once?: boolean             // 是否只执行一次
}
```

**事件类型**：
```typescript
type HookEvent = 
  | 'preToolUse'           // 工具执行前
  | 'postToolUse'          // 工具执行后
  | 'postSampling'         // 消息发送前
  | 'onBeforeQuery'        // Query 开始前
  | 'onTurnComplete'       // Turn 完成后
  | 'notification'         // 通知
  | 'elicitation'          // 用户输入请求
  | 'statusLine'           // 状态栏更新
  | 'fileSuggestion'       // 文件建议
  | 'worktreeCreate'       // Worktree 创建
  | 'worktreeRemove'       // Worktree 删除
```

#### 2.2.2 模式匹配

Hook 可以通过模式匹配特定工具或事件：

```typescript
// 匹配所有 Bash 工具调用
{ event: 'preToolUse', pattern: 'bash' }

// 匹配所有 Read 工具调用
{ event: 'preToolUse', pattern: 'read' }

// 匹配所有工具调用（无 pattern）
{ event: 'preToolUse' }

// 正则匹配
{ event: 'preToolUse', pattern: /^(bash|read)$/ }
```

**匹配优先级**：
1. 精确匹配（`pattern === toolName`）
2. 正则匹配（`pattern.test(toolName)`）
3. 无模式匹配（`pattern === undefined`）

---

### 2.3 异步 Hook 机制

#### 2.3.1 AsyncHookRegistry

Claude Code 使用 `AsyncHookRegistry` 管理异步 Hook：

```typescript
class AsyncHookRegistry {
  private pendingHooks: Map<string, AsyncHook>
  
  // 注册异步 Hook
  register(hookId: string, hook: AsyncHook): void
  
  // 轮询异步 Hook 状态
  poll(): Promise<AsyncHookResult[]>
  
  // 取消异步 Hook
  cancel(hookId: string): void
  
  // 清理完成的 Hook
  cleanup(): void
}
```

**执行流程**：
```
Hook 触发 → 注册到 AsyncHookRegistry → 后台进程轮询
           ↓
       Hook 完成 → 返回结果 → 从 Registry 移除
```

**典型用途**：
- 长时间运行的操作（编译、测试）
- 需要用户交互的操作（审批、确认）
- 外部服务调用（API、数据库）

#### 2.3.2 同步 vs 异步

| 特性 | 同步 Hook | 异步 Hook |
|------|----------|----------|
| **执行** | 阻塞主流程 | 后台执行 |
| **返回** | 立即返回 | 轮询获取 |
| **超时** | 有超时限制 | 无超时限制 |
| **取消** | 通过 AbortController | 通过 Registry |
| **用途** | 快速操作 | 长时间操作 |

---

## 3. 接口契约

### 3.1 PreToolUse Hook

**触发时机**：工具执行前，权限检查后。

**输入**：
```typescript
interface PreToolUseContext {
  toolName: string          // 工具名称
  toolInput: any            // 工具输入
  toolUseId: string         // 工具调用 ID
  conversationId: string    // 会话 ID
  userId: string            // 用户 ID
}
```

**输出**：
```typescript
interface PreToolUseResult {
  allow: boolean            // 是否允许执行
  modifiedInput?: any       // 修改后的输入（可选）
  message?: string          // 消息（拒绝时显示）
}
```

**典型用途**：
- 输入验证和清理
- 参数转换
- 条件拦截
- 审计日志

**示例**：
```typescript
// 拦截危险的 Bash 命令
{
  event: 'preToolUse',
  pattern: 'bash',
  hook: {
    type: 'function',
    function: `(ctx) => {
      if (ctx.toolInput.command.includes('rm -rf /')) {
        return { allow: false, message: 'Dangerous command blocked' };
      }
      return { allow: true };
    }`
  }
}
```

---

### 3.2 PostToolUse Hook

**触发时机**：工具执行后，结果返回前。

**输入**：
```typescript
interface PostToolUseContext {
  toolName: string          // 工具名称
  toolInput: any            // 工具输入
  toolOutput: any           // 工具输出
  toolUseId: string         // 工具调用 ID
  error?: Error             // 错误（如果有）
  duration: number          // 执行时长（ms）
}
```

**输出**：
```typescript
interface PostToolUseResult {
  modifiedOutput?: any      // 修改后的输出（可选）
  suppressOutput?: boolean  // 是否抑制输出
  additionalMessages?: Message[]  // 额外消息
}
```

**典型用途**：
- 结果转换和格式化
- 错误处理和重试
- 结果缓存
- 性能监控

**示例**：
```typescript
// 缓存 Read 工具结果
{
  event: 'postToolUse',
  pattern: 'read',
  hook: {
    type: 'function',
    function: `(ctx) => {
      cache.set(ctx.toolInput.path, ctx.toolOutput);
      return { modifiedOutput: ctx.toolOutput };
    }`
  }
}
```

---

### 3.3 PostSampling Hook

**触发时机**：消息发送到 API 前的最后一刻。

**输入**：
```typescript
interface PostSamplingContext {
  messages: Message[]       // 消息列表
  systemPrompt: string      // 系统提示
  tools: Tool[]             // 工具列表
  model: string             // 模型名称
}
```

**输出**：
```typescript
interface PostSamplingResult {
  modifiedMessages?: Message[]     // 修改后的消息
  modifiedSystemPrompt?: string    // 修改后的系统提示
  additionalContext?: string       // 额外上下文
}
```

**典型用途**：
- 注入额外上下文
- 消息过滤和清理
- 动态系统提示
- A/B 测试

**示例**：
```typescript
// 注入当前时间
{
  event: 'postSampling',
  hook: {
    type: 'function',
    function: `(ctx) => {
      const timeContext = \`Current time: \${new Date().toISOString()}\`;
      return { additionalContext: timeContext };
    }`
  }
}
```

---

### 3.4 onBeforeQuery Hook

**触发时机**：Query 开始前，消息入队后。

**输入**：
```typescript
interface BeforeQueryContext {
  userMessage: string       // 用户消息
  conversationId: string    // 会话 ID
  turnNumber: number        // Turn 编号
}
```

**输出**：
```typescript
interface BeforeQueryResult {
  cancel?: boolean          // 是否取消 Query
  modifiedMessage?: string  // 修改后的消息
  prependMessages?: Message[]  // 前置消息
}
```

**典型用途**：
- 消息预处理
- 上下文注入
- 条件拦截
- 路由决策

---

### 3.5 onTurnComplete Hook

**触发时机**：Turn 完成后，结果返回前。

**输入**：
```typescript
interface TurnCompleteContext {
  conversationId: string    // 会话 ID
  turnNumber: number        // Turn 编号
  messages: Message[]       // 本轮消息
  toolCalls: ToolCall[]     // 工具调用
  duration: number          // 执行时长（ms）
  tokenUsage: TokenUsage    // Token 使用量
}
```

**输出**：
```typescript
interface TurnCompleteResult {
  appendMessages?: Message[]  // 追加消息
  metadata?: Record<string, any>  // 元数据
}
```

**典型用途**：
- 会话总结
- 性能分析
- 成本追踪
- 自动记忆提取

---

## 4. 实现要点

### 4.1 Hook 去重机制

**问题**：同一个 Hook 可能被多次触发（例如，Plugin 和 Skill 都注册了相同的 Hook）。

**解决方案**：`hookDedupKey()` 函数生成去重键。

```typescript
function hookDedupKey(hook: Hook): string {
  if (hook.type === 'command') {
    return `cmd:${hook.command}:${JSON.stringify(hook.args)}`;
  } else if (hook.type === 'function') {
    return `fn:${hash(hook.function)}`;
  } else if (hook.type === 'callback') {
    return `cb:${hook.callback.name}`;
  }
}
```

**去重策略**：
- 相同的 Command Hook（命令 + 参数相同）只执行一次
- 相同的 Function Hook（函数代码相同）只执行一次
- Callback Hook 通过函数名去重

---

### 4.2 Hook 信任检查

**问题**：Plugin Hook 可能不受信任，需要用户确认。

**解决方案**：`shouldSkipHookDueToTrust()` 函数检查信任状态。

```typescript
function shouldSkipHookDueToTrust(
  hook: Hook,
  source: HookSource,
  trustLevel: TrustLevel
): boolean {
  // Builtin Hook 总是信任
  if (source === 'builtin') return false;
  
  // Plugin Hook 需要检查信任级别
  if (source === 'plugin') {
    return trustLevel < TrustLevel.Trusted;
  }
  
  // Session Hook 需要用户确认
  if (source === 'session') {
    return trustLevel < TrustLevel.Confirmed;
  }
  
  return false;
}
```

**信任级别**：
```typescript
enum TrustLevel {
  Untrusted = 0,    // 不信任
  Confirmed = 1,    // 用户确认
  Trusted = 2,      // 完全信任
}
```

---

### 4.3 pendingHookMessages 延迟注入

**设计思想**：某些 Hook 需要在特定时机注入消息，而不是立即注入。

**实现**：
```typescript
interface PendingHookMessage {
  message: Message          // 待注入消息
  injectAt: 'beforeQuery' | 'afterQuery' | 'beforeSampling'
  priority: number          // 优先级
}

class HookMessageQueue {
  private pending: PendingHookMessage[] = [];
  
  // 添加待注入消息
  add(msg: PendingHookMessage): void {
    this.pending.push(msg);
    this.pending.sort((a, b) => b.priority - a.priority);
  }
  
  // 获取并清空特定时机的消息
  drain(injectAt: string): Message[] {
    const messages = this.pending
      .filter(m => m.injectAt === injectAt)
      .map(m => m.message);
    this.pending = this.pending.filter(m => m.injectAt !== injectAt);
    return messages;
  }
}
```

**典型用途**：
- Elicitation Hook 请求用户输入
- MCP Server 请求额外上下文
- 动态注入系统提示

---

### 4.4 Hook 执行顺序

**问题**：多个 Hook 注册到同一事件时，执行顺序如何确定？

**解决方案**：按优先级排序，优先级相同时按注册顺序。

```typescript
function sortHooks(hooks: HookRegistration[]): HookRegistration[] {
  return hooks.sort((a, b) => {
    // 优先级高的先执行
    if (a.priority !== b.priority) {
      return (b.priority || 0) - (a.priority || 0);
    }
    // 优先级相同时，按注册顺序
    return 0;
  });
}
```

**执行模式**：
- **串行执行**：PreToolUse、PostToolUse（需要修改输入/输出）
- **并行执行**：Event Hook（UI 更新）
- **管道模式**：PostSampling（消息逐层转换）

---

### 4.5 Hook 错误处理

**原则**：Hook 失败不应导致整个 Agent 崩溃。

**策略**：
```typescript
async function executeHook(
  hook: Hook,
  context: HookContext
): Promise<HookResult> {
  try {
    const result = await hook.execute(context);
    return result;
  } catch (error) {
    // 记录错误
    logger.error('Hook execution failed', { hook, error });
    
    // 返回默认结果（允许继续执行）
    return { allow: true };
  }
}
```

**错误分类**：
- **致命错误**：Hook 代码语法错误 → 禁用 Hook
- **运行时错误**：Hook 执行失败 → 记录日志，继续执行
- **超时错误**：Hook 超时 → 取消 Hook，继续执行

---

## 5. 设计决策

### 5.1 为什么需要 5 层 Hook？

**单层 Hook 的问题**：
- 粒度不够：无法区分工具级和会话级
- 时机不对：无法在消息发送前修改
- 性能差：所有 Hook 都在关键路径上

**5 层设计的优势**：
- **粒度分离**：每层控制不同的关注点
- **性能优化**：Event Hook 异步执行，不阻塞主流程
- **灵活性**：可以在任意阶段注入逻辑

### 5.2 为什么支持三种 Hook 类型？

**Command Hook**：
- 优势：可以调用任何外部工具，语言无关
- 劣势：启动开销大，需要序列化输入输出

**Function Hook**：
- 优势：轻量级，无启动开销，可以访问 JavaScript 生态
- 劣势：安全风险（eval），无法调用外部工具

**Callback Hook**：
- 优势：性能最好，可以访问内部 API
- 劣势：仅限内部使用，Plugin 无法注册

**权衡**：提供三种类型，让用户根据场景选择。

### 5.3 为什么需要异步 Hook？

**同步 Hook 的限制**：
- 阻塞主流程：长时间操作会导致 Agent 卡住
- 超时限制：无法执行超过 30 秒的操作
- 用户体验差：用户需要等待 Hook 完成

**异步 Hook 的优势**：
- 后台执行：不阻塞主流程
- 无超时限制：可以执行任意长时间的操作
- 可取消：用户可以随时取消

**典型场景**：
- 编译大型项目（可能需要几分钟）
- 运行测试套件（可能需要几十秒）
- 等待用户审批（可能需要几小时）

### 5.4 为什么需要 pendingHookMessages？

**直接注入的问题**：
- 时机不对：Hook 执行时可能还没到注入时机
- 顺序混乱：多个 Hook 注入消息时顺序不确定
- 重复注入：同一消息可能被多次注入

**延迟注入的优势**：
- 精确控制注入时机
- 按优先级排序
- 去重和合并

**典型场景**：
- Elicitation Hook 请求用户输入（需要在 Query 前注入）
- MCP Server 请求额外上下文（需要在 Sampling 前注入）
- 动态系统提示（需要在 Sampling 前注入）

---

## 6. 参考实现

### 6.1 源码位置

| 模块 | 文件 | 说明 |
|------|------|------|
| Hook 注册 | `hookRegistry.ts` | Hook 注册和匹配 |
| Hook 执行 | `hookExecutor.ts` | Hook 执行引擎 |
| 异步 Hook | `asyncHookRegistry.ts` | 异步 Hook 管理 |
| Hook 事件 | `hookEvents.ts` | Event Hook 定义 |
| Hook 去重 | `hookDedup.ts` | 去重逻辑 |
| Hook 信任 | `hookTrust.ts` | 信任检查 |
| 消息队列 | `hookMessageQueue.ts` | pendingHookMessages |

### 6.2 关键函数签名

```typescript
// Hook 注册
function registerHook(
  event: HookEvent,
  pattern: string | RegExp | undefined,
  hook: Hook,
  options?: HookOptions
): void

// Hook 执行
async function executeHooks(
  event: HookEvent,
  context: HookContext,
  signal?: AbortSignal
): Promise<HookResult[]>

// 异步 Hook 注册
function registerAsyncHook(
  hookId: string,
  hook: AsyncHook
): void

// 异步 Hook 轮询
async function pollAsyncHooks(): Promise<AsyncHookResult[]>

// Hook 去重
function hookDedupKey(hook: Hook): string

// Hook 信任检查
function shouldSkipHookDueToTrust(
  hook: Hook,
  source: HookSource,
  trustLevel: TrustLevel
): boolean

// 消息队列
function addPendingHookMessage(
  message: Message,
  injectAt: InjectTiming,
  priority: number
): void

function drainPendingHookMessages(
  injectAt: InjectTiming
): Message[]
```

---

## 7. 实现检查清单

### 7.1 必须实现

- [ ] Hook 注册机制（支持模式匹配）
- [ ] Hook 执行引擎（支持同步/异步）
- [ ] PreToolUse Hook（工具执行前）
- [ ] PostToolUse Hook（工具执行后）
- [ ] PostSampling Hook（消息发送前）
- [ ] Hook 去重机制
- [ ] Hook 信任检查
- [ ] Hook 错误处理（不崩溃）
- [ ] Hook 超时控制
- [ ] Hook 取消机制（AbortController）

### 7.2 推荐实现

- [ ] onBeforeQuery Hook（Query 开始前）
- [ ] onTurnComplete Hook（Turn 完成后）
- [ ] AsyncHookRegistry（异步 Hook 管理）
- [ ] pendingHookMessages（延迟注入）
- [ ] Hook 优先级排序
- [ ] Hook 执行日志和遥测
- [ ] Hook 性能监控
- [ ] Hook 调试工具

### 7.3 可选优化

- [ ] Hook 缓存（避免重复执行）
- [ ] Hook 并行执行（Event Hook）
- [ ] Hook 管道模式（PostSampling）
- [ ] Hook 热重载（开发模式）
- [ ] Hook 可视化调试器
- [ ] Hook 性能分析器

### 7.4 测试验证点

- [ ] Hook 能正确匹配工具名称
- [ ] Hook 能修改工具输入/输出
- [ ] Hook 能拦截工具执行
- [ ] Hook 失败不导致 Agent 崩溃
- [ ] 异步 Hook 能后台执行
- [ ] Hook 去重机制生效
- [ ] Hook 信任检查生效
- [ ] pendingHookMessages 正确注入
- [ ] Hook 优先级排序正确
- [ ] Hook 能被取消

---

## 8. 总结

Hook 系统是 Claude Code 可扩展性的核心，通过 **5 层注入点 + 3 种实现方式 + 异步机制**，提供了完整的中间件架构。

**核心设计原则**：
1. **分层控制**：每层控制不同粒度的关注点
2. **多种实现**：Command/Function/Callback 满足不同场景
3. **异步优先**：长时间操作不阻塞主流程
4. **安全第一**：信任检查 + 去重 + 错误处理
5. **延迟注入**：精确控制消息注入时机

**与其他系统的关系**：
- **Tool System**：Hook 拦截和修改工具执行
- **Permission System**：Hook 在权限检查后执行
- **Context Engine**：Hook 可以注入额外上下文
- **Plugin System**：Plugin 通过 Hook 扩展功能
- **Multi-Agent**：Hook 可以在 Agent 间传递消息

**下一步**：阅读 [06-PERMISSION.md](06-PERMISSION.md) 了解权限系统如何与 Hook 系统协作。
