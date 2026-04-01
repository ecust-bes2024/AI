# Agent 运行时核心概念与架构

## 文档定位

本文档是 Agent 编排知识库的**入口文档**，介绍 Agent 运行时（Harness）的核心概念、整体架构和设计动机。阅读本文后，你将理解：

- 什么是 Harness，为什么需要它
- Agent Loop 的完整生命周期
- 核心组件及其职责
- 消息流转的完整路径
- 关键设计决策的动机

**目标读者**：需要实现 Agent 编排系统的开发者、架构师。

**前置知识**：理解 LLM API 调用、工具调用（Tool Use）、消息格式。

---

## 1. 核心概念

### 1.1 什么是 Harness

**Harness（编排引擎）** 是 Agent 的运行时环境，负责：

1. **接收输入**：用户消息、斜杠命令、Hook 触发
2. **编排执行**：调用 LLM、执行工具、管理上下文
3. **控制流程**：权限检查、错误处理、并发控制
4. **输出结果**：流式渲染、状态更新、遥测上报

**类比**：
- 如果 LLM 是 CPU，Harness 就是操作系统
- 如果 Agent 是应用程序，Harness 就是运行时（Runtime）
- 如果工具是函数，Harness 就是调用栈管理器

### 1.2 为什么需要 Harness

**问题**：直接调用 LLM API 无法构建生产级 Agent，因为：

1. **上下文爆炸**：对话历史无限增长，超出 token 限制
2. **工具执行混乱**：并发、错误、权限、超时无人管理
3. **用户体验差**：无流式输出、无进度反馈、无取消机制
4. **不可扩展**：硬编码流程，无法插入自定义逻辑
5. **不可观测**：无法追踪性能瓶颈、错误根因

**Harness 的价值**：

```
原始 LLM API 调用：
  用户输入 → API 请求 → 等待响应 → 工具执行 → 再次请求 → ...
  ❌ 上下文管理：手动拼接消息
  ❌ 工具执行：串行、无错误处理
  ❌ 用户体验：阻塞等待、无进度
  ❌ 可扩展性：硬编码流程

Harness 编排：
  用户输入 → [上下文管理] → [权限检查] → API 请求 → [流式渲染]
           → [工具并发执行] → [结果压缩] → [Hook 注入] → 下一轮
  ✅ 上下文管理：自动压缩、智能裁剪
  ✅ 工具执行：并发、超时、重试、权限
  ✅ 用户体验：流式输出、进度条、可取消
  ✅ 可扩展性：Hook 系统、Plugin 机制
```

### 1.3 核心术语

| 术语 | 定义 | 类比 |
|------|------|------|
| **Turn** | 一次完整的"用户输入 → LLM 响应 → 工具执行"循环 | HTTP 请求-响应周期 |
| **REPL** | Read-Eval-Print Loop，Agent 的主循环 | Shell 的命令循环 |
| **Query** | 一次 LLM API 调用（可能包含多轮工具执行） | 数据库查询 |
| **Tool Use** | LLM 请求执行某个工具 | 函数调用 |
| **Tool Result** | 工具执行的返回结果 | 函数返回值 |
| **Message** | 对话历史中的一条消息（user/assistant/tool_result） | 聊天记录 |
| **Context** | 发送给 LLM 的完整上下文（system prompt + messages） | 程序的运行时环境 |
| **Hook** | 在特定生命周期注入自定义逻辑的机制 | 中间件、拦截器 |
| **Permission** | 工具执行前的权限检查机制 | 操作系统的权限系统 |
| **Compact** | 压缩对话历史以节省 token | 垃圾回收 |

---

## 2. 整体架构

