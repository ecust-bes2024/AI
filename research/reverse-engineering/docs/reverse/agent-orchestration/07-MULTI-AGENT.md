# 多 Agent 编排系统

## 1. 核心概念

### 1.1 设计动机

单 Agent 系统在处理复杂任务时面临三大挑战：

1. **任务并行度受限**：一个 Agent 只能串行处理任务，无法利用多核并行能力
2. **上下文污染**：不同子任务的上下文混在一起，导致 token 浪费和决策干扰
3. **专业化不足**：一个 Agent 需要处理所有类型的任务，缺乏专业化分工

多 Agent 编排系统通过 **Team/Swarm 模型** 解决这些问题：

- **Leader-Teammate 架构**：主 Agent 作为协调者，生成专业化的队友 Agent
- **任务所有权**：每个任务有明确的所有者，通过文件系统持久化
- **异步消息传递**：Agent 间通过 Mailbox 通信，解耦执行流程
- **隔离工作空间**：每个 Agent 在独立的 git worktree 中工作

### 1.2 关键术语

| 术语 | 定义 | 示例 |
|------|------|------|
| **Leader** | 主 Agent，负责任务分解和协调 | 用户直接交互的 Agent |
| **Teammate** | 队友 Agent，由 Leader 生成，执行子任务 | 专门处理测试的 Agent |
| **Task** | 任务单元，持久化为 JSON 文件 | `~/.claude/tasks/{listId}/{taskId}.json` |
| **Mailbox** | 异步消息队列，Agent 间通信通道 | `teammateMailbox.ts` |
| **Spawn** | 生成队友的操作，支持三种模式 | InProcess / SplitPane / SeparateWindow |
| **High Water Mark** | 任务进度断点，用于恢复和同步 | 文件持久化的进度标记 |

### 1.3 架构定位

多 Agent 系统不是简单的"多进程执行"，而是：

- **分布式任务系统**：任务状态通过文件系统共享
- **消息驱动架构**：Agent 通过消息传递协作，而非共享内存
- **容错设计**：任务可以在 Agent 崩溃后恢复
- **可观测性**：所有 Agent 状态可通过 UI 实时查看

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Leader Agent                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ TeamCreateTool│  │SendMessageTool│  │ handleSpawn()│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Task System (文件系统)                     │
│  ~/.claude/tasks/{taskListId}/                               │
│    ├── {taskId}.json          ← 任务定义                     │
│    ├── .high_water_mark       ← 进度断点                     │
│    └── .blocked_by            ← 阻塞关系                     │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Teammate 1  │  │  Teammate 2  │  │  Teammate 3  │
│  (InProcess) │  │ (SplitPane)  │  │(SeparateWin) │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                  ┌──────────────┐
                  │   Mailbox    │
                  │ (异步消息队列) │
                  └──────────────┘
```

### 2.2 数据流图

```
用户输入
  ↓
Leader Agent 分析任务
  ↓
创建 Task List (TeamCreateTool)
  ↓
生成 Teammate (handleSpawn)
  ├─→ resolveTeammateModel()      ← 选择队友模型
  ├─→ createWorktree()            ← 创建隔离工作空间
  └─→ spawnTeammateProcess()      ← 启动队友进程
  ↓
分配任务 (claimTask)
  ├─→ writeTaskFile()             ← 写入任务文件
  └─→ writeHighWaterMark()        ← 记录进度断点
  ↓
Teammate 执行任务
  ├─→ readTaskFile()              ← 读取任务定义
  ├─→ executeTask()               ← 执行任务逻辑
  └─→ updateHighWaterMark()       ← 更新进度
  ↓
发送消息 (SendMessageTool)
  ├─→ writeToMailbox()            ← 写入消息队列
  └─→ notifyLeader()              ← 通知 Leader
  ↓
Leader 汇总结果
  ├─→ readMailbox()               ← 读取队友消息
  ├─→ checkTaskStatus()           ← 检查任务状态
  └─→ synthesizeResults()         ← 合成最终结果
  ↓
返回给用户
```

### 2.3 状态机定义

#### Task 状态机

```
[Created] ──claimTask()──→ [Assigned]
    │                          │
    │                          │ startTask()
    │                          ↓
    │                      [Running]
    │                          │
    │                          ├─→ updateProgress() ──→ [Running]
    │                          │
    │                          ├─→ completeTask() ──→ [Completed]
    │                          │
    │                          ├─→ failTask() ──→ [Failed]
    │                          │
    │                          └─→ blockTask() ──→ [Blocked]
    │                                               │
    │                                               │ unblockTask()
    │                                               ↓
    └───────────────────────────────────────→ [Assigned]
```

#### Teammate 生命周期

```
[Idle] ──spawn()──→ [Spawning]
                        │
                        ├─→ resolveModel()
                        ├─→ createWorktree()
                        └─→ startProcess()
                        │
                        ↓
                    [Active]
                        │
                        ├─→ executeTask() ──→ [Busy]
                        │                      │
                        │                      │ taskComplete()
                        │                      ↓
                        │                  [Active]
                        │
                        ├─→ sendMessage() ──→ [Communicating]
                        │                      │
                        │                      ↓
                        │                  [Active]
                        │
                        └─→ terminate() ──→ [Terminated]
                                            │
                                            └─→ cleanupWorktree()
                                            │
                                            ↓
                                        [Cleaned]
```

---

## 3. 接口契约

### 3.1 Team 管理接口

```typescript
interface TeamManager {
  // 创建团队
  createTeam(config: TeamConfig): Promise<TeamId>
  
  // 生成队友
  spawnTeammate(
    mode: SpawnMode,           // InProcess | SplitPane | SeparateWindow
    model?: ModelId,           // 可选：指定队友模型
    worktreeConfig?: WorktreeConfig
  ): Promise<TeammateId>
  
  // 终止队友
  terminateTeammate(
    teammateId: TeammateId,
    cleanup: boolean           // 是否清理 worktree
  ): Promise<void>
  
  // 获取团队状态
  getTeamStatus(): TeamStatus
}

interface TeamConfig {
  taskListId: string
  maxTeammates: number
  defaultModel: ModelId
  sharedContext?: ContextConfig
}

type SpawnMode = 
  | 'InProcess'        // 进程内队友（共享内存）
  | 'SplitPane'        // 分屏队友（独立进程，UI 分屏）
  | 'SeparateWindow'   // 独立窗口队友（完全隔离）

interface TeamStatus {
  leaderId: AgentId
  teammates: TeammateInfo[]
  activeTasks: number
  completedTasks: number
}
```

### 3.2 Task 系统接口

```typescript
interface TaskSystem {
  // 创建任务
  createTask(definition: TaskDefinition): Promise<TaskId>
  
  // 认领任务
  claimTask(
    taskId: TaskId,
    teammateId: TeammateId
  ): Promise<boolean>
  
  // 取消分配
  unassignTask(taskId: TaskId): Promise<void>
  
  // 更新进度
  updateProgress(
    taskId: TaskId,
    progress: number,           // 0-100
    checkpoint?: any            // 可选：检查点数据
  ): Promise<void>
  
  // 完成任务
  completeTask(
    taskId: TaskId,
    result: TaskResult
  ): Promise<void>
  
  // 任务失败
  failTask(
    taskId: TaskId,
    error: Error
  ): Promise<void>
  
  // 阻塞任务
  blockTask(
    fromTaskId: TaskId,
    toTaskId: TaskId,
    reason: string
  ): Promise<void>
  
