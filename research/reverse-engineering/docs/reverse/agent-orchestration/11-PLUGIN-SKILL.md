# 11. 扩展系统设计：Plugin 与 Skill

## 1. 核心概念

### 1.1 扩展系统的双轨设计

Claude Code 采用 **Plugin（命令式）+ Skill（声明式）** 的双轨扩展架构：

| 维度 | Plugin | Skill |
|------|--------|-------|
| **定义方式** | 代码（TypeScript/JavaScript） | 声明（Markdown + YAML） |
| **能力边界** | 完整的运行时能力（Hook、Command、Agent、Tool） | 提示词增强 + 文件引用 |
| **安全模型** | 信任边界（需要用户审批） | 无代码执行（天然安全） |
| **分发方式** | npm/git/marketplace/local | 文件系统（`.claude/skills/`） |
| **生命周期** | 安装 → 缓存 → 加载 → 验证 → 运行 | 发现 → 解析 → 注入 |
| **典型用例** | MCP 集成、自定义 UI、复杂工作流 | 领域知识、最佳实践、模板 |

**设计动机**：

- **Plugin** 解决"能力扩展"问题 — 当需要新的工具、命令、Hook 时
- **Skill** 解决"知识扩展"问题 — 当需要注入领域知识、指导原则时

### 1.2 关键术语

- **Plugin Manifest**：`plugin.json`，定义插件元数据、依赖、权限
- **Plugin Source**：插件来源（session/marketplace/builtin）
- **Plugin Cache**：版本化缓存目录（`~/.claude/plugins/{id}/{version}/`）
- **Skill Definition**：`SKILL.md`，Markdown 格式的技能定义
- **Skill Tool**：将 Skill 暴露为 LLM 可调用的 Tool
- **Prompt-as-Code**：通过结构化文本定义能力的设计模式

---

## 2. Plugin 系统架构

### 2.1 Plugin 生命周期

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 安装阶段                                                  │
│    npm | git | github | local | marketplace                 │
│    └─> cachePlugin() → resolvePluginPath()                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 缓存阶段                                                  │
│    getVersionedCachePath(pluginId, version)                 │
│    ~/.claude/plugins/{id}/{version}/                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 加载阶段                                                  │
│    loadPluginManifest()  ← 读取 plugin.json                │
│    loadPluginHooks()     ← 加载 Hook 定义                  │
│    loadPluginSettings()  ← 加载配置                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 验证阶段                                                  │
│    validatePluginPaths() ← 检查文件完整性                  │
│    checkPluginTrust()    ← 信任检查                        │
│    checkPluginBlocklist() ← 黑名单检查                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 合并阶段                                                  │
│    mergePluginSources({session, marketplace, builtin})      │
│    优先级: session > marketplace > builtin                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 运行时阶段                                                │
│    loadPluginCommands()      ← 注册斜杠命令                │
│    loadPluginAgents()        ← 注册子 Agent                │
│    loadPluginHooks()         ← 注册 Hook                   │
│    loadPluginOutputStyles()  ← 注册输出样式                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 三层合并策略

Plugin 可以来自三个来源，按优先级合并：

```typescript
interface PluginSources {
  session: Plugin[]      // 会话级插件（最高优先级）
  marketplace: Plugin[]  // 市场插件
  builtin: Plugin[]      // 内置插件（最低优先级）
}

function mergePluginSources(sources: PluginSources): Plugin[] {
  const merged = new Map<string, Plugin>()
  
  // 按优先级逆序合并（后者覆盖前者）
  for (const plugin of sources.builtin) {
    merged.set(plugin.id, plugin)
  }
  for (const plugin of sources.marketplace) {
    merged.set(plugin.id, plugin)  // 覆盖 builtin
  }
  for (const plugin of sources.session) {
    merged.set(plugin.id, plugin)  // 覆盖 marketplace
  }
  
  return Array.from(merged.values())
}
```

**设计洞察**：

- **Session 插件优先级最高** — 用户当前会话的定制优先于全局配置
- **同 ID 插件只保留一个** — 避免冲突和重复注册
- **Builtin 作为兜底** — 确保核心功能始终可用