### 2.1 架构全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                               │
│                    (Terminal UI / React)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ 用户输入
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         REPL 主循环                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ MessageQueueManager: 输入排队                             │  │
│  │ - 用户消息入队                                            │  │
│  │ - Hook 消息延迟注入                                       │  │
│  │ - 斜杠命令解析                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ QueryGuard: 并发控制                                      │  │
│  │ - 互斥锁：同一时刻只有一个 Query                          │  │
│  │ - 防止用户快速连续输入导致并发请求                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ onBeforeQuery Hook: 发送前拦截                            │  │
│  │ - PostSamplingHooks 修改 messages/systemPrompt            │  │
│  │ - 上下文预算检查                                          │  │
│  │ - Hook 系统注入额外消息                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QueryEngine: API 调用层                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ QueryContext: 组装请求                                    │  │
│  │ - fetchSystemPromptParts(): 组装 system prompt            │  │
│  │ - 合并 MCP 工具                                           │  │
│  │ - 计算工具描述                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Anthropic API 调用                                        │  │
│  │ - 流式响应处理                                            │  │
│  │ - 错误重试                                                │  │
│  │ - 取消控制                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ LLM 响应（可能包含 tool_use）
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   StreamingToolExecutor: 工具执行层              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PermissionContext: 权限检查                               │  │
│  │ - 4 级权限模式（YOLO/Autopilot/Supervised/Manual）        │  │
│  │ - YOLO Classifier 自动审查                                │  │
│  │ - 用户确认队列                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 工具并发执行                                              │  │
│  │ - 独立工具并行执行                                        │  │
│  │ - 依赖工具串行执行                                        │  │
│  │ - 超时控制、错误分类                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ToolResultStorage: 结果压缩                               │  │
│  │ - 大结果自动压缩                                          │  │
│  │ - 引用替换（"见上文"）                                    │  │
│  │ - 按需展开                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ Tool Results
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         REPL 主循环                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 判断是否需要继续                                          │  │
│  │ - 如果有 tool_use → 继续下一轮 Query                      │  │
│  │ - 如果是 end_turn → 进入 onTurnComplete                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ onTurnComplete Hook: Turn 完成后处理                      │  │
│  │ - 记忆提取（extractMemories）                             │  │
│  │ - Speculation 启动                                        │  │
│  │ - Compact 检查                                            │  │
│  │ - 遥测上报                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                      等待下一次用户输入
```

### 2.2 数据流：从输入到输出

**完整的 Turn 生命周期**：

```
1. 用户输入
   ├─ 自然语言消息
   ├─ 斜杠命令（/commit, /review-pr）
   └─ Hook 触发消息
        │
        ▼
2. MessageQueueManager 入队
   ├─ 解析命令类型
   ├─ 排队等待执行
   └─ 可编辑命令合并
        │
        ▼
3. QueryGuard 加锁
   ├─ 检查是否有正在执行的 Query
   ├─ 等待前一个 Query 完成
   └─ 预留执行权
        │
        ▼
4. onBeforeQuery Hook
   ├─ PostSamplingHooks 修改消息
   ├─ 上下文预算检查
   └─ Hook 系统注入消息
        │
        ▼
5. QueryContext 组装请求
   ├─ fetchSystemPromptParts()
   │   ├─ 基础 system prompt
   │   ├─ 工具描述
   │   ├─ MCP 工具合并
   │   └─ 用户自定义 prompt
   ├─ 计算 messages
   │   ├─ 对话历史
   │   ├─ 压缩后的 tool results
   │   └─ 新用户消息
   └─ 配置参数
       ├─ model
       ├─ max_tokens
       ├─ temperature
       └─ tools
        │
        ▼
6. QueryEngine 发起 API 调用
   ├─ 创建 AbortController
   ├─ 流式响应处理
   └─ QueryProfiler 计时
        │
        ▼
7. LLM 响应（流式）
   ├─ text delta → 实时渲染
   ├─ tool_use → 收集工具调用
   └─ end_turn → 结束标记
        │
        ▼
8. StreamingToolExecutor 执行工具
   ├─ 解析 tool_use
   ├─ PermissionContext 权限检查
   │   ├─ YOLO Classifier 自动审查
   │   ├─ 权限规则匹配
   │   └─ 用户确认（如需要）
   ├─ 并发执行工具
   │   ├─ 独立工具并行
   │   ├─ 依赖工具串行
   │   └─ 超时控制
   ├─ 收集 tool results
   └─ ToolResultStorage 压缩
        │
        ▼
9. 判断是否继续
   ├─ 有 tool_use → 回到步骤 5（继续 Query）
   └─ end_turn → 进入步骤 10
        │
        ▼
10. onTurnComplete Hook
    ├─ 记忆提取
    ├─ Speculation 启动
    ├─ Compact 检查
    └─ 遥测上报
        │
        ▼
11. QueryGuard 解锁
    └─ 释放执行权
        │
        ▼
12. 等待下一次输入
```

---

## 3. 核心组件详解

### 3.1 REPL：主循环的大脑

**职责**：
- 管理整个 Agent 的生命周期
- 协调各个子系统
- 维护对话状态

**关键设计**：

```typescript
// 伪代码接口
interface REPLProps {
  // 输入源
  commands: SlashCommand[]           // 斜杠命令注册表
  initialMessages: Message[]         // 初始对话历史
  pendingHookMessages: Promise<HookResultMessage[]>  // Hook 消息异步注入
  
  // 工具系统
  initialTools: Tool[]               // 初始工具集
  mcpClients: MCPClient[]            // MCP 客户端
  
  // 生命周期 Hook
  onBeforeQuery: (context) => void   // Query 前回调
  onTurnComplete: (context) => void  // Turn 完成回调
  
  // 配置
  systemPrompt: string               // 自定义系统提示
  thinkingConfig: ThinkingConfig     // Extended Thinking 配置
  
