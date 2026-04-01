# 03 - 工具系统：LLM 的能力原子

## 1. 核心概念

### 1.1 什么是 Tool

在 Claude Code 中，**Tool 是 LLM 可调用的最小能力单元**。它不是简单的函数调用，而是一个完整的能力抽象，包含：

- **JSON Schema 定义**：描述工具的输入参数
- **执行函数**：实际执行逻辑
- **权限检查**：是否允许执行
- **错误分类**：统一的错误处理
- **并发控制**：如何与其他工具协同执行

### 1.2 设计动机

**为什么需要 Tool 系统？**

1. **标准化接口**：LLM 通过统一的 JSON Schema 理解能力边界
2. **权限管理**：每个 Tool 都可以独立配置权限策略
3. **并发优化**：不同类型的 Tool 可以并行执行
4. **错误恢复**：统一的错误分类支持智能重试
5. **可扩展性**：Plugin/Skill 可以注册新 Tool

### 1.3 Tool vs Command vs Service

```
┌─────────────────────────────────────────────┐
│  Command (用户意图层)                        │
│  - 参数解析                                  │
│  - UI 交互                                   │
│  - 用户确认                                  │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│  Tool (能力原子层)                           │
│  - JSON Schema 定义                          │
│  - LLM 可调用                                │
│  - 权限检查                                  │
│  - 并发控制                                  │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│  Service (业务逻辑层)                        │
│  - 跨 Tool 的复杂逻辑                        │
│  - 状态管理                                  │
│  - 外部系统集成                              │
└─────────────────────────────────────────────┘
```

**关键区别**：
- **Command** 面向人类，有丰富的交互和提示
- **Tool** 面向 LLM，有严格的 Schema 约束
- **Service** 面向系统，承载可复用的业务逻辑

---

## 2. 架构设计

### 2.1 Tool 接口定义

```typescript
interface Tool {
  // 基础元数据
  name: string;                    // 工具名称（唯一标识）
  description: string;             // 工具描述（LLM 可见）
  
  // JSON Schema 定义
  input_schema: {
    type: "object";
    properties: Record<string, JSONSchema>;
    required?: string[];
  };
  
  // 执行函数
  execute: (
    params: Record<string, any>,
    context: ToolUseContext
  ) => Promise<ToolResult>;
  
  // 可选配置
  cache_control?: { type: "ephemeral" };  // 缓存控制
  concurrency?: "sequential" | "parallel"; // 并发策略
  permission?: PermissionLevel;            // 权限要求
}

interface ToolResult {
  type: "tool_result";
  tool_use_id: string;
  content: string | ContentBlock[];
  is_error?: boolean;
}

interface ToolUseContext {
  abortSignal: AbortSignal;       // 取消信号
  canUseTool: CanUseToolFn;       // 权限检查函数
  onProgress?: ProgressCallback;   // 进度回调
  workingDirectory: string;        // 工作目录
  // ... 其他上下文
}
```

### 2.2 工具注册机制

```typescript
class ToolRegistry {
  private tools: Map<string, Tool> = new Map();
  
  // 注册工具
  register(tool: Tool): void {
    if (this.tools.has(tool.name)) {
      throw new Error(`Tool ${tool.name} already registered`);
    }
    this.tools.set(tool.name, tool);
  }
  
  // 获取工具
  get(name: string): Tool | undefined {
    return this.tools.get(name);
  }
  
  // 获取所有工具（用于发送给 LLM）
  getAllSchemas(): ToolSchema[] {
    return Array.from(this.tools.values()).map(tool => ({
      name: tool.name,
      description: tool.description,
      input_schema: tool.input_schema,
      cache_control: tool.cache_control
    }));
  }
  
  // 按类型分组（用于并发控制）
  groupByType(): Map<ToolType, Tool[]> {
    const groups = new Map<ToolType, Tool[]>();
    for (const tool of this.tools.values()) {
      const type = inferToolType(tool.name);
      if (!groups.has(type)) {
        groups.set(type, []);
      }
      groups.get(type)!.push(tool);
    }
    return groups;
  }
}
```

### 2.3 工具执行流水线

