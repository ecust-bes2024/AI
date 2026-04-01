# 10. Speculation 预执行优化系统

## 1. 核心概念

### 1.1 什么是 Speculation

**Speculation（预执行）** 是 Claude Code 中最具创新性的性能优化机制之一。其核心思想是：**在用户确认之前，提前在隔离环境中执行 LLM 建议的操作，如果用户接受建议，则直接应用预执行结果，节省等待时间**。

### 1.2 设计动机

在传统的 Agent 交互流程中：

```
LLM 生成建议 → 用户确认 → 执行工具 → 返回结果
                  ↑
              等待时间（人类决策）
```

问题：用户确认后，还需要等待工具执行（文件操作、网络请求等），体验不流畅。

Speculation 的优化：

```
LLM 生成建议 → startSpeculation() 在 Overlay FS 中预执行
                  ↓
              用户确认（同时预执行已完成）
                  ↓
              copyOverlayToMain() 原子合并（毫秒级）
```

**时间节省** = 工具执行时间 - 用户决策时间（如果预执行先完成）

### 1.3 关键术语

| 术语 | 定义 |
|------|------|
| **Overlay FS** | 临时文件系统层，所有预执行操作在此进行，不影响主文件系统 |
| **Speculation Session** | 一次预执行会话，包含预执行的工具调用和结果 |
| **Atomic Merge** | 原子合并操作，将 Overlay FS 的变更一次性应用到主文件系统 |
| **Deny Speculation** | 拒绝预执行结果，清理 Overlay FS，不影响主系统 |
| **Time Saved** | 预执行节省的时间（毫秒），用于反馈和遥测 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Speculation Engine                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │ Speculation  │      │  Overlay FS  │      │  Atomic   │ │
│  │   Trigger    │─────▶│   Manager    │─────▶│  Merger   │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │       │
│         │                      │                     │       │
│         ▼                      ▼                     ▼       │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Tool       │      │  Isolation   │      │ Feedback  │ │
│  │  Executor    │      │   Layer      │      │ Generator │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
用户输入建议
    ↓
startSpeculation()
    ↓
创建 Overlay 目录（临时隔离环境）
    ↓
在 Overlay FS 中执行工具调用
    ↓
记录执行结果和时间戳
    ↓
等待用户决策
    ↓
┌─────────────┬─────────────┐
│  用户接受   │  用户拒绝   │
└─────────────┴─────────────┘
      ↓              ↓
copyOverlayToMain() denySpeculation()
      ↓              ↓
原子合并到主系统    清理 Overlay FS
      ↓              ↓
生成 SpeculationFeedbackMessage
      ↓
显示时间节省统计
```

### 2.3 状态机

```
┌─────────┐
│  IDLE   │ 初始状态，无预执行
└────┬────┘
     │ startSpeculation()
     ▼
┌─────────┐
│ RUNNING │ 预执行进行中
└────┬────┘
     │ 预执行完成
     ▼
┌─────────┐
│ PENDING │ 等待用户决策
└────┬────┘
     │
     ├─────────────┬─────────────┐
     │ accept      │ deny        │
     ▼             ▼             │
┌─────────┐  ┌─────────┐        │
│ACCEPTED │  │ DENIED  │        │
└────┬────┘  └────┬────┘        │
     │            │              │
     │ merge      │ cleanup      │
     ▼            ▼              │
┌─────────┐  ┌─────────┐        │
│COMPLETED│  │ CLEANED │        │
└────┬────┘  └────┬────┘        │
     │            │              │
     └────────────┴──────────────┘
                  ↓
              回到 IDLE
```


---

## 3. 接口契约

### 3.1 核心接口定义

```typescript
interface SpeculationEngine {
  // 启动预执行
  startSpeculation(
    suggestion: ToolCall[],
    context: ExecutionContext
  ): Promise<SpeculationSession>;
  
  // 接受预执行结果
  acceptSpeculation(
    sessionId: string
  ): Promise<SpeculationResult>;
  
  // 拒绝预执行结果
  denySpeculation(
    sessionId: string
  ): Promise<void>;
  
  // 获取预执行状态
  getSpeculationStatus(
    sessionId: string
  ): SpeculationStatus;
}

interface SpeculationSession {
  id: string;
  overlayPath: string;        // Overlay FS 路径
  startTime: number;           // 开始时间戳
  toolCalls: ToolCall[];       // 预执行的工具调用
  status: SpeculationStatus;
}

interface SpeculationResult {
  success: boolean;
  timeSavedMs: number;         // 节省的时间（毫秒）
  sessionTotalMs: number;      // 会话累计节省时间
  toolResults: ToolResult[];   // 工具执行结果
  mergedFiles: string[];       // 合并的文件列表
}

enum SpeculationStatus {
  IDLE = 'idle',
  RUNNING = 'running',
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  DENIED = 'denied',
  COMPLETED = 'completed',
  CLEANED = 'cleaned',
  FAILED = 'failed'
}
```

### 3.2 Overlay FS 管理接口

```typescript
interface OverlayFSManager {
  // 创建 Overlay 目录
  createOverlay(sessionId: string): Promise<string>;
  
  // 在 Overlay 中执行工具
  executeInOverlay(
    overlayPath: string,
    toolCall: ToolCall
  ): Promise<ToolResult>;
  
  // 原子合并到主文件系统
  copyOverlayToMain(
    overlayPath: string,
    mainPath: string
  ): Promise<MergeResult>;
  
  // 安全清理 Overlay
  safeRemoveOverlay(overlayPath: string): Promise<void>;
  
  // 获取 Overlay 变更列表
  getOverlayChanges(overlayPath: string): Promise<FileChange[]>;
}

interface MergeResult {
  success: boolean;
  filesChanged: number;
  bytesWritten: number;
  conflicts: FileConflict[];
}

interface FileChange {
  path: string;
  type: 'created' | 'modified' | 'deleted';
  size: number;
}
```

### 3.3 反馈消息接口

```typescript
interface SpeculationFeedbackMessage {
  type: 'speculation_feedback';
  accepted: boolean;
  timeSavedMs: number;
  sessionTotalMs: number;
  toolCount: number;
  message: string;  // 用户可见的反馈文本
}