  // 状态管理
  initialContentReplacements: Map    // ToolResultStorage 初始状态
  initialFileHistorySnapshots: Map   // 文件历史快照
}

class REPL {
  // 状态
  private messages: Message[]
  private tools: Tool[]
  private contentReplacements: Map
  
  // 子系统
  private messageQueue: MessageQueueManager
  private queryGuard: QueryGuard
  private queryEngine: QueryEngine
  private toolExecutor: StreamingToolExecutor
  
  // 主循环
  async run() {
    while (true) {
      // 1. 等待输入
      const input = await this.messageQueue.dequeue()
      
      // 2. 加锁
      await this.queryGuard.reserve()
      
      // 3. 执行 Turn
      await this.executeTurn(input)
      
      // 4. 解锁
      this.queryGuard.release()
    }
  }
  
  async executeTurn(input: UserInput) {
    // 1. onBeforeQuery Hook
    await this.onBeforeQuery(this.buildContext())
    
    // 2. 组装请求
    const request = this.buildRequest()
    
    // 3. 发起 Query
    const response = await this.queryEngine.query(request)
    
    // 4. 执行工具
    const toolResults = await this.toolExecutor.execute(response.tool_uses)
    
    // 5. 判断是否继续
    if (toolResults.length > 0) {
      // 有工具执行 → 继续下一轮 Query
      this.messages.push(...toolResults)
      return this.executeTurn(null) // 递归
    }
    
    // 6. onTurnComplete Hook
    await this.onTurnComplete(this.buildContext())
  }
}
```

**设计动机**：

1. **为什么用 React 组件而不是 while 循环？**
   - React 的状态管理天然支持异步更新
   - 组件生命周期与 Agent 生命周期对齐
   - 易于集成 UI 渲染（Ink）

2. **为什么需要 MessageQueueManager？**
   - 用户可能快速连续输入
   - Hook 可能异步注入消息
   - 需要合并可编辑命令（如连续的文本输入）

3. **为什么需要 QueryGuard？**
   - 防止并发 Query 导致状态混乱
   - 防止 Speculation 和用户输入冲突
   - 确保消息顺序正确

### 3.2 QueryEngine：API 调用的执行层

**职责**：
- 封装 LLM API 调用
- 处理流式响应
- 管理取消和超时
- 追踪性能指标

**关键设计**：

```typescript
interface QueryEngineConfig {
  model: string                    // 模型名称
  maxTokens: number                // 最大输出 token
  temperature: number              // 温度参数
  apiKey: string                   // API 密钥
  baseURL?: string                 // API 端点
}

class QueryEngine {
  private config: QueryEngineConfig
  private profiler: QueryProfiler
  
  constructor(config: QueryEngineConfig) {
    this.config = config
    this.profiler = new QueryProfiler()
  }
  
  async query(request: QueryRequest): Promise<QueryResponse> {
    // 1. 开始性能追踪
    this.profiler.startQueryProfile()
    
    // 2. 创建取消控制器
    const abortController = new AbortController()
    
    // 3. 发起 API 调用
    this.profiler.queryCheckpoint('api_call_start')
    const stream = await this.callAPI(request, abortController.signal)
    
    // 4. 处理流式响应
    const response = await this.processStream(stream)
    
    // 5. 结束性能追踪
    this.profiler.endQueryProfile()
    this.profiler.logQueryProfileReport()
    
    return response
  }
  
  private async processStream(stream: ReadableStream): Promise<QueryResponse> {
    const response = {
      text: '',
      tool_uses: [],
      stop_reason: null
    }
    
    for await (const chunk of stream) {
      if (chunk.type === 'content_block_delta') {
        if (chunk.delta.type === 'text_delta') {
          response.text += chunk.delta.text
          // 实时渲染到 UI
          this.emit('text_delta', chunk.delta.text)
        }
      } else if (chunk.type === 'content_block_start') {
        if (chunk.content_block.type === 'tool_use') {
          response.tool_uses.push(chunk.content_block)
        }
      } else if (chunk.type === 'message_stop') {
        response.stop_reason = chunk.stop_reason
      }
    }
    
    return response
  }
}
```

**设计动机**：

1. **为什么需要 QueryProfiler？**
   - 精确定位性能瓶颈（API 延迟、工具执行、上下文组装）
   - 生成慢操作警告
   - 支持遥测上报

2. **为什么需要 AbortController？**
   - 用户可能中途取消
   - 超时需要强制终止
   - 级联取消（父 Query 取消 → 子工具取消）

### 3.3 StreamingToolExecutor：工具执行的编排器

**职责**：
- 解析 LLM 的 tool_use 请求
- 权限检查
- 并发执行工具
- 收集和压缩结果

**关键设计**：

```typescript
class StreamingToolExecutor {
  private tools: Map<string, Tool>
  private permissionContext: PermissionContext
  private resultStorage: ToolResultStorage
  
