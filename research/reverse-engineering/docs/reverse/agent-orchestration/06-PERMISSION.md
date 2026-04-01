# 06 - 权限系统：安全管道式设计

## 1. 核心概念

### 1.1 权限即管道（Permission as Pipeline）

Claude Code 的权限系统不是传统的"门禁"模型（allow/deny），而是**嵌入执行链的安全管道**。每个工具调用在执行前都要流经这条管道，管道的每个阶段都可以：

- **检查**：静态分析、动态分类、规则匹配
- **修改**：调整参数、添加约束、注入上下文
- **拦截**：暂停执行、请求确认、直接拒绝
- **学习**：记录决策、更新规则、持久化策略

这种设计让权限系统成为 Agent Loop 的**有机组成部分**，而非外挂的检查器。

### 1.2 四级权限模式

```
read-only  →  default  →  plan  →  auto
   ↑           ↑          ↑        ↑
只读模式    标准模式   计划模式  自动模式
```

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| **read-only** | 只允许读操作（Read、Glob、Grep），所有写操作被拒绝 | 代码审查、安全审计、探索陌生代码库 |
| **default** | 每个工具调用都需要用户确认 | 日常开发、学习新工具、不确定的操作 |
| **plan** | 批量确认：展示完整计划，用户一次性批准所有步骤 | 多步骤任务、重构、批量操作 |
| **auto** | YOLO Classifier 自动审查，只拦截高风险操作 | 信任的环境、重复性任务、CI/CD |

**关键设计**：模式不是全局的，而是**可以动态切换**。用户可以在任务中途从 `default` 切换到 `auto`，或在执行危险操作前临时切回 `default`。

### 1.3 YOLO Classifier：用 LLM 保护 LLM

**YOLO = You Only Look Once**，但在这里是 **You Only Live Once** 的隐喻——自动模式下的安全网。

核心思想：**用一个轻量级 LLM（Haiku）来审查主模型（Opus/Sonnet）的工具调用决策**。

```
主模型决策 → YOLO Classifier 审查 → 执行/拒绝/请求确认
   Opus          Haiku (快速)         结果
```

**为什么有效？**
- 主模型专注于任务完成，可能忽略安全风险
- 分类器专注于安全审查，使用专门的系统提示
- 双模型对抗：攻击者需要同时绕过两个模型
- 成本可控：Haiku 比 Opus 便宜 50 倍

### 1.4 设计动机

传统 Agent 的权限困境：
- **过于宽松**：给 Agent 完全权限 → 一个错误可能删除整个项目
- **过于严格**：每个操作都确认 → 用户疲劳，体验糟糕
- **静态规则**：预定义白名单 → 无法适应新场景，规则爆炸

Claude Code 的解决方案：
- **分级授权**：根据风险级别选择模式
- **动态学习**：从用户决策中学习，自动生成规则
- **智能分类**：用 LLM 理解操作意图，而非简单匹配
- **管道嵌入**：权限检查是执行流的一部分，不是外部守卫

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Tool Execution Pipeline                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  1. PermissionContext 创建                                   │
│     - 读取当前权限模式                                        │
│     - 加载权限规则列表                                        │
│     - 初始化 UI 状态（confirm queue）                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. 静态规则匹配                                             │
│     - 检查 CLAUDE.md 中的权限规则                            │
│     - 路径模式匹配（glob）                                   │
│     - 工具白名单/黑名单                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                         规则命中？
                        /          \
                      是             否
                      ↓              ↓
              ┌──────────────┐  ┌──────────────────────┐
              │ 直接执行/拒绝 │  │ 3. 模式决策          │
              └──────────────┘  │   - read-only: 拒绝  │
                                │   - default: 请求确认 │
                                │   - plan: 加入计划    │
                                │   - auto: YOLO 分类   │
                                └──────────────────────┘
                                          ↓
                                  ┌──────────────────┐
                                  │ 4. YOLO Classifier│
                                  │   (仅 auto 模式)  │
                                  │   - Stage 1: 快速 │
                                  │   - Stage 2: 精细 │
                                  └──────────────────┘
                                          ↓
                                    分类结果
                                  /     |      \
                            允许   不确定   拒绝
                              ↓      ↓       ↓
                            执行  请求确认  拒绝
                                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. PermissionUpdate 应用                                    │
│     - 用户批准 → 建议创建规则                                │
│     - 持久化到 CLAUDE.md                                     │
│     - 更新 PermissionContext                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
┌──────────────┐
│ Tool Call    │
│ (from LLM)   │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│ createPermissionContext()            │
│ ┌──────────────────────────────────┐ │
│ │ ToolPermissionContext            │ │
│ │ - mode: PermissionMode           │ │
│ │ - rules: PermissionRule[]        │ │
│ │ - confirmQueue: ToolUseConfirm[] │ │
│ │ - toolUseID: string              │ │
│ └──────────────────────────────────┘ │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│ Rule Matching Engine                 │
│ - matchPathPattern(rule, path)       │
│ - matchToolName(rule, tool)          │
│ - evaluateConditions(rule, context)  │
└──────┬───────────────────────────────┘
       │
       ↓ (no match)
┌──────────────────────────────────────┐
│ Mode-based Decision                  │
│ switch (context.mode) {              │
│   case 'read-only': checkReadOnly()  │
│   case 'default': requestConfirm()   │
│   case 'plan': addToPlan()           │
│   case 'auto': invokeYOLO()          │
│ }                                    │
└──────┬───────────────────────────────┘
       │
       ↓ (auto mode)
┌──────────────────────────────────────┐
│ YOLO Classifier                      │
│ ┌──────────────────────────────────┐ │
│ │ Stage 1: Quick Classification    │ │
│ │ - buildTranscriptForClassifier() │ │
│ │ - buildYoloSystemPrompt()        │ │
│ │ - classifyYoloAction()           │ │
│ │   → allow / deny / uncertain     │ │
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ Stage 2: Deep Analysis           │ │
│ │ (if uncertain)                   │ │
│ │ - 更详细的上下文                  │ │
│ │ - 更严格的评估标准                │ │
│ └──────────────────────────────────┘ │
└──────┬───────────────────────────────┘
       │
       ↓ (user approved)
┌──────────────────────────────────────┐
│ PermissionUpdate                     │
│ - extractRules(updates)              │
│ - applyPermissionUpdate(ctx, update) │
│ - persistPermissionUpdate(update)    │
│   → 写入 CLAUDE.md                   │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────┐
│ Tool Execute │
└──────────────┘
```

### 2.3 状态机定义

```typescript
// 权限决策状态机
enum PermissionDecision {
  ALLOW,           // 直接允许
  DENY,            // 直接拒绝
  REQUEST_CONFIRM, // 请求用户确认
  CHECKING,        // YOLO 分类中
  PENDING,         // 等待用户响应
}

// 状态转换
ALLOW → EXECUTE
DENY → ABORT
REQUEST_CONFIRM → PENDING → (user input) → ALLOW | DENY
CHECKING → (classifier result) → ALLOW | DENY | REQUEST_CONFIRM
```

---

## 3. 接口契约

### 3.1 核心接口定义

```typescript
// ============ PermissionContext ============

interface ToolPermissionContext {
  mode: PermissionMode;
  rules: PermissionRule[];
  confirmQueue: ToolUseConfirm[];
  toolUseID: string;
  tool: Tool;
  input: any;
  assistantMessage: Message;
}