function createSpeculationFeedbackMessage(
  result: SpeculationResult,
  accepted: boolean
): SpeculationFeedbackMessage {
  return {
    type: 'speculation_feedback',
    accepted,
    timeSavedMs: result.timeSavedMs,
    sessionTotalMs: result.sessionTotalMs,
    toolCount: result.toolResults.length,
    message: accepted 
      ? `✓ Applied changes instantly (saved ${result.timeSavedMs}ms)`
      : `✗ Discarded speculative execution`
  };
}
```

---

## 4. 实现要点

### 4.1 Overlay FS 实现策略

**方案 1：临时目录 + 文件复制（Claude Code 采用）**

```typescript
class OverlayFSManager {
  async createOverlay(sessionId: string): Promise<string> {
    // 在系统临时目录创建隔离环境
    const overlayPath = path.join(
      os.tmpdir(), 
      `speculation-${sessionId}`
    );
    await fs.mkdir(overlayPath, { recursive: true });
    
    // 复制工作目录到 Overlay（可选，按需复制）
    // await this.copyWorkspaceToOverlay(overlayPath);
    
    return overlayPath;
  }
  
  async executeInOverlay(
    overlayPath: string,
    toolCall: ToolCall
  ): Promise<ToolResult> {
    // 重定向工具的文件操作到 Overlay
    const originalCwd = process.cwd();
    process.chdir(overlayPath);
    
    try {
      const result = await this.toolExecutor.execute(toolCall);
      return result;
    } finally {
      process.chdir(originalCwd);
    }
  }
  
  async copyOverlayToMain(
    overlayPath: string,
    mainPath: string
  ): Promise<MergeResult> {
    const changes = await this.getOverlayChanges(overlayPath);
    const conflicts: FileConflict[] = [];
    
    for (const change of changes) {
      const overlayFile = path.join(overlayPath, change.path);
      const mainFile = path.join(mainPath, change.path);
      
      // 检测冲突：主文件在预执行期间被修改
      if (await this.hasConflict(mainFile, change)) {
        conflicts.push({ path: change.path, reason: 'modified' });
        continue;
      }
      
      // 原子复制
      if (change.type === 'created' || change.type === 'modified') {
        await fs.copyFile(overlayFile, mainFile);
      } else if (change.type === 'deleted') {
        await fs.unlink(mainFile);
      }
    }
    
    return {
      success: conflicts.length === 0,
      filesChanged: changes.length,
      bytesWritten: changes.reduce((sum, c) => sum + c.size, 0),
      conflicts
    };
  }
}
```

**方案 2：Union FS（高级，需要系统支持）**

```bash
# Linux: OverlayFS
mount -t overlay overlay \
  -o lowerdir=/workspace,upperdir=/tmp/overlay,workdir=/tmp/work \
  /tmp/speculation

# macOS: 无原生支持，需要 FUSE
```

### 4.2 时间节省计量算法

```typescript
class SpeculationTimer {
  private startTime: number;
  private userDecisionTime: number;
  private executionEndTime: number;
  
  startSpeculation(): void {
    this.startTime = Date.now();
  }
  
  recordUserDecision(): void {
    this.userDecisionTime = Date.now();
  }
  
  recordExecutionEnd(): void {
    this.executionEndTime = Date.now();
  }
  
  calculateTimeSaved(): number {
    // 预执行时间
    const speculationDuration = this.executionEndTime - this.startTime;
    
    // 用户决策时间
    const userThinkTime = this.userDecisionTime - this.startTime;
    
    // 节省时间 = 预执行时间 - 用户决策时间
    // 如果预执行更快完成，则节省了等待时间
    const timeSaved = Math.max(0, speculationDuration - userThinkTime);
    
    return timeSaved;
  }
}
```

**关键洞察**：
- 如果用户决策时间 > 预执行时间，则完全节省了执行等待
- 如果用户决策时间 < 预执行时间，则部分节省
- 累计统计 `sessionTotalMs` 用于展示整体效果


### 4.3 失败安全设计

```typescript
class SpeculationEngine {
  async denySpeculation(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) return;
    