  async execute(toolUses: ToolUse[]): Promise<ToolResult[]> {
    const results: ToolResult[] = []
    
    // 1. 权限检查
    for (const toolUse of toolUses) {
      const permission = await this.permissionContext.check(toolUse)
      if (!permission.allowed) {
        results.push({
          tool_use_id: toolUse.id,
          is_error: true,
          content: 'Permission denied'
        })
        continue
      }
    }
    
    // 2. 分析依赖关系
    const { independent, dependent } = this.analyzeDependencies(toolUses)
    
    // 3. 并发执行独立工具
    const independentResults = await Promise.all(
      independent.map(toolUse => this.executeOne(toolUse))
    )
    results.push(...independentResults)
    
    // 4. 串行执行依赖工具
    for (const toolUse of dependent) {
      const result = await this.executeOne(toolUse)
      results.push(result)
    }
    
    // 5. 压缩结果
    const compressedResults = this.resultStorage.compress(results)
    
    return compressedResults
  }
  
  private async executeOne(toolUse: ToolUse): Promise<ToolResult> {
    const tool = this.tools.get(toolUse.name)
    
    try {
      // 超时控制
      const result = await Promise.race([
        tool.execute(toolUse.input),
        this.timeout(tool.timeout || 30000)
      ])
      
      return {
        tool_use_id: toolUse.id,
        content: result
      }
    } catch (error) {
      return {
        tool_use_id: toolUse.id,
        is_error: true,
        content: this.classifyError(error)
      }
    }
  }
}
```

**设计动机**：

1. **为什么需要依赖分析？**
   - 独立工具并行执行可以节省时间
   - 依赖工具必须串行（如先 Read 再 Edit）

2. **为什么需要 ToolResultStorage？**
   - 工具结果可能很大（如读取大文件）
   - 压缩可以节省上下文 token
   - 引用替换让 LLM 知道"结果在上文"

### 3.4 PermissionContext：安全管道

**职责**：
- 根据权限模式决定是否执行工具
- YOLO Classifier 自动审查
- 管理用户确认队列
- 持久化权限规则

**关键设计**：

```typescript
enum PermissionMode {
  YOLO = 'yolo',           // 全自动，Classifier 审查
  Autopilot = 'autopilot', // 自动执行，危险操作需确认
  Supervised = 'supervised', // 执行后可撤销
  Manual = 'manual'        // 每次都需确认
}

interface PermissionRule {
  tool: string             // 工具名称
  pattern?: string         // 参数模式（正则）
  action: 'allow' | 'deny' // 动作
  scope?: string           // 作用域（如目录）
}

class PermissionContext {
  private mode: PermissionMode
  private rules: PermissionRule[]
  private classifier: YOLOClassifier
  private confirmQueue: ToolUseConfirmQueue
  
  async check(toolUse: ToolUse): Promise<PermissionResult> {
    // 1. 检查规则
    const ruleMatch = this.matchRule(toolUse)
    if (ruleMatch) {
      return { allowed: ruleMatch.action === 'allow' }
    }
    
    // 2. 根据模式决策
    switch (this.mode) {
      case PermissionMode.YOLO:
        // Classifier 自动审查
        const safe = await this.classifier.isSafe(toolUse)
        return { allowed: safe }
      
      case PermissionMode.Autopilot:
        // 危险操作需确认
        if (this.isDangerous(toolUse)) {
          return await this.requestConfirm(toolUse)
        }
        return { allowed: true }
      
      case PermissionMode.Supervised:
        // 先执行，后撤销
        return { allowed: true, canRevert: true }
      
      case PermissionMode.Manual:
        // 每次都确认
        return await this.requestConfirm(toolUse)
    }
  }
  
  private async requestConfirm(toolUse: ToolUse): Promise<PermissionResult> {
    // 加入确认队列，等待用户响应
    return new Promise((resolve) => {
      this.confirmQueue.enqueue({
        toolUse,
        onConfirm: () => resolve({ allowed: true }),
        onDeny: () => resolve({ allowed: false })
      })
    })
  }
}
```

**设计动机**：

1. **为什么需要 4 级权限模式？**
   - YOLO：完全信任 AI，适合熟练用户
   - Autopilot：平衡自动化和安全
   - Supervised：允许撤销，适合学习阶段
   - Manual：完全控制，适合敏感操作

2. **为什么需要 YOLO Classifier？**
   - 自动识别危险操作（删除、覆盖、网络请求）
   - 减少用户打断
   - 可训练和改进

### 3.5 MessageQueueManager：输入的排队机制

**职责**：
- 管理用户输入队列
- 合并可编辑命令
- 延迟注入 Hook 消息

**关键设计**：

```typescript
interface QueuedCommand {
  type: 'user_message' | 'slash_command' | 'hook_message'
  content: string
  editable: boolean        // 是否可编辑
  visible: boolean         // 是否在 UI 显示
  timestamp: number
}