  // 解除阻塞
  unblockTask(
    fromTaskId: TaskId,
    toTaskId: TaskId
  ): Promise<void>
  
  // 读取任务
  readTask(taskId: TaskId): Promise<Task>
  
  // 查询任务
  queryTasks(filter: TaskFilter): Promise<Task[]>
}

interface TaskDefinition {
  title: string
  description: string
  dependencies?: TaskId[]      // 依赖的任务
  priority: number             // 优先级 (1-10)
  estimatedTokens?: number     // 预估 token 消耗
  context?: ContextSnapshot    // 任务上下文快照
}

interface Task {
  id: TaskId
  definition: TaskDefinition
  status: TaskStatus
  assignee?: TeammateId
  progress: number
  createdAt: number
  startedAt?: number
  completedAt?: number
  result?: TaskResult
  error?: Error
}

type TaskStatus = 
  | 'Created'
  | 'Assigned'
  | 'Running'
  | 'Blocked'
  | 'Completed'
  | 'Failed'
```

### 3.3 Mailbox 接口

```typescript
interface Mailbox {
  // 发送消息
  send(message: Message): Promise<void>
  
  // 接收消息（阻塞）
  receive(timeout?: number): Promise<Message | null>
  
  // 轮询消息（非阻塞）
  poll(): Promise<Message[]>
  
  // 订阅消息
  subscribe(
    filter: MessageFilter,
    handler: MessageHandler
  ): Subscription
  
  // 清空邮箱
  clear(): Promise<void>
}

interface Message {
  id: MessageId
  from: AgentId
  to: AgentId | 'broadcast'    // 支持广播
  type: MessageType
  payload: any
  timestamp: number
  replyTo?: MessageId          // 回复消息 ID
}

type MessageType =
  | 'TaskUpdate'               // 任务更新
  | 'TaskComplete'             // 任务完成
  | 'TaskFailed'               // 任务失败
  | 'Question'                 // 询问 Leader
  | 'Answer'                   // 回答队友
  | 'ContextShare'             // 共享上下文
  | 'Terminate'                // 终止信号

interface MessageFilter {
  from?: AgentId
  to?: AgentId
  type?: MessageType
  since?: number               // 时间戳过滤
}

type MessageHandler = (message: Message) => Promise<void>
```

### 3.4 High Water Mark 接口

```typescript
interface HighWaterMarkManager {
  // 读取断点
  readHighWaterMark(taskId: TaskId): Promise<HighWaterMark | null>
  
  // 写入断点
  writeHighWaterMark(
    taskId: TaskId,
    mark: HighWaterMark
  ): Promise<void>
  
  // 删除断点
  deleteHighWaterMark(taskId: TaskId): Promise<void>
}

interface HighWaterMark {
  taskId: TaskId
  progress: number             // 0-100
  checkpoint: any              // 检查点数据（任务特定）
  timestamp: number
  metadata?: Record<string, any>
}
```

---

## 4. 实现要点

### 4.1 任务分配算法

```typescript
// 伪代码：任务分配策略
function assignTask(task: Task, teammates: Teammate[]): Teammate | null {
  // 1. 过滤可用队友
  const available = teammates.filter(t => 
    t.status === 'Active' && 
    t.currentTask === null &&
    t.capabilities.includes(task.requiredCapability)
  )
  
  if (available.length === 0) return null
  
  // 2. 按负载排序（最少任务优先）
  available.sort((a, b) => 
    a.completedTasks - b.completedTasks
  )
  
  // 3. 考虑任务亲和性（同类任务分配给同一队友）
  const affinityMatch = available.find(t =>
    t.lastTaskType === task.type
  )
  
  return affinityMatch || available[0]
}
```

### 4.2 阻塞关系管理

```typescript
// 伪代码：阻塞关系图
class BlockingGraph {
  private edges: Map<TaskId, Set<TaskId>> = new Map()
  
  // 添加阻塞关系
  block(from: TaskId, to: TaskId): void {
    if (!this.edges.has(from)) {
      this.edges.set(from, new Set())
    }
    this.edges.get(from)!.add(to)
    
    // 检测循环依赖
    if (this.hasCycle(from, to)) {
      throw new Error('Circular dependency detected')
    }
  }
  
  // 解除阻塞
  unblock(from: TaskId, to: TaskId): void {
    this.edges.get(from)?.delete(to)
  }
  
  // 获取被阻塞的任务
  getBlockedTasks(taskId: TaskId): TaskId[] {
    return Array.from(this.edges.get(taskId) || [])
  }
  
  // 检测循环依赖（DFS）
  private hasCycle(start: TaskId, target: TaskId): boolean {
    const visited = new Set<TaskId>()
    const stack: TaskId[] = [target]
    
    while (stack.length > 0) {
      const current = stack.pop()!
      if (current === start) return true
      if (visited.has(current)) continue
      
      visited.add(current)
      const blocked = this.edges.get(current) || new Set()
      stack.push(...blocked)
    }
    
    return false
  }
}
```

### 4.3 文件系统持久化

```typescript
// 伪代码：任务文件系统布局
/*
~/.claude/tasks/
  ├── {taskListId}/
  │   ├── {taskId}.json              ← 任务定义
  │   ├── {taskId}.hwm               ← High Water Mark
  │   ├── {taskId}.blocked_by        ← 阻塞关系
  │   └── {taskId}.result            ← 任务结果
  └── mailbox/
      ├── {agentId}/
      │   ├── inbox/
      │   │   └── {messageId}.json   ← 收件箱
      │   └── outbox/
      │       └── {messageId}.json   ← 发件箱
*/

class FileSystemTaskStore {
  private basePath: string
  
  async writeTask(task: Task): Promise<void> {
    const taskPath = this.getTaskPath(task.id)
    await fs.writeFile(
      taskPath,
      JSON.stringify(task, null, 2)
    )
  }
  
  async readTask(taskId: TaskId): Promise<Task> {
    const taskPath = this.getTaskPath(taskId)
    const content = await fs.readFile(taskPath, 'utf-8')
    return JSON.parse(content)
  }
  
  async writeHighWaterMark(
    taskId: TaskId,
    mark: HighWaterMark
  ): Promise<void> {
    const hwmPath = this.getHWMPath(taskId)
    await fs.writeFile(
      hwmPath,
      JSON.stringify(mark, null, 2)
    )
  }
  
  async readHighWaterMark(
    taskId: TaskId
  ): Promise<HighWaterMark | null> {
    const hwmPath = this.getHWMPath(taskId)
    try {
      const content = await fs.readFile(hwmPath, 'utf-8')
      return JSON.parse(content)
    } catch (e) {
      if (e.code === 'ENOENT') return null
      throw e
    }
  }
  
  private getTaskPath(taskId: TaskId): string {
    return path.join(this.basePath, `${taskId}.json`)
  }
  
  private getHWMPath(taskId: TaskId): string {
    return path.join(this.basePath, `${taskId}.hwm`)
  }
}
```

### 4.4 Mailbox 实现

```typescript
// 伪代码：基于文件系统的 Mailbox
class FileSystemMailbox implements Mailbox {
  private inboxPath: string
  private outboxPath: string
  private watchers: Map<string, FSWatcher> = new Map()
  
  async send(message: Message): Promise<void> {
    const recipientInbox = this.getInboxPath(message.to)
    const messagePath = path.join(
      recipientInbox,
      `${message.id}.json`
    )
    
    await fs.mkdir(recipientInbox, { recursive: true })
    await fs.writeFile(
      messagePath,
      JSON.stringify(message, null, 2)
    )
  }
  