function createPermissionContext(
  tool: Tool,
  input: any,
  toolUseContext: ToolUseContext,
  assistantMessage: Message,
  toolUseID: string,
  setToolPermissionContext: (ctx: ToolPermissionContext) => void
): ToolPermissionContext;

function createPermissionQueueOps(
  setToolUseConfirmQueue: (queue: ToolUseConfirm[]) => void
): {
  enqueue: (confirm: ToolUseConfirm) => void;
  dequeue: (toolUseID: string) => void;
  clear: () => void;
};

// ============ PermissionRule ============

interface PermissionRule {
  type: 'allow' | 'deny';
  tool?: string;           // 工具名称（可选）
  pathPattern?: string;    // 路径模式（glob）
  condition?: string;      // 条件表达式
  reason?: string;         // 规则说明
}

// 示例规则
const exampleRules: PermissionRule[] = [
  {
    type: 'allow',
    tool: 'Read',
    pathPattern: 'src/**/*.ts',
    reason: '允许读取源码目录'
  },
  {
    type: 'deny',
    tool: 'Bash',
    condition: 'input.includes("rm -rf")',
    reason: '禁止危险的删除命令'
  }
];

// ============ PermissionUpdate ============

interface PermissionUpdate {
  action: 'add_rule' | 'remove_rule' | 'change_mode';
  rule?: PermissionRule;
  mode?: PermissionMode;
  persist?: boolean;  // 是否持久化到 CLAUDE.md
}

function extractRules(updates: PermissionUpdate[]): PermissionRule[];

function applyPermissionUpdate(
  context: ToolPermissionContext,
  update: PermissionUpdate
): ToolPermissionContext;

function applyPermissionUpdates(
  context: ToolPermissionContext,
  updates: PermissionUpdate[]
): ToolPermissionContext;

function persistPermissionUpdate(update: PermissionUpdate): Promise<void>;

function persistPermissionUpdates(updates: PermissionUpdate[]): Promise<void>;

function createReadRuleSuggestion(
  dirPath: string,
  destination: string
): PermissionUpdate;

// ============ YOLO Classifier ============

interface YoloClassificationResult {
  decision: 'allow' | 'deny' | 'uncertain';
  reasoning: string;
  confidence: number;
  stage: 1 | 2;
}

function classifyYoloAction(
  messages: Message[],
  action: ToolCall,
  tools: Tool[],
  context: ToolUseContext,
  signal: AbortSignal
): Promise<YoloClassificationResult>;

function buildTranscriptForClassifier(
  messages: Message[],
  tools: Tool[]
): string;

function buildYoloSystemPrompt(context: ToolUseContext): string;

function isTwoStageClassifierEnabled(): boolean;

function logAutoModeOutcome(
  outcome: YoloClassificationResult,
  model: string,
  extra: Record<string, any>
): void;

// ============ ClassifierApprovalsHook ============

function useIsClassifierChecking(toolUseID: string): boolean;
```

### 3.2 输入输出规范

**createPermissionContext 输入**：
```typescript
{
  tool: { name: 'Bash', description: '...' },
  input: { command: 'rm -rf /tmp/test' },
  toolUseContext: { cwd: '/project', ... },
  assistantMessage: { role: 'assistant', content: [...] },
  toolUseID: 'toolu_abc123',
  setToolPermissionContext: (ctx) => { /* React setState */ }
}
```

**createPermissionContext 输出**：
```typescript
{
  mode: 'default',
  rules: [
    { type: 'allow', tool: 'Read', pathPattern: 'src/**' },
    { type: 'deny', tool: 'Bash', condition: 'dangerous' }
  ],
  confirmQueue: [],
  toolUseID: 'toolu_abc123',
  tool: { name: 'Bash', ... },
  input: { command: 'rm -rf /tmp/test' },
  assistantMessage: { ... }
}
```

**classifyYoloAction 输入**：
```typescript
{
  messages: [
    { role: 'user', content: 'Delete all test files' },
    { role: 'assistant', content: [...] }
  ],
  action: {
    type: 'tool_use',
    name: 'Bash',
    input: { command: 'rm -rf test/' }
  },
  tools: [{ name: 'Bash', ... }, ...],
  context: { cwd: '/project', ... },
  signal: AbortSignal
}
```

**classifyYoloAction 输出**：
```typescript
{
  decision: 'deny',
  reasoning: 'Recursive deletion without confirmation is high risk',
  confidence: 0.95,
  stage: 1
}
```

### 3.3 错误处理

```typescript
// 权限拒绝错误
class PermissionDeniedError extends Error {
  constructor(
    public tool: string,
    public reason: string,
    public rule?: PermissionRule
  ) {
    super(`Permission denied for ${tool}: ${reason}`);
  }
}

// 分类器超时错误
class ClassifierTimeoutError extends Error {
  constructor(public toolUseID: string) {
    super(`YOLO classifier timeout for ${toolUseID}`);
  }
}

// 规则解析错误
class RuleParseError extends Error {
  constructor(public ruleText: string, public parseError: string) {
    super(`Failed to parse rule: ${parseError}`);
  }
}

// 错误处理策略
try {
  const context = createPermissionContext(...);
  const decision = await checkPermission(context);
  if (decision === 'DENY') {
    throw new PermissionDeniedError(tool.name, 'Rule matched');
  }
} catch (error) {
  if (error instanceof PermissionDeniedError) {
    // 显示拒绝原因给用户
    showPermissionDenied(error.tool, error.reason);
  } else if (error instanceof ClassifierTimeoutError) {
    // 降级到请求确认
    requestUserConfirmation(error.toolUseID);
  } else {
    // 未知错误，默认拒绝
    throw error;
  }
}
```

---

## 4. 实现要点

### 4.1 YOLO Classifier 双阶段设计

**Stage 1：快速分类（~500ms）**

```typescript
// 构建压缩的对话历史
function buildTranscriptForClassifier(
  messages: Message[],
  tools: Tool[]
): string {
  // 只保留最近 N 条消息
  const recentMessages = messages.slice(-10);
  
  // 移除大型工具输出
  const compactMessages = recentMessages.map(msg => {
    if (msg.role === 'tool' && msg.content.length > 1000) {
      return { ...msg, content: msg.content.slice(0, 1000) + '...' };
    }
    return msg;
  });
  
  return JSON.stringify(compactMessages);
}

// 构建分类器系统提示
function buildYoloSystemPrompt(context: ToolUseContext): string {
  return `You are a security classifier for an AI agent.

Your task: Determine if the following tool call is safe to execute automatically.

Context:
- Working directory: ${context.cwd}
- User trust level: ${context.trustLevel || 'unknown'}
- Previous approvals: ${context.approvalHistory?.length || 0}

Classification criteria:
- ALLOW: Safe operations (read files, list directories, non-destructive commands)
- DENY: Dangerous operations (delete files, modify system, network requests to unknown hosts)
- UNCERTAIN: Ambiguous cases that need human judgment

Output format:
<decision>allow|deny|uncertain</decision>
<reasoning>Brief explanation</reasoning>
<confidence>0.0-1.0</confidence>`;
}