class MessageQueueManager {
  private queue: QueuedCommand[] = []
  
  enqueue(command: QueuedCommand) {
    // 如果是可编辑命令，尝试合并
    if (command.editable) {
      const last = this.queue[this.queue.length - 1]
      if (last && last.editable && last.type === command.type) {
        // 合并到上一条
        last.content += command.content
        return
      }
    }
    
    this.queue.push(command)
  }
  
  async dequeue(): Promise<QueuedCommand | null> {
    if (this.queue.length === 0) {
      // 等待新输入
      return await this.waitForInput()
    }
    
    return this.queue.shift()
  }
  
  // 弹出所有可编辑命令（用户按 Enter 前）
  popAllEditable(currentInput: string, cursorOffset: number): string {
    const editable = this.queue.filter(cmd => cmd.editable)
    this.queue = this.queue.filter(cmd => !cmd.editable)
    
    // 合并到当前输入
    return editable.map(cmd => cmd.content).join('') + currentInput
  }
}
```

**设计动机**：

1. **为什么需要可编辑命令合并？**
   - 用户可能连续输入多个字符
   - 避免每个字符都触发一次 Query
   - 提升用户体验

2. **为什么需要延迟注入 Hook 消息？**
   - Hook 执行可能耗时
   - 不阻塞 REPL 初始化
   - 异步注入保持响应性

### 3.6 QueryGuard：并发控制的互斥锁

**职责**：
- 确保同一时刻只有一个 Query 执行
- 管理等待队列
- 提供取消信号

**关键设计**：

```typescript
class QueryGuard {
  private reserved: boolean = false
  private waiters: Array<() => void> = []
  private abortController: AbortController | null = null
  
  async reserve(): Promise<AbortSignal> {
    // 如果已被预留，等待释放
    while (this.reserved) {
      await new Promise(resolve => this.waiters.push(resolve))
    }
    
    // 预留
    this.reserved = true
    this.abortController = new AbortController()
    
    return this.abortController.signal
  }
  
  release() {
    this.reserved = false
    this.abortController = null
    
    // 通知下一个等待者
    const next = this.waiters.shift()
    if (next) next()
  }
  
  idle(): boolean {
    return !this.reserved
  }
  
  abort() {
    if (this.abortController) {
      this.abortController.abort()
    }
  }
}
```

**设计动机**：

1. **为什么需要互斥锁？**
   - 防止用户快速连续输入导致并发 Query
   - 防止 Speculation 和用户输入同时发起请求
   - 确保消息顺序正确

2. **为什么返回 AbortSignal？**
   - 支持级联取消
   - 用户取消 → Query 取消 → 工具取消

---

## 4. 生命周期 Hook 系统

### 4.1 Hook 注入点

Harness 提供两个关键的生命周期 Hook：

```
Turn 生命周期：
  用户输入
    │
    ▼
  [onBeforeQuery] ← Hook 注入点 1
    │
    ▼
  API 调用
    │
    ▼
  工具执行
    │
    ▼
  [onTurnComplete] ← Hook 注入点 2
    │
    ▼
  等待下一次输入
```

### 4.2 onBeforeQuery Hook

**触发时机**：每次 API 调用前

**用途**：
- 修改 messages（添加/删除/修改消息）
- 修改 systemPrompt（动态调整系统提示）
- 注入上下文（userContext/systemContext）
- 上下文预算检查

**接口**：

```typescript
interface BeforeQueryContext {
  messages: Message[]
  systemPrompt: string
  userContext: Record<string, string>
  systemContext: Record<string, string>
  tools: Tool[]
}

type OnBeforeQuery = (context: BeforeQueryContext) => Promise<void>
```

**典型用例**：

```typescript
// 1. PostSamplingHooks：修改消息
onBeforeQuery: async (context) => {
  // 执行所有注册的 PostSamplingHooks
  await executePostSamplingHooks(context)
}

// 2. 上下文预算检查
onBeforeQuery: async (context) => {
  const tokenCount = estimateTokens(context.messages)
  if (tokenCount > MAX_CONTEXT_TOKENS) {
    // 触发 Compact
    await compactMessages(context.messages)
  }
}

// 3. 注入动态上下文
onBeforeQuery: async (context) => {
  context.systemContext['current_time'] = new Date().toISOString()
  context.systemContext['git_branch'] = await getCurrentBranch()
}
```

### 4.3 onTurnComplete Hook

**触发时机**：Turn 完成后（LLM 返回 end_turn）

**用途**：
- 记忆提取
- Speculation 启动
- Compact 检查
- 遥测上报

**接口**：

```typescript
interface TurnCompleteContext {
  messages: Message[]
  lastAssistantMessage: AssistantMessage
  toolResults: ToolResult[]
  turnDuration: number
}

