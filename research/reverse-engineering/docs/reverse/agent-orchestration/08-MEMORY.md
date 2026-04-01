# 记忆系统：Agent 的长期记忆工程

## 1. 核心概念

### 1.1 什么是 Agent 记忆系统

Agent 记忆系统是让 AI 能够跨会话保持知识和经验的基础设施。与人类记忆类似，Agent 需要：

- **短期记忆**：当前会话中的上下文和状态
- **长期记忆**：跨会话持久化的知识和经验
- **工作记忆**：正在处理的任务相关信息

### 1.2 设计动机

**为什么需要记忆系统？**

1. **上下文窗口有限**：即使 200k token 也不够存储所有历史信息
2. **知识复用**：避免重复学习相同的项目规范和用户偏好
3. **持续改进**：从过去的交互中学习，优化未来的行为
4. **用户体验**：让 Agent 表现得"记得"用户和项目

**核心挑战**：

- 什么值得记住？（提取策略）
- 如何避免记忆污染？（去重和验证）
- 如何高效检索？（索引和搜索）
- 如何保证安全？（权限和隔离）

### 1.3 关键术语

| 术语 | 定义 |
|------|------|
| **会话记忆** | 当前对话中的临时记忆，会话结束后可选择性持久化 |
| **显式记忆** | 用户主动写入的记忆（如 CLAUDE.md） |
| **自动记忆** | 系统后台自动提取的关键信息 |
| **MagicDocs** | 自动检测和更新的项目文档 |
| **记忆提取** | 从对话中识别和提取值得保存的信息 |
| **记忆去重** | 避免重复写入相同或相似的记忆 |

---

## 2. 架构设计

### 2.1 三层记忆架构

```
┌─────────────────────────────────────────────────────────┐
│                    Agent 记忆系统                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  第一层：会话记忆 (Session Memory)               │   │
│  │  ─────────────────────────────────────────────   │   │
│  │  • 文件：sessionMemory.ts                        │   │
│  │  • 机制：自动提取 + 文件持久化                    │   │
│  │  • 触发：shouldExtractMemory() 决定是否提取      │   │
│  │  • 生命周期：会话内有效，结束后可选择性保存       │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  第二层：显式记忆 (Explicit Memory)              │   │
│  │  ─────────────────────────────────────────────   │   │
│  │  • 文件：memory.tsx                              │   │
│  │  • 机制：用户主动写入 CLAUDE.md                  │   │
│  │  • 触发：通过 MemoryCommand 交互                 │   │
│  │  • 特点：用户完全控制，高优先级                  │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  第三层：自动记忆 (Auto Memory)                  │   │
│  │  ─────────────────────────────────────────────   │   │
│  │  • 文件：extractMemories.ts                      │   │
│  │  • 机制：后台自动提取关键信息                    │   │
│  │  • 触发：runExtraction() + drainPendingExtraction()│ │
│  │  • 特点：非阻塞，有去重和安全限制                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 记忆提取流程

```
用户消息 → Agent 响应 → 记忆提取判断
                              ↓
                    shouldExtractMemory()?
                    /                    \
                  NO                     YES
                  ↓                       ↓
              跳过提取              检查去重条件
                                         ↓
                              hasMemoryWritesSince()?
                              /                    \
                            YES                    NO
                            ↓                       ↓
                        跳过（已有记忆）      执行提取
                                                    ↓
                                          创建受限记忆工具
                                                    ↓
                                          调用 LLM 提取
                                                    ↓
                                          安全检查（denyAutoMemTool）
                                                    ↓
                                          写入记忆文件
                                                    ↓
                                          后台排队（drainPendingExtraction）
```

### 2.3 MagicDocs 自文档化流程

```
文件变更事件
    ↓
detectMagicDocHeader(content)
    ↓
检测到特定文件头？
    /            \
  NO             YES
  ↓               ↓
跳过          registerMagicDoc(filePath)
                  ↓
            获取文档上下文
                  ↓
            getMagicDocsAgent()
                  ↓
            updateMagicDoc(docInfo, context)
                  ↓
            自动更新文档内容
```

---

## 3. 接口契约

### 3.1 会话记忆接口

```typescript
// sessionMemory.ts

interface SessionMemory {
  // 判断是否应该提取记忆
  shouldExtractMemory(messages: Message[]): boolean
  
  // 提取会话记忆
  extractSessionMemory(
    messages: Message[],
    context: SessionContext
  ): Promise<MemoryEntry[]>
  