// Stage 1 分类
async function classifyStage1(
  action: ToolCall,
  context: ToolUseContext
): Promise<YoloClassificationResult> {
  const transcript = buildTranscriptForClassifier(messages, tools);
  const systemPrompt = buildYoloSystemPrompt(context);
  
  const response = await queryLLM({
    model: 'claude-3-haiku',
    systemPrompt,
    messages: [
      { role: 'user', content: `Classify this action:\n${JSON.stringify(action)}` }
    ],
    maxTokens: 200,
    temperature: 0
  });
  
  return parseClassificationResponse(response, 1);
}
```

**Stage 2：精细分析（~2s，仅在 uncertain 时触发）**

```typescript
async function classifyStage2(
  action: ToolCall,
  context: ToolUseContext,
  stage1Result: YoloClassificationResult
): Promise<YoloClassificationResult> {
  // 更详细的上下文
  const detailedContext = {
    ...context,
    fileTree: await getFileTree(context.cwd),
    gitStatus: await getGitStatus(context.cwd),
    recentChanges: await getRecentFileChanges(context.cwd)
  };
  
  const systemPrompt = buildYoloSystemPrompt(detailedContext) + `

Stage 1 result: ${stage1Result.decision} (confidence: ${stage1Result.confidence})
Stage 1 reasoning: ${stage1Result.reasoning}

Please perform a deeper analysis considering:
1. Impact on project structure
2. Reversibility of the operation
3. Potential data loss
4. Security implications

Be more conservative in Stage 2. When in doubt, choose DENY or request confirmation.`;
  
  const response = await queryLLM({
    model: 'claude-3-haiku',
    systemPrompt,
    messages: [
      { role: 'user', content: `Deep analysis:\n${JSON.stringify(action)}` }
    ],
    maxTokens: 500,
    temperature: 0
  });
  
  return parseClassificationResponse(response, 2);
}
```

**双阶段协调**

```typescript
async function classifyYoloAction(
  messages: Message[],
  action: ToolCall,
  tools: Tool[],
  context: ToolUseContext,
  signal: AbortSignal
): Promise<YoloClassificationResult> {
  // Stage 1
  const stage1 = await classifyStage1(action, context);
  
  // 高置信度决策直接返回
  if (stage1.confidence > 0.9 && stage1.decision !== 'uncertain') {
    logAutoModeOutcome(stage1, 'claude-3-haiku', { stage: 1 });
    return stage1;
  }
  
  // 低置信度或不确定，进入 Stage 2
  if (isTwoStageClassifierEnabled()) {
    const stage2 = await classifyStage2(action, context, stage1);
    logAutoModeOutcome(stage2, 'claude-3-haiku', { stage: 2, stage1 });
    return stage2;
  }
  
  // 未启用双阶段，降级到请求确认
  return {
    decision: 'uncertain',
    reasoning: 'Low confidence, requesting user confirmation',
    confidence: stage1.confidence,
    stage: 1
  };
}
```

### 4.2 权限规则匹配引擎

```typescript
// 路径模式匹配（支持 glob）
function matchPathPattern(rule: PermissionRule, path: string): boolean {
  if (!rule.pathPattern) return true;
  
  // 使用 minimatch 或类似库
  return minimatch(path, rule.pathPattern, { dot: true });
}

// 工具名称匹配
function matchToolName(rule: PermissionRule, tool: Tool): boolean {
  if (!rule.tool) return true;
  
  // 支持通配符
  if (rule.tool.includes('*')) {
    const regex = new RegExp(rule.tool.replace('*', '.*'));
    return regex.test(tool.name);
  }
  
  return rule.tool === tool.name;
}

// 条件表达式求值
function evaluateCondition(
  rule: PermissionRule,
  context: ToolPermissionContext
): boolean {
  if (!rule.condition) return true;
  
  try {
    // 安全的表达式求值（使用沙箱）
    const sandbox = {
      tool: context.tool,
      input: context.input,
      cwd: context.toolUseContext.cwd,
      // 辅助函数
      includes: (str: string, substr: string) => str.includes(substr),
      matches: (str: string, pattern: string) => new RegExp(pattern).test(str)
    };
    
    // 使用 vm2 或类似的安全沙箱
    return evaluateInSandbox(rule.condition, sandbox);
  } catch (error) {
    console.error('Rule condition evaluation failed:', error);
    return false;
  }
}

// 规则匹配主函数
function findMatchingRule(
  rules: PermissionRule[],
  context: ToolPermissionContext
): PermissionRule | null {
  for (const rule of rules) {
    const toolMatch = matchToolName(rule, context.tool);
    const pathMatch = matchPathPattern(rule, context.input.path || '');
    const conditionMatch = evaluateCondition(rule, context);
    
    if (toolMatch && pathMatch && conditionMatch) {
      return rule;
    }
  }
  
  return null;
}
```

### 4.3 动态规则学习与持久化

```typescript
// 从用户批准中提取规则建议
function createReadRuleSuggestion(
  dirPath: string,
  destination: string
): PermissionUpdate {
  return {
    action: 'add_rule',
    rule: {
      type: 'allow',
      tool: 'Read',
      pathPattern: `${dirPath}/**`,
      reason: `Auto-generated: User approved reading from ${dirPath}`
    },
    persist: true
  };
}

// 持久化规则到 CLAUDE.md
async function persistPermissionUpdate(
  update: PermissionUpdate
): Promise<void> {
  if (!update.persist || !update.rule) return;
  
  const claudeMdPath = path.join(process.cwd(), 'CLAUDE.md');
  
  // 读取现有内容
  let content = '';
  try {
    content = await fs.readFile(claudeMdPath, 'utf-8');
  } catch (error) {
    // CLAUDE.md 不存在，创建新文件
    content = '# Project Configuration\n\n';
  }
  
  // 查找或创建 permissions 部分
  const permissionsSection = '## Permissions\n\n';
  if (!content.includes(permissionsSection)) {
    content += '\n' + permissionsSection;
  }
  
  // 格式化规则
  const ruleText = formatPermissionRule(update.rule);
  
  // 插入规则（避免重复）
  if (!content.includes(ruleText)) {
    const insertPos = content.indexOf(permissionsSection) + permissionsSection.length;
    content = content.slice(0, insertPos) + ruleText + '\n' + content.slice(insertPos);
  }
  
  // 写回文件
  await fs.writeFile(claudeMdPath, content, 'utf-8');
}

// 格式化规则为 Markdown
function formatPermissionRule(rule: PermissionRule): string {
  const parts = [`- **${rule.type}**`];
  
  if (rule.tool) parts.push(`tool: \`${rule.tool}\``);
  if (rule.pathPattern) parts.push(`path: \`${rule.pathPattern}\``);
  if (rule.condition) parts.push(`condition: \`${rule.condition}\``);
  if (rule.reason) parts.push(`// ${rule.reason}`);
  
  return parts.join(' ');
}
```

### 4.4 UI 集成：ClassifierApprovalsHook

```typescript
// React Hook：检查分类器是否正在审查工具调用
function useIsClassifierChecking(toolUseID: string): boolean {
  const [checkingTools, setCheckingTools] = useState<Set<string>>(new Set());
  
  useEffect(() => {
    // 订阅分类器状态变化
    const unsubscribe = subscribeToClassifierStatus((status) => {
      if (status.toolUseID === toolUseID) {
        if (status.stage === 'checking') {
          setCheckingTools(prev => new Set(prev).add(toolUseID));
        } else {
          setCheckingTools(prev => {
            const next = new Set(prev);
            next.delete(toolUseID);
            return next;
          });
        }
      }
    });
    
    return unsubscribe;
  }, [toolUseID]);
  
  return checkingTools.has(toolUseID);
}