    try {
      // 1. 标记状态为 DENIED
      session.status = SpeculationStatus.DENIED;
      
      // 2. 安全清理 Overlay FS
      await this.safeRemoveOverlay(session.overlayPath);
      
      // 3. 清理会话记录
      this.sessions.delete(sessionId);
      
      // 4. 记录遥测数据
      this.telemetry.logSpeculationDenied(sessionId, {
        toolCount: session.toolCalls.length,
        duration: Date.now() - session.startTime
      });
      
    } catch (error) {
      // 即使清理失败，也不影响主系统
      console.error('Speculation cleanup failed:', error);
      // 标记为需要后台清理
      this.scheduleBackgroundCleanup(session.overlayPath);
    }
  }
  
  private async safeRemoveOverlay(overlayPath: string): Promise<void> {
    // 防御性检查：确保不删除主工作目录
    if (!overlayPath.includes('speculation-')) {
      throw new Error('Invalid overlay path');
    }
    
    // 递归删除临时目录
    await fs.rm(overlayPath, { recursive: true, force: true });
  }
}
```

**安全原则**：
1. **隔离性**：Overlay FS 完全独立，失败不影响主系统
2. **原子性**：合并操作要么全部成功，要么全部回滚
3. **幂等性**：重复调用 `denySpeculation()` 不会产生副作用
4. **防御性**：路径检查防止误删主目录

### 4.4 冲突检测与处理

```typescript
interface ConflictDetector {
  async hasConflict(
    mainFile: string,
    overlayChange: FileChange
  ): Promise<boolean> {
    // 检查主文件是否在预执行期间被修改
    const mainStat = await fs.stat(mainFile).catch(() => null);
    
    if (!mainStat) {
      // 主文件不存在，无冲突
      return false;
    }
    
    // 比较修改时间
    if (mainStat.mtimeMs > overlayChange.timestamp) {
      // 主文件更新，存在冲突
      return true;
    }
    
    // 可选：内容哈希比对
    const mainHash = await this.computeFileHash(mainFile);
    const overlayHash = overlayChange.hash;
    
    return mainHash !== overlayChange.baseHash;
  }
}
```

**冲突处理策略**：
- **保守策略**：发现冲突立即中止合并，提示用户手动解决
- **激进策略**：Overlay 优先，覆盖主文件（需要用户明确授权）
- **三路合并**：尝试自动合并（复杂度高，Claude Code 未采用）

---

## 5. 设计决策

### 5.1 为什么选择 Overlay FS 而非事务日志？

**对比方案**：

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Overlay FS** | 实现简单、隔离性强、支持任意工具 | 需要复制文件、占用磁盘空间 |
| **事务日志** | 节省空间、回滚快速 | 需要工具支持事务、实现复杂 |
| **Copy-on-Write** | 性能最优、空间效率高 | 需要文件系统支持（Btrfs/ZFS） |

**Claude Code 选择 Overlay FS 的原因**：
1. **通用性**：不依赖特定文件系统或工具支持
2. **简单性**：实现逻辑清晰，易于调试
3. **隔离性**：完全独立的临时目录，失败安全
4. **可移植性**：跨平台支持（Windows/macOS/Linux）

### 5.2 为什么不是所有操作都预执行？

**预执行的适用场景**：
- ✅ 文件读写操作（Edit、Write、Read）
- ✅ 本地命令执行（Bash、Git）
- ✅ 代码分析工具（Grep、Glob）
- ❌ 网络请求（API 调用、数据库操作）
- ❌ 不可逆操作（删除远程资源、发送邮件）
- ❌ 有副作用的操作（触发 CI/CD、通知用户）

**判断标准**：
```typescript
function isSpeculatable(toolCall: ToolCall): boolean {
  // 1. 工具必须声明支持预执行
  if (!toolCall.tool.supportsSpeculation) return false;
  
  // 2. 操作必须是幂等的
  if (!toolCall.tool.isIdempotent) return false;
  
  // 3. 操作必须是本地的
  if (toolCall.tool.requiresNetwork) return false;
  
  // 4. 操作必须是可回滚的
  if (toolCall.tool.hasIrreversibleEffects) return false;
  
  return true;
}
```

### 5.3 时间节省的边界条件

**场景 1：预执行比用户决策快**
```
用户思考 5 秒 → 预执行 2 秒完成 → 节省 2 秒
```

**场景 2：预执行比用户决策慢**
```
用户思考 1 秒 → 预执行 3 秒完成 → 节省 0 秒（但不浪费时间）
```

**场景 3：用户拒绝建议**
```
用户思考 2 秒 → 拒绝 → 预执行浪费 2 秒（但不影响主系统）
```

**权衡**：
- **收益**：大部分情况下节省等待时间，提升体验
- **成本**：少数情况下浪费计算资源（用户拒绝时）
- **结论**：用户接受率 > 50% 时，预执行是值得的


---

## 6. 参考实现

### 6.1 Claude Code 源码位置

| 组件 | 文件路径 | 关键函数 |
|------|----------|----------|
| Speculation Engine | `src/speculation/SpeculationEngine.ts` | `startSpeculation()`, `acceptSpeculation()`, `denySpeculation()` |
| Overlay FS Manager | `src/speculation/OverlayFSManager.ts` | `createOverlay()`, `copyOverlayToMain()`, `safeRemoveOverlay()` |
| Feedback Generator | `src/speculation/FeedbackGenerator.ts` | `createSpeculationFeedbackMessage()` |
| Timer | `src/speculation/SpeculationTimer.ts` | `calculateTimeSaved()` |

### 6.2 关键函数签名

```typescript
// src/speculation/SpeculationEngine.ts
export class SpeculationEngine {
  constructor(
    private toolExecutor: ToolExecutor,
    private overlayManager: OverlayFSManager,
    private telemetry: TelemetryService
  ) {}
  
  async startSpeculation(
    suggestion: ToolCall[],
    context: ExecutionContext
  ): Promise<SpeculationSession>;
  
  async acceptSpeculation(sessionId: string): Promise<SpeculationResult>;
  
  async denySpeculation(sessionId: string): Promise<void>;
}

// src/speculation/OverlayFSManager.ts
export class OverlayFSManager {
  async createOverlay(sessionId: string): Promise<string>;
  
  async executeInOverlay(
    overlayPath: string,
    toolCall: ToolCall
  ): Promise<ToolResult>;
  
  async copyOverlayToMain(
    overlayPath: string,
    mainPath: string
  ): Promise<MergeResult>;
  
  async safeRemoveOverlay(overlayPath: string): Promise<void>;
  
  async getOverlayChanges(overlayPath: string): Promise<FileChange[]>;
}
```

### 6.3 设计模式应用

**1. Strategy Pattern（策略模式）**
```typescript
interface MergeStrategy {
  merge(overlay: string, main: string): Promise<MergeResult>;
}

class ConservativeMerge implements MergeStrategy {
  // 发现冲突立即中止
}

class AggressiveMerge implements MergeStrategy {
  // Overlay 优先覆盖
}

class OverlayFSManager {
  constructor(private strategy: MergeStrategy) {}
}
```

**2. Command Pattern（命令模式）**
```typescript
interface SpeculationCommand {
  execute(): Promise<void>;
  undo(): Promise<void>;
}

class AcceptSpeculationCommand implements SpeculationCommand {
  async execute() {
    await this.engine.acceptSpeculation(this.sessionId);
  }
  
  async undo() {
    // 回滚合并操作
  }
}
```

**3. Observer Pattern（观察者模式）**
```typescript
class SpeculationEngine extends EventEmitter {
  emit('speculation:started', session);
  emit('speculation:completed', result);
  emit('speculation:accepted', result);
  emit('speculation:denied', sessionId);
}