```
LLM 输出 tool_use
       ↓
partitionToolCalls()          ← 按类型分区
       ↓
┌──────┴──────┐
│  Sequential  │  Parallel
│   Group 1    │  Group 2
└──────┬───────┘
       ↓
checkPermissionsAndCallTool() ← 权限检查 + 执行
       ↓
┌──────┴──────┐
│  Pre-Hook   │  ← PreToolUse Hook
└──────┬──────┘
       ↓
tool.execute()                ← 实际执行
       ↓
┌──────┴──────┐
│  Post-Hook  │  ← PostToolUse Hook
└──────┬──────┘
       ↓
classifyToolError()           ← 错误分类
       ↓
addToolResult()               ← 结果注入消息队列
```

---

## 3. 接口契约

### 3.1 并发执行策略（partitionToolCalls）

```typescript
/**
 * 将工具调用按并发策略分区
 * 
 * 设计原则：
 * 1. 文件系统操作（Read/Write/Edit）必须串行
 * 2. 网络请求（WebSearch/WebFetch）可以并行
 * 3. 计算密集型（Grep/Glob）可以并行
 * 4. 状态修改操作（Git/Bash）必须串行
 */
function partitionToolCalls(
  toolUses: ToolUse[]
): ToolCallPartition[] {
  const partitions: ToolCallPartition[] = [];
  const sequentialTools = new Set([
    'Read', 'Write', 'Edit', 'Bash', 
    'NotebookEdit', 'EnterWorktree', 'ExitWorktree'
  ]);
  
  let currentPartition: ToolUse[] = [];
  let isSequential = false;
  
  for (const toolUse of toolUses) {
    const needsSequential = sequentialTools.has(toolUse.name);
    
    if (needsSequential || isSequential) {
      // 串行工具：每个单独一个分区
      if (currentPartition.length > 0) {
        partitions.push({
          tools: currentPartition,
          mode: isSequential ? 'sequential' : 'parallel'
        });
        currentPartition = [];
      }
      partitions.push({
        tools: [toolUse],
        mode: 'sequential'
      });
      isSequential = needsSequential;
    } else {
      // 并行工具：累积到当前分区
      currentPartition.push(toolUse);
      isSequential = false;
    }
  }
  
  if (currentPartition.length > 0) {
    partitions.push({
      tools: currentPartition,
      mode: 'parallel'
    });
  }
  
  return partitions;
}

/**
 * 获取最大并发数
 */
function getMaxToolUseConcurrency(toolName: string): number {
  const concurrencyLimits: Record<string, number> = {
    'WebSearch': 3,
    'WebFetch': 5,
    'Grep': 4,
    'Glob': 4,
    'Read': 1,      // 文件系统操作串行
    'Write': 1,
    'Edit': 1,
    'Bash': 1
  };
  
  return concurrencyLimits[toolName] || 2;
}
```

**设计原因**：
- **文件系统一致性**：Read/Write/Edit 串行避免竞态条件
- **网络优化**：WebSearch/WebFetch 并行提升响应速度
- **资源保护**：限制并发数避免系统过载

### 3.2 权限检查嵌入执行链