type OnTurnComplete = (context: TurnCompleteContext) => Promise<void>
```

**典型用例**：

```typescript
// 1. 记忆提取
onTurnComplete: async (context) => {
  const memories = await extractMemories(context.messages)
  await saveMemories(memories)
}

// 2. Speculation 启动
onTurnComplete: async (context) => {
  if (shouldSpeculate(context)) {
    await startSpeculation(context.messages)
  }
}

// 3. Compact 检查
onTurnComplete: async (context) => {
  if (shouldCompact(context.messages)) {
    await scheduleCompact()
  }
}
```

---

## 5. 设计决策与权衡

### 5.1 为什么用 React 而不是纯函数式循环？

**决策**：使用 React 组件 + Ink 渲染

**理由**：
1. **状态管理**：React 的 useState/useEffect 天然支持异步状态更新
2. **UI 集成**：Ink 提供终端 UI 组件，易于构建交互界面
3. **生命周期对齐**：组件生命周期与 Agent 生命周期对齐
4. **可测试性**：组件易于单元测试

**权衡**：
- ✅ 开发效率高
- ✅ UI 渲染流畅
- ❌ 引入 React 依赖
- ❌ 学习曲线（需要理解 React）

### 5.2 为什么需要 QueryGuard 而不是简单的 flag？

**决策**：使用互斥锁 + 等待队列

**理由**：
1. **并发安全**：防止竞态条件
2. **公平调度**：先到先服务
3. **取消支持**：提供 AbortSignal

**权衡**：
- ✅ 并发安全
- ✅ 支持取消
- ❌ 增加复杂度

### 5.3 为什么工具执行需要权限系统？

**决策**：4 级权限模式 + YOLO Classifier

**理由**：
1. **安全性**：防止 AI 执行危险操作
2. **灵活性**：不同场景不同模式
3. **用户体验**：减少不必要的打断

**权衡**：
- ✅ 安全可控
- ✅ 用户体验好
- ❌ 实现复杂
- ❌ Classifier 需要训练

### 5.4 为什么需要 ToolResultStorage？

**决策**：自动压缩 + 引用替换

**理由**：
1. **节省 token**：大结果压缩可节省 50-90% token
2. **保持可读性**：LLM 仍能理解"见上文"
3. **按需展开**：需要时可以展开完整内容

**权衡**：
- ✅ 大幅节省 token
- ✅ 延长对话长度
- ❌ 增加状态管理复杂度
- ❌ 可能影响 LLM 理解

### 5.5 为什么需要 PostSamplingHooks？

**决策**：在发送前最后修改消息

**理由**：
1. **动态注入**：根据运行时状态注入上下文
2. **解耦**：Hook 系统与 REPL 解耦
3. **可扩展**：Plugin 可以注册自己的 Hook

**权衡**：
- ✅ 高度可扩展
- ✅ 解耦良好
- ❌ 调试困难（消息被多次修改）

---

## 6. 消息生命周期详解

### 6.1 消息的诞生

```
用户输入 "帮我重构这个函数"
  │
  ▼
MessageQueueManager.enqueue({
  type: 'user_message',
  content: '帮我重构这个函数',
  editable: false,
  visible: true
})
  │
  ▼
存储在队列中，等待 dequeue
```

### 6.2 消息的处理

```
MessageQueueManager.dequeue()
  │
  ▼
构建 Message 对象：
{
  role: 'user',
  content: '帮我重构这个函数'
}
  │
  ▼
添加到 messages 数组
  │
  ▼
onBeforeQuery Hook 修改（可能添加上下文）
  │
  ▼
发送给 LLM API
```

### 6.3 消息的响应

```
LLM 返回流式响应：
  │
  ├─ text delta: "我来帮你重构..."
  │   └─ 实时渲染到 UI
  │
  ├─ tool_use: { name: 'Read', input: { file_path: '...' } }
  │   └─ 收集工具调用
  │
  └─ end_turn
      └─ 构建 assistant message
```

### 6.4 消息的存储

```
assistant message 添加到 messages 数组：
{
  role: 'assistant',
  content: [
    { type: 'text', text: '我来帮你重构...' },
    { type: 'tool_use', id: 'toolu_xxx', name: 'Read', input: {...} }
  ]
}
  │
  ▼
工具执行后，添加 tool_result message：
{
  role: 'user',
  content: [
    { type: 'tool_result', tool_use_id: 'toolu_xxx', content: '...' }
  ]
}
  │
  ▼