### 2.3 版本化缓存机制

```typescript
interface PluginCache {
  basePath: string  // ~/.claude/plugins/
  
  getVersionedCachePath(pluginId: string, version: string): string
  // 返回: ~/.claude/plugins/{pluginId}/{version}/
  
  probeSeedCache(pluginId: string, version: string): boolean
  // 检查特定版本是否已缓存
  
  probeSeedCacheAnyVersion(pluginId: string): string | null
  // 查找任意已缓存版本（离线启动）
}
```

**缓存目录结构**：

```
~/.claude/plugins/
├── playwright-plugin/
│   ├── 1.0.0/
│   │   ├── plugin.json
│   │   ├── index.js
│   │   └── hooks/
│   └── 1.1.0/
│       ├── plugin.json
│       └── index.js
└── mcp-integration/
    └── 2.0.0/
        ├── plugin.json
        └── servers/
```

**离线启动支持**：

```typescript
// 优先使用指定版本
let pluginPath = probeSeedCache(pluginId, requestedVersion)

// 降级：使用任意已缓存版本
if (!pluginPath) {
  pluginPath = probeSeedCacheAnyVersion(pluginId)
  if (pluginPath) {
    warn(`Using cached version instead of ${requestedVersion}`)
  }
}
```

---

## 3. Plugin 安全机制

### 3.1 四层安全防护

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Trust Warning                                      │
│   PluginTrustWarning — 首次加载时提示用户                   │
│   "This plugin can execute code. Trust it?"                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Blocklist                                          │
│   pluginBlocklist — 已知恶意插件黑名单                      │
│   拒绝加载，显示警告                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Policy Control                                     │
│   pluginPolicy       — 允许列表（只加载指定插件）           │
│   pluginOnlyPolicy   — 排他模式（只加载这些，拒绝其他）     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: MDM Management                                     │
│   managedPlugins — 企业 MDM 托管插件                        │
│   强制安装、禁止卸载                                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 信任模型

```typescript
interface PluginTrustContext {
  pluginId: string
  source: 'marketplace' | 'npm' | 'git' | 'local'
  firstLoad: boolean
  
  // 信任决策
  isTrusted(): boolean
  requestTrust(): Promise<boolean>
  revokeTrust(): void
}

// 信任决策流程
async function loadPluginWithTrust(plugin: Plugin): Promise<void> {
  const trustCtx = createTrustContext(plugin)
  
  // 1. 检查黑名单
  if (isBlocklisted(plugin.id)) {
    throw new PluginBlockedError(plugin.id)
  }
  
  // 2. 检查策略
  if (!isPolicyAllowed(plugin.id)) {
    throw new PluginPolicyError(plugin.id)
  }
  
  // 3. 检查信任
  if (!trustCtx.isTrusted()) {
    const approved = await trustCtx.requestTrust()
    if (!approved) {
      throw new PluginTrustDeniedError(plugin.id)
    }
  }
  
  // 4. 加载插件
  await loadPlugin(plugin)
}
```

### 3.3 MDM 托管插件

企业环境下的强制插件管理：

```typescript
interface ManagedPlugin {
  id: string
  version: string
  source: string
  mandatory: boolean      // 强制安装
  immutable: boolean      // 禁止卸载/修改
  autoUpdate: boolean     // 自动更新
}

// MDM 策略执行
function enforceManagedPlugins(
  installed: Plugin[],
  managed: ManagedPlugin[]
): void {
  for (const mp of managed) {
    const existing = installed.find(p => p.id === mp.id)
    
    if (!existing && mp.mandatory) {
      // 强制安装缺失的插件
      installPlugin(mp.id, mp.version, mp.source)
    }
    
    if (existing && mp.immutable) {
      // 锁定插件，禁止用户修改
      lockPlugin(mp.id)
    }
    
    if (existing && mp.autoUpdate) {
      // 检查更新
      checkAndUpdatePlugin(mp.id, mp.version)
    }
  }
}
```

---

## 4. Skill 系统架构

### 4.1 Skill 定义格式