// UI 组件示例
function ToolCallStatus({ toolUseID, tool, input }) {
  const isChecking = useIsClassifierChecking(toolUseID);
  
  if (isChecking) {
    return (
      <div className="tool-status checking">
        <Spinner />
        <span>Security check in progress...</span>
      </div>
    );
  }
  
  return (
    <div className="tool-status ready">
      <span>{tool.name}</span>
      <code>{JSON.stringify(input)}</code>
    </div>
  );
}
```

### 4.5 边界情况处理

**情况 1：分类器超时**
```typescript
async function classifyWithTimeout(
  action: ToolCall,
  context: ToolUseContext,
  timeoutMs: number = 5000
): Promise<YoloClassificationResult> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new ClassifierTimeoutError(action.id)), timeoutMs);
  });
  
  try {
    return await Promise.race([
      classifyYoloAction(messages, action, tools, context, signal),
      timeoutPromise
    ]);
  } catch (error) {
    if (error instanceof ClassifierTimeoutError) {
      // 降级策略：请求用户确认
      return {
        decision: 'uncertain',
        reasoning: 'Classifier timeout, requesting user confirmation',
        confidence: 0,
        stage: 1
      };
    }
    throw error;
  }
}
```

**情况 2：规则冲突**
```typescript
function resolveRuleConflict(
  rules: PermissionRule[],
  context: ToolPermissionContext
): PermissionRule {
  const matchingRules = rules.filter(rule => 
    matchToolName(rule, context.tool) &&
    matchPathPattern(rule, context.input.path || '') &&
    evaluateCondition(rule, context)
  );
  
  if (matchingRules.length === 0) {
    return null;
  }
  
  if (matchingRules.length === 1) {
    return matchingRules[0];
  }
  
  // 多个规则匹配：优先级策略
  // 1. deny 优先于 allow
  const denyRules = matchingRules.filter(r => r.type === 'deny');
  if (denyRules.length > 0) {
    return denyRules[0];
  }
  
  // 2. 更具体的规则优先（路径模式更长）
  return matchingRules.sort((a, b) => {
    const aLen = a.pathPattern?.length || 0;
    const bLen = b.pathPattern?.length || 0;
    return bLen - aLen;
  })[0];
}
```

**情况 3：read-only 模式的写操作检测**
```typescript
const READ_ONLY_TOOLS = new Set(['Read', 'Glob', 'Grep', 'WebSearch', 'WebFetch']);

function isReadOnlyTool(tool: Tool): boolean {
  return READ_ONLY_TOOLS.has(tool.name);
}

function checkReadOnlyMode(context: ToolPermissionContext): PermissionDecision {
  if (context.mode !== 'read-only') {
    return PermissionDecision.ALLOW;
  }
  
  if (isReadOnlyTool(context.tool)) {
    return PermissionDecision.ALLOW;
  }
  
  // 拒绝所有写操作
  throw new PermissionDeniedError(
    context.tool.name,
    'Write operations are not allowed in read-only mode'
  );
}
```

---

## 5. 设计决策

### 5.1 为什么选择管道式设计？

**传统门禁模型的问题**：
```
User Input → Agent → [Permission Gate] → Tool Execution
                           ↑
                      单点检查，二元决策
```

问题：
- 权限检查与执行流程脱节
- 无法利用执行上下文信息
- 难以实现动态学习
- 用户体验割裂（突然弹窗）

**管道式设计的优势**：
```
User Input → Agent → [Permission Pipeline] → Tool Execution
                      ↓    ↓    ↓    ↓
                    规则  模式  分类  学习
```

优势：
- 权限检查是执行流的一部分
- 每个阶段都可以访问完整上下文
- 支持多级决策（allow/deny/uncertain）
- 可以在管道中注入学习逻辑
- 用户体验流畅（渐进式确认）

### 5.2 为什么需要四级模式？

**单一模式的困境**：
- 只有 `default`：每个操作都确认 → 用户疲劳
- 只有 `auto`：完全自动 → 安全风险
- 只有 `read-only`：无法执行任何操作 → 功能受限

**四级模式的设计理念**：
- `read-only`：探索阶段，零风险
- `default`：学习阶段，建立信任
- `plan`：批量操作，减少打断
- `auto`：信任阶段，高效执行

用户可以根据任务性质和信任程度动态切换，而不是被锁定在单一模式。

### 5.3 为什么用 LLM 做分类器？

**传统规则引擎的局限**：
```python
# 规则爆炸
if command.startswith('rm'):
    if '-rf' in command:
        if not command.startswith('rm -rf /tmp'):
            return 'deny'
# 无法处理变体
# rm -r -f /
# rm -rf / --no-preserve-root
# find . -delete
```

**LLM 分类器的优势**：
- 理解操作意图，而非匹配字符串
- 处理无限变体（`rm -rf` vs `find . -delete`）
- 考虑上下文（删除 `/tmp/test` vs 删除 `/`）
- 可以解释决策（reasoning）

**成本权衡**：
- Haiku 调用成本：~$0.0001/次
- 用户时间成本：~$1/分钟（假设 $60/小时）
- 如果分类器节省 1 秒用户时间，ROI = 10000x

### 5.4 为什么需要双阶段分类？

**单阶段的问题**：
- 快速但不准确 → 误报/漏报
- 准确但太慢 → 用户等待

**双阶段的权衡**：
- Stage 1：快速过滤（90% 的情况）
- Stage 2：精细分析（10% 的不确定情况）

**实测数据**（假设）：
- Stage 1 平均延迟：500ms
- Stage 2 平均延迟：2s
- Stage 2 触发率：10%
- 平均延迟：500ms + 10% × 2s = 700ms

相比单阶段精细分析（2s），节省 65% 时间。

### 5.5 权衡取舍

| 设计选择 | 优势 | 劣势 | 决策 |
|---------|------|------|------|
| **管道式 vs 门禁式** | 灵活、可扩展、上下文丰富 | 实现复杂 | ✅ 管道式 |
| **四级模式 vs 二级模式** | 适应不同场景 | 用户需要理解模式 | ✅ 四级模式 |
| **LLM 分类器 vs 规则引擎** | 智能、适应性强 | 成本、延迟 | ✅ LLM 分类器 |
| **双阶段 vs 单阶段** | 平衡速度和准确性 | 实现复杂 | ✅ 双阶段 |
| **动态学习 vs 静态规则** | 减少重复确认 | 可能学到错误规则 | ✅ 动态学习 + 用户审查 |

### 5.6 可选方案

**方案 A：基于角色的权限（RBAC）**
```typescript
roles = {
  'developer': ['Read', 'Write', 'Bash'],
  'reviewer': ['Read', 'Grep'],
  'admin': ['*']
}
```
- 优势：简单、清晰
- 劣势：不够灵活，无法处理细粒度权限
- 决策：❌ 不适合 Agent 场景

**方案 B：基于能力的权限（Capability-based）**
```typescript
capabilities = [
  { action: 'read', resource: 'file:///project/**' },
  { action: 'write', resource: 'file:///project/src/**' }
]
```
- 优势：细粒度、安全
- 劣势：配置复杂、用户难以理解
- 决策：❌ 过于复杂

**方案 C：混合模式（当前方案）**
- 规则引擎（静态）+ LLM 分类器（动态）
- 四级模式（粗粒度）+ 规则（细粒度）
- 优势：平衡灵活性和可控性
- 决策：✅ 采用

---

## 6. 参考实现

### 6.1 Claude Code 源码位置

```
src/
├── permissions/
│   ├── PermissionContext.ts          # 权限上下文创建
│   ├── PermissionUpdate.ts           # 动态权限更新
│   ├── yoloClassifier.ts             # YOLO 分类器
│   ├── classifierApprovalsHook.ts    # UI 集成 Hook
│   └── permissionRules.ts            # 规则匹配引擎
├── security/
│   ├── treeSitterAnalysis.ts         # Bash 命令 AST 分析
│   ├── ssrfGuard.ts                  # SSRF 防护
│   └── gitSafety.ts                  # Git 安全检查
└── repl/
    └── REPL.tsx                      # 权限系统集成点