ToolResultStorage 压缩（如果结果过大）
  │
  ▼
继续下一轮 Query（如果有更多 tool_use）
```

---

## 7. 性能优化机制

### 7.1 QueryProfiler：精确计时

**关键指标**：

```typescript
interface QueryProfile {
  phases: {
    context_assembly: number    // 上下文组装耗时
    api_call: number            // API 调用耗时
    tool_execution: number      // 工具执行耗时
    result_compression: number  // 结果压缩耗时
  }
  total: number
  slowWarnings: string[]        // 慢操作警告
}
```

**慢操作阈值**：

| 阶段 | 阈值 | 警告 |
|------|------|------|
| context_assembly | 500ms | "上下文组装过慢，考虑优化" |
| api_call | 5000ms | "API 调用过慢，检查网络" |
| tool_execution | 10000ms | "工具执行过慢，考虑并发" |
| result_compression | 1000ms | "结果压缩过慢，考虑异步" |

### 7.2 工具并发执行

**依赖分析算法**：

```typescript
function analyzeDependencies(toolUses: ToolUse[]): {
  independent: ToolUse[]
  dependent: ToolUse[]
} {
  const independent: ToolUse[] = []
  const dependent: ToolUse[] = []
  
  for (const toolUse of toolUses) {
    // 检查是否依赖前面的工具结果
    const hasDependency = toolUses.some((other, index) => {
      if (other === toolUse) return false
      // 如果输入中引用了其他工具的输出
      return JSON.stringify(toolUse.input).includes(other.id)
    })
    
    if (hasDependency) {
      dependent.push(toolUse)
    } else {
      independent.push(toolUse)
    }
  }
  
  return { independent, dependent }
}
```

**性能提升**：
- 3 个独立工具并发执行：节省 66% 时间
- 5 个独立工具并发执行：节省 80% 时间

### 7.3 ToolResultStorage 压缩策略

**压缩阈值**：

| 结果大小 | 策略 | 压缩率 |
|----------|------|--------|
| < 1KB | 不压缩 | 0% |
| 1KB - 10KB | 摘要 + 引用 | 50-70% |
| 10KB - 100KB | 强压缩 + 引用 | 70-90% |
| > 100KB | 仅保留摘要 | 95%+ |

**压缩示例**：

```typescript
// 原始结果（5KB）
{
  tool_use_id: 'toolu_xxx',
  content: '... 5000 行代码 ...'
}

// 压缩后（500B）
{
  tool_use_id: 'toolu_xxx',
  content: '[文件内容已压缩，共 5000 行。见上文 tool_use toolu_xxx 的完整输出]',
  _compressed: true,
  _original_size: 5000,
  _compression_ratio: 0.9
}
```

---

## 8. 错误处理与恢复

### 8.1 错误分类

```typescript
enum ErrorType {
  // 可重试错误
  NetworkError = 'network_error',       // 网络错误
  TimeoutError = 'timeout_error',       // 超时
  RateLimitError = 'rate_limit_error',  // 速率限制
  
  // 不可重试错误
  AuthError = 'auth_error',             // 认证错误
  PermissionError = 'permission_error', // 权限错误
  ValidationError = 'validation_error', // 参数错误
  
  // 系统错误
  InternalError = 'internal_error',     // 内部错误
  UnknownError = 'unknown_error'        // 未知错误
}
```

### 8.2 重试策略

```typescript
interface RetryConfig {
  maxRetries: number        // 最大重试次数
  backoff: 'linear' | 'exponential'  // 退避策略
  initialDelay: number      // 初始延迟（ms）
  maxDelay: number          // 最大延迟（ms）
}

async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: RetryConfig
): Promise<T> {
  let lastError: Error
  
  for (let i = 0; i < config.maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      
      // 不可重试错误直接抛出
      if (!isRetryable(error)) {
        throw error
      }
      
      // 计算延迟
      const delay = config.backoff === 'exponential'
        ? Math.min(config.initialDelay * Math.pow(2, i), config.maxDelay)
        : Math.min(config.initialDelay * (i + 1), config.maxDelay)
      
      await sleep(delay)
    }
  }
  
  throw lastError
}
```

### 8.3 错误恢复

```typescript
class ErrorRecovery {
  async recover(error: Error, context: ExecutionContext): Promise<void> {
    const errorType = classifyError(error)
    
    switch (errorType) {
      case ErrorType.NetworkError:
        // 网络错误：重试
        await this.retryWithBackoff(context.operation)
        break
      
      case ErrorType.TimeoutError:
        // 超时：增加超时时间后重试
        context.timeout *= 2
        await this.retryWithBackoff(context.operation)
        break
      
      case ErrorType.RateLimitError:
        // 速率限制：等待后重试
        await sleep(60000) // 等待 1 分钟
        await this.retryWithBackoff(context.operation)
        break
      
      case ErrorType.PermissionError:
        // 权限错误：请求用户授权
        await this.requestPermission(context)
        break
      
      default:
        // 其他错误：记录并通知用户
        this.logError(error)
        this.notifyUser(error)
        throw error
    }
  }
}
```

---

## 9. 可观测性

### 9.1 遥测数据

**收集的指标**：

```typescript
interface TelemetryData {
  // 性能指标
  queryDuration: number
  toolExecutionDuration: number
  contextAssemblyDuration: number
  