// 订阅者
engine.on('speculation:accepted', (result) => {
  ui.showFeedback(`Saved ${result.timeSavedMs}ms`);
});
```

---

## 7. 实现检查清单

### 7.1 必须实现的功能

**核心功能**：
- [ ] Overlay FS 创建和管理
- [ ] 工具在 Overlay 中执行
- [ ] 原子合并到主文件系统
- [ ] 安全清理 Overlay
- [ ] 时间节省计量
- [ ] 反馈消息生成

**安全保障**：
- [ ] 路径验证（防止误删主目录）
- [ ] 冲突检测
- [ ] 失败回滚
- [ ] 错误日志记录

**状态管理**：
- [ ] Speculation 状态机
- [ ] 会话生命周期管理
- [ ] 并发控制（同时只能有一个预执行）

### 7.2 可选的优化

**性能优化**：
- [ ] 增量复制（只复制需要的文件）
- [ ] 并行执行多个工具调用
- [ ] 后台清理（异步删除 Overlay）
- [ ] 缓存预执行结果（相同操作复用）

**用户体验**：
- [ ] 预执行进度显示
- [ ] 累计时间节省统计
- [ ] 预执行成功率统计
- [ ] 可配置的预执行策略

**高级特性**：
- [ ] 三路合并（自动解决冲突）
- [ ] 预执行历史记录
- [ ] 预执行回放（调试用）
- [ ] 分布式预执行（多机并行）

### 7.3 测试验证点

**单元测试**：
```typescript
describe('SpeculationEngine', () => {
  it('should create overlay directory', async () => {
    const session = await engine.startSpeculation([toolCall], context);
    expect(fs.existsSync(session.overlayPath)).toBe(true);
  });
  
  it('should merge overlay to main on accept', async () => {
    const session = await engine.startSpeculation([writeFile], context);
    const result = await engine.acceptSpeculation(session.id);
    expect(result.success).toBe(true);
    expect(fs.existsSync(mainFilePath)).toBe(true);
  });
  
  it('should cleanup overlay on deny', async () => {
    const session = await engine.startSpeculation([toolCall], context);
    await engine.denySpeculation(session.id);
    expect(fs.existsSync(session.overlayPath)).toBe(false);
  });
  
  it('should detect conflicts', async () => {
    const session = await engine.startSpeculation([writeFile], context);
    // 在预执行期间修改主文件
    await fs.writeFile(mainFilePath, 'conflict');
    const result = await engine.acceptSpeculation(session.id);
    expect(result.conflicts.length).toBeGreaterThan(0);
  });
});
```

**集成测试**：
```typescript
describe('Speculation Integration', () => {
  it('should save time when user accepts quickly', async () => {
    const session = await engine.startSpeculation([slowTool], context);
    await sleep(100); // 模拟用户思考
    const result = await engine.acceptSpeculation(session.id);
    expect(result.timeSavedMs).toBeGreaterThan(0);
  });
  
  it('should handle multiple file operations', async () => {
    const tools = [writeFile1, writeFile2, deleteFile3];
    const session = await engine.startSpeculation(tools, context);
    const result = await engine.acceptSpeculation(session.id);
    expect(result.filesChanged).toBe(3);
  });
});
```

**边界测试**：
- [ ] 磁盘空间不足时的处理
- [ ] 权限不足时的处理
- [ ] 并发预执行冲突
- [ ] 超大文件操作
- [ ] 网络文件系统兼容性


---

## 8. 附录

### 8.1 完整示例：文件编辑预执行

```typescript
// 用户请求：修改 config.json
const userRequest = "Update timeout to 5000 in config.json";

// LLM 生成建议
const suggestion: ToolCall = {
  tool: 'edit',
  parameters: {
    file: 'config.json',
    oldText: '"timeout": 3000',
    newText: '"timeout": 5000'
  }
};

// 1. 启动预执行
const session = await speculationEngine.startSpeculation(
  [suggestion],
  context
);

console.log(`Speculation started in ${session.overlayPath}`);

// 2. 在 Overlay 中执行
// (后台自动进行，用户看到建议)

// 3. 用户确认
const userAccepted = await ui.promptUser(suggestion);

if (userAccepted) {
  // 4. 原子合并
  const result = await speculationEngine.acceptSpeculation(session.id);
  
  // 5. 显示反馈
  ui.showMessage(
    `✓ Applied changes instantly (saved ${result.timeSavedMs}ms)`
  );
  
  console.log(`Session total saved: ${result.sessionTotalMs}ms`);
} else {
  // 6. 清理 Overlay
  await speculationEngine.denySpeculation(session.id);
  ui.showMessage('✗ Changes discarded');
}
```

### 8.2 性能基准测试数据

基于 Claude Code 实际使用数据（模拟）：

| 操作类型 | 平均执行时间 | 平均用户决策时间 | 平均节省时间 | 节省率 |
|----------|--------------|------------------|--------------|--------|
| 单文件编辑 | 150ms | 3000ms | 150ms | 100% |
| 多文件编辑 | 800ms | 5000ms | 800ms | 100% |
| Bash 命令 | 500ms | 4000ms | 500ms | 100% |
| 代码重构 | 2000ms | 8000ms | 2000ms | 100% |
| 快速确认 | 100ms | 500ms | 0ms | 0% |

**关键发现**：
- 用户平均决策时间：3-8 秒
- 工具平均执行时间：100-2000ms
- 预执行成功率：85%（用户接受建议的比例）
- 平均时间节省：每次操作 500-1000ms
- 会话累计节省：10-30 秒（10-20 次操作）

### 8.3 与其他系统的对比

| 系统 | 预执行机制 | 隔离方式 | 回滚策略 |
|------|-----------|----------|----------|
| **Claude Code** | Overlay FS + 原子合并 | 临时目录 | 删除 Overlay |
| **Git** | Staging Area | Index 文件 | `git reset` |
| **Docker** | Layer Cache | Union FS | 删除容器 |
| **Database** | Transaction Log | MVCC | Rollback |
| **IDE Refactoring** | Preview Mode | 内存 Diff | 取消操作 |

**Claude Code 的独特性**：
- 面向 LLM 建议的预执行（而非用户操作）
- 文件系统级别的隔离（而非应用层）
- 时间节省的显式计量（用户可见的反馈）

### 8.4 常见问题

**Q1: 预执行失败会影响主系统吗？**
A: 不会。所有操作在 Overlay FS 中进行，失败时只需清理临时目录。

**Q2: 如何处理预执行期间主文件被修改？**
A: 合并时检测冲突，发现冲突则中止合并，提示用户手动解决。

**Q3: 预执行会占用多少磁盘空间？**
A: 取决于操作的文件大小。通常 < 100MB，操作完成后立即清理。

**Q4: 可以同时进行多个预执行吗？**
A: Claude Code 限制同时只能有一个预执行会话，避免冲突。

**Q5: 预执行适用于所有工具吗？**
A: 不适用。仅支持本地、幂等、可回滚的操作（文件、命令）。

**Q6: 如何调试预执行问题？**
A: 检查 Overlay 目录内容、查看遥测日志、启用详细日志模式。

### 8.5 未来优化方向

**1. 智能预测**
```typescript
// 基于历史数据预测用户接受率
if (predictAcceptRate(suggestion) > 0.7) {
  startSpeculation(suggestion);
}
```

**2. 增量合并**
```typescript
// 只合并变更的文件，而非全部复制
const changes = await getIncrementalChanges(overlay);
await applyChanges(changes);
```

**3. 分布式预执行**
```typescript
// 在多台机器上并行预执行不同建议
const results = await Promise.all([
  speculateOnMachine1(suggestion1),
  speculateOnMachine2(suggestion2)
]);
```

**4. 预执行缓存**
```typescript
// 相同操作复用预执行结果
const cacheKey = hashToolCall(toolCall);
if (cache.has(cacheKey)) {
  return cache.get(cacheKey);
}
```

---

## 9. 总结

### 9.1 核心价值

Speculation 预执行系统通过 **Overlay FS + 原子合并** 实现了：

1. **零等待体验**：用户确认后立即看到结果
2. **失败安全**：预执行失败不影响主系统
3. **可量化收益**：显式计量时间节省，提升用户感知
4. **通用性**：适用于任意本地工具，无需特殊支持

### 9.2 设计精髓

- **隔离性**：临时目录完全独立，失败安全
- **原子性**：合并操作要么全部成功，要么全部回滚
- **可观测性**：时间节省计量 + 遥测数据
- **简单性**：实现逻辑清晰，易于调试和维护

### 9.3 适用场景

**最适合**：
- 文件编辑操作（Edit、Write、Delete）
- 本地命令执行（Bash、Git）
- 代码分析工具（Grep、Glob）
- 用户决策时间 > 工具执行时间

**不适合**：
- 网络请求（API 调用、数据库操作）
- 不可逆操作（删除远程资源、发送通知）
- 有副作用的操作（触发 CI/CD、修改外部状态）

### 9.4 实现建议

1. **从简单开始**：先实现单文件编辑的预执行
2. **逐步扩展**：支持更多工具类型（Bash、Git）
3. **监控效果**：收集时间节省数据，验证收益
4. **优化策略**：根据用户接受率调整预执行策略

---

**相关文档**：
- [02-AGENT-LOOP.md](02-AGENT-LOOP.md) - Agent 主循环设计
- [03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md) - 工具系统架构
- [06-PERMISSION.md](06-PERMISSION.md) - 权限系统设计
- [12-DESIGN-PHILOSOPHY.md](12-DESIGN-PHILOSOPHY.md) - 设计哲学

**版本信息**：
- 文档版本：v1.0
- 基于 Claude Code 版本：v2.1.88
- 最后更新：2026-04-01

---

## 10. 深度技术分析

### 10.1 Overlay FS 的内存与性能权衡

**内存占用分析**：

```typescript
class OverlayMemoryManager {
  private maxOverlaySize = 500 * 1024 * 1024; // 500MB 限制
  