```typescript
/**
 * 权限检查 + 工具执行一体化
 * 
 * 关键设计：权限检查不是前置门卫，而是管道的一部分
 */
async function checkPermissionsAndCallTool(
  tool: Tool,
  toolUse: ToolUse,
  context: ToolUseContext
): Promise<ToolResult> {
  const { canUseTool, abortSignal } = context;
  
  // 1. 权限检查
  const permission = await canUseTool(tool.name, toolUse.input);
  
  if (permission.denied) {
    return {
      type: 'tool_result',
      tool_use_id: toolUse.id,
      content: `Permission denied: ${permission.reason}`,
      is_error: true
    };
  }
  
  if (permission.needsConfirmation) {
    // 等待用户确认
    const confirmed = await requestUserConfirmation(
      tool.name, 
      toolUse.input,
      permission.reason
    );
    
    if (!confirmed) {
      return {
        type: 'tool_result',
        tool_use_id: toolUse.id,
        content: 'User denied permission',
        is_error: true
      };
    }
  }
  
  // 2. 执行前 Hook
  await executePreToolUseHooks(tool.name, toolUse.input);
  
  // 3. 实际执行
  try {
    const result = await tool.execute(toolUse.input, context);
    
    // 4. 执行后 Hook
    await executePostToolUseHooks(tool.name, result);
    
    return result;
  } catch (error) {
    // 5. 错误分类
    const classified = classifyToolError(error, tool.name);
    
    return {
      type: 'tool_result',
      tool_use_id: toolUse.id,
      content: classified.message,
      is_error: true
    };
  }
}

/**
 * 流式版本：支持进度回调
 */
async function streamedCheckPermissionsAndCallTool(
  tool: Tool,
  toolUse: ToolUse,
  context: ToolUseContext,
  onProgress: (progress: ToolProgress) => void
): Promise<ToolResult> {
  // 权限检查逻辑同上
  
  // 执行时注入进度回调
  const enhancedContext = {
    ...context,
    onProgress: (progress: number, message: string) => {
      onProgress({
        tool_use_id: toolUse.id,
        tool_name: tool.name,
        progress,
        message
      });
    }
  };
  
  return tool.execute(toolUse.input, enhancedContext);
}
```

### 3.3 错误分类系统

```typescript
/**
 * 统一的错误分类入口
 * 
 * 设计目标：
 * 1. 区分可重试 vs 不可重试错误
 * 2. 提取结构化错误信息
 * 3. 生成用户友好的错误消息
 */
function classifyToolError(
  error: unknown,
  toolName: string
): ClassifiedError {
  // 1. 已知错误类型
  if (error instanceof ClaudeError) {
    return {
      type: error.constructor.name,
      message: error.message,
      retryable: error.retryable,
      userMessage: error.userMessage
    };
  }
  
  // 2. 系统错误
  if (error instanceof Error) {
    // 文件系统错误
    if ('code' in error) {
      const code = (error as any).code;
      
      if (code === 'ENOENT') {
        return {
          type: 'FileNotFoundError',
          message: `File not found: ${error.message}`,
          retryable: false,
          userMessage: 'The file does not exist'
        };
      }
      
      if (code === 'EACCES') {
        return {
          type: 'PermissionError',
          message: `Permission denied: ${error.message}`,
          retryable: false,
          userMessage: 'Permission denied to access the file'
        };
      }
      
      if (code === 'ETIMEDOUT') {
        return {
          type: 'TimeoutError',
          message: error.message,
          retryable: true,
          userMessage: 'Operation timed out, please retry'
        };
      }
    }
    
    // 网络错误
    if (error.message.includes('ECONNREFUSED')) {
      return {
        type: 'ConnectionError',
        message: error.message,
        retryable: true,
        userMessage: 'Connection refused, please check network'
      };
    }
  }
  
  // 3. 取消信号
  if (error instanceof DOMException && error.name === 'AbortError') {
    return {
      type: 'AbortError',
      message: 'Operation was cancelled',
      retryable: false,
      userMessage: 'Operation cancelled by user'
    };
  }
  
  // 4. 未知错误
  return {
    type: 'UnknownError',
    message: String(error),
    retryable: false,
    userMessage: 'An unexpected error occurred'
  };
}

/**
 * 错误类型体系（Strategy 模式）
 */
class ClaudeError extends Error {
  retryable: boolean = false;
  userMessage: string;
  
  constructor(message: string, userMessage?: string) {
    super(message);
    this.userMessage = userMessage || message;
  }
}

class McpAuthError extends ClaudeError {
  retryable = false;
}

class RipgrepTimeoutError extends ClaudeError {
  retryable = true;
}

class FileTooLargeError extends ClaudeError {
  retryable = false;
}

class ImageSizeError extends ClaudeError {
  retryable = false;
}

class CannotRetryError extends ClaudeError {
  retryable = false;
}
```

---

## 4. 实现要点

### 4.1 StreamingToolExecutor：核心执行器