  // 使用指标
  toolsUsed: string[]
  toolsDiscovered: string[]  // Tool Search 发现的工具
  messagesCount: number
  tokensUsed: number
  
  // 错误指标
  errors: Array<{
    type: ErrorType
    message: string
    stack: string
  }>
  
  // 用户行为
  permissionDenials: number
  cancellations: number
}
```

### 9.2 日志系统

**日志级别**：

```typescript
enum LogLevel {
  DEBUG = 'debug',     // 调试信息
  INFO = 'info',       // 一般信息
  WARN = 'warn',       // 警告
  ERROR = 'error',     // 错误
  FATAL = 'fatal'      // 致命错误
}
```

**结构化日志**：

```typescript
interface LogEntry {
  timestamp: string
  level: LogLevel
  component: string    // 组件名称
  message: string
  context?: any        // 上下文数据
  error?: Error        // 错误对象
}
```

---

## 10. 实现检查清单

### 10.1 核心功能（必须实现）

- [ ] REPL 主循环
  - [ ] 消息队列管理
  - [ ] QueryGuard 互斥锁
  - [ ] 生命周期 Hook（onBeforeQuery, onTurnComplete）
  
- [ ] QueryEngine
  - [ ] API 调用封装
  - [ ] 流式响应处理
  - [ ] 取消控制
  
- [ ] StreamingToolExecutor
  - [ ] 工具注册和查找
  - [ ] 权限检查
  - [ ] 并发执行
  - [ ] 结果压缩
  
- [ ] PermissionContext
  - [ ] 4 级权限模式
  - [ ] 权限规则匹配
  - [ ] 用户确认队列

### 10.2 性能优化（推荐实现）

- [ ] QueryProfiler 性能追踪
- [ ] 工具依赖分析和并发执行
- [ ] ToolResultStorage 自动压缩
- [ ] 慢操作警告

### 10.3 可观测性（推荐实现）

- [ ] 结构化日志
- [ ] 遥测数据收集
- [ ] 错误分类和追踪

### 10.4 高级特性（可选实现）

- [ ] YOLO Classifier 自动审查
- [ ] Speculation 预执行
- [ ] Compact 自动压缩
- [ ] 记忆提取

---

## 11. 参考实现

### 11.1 Claude Code 源码位置

| 组件 | 文件路径 |
|------|----------|
| REPL | `src/cli/repl.tsx` |
| QueryEngine | `src/query/QueryEngine.ts` |
| QueryGuard | `src/query/QueryGuard.ts` |
| QueryProfiler | `src/query/queryProfiler.ts` |
| StreamingToolExecutor | `src/tools/StreamingToolExecutor.ts` |
| PermissionContext | `src/permission/PermissionContext.ts` |
| MessageQueueManager | `src/cli/messageQueueManager.ts` |
| PostSamplingHooks | `src/hooks/postSamplingHooks.ts` |

### 11.2 关键函数签名

```typescript
// REPL.tsx
function REPL(props: REPLProps): JSX.Element

// QueryEngine.ts
class QueryEngine {
  constructor(config: QueryEngineConfig)
  async query(request: QueryRequest): Promise<QueryResponse>
}

// StreamingToolExecutor.ts
class StreamingToolExecutor {
  async execute(toolUses: ToolUse[]): Promise<ToolResult[]>
}

// PermissionContext.ts
function createPermissionContext(
  tool: Tool,
  input: any,
  toolUseContext: ToolUseContext
): ToolPermissionContext
```

---

## 12. 下一步阅读

- **[02-AGENT-LOOP.md](02-AGENT-LOOP.md)**：深入理解 Agent Loop 的完整流程
- **[03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md)**：工具系统的设计与实现
- **[04-CONTEXT-ENGINE.md](04-CONTEXT-ENGINE.md)**：上下文管理的三层防线
- **[05-HOOK-SYSTEM.md](05-HOOK-SYSTEM.md)**：Hook 系统的 5 层注入点
- **[06-PERMISSION.md](06-PERMISSION.md)**：权限系统的安全管道

---

**文档版本**：v1.0  
**最后更新**：2026-04-01  
**基于**：Claude Code v2.1.88 源码分析