Skill 是 **Prompt-as-Code** 的实现，通过结构化 Markdown 定义：

```markdown
---
name: deep-research
description: 企业级深度调研
trigger: 当用户需要全面分析时使用
version: 1.0.0
---

# Deep Research Skill

## 能力

- 多源信息综合
- 引用验证
- 结构化输出

## 使用场景

当用户提出以下需求时触发：
- "调研 XXX"
- "分析 XXX 的市场"
- "对比 A 和 B"

## 执行流程

1. 明确调研目标
2. 制定信息源列表
3. 并行搜索和抓取
4. 交叉验证
5. 生成报告

## 输出格式

使用 Markdown，包含：
- 执行摘要
- 详细分析
- 引用列表

## 内联文件引用

#[[file:templates/research-report.md]]
```

### 4.2 Skill 加载流程

```typescript
interface SkillDefinition {
  name: string
  description: string
  trigger?: string
  content: string           // Markdown 内容
  inlineRefs: string[]      // #[[file:...]] 引用
}

// Skill 加载管线
async function loadSkill(skillPath: string): Promise<SkillDefinition> {
  // 1. 读取 SKILL.md
  const raw = await readFile(skillPath, 'utf-8')
  
  // 2. 解析 Front Matter
  const { frontMatter, content } = parseFrontMatter(raw)
  
  // 3. 处理内联引用
  const { processedContent, refs } = await processInlineReferences(content)
  
  // 4. 构建 Skill 定义
  return {
    name: frontMatter.name,
    description: frontMatter.description,
    trigger: frontMatter.trigger,
    content: processedContent,
    inlineRefs: refs
  }
}
```

### 4.3 内联文件引用机制

Skill 可以引用外部文件，实现知识复用：

```typescript
// 语法: #[[file:relative/path/to/file.md]]
function processInlineReferences(content: string): {
  processedContent: string
  refs: string[]
} {
  const refPattern = /#\[\[file:([^\]]+)\]\]/g
  const refs: string[] = []
  
  const processed = content.replace(refPattern, (match, filePath) => {
    refs.push(filePath)
    
    // 读取并内联文件内容
    const fileContent = readFileSync(filePath, 'utf-8')
    return `\n\n<!-- Inlined from ${filePath} -->\n${fileContent}\n`
  })
  
  return { processedContent: processed, refs }
}
```

**典型用例**：

```markdown
<!-- 在 Skill 中引用 OpenAPI 规范 -->
## API 规范

#[[file:specs/api.openapi.yaml]]

<!-- 在 Skill 中引用代码模板 -->
## 实现模板

#[[file:templates/component.tsx]]
```

### 4.4 SkillTool：将 Skill 暴露为 Tool

```typescript
interface SkillTool extends Tool {
  name: 'Skill'
  description: 'Invoke a specialized skill'
  
  input_schema: {
    skill: string      // Skill 名称
    args?: string      // 可选参数
  }
}

// SkillTool 执行逻辑
async function executeSkillTool(input: {
  skill: string
  args?: string
}): Promise<ToolResult> {
  // 1. 查找 Skill
  const skillDef = findSkill(input.skill)
  if (!skillDef) {
    return { error: `Skill '${input.skill}' not found` }
  }
  
  // 2. 构建增强提示
  const enhancedPrompt = buildPrompt(skillDef, input.args)
  
  // 3. 注入到上下文
  return {
    content: enhancedPrompt,
    metadata: {
      skillName: skillDef.name,
      inlineRefs: skillDef.inlineRefs
    }
  }
}
```

### 4.5 Skillify：元编程的自举设计

`skillify` 是"创建 Skill 的 Skill"，实现自举：

```markdown
---
name: skillify
description: 创建新的 Skill
---

# Skillify - Skill Creator

## 能力

根据用户描述生成 Skill 定义文件。

## 输入

- 领域描述
- 触发场景
- 期望输出格式

## 输出

生成符合规范的 SKILL.md 文件：
1. Front Matter（元数据）
2. 能力说明
3. 使用场景
4. 执行流程
5. 输出格式

## 模板

#[[file:templates/skill-template.md]]
```