```

### 6.2 关键函数签名

```typescript
// PermissionContext.ts
export function createPermissionContext(
  tool: Tool,
  input: any,
  toolUseContext: ToolUseContext,
  assistantMessage: Message,
  toolUseID: string,
  setToolPermissionContext: (ctx: ToolPermissionContext) => void
): ToolPermissionContext;

export function createPermissionQueueOps(
  setToolUseConfirmQueue: (queue: ToolUseConfirm[]) => void
): PermissionQueueOps;

// PermissionUpdate.ts
export function extractRules(updates: PermissionUpdate[]): PermissionRule[];
export function applyPermissionUpdate(
  context: ToolPermissionContext,
  update: PermissionUpdate
): ToolPermissionContext;
export function persistPermissionUpdate(update: PermissionUpdate): Promise<void>;
export function createReadRuleSuggestion(
  dirPath: string,
  destination: string
): PermissionUpdate;

// yoloClassifier.ts
export async function classifyYoloAction(
  messages: Message[],
  action: ToolCall,
  tools: Tool[],
  context: ToolUseContext,
  signal: AbortSignal
): Promise<YoloClassificationResult>;

export function buildTranscriptForClassifier(
  messages: Message[],
  tools: Tool[]
): string;

export function buildYoloSystemPrompt(context: ToolUseContext): string;
export function isTwoStageClassifierEnabled(): boolean;
export function logAutoModeOutcome(
  outcome: YoloClassificationResult,
  model: string,
  extra: Record<string, any>
): void;

// classifierApprovalsHook.ts
export function useIsClassifierChecking(toolUseID: string): boolean;
```

### 6.3 设计模式应用

**模式 1：责任链模式（Chain of Responsibility）**
```typescript
// 权限检查链
class PermissionChecker {
  private next: PermissionChecker | null = null;
  
  setNext(checker: PermissionChecker): PermissionChecker {
    this.next = checker;
    return checker;
  }
  
  async check(context: ToolPermissionContext): Promise<PermissionDecision> {
    const decision = await this.doCheck(context);
    
    if (decision === PermissionDecision.ALLOW && this.next) {
      return this.next.check(context);
    }
    
    return decision;
  }
  
  protected abstract doCheck(context: ToolPermissionContext): Promise<PermissionDecision>;
}

// 具体检查器
class RuleChecker extends PermissionChecker {
  protected async doCheck(context: ToolPermissionContext): Promise<PermissionDecision> {
    const rule = findMatchingRule(context.rules, context);
    if (rule) {
      return rule.type === 'allow' ? PermissionDecision.ALLOW : PermissionDecision.DENY;
    }
    return PermissionDecision.ALLOW; // 继续下一个检查器
  }
}

class ModeChecker extends PermissionChecker {
  protected async doCheck(context: ToolPermissionContext): Promise<PermissionDecision> {
    if (context.mode === 'read-only') {
      return checkReadOnlyMode(context);
    }
    return PermissionDecision.ALLOW;
  }
}

class YoloChecker extends PermissionChecker {
  protected async doCheck(context: ToolPermissionContext): Promise<PermissionDecision> {
    if (context.mode === 'auto') {
      const result = await classifyYoloAction(...);
      return result.decision === 'allow' ? PermissionDecision.ALLOW : PermissionDecision.DENY;
    }
    return PermissionDecision.ALLOW;
  }
}

// 构建检查链
const checker = new RuleChecker()
  .setNext(new ModeChecker())
  .setNext(new YoloChecker());
```

**模式 2：策略模式（Strategy Pattern）**
```typescript
// 不同模式的决策策略
interface PermissionStrategy {
  decide(context: ToolPermissionContext): Promise<PermissionDecision>;
}

class ReadOnlyStrategy implements PermissionStrategy {
  async decide(context: ToolPermissionContext): Promise<PermissionDecision> {
    return isReadOnlyTool(context.tool) 
      ? PermissionDecision.ALLOW 
      : PermissionDecision.DENY;
  }
}

class DefaultStrategy implements PermissionStrategy {
  async decide(context: ToolPermissionContext): Promise<PermissionDecision> {
    return PermissionDecision.REQUEST_CONFIRM;
  }
}

class AutoStrategy implements PermissionStrategy {
  async decide(context: ToolPermissionContext): Promise<PermissionDecision> {
    const result = await classifyYoloAction(...);
    return result.decision === 'allow' 
      ? PermissionDecision.ALLOW 
      : PermissionDecision.REQUEST_CONFIRM;
  }
}

// 策略选择器
class PermissionStrategySelector {
  private strategies = new Map<PermissionMode, PermissionStrategy>([
    ['read-only', new ReadOnlyStrategy()],
    ['default', new DefaultStrategy()],
    ['auto', new AutoStrategy()]
  ]);
  
  getStrategy(mode: PermissionMode): PermissionStrategy {
    return this.strategies.get(mode) || new DefaultStrategy();
  }
}
```

**模式 3：观察者模式（Observer Pattern）**
```typescript
// 权限决策事件
interface PermissionObserver {
  onPermissionGranted(context: ToolPermissionContext): void;
  onPermissionDenied(context: ToolPermissionContext, reason: string): void;
  onPermissionPending(context: ToolPermissionContext): void;
}

class PermissionSubject {
  private observers: PermissionObserver[] = [];
  
  attach(observer: PermissionObserver): void {
    this.observers.push(observer);
  }
  
  detach(observer: PermissionObserver): void {
    const index = this.observers.indexOf(observer);
    if (index > -1) {
      this.observers.splice(index, 1);
    }
  }
  
  notifyGranted(context: ToolPermissionContext): void {
    for (const observer of this.observers) {
      observer.onPermissionGranted(context);
    }
  }
  
  notifyDenied(context: ToolPermissionContext, reason: string): void {
    for (const observer of this.observers) {
      observer.onPermissionDenied(context, reason);
    }
  }
}

// 具体观察者：规则学习器
class RuleLearningObserver implements PermissionObserver {
  onPermissionGranted(context: ToolPermissionContext): void {
    // 建议创建规则
    const suggestion = createReadRuleSuggestion(context.input.path, 'CLAUDE.md');
    showRuleSuggestion(suggestion);
  }
  
  onPermissionDenied(context: ToolPermissionContext, reason: string): void {
    // 记录拒绝原因，用于改进分类器
    logDenialReason(context, reason);
  }
  