  async receive(timeout?: number): Promise<Message | null> {
    const messages = await this.poll()
    if (messages.length > 0) {
      return messages[0]
    }
    
    if (timeout) {
      return this.waitForMessage(timeout)
    }
    
    return null
  }
  
  async poll(): Promise<Message[]> {
    const files = await fs.readdir(this.inboxPath)
    const messages: Message[] = []
    
    for (const file of files) {
      if (!file.endsWith('.json')) continue
      
      const filePath = path.join(this.inboxPath, file)
      const content = await fs.readFile(filePath, 'utf-8')
      messages.push(JSON.parse(content))
      
      // 读取后删除（消费模式）
      await fs.unlink(filePath)
    }
    
    return messages.sort((a, b) => a.timestamp - b.timestamp)
  }
  
  subscribe(
    filter: MessageFilter,
    handler: MessageHandler
  ): Subscription {
    const watcher = fs.watch(this.inboxPath, async (event, filename) => {
      if (event !== 'rename' || !filename) return
      
      const filePath = path.join(this.inboxPath, filename)
      try {
        const content = await fs.readFile(filePath, 'utf-8')
        const message = JSON.parse(content)
        
        if (this.matchesFilter(message, filter)) {
          await handler(message)
          await fs.unlink(filePath)
        }
      } catch (e) {
        // 文件可能已被其他进程处理
      }
    })
    
    const subscriptionId = generateId()
    this.watchers.set(subscriptionId, watcher)
    
    return {
      unsubscribe: () => {
        watcher.close()
        this.watchers.delete(subscriptionId)
      }
    }
  }
  
  private matchesFilter(
    message: Message,
    filter: MessageFilter
  ): boolean {
    if (filter.from && message.from !== filter.from) return false
    if (filter.to && message.to !== filter.to) return false
    if (filter.type && message.type !== filter.type) return false
    if (filter.since && message.timestamp < filter.since) return false
    return true
  }
  
  private async waitForMessage(timeout: number): Promise<Message | null> {
    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        subscription.unsubscribe()
        resolve(null)
      }, timeout)
      
      const subscription = this.subscribe({}, async (message) => {
        clearTimeout(timer)
        subscription.unsubscribe()
        resolve(message)
      })
    })
  }
}
```

### 4.5 Teammate 模型选择

```typescript
// 伪代码：队友模型解析
function resolveTeammateModel(
  config: TeammateConfig,
  leaderModel: ModelId
): ModelId {
  // 1. 显式指定模型
  if (config.model) {
    return config.model
  }
  
  // 2. 根据任务类型选择
  if (config.taskType) {
    const modelMap: Record<string, ModelId> = {
      'code-review': 'claude-opus-4',      // 需要深度理解
      'testing': 'claude-sonnet-4',        // 平衡性能和成本
      'documentation': 'claude-sonnet-4',  // 文档生成
      'refactoring': 'claude-opus-4',      // 复杂重构
      'bug-fix': 'claude-sonnet-4',        // 快速修复
    }
    
    if (modelMap[config.taskType]) {
      return modelMap[config.taskType]
    }
  }
  
  // 3. 默认跟随 Leader
  return leaderModel
}
```

### 4.6 Worktree 隔离

```typescript
// 伪代码：为队友创建隔离工作空间
async function createTeammateWorktree(
  teammateId: TeammateId,
  repoRoot: string
): Promise<string> {
  const worktreePath = path.join(
    repoRoot,
    '.claude',
    'worktrees',
    teammateId
  )
  
  // 1. 创建 git worktree
  await exec(`git worktree add ${worktreePath} -b agent/${teammateId}`)
  
  // 2. 符号链接共享目录（节省空间）
  const sharedDirs = ['node_modules', '.git', 'dist']
  for (const dir of sharedDirs) {
    const source = path.join(repoRoot, dir)
    const target = path.join(worktreePath, dir)
    
    if (await fs.exists(source)) {
      await fs.symlink(source, target)
    }
  }
  
  // 3. 复制配置文件
  const configFiles = ['.env', 'package.json', 'tsconfig.json']
  for (const file of configFiles) {
    const source = path.join(repoRoot, file)
    const target = path.join(worktreePath, file)
    
    if (await fs.exists(source)) {
      await fs.copyFile(source, target)
    }
  }
  
  return worktreePath
}

// 清理 worktree
async function cleanupTeammateWorktree(
  worktreePath: string,
  repoRoot: string
): Promise<void> {
  // 1. 检查是否有未提交的更改
  const hasChanges = await exec(
    `git -C ${worktreePath} status --porcelain`
  )
  
  if (hasChanges.trim()) {
    // 提示用户或自动提交
    await exec(`git -C ${worktreePath} add -A`)
    await exec(`git -C ${worktreePath} commit -m "Auto-commit before cleanup"`)
  }
  
  // 2. 移除 worktree
  await exec(`git worktree remove ${worktreePath}`)
  
  // 3. 删除分支（可选）
  const branch = path.basename(worktreePath)
  await exec(`git branch -D agent/${branch}`)
}
```

### 4.7 完整的 Team 编排示例

```typescript
// 伪代码：完整的多 Agent 协作流程
async function orchestrateTeamDevelopment(
  feature: FeatureRequest
): Promise<FeatureResult> {
  // 1. Leader 分析需求，创建团队
  const team = await createTeam({
    taskListId: `feature-${feature.id}`,
    maxTeammates: 3,
    defaultModel: 'claude-sonnet-4'
  })
  
  // 2. 分解任务
  const tasks = await decomposeFeature(feature)
  // tasks = [
  //   { type: 'implementation', title: 'Implement core logic' },
  //   { type: 'testing', title: 'Write unit tests' },
  //   { type: 'documentation', title: 'Update docs' }
  // ]
  
  // 3. 创建任务并设置依赖
  const taskIds: TaskId[] = []
  for (const taskDef of tasks) {
    const task = await createTask({
      title: taskDef.title,
      description: taskDef.description,
      priority: taskDef.priority,
      estimatedTokens: taskDef.estimatedTokens,
      context: {
        featureSpec: feature.spec,
        codebase: await getCodebaseSnapshot()
      }
    })
    taskIds.push(task.id)
  }
  
  // 测试依赖实现，文档依赖测试
  await blockTask(taskIds[1], taskIds[0])  // testing blocks on implementation
  await blockTask(taskIds[2], taskIds[1])  // docs blocks on testing
  
  // 4. 生成 Teammate 并分配任务
  const teammates: Teammate[] = []
  for (let i = 0; i < tasks.length; i++) {
    const teammate = await spawnTeammate(
      'InProcess',
      resolveTeammateModel({ taskType: tasks[i].type }, 'claude-opus-4')
    )
    teammates.push(teammate)
    
    // 尝试认领任务（可能因依赖而失败）
    const claimed = await claimTask(taskIds[i], teammate.id)
    if (!claimed) {
      console.log(`Task ${taskIds[i]} blocked, will retry later`)
    }
  }
  
  // 5. 监控执行进度
  const results = await monitorTeamExecution(team, taskIds, teammates)
  
  // 6. 清理资源
  for (const teammate of teammates) {
    await terminateTeammate(teammate.id, true)
  }
  
  return synthesizeResults(results)
}