  async checkMemoryConstraints(
    overlayPath: string
  ): Promise<MemoryCheckResult> {
    const size = await this.calculateDirectorySize(overlayPath);
    
    if (size > this.maxOverlaySize) {
      return {
        allowed: false,
        reason: 'Overlay size exceeds limit',
        currentSize: size,
        maxSize: this.maxOverlaySize
      };
    }
    
    // 检查系统可用磁盘空间
    const diskSpace = await this.getAvailableDiskSpace();
    if (diskSpace < size * 2) {
      return {
        allowed: false,
        reason: 'Insufficient disk space',
        required: size * 2,
        available: diskSpace
      };
    }
    
    return { allowed: true };
  }
}
```

**性能优化策略**：

1. **按需复制（Copy-on-Write 模拟）**
```typescript
class LazyOverlayManager {
  // 不预先复制整个工作目录，只在访问时复制
  async getFileInOverlay(
    filePath: string,
    overlayPath: string
  ): Promise<string> {
    const overlayFile = path.join(overlayPath, filePath);
    
    if (!fs.existsSync(overlayFile)) {
      // 首次访问时才复制
      const mainFile = path.join(this.mainPath, filePath);
      await fs.copyFile(mainFile, overlayFile);
    }
    
    return overlayFile;
  }
}
```

2. **并行文件操作**
```typescript
async copyOverlayToMain(
  overlayPath: string,
  mainPath: string
): Promise<MergeResult> {
  const changes = await this.getOverlayChanges(overlayPath);
  
  // 并行复制多个文件
  const results = await Promise.allSettled(
    changes.map(change => this.copyFile(change, overlayPath, mainPath))
  );
  
  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected');
  
  return {
    success: failed.length === 0,
    filesChanged: succeeded,
    errors: failed.map(f => f.reason)
  };
}
```

### 10.2 冲突解决的高级策略

**三路合并实现**（可选高级特性）：

```typescript
interface ThreeWayMerger {
  merge(
    base: string,      // 预执行开始时的版本
    overlay: string,   // 预执行后的版本
    main: string       // 当前主文件版本
  ): Promise<MergeResult>;
}

class TextFileMerger implements ThreeWayMerger {
  async merge(base: string, overlay: string, main: string): Promise<MergeResult> {
    const baseContent = await fs.readFile(base, 'utf-8');
    const overlayContent = await fs.readFile(overlay, 'utf-8');
    const mainContent = await fs.readFile(main, 'utf-8');
    
    // 使用 diff3 算法
    const merged = this.diff3Merge(baseContent, overlayContent, mainContent);
    
    if (merged.conflicts.length > 0) {
      return {
        success: false,
        conflicts: merged.conflicts,
        mergedContent: merged.contentWithMarkers
      };
    }
    
    return {
      success: true,
      mergedContent: merged.content
    };
  }
  
  private diff3Merge(
    base: string,
    ours: string,
    theirs: string
  ): Diff3Result {
    // 实现 diff3 算法
    // 1. 计算 base -> ours 的差异
    const oursDiff = this.computeDiff(base, ours);
    
    // 2. 计算 base -> theirs 的差异
    const theirsDiff = this.computeDiff(base, theirs);
    
    // 3. 合并两组差异
    return this.mergeDiffs(oursDiff, theirsDiff);
  }
}
```

**冲突标记格式**：

```
<<<<<<< Overlay (Speculation)
timeout: 5000
=======
timeout: 4000
>>>>>>> Main (Current)
```

### 10.3 预执行的遥测与可观测性

**完整的遥测数据收集**：

```typescript
interface SpeculationTelemetry {
  // 基础指标
  sessionId: string;
  startTime: number;
  endTime: number;
  duration: number;
  
  // 工具执行
  toolCalls: ToolCall[];
  toolCount: number;
  toolExecutionTime: number;
  
  // 用户行为
  userDecisionTime: number;
  userAccepted: boolean;
  
  // 性能指标
  timeSavedMs: number;
  overlaySize: number;
  filesChanged: number;
  
  // 错误信息
  errors: Error[];
  conflicts: FileConflict[];
  
  // 上下文
  workspaceSize: number;
  systemMemory: number;
  diskSpace: number;
}

class TelemetryCollector {
  async logSpeculation(telemetry: SpeculationTelemetry): Promise<void> {
    // 1. 记录到本地日志
    await this.writeToLog(telemetry);
    
    // 2. 发送到分析服务（可选）
    if (this.config.enableRemoteTelemetry) {
      await this.sendToAnalytics(telemetry);
    }
    
    // 3. 更新会话统计
    await this.updateSessionStats(telemetry);
  }
  