```typescript
/**
 * 流式工具执行器
 * 
 * 职责：
 * 1. 管理工具调用的生命周期
 * 2. 协调并发执行
 * 3. 处理取消信号
 * 4. 收集执行结果
 */
class StreamingToolExecutor {
  private tools: Map<string, Tool>;
  private canUseTool: CanUseToolFn;
  private context: ToolUseContext;
  private abortController: AbortController;
  
  constructor(
    tools: Tool[],
    canUseTool: CanUseToolFn,
    context: ToolUseContext
  ) {
    this.tools = new Map(tools.map(t => [t.name, t]));
    this.canUseTool = canUseTool;
    this.context = context;
    this.abortController = new AbortController();
  }
  
  /**
   * 执行工具调用（支持并发）
   */
  async execute(toolUses: ToolUse[]): Promise<ToolResult[]> {
    const partitions = partitionToolCalls(toolUses);
    const results: ToolResult[] = [];
    
    for (const partition of partitions) {
      if (partition.mode === 'sequential') {
        // 串行执行
        for (const toolUse of partition.tools) {
          const result = await this.executeSingle(toolUse);
          results.push(result);
        }
      } else {
        // 并行执行
        const parallelResults = await Promise.all(
          partition.tools.map(toolUse => this.executeSingle(toolUse))
        );
        results.push(...parallelResults);
      }
    }
    
    return results;
  }
  
  /**
   * 执行单个工具
   */
  private async executeSingle(toolUse: ToolUse): Promise<ToolResult> {
    const tool = this.tools.get(toolUse.name);
    
    if (!tool) {
      return {
        type: 'tool_result',
        tool_use_id: toolUse.id,
        content: `Unknown tool: ${toolUse.name}`,
        is_error: true
      };
    }
    
    // 创建子 AbortController（级联取消）
    const childController = createChildAbortController(
      this.abortController
    );
    
    const enhancedContext = {
      ...this.context,
      abortSignal: childController.signal
    };
    
    return checkPermissionsAndCallTool(tool, toolUse, enhancedContext);
  }
  
  /**
   * 取消所有执行中的工具
   */
  cancel(): void {
    this.abortController.abort();
  }
  
  /**
   * 标记工具执行完成
   */
  markToolUseAsComplete(toolUseId: string): void {
    // 通知 UI 更新状态
    this.context.onToolComplete?.(toolUseId);
  }
}

/**
 * 创建子 AbortController（级联取消）
 */
function createChildAbortController(
  parent: AbortController
): AbortController {
  const child = new AbortController();
  
  // 父取消时，子也取消
  parent.signal.addEventListener('abort', () => {
    child.abort();
  });
  
  return child;
}
```

### 4.2 工具分组显示（GroupedToolUses）

```typescript
/**
 * 工具调用分组显示
 * 
 * 设计目标：
 * 1. 相同类型的工具调用合并显示
 * 2. 显示执行进度
 * 3. 支持展开/折叠
 */
interface GroupedToolUse {
  toolName: string;
  count: number;
  status: 'pending' | 'running' | 'completed' | 'error';
  items: ToolUse[];
  results?: ToolResult[];
}

function groupToolUses(toolUses: ToolUse[]): GroupedToolUse[] {
  const groups = new Map<string, GroupedToolUse>();
  
  for (const toolUse of toolUses) {
    if (!groups.has(toolUse.name)) {
      groups.set(toolUse.name, {
        toolName: toolUse.name,
        count: 0,
        status: 'pending',
        items: [],
        results: []
      });
    }
    
    const group = groups.get(toolUse.name)!;
    group.count++;
    group.items.push(toolUse);
  }
  
  return Array.from(groups.values());
}

/**
 * UI 渲染示例（React + Ink）
 */
function ToolUsesDisplay({ groups }: { groups: GroupedToolUse[] }) {
  return (
    <Box flexDirection="column">
      {groups.map(group => (
        <Box key={group.toolName} marginBottom={1}>
          <Text color={getStatusColor(group.status)}>
            {getStatusIcon(group.status)} {group.toolName}
          </Text>
          {group.count > 1 && (
            <Text dimColor> × {group.count}</Text>
          )}
        </Box>
      ))}
    </Box>
  );
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'pending': return '⏳';
    case 'running': return '⚙️';
    case 'completed': return '✅';
    case 'error': return '❌';
    default: return '•';
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'running': return 'blue';
    case 'completed': return 'green';
    case 'error': return 'red';
    default: return 'gray';
  }
}
```