// 监控团队执行
async function monitorTeamExecution(
  team: Team,
  taskIds: TaskId[],
  teammates: Teammate[]
): Promise<TaskResult[]> {
  const results: TaskResult[] = []
  const completedTasks = new Set<TaskId>()
  
  // 订阅消息
  const subscription = mailbox.subscribe(
    { type: 'TaskComplete' },
    async (message) => {
      const { taskId, result } = message.payload
      results.push(result)
      completedTasks.add(taskId)
      
      // 解除阻塞
      const blockedTasks = await getBlockedTasks(taskId)
      for (const blockedId of blockedTasks) {
        await unblockTask(taskId, blockedId)
        
        // 尝试分配给空闲的 Teammate
        const idleTeammate = teammates.find(t => t.status === 'Idle')
        if (idleTeammate) {
          await claimTask(blockedId, idleTeammate.id)
        }
      }
    }
  )
  
  // 等待所有任务完成
  while (completedTasks.size < taskIds.length) {
    await sleep(1000)
    
    // 检查超时或失败
    for (const taskId of taskIds) {
      if (completedTasks.has(taskId)) continue
      
      const task = await readTask(taskId)
      if (task.status === 'Failed') {
        throw new Error(`Task ${taskId} failed: ${task.error}`)
      }
    }
  }
  
  subscription.unsubscribe()
  return results
}
```

### 4.8 并发控制与资源管理

```typescript
// 伪代码：并发控制器
class ConcurrencyController {
  private maxConcurrent: number
  private activeCount: number = 0
  private queue: Array<() => Promise<void>> = []
  
  constructor(maxConcurrent: number) {
    this.maxConcurrent = maxConcurrent
  }
  
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // 等待槽位
    while (this.activeCount >= this.maxConcurrent) {
      await this.waitForSlot()
    }
    
    this.activeCount++
    
    try {
      return await fn()
    } finally {
      this.activeCount--
      this.processQueue()
    }
  }
  
  private async waitForSlot(): Promise<void> {
    return new Promise(resolve => {
      this.queue.push(async () => resolve())
    })
  }
  
  private processQueue(): void {
    if (this.queue.length > 0 && this.activeCount < this.maxConcurrent) {
      const next = this.queue.shift()
      if (next) next()
    }
  }
}

// 使用并发控制器
const controller = new ConcurrencyController(5)  // 最多 5 个并发 Teammate

for (const task of tasks) {
  await controller.execute(async () => {
    const teammate = await spawnTeammate('InProcess')
    await claimTask(task.id, teammate.id)
    await executeTask(task)
    await terminateTeammate(teammate.id, true)
  })
}
```

### 4.9 任务调度策略

```typescript
// 伪代码：智能任务调度器
class TaskScheduler {
  private teammates: Teammate[]
  private tasks: Task[]
  
  // 调度策略：优先级 + 负载均衡 + 亲和性
  async schedule(): Promise<Map<TeammateId, TaskId>> {
    const assignments = new Map<TeammateId, TaskId>()
    
    // 1. 按优先级排序任务
    const sortedTasks = this.tasks
      .filter(t => t.status === 'Created' || t.status === 'Assigned')
      .sort((a, b) => b.priority - a.priority)
    
    // 2. 为每个任务找到最佳 Teammate
    for (const task of sortedTasks) {
      const teammate = await this.findBestTeammate(task)
      if (teammate) {
        assignments.set(teammate.id, task.id)
        await claimTask(task.id, teammate.id)
      }
    }
    
    return assignments
  }
  
  private async findBestTeammate(task: Task): Promise<Teammate | null> {
    // 过滤可用的 Teammate
    const available = this.teammates.filter(t => 
      t.status === 'Idle' || t.status === 'Active'
    )
    
    if (available.length === 0) return null
    
    // 计算每个 Teammate 的得分
    const scores = available.map(teammate => ({
      teammate,
      score: this.calculateScore(teammate, task)
    }))
    
    // 选择得分最高的
    scores.sort((a, b) => b.score - a.score)
    return scores[0].teammate
  }
  
  private calculateScore(teammate: Teammate, task: Task): number {
    let score = 0
    
    // 1. 负载因子（负载越低越好）
    const loadFactor = 1 - (teammate.currentLoad / teammate.maxLoad)
    score += loadFactor * 40
    
    // 2. 亲和性因子（同类任务优先）
    if (teammate.lastTaskType === task.type) {
      score += 30
    }
    
    // 3. 能力匹配（模型能力与任务需求）
    if (this.isCapabilityMatch(teammate.model, task.requiredCapability)) {
      score += 20
    }
    
    // 4. 历史成功率
    const successRate = teammate.completedTasks / 
                       (teammate.completedTasks + teammate.failedTasks)
    score += successRate * 10
    
    return score
  }
  
  private isCapabilityMatch(model: ModelId, capability: string): boolean {
    const modelCapabilities: Record<ModelId, string[]> = {
      'claude-opus-4': ['complex-reasoning', 'code-review', 'refactoring'],
      'claude-sonnet-4': ['testing', 'documentation', 'bug-fix'],
      'claude-haiku-4': ['simple-tasks', 'formatting']
    }
    
    return modelCapabilities[model]?.includes(capability) || false
  }
}
```

---

## 5. 设计决策

### 5.1 为什么用文件系统而非数据库？

**决策**：任务状态和消息队列都基于文件系统实现。

**理由**：

1. **可审计性**：用户可以直接查看 `~/.claude/tasks/` 目录，理解任务状态
2. **可修复性**：任务卡住时，用户可以手动编辑 JSON 文件恢复
3. **零依赖**：不需要安装 Redis、SQLite 等外部服务
4. **天然持久化**：文件系统本身就是持久化存储
5. **版本控制友好**：任务定义可以纳入 git 管理

**权衡**：

- ✅ 简单、可靠、可调试
- ❌ 性能不如内存数据库（但对 Agent 场景足够）
- ❌ 并发控制需要文件锁（通过原子操作缓解）

**实现细节**：

```typescript
// 原子写入：先写临时文件，再重命名
async function atomicWriteTask(task: Task): Promise<void> {
  const taskPath = getTaskPath(task.id)
  const tempPath = `${taskPath}.tmp`
  
  // 1. 写入临时文件
  await fs.writeFile(tempPath, JSON.stringify(task, null, 2))
  
  // 2. 原子重命名（操作系统保证原子性）
  await fs.rename(tempPath, taskPath)
}