  onPermissionPending(context: ToolPermissionContext): void {
    // 显示等待 UI
  }
}
```

---

## 7. 实现检查清单

### 7.1 必须实现的功能

**核心权限系统**
- [ ] `PermissionContext` 创建和管理
- [ ] 四级权限模式（read-only, default, plan, auto）
- [ ] 权限规则匹配引擎（工具名、路径模式、条件表达式）
- [ ] 权限决策状态机（ALLOW/DENY/REQUEST_CONFIRM/CHECKING/PENDING）

**YOLO Classifier**
- [ ] Stage 1 快速分类（~500ms）
- [ ] Stage 2 精细分析（仅在 uncertain 时触发）
- [ ] 对话历史压缩（`buildTranscriptForClassifier`）
- [ ] 分类器系统提示构建（`buildYoloSystemPrompt`）
- [ ] 分类结果解析（decision/reasoning/confidence）

**动态规则学习**
- [ ] 从用户批准中提取规则建议
- [ ] 规则持久化到 CLAUDE.md
- [ ] 规则冲突解决（deny 优先、更具体优先）
- [ ] 规则格式化和解析

**UI 集成**
- [ ] 权限确认队列（`confirmQueue`）
- [ ] 分类器检查状态显示（`useIsClassifierChecking`）
- [ ] 规则建议 UI
- [ ] 权限拒绝错误提示

**错误处理**
- [ ] `PermissionDeniedError`
- [ ] `ClassifierTimeoutError`
- [ ] `RuleParseError`
- [ ] 降级策略（分类器失败 → 请求确认）

### 7.2 可选的优化

**性能优化**
- [ ] 规则缓存（避免重复解析 CLAUDE.md）
- [ ] 分类器结果缓存（相同操作不重复分类）
- [ ] 批量权限检查（plan 模式）
- [ ] 异步分类（不阻塞 UI）

**安全增强**
- [ ] TreeSitter AST 分析（Bash 命令）
- [ ] SSRF 防护（网络请求）
- [ ] Git 安全检查（.git 路径保护）
- [ ] 路径遍历防护（`../` 检测）

**用户体验**
- [ ] 权限模式快速切换（快捷键）
- [ ] 批量批准（选择多个待确认操作）
- [ ] 权限历史记录（审计日志）
- [ ] 规则模板（常见场景预设）

**可观测性**
- [ ] 权限决策遥测（`logAutoModeOutcome`）
- [ ] 分类器性能监控（延迟、准确率）
- [ ] 规则匹配统计（命中率）
- [ ] 用户行为分析（批准/拒绝比例）

### 7.3 测试验证点

**单元测试**
```typescript
describe('PermissionContext', () => {
  test('创建权限上下文', () => {
    const context = createPermissionContext(...);
    expect(context.mode).toBe('default');
    expect(context.rules).toBeInstanceOf(Array);
  });
  
  test('规则匹配：工具名', () => {
    const rule = { type: 'allow', tool: 'Read' };
    expect(matchToolName(rule, { name: 'Read' })).toBe(true);
    expect(matchToolName(rule, { name: 'Write' })).toBe(false);
  });
  
  test('规则匹配：路径模式', () => {
    const rule = { type: 'allow', pathPattern: 'src/**/*.ts' };
    expect(matchPathPattern(rule, 'src/index.ts')).toBe(true);
    expect(matchPathPattern(rule, 'test/index.ts')).toBe(false);
  });
  
  test('规则冲突解决：deny 优先', () => {
    const rules = [
      { type: 'allow', tool: 'Bash' },
      { type: 'deny', tool: 'Bash', condition: 'dangerous' }
    ];
    const resolved = resolveRuleConflict(rules, context);
    expect(resolved.type).toBe('deny');
  });
});