### 4.3 工具结果存储与压缩

```typescript
/**
 * 工具结果存储
 * 
 * 问题：大的工具输出会导致上下文爆炸
 * 解决：用占位符替换大输出，按需恢复
 */
class ToolResultStorage {
  private storage: Map<string, string> = new Map();
  private sizeThreshold = 10000; // 10KB
  
  /**
   * 存储工具结果（如果太大则替换为占位符）
   */
  storeResult(toolUseId: string, content: string): string {
    if (content.length > this.sizeThreshold) {
      this.storage.set(toolUseId, content);
      
      return `[Large output stored (${content.length} chars). ` +
             `Use tool_use_id: ${toolUseId} to retrieve.]`;
    }
    
    return content;
  }
  
  /**
   * 恢复工具结果
   */
  retrieveResult(toolUseId: string): string | undefined {
    return this.storage.get(toolUseId);
  }
  
  /**
   * 重建内容替换状态（用于子 Agent）
   */
  reconstructContentReplacementState(
    messages: Message[]
  ): Map<string, string> {
    const state = new Map<string, string>();
    
    for (const message of messages) {
      if (message.role === 'user') {
        for (const block of message.content) {
          if (block.type === 'tool_result') {
            const match = block.content.match(
              /\[Large output stored.*tool_use_id: (.*?)\]/
            );
            if (match) {
              const stored = this.storage.get(match[1]);
              if (stored) {
                state.set(match[1], stored);
              }
            }
          }
        }
      }
    }
    
    return state;
  }
}
```

### 4.4 边界情况处理

**1. 工具执行超时**

```typescript
async function executeWithTimeout(
  tool: Tool,
  toolUse: ToolUse,
  context: ToolUseContext,
  timeoutMs: number = 120000 // 2分钟
): Promise<ToolResult> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => {
      reject(new Error(`Tool ${tool.name} timed out after ${timeoutMs}ms`));
    }, timeoutMs);
  });
  
  return Promise.race([
    checkPermissionsAndCallTool(tool, toolUse, context),
    timeoutPromise
  ]);
}
```

**2. 工具不存在**

```typescript
function handleUnknownTool(toolName: string, toolUseId: string): ToolResult {
  return {
    type: 'tool_result',
    tool_use_id: toolUseId,
    content: `Unknown tool: ${toolName}. Available tools: ${
      Array.from(toolRegistry.keys()).join(', ')
    }`,
    is_error: true
  };
}
```

**3. 参数验证失败**

```typescript
function validateToolInput(
  tool: Tool,
  input: Record<string, any>
): ValidationResult {
  const schema = tool.input_schema;
  const errors: string[] = [];
  
  // 检查必需参数
  for (const required of schema.required || []) {
    if (!(required in input)) {
      errors.push(`Missing required parameter: ${required}`);
    }
  }
  
  // 检查参数类型
  for (const [key, value] of Object.entries(input)) {
    const propSchema = schema.properties[key];
    if (!propSchema) {
      errors.push(`Unknown parameter: ${key}`);
      continue;
    }
    
    if (!validateType(value, propSchema)) {
      errors.push(`Invalid type for ${key}: expected ${propSchema.type}`);
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}
```

---

## 5. 设计决策

### 5.1 为什么并发执行需要分区？

**问题**：如果所有工具都并行执行，会导致：
- 文件系统竞态条件（同时读写同一文件）
- 资源耗尽（同时执行 100 个 Bash 命令）
- 状态不一致（Git 操作交错执行）

**解决方案**：`partitionToolCalls()` 按工具类型分区
- **串行工具**：Read/Write/Edit/Bash/Git（保证顺序）
- **并行工具**：WebSearch/WebFetch/Grep/Glob（提升速度）

**权衡**：
- ✅ 保证文件系统一致性
- ✅ 避免资源过载
- ❌ 牺牲部分并行性（但实际影响小）

### 5.2 为什么权限检查嵌入执行链？