  // 持久化会话记忆
  persistSessionMemory(
    entries: MemoryEntry[],
    targetPath: string
  ): Promise<void>
}

interface MemoryEntry {
  content: string        // 记忆内容
  timestamp: number      // 时间戳
  source: string         // 来源（会话ID）
  confidence: number     // 置信度 0-1
  tags: string[]         // 标签
}
```

### 3.2 自动记忆提取接口

```typescript
// extractMemories.ts

interface MemoryExtractor {
  // 计数模型可见消息
  countModelVisibleMessagesSince(
    messages: Message[],
    since: number
  ): number
  
  // 检查是否已有记忆写入
  hasMemoryWritesSince(
    messages: Message[],
    since: number
  ): boolean
  
  // 拒绝不当记忆写入
  denyAutoMemTool(
    tool: ToolCall,
    reason: string
  ): ToolDenyResult
  
  // 创建带限制的记忆工具
  createAutoMemCanUseTool(
    memoryDir: string
  ): CanUseToolFunction
  
  // 提取写入路径
  extractWrittenPaths(
    agentMessages: Message[]
  ): string[]
  
  // 排空待处理提取（非阻塞）
  drainPendingExtraction(
    timeoutMs: number
  ): Promise<void>
}

type CanUseToolFunction = (
  tool: ToolCall,
  context: ToolContext
) => boolean | DenyReason
```

### 3.3 MagicDocs 接口

```typescript
// magicDocs.ts

interface MagicDocsSystem {
  // 检测文档头（自动识别）
  detectMagicDocHeader(content: string): MagicDocHeader | null
  
  // 注册文档
  registerMagicDoc(filePath: string): void
  
  // 获取 MagicDocs Agent
  getMagicDocsAgent(): Agent
  
  // 更新文档
  updateMagicDoc(
    docInfo: MagicDocInfo,
    context: UpdateContext
  ): Promise<void>
}

interface MagicDocHeader {
  type: string           // 文档类型
  version: string        // 版本
  autoUpdate: boolean    // 是否自动更新
  updateTriggers: string[] // 更新触发条件
}

interface MagicDocInfo {
  filePath: string
  header: MagicDocHeader
  lastUpdate: number
  dependencies: string[] // 依赖的文件
}
```

---

## 4. 实现要点

### 4.1 记忆提取触发策略

**核心算法**：

```typescript
function shouldExtractMemory(messages: Message[]): boolean {
  // 1. 检查消息数量阈值
  const visibleCount = countModelVisibleMessagesSince(messages, lastExtraction)
  if (visibleCount < MIN_MESSAGES_FOR_EXTRACTION) {
    return false
  }
  
  // 2. 检查是否已有记忆写入（去重）
  if (hasMemoryWritesSince(messages, lastExtraction)) {
    return false
  }
  
  // 3. 检查时间间隔
  const timeSinceLastExtraction = Date.now() - lastExtraction
  if (timeSinceLastExtraction < MIN_EXTRACTION_INTERVAL) {
    return false
  }
  
  // 4. 检查内容质量（启发式）
  const hasSignificantContent = messages.some(msg => 
    msg.role === 'assistant' && 
    msg.content.length > MIN_CONTENT_LENGTH &&
    containsActionableInfo(msg.content)
  )
  
  return hasSignificantContent
}
```

**设计要点**：

1. **不是每轮都提取**：避免记忆膨胀和性能开销
2. **去重机制**：`hasMemoryWritesSince` 避免重复写入
3. **质量过滤**：只提取有价值的信息
4. **时间控制**：限制提取频率

### 4.2 记忆去重策略

**去重层次**：

```typescript
// 第一层：路径去重
function hasMemoryWritesSince(messages: Message[], since: number): boolean {
  const writtenPaths = extractWrittenPaths(messages.filter(m => m.timestamp > since))
  return writtenPaths.some(path => isMemoryFile(path))
}

// 第二层：内容去重（语义相似度）
function isDuplicateMemory(newEntry: MemoryEntry, existing: MemoryEntry[]): boolean {
  return existing.some(entry => {
    const similarity = computeSemanticSimilarity(newEntry.content, entry.content)
    return similarity > DUPLICATE_THRESHOLD
  })
}