// 文件锁：防止并发写入冲突
async function withFileLock<T>(
  lockPath: string,
  fn: () => Promise<T>
): Promise<T> {
  const lockFile = `${lockPath}.lock`
  
  // 尝试创建锁文件（O_EXCL 保证原子性）
  while (true) {
    try {
      await fs.open(lockFile, 'wx')
      break
    } catch (e) {
      if (e.code === 'EEXIST') {
        // 锁已被占用，等待后重试
        await sleep(100)
        continue
      }
      throw e
    }
  }
  
  try {
    return await fn()
  } finally {
    await fs.unlink(lockFile)
  }
}
```

### 5.2 为什么需要 High Water Mark？

**决策**：每个任务维护一个进度断点文件。

**理由**：

1. **容错恢复**：Agent 崩溃后可以从断点继续，而非重头开始
2. **进度可视化**：Leader 可以实时查看队友的进度
3. **增量处理**：大任务可以分段处理，避免超时
4. **成本控制**：避免重复消耗 token

**实现要点**：

```typescript
// 伪代码：使用 High Water Mark 的任务执行
async function executeTaskWithCheckpoint(task: Task): Promise<void> {
  // 1. 读取断点
  const hwm = await readHighWaterMark(task.id)
  const startFrom = hwm?.checkpoint || 0
  
  // 2. 从断点继续执行
  for (let i = startFrom; i < task.steps.length; i++) {
    await executeStep(task.steps[i])
    
    // 3. 每完成一步，更新断点
    await writeHighWaterMark(task.id, {
      progress: (i + 1) / task.steps.length * 100,
      checkpoint: i + 1,
      timestamp: Date.now()
    })
  }
  
  // 4. 完成后删除断点
  await deleteHighWaterMark(task.id)
}
```

**断点粒度选择**：

| 粒度 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **粗粒度**（每个阶段） | 开销小，性能好 | 恢复时重复工作多 | 快速任务（< 1 分钟） |
| **中粒度**（每 N 步） | 平衡性能和恢复 | 需要设计合理的步长 | 中等任务（1-10 分钟） |
| **细粒度**（每一步） | 恢复精确，浪费少 | 频繁 I/O，性能差 | 长时间任务（> 10 分钟） |

### 5.3 为什么需要阻塞关系？

**决策**：任务间可以声明依赖关系（`blockTask(A, B)` 表示 B 依赖 A）。

**理由**：

1. **依赖管理**：某些任务必须等待其他任务完成（如测试依赖代码实现）
2. **资源协调**：避免多个任务同时修改同一文件
3. **逻辑正确性**：确保任务按正确顺序执行

**实现要点**：

- 使用有向图表示阻塞关系
- 检测循环依赖，防止死锁
- 任务完成时自动解除对其他任务的阻塞

**循环依赖检测算法**：

```typescript
// 深度优先搜索检测环
function detectCycle(graph: BlockingGraph, start: TaskId): boolean {
  const visited = new Set<TaskId>()
  const recStack = new Set<TaskId>()
  
  function dfs(node: TaskId): boolean {
    visited.add(node)
    recStack.add(node)
    
    const neighbors = graph.getBlockedTasks(node)
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        if (dfs(neighbor)) return true
      } else if (recStack.has(neighbor)) {
        // 发现环
        return true
      }
    }
    
    recStack.delete(node)
    return false
  }
  
  return dfs(start)
}
```

### 5.4 三种 Spawn 模式的选择

| 模式 | 特点 | 适用场景 | 资源开销 |
|------|------|----------|----------|
| **InProcess** | 共享内存，低开销 | 轻量级任务，需要快速通信 | 低（共享进程） |
| **SplitPane** | 独立进程，UI 分屏 | 中等任务，用户需要监控进度 | 中（独立进程） |
| **SeparateWindow** | 完全隔离，独立窗口 | 重量级任务，长时间运行 | 高（独立进程 + UI） |

**决策逻辑**：

```typescript
function chooseSpawnMode(task: Task): SpawnMode {
  // 1. 估算任务复杂度
  const complexity = estimateComplexity(task)
  
  // 2. 根据复杂度选择模式
  if (complexity < 1000) {
    return 'InProcess'        // 简单任务
  } else if (complexity < 10000) {
    return 'SplitPane'        // 中等任务
  } else {
    return 'SeparateWindow'   // 复杂任务
  }
}

function estimateComplexity(task: Task): number {
  return (
    task.estimatedTokens +
    task.dependencies.length * 500 +
    task.steps.length * 100
  )
}
```

**InProcess 模式的优势**：

- 共享内存，通信零开销
- 启动快速（无需创建新进程）
- 资源占用小

**InProcess 模式的限制**：

- 无法真正隔离（崩溃会影响 Leader）
- 无法独立监控资源使用
- 不适合长时间运行的任务

### 5.5 为什么需要 Coordinator UI？

**决策**：提供统一的 UI 展示所有 Agent 状态。

**理由**：

1. **可观测性**：用户需要知道每个 Agent 在做什么
2. **调试能力**：出问题时可以快速定位是哪个 Agent
3. **资源监控**：查看 token 消耗、任务进度、错误信息
4. **手动干预**：用户可以终止失控的 Agent

**UI 设计**：

```
┌─────────────────────────────────────────────────────────┐
│ Team Status                                              │
├─────────────────────────────────────────────────────────┤
│ Leader: claude-opus-4 (Active)                          │
│   ├─ Current Task: Coordinating team                    │
│   └─ Token Usage: 12,450 / 200,000                      │
│                                                          │
│ Teammates:                                               │
│   ├─ [1] Tester (claude-sonnet-4) - Running             │
│   │   ├─ Task: Run integration tests                    │
│   │   ├─ Progress: 65% (13/20 tests)                    │
│   │   └─ Token Usage: 3,200                             │
│   │                                                      │
│   ├─ [2] Documenter (claude-sonnet-4) - Idle            │
│   │   └─ Last Task: Update API docs (Completed)         │
│   │                                                      │
│   └─ [3] Refactorer (claude-opus-4) - Blocked           │
│       ├─ Task: Refactor auth module                     │
│       └─ Blocked by: Task #5 (Tester)                   │
│                                                          │
│ Tasks: 3 active, 7 completed, 2 pending                 │
└─────────────────────────────────────────────────────────┘
```

**UI 更新机制**：

```typescript
// 实时更新 UI
class CoordinatorUI {
  private updateInterval: NodeJS.Timer
  
  start(): void {
    this.updateInterval = setInterval(async () => {
      const status = await getTeamStatus()
      this.render(status)
    }, 1000)  // 每秒更新
  }
  
  stop(): void {
    clearInterval(this.updateInterval)
  }
  
  private render(status: TeamStatus): void {
    // 使用 Ink 渲染终端 UI
    console.clear()
    console.log(this.formatStatus(status))
  }
}
```

### 5.6 消息传递 vs 共享状态

**决策**：Agent 间通过消息传递通信，而非共享状态。

**对比**：

| 方式 | 优点 | 缺点 |
|------|------|------|
| **消息传递** | 解耦、容错、可追踪 | 延迟高、需要序列化 |
| **共享状态** | 低延迟、零拷贝 | 耦合、竞态条件、难调试 |

**为什么选择消息传递**：

1. **解耦**：Agent 不需要知道彼此的内部状态
2. **容错**：消息可以持久化，Agent 崩溃后可以重放
3. **可追踪**：所有通信都有记录，便于调试
4. **分布式友好**：未来可以扩展到多机部署

**消息传递的性能优化**：

```typescript
// 批量发送消息
async function sendBatch(messages: Message[]): Promise<void> {
  const grouped = groupByRecipient(messages)
  
  await Promise.all(
    Array.from(grouped.entries()).map(([recipient, msgs]) =>
      writeBatchToMailbox(recipient, msgs)
    )
  )
}