**备选方案 1**：前置门卫模式
```typescript
// ❌ 问题：权限检查和执行分离，难以处理动态权限
if (!hasPermission(tool)) {
  throw new PermissionError();
}
const result = await tool.execute();
```

**备选方案 2**：装饰器模式
```typescript
// ❌ 问题：增加复杂度，难以处理流式执行
const wrappedTool = withPermissionCheck(tool);
const result = await wrappedTool.execute();
```

**最终方案**：管道模式
```typescript
// ✅ 优势：权限检查、Hook、执行、错误处理一体化
async function checkPermissionsAndCallTool(tool, toolUse, context) {
  await checkPermission();
  await preHook();
  const result = await tool.execute();
  await postHook();
  return classifyError(result);
}
```

**优势**：
- 统一的执行入口
- 支持流式进度回调
- 错误处理集中化
- Hook 自然嵌入

### 5.3 为什么需要 ToolResultStorage？

**问题场景**：
```typescript
// 用户：读取一个 10MB 的日志文件
Read({ file_path: "/var/log/huge.log" })

// 结果：10MB 文本进入消息历史
// 后果：上下文爆炸，后续请求变慢
```

**解决方案**：
```typescript
// 1. 检测大输出
if (content.length > 10000) {
  storage.set(toolUseId, content);
  return `[Large output stored (${content.length} chars)]`;
}

// 2. LLM 看到占位符，知道有大输出但不占用上下文
// 3. 如果需要，LLM 可以用 Grep 精确查询
Grep({ pattern: "ERROR", path: "/var/log/huge.log" })
```

**权衡**：
- ✅ 避免上下文爆炸
- ✅ 保持消息历史可读
- ❌ LLM 无法直接看到完整内容（但可以用 Grep 查询）

### 5.4 为什么错误分类如此重要？

**问题**：不同错误需要不同处理策略
- **网络超时** → 可重试
- **文件不存在** → 不可重试，需要 LLM 修正路径
- **权限拒绝** → 不可重试，需要用户授权
- **取消操作** → 不可重试，用户主动取消

**解决方案**：`classifyToolError()` 统一分类
```typescript
const classified = classifyToolError(error, toolName);

if (classified.retryable) {
  // 自动重试
  return retry(tool, toolUse, context);
} else {
  // 返回错误给 LLM，让它决定下一步
  return {
    type: 'tool_result',
    content: classified.userMessage,
    is_error: true
  };
}
```

**优势**：
- 统一的错误语义
- 支持智能重试
- 用户友好的错误消息
- 可扩展的错误类型体系

---

## 6. 参考实现

### 6.1 Claude Code 源码位置

| 功能 | 文件 | 关键函数 |
|------|------|----------|
| Tool 接口定义 | `src/Tool.ts` | `Tool`, `ToolResult`, `ToolUseContext` |
| 工具注册 | `src/tools.ts` | `getTools()`, `getToolSchemas()` |
| 并发控制 | `src/toolOrchestration.ts` | `partitionToolCalls()`, `getMaxToolUseConcurrency()` |
| 权限执行 | `src/toolExecution.ts` | `checkPermissionsAndCallTool()`, `streamedCheckPermissionsAndCallTool()` |
| 错误分类 | `src/toolExecution.ts` | `classifyToolError()` |
| 流式执行器 | `src/StreamingToolExecutor.ts` | `StreamingToolExecutor` 类 |
| 结果存储 | `src/toolResultStorage.ts` | `ToolResultStorage` 类 |
| 分组显示 | `src/components/GroupedToolUses.tsx` | `GroupedToolUses` 组件 |

### 6.2 关键函数签名