// 第三层：时间窗口去重
function isRecentlyWritten(topic: string, timeWindow: number): boolean {
  const recentMemories = getMemoriesInWindow(Date.now() - timeWindow)
  return recentMemories.some(m => m.tags.includes(topic))
}
```

### 4.3 安全限制机制

**记忆工具的安全限制**：

```typescript
function createAutoMemCanUseTool(memoryDir: string): CanUseToolFunction {
  return (tool: ToolCall, context: ToolContext) => {
    // 1. 只允许写入指定目录
    if (tool.name === 'write' || tool.name === 'edit') {
      const targetPath = tool.parameters.file_path
      if (!targetPath.startsWith(memoryDir)) {
        return denyAutoMemTool(tool, 'Path outside memory directory')
      }
    }
    
    // 2. 禁止删除操作
    if (tool.name === 'delete' || tool.name === 'bash' && tool.parameters.command.includes('rm')) {
      return denyAutoMemTool(tool, 'Delete operations not allowed in auto memory')
    }
    
    // 3. 禁止执行命令
    if (tool.name === 'bash') {
      return denyAutoMemTool(tool, 'Command execution not allowed in auto memory')
    }
    
    // 4. 文件大小限制
    if (tool.name === 'write') {
      const content = tool.parameters.content
      if (content.length > MAX_MEMORY_SIZE) {
        return denyAutoMemTool(tool, 'Memory content too large')
      }
    }
    
    return true
  }
}
```

### 4.4 后台排队机制

**非阻塞提取**：

```typescript
// 提取队列
const extractionQueue: Array<{
  messages: Message[]
  context: SessionContext
  resolve: (result: MemoryEntry[]) => void
  reject: (error: Error) => void
}> = []

// 异步提取
async function runExtraction(messages: Message[], context: SessionContext): Promise<void> {
  return new Promise((resolve, reject) => {
    extractionQueue.push({ messages, context, resolve, reject })
    // 不等待，立即返回
  })
}

// 排空队列（在空闲时或会话结束时）
async function drainPendingExtraction(timeoutMs: number): Promise<void> {
  const startTime = Date.now()
  
  while (extractionQueue.length > 0 && Date.now() - startTime < timeoutMs) {
    const task = extractionQueue.shift()
    if (!task) break
    
    try {
      const result = await extractMemoriesInternal(task.messages, task.context)
      task.resolve(result)
    } catch (error) {
      task.reject(error)
    }
  }
  
  // 超时后剩余任务丢弃或持久化到磁盘
  if (extractionQueue.length > 0) {
    await persistPendingExtractions(extractionQueue)
  }
}
```

### 4.5 MagicDocs 文档头检测

**自动识别机制**：

```typescript
function detectMagicDocHeader(content: string): MagicDocHeader | null {
  // 检测特定格式的文档头
  const headerPattern = /^---\s*\nmagic-doc:\s*true\s*\ntype:\s*(\w+)\s*\nversion:\s*([\d.]+)\s*\nauto-update:\s*(true|false)\s*\n---/m
  
  const match = content.match(headerPattern)
  if (!match) return null
  
  return {
    type: match[1],
    version: match[2],
    autoUpdate: match[3] === 'true',
    updateTriggers: extractUpdateTriggers(content)
  }
}

// 示例文档头
/*
---
magic-doc: true
type: api-reference
version: 1.0.0
auto-update: true
update-triggers:
  - src/api/**/*.ts
  - src/types/**/*.ts
---

# API Reference