// 消息压缩
async function compressMessage(message: Message): Promise<Buffer> {
  const json = JSON.stringify(message)
  return await gzip(json)
}
```

---

## 6. 参考实现

### 6.1 Claude Code 源码位置

| 功能 | 文件路径 | 关键函数 |
|------|----------|----------|
| Team 创建 | `tools/TeamCreateTool.ts` | `createTeam()` |
| 消息发送 | `tools/SendMessageTool.ts` | `sendMessage()` |
| Spawn 处理 | `agent/spawn.ts` | `handleSpawn()`, `handleSpawnInProcess()`, `handleSpawnSplitPane()`, `handleSpawnSeparateWindow()` |
| 模型选择 | `agent/teammate.ts` | `resolveTeammateModel()` |
| 任务系统 | `tasks/taskSystem.ts` | `claimTask()`, `unassignTeammateTasks()` |
| High Water Mark | `tasks/highWaterMark.ts` | `readHighWaterMark()`, `writeHighWaterMark()` |
| 阻塞关系 | `tasks/blocking.ts` | `blockTask()`, `unblockTask()` |
| Mailbox | `agent/teammateMailbox.ts` | `send()`, `receive()`, `poll()` |
| Coordinator UI | `ui/coordinatorAgentStatus.tsx` | `CoordinatorAgentStatus` 组件 |
| Swarm Worker | `agent/swarmWorkerHandler.ts` | `handleSwarmWorker()` |

### 6.2 关键函数签名

```typescript
// Team 创建
interface TeamCreateTool {
  execute(params: {
    taskListId: string
    maxTeammates?: number
    sharedContext?: string
  }): Promise<TeamId>
}

// Spawn 处理
interface SpawnHandler {
  handleSpawn(
    mode: SpawnMode,
    model?: ModelId,
    worktreeConfig?: WorktreeConfig
  ): Promise<TeammateId>
  
  handleSpawnInProcess(config: SpawnConfig): Promise<Teammate>
  handleSpawnSplitPane(config: SpawnConfig): Promise<Teammate>
  handleSpawnSeparateWindow(config: SpawnConfig): Promise<Teammate>
}

// 任务系统
interface TaskSystem {
  claimTask(taskId: TaskId, teammateId: TeammateId): Promise<boolean>
  unassignTeammateTasks(teammateId: TeammateId): Promise<void>
  blockTask(fromId: TaskId, toId: TaskId): Promise<void>
  unblockTask(fromId: TaskId, toId: TaskId): Promise<void>
}

// Mailbox
interface TeammateMailbox {
  send(message: Message): Promise<void>
  receive(timeout?: number): Promise<Message | null>
  poll(): Promise<Message[]>
  subscribe(filter: MessageFilter, handler: MessageHandler): Subscription
}
```

### 6.3 设计模式应用

| 模式 | 应用场景 | 实现位置 |
|------|----------|----------|
| **Leader-Follower** | Leader 协调多个 Teammate | `agent/spawn.ts` |
| **Producer-Consumer** | Mailbox 消息队列 | `agent/teammateMailbox.ts` |
| **Observer** | 任务状态变化通知 | `tasks/taskSystem.ts` |
| **Strategy** | 不同 Spawn 模式的选择 | `agent/spawn.ts` |
| **Memento** | High Water Mark 检查点 | `tasks/highWaterMark.ts` |
| **Facade** | Coordinator UI 统一接口 | `ui/coordinatorAgentStatus.tsx` |

---

## 7. 实现检查清单

### 7.1 必须实现的功能

**Team 管理**
- [ ] 创建团队（`createTeam`）
- [ ] 生成队友（`spawnTeammate`，至少支持 InProcess 模式）
- [ ] 终止队友（`terminateTeammate`）
- [ ] 获取团队状态（`getTeamStatus`）

**Task 系统**
- [ ] 创建任务（`createTask`）
- [ ] 认领任务（`claimTask`）
- [ ] 更新进度（`updateProgress`）
- [ ] 完成任务（`completeTask`）
- [ ] 任务失败处理（`failTask`）
- [ ] 文件系统持久化（JSON 格式）

**Mailbox**
- [ ] 发送消息（`send`）
- [ ] 接收消息（`receive`，支持阻塞和非阻塞）
- [ ] 轮询消息（`poll`）
- [ ] 基于文件系统的实现

**High Water Mark**
- [ ] 读取断点（`readHighWaterMark`）
- [ ] 写入断点（`writeHighWaterMark`）
- [ ] 删除断点（`deleteHighWaterMark`）

### 7.2 可选的优化

**高级 Task 功能**
- [ ] 阻塞关系管理（`blockTask`, `unblockTask`）
- [ ] 循环依赖检测
- [ ] 任务优先级队列
- [ ] 任务超时机制

**高级 Spawn 模式**
- [ ] SplitPane 模式（UI 分屏）
- [ ] SeparateWindow 模式（独立窗口）
- [ ] 队友模型自动选择（`resolveTeammateModel`）

**Worktree 隔离**
- [ ] 为队友创建 git worktree
- [ ] 符号链接共享目录
- [ ] 自动清理过期 worktree

**Mailbox 高级功能**
- [ ] 消息订阅（`subscribe`）
- [ ] 消息过滤（`MessageFilter`）
- [ ] 广播消息（`to: 'broadcast'`）
- [ ] 消息回复链（`replyTo`）

**可观测性**
- [ ] Coordinator UI（实时状态展示）
- [ ] 任务进度可视化
- [ ] Token 使用统计
- [ ] 错误日志收集

### 7.3 测试验证点

**单元测试**
- [ ] Task 状态机转换正确性
- [ ] Mailbox 消息顺序保证
- [ ] High Water Mark 读写一致性
- [ ] 阻塞关系图循环检测

**集成测试**
- [ ] Leader 创建 Teammate 并分配任务
- [ ] Teammate 执行任务并更新进度
- [ ] Teammate 通过 Mailbox 向 Leader 发送消息
- [ ] 任务失败后的恢复机制

**压力测试**
- [ ] 10+ 个并发 Teammate
- [ ] 100+ 个任务的调度
- [ ] 文件系统并发读写
- [ ] 长时间运行的稳定性

**边界情况**
- [ ] Teammate 崩溃后的任务恢复
- [ ] 文件系统满时的错误处理
- [ ] 循环依赖的检测和拒绝
- [ ] 消息队列满时的背压处理

---

## 8. 最佳实践

### 8.1 任务分解原则

**粒度控制**
- 单个任务的 token 消耗应在 1k-10k 之间
- 过小的任务增加协调开销
- 过大的任务难以恢复和监控

**依赖最小化**
- 尽量减少任务间的依赖关系
- 优先设计可并行的任务
- 必要的依赖通过 `blockTask` 显式声明

**上下文隔离**
- 每个任务应有清晰的输入和输出
- 避免隐式的全局状态依赖
- 通过 `context` 字段传递必要的上下文快照

**任务分解示例**：

```typescript
// ❌ 错误：任务过大，难以恢复
const badTask = {
  title: 'Implement entire feature',
  steps: [
    'Design API',
    'Implement backend',
    'Write tests',
    'Update docs',
    'Deploy to production'
  ]
}

// ✅ 正确：拆分为独立任务
const goodTasks = [
  {
    title: 'Design API',
    estimatedTokens: 2000,
    dependencies: []
  },
  {
    title: 'Implement backend',
    estimatedTokens: 5000,
    dependencies: ['design-api']
  },
  {
    title: 'Write tests',
    estimatedTokens: 3000,
    dependencies: ['implement-backend']
  },
  {
    title: 'Update docs',
    estimatedTokens: 1500,
    dependencies: ['implement-backend']
  }
]
```

### 8.2 Teammate 生命周期管理

**按需创建**
```typescript
// 不要预先创建所有 Teammate
// ❌ 错误做法
for (let i = 0; i < 10; i++) {
  await spawnTeammate('InProcess')
}