```typescript
// src/Tool.ts
export interface Tool {
  name: string;
  description: string;
  input_schema: JSONSchema;
  execute: (params: any, context: ToolUseContext) => Promise<ToolResult>;
  cache_control?: { type: "ephemeral" };
}

// src/toolOrchestration.ts
export function partitionToolCalls(
  toolUses: ToolUse[]
): ToolCallPartition[];

export function getMaxToolUseConcurrency(
  toolName: string
): number;

// src/toolExecution.ts
export async function checkPermissionsAndCallTool(
  tool: Tool,
  toolUse: ToolUse,
  context: ToolUseContext
): Promise<ToolResult>;

export function classifyToolError(
  error: unknown,
  toolName: string
): ClassifiedError;

// src/StreamingToolExecutor.ts
export class StreamingToolExecutor {
  constructor(
    tools: Tool[],
    canUseTool: CanUseToolFn,
    context: ToolUseContext
  );
  
  execute(toolUses: ToolUse[]): Promise<ToolResult[]>;
  cancel(): void;
  markToolUseAsComplete(toolUseId: string): void;
}
```

### 6.3 设计模式应用

**Strategy 模式**：错误类型体系
```typescript
// 基类
class ClaudeError extends Error {
  retryable: boolean;
  userMessage: string;
}

// 具体策略
class McpAuthError extends ClaudeError { retryable = false; }
class RipgrepTimeoutError extends ClaudeError { retryable = true; }
class FileTooLargeError extends ClaudeError { retryable = false; }
```

**Factory 模式**：工具创建
```typescript
function createTool(name: string, config: ToolConfig): Tool {
  return {
    name,
    description: config.description,
    input_schema: config.schema,
    execute: config.handler
  };
}
```

**Pipeline 模式**：执行流水线
```typescript
checkPermission → preHook → execute → postHook → classifyError
```

**Observer 模式**：进度回调
```typescript
tool.execute(params, {
  onProgress: (progress, message) => {
    // UI 更新
  }
});
```


---

## 7. 实现检查清单

### 7.1 必须实现的功能

**核心接口**
- [ ] Tool 接口定义（name, description, input_schema, execute）
- [ ] ToolResult 接口（type, tool_use_id, content, is_error）
- [ ] ToolUseContext 接口（abortSignal, canUseTool, onProgress）

**工具注册**
- [ ] ToolRegistry 类（register, get, getAllSchemas）
- [ ] 工具名称唯一性检查
- [ ] 按类型分组功能

**并发控制**
- [ ] partitionToolCalls() 实现
- [ ] 串行/并行分区逻辑
- [ ] getMaxToolUseConcurrency() 配置

**权限执行**
- [ ] checkPermissionsAndCallTool() 实现
- [ ] 权限检查集成
- [ ] Pre/Post Hook 支持

**错误处理**
- [ ] classifyToolError() 实现
- [ ] ClaudeError 基类
- [ ] 至少 5 种具体错误类型
- [ ] 可重试标记

**执行器**
- [ ] StreamingToolExecutor 类
- [ ] 并发执行逻辑
- [ ] AbortController 级联取消
- [ ] 进度回调支持

### 7.2 可选的优化

**性能优化**
- [ ] ToolResultStorage（大输出压缩）
- [ ] 工具执行超时控制
- [ ] 并发数动态调整

**用户体验**
- [ ] GroupedToolUses 分组显示
- [ ] 执行进度可视化
- [ ] 错误消息本地化

**可扩展性**
- [ ] 工具热加载
- [ ] 自定义并发策略
- [ ] 工具执行中间件

### 7.3 测试验证点

**单元测试**
- [ ] 工具注册和查询
- [ ] 并发分区逻辑
- [ ] 错误分类准确性
- [ ] AbortController 级联

**集成测试**
- [ ] 串行工具顺序执行
- [ ] 并行工具并发执行
- [ ] 权限拒绝处理
- [ ] 工具执行超时

**边界测试**
- [ ] 未知工具处理
- [ ] 参数验证失败
- [ ] 大输出压缩
- [ ] 取消信号传播

---

## 8. 工具执行流水线图

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM 输出 tool_use                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              partitionToolCalls()                            │
│  - 按工具类型分区                                             │
│  - 串行工具：Read/Write/Edit/Bash                            │
│  - 并行工具：WebSearch/WebFetch/Grep                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  Sequential      │          │  Parallel        │
│  Partition       │          │  Partition       │
│  (逐个执行)       │          │  (并发执行)       │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         └──────────────┬──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         checkPermissionsAndCallTool()                        │
│  1. 权限检查 (canUseTool)                                     │
│  2. 用户确认 (如需要)                                         │
│  3. Pre-Hook 执行                                            │
│  4. 工具执行 (tool.execute)                                  │
│  5. Post-Hook 执行                                           │
│  6. 错误分类 (classifyToolError)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ToolResult                                  │
│  - tool_use_id                                               │
│  - content (或占位符)                                         │
│  - is_error                                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            addToolResult() → 消息队列                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 核心设计原则总结