  async getSpeculationStats(): Promise<SpeculationStats> {
    return {
      totalSpeculations: this.stats.total,
      acceptedCount: this.stats.accepted,
      deniedCount: this.stats.denied,
      acceptRate: this.stats.accepted / this.stats.total,
      avgTimeSaved: this.stats.totalTimeSaved / this.stats.accepted,
      avgUserDecisionTime: this.stats.totalDecisionTime / this.stats.total
    };
  }
}
```

**实时监控面板**：

```typescript
class SpeculationMonitor {
  displayStats(): void {
    const stats = this.telemetry.getSpeculationStats();
    
    console.log(`
╔════════════════════════════════════════╗
║     Speculation Performance Stats      ║
╠════════════════════════════════════════╣
║ Total Speculations: ${stats.totalSpeculations.toString().padStart(18)} ║
║ Accept Rate:        ${(stats.acceptRate * 100).toFixed(1).padStart(15)}% ║
║ Avg Time Saved:     ${stats.avgTimeSaved.toFixed(0).padStart(15)}ms ║
║ Avg Decision Time:  ${stats.avgUserDecisionTime.toFixed(0).padStart(15)}ms ║
╚════════════════════════════════════════╝
    `);
  }
}
```

### 10.4 与权限系统的集成

**预执行的权限检查**：

```typescript
class SpeculationPermissionChecker {
  async canSpeculate(
    toolCall: ToolCall,
    permissionMode: PermissionMode
  ): Promise<boolean> {
    // 1. YOLO 模式：允许所有本地操作预执行
    if (permissionMode === PermissionMode.YOLO) {
      return this.isLocalOperation(toolCall);
    }
    
    // 2. Auto 模式：使用分类器判断
    if (permissionMode === PermissionMode.AUTO) {
      const classification = await this.classifier.classify(toolCall);
      return classification.allowSpeculation;
    }
    
    // 3. Plan 模式：需要用户明确授权
    if (permissionMode === PermissionMode.PLAN) {
      return await this.promptUser(
        `Allow speculation for: ${toolCall.tool}?`
      );
    }
    
    // 4. Manual 模式：不允许预执行
    return false;
  }
  
  private isLocalOperation(toolCall: ToolCall): boolean {
    const localTools = ['edit', 'write', 'read', 'bash', 'git'];
    return localTools.includes(toolCall.tool);
  }
}
```

**权限模式与预执行的关系**：

| 权限模式 | 预执行策略 | 用户体验 |
|----------|-----------|----------|
| **Manual** | 禁用 | 每次操作都需确认，无预执行 |
| **Plan** | 需授权 | 用户可选择是否预执行 |
| **Auto** | 智能判断 | 分类器决定是否预执行 |
| **YOLO** | 全部启用 | 所有本地操作自动预执行 |


### 10.5 边界情况与错误处理

**场景 1：磁盘空间不足**

```typescript
class SpeculationEngine {
  async startSpeculation(
    suggestion: ToolCall[],
    context: ExecutionContext
  ): Promise<SpeculationSession> {
    // 预检查磁盘空间
    const estimatedSize = this.estimateOperationSize(suggestion);
    const availableSpace = await this.getAvailableDiskSpace();
    
    if (availableSpace < estimatedSize * 2) {
      throw new SpeculationError(
        'Insufficient disk space for speculation',
        { required: estimatedSize * 2, available: availableSpace }
      );
    }
    
    // 继续创建 Overlay
    const session = await this.createSpeculationSession(suggestion);
    return session;
  }
  
  private estimateOperationSize(toolCalls: ToolCall[]): number {
    let totalSize = 0;
    
    for (const call of toolCalls) {
      if (call.tool === 'write') {
        totalSize += call.parameters.content.length;
      } else if (call.tool === 'edit') {
        // 估算编辑后的文件大小
        totalSize += this.estimateEditSize(call);
      }
    }
    
    return totalSize;
  }
}
```

**场景 2：预执行超时**

```typescript
class SpeculationEngine {
  private readonly SPECULATION_TIMEOUT = 30000; // 30秒
  
  async startSpeculation(
    suggestion: ToolCall[],
    context: ExecutionContext
  ): Promise<SpeculationSession> {
    const session = await this.createSpeculationSession(suggestion);
    
    // 设置超时保护
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new SpeculationTimeoutError(
          `Speculation timed out after ${this.SPECULATION_TIMEOUT}ms`
        ));
      }, this.SPECULATION_TIMEOUT);
    });
    
    try {
      await Promise.race([
        this.executeInOverlay(session),
        timeoutPromise
      ]);
    } catch (error) {
      // 超时或失败，清理 Overlay
      await this.safeRemoveOverlay(session.overlayPath);
      throw error;
    }
    
    return session;
  }
}
```

**场景 3：并发预执行冲突**

```typescript
class SpeculationEngine {
  private activeSession: SpeculationSession | null = null;
  private sessionLock = new AsyncLock();
  
  async startSpeculation(
    suggestion: ToolCall[],
    context: ExecutionContext
  ): Promise<SpeculationSession> {
    return this.sessionLock.acquire('speculation', async () => {
      // 检查是否有活跃的预执行
      if (this.activeSession) {
        throw new SpeculationConflictError(
          'Another speculation is already running',
          { activeSessionId: this.activeSession.id }
        );
      }
      
      // 创建新会话
      const session = await this.createSpeculationSession(suggestion);
      this.activeSession = session;
      
      return session;
    });
  }
  
  async acceptSpeculation(sessionId: string): Promise<SpeculationResult> {
    return this.sessionLock.acquire('speculation', async () => {
      const result = await this.mergeOverlay(sessionId);
      this.activeSession = null;
      return result;
    });
  }
}
```

**场景 4：文件权限问题**

```typescript
class OverlayFSManager {
  async copyOverlayToMain(
    overlayPath: string,
    mainPath: string
  ): Promise<MergeResult> {
    const changes = await this.getOverlayChanges(overlayPath);
    const errors: FileError[] = [];
    
    for (const change of changes) {
      try {
        const mainFile = path.join(mainPath, change.path);
        
        // 检查写权限
        if (!await this.hasWritePermission(mainFile)) {
          errors.push({
            file: change.path,
            error: 'Permission denied',
            code: 'EACCES'
          });
          continue;
        }
        
        // 执行复制
        await this.copyFile(change, overlayPath, mainPath);
        
      } catch (error) {
        errors.push({
          file: change.path,
          error: error.message,
          code: error.code
        });
      }
    }
    
    return {
      success: errors.length === 0,
      filesChanged: changes.length - errors.length,
      errors
    };
  }
}
```

### 10.6 多工具预执行的依赖管理

**工具依赖图构建**：

```typescript
interface ToolDependency {
  tool: ToolCall;
  dependsOn: string[];  // 依赖的工具 ID
}