This document is automatically maintained by MagicDocs.
*/
```

---

## 5. 设计决策

### 5.1 为什么三层架构？

**权衡**：

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 单层记忆 | 简单 | 无法区分临时和永久记忆 | ❌ |
| 两层记忆 | 较简单 | 缺少自动化层 | ❌ |
| 三层记忆 | 灵活、可控 | 复杂度较高 | ✅ |

**选择三层的原因**：

1. **会话记忆**：处理临时信息，避免污染长期记忆
2. **显式记忆**：用户完全控制，高优先级
3. **自动记忆**：减少用户负担，自动积累知识

### 5.2 为什么不是每轮都提取？

**成本分析**：

- 每次提取需要额外的 LLM 调用（成本）
- 大部分对话不包含值得记忆的信息（噪音）
- 频繁提取会导致记忆膨胀（存储和检索成本）

**解决方案**：

- 设置提取阈值（消息数量、时间间隔）
- 启发式判断内容质量
- 去重机制避免重复

### 5.3 为什么用文件系统而不是数据库？

**对比**：

| 存储方式 | 优点 | 缺点 |
|----------|------|------|
| 数据库 | 查询快、事务支持 | 需要额外服务、不透明 |
| 文件系统 | 透明、可版本控制、无依赖 | 查询慢、无事务 |

**选择文件系统的原因**：

1. **透明性**：用户可以直接查看和编辑记忆文件
2. **版本控制**：天然支持 git 管理
3. **无依赖**：不需要额外的数据库服务
4. **Agent 友好**：Agent 本身就有文件系统访问权限

### 5.4 MagicDocs vs 手动文档

**为什么需要自动文档化？**

- 文档容易过时（手动维护成本高）
- 代码和文档不同步（一致性问题）
- 重复劳动（每次变更都要更新文档）

**MagicDocs 的优势**：

- 自动检测需要更新的文档
- 基于代码变更自动更新
- 保持文档和代码同步

**限制**：

- 只适用于结构化文档（API 参考、配置说明等）
- 不适用于概念性文档（需要人类创意）

---

## 6. 参考实现

### 6.1 Claude Code 源码位置

```
src/
├── sessionMemory.ts          # 会话记忆
├── memory.tsx                # 显式记忆（UI 组件）
├── extractMemories.ts        # 自动记忆提取
├── magicDocs.ts              # MagicDocs 系统
└── memoryCommand.ts          # 记忆命令处理
```

### 6.2 关键函数签名

```typescript
// sessionMemory.ts
export function shouldExtractMemory(messages: Message[]): boolean
export function extractSessionMemory(messages: Message[], context: SessionContext): Promise<MemoryEntry[]>

// extractMemories.ts
export function countModelVisibleMessagesSince(messages: Message[], since: number): number
export function hasMemoryWritesSince(messages: Message[], since: number): boolean
export function denyAutoMemTool(tool: ToolCall, reason: string): ToolDenyResult
export function createAutoMemCanUseTool(memoryDir: string): CanUseToolFunction
export function extractWrittenPaths(agentMessages: Message[]): string[]
export function drainPendingExtraction(timeoutMs: number): Promise<void>

// magicDocs.ts
export function detectMagicDocHeader(content: string): MagicDocHeader | null
export function registerMagicDoc(filePath: string): void
export function getMagicDocsAgent(): Agent
export function updateMagicDoc(docInfo: MagicDocInfo, context: UpdateContext): Promise<void>
```

### 6.3 设计模式应用

**1. 策略模式**（记忆提取策略）

```typescript
interface ExtractionStrategy {
  shouldExtract(messages: Message[]): boolean
  extract(messages: Message[]): Promise<MemoryEntry[]>
}

class ThresholdStrategy implements ExtractionStrategy {
  shouldExtract(messages: Message[]): boolean {
    return messages.length >= this.threshold
  }
}

class QualityStrategy implements ExtractionStrategy {
  shouldExtract(messages: Message[]): boolean {
    return messages.some(m => this.hasHighQualityContent(m))
  }
}
```

**2. 观察者模式**（MagicDocs 文件监听）

```typescript
class FileWatcher {
  private observers: Array<(path: string) => void> = []
  
  subscribe(callback: (path: string) => void): void {
    this.observers.push(callback)
  }
  
  notify(path: string): void {
    this.observers.forEach(cb => cb(path))
  }
}

// MagicDocs 订阅文件变更
fileWatcher.subscribe(async (path) => {
  const content = await readFile(path)
  const header = detectMagicDocHeader(content)
  if (header) {
    await updateMagicDoc({ filePath: path, header }, context)
  }
})
```

**3. 责任链模式**（安全检查）

```typescript
type SecurityCheck = (tool: ToolCall) => boolean | DenyReason

const securityChain: SecurityCheck[] = [
  checkPathRestriction,
  checkOperationWhitelist,
  checkSizeLimit,
  checkRateLimit
]