// ✅ 正确做法：按需创建
const task = await createTask(definition)
const teammate = await spawnTeammate('InProcess')
await claimTask(task.id, teammate.id)
```

**及时清理**
```typescript
// 任务完成后立即清理
await completeTask(task.id, result)
await terminateTeammate(teammate.id, true)  // cleanup=true
```

**资源限制**
```typescript
// 限制并发 Teammate 数量
const MAX_TEAMMATES = 5
if (activeTeammates.length >= MAX_TEAMMATES) {
  await waitForTeammateAvailable()
}
```

**生命周期监控**：

```typescript
class TeammateLifecycleManager {
  private teammates: Map<TeammateId, TeammateInfo> = new Map()
  
  async spawn(config: SpawnConfig): Promise<Teammate> {
    const teammate = await spawnTeammate(config.mode, config.model)
    
    this.teammates.set(teammate.id, {
      teammate,
      spawnedAt: Date.now(),
      lastHeartbeat: Date.now(),
      tasksCompleted: 0,
      tasksFailed: 0
    })
    
    // 启动心跳监控
    this.startHeartbeat(teammate.id)
    
    return teammate
  }
  
  private startHeartbeat(teammateId: TeammateId): void {
    const interval = setInterval(async () => {
      const info = this.teammates.get(teammateId)
      if (!info) {
        clearInterval(interval)
        return
      }
      
      // 检查是否超时
      const now = Date.now()
      if (now - info.lastHeartbeat > 30000) {
        console.warn(`Teammate ${teammateId} timeout, terminating...`)
        await this.terminate(teammateId)
        clearInterval(interval)
      }
    }, 10000)
  }
  
  async terminate(teammateId: TeammateId): Promise<void> {
    const info = this.teammates.get(teammateId)
    if (!info) return
    
    await terminateTeammate(teammateId, true)
    this.teammates.delete(teammateId)
  }
}
```

### 8.3 消息传递模式

**请求-响应模式**
```typescript
// Leader 发送问题
await mailbox.send({
  from: leaderId,
  to: teammateId,
  type: 'Question',
  payload: { question: 'Should we refactor this?' },
  timestamp: Date.now()
})

// Teammate 回复
await mailbox.send({
  from: teammateId,
  to: leaderId,
  type: 'Answer',
  payload: { answer: 'Yes, it has code smell' },
  replyTo: questionMessageId,
  timestamp: Date.now()
})
```

**进度报告模式**
```typescript
// Teammate 定期报告进度
setInterval(async () => {
  await mailbox.send({
    from: teammateId,
    to: leaderId,
    type: 'TaskUpdate',
    payload: {
      taskId: currentTask.id,
      progress: currentProgress,
      status: 'Running'
    },
    timestamp: Date.now()
  })
}, 5000)  // 每 5 秒报告一次
```

**广播模式**
```typescript
// Leader 广播通知所有 Teammate
await mailbox.send({
  from: leaderId,
  to: 'broadcast',
  type: 'ContextShare',
  payload: { newContext: updatedContext },
  timestamp: Date.now()
})
```

**消息优先级队列**：

```typescript
class PriorityMailbox extends Mailbox {
  private queues: Map<MessagePriority, Message[]> = new Map([
    ['urgent', []],
    ['high', []],
    ['normal', []],
    ['low', []]
  ])
  
  async send(message: Message, priority: MessagePriority = 'normal'): Promise<void> {
    const queue = this.queues.get(priority)!
    queue.push(message)
    await this.persist(message)
  }
  
  async receive(timeout?: number): Promise<Message | null> {
    // 按优先级顺序读取
    for (const priority of ['urgent', 'high', 'normal', 'low']) {
      const queue = this.queues.get(priority as MessagePriority)!
      if (queue.length > 0) {
        return queue.shift()!
      }
    }
    
    if (timeout) {
      return this.waitForMessage(timeout)
    }
    
    return null
  }
}
```

### 8.4 错误处理策略

**任务级重试**
```typescript
async function executeTaskWithRetry(
  task: Task,
  maxRetries: number = 3
): Promise<void> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await executeTask(task)
      await completeTask(task.id, result)
      return
    } catch (error) {
      if (attempt === maxRetries) {
        await failTask(task.id, error)
        throw error
      }
      
      // 指数退避
      await sleep(1000 * Math.pow(2, attempt))
    }
  }
}
```

**Teammate 级容错**
```typescript
// 监控 Teammate 健康状态
async function monitorTeammate(teammate: Teammate): Promise<void> {
  const healthCheck = setInterval(async () => {
    if (!await isTeammateAlive(teammate.id)) {
      clearInterval(healthCheck)
      
      // 重新分配任务
      const tasks = await getTeammateTasks(teammate.id)
      await unassignTeammateTasks(teammate.id)
      
      for (const task of tasks) {
        const newTeammate = await spawnTeammate('InProcess')
        await claimTask(task.id, newTeammate.id)
      }
    }
  }, 10000)  // 每 10 秒检查一次
}
```

**错误分类与处理**：

```typescript
enum ErrorSeverity {
  Recoverable = 'recoverable',      // 可重试
  Fatal = 'fatal',                  // 任务失败
  Critical = 'critical'             // 整个团队失败
}

function classifyError(error: Error): ErrorSeverity {
  if (error instanceof NetworkError) {
    return ErrorSeverity.Recoverable
  }
  
  if (error instanceof ValidationError) {
    return ErrorSeverity.Fatal
  }
  
  if (error instanceof OutOfMemoryError) {
    return ErrorSeverity.Critical
  }
  
  return ErrorSeverity.Fatal
}

async function handleTaskError(
  task: Task,
  error: Error
): Promise<void> {
  const severity = classifyError(error)
  
  switch (severity) {
    case ErrorSeverity.Recoverable:
      // 重试任务
      await retryTask(task)
      break
      
    case ErrorSeverity.Fatal:
      // 标记任务失败
      await failTask(task.id, error)
      break
      
    case ErrorSeverity.Critical:
      // 终止整个团队
      await terminateTeam(task.teamId)
      throw error
  }
}
```

### 8.5 性能优化

**批量操作**
```typescript
// 批量创建任务
const tasks = await Promise.all(
  definitions.map(def => createTask(def))
)

// 批量分配
await Promise.all(
  tasks.map((task, i) => claimTask(task.id, teammates[i].id))
)
```

**消息批处理**
```typescript
// 批量读取消息
const messages = await mailbox.poll()
for (const message of messages) {
  await handleMessage(message)
}
```

**缓存任务状态**
```typescript
// 避免频繁读取文件系统
class CachedTaskStore {
  private cache: Map<TaskId, Task> = new Map()
  private ttl: number = 5000  // 5 秒缓存
  
  async readTask(taskId: TaskId): Promise<Task> {
    const cached = this.cache.get(taskId)
    if (cached && Date.now() - cached.cachedAt < this.ttl) {
      return cached.task
    }
    
    const task = await this.store.readTask(taskId)
    this.cache.set(taskId, { task, cachedAt: Date.now() })
    return task
  }
  
  async writeTask(task: Task): Promise<void> {
    await this.store.writeTask(task)
    this.cache.set(task.id, { task, cachedAt: Date.now() })
  }
  
  invalidate(taskId: TaskId): void {
    this.cache.delete(taskId)
  }
}
```

**连接池模式**：

```typescript
class TeammatePool {
  private pool: Teammate[] = []
  private maxSize: number
  private minSize: number
  
  constructor(minSize: number = 2, maxSize: number = 10) {
    this.minSize = minSize
    this.maxSize = maxSize
  }
  
  async initialize(): Promise<void> {
    // 预创建最小数量的 Teammate
    for (let i = 0; i < this.minSize; i++) {
      const teammate = await spawnTeammate('InProcess')
      this.pool.push(teammate)
    }
  }
  