class SpeculationDependencyResolver {
  buildDependencyGraph(toolCalls: ToolCall[]): ToolDependency[] {
    const graph: ToolDependency[] = [];
    
    for (const tool of toolCalls) {
      const deps = this.findDependencies(tool, toolCalls);
      graph.push({ tool, dependsOn: deps });
    }
    
    return graph;
  }
  
  private findDependencies(
    tool: ToolCall,
    allTools: ToolCall[]
  ): string[] {
    const deps: string[] = [];
    
    // 示例：Edit 依赖于 Read
    if (tool.tool === 'edit') {
      const readTool = allTools.find(
        t => t.tool === 'read' && t.parameters.file === tool.parameters.file
      );
      if (readTool) {
        deps.push(readTool.id);
      }
    }
    
    // 示例：Write 依赖于 Bash（如果 Bash 生成了文件）
    if (tool.tool === 'write') {
      const bashTool = allTools.find(
        t => t.tool === 'bash' && this.generatesFile(t, tool.parameters.file)
      );
      if (bashTool) {
        deps.push(bashTool.id);
      }
    }
    
    return deps;
  }
  
  async executeInOrder(
    toolCalls: ToolCall[],
    overlayPath: string
  ): Promise<ToolResult[]> {
    const graph = this.buildDependencyGraph(toolCalls);
    const executed = new Set<string>();
    const results: ToolResult[] = [];
    
    // 拓扑排序执行
    while (executed.size < toolCalls.length) {
      const ready = graph.filter(
        node => !executed.has(node.tool.id) &&
                node.dependsOn.every(dep => executed.has(dep))
      );
      
      if (ready.length === 0) {
        throw new Error('Circular dependency detected');
      }
      
      // 并行执行无依赖的工具
      const batchResults = await Promise.all(
        ready.map(node => this.executeInOverlay(node.tool, overlayPath))
      );
      
      results.push(...batchResults);
      ready.forEach(node => executed.add(node.tool.id));
    }
    
    return results;
  }
}
```

### 10.7 预执行结果的缓存策略

**基于内容哈希的缓存**：

```typescript
class SpeculationCache {
  private cache = new Map<string, CachedResult>();
  private readonly MAX_CACHE_SIZE = 100;
  private readonly CACHE_TTL = 3600000; // 1小时
  
  async get(toolCall: ToolCall): Promise<ToolResult | null> {
    const key = this.computeCacheKey(toolCall);
    const cached = this.cache.get(key);
    
    if (!cached) return null;
    
    // 检查是否过期
    if (Date.now() - cached.timestamp > this.CACHE_TTL) {
      this.cache.delete(key);
      return null;
    }
    
    // 检查依赖文件是否变更
    if (await this.hasFileChanged(cached.dependencies)) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.result;
  }
  
  async set(
    toolCall: ToolCall,
    result: ToolResult,
    dependencies: string[]
  ): Promise<void> {
    const key = this.computeCacheKey(toolCall);
    
    // LRU 淘汰
    if (this.cache.size >= this.MAX_CACHE_SIZE) {
      const oldest = this.findOldestEntry();
      this.cache.delete(oldest);
    }
    
    this.cache.set(key, {
      result,
      dependencies,
      timestamp: Date.now()
    });
  }
  
  private computeCacheKey(toolCall: ToolCall): string {
    // 基于工具名称和参数计算哈希
    const content = JSON.stringify({
      tool: toolCall.tool,
      parameters: toolCall.parameters
    });
    return crypto.createHash('sha256').update(content).digest('hex');
  }
  
  private async hasFileChanged(files: string[]): Promise<boolean> {
    for (const file of files) {
      const currentHash = await this.computeFileHash(file);
      const cachedHash = this.fileHashes.get(file);
      
      if (currentHash !== cachedHash) {
        return true;
      }
    }
    return false;
  }
}
```


### 10.8 实战案例：复杂重构的预执行

**场景：重命名函数并更新所有引用**

```typescript
// 用户请求：将 calculatePrice 重命名为 computeTotal
const refactoringPlan: ToolCall[] = [
  {
    id: '1',
    tool: 'grep',
    parameters: {
      pattern: 'calculatePrice',
      path: 'src/'
    }
  },
  {
    id: '2',
    tool: 'edit',
    parameters: {
      file: 'src/utils.ts',
      oldText: 'function calculatePrice',
      newText: 'function computeTotal'
    }
  },
  {
    id: '3',
    tool: 'edit',
    parameters: {
      file: 'src/cart.ts',
      oldText: 'calculatePrice(items)',
      newText: 'computeTotal(items)'
    }
  },
  {
    id: '4',
    tool: 'bash',
    parameters: {
      command: 'npm run type-check'
    }
  }
];

// 预执行流程
const session = await speculationEngine.startSpeculation(
  refactoringPlan,
  context
);

// 在 Overlay 中执行所有步骤
// 1. Grep 找到所有引用
// 2. 编辑函数定义
// 3. 编辑所有调用点
// 4. 运行类型检查验证

// 用户确认后，原子合并所有变更
const result = await speculationEngine.acceptSpeculation(session.id);

console.log(`Refactoring completed in ${result.timeSavedMs}ms`);
console.log(`Files changed: ${result.filesChanged}`);
```

**预执行的价值**：
- 用户思考时间：10 秒（评估重构影响）
- 工具执行时间：5 秒（Grep + Edit + Type Check）
- 时间节省：5 秒（完全并行）

### 10.9 与 Git 集成的预执行

**在 Git 分支中预执行**：

```typescript
class GitAwareSpeculationEngine extends SpeculationEngine {
  async startSpeculation(
    suggestion: ToolCall[],
    context: ExecutionContext
  ): Promise<SpeculationSession> {
    // 1. 创建临时 Git 分支
    const branchName = `speculation-${Date.now()}`;
    await this.git.createBranch(branchName);
    await this.git.checkout(branchName);
    
    // 2. 在分支中执行工具
    const session = await super.startSpeculation(suggestion, context);
    session.gitBranch = branchName;
    
    return session;
  }
  