function canUseTool(tool: ToolCall): boolean | DenyReason {
  for (const check of securityChain) {
    const result = check(tool)
    if (result !== true) return result
  }
  return true
}
```

---

## 7. 实现检查清单

### 7.1 必须实现的功能

**会话记忆**：
- [ ] `shouldExtractMemory()` 提取判断逻辑
- [ ] 消息计数和时间窗口检查
- [ ] 会话记忆持久化到文件

**自动记忆**：
- [ ] `hasMemoryWritesSince()` 去重检查
- [ ] `createAutoMemCanUseTool()` 安全限制
- [ ] `drainPendingExtraction()` 后台排队
- [ ] 记忆提取的 LLM 调用

**MagicDocs**：
- [ ] `detectMagicDocHeader()` 文档头检测
- [ ] 文件变更监听
- [ ] 自动文档更新

**安全机制**：
- [ ] 路径限制（只能写入记忆目录）
- [ ] 操作白名单（禁止删除和执行）
- [ ] 大小限制（防止记忆膨胀）

### 7.2 可选的优化

**性能优化**：
- [ ] 记忆索引（加速检索）
- [ ] 语义去重（使用 embedding）
- [ ] 增量更新（只更新变更部分）

**用户体验**：
- [ ] 记忆可视化（UI 展示）
- [ ] 记忆搜索（全文搜索）
- [ ] 记忆导出（备份和迁移）

**高级特性**：
- [ ] 记忆优先级（重要性评分）
- [ ] 记忆过期（自动清理旧记忆）
- [ ] 记忆压缩（摘要和归档）
- [ ] 跨项目记忆共享

### 7.3 测试验证点

**功能测试**：
- [ ] 会话记忆能正确提取和持久化
- [ ] 去重机制能避免重复写入
- [ ] 安全限制能阻止不当操作
- [ ] MagicDocs 能自动检测和更新文档

**边界测试**：
- [ ] 空消息列表不触发提取
- [ ] 超大记忆内容被拒绝
- [ ] 路径遍历攻击被阻止
- [ ] 并发提取不冲突

**性能测试**：
- [ ] 提取不阻塞主循环
- [ ] 队列排空在合理时间内完成
- [ ] 记忆文件大小在可控范围

**集成测试**：
- [ ] 记忆在下次会话中可用
- [ ] MagicDocs 与文件监听集成正常
- [ ] 记忆系统与其他子系统协同工作

---

## 8. 最佳实践

### 8.1 记忆内容设计

**好的记忆**：

```markdown
# 项目规范

## 代码风格
- 使用 TypeScript strict 模式
- 函数命名采用 camelCase
- 接口命名以 I 开头

## 测试要求
- 单元测试覆盖率 > 80%
- 集成测试覆盖核心流程
```

**不好的记忆**：

```markdown
# 记录

今天用户说要用 TypeScript，然后我们讨论了代码风格，
用户提到了一些规范，还说了测试的事情...
```

**原则**：

1. **结构化**：使用标题、列表、表格
2. **具体**：避免模糊的描述
3. **可执行**：能直接指导行动
4. **简洁**：去除冗余信息

### 8.2 提取时机选择

**合适的提取时机**：

- 用户明确表达偏好或规范
- 完成重要任务后的总结
- 发现新的项目约定
- 解决复杂问题后的经验

**不合适的提取时机**：

- 简单的问答对话
- 临时的调试信息
- 重复的常识性内容
- 未经验证的假设

### 8.3 MagicDocs 使用场景

**适合 MagicDocs**：

- API 参考文档（从代码生成）
- 配置文件说明（从 schema 生成）
- 命令行帮助（从参数定义生成）
- 变更日志（从 git 提交生成）

**不适合 MagicDocs**：

- 概念性教程（需要人类创意）
- 设计决策文档（需要深度思考）
- 用户故事（需要业务理解）
- 营销文案（需要情感表达）

---

## 9. 扩展阅读

### 9.1 相关文档

- [04-CONTEXT-ENGINE.md](04-CONTEXT-ENGINE.md) - 上下文管理与记忆系统的关系
- [05-HOOK-SYSTEM.md](05-HOOK-SYSTEM.md) - 使用 Hook 触发记忆提取
- [11-PLUGIN-SKILL.md](11-PLUGIN-SKILL.md) - 通过 Plugin 扩展记忆系统

### 9.2 设计哲学

**文件系统是 Agent 最好的数据库**：

Claude Code 的记忆系统完全基于文件系统，不使用任何数据库。原因：

1. **用户可以手动检查和修复**：记忆文件是纯文本，用户可以直接编辑
2. **天然支持版本控制**：记忆文件可以用 git 管理
3. **不需要额外的服务依赖**：无需安装和维护数据库
4. **Agent 本身就有文件系统的访问权限**：无需额外的权限管理

这个设计决策体现了 Claude Code 的核心理念：**让 AI 系统透明、可控、易于理解**。

---

**下一步**：阅读 [09-SECURITY.md](09-SECURITY.md) 了解记忆系统的安全防护机制。