describe('YOLO Classifier', () => {
  test('Stage 1 快速分类', async () => {
    const result = await classifyStage1(action, context);
    expect(result.decision).toMatch(/allow|deny|uncertain/);
    expect(result.confidence).toBeGreaterThanOrEqual(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
  });
  
  test('高置信度跳过 Stage 2', async () => {
    const result = await classifyYoloAction(...);
    if (result.confidence > 0.9) {
      expect(result.stage).toBe(1);
    }
  });
  
  test('分类器超时降级', async () => {
    const result = await classifyWithTimeout(action, context, 100);
    // 应该在 100ms 内返回或降级
    expect(result).toBeDefined();
  });
});

describe('PermissionUpdate', () => {
  test('提取规则', () => {
    const updates = [
      { action: 'add_rule', rule: { type: 'allow', tool: 'Read' } },
      { action: 'change_mode', mode: 'auto' }
    ];
    const rules = extractRules(updates);
    expect(rules).toHaveLength(1);
  });
  
  test('持久化规则到 CLAUDE.md', async () => {
    const update = {
      action: 'add_rule',
      rule: { type: 'allow', tool: 'Read', pathPattern: 'src/**' },
      persist: true
    };
    await persistPermissionUpdate(update);
    
    const content = await fs.readFile('CLAUDE.md', 'utf-8');
    expect(content).toContain('allow');
    expect(content).toContain('Read');
  });
});
```

**集成测试**
```typescript
describe('Permission Pipeline', () => {
  test('read-only 模式拒绝写操作', async () => {
    const context = createPermissionContext({
      mode: 'read-only',
      tool: { name: 'Write' },
      input: { path: 'test.txt', content: 'hello' }
    });
    
    await expect(checkPermission(context)).rejects.toThrow(PermissionDeniedError);
  });
  
  test('default 模式请求确认', async () => {
    const context = createPermissionContext({
      mode: 'default',
      tool: { name: 'Bash' },
      input: { command: 'ls -la' }
    });
    
    const decision = await checkPermission(context);
    expect(decision).toBe(PermissionDecision.REQUEST_CONFIRM);
  });
  
  test('auto 模式调用分类器', async () => {
    const context = createPermissionContext({
      mode: 'auto',
      tool: { name: 'Bash' },
      input: { command: 'echo hello' }
    });
    
    const decision = await checkPermission(context);
    expect([PermissionDecision.ALLOW, PermissionDecision.REQUEST_CONFIRM]).toContain(decision);
  });
  
  test('规则匹配优先于模式', async () => {
    const context = createPermissionContext({
      mode: 'auto',
      rules: [{ type: 'deny', tool: 'Bash' }],
      tool: { name: 'Bash' },
      input: { command: 'ls' }
    });
    
    await expect(checkPermission(context)).rejects.toThrow(PermissionDeniedError);
  });
});
```

**端到端测试**
```typescript
describe('E2E: Permission Flow', () => {
  test('用户批准后创建规则建议', async () => {
    // 1. 工具调用触发权限检查
    const toolCall = { name: 'Read', input: { path: 'src/index.ts' } };
    const context = createPermissionContext(toolCall);
    
    // 2. 请求用户确认
    const decision = await checkPermission(context);
    expect(decision).toBe(PermissionDecision.REQUEST_CONFIRM);
    
    // 3. 用户批准
    await approveToolCall(context.toolUseID);
    
    // 4. 系统建议创建规则
    const suggestion = createReadRuleSuggestion('src', 'CLAUDE.md');
    expect(suggestion.rule.pathPattern).toBe('src/**');
    
    // 5. 用户接受建议，规则持久化
    await persistPermissionUpdate(suggestion);
    
    // 6. 下次相同操作直接通过
    const context2 = createPermissionContext(toolCall);
    const decision2 = await checkPermission(context2);
    expect(decision2).toBe(PermissionDecision.ALLOW);
  });
});
```

### 7.4 性能基准

| 操作 | 目标延迟 | 说明 |
|------|---------|------|
| 规则匹配 | < 1ms | 内存操作，应该极快 |
| Stage 1 分类 | < 500ms | Haiku 快速推理 |
| Stage 2 分类 | < 2s | 精细分析，可接受 |
| 规则持久化 | < 100ms | 文件写入，异步执行 |
| UI 状态更新 | < 16ms | 60fps 要求 |

### 7.5 安全审查清单

- [ ] 规则条件表达式在沙箱中执行（防止代码注入）
- [ ] 路径模式匹配防止遍历攻击（`../`）
- [ ] 分类器系统提示防止提示注入
- [ ] 权限规则文件权限正确（只有用户可写）
- [ ] 敏感信息不记录到日志（API keys, tokens）
- [ ] 分类器超时不导致拒绝服务
- [ ] 规则冲突解决逻辑安全优先（deny > allow）

---

## 8. 实战案例分析

### 8.1 案例 1：文件删除操作的权限决策

**场景**：用户要求"清理所有测试文件"

```typescript
// LLM 生成的工具调用
const toolCall = {
  type: 'tool_use',
  name: 'Bash',
  input: {
    command: 'find . -name "*.test.ts" -delete'
  }
};
```

**权限决策流程**：

```
1. 创建 PermissionContext
   - mode: 'default'
   - rules: []
   - tool: Bash
   - input: { command: 'find . -name "*.test.ts" -delete' }

2. 规则匹配
   - 无匹配规则 → 继续

3. 模式决策 (default)
   - 请求用户确认
   - UI 显示：
     ┌─────────────────────────────────────┐
     │ 🔧 Bash Command                     │
     │ find . -name "*.test.ts" -delete    │
     │                                     │
     │ ⚠️  This will delete files          │
     │                                     │
     │ [Approve] [Deny] [Always Allow]     │
     └─────────────────────────────────────┘

4. 用户选择 "Always Allow"
   - 执行命令
   - 建议创建规则：
     {
       type: 'allow',
       tool: 'Bash',
       condition: 'input.command.includes("*.test.ts")',
       reason: 'User approved: delete test files'
     }

5. 规则持久化到 CLAUDE.md
   - **allow** tool: `Bash` condition: `input.command.includes("*.test.ts")` // User approved: delete test files

6. 下次相同操作
   - 规则匹配成功 → 直接执行
```

### 8.2 案例 2：Auto 模式下的危险命令拦截

**场景**：在 auto 模式下，LLM 错误地尝试删除整个项目

```typescript
const toolCall = {
  type: 'tool_use',
  name: 'Bash',
  input: {
    command: 'rm -rf .'
  }
};
```

**YOLO Classifier 决策**：

```
1. Stage 1 快速分类
   Input:
   - Command: rm -rf .
   - Context: cwd=/project, mode=auto
   
   Classifier reasoning:
   "Recursive deletion of current directory is extremely dangerous.
    This will delete the entire project including source code.
    High risk operation that should never be auto-approved."
   
   Output:
   - decision: 'deny'
   - confidence: 0.98
   - stage: 1

2. 结果
   - 直接拒绝，不执行
   - 显示错误：
     ❌ Command blocked by security classifier
     Reason: Recursive deletion of current directory
     
     The AI attempted to run: rm -rf .
     This command would delete your entire project.
```

**关键设计**：即使在 auto 模式下，分类器也能拦截明显危险的操作。

### 8.3 案例 3：Read-only 模式的探索性分析

**场景**：代码审查，只读模式下探索代码库

```typescript
// 允许的操作
const allowedCalls = [
  { name: 'Read', input: { path: 'src/index.ts' } },      // ✅
  { name: 'Glob', input: { pattern: '**/*.ts' } },        // ✅
  { name: 'Grep', input: { pattern: 'TODO', path: '.' } } // ✅
];

// 被拒绝的操作
const deniedCalls = [
  { name: 'Write', input: { path: 'notes.md' } },         // ❌
  { name: 'Edit', input: { path: 'src/index.ts' } },      // ❌
  { name: 'Bash', input: { command: 'git commit' } }      // ❌
];
```

**用户体验**：
```
User: "帮我分析这个项目的架构"
Agent: [read-only mode]
  ✅ Reading src/index.ts...
  ✅ Searching for imports...
  ✅ Analyzing file structure...
  
User: "把分析结果写到 analysis.md"
Agent: ❌ Cannot write files in read-only mode
       Tip: Switch to default mode with /mode default
```

### 8.4 案例 4：Plan 模式的批量操作

**场景**：重构多个文件

```typescript
// LLM 生成的执行计划
const plan = [
  { name: 'Edit', input: { path: 'src/a.ts', old: 'foo', new: 'bar' } },
  { name: 'Edit', input: { path: 'src/b.ts', old: 'foo', new: 'bar' } },
  { name: 'Edit', input: { path: 'src/c.ts', old: 'foo', new: 'bar' } },
  { name: 'Bash', input: { command: 'npm test' } }
];
```

**Plan 模式 UI**：
```
┌─────────────────────────────────────────────────┐
│ 📋 Execution Plan (4 steps)                     │
├─────────────────────────────────────────────────┤
│ 1. Edit src/a.ts                                │
│    Replace "foo" with "bar"                     │
│                                                 │
│ 2. Edit src/b.ts                                │
│    Replace "foo" with "bar"                     │
│                                                 │
│ 3. Edit src/c.ts                                │
│    Replace "foo" with "bar"                     │
│                                                 │
│ 4. Run tests                                    │
│    npm test                                     │
├─────────────────────────────────────────────────┤
│ [Approve All] [Review Each] [Cancel]            │
└─────────────────────────────────────────────────┘
```

**优势**：
- 用户一次性看到完整计划
- 减少打断（4 次确认 → 1 次确认）
- 可以在执行前审查整体逻辑

### 8.5 案例 5：规则冲突解决

**场景**：同时存在 allow 和 deny 规则

```typescript
// CLAUDE.md 中的规则
const rules = [
  {
    type: 'allow',
    tool: 'Bash',
    pathPattern: 'scripts/**',
    reason: 'Allow running scripts in scripts/ directory'
  },
  {
    type: 'deny',
    tool: 'Bash',
    condition: 'input.command.includes("rm -rf")',
    reason: 'Never allow recursive deletion'
  }
];

// 工具调用
const toolCall = {
  name: 'Bash',
  input: {
    command: 'cd scripts && rm -rf temp'
  }
};
```

**冲突解决**：
```
1. 匹配规则
   - Rule 1 (allow): ✅ 匹配（在 scripts/ 目录）
   - Rule 2 (deny): ✅ 匹配（包含 rm -rf）

2. 冲突解决策略
   - deny 优先于 allow
   - 结果：拒绝执行

3. 用户提示
   ❌ Permission denied
   
   Matched rules:
   - ✅ Allow: Bash in scripts/** 
   - ❌ Deny: Commands with "rm -rf"
   
   Deny rule takes precedence for safety.
```

### 8.6 案例 6：分类器的上下文理解

**场景 A**：删除临时文件（安全）
```typescript
// 对话上下文
User: "清理构建产物"
Assistant: "好的，我会删除 dist/ 和 .cache/ 目录"

// 工具调用
{ name: 'Bash', input: { command: 'rm -rf dist .cache' } }

// 分类器推理
Context: User explicitly asked to clean build artifacts
Command: rm -rf dist .cache
Analysis: 
  - dist/ and .cache/ are standard build directories
  - User's intent is clear
  - Operation is reversible (can rebuild)
Decision: ALLOW
Confidence: 0.92
```

**场景 B**：删除临时文件（危险）
```typescript
// 对话上下文
User: "帮我优化项目结构"
Assistant: "我会重新组织文件..."

// 工具调用（LLM 错误）
{ name: 'Bash', input: { command: 'rm -rf src' } }

// 分类器推理
Context: User asked to optimize structure, not delete code
Command: rm -rf src
Analysis:
  - src/ typically contains source code
  - No explicit user approval for deletion
  - Operation is destructive and hard to reverse
  - Mismatch between user intent and action
Decision: DENY
Confidence: 0.96
```

**关键洞察**：分类器不仅看命令本身，还理解对话上下文和用户意图。

---

## 9. 高级主题

### 9.1 权限的时间维度

**问题**：用户批准一次操作后，这个批准应该持续多久？

**方案 A：永久批准（当前实现）**
```typescript
// 规则一旦创建，永久有效
{
  type: 'allow',
  tool: 'Bash',
  condition: 'input.command.startsWith("npm test")'
}
```
- 优势：减少重复确认
- 劣势：可能批准过时的操作

**方案 B：会话级批准**
```typescript
{
  type: 'allow',
  tool: 'Bash',
  condition: '...',
  expiresAt: 'session_end'
}
```
- 优势：更安全
- 劣势：每次重启都要重新批准

**方案 C：时间窗口批准**
```typescript
{
  type: 'allow',
  tool: 'Bash',
  condition: '...',
  expiresAt: Date.now() + 24 * 60 * 60 * 1000 // 24小时
}
```
- 优势：平衡安全和便利
- 劣势：需要定期清理过期规则

**Claude Code 的选择**：方案 A（永久批准）+ 用户可手动编辑 CLAUDE.md 删除规则

### 9.2 权限的空间维度

**问题**：权限规则应该在什么范围内生效？

**层级结构**：
```
全局规则 (~/.claude/permissions.md)
  ↓ 覆盖
工作区规则 (/project/CLAUDE.md)
  ↓ 覆盖
子目录规则 (/project/src/CLAUDE.md)
```

**示例**：
```typescript
// 全局：禁止所有 rm -rf
~/.claude/permissions.md:
  - deny: Bash, condition: 'rm -rf'

// 项目：允许删除 node_modules
/project/CLAUDE.md:
  - allow: Bash, command: 'rm -rf node_modules'

// 结果：在 /project 下可以删除 node_modules，但不能删除其他
```

### 9.3 权限的协作维度

**问题**：团队如何共享权限规则？

**方案 A：Git 提交 CLAUDE.md**
```bash
# 团队共享的规则
git add CLAUDE.md
git commit -m "Add permission rules for CI scripts"
```
- 优势：版本控制、代码审查
- 劣势：可能泄露敏感路径

**方案 B：规则模板**
```typescript
// .claude/templates/web-dev.md
## Web Development Permissions
- allow: Bash, command: 'npm *'
- allow: Bash, command: 'yarn *'
- allow: Read, path: 'src/**'
- allow: Write, path: 'src/**'
- deny: Bash, condition: 'rm -rf'
```

用户可以导入模板：
```bash
claude import-permissions web-dev
```

### 9.4 权限与审计

**审计日志格式**：
```json
{
  "timestamp": "2026-04-01T02:20:11.925Z",
  "toolUseID": "toolu_abc123",
  "tool": "Bash",
  "input": { "command": "rm -rf temp" },
  "decision": "allow",
  "reason": "rule_match",
  "rule": {
    "type": "allow",
    "tool": "Bash",
    "pathPattern": "temp/**"
  },
  "user": "jerry_hu",
  "session": "sess_xyz789"
}
```

**审计查询**：
```typescript
// 查询所有被拒绝的操作
const deniedOps = auditLog.filter(log => log.decision === 'deny');

// 查询特定工具的使用
const bashOps = auditLog.filter(log => log.tool === 'Bash');

// 查询高风险操作（分类器拦截）
const highRisk = auditLog.filter(log => 
  log.reason === 'classifier_deny' && log.confidence > 0.9
);
```

### 9.5 权限的机器学习优化

**问题**：能否让系统自动学习用户的权限偏好？

**特征提取**：
```typescript
interface PermissionFeatures {
  tool: string;
  pathDepth: number;
  fileExtension: string;
  commandKeywords: string[];
  timeOfDay: number;
  dayOfWeek: number;
  recentApprovals: number;
  recentDenials: number;
}
```

**训练数据**：
```typescript
const trainingData = [
  {
    features: {
      tool: 'Bash',
      commandKeywords: ['npm', 'test'],
      timeOfDay: 14,
      recentApprovals: 5
    },
    label: 'approve'
  },
  {
    features: {
      tool: 'Bash',
      commandKeywords: ['rm', '-rf'],
      pathDepth: 1,
      recentDenials: 2
    },
    label: 'deny'
  }
];
```

**预测模型**：
```typescript
async function predictPermission(
  features: PermissionFeatures
): Promise<{ decision: string; confidence: number }> {
  // 使用简单的决策树或神经网络
  const model = await loadModel('permission-predictor');
  const prediction = await model.predict(features);
  
  return {
    decision: prediction.label,
    confidence: prediction.probability
  };
}
```

**注意**：这是未来方向，当前 Claude Code 使用 LLM 分类器而非传统 ML。

---

## 10. 总结与最佳实践

### 10.1 核心设计原则回顾

1. **权限即管道**：嵌入执行流，而非外部守卫
2. **分级授权**：四级模式适应不同场景
3. **智能分类**：LLM 理解意图，而非匹配字符串
4. **动态学习**：从用户行为中学习，自动生成规则
5. **安全优先**：deny 优先、双阶段验证、降级策略

### 10.2 实现建议

**DO（推荐）**：
- ✅ 使用管道式设计，让权限检查成为执行流的一部分
- ✅ 实现四级模式，给用户选择权
- ✅ 用 LLM 做分类器，处理复杂场景
- ✅ 双阶段分类，平衡速度和准确性
- ✅ 从用户批准中学习，自动生成规则
- ✅ 规则持久化到项目配置文件
- ✅ 提供清晰的错误提示和建议

**DON'T（避免）**：
- ❌ 不要用简单的白名单/黑名单（无法适应新场景）
- ❌ 不要在分类器中执行不安全的代码
- ❌ 不要忽略分类器超时（需要降级策略）
- ❌ 不要让规则冲突导致不确定行为
- ❌ 不要在日志中记录敏感信息
- ❌ 不要假设用户理解所有技术细节（提供友好提示）

### 10.3 性能优化建议

1. **规则缓存**：避免每次都解析 CLAUDE.md
2. **分类器批处理**：plan 模式下批量分类
3. **异步执行**：分类器不阻塞 UI
4. **结果缓存**：相同操作不重复分类（带 TTL）
5. **预测性加载**：提前加载可能需要的规则

### 10.4 安全加固建议

1. **沙箱执行**：规则条件表达式在隔离环境中求值
2. **输入验证**：路径、命令、参数都要验证
3. **最小权限**：默认拒绝，显式允许
4. **审计日志**：记录所有权限决策
5. **定期审查**：提醒用户审查权限规则

---

**下一步**：阅读 [07-MULTI-AGENT.md](07-MULTI-AGENT.md) 了解多 Agent 编排机制。