**使用示例**：

```
User: 帮我创建一个代码审查的 Skill
Agent: /skillify "创建一个代码审查 Skill，关注安全漏洞和最佳实践"

Skillify 输出:
→ 生成 .claude/skills/code-review-security/SKILL.md
→ 包含 OWASP Top 10 检查清单
→ 引用安全编码规范
```

---

## 5. 实现要点

### 5.1 Plugin 动态加载

```typescript
// Plugin 运行时注册
class PluginRuntime {
  private plugins = new Map<string, LoadedPlugin>()
  
  async loadPlugin(pluginId: string, version: string): Promise<void> {
    // 1. 解析路径
    const pluginPath = resolvePluginPath(pluginId, version)
    
    // 2. 加载 manifest
    const manifest = await loadPluginManifest(pluginPath)
    
    // 3. 验证依赖
    await validateDependencies(manifest.dependencies)
    
    // 4. 加载模块
    const module = await import(path.join(pluginPath, manifest.main))
    
    // 5. 注册能力
    if (manifest.commands) {
      await this.registerCommands(module.commands)
    }
    if (manifest.hooks) {
      await this.registerHooks(module.hooks)
    }
    if (manifest.agents) {
      await this.registerAgents(module.agents)
    }
    
    // 6. 缓存
    this.plugins.set(pluginId, {
      id: pluginId,
      version,
      manifest,
      module
    })
  }
  
  unloadPlugin(pluginId: string): void {
    const plugin = this.plugins.get(pluginId)
    if (!plugin) return
    
    // 清理注册的能力
    this.unregisterCommands(plugin)
    this.unregisterHooks(plugin)
    this.unregisterAgents(plugin)
    
    this.plugins.delete(pluginId)
  }
}
```

### 5.2 Skill 内容处理管线

```typescript
// Skill 内容处理
async function processSkillContent(
  skillDef: SkillDefinition,
  args?: string
): Promise<string> {
  let content = skillDef.content
  
  // 1. 处理内联引用
  content = await expandInlineReferences(content)
  
  // 2. 语言检测与本地化
  const language = detectLanguage(content)
  content = localizeContent(content, language)
  
  // 3. 参数替换
  if (args) {
    content = substituteParameters(content, args)
  }
  
  // 4. 构建最终提示
  return buildPrompt(content, {
    skillName: skillDef.name,
    timestamp: new Date().toISOString()
  })
}

// 内联引用展开
async function expandInlineReferences(content: string): Promise<string> {
  const refPattern = /#\[\[file:([^\]]+)\]\]/g
  const matches = Array.from(content.matchAll(refPattern))
  
  for (const match of matches) {
    const filePath = match[1]
    try {
      const fileContent = await readFile(filePath, 'utf-8')
      content = content.replace(match[0], fileContent)
    } catch (error) {
      console.warn(`Failed to load inline reference: ${filePath}`)
    }
  }
  
  return content
}
```

### 5.3 Plugin 与 Skill 的协同

```typescript
// Plugin 可以注册新的 Skill
interface PluginWithSkills {
  skills: SkillDefinition[]
}

// 在 Plugin 加载时注册 Skill
async function loadPluginWithSkills(plugin: PluginWithSkills): Promise<void> {
  for (const skill of plugin.skills) {
    await registerSkill(skill)
  }
}

// 示例：MCP Plugin 注册 MCP 相关的 Skill
const mcpPlugin = {
  id: 'mcp-integration',
  skills: [
    {
      name: 'mcp-server-setup',
      description: '配置 MCP 服务器',
      content: '...'
    },
    {
      name: 'mcp-tool-discovery',
      description: '发现 MCP 工具',
      content: '...'
    }
  ]
}
```

### 5.4 边界情况处理

**Plugin 加载失败**：