  async acceptSpeculation(sessionId: string): Promise<SpeculationResult> {
    const session = this.sessions.get(sessionId);
    
    // 1. 合并分支到主分支
    await this.git.checkout('main');
    await this.git.merge(session.gitBranch);
    
    // 2. 删除临时分支
    await this.git.deleteBranch(session.gitBranch);
    
    return {
      success: true,
      timeSavedMs: this.calculateTimeSaved(session),
      gitCommit: await this.git.getLastCommit()
    };
  }
  
  async denySpeculation(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    
    // 1. 切回主分支
    await this.git.checkout('main');
    
    // 2. 删除临时分支（丢弃所有变更）
    await this.git.deleteBranch(session.gitBranch, { force: true });
  }
}
```

**优势**：
- 利用 Git 的原子性保证
- 自动版本控制
- 可以查看预执行的 diff
- 支持回滚到任意时间点

### 10.10 跨平台兼容性

**Windows 特殊处理**：

```typescript
class PlatformAwareOverlayManager extends OverlayFSManager {
  async createOverlay(sessionId: string): Promise<string> {
    const tmpDir = this.getTempDirectory();
    const overlayPath = path.join(tmpDir, `speculation-${sessionId}`);
    
    if (process.platform === 'win32') {
      // Windows: 使用短路径避免路径长度限制
      const shortPath = await this.getShortPath(overlayPath);
      await fs.mkdir(shortPath, { recursive: true });
      return shortPath;
    } else {
      // Unix: 标准路径
      await fs.mkdir(overlayPath, { recursive: true });
      return overlayPath;
    }
  }
  
  private getTempDirectory(): string {
    if (process.platform === 'win32') {
      // Windows: 使用 %TEMP%
      return process.env.TEMP || 'C:\\Temp';
    } else if (process.platform === 'darwin') {
      // macOS: 使用 /tmp
      return '/tmp';
    } else {
      // Linux: 使用 /tmp 或 /var/tmp
      return '/tmp';
    }
  }
  
  async copyFile(src: string, dest: string): Promise<void> {
    if (process.platform === 'win32') {
      // Windows: 处理文件锁和权限
      await this.copyFileWindows(src, dest);
    } else {
      // Unix: 标准复制
      await fs.copyFile(src, dest);
    }
  }
  
  private async copyFileWindows(src: string, dest: string): Promise<void> {
    // 重试机制处理文件锁
    const maxRetries = 3;
    for (let i = 0; i < maxRetries; i++) {
      try {
        await fs.copyFile(src, dest);
        return;
      } catch (error) {
        if (error.code === 'EBUSY' && i < maxRetries - 1) {
          await this.sleep(100 * (i + 1));
          continue;
        }
        throw error;
      }
    }
  }
}
```

---

## 11. 生产环境部署建议

### 11.1 配置参数

```typescript
interface SpeculationConfig {
  // 功能开关
  enabled: boolean;                    // 是否启用预执行
  
  // 性能参数
  maxOverlaySize: number;              // 最大 Overlay 大小（字节）
  timeout: number;                     // 预执行超时时间（毫秒）
  maxConcurrentSpeculations: number;   // 最大并发预执行数
  
  // 缓存配置
  enableCache: boolean;                // 是否启用结果缓存
  cacheSize: number;                   // 缓存条目数
  cacheTTL: number;                    // 缓存过期时间（毫秒）
  
  // 安全配置
  allowedTools: string[];              // 允许预执行的工具列表
  forbiddenPaths: string[];            // 禁止预执行的路径
  requireUserConfirmation: boolean;    // 是否需要用户确认
  
  // 遥测配置
  enableTelemetry: boolean;            // 是否启用遥测
  telemetryEndpoint: string;           // 遥测数据上报地址
}

// 推荐配置
const productionConfig: SpeculationConfig = {
  enabled: true,
  maxOverlaySize: 500 * 1024 * 1024,   // 500MB
  timeout: 30000,                       // 30秒
  maxConcurrentSpeculations: 1,
  enableCache: true,
  cacheSize: 100,
  cacheTTL: 3600000,                    // 1小时
  allowedTools: ['edit', 'write', 'read', 'bash', 'git'],
  forbiddenPaths: ['/etc', '/sys', '/proc'],
  requireUserConfirmation: false,
  enableTelemetry: true,
  telemetryEndpoint: 'https://telemetry.example.com'
};
```

### 11.2 监控指标

**关键指标**：

```typescript
interface SpeculationMetrics {
  // 使用率
  totalSpeculations: number;
  acceptedSpeculations: number;
  deniedSpeculations: number;
  acceptRate: number;
  
  // 性能
  avgTimeSaved: number;
  totalTimeSaved: number;
  avgExecutionTime: number;
  avgUserDecisionTime: number;
  
  // 资源
  avgOverlaySize: number;
  maxOverlaySize: number;
  diskSpaceUsed: number;
  
  // 错误
  timeoutCount: number;
  conflictCount: number;
  errorCount: number;
  errorRate: number;
}

// 监控告警阈值
const alertThresholds = {
  acceptRate: 0.5,           // 接受率 < 50% 告警
  errorRate: 0.1,            // 错误率 > 10% 告警
  avgTimeSaved: 500,         // 平均节省 < 500ms 告警
  diskSpaceUsed: 10 * 1024 * 1024 * 1024  // 磁盘占用 > 10GB 告警
};
```

### 11.3 故障排查清单

**问题 1：预执行总是超时**
```
诊断步骤：
1. 检查工具执行时间：是否有慢工具（网络请求、大文件操作）
2. 检查系统资源：CPU、内存、磁盘 I/O 是否饱和
3. 检查超时配置：是否设置过短
4. 查看日志：是否有异常堆栈

解决方案：
- 增加超时时间
- 排除慢工具（不预执行）
- 优化工具实现
- 升级硬件资源
```

**问题 2：合并时频繁冲突**
```
诊断步骤：
1. 检查用户决策时间：是否过长导致主文件被修改
2. 检查并发操作：是否有其他进程修改文件
3. 检查文件类型：是否是频繁变更的文件（日志、缓存）

解决方案：
- 缩短预执行范围
- 排除频繁变更的文件
- 实现三路合并
- 提示用户避免并发修改
```

**问题 3：磁盘空间占用过高**
```
诊断步骤：
1. 检查 Overlay 清理：是否有未清理的临时目录
2. 检查缓存大小：是否缓存过多结果
3. 检查文件大小：是否预执行了大文件操作

解决方案：
- 定期清理临时目录
- 减小缓存大小
- 限制 Overlay 最大大小
- 实现增量复制
```