### 9.1 命令-工具-服务三层分离

```
Command (用户意图) → Tool (能力原子) → Service (业务逻辑)
```

- **Command** 只负责参数解析和 UI 交互
- **Tool** 是 LLM 可调用的原子操作（有 JSON Schema）
- **Service** 承载跨 Tool 的业务逻辑

### 9.2 权限即管道，而非门卫

权限检查不是在入口处一把拦截，而是嵌入执行流水线的每个阶段：
- `canUseTool` 函数贯穿整个 tool execution chain
- 支持动态权限决策（YOLO Classifier）
- 用户确认无缝集成

### 9.3 错误类型即领域语言

`ClaudeError` 家族（Strategy 模式）定义了完整的错误语义：
- 每种错误都有明确的 `retryable` 标记
- 用户友好的 `userMessage`
- 可扩展的错误类型体系

### 9.4 并发控制保证一致性

`partitionToolCalls()` 按工具类型分区：
- 文件系统操作串行（避免竞态）
- 网络请求并行（提升速度）
- 限制并发数（保护资源）

### 9.5 AbortController 树状传播

从 QueryEngine 到 StreamingToolExecutor 到单个 Tool，取消信号逐级传播：
- 父取消时，所有子任务自动取消
- 支持细粒度的取消控制
- 避免资源泄漏

---

## 10. 与其他系统的交互

### 10.1 与 Agent Loop 的关系

```
Agent Loop (02-AGENT-LOOP.md)
    ↓
  QueryEngine.query()
    ↓
  LLM 返回 tool_use
    ↓
  Tool System (本文档)
    ↓
  执行工具并返回结果
    ↓
  结果注入消息队列
    ↓
  回到 Agent Loop
```

### 10.2 与权限系统的关系

```
Permission System (06-PERMISSION.md)
    ↓
  canUseTool(toolName, params)
    ↓
  Tool System 调用权限检查
    ↓
  返回 { allowed, denied, needsConfirmation }
    ↓
  Tool System 根据结果决定是否执行
```

### 10.3 与 Hook 系统的关系

```
Hook System (05-HOOK-SYSTEM.md)
    ↓
  PreToolUse / PostToolUse Hook
    ↓
  Tool System 在执行前后触发
    ↓
  Hook 可以修改参数或结果
```

### 10.4 与上下文引擎的关系

```
Context Engine (04-CONTEXT-ENGINE.md)
    ↓
  ToolResultStorage
    ↓
  Tool System 存储大输出
    ↓
  Context Engine 用占位符替换
    ↓
  避免上下文爆炸
```

---

## 11. 常见问题

**Q1: 为什么不用简单的函数调用，而要定义 Tool 接口？**

A: Tool 接口提供了：
- 标准化的 JSON Schema（LLM 可理解）
- 统一的权限检查入口
- 一致的错误处理
- 可扩展的 Hook 机制

**Q2: 并发执行会不会导致文件系统竞态？**

A: 不会。`partitionToolCalls()` 确保文件系统操作（Read/Write/Edit）串行执行。

**Q3: 如何处理工具执行超时？**

A: 使用 `Promise.race()` 结合 `setTimeout()`，超时后通过 `AbortController` 取消执行。

**Q4: 大的工具输出如何处理？**

A: `ToolResultStorage` 会检测大输出（>10KB），用占位符替换，LLM 可以用 Grep 精确查询。

**Q5: 如何扩展新的工具？**

A: 实现 `Tool` 接口，调用 `toolRegistry.register(tool)` 注册即可。

---

**下一步**：阅读 [04-CONTEXT-ENGINE.md](04-CONTEXT-ENGINE.md) 了解上下文管理的三层防线。