```typescript
async function safeLoadPlugin(pluginId: string): Promise<LoadResult> {
  try {
    await loadPlugin(pluginId)
    return { success: true }
  } catch (error) {
    if (error instanceof PluginNotFoundError) {
      // 插件不存在，尝试从 marketplace 安装
      return { success: false, action: 'install' }
    }
    if (error instanceof PluginVersionMismatchError) {
      // 版本不匹配，尝试使用缓存版本
      return { success: false, action: 'use-cached' }
    }
    if (error instanceof PluginTrustDeniedError) {
      // 用户拒绝信任
      return { success: false, action: 'skip' }
    }
    throw error
  }
}
```

**Skill 循环引用**：

```typescript
// 检测 Skill 内联引用的循环依赖
function detectCircularReferences(
  skillPath: string,
  visited = new Set<string>()
): boolean {
  if (visited.has(skillPath)) {
    return true  // 检测到循环
  }
  
  visited.add(skillPath)
  
  const content = readFileSync(skillPath, 'utf-8')
  const refs = extractInlineReferences(content)
  
  for (const ref of refs) {
    const refPath = resolvePath(skillPath, ref)
    if (detectCircularReferences(refPath, visited)) {
      return true
    }
  }
  
  visited.delete(skillPath)
  return false
}
```

---

## 6. 设计决策

### 6.1 为什么需要双轨扩展？

**单一扩展机制的问题**：

- **纯代码扩展（如 VSCode Extension）**：
  - ✅ 能力强大，可以做任何事
  - ❌ 安全风险高，需要复杂的沙箱
  - ❌ 学习曲线陡峭，普通用户无法创建
  
- **纯声明扩展（如配置文件）**：
  - ✅ 安全，无代码执行
  - ✅ 易于创建和分享
  - ❌ 能力受限，无法实现复杂逻辑

**双轨设计的优势**：

```
能力需求
  ↓
  需要执行代码？
  ├─ 是 → Plugin（命令式）
  │        - 完整运行时能力
  │        - 严格安全审查
  │        - 适合开发者
  │
  └─ 否 → Skill（声明式）
           - 提示词增强
           - 天然安全
           - 适合所有用户
```

### 6.2 为什么 Plugin 需要版本化缓存？

**问题场景**：

1. **离线启动** — 网络不可用时仍能加载插件
2. **版本回退** — 新版本有问题时快速回退
3. **多版本共存** — 不同项目可能依赖不同版本

**设计权衡**：

| 方案 | 优点 | 缺点 |
|------|------|------|
| 不缓存，每次下载 | 始终最新 | 网络依赖，启动慢 |
| 缓存单一版本 | 节省空间 | 无法回退，多版本冲突 |
| **版本化缓存** | 离线可用，支持回退 | 占用空间 |

**最终选择**：版本化缓存 + Seed Cache 探测（离线降级）

### 6.3 为什么 Skill 使用 Markdown？

**Markdown 的优势**：

1. **人类可读** — 非技术用户也能理解和修改
2. **结构化** — Front Matter + 章节结构
3. **工具支持** — 所有编辑器都支持
4. **版本控制友好** — Git diff 清晰可读
5. **内联引用** — 通过 `#[[file:...]]` 实现模块化

**对比其他格式**：

| 格式 | 可读性 | 结构化 | 工具支持 | 学习成本 |
|------|--------|--------|----------|----------|
| JSON | ❌ | ✅ | ✅ | 低 |
| YAML | ⚠️ | ✅ | ✅ | 中 |
| **Markdown** | ✅ | ✅ | ✅ | 低 |
| Python | ❌ | ✅ | ⚠️ | 高 |

### 6.4 三层合并策略的设计理由

**优先级设计**：

```
session > marketplace > builtin
```

**理由**：

1. **Session 最高** — 用户当前会话的定制应该覆盖一切
2. **Marketplace 次之** — 用户主动安装的插件优先于默认
3. **Builtin 兜底** — 确保核心功能始终可用

**冲突解决**：

```typescript
// 同 ID 插件只保留优先级最高的
const plugins = [
  { id: 'foo', source: 'builtin', version: '1.0.0' },
  { id: 'foo', source: 'marketplace', version: '1.1.0' },
  { id: 'foo', source: 'session', version: '1.0.5' }
]

// 合并后只保留 session 版本
merged = [
  { id: 'foo', source: 'session', version: '1.0.5' }
]
```