  async acquire(): Promise<Teammate> {
    // 从池中获取空闲 Teammate
    const idle = this.pool.find(t => t.status === 'Idle')
    if (idle) return idle
    
    // 池未满，创建新的
    if (this.pool.length < this.maxSize) {
      const teammate = await spawnTeammate('InProcess')
      this.pool.push(teammate)
      return teammate
    }
    
    // 等待空闲
    return this.waitForIdle()
  }
  
  release(teammate: Teammate): void {
    // 标记为空闲
    teammate.status = 'Idle'
  }
  
  async shutdown(): Promise<void> {
    await Promise.all(
      this.pool.map(t => terminateTeammate(t.id, true))
    )
    this.pool = []
  }
  
  private async waitForIdle(): Promise<Teammate> {
    return new Promise(resolve => {
      const interval = setInterval(() => {
        const idle = this.pool.find(t => t.status === 'Idle')
        if (idle) {
          clearInterval(interval)
          resolve(idle)
        }
      }, 100)
    })
  }
}
```

### 8.6 实战案例：重构大型代码库

**场景**：重构一个包含 100+ 文件的代码库。

**任务分解**：

```typescript
async function refactorCodebase(files: string[]): Promise<void> {
  // 1. 创建团队
  const team = await createTeam({
    taskListId: 'refactor-codebase',
    maxTeammates: 5,
    defaultModel: 'claude-opus-4'
  })
  
  // 2. 按模块分组文件
  const modules = groupFilesByModule(files)
  // modules = {
  //   'auth': ['auth/login.ts', 'auth/register.ts', ...],
  //   'api': ['api/users.ts', 'api/posts.ts', ...],
  //   ...
  // }
  
  // 3. 为每个模块创建任务
  const tasks: Task[] = []
  for (const [moduleName, moduleFiles] of Object.entries(modules)) {
    const task = await createTask({
      title: `Refactor ${moduleName} module`,
      description: `Refactor ${moduleFiles.length} files in ${moduleName}`,
      priority: calculatePriority(moduleName),
      estimatedTokens: moduleFiles.length * 500,
      context: {
        files: moduleFiles,
        refactoringRules: getRefactoringRules()
      }
    })
    tasks.push(task)
  }
  
  // 4. 设置依赖关系（核心模块优先）
  const coreModules = ['auth', 'database']
  const coreTasks = tasks.filter(t => 
    coreModules.some(m => t.title.includes(m))
  )
  const otherTasks = tasks.filter(t => !coreTasks.includes(t))
  
  for (const otherTask of otherTasks) {
    for (const coreTask of coreTasks) {
      await blockTask(otherTask.id, coreTask.id)
    }
  }
  
  // 5. 使用连接池执行
  const pool = new TeammatePool(3, 5)
  await pool.initialize()
  
  const results = await Promise.all(
    tasks.map(async task => {
      const teammate = await pool.acquire()
      try {
        await claimTask(task.id, teammate.id)
        const result = await executeRefactorTask(task, teammate)
        await completeTask(task.id, result)
        return result
      } finally {
        pool.release(teammate)
      }
    })
  )
  
  await pool.shutdown()
  
  // 6. 合并结果
  await mergeRefactoringResults(results)
}
```

**关键优化**：

1. **模块化分组**：按模块而非单个文件分组，减少任务数量
2. **依赖管理**：核心模块优先重构，避免后续冲突
3. **连接池**：复用 Teammate，减少创建开销
4. **并行执行**：独立模块并行重构，提升效率

---

## 9. 常见问题

### Q1: 如何处理 Teammate 之间的通信？

**A**: Teammate 之间不直接通信，所有消息都通过 Leader 中转。

```typescript
// Teammate A 想问 Teammate B 问题
// ❌ 错误：直接发送
await mailbox.send({ from: teammateA, to: teammateB, ... })

// ✅ 正确：通过 Leader
await mailbox.send({ 
  from: teammateA, 
  to: leaderId, 
  type: 'Question',
  payload: { 
    question: '...',
    targetTeammate: teammateB 
  }
})

// Leader 转发
await mailbox.send({ 
  from: leaderId, 
  to: teammateB, 
  type: 'Question',
  payload: { ... }
})
```

### Q2: 如何避免任务死锁？

**A**: 在添加阻塞关系时检测循环依赖。

```typescript
// BlockingGraph 的 hasCycle 方法会在 block() 时自动检测
try {
  await blockTask(taskA, taskB)
  await blockTask(taskB, taskC)
  await blockTask(taskC, taskA)  // 抛出错误：循环依赖
} catch (error) {
  console.error('Circular dependency detected')
}
```

### Q3: 如何限制 Teammate 数量？

**A**: 在 `TeamConfig` 中设置 `maxTeammates`。

```typescript
const team = await createTeam({
  taskListId: 'project-x',
  maxTeammates: 5,  // 最多 5 个 Teammate
  defaultModel: 'claude-sonnet-4'
})

// spawnTeammate 会检查限制
if (activeTeammates.length >= team.maxTeammates) {
  throw new Error('Max teammates reached')
}
```

### Q4: 如何在 Teammate 崩溃后恢复任务？

**A**: 使用 High Water Mark 从断点继续。

```typescript
// Teammate 崩溃前
await writeHighWaterMark(task.id, {
  progress: 50,
  checkpoint: { processedFiles: ['a.ts', 'b.ts'] },
  timestamp: Date.now()
})

// 新 Teammate 接手
const hwm = await readHighWaterMark(task.id)
if (hwm) {
  // 从断点继续
  const processedFiles = hwm.checkpoint.processedFiles
  const remainingFiles = allFiles.filter(f => !processedFiles.includes(f))
  await processFiles(remainingFiles)
}
```

### Q5: 如何调试多 Agent 系统？

**A**: 使用 Coordinator UI 和日志。

```typescript
// 启用详细日志
const team = await createTeam({
  taskListId: 'debug-session',
  debug: true  // 启用调试模式
})

// 查看实时状态
const status = await getTeamStatus()
console.log(status)

// 查看任务文件
// ~/.claude/tasks/{taskListId}/{taskId}.json
```

---

## 10. 总结

多 Agent 编排系统的核心设计原则：

1. **任务所有权明确**：每个任务有唯一的所有者，通过文件系统持久化
2. **消息驱动协作**：Agent 间通过异步消息传递通信，解耦执行流程
3. **容错优先**：High Water Mark 支持任务恢复，阻塞关系防止死锁
4. **简单可靠**：基于文件系统实现，零外部依赖，可审计可修复
5. **渐进式复杂度**：从 InProcess 到 SplitPane 到 SeparateWindow，按需选择隔离级别

这套架构在 Claude Code 中经过大规模验证，支持复杂的多 Agent 协作场景，同时保持了实现的简洁性和可维护性。

**关键洞察**：多 Agent 系统的核心不是通信协议，而是**任务所有权和状态同步**。Claude Code 用文件系统（tasks 目录 + high water mark）来实现这一点，简单但可靠。

---

**相关文档**：
- [01-OVERVIEW.md](01-OVERVIEW.md) - Agent 运行时核心概念
- [02-AGENT-LOOP.md](02-AGENT-LOOP.md) - Agent 主循环设计
- [03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md) - 工具系统架构
- [05-HOOK-SYSTEM.md](05-HOOK-SYSTEM.md) - Hook 扩展机制
- [06-PERMISSION.md](06-PERMISSION.md) - 权限系统设计