---

## 7. 参考实现

### 7.1 Claude Code 源码位置

**Plugin 系统**：

```
src/plugins/
├── pluginLoader.ts          # 插件加载器
├── pluginCache.ts           # 版本化缓存
├── pluginManifest.ts        # Manifest 解析
├── pluginSecurity.ts        # 安全检查
├── pluginMerge.ts           # 三层合并
└── types/
    ├── Plugin.ts            # 插件类型定义
    └── PluginManifest.ts    # Manifest 类型
```

**Skill 系统**：

```
src/skills/
├── SkillTool/
│   └── SkillTool.ts         # Skill Tool 实现
├── bundled/
│   ├── claudeApi.ts         # 内置 Skill: Claude API
│   └── skillify.ts          # 内置 Skill: Skill 创建器
├── processContent.ts        # 内容处理管线
├── buildPrompt.ts           # 提示构建
└── buildInlineReference.ts  # 内联引用处理
```

### 7.2 关键函数签名

```typescript
// Plugin 加载
function cachePlugin(
  pluginId: string,
  source: PluginSource
): Promise<string>

function resolvePluginPath(
  pluginId: string,
  version?: string
): string

function loadPluginManifest(
  pluginPath: string
): Promise<PluginManifest>

function validatePluginPaths(
  pluginPath: string,
  manifest: PluginManifest
): void

function mergePluginSources(
  sources: PluginSources
): Plugin[]

// Skill 处理
function processContent(
  content: string,
  context: SkillContext
): Promise<string>

function buildPrompt(
  skillDef: SkillDefinition,
  args?: string
): string

function buildInlineReference(
  filePath: string,
  basePath: string
): Promise<string>
```

### 7.3 设计模式应用

**Plugin 系统**：

- **Strategy 模式** — 不同来源的插件加载策略
- **Factory 模式** — `createPlugin()` 工厂函数
- **Singleton 模式** — `PluginRuntime` 全局单例
- **Observer 模式** — 插件加载/卸载事件通知

**Skill 系统**：

- **Template Method 模式** — Skill 处理管线
- **Decorator 模式** — 内联引用装饰原始内容
- **Interpreter 模式** — Markdown 解析和执行
- **Composite 模式** — Skill 可以引用其他 Skill

---

## 8. 实现检查清单

### 8.1 Plugin 系统必须实现

- [ ] **生命周期管理**
  - [ ] 安装：支持 npm/git/local 来源
  - [ ] 缓存：版本化目录结构
  - [ ] 加载：Manifest 解析和验证
  - [ ] 运行：Commands/Hooks/Agents 注册
  - [ ] 卸载：清理注册的能力

- [ ] **安全机制**
  - [ ] 信任警告：首次加载提示
  - [ ] 黑名单：拒绝已知恶意插件
  - [ ] 策略控制：允许/拒绝列表
  - [ ] MDM 支持：企业托管插件

- [ ] **三层合并**
  - [ ] Session 插件优先级最高
  - [ ] Marketplace 插件次之
  - [ ] Builtin 插件兜底
  - [ ] 同 ID 冲突解决

- [ ] **离线支持**
  - [ ] Seed Cache 探测
  - [ ] 版本降级策略
  - [ ] 缓存失效处理

### 8.2 Skill 系统必须实现

- [ ] **Skill 定义**
  - [ ] Markdown + Front Matter 解析
  - [ ] 内联引用语法：`#[[file:...]]`
  - [ ] 参数替换机制
  - [ ] 循环引用检测

- [ ] **SkillTool**
  - [ ] 将 Skill 暴露为 Tool
  - [ ] 动态提示构建
  - [ ] 上下文注入

- [ ] **内容处理**
  - [ ] 内联引用展开
  - [ ] 语言检测与本地化
  - [ ] 模板渲染

- [ ] **Skillify 元编程**
  - [ ] Skill 创建 Skill
  - [ ] 模板生成
  - [ ] 验证和测试

### 8.3 可选优化

- [ ] **Plugin 热重载** — 无需重启即可更新插件
- [ ] **Skill 预编译** — 缓存处理后的 Skill 内容
- [ ] **Plugin Marketplace** — 插件市场集成
- [ ] **Skill 版本控制** — Skill 的版本管理
- [ ] **依赖解析** — Plugin 依赖自动安装
- [ ] **性能监控** — Plugin/Skill 执行时间追踪

### 8.4 测试验证点

**Plugin 系统测试**：

```typescript
// 1. 基础加载
test('load plugin from npm', async () => {
  const plugin = await loadPlugin('test-plugin', '1.0.0')
  expect(plugin.id).toBe('test-plugin')
})

// 2. 版本化缓存
test('cache plugin by version', async () => {
  await cachePlugin('foo', '1.0.0')
  await cachePlugin('foo', '1.1.0')
  
  const v1 = probeSeedCache('foo', '1.0.0')
  const v2 = probeSeedCache('foo', '1.1.0')
  
  expect(v1).toBeTruthy()
  expect(v2).toBeTruthy()
  expect(v1).not.toBe(v2)
})

// 3. 三层合并
test('merge plugin sources with priority', () => {
  const merged = mergePluginSources({
    builtin: [{ id: 'foo', version: '1.0.0' }],
    marketplace: [{ id: 'foo', version: '1.1.0' }],
    session: [{ id: 'foo', version: '1.0.5' }]
  })
  
  expect(merged).toHaveLength(1)
  expect(merged[0].version).toBe('1.0.5')  // session 优先
})

// 4. 安全检查
test('block malicious plugin', async () => {
  await expect(
    loadPlugin('malicious-plugin')
  ).rejects.toThrow(PluginBlockedError)
})
```

**Skill 系统测试**：

```typescript
// 1. Skill 加载
test('load skill from markdown', async () => {
  const skill = await loadSkill('test-skill/SKILL.md')
  expect(skill.name).toBe('test-skill')
})

// 2. 内联引用
test('expand inline file references', async () => {
  const content = 'Intro\n#[[file:template.md]]\nOutro'
  const expanded = await expandInlineReferences(content)
  
  expect(expanded).toContain('Intro')
  expect(expanded).toContain('<!-- template content -->')
  expect(expanded).toContain('Outro')
})

// 3. 循环引用检测
test('detect circular references', () => {
  // skill-a.md 引用 skill-b.md
  // skill-b.md 引用 skill-a.md
  
  expect(
    detectCircularReferences('skill-a.md')
  ).toBe(true)
})

// 4. SkillTool 执行
test('execute skill via tool', async () => {
  const result = await executeSkillTool({
    skill: 'deep-research',
    args: 'topic: AI safety'
  })
  
  expect(result.content).toContain('deep-research')
  expect(result.metadata.skillName).toBe('deep-research')
})
```

---

## 9. 扩展阅读

**相关文档**：

- [05-HOOK-SYSTEM.md](05-HOOK-SYSTEM.md) — Hook 系统是 Plugin 的注入点
- [03-TOOL-SYSTEM.md](03-TOOL-SYSTEM.md) — SkillTool 是 Tool 系统的一部分
- [06-PERMISSION.md](06-PERMISSION.md) — Plugin 执行受权限系统约束
- [12-DESIGN-PHILOSOPHY.md](12-DESIGN-PHILOSOPHY.md) — 扩展系统的设计哲学

**设计模式**：

- **Prompt-as-Code** — Skill 的核心理念
- **Plugin Architecture** — 可扩展系统的经典模式
- **Strategy Pattern** — Plugin 加载策略
- **Template Method** — Skill 处理管线

**实现参考**：

- VSCode Extension API — Plugin 系统的灵感来源
- Obsidian Plugin — Markdown 生态的插件设计
- Webpack Loader — 内容处理管线的参考
- npm/yarn — 包管理和版本化缓存

---

**总结**：Plugin 和 Skill 构成了 Claude Code 的扩展系统双轨。Plugin 提供完整的运行时能力，适合复杂场景；Skill 提供声明式的知识注入，适合快速定制。两者协同工作，实现了安全性和灵活性的平衡。
