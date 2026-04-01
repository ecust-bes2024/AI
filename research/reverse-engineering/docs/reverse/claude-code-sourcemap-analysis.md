# Claude Code 源码提取与架构分析

## 概述

Claude Code 是 Anthropic 官方推出的 AI 编程助手 CLI 工具。通过分析其发布的 `cli.js.map` 文件（57MB），我们可以完整提取其 TypeScript 源码，深入理解其架构设计。

**关键发现**：
- `cli.js.map` 包含 4756 个源文件的完整内容
- 1906 个 Claude Code 自身源码（TypeScript/TSX）
- 2850 个 node_modules 依赖
- **无需反编译**：sourcemap 的 `sourcesContent` 字段直接存储原始代码

**技术栈**：
- React + Ink（终端 UI）
- TypeScript（类型安全）
- Anthropic API（Claude 模型）
- 自定义工具系统（45+ 工具）
- Agent/Skill/Team 协作框架

---

## 源码提取方法

### 原理

Sourcemap 文件（`.js.map`）是 JavaScript 构建工具生成的调试文件，用于将压缩/转译后的代码映射回原始源码。其 JSON 结构包含：

```json
{
  "version": 3,
  "sources": ["src/file1.ts", "src/file2.tsx", ...],
  "sourcesContent": ["<file1 完整源码>", "<file2 完整源码>", ...],
  "mappings": "AAAA,CAAC,CAAC...",
  ...
}
```

- `sources`：源文件路径数组
- `sourcesContent`：对应的完整源码数组
- 两者索引一一对应

### 提取脚本（Node.js）

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// 读取 sourcemap 文件
const sourcemapPath = process.argv[2] || 'cli.js.map';
const outputDir = process.argv[3] || 'extracted-source';

console.log(`Reading sourcemap: ${sourcemapPath}`);
const sourcemap = JSON.parse(fs.readFileSync(sourcemapPath, 'utf8'));

const { sources, sourcesContent } = sourcemap;

if (!sources || !sourcesContent) {
  console.error('Invalid sourcemap: missing sources or sourcesContent');
  process.exit(1);
}

console.log(`Found ${sources.length} source files`);

// 提取源码
let extracted = 0;
let skipped = 0;

sources.forEach((sourcePath, index) => {
  const content = sourcesContent[index];
  
  if (!content) {
    skipped++;
    return;
  }

  // 过滤 node_modules（可选）
  if (sourcePath.includes('node_modules')) {
    skipped++;
    return;
  }

  // 构建输出路径
  const outputPath = path.join(outputDir, sourcePath);
  const outputDirPath = path.dirname(outputPath);

  // 创建目录
  fs.mkdirSync(outputDirPath, { recursive: true });

  // 写入文件
  fs.writeFileSync(outputPath, content, 'utf8');
  extracted++;
});

console.log(`\nExtraction complete:`);
console.log(`  Extracted: ${extracted} files`);
console.log(`  Skipped: ${skipped} files`);
console.log(`  Output: ${outputDir}/`);
```

**使用方法**：

```bash
node extract-sourcemap.js cli.js.map output/
```

### 提取脚本（Python）

```python
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def extract_sourcemap(sourcemap_path, output_dir):
    print(f"Reading sourcemap: {sourcemap_path}")
    
    with open(sourcemap_path, 'r', encoding='utf-8') as f:
        sourcemap = json.load(f)
    
    sources = sourcemap.get('sources', [])
    sources_content = sourcemap.get('sourcesContent', [])
    
    if not sources or not sources_content:
        print("Invalid sourcemap: missing sources or sourcesContent")
        sys.exit(1)
    
    print(f"Found {len(sources)} source files")
    
    extracted = 0
    skipped = 0
    
    for source_path, content in zip(sources, sources_content):
        if not content:
            skipped += 1
            continue
        
        # 过滤 node_modules（可选）
        if 'node_modules' in source_path:
            skipped += 1
            continue
        
        # 构建输出路径
        output_path = Path(output_dir) / source_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        output_path.write_text(content, encoding='utf-8')
        extracted += 1
    
    print(f"\nExtraction complete:")
    print(f"  Extracted: {extracted} files")
    print(f"  Skipped: {skipped} files")
    print(f"  Output: {output_dir}/")

if __name__ == '__main__':
    sourcemap_path = sys.argv[1] if len(sys.argv) > 1 else 'cli.js.map'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'extracted-source'
    extract_sourcemap(sourcemap_path, output_dir)
```

**使用方法**：

```bash
python3 extract-sourcemap.py cli.js.map output/
```

---

## 项目结构分析

提取后的源码目录结构如下（仅展示核心部分）：

```
src/
├── cli/                    # CLI 入口与主循环
│   ├── index.tsx          # 主入口
│   ├── repl.tsx           # REPL 循环实现
│   └── commands/          # 90+ 个命令实现
├── tools/                  # 工具系统
│   ├── bash.ts            # Bash 命令执行
│   ├── file.ts            # 文件操作
│   ├── agent.ts           # Agent 调度
│   ├── skill.ts           # Skill 管理
│   └── mcp/               # MCP 协议支持
├── agent/                  # Agent 系统
│   ├── agent-manager.ts   # Agent 生命周期管理
│   ├── team.ts            # Team 协作
│   └── harness.ts         # Agent 执行环境
├── skill/                  # Skill 系统
│   ├── skill-loader.ts    # Skill 加载器
│   └── skill-executor.ts  # Skill 执行器
├── ui/                     # 终端 UI 组件
│   ├── components/        # React 组件
│   ├── renderer/          # 自定义 Ink 渲染器
│   └── theme.ts           # 主题配置
├── api/                    # Anthropic API 客户端
│   ├── client.ts          # API 封装
│   └── streaming.ts       # 流式响应处理
├── memory/                 # 记忆系统
│   ├── memory-manager.ts  # 记忆管理
│   └── context.ts         # 上下文管理
└── utils/                  # 工具函数
    ├── git.ts             # Git 操作
    ├── fs.ts              # 文件系统
    └── logger.ts          # 日志系统
```

**统计数据**：
- 总文件数：1906 个（不含 node_modules）
- TypeScript 文件：1654 个
- TSX 文件（React 组件）：252 个
- 核心模块：8 个
- 工具实现：45+ 个
- 命令实现：90+ 个

---

## 核心架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
│                   (React + Ink)                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   REPL Loop                              │
│  • 接收用户输入（自然语言 / slash 命令）                │
│  • 解析命令                                              │
│  • 路由到对应处理器                                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼──────┐ ┌──▼──────────┐
│   Tool       │ │ Agent   │ │   Skill     │
│   System     │ │ System  │ │   System    │
└───────┬──────┘ └──┬──────┘ └──┬──────────┘
        │           │            │
        └───────────┼────────────┘
                    │
        ┌───────────▼────────────┐
        │   Anthropic API        │
        │   (Claude Models)      │
        └────────────────────────┘
```

### 2. REPL 循环

核心文件：`src/cli/repl.tsx`

```typescript
// 简化的 REPL 循环逻辑
async function replLoop() {
  while (true) {
    // 1. 显示提示符
    const input = await prompt('> ');
    
    // 2. 解析输入
    const parsed = parseInput(input);
    
    // 3. 路由处理
    if (parsed.type === 'slash-command') {
      await handleCommand(parsed.command, parsed.args);
    } else if (parsed.type === 'natural-language') {
      await handleNaturalLanguage(parsed.text);
    }
    
    // 4. 更新上下文
    updateContext(input, response);
  }
}
```

**关键特性**：
- 支持自然语言输入
- 支持 slash 命令（如 `/commit`, `/review-pr`）
- 流式响应渲染
- 上下文管理（记忆系统）
- 错误处理与重试

### 3. 工具系统

核心文件：`src/tools/`

工具系统是 Claude Code 的核心能力层，提供 45+ 个工具供 LLM 调用。

**工具分类**：

| 类别 | 工具 | 功能 |
|------|------|------|
| 文件操作 | Read, Write, Edit, Glob, Grep | 文件读写、搜索、编辑 |
| 代码执行 | Bash, NotebookEdit | 执行命令、编辑 Jupyter |
| 版本控制 | Git 系列 | Git 操作封装 |
| 协作 | Agent, Skill, Team | Agent/Skill 调度 |
| 浏览器 | WebFetch, WebSearch | 网页抓取、搜索 |
| MCP | MCP 系列 | Model Context Protocol 支持 |

**工具接口设计**：

```typescript
interface Tool {
  name: string;
  description: string;
  parameters: JSONSchema;
  execute: (params: any) => Promise<ToolResult>;
}

interface ToolResult {
  success: boolean;
  output?: string;
  error?: string;
  artifacts?: Artifact[];
}
```

**示例：Bash 工具**

```typescript
// src/tools/bash.ts
export const BashTool: Tool = {
  name: 'Bash',
  description: 'Execute bash commands',
  parameters: {
    type: 'object',
    properties: {
      command: { type: 'string' },
      timeout: { type: 'number' },
      run_in_background: { type: 'boolean' }
    },
    required: ['command']
  },
  
  async execute(params) {
    const { command, timeout = 120000 } = params;
    
    try {
      const result = await execCommand(command, { timeout });
      return {
        success: true,
        output: result.stdout
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
};
```

### 4. Agent 系统

核心文件：`src/agent/`

Agent 系统允许主 Agent 生成子 Agent 处理特定任务。

**Agent 生命周期**：

```
创建 → 初始化 → 执行 → 返回结果 → 销毁
```

**关键组件**：

1. **AgentManager**：管理 Agent 生命周期
2. **AgentHarness**：Agent 执行环境（隔离的上下文）
3. **Team**：多 Agent 协作框架

**示例：Agent 调用**

```typescript
// 主 Agent 调用子 Agent
const result = await spawnAgent({
  role: 'code-reviewer',
  task: 'Review the changes in PR #123',
  context: {
    pr_number: 123,
    files: ['src/index.ts', 'src/utils.ts']
  }
});
```

### 5. Skill 系统

核心文件：`src/skill/`

Skill 是预定义的任务模板，类似于"技能包"。

**Skill 结构**：

```
.claude/skills/<skill-name>/
├── SKILL.md          # Skill 定义（Markdown）
├── system.md         # 系统提示词（可选）
└── examples/         # 示例（可选）
```

**Skill 加载流程**：

```typescript
// 1. 扫描 .claude/skills/ 目录
const skills = await loadSkills('.claude/skills');

// 2. 解析 SKILL.md
const skill = parseSkillMarkdown(skillContent);

// 3. 注册到 Skill 系统
registerSkill(skill);

// 4. 用户调用（如 /commit）
await executeSkill('commit', args);
```

### 6. 终端 UI（React + Ink）

核心文件：`src/ui/`

Claude Code 使用 React + Ink 构建终端 UI，实现了类似 Web 的组件化开发。

**核心组件**：

```typescript
// src/ui/components/ChatMessage.tsx
export const ChatMessage: React.FC<Props> = ({ role, content }) => {
  return (
    <Box flexDirection="column">
      <Text bold color={role === 'user' ? 'blue' : 'green'}>
        {role === 'user' ? 'You' : 'Claude'}:
      </Text>
      <Text>{content}</Text>
    </Box>
  );
};
```

**自定义渲染器**：

Claude Code 扩展了 Ink 的渲染器，支持：
- 流式文本渲染
- 代码高亮
- 进度条
- 交互式组件（确认对话框、选择器）

---

## 关键模块详解

### 1. 文件操作模块

**Read 工具**：

```typescript
// src/tools/file.ts
async function readFile(filePath: string, options?: ReadOptions) {
  // 1. 验证路径
  if (!isValidPath(filePath)) {
    throw new Error('Invalid file path');
  }
  
  // 2. 读取文件
  const content = await fs.readFile(filePath, 'utf8');
  
  // 3. 处理大文件（分页）
  if (options?.limit) {
    return paginateContent(content, options.offset, options.limit);
  }
  
  // 4. 添加行号
  return addLineNumbers(content);
}
```

**Edit 工具**：

```typescript
// 精确字符串替换
async function editFile(filePath: string, oldString: string, newString: string) {
  const content = await fs.readFile(filePath, 'utf8');
  
  // 确保 oldString 唯一
  const occurrences = countOccurrences(content, oldString);
  if (occurrences === 0) {
    throw new Error('String not found');
  }
  if (occurrences > 1) {
    throw new Error('String is not unique, provide more context');
  }
  
  // 替换
  const newContent = content.replace(oldString, newString);
  await fs.writeFile(filePath, newContent, 'utf8');
}
```

### 2. Git 集成

**Git 工具封装**：

```typescript
// src/utils/git.ts
export async function gitStatus() {
  const result = await exec('git status --porcelain');
  return parseGitStatus(result.stdout);
}

export async function gitCommit(message: string) {
  // 1. 检查是否有变更
  const status = await gitStatus();
  if (status.length === 0) {
    throw new Error('No changes to commit');
  }
  
  // 2. 添加 Co-Authored-By
  const fullMessage = `${message}\n\nCo-Authored-By: Claude <noreply@anthropic.com>`;
  
  // 3. 提交
  await exec(`git commit -m "${escapeShellArg(fullMessage)}"`);
}
```

### 3. MCP 协议支持

**MCP（Model Context Protocol）** 是 Anthropic 提出的标准化协议，用于 LLM 与外部工具通信。

**MCP 工具注册**：

```typescript
// src/tools/mcp/registry.ts
export class MCPRegistry {
  private tools = new Map<string, MCPTool>();
  
  async registerServer(serverConfig: MCPServerConfig) {
    // 1. 连接 MCP 服务器
    const client = await connectMCPServer(serverConfig);
    
    // 2. 获取工具列表
    const tools = await client.listTools();
    
    // 3. 注册到工具系统
    tools.forEach(tool => {
      this.tools.set(tool.name, tool);
    });
  }
  
  async executeTool(name: string, params: any) {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new Error(`Tool not found: ${name}`);
    }
    
    return await tool.execute(params);
  }
}
```

### 4. 记忆系统

**上下文管理**：

```typescript
// src/memory/context.ts
export class ContextManager {
  private messages: Message[] = [];
  private maxTokens = 100000; // 100K context window
  
  addMessage(message: Message) {
    this.messages.push(message);
    
    // 超出限制时压缩
    if (this.estimateTokens() > this.maxTokens) {
      this.compress();
    }
  }
  
  private compress() {
    // 1. 保留最近的消息
    // 2. 压缩中间的消息（摘要）
    // 3. 保留关键上下文（文件内容、错误信息）
  }
}
```

### 5. 流式响应处理

**SSE（Server-Sent Events）流式处理**：

```typescript
// src/api/streaming.ts
export async function* streamResponse(prompt: string) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-opus-4',
      messages: [{ role: 'user', content: prompt }],
      stream: true
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'content_block_delta') {
          yield data.delta.text;
        }
      }
    }
  }
}
```

---

## 技术栈总结

### 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `react` | 18.x | UI 框架 |
| `ink` | 4.x | 终端 UI 渲染 |
| `typescript` | 5.x | 类型系统 |
| `@anthropic-ai/sdk` | 最新 | Anthropic API 客户端 |
| `commander` | 11.x | CLI 参数解析 |
| `chalk` | 5.x | 终端颜色 |
| `ora` | 7.x | 加载动画 |
| `inquirer` | 9.x | 交互式提示 |

### 构建工具

- **打包器**：esbuild（快速构建）
- **类型检查**：tsc（TypeScript 编译器）
- **Sourcemap**：生成完整的 sourcemap（包含 sourcesContent）

### 设计模式

1. **工具模式**：所有能力封装为工具，LLM 按需调用
2. **组件化 UI**：React 组件化开发终端界面
3. **流式处理**：SSE 流式响应，实时渲染
4. **插件系统**：Skill/Agent/MCP 可扩展架构
5. **上下文管理**：智能压缩，保持长对话能力

---

## 参考资料

### 官方资源

- [Claude Code 官网](https://claude.com/claude-code)
- [Anthropic API 文档](https://docs.anthropic.com/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

### 技术文档

- [Ink 文档](https://github.com/vadimdemedes/ink)
- [React 文档](https://react.dev/)
- [Sourcemap 规范](https://sourcemaps.info/spec.html)

### 相关工具

- [esbuild](https://esbuild.github.io/) - 快速 JavaScript 打包器
- [TypeScript](https://www.typescriptlang.org/) - JavaScript 超集
- [Commander.js](https://github.com/tj/commander.js) - CLI 框架

---

## 附录：关键文件清单

### 入口文件

- `src/cli/index.tsx` - CLI 主入口
- `src/cli/repl.tsx` - REPL 循环

### 工具系统

- `src/tools/bash.ts` - Bash 执行
- `src/tools/file.ts` - 文件操作（Read/Write/Edit）
- `src/tools/glob.ts` - 文件搜索
- `src/tools/grep.ts` - 内容搜索
- `src/tools/agent.ts` - Agent 调度
- `src/tools/skill.ts` - Skill 执行
- `src/tools/web.ts` - 网页抓取
- `src/tools/mcp/` - MCP 协议支持

### Agent 系统

- `src/agent/agent-manager.ts` - Agent 管理器
- `src/agent/harness.ts` - Agent 执行环境
- `src/agent/team.ts` - Team 协作

### Skill 系统

- `src/skill/skill-loader.ts` - Skill 加载器
- `src/skill/skill-executor.ts` - Skill 执行器

### UI 组件

- `src/ui/components/ChatMessage.tsx` - 聊天消息
- `src/ui/components/ToolCall.tsx` - 工具调用显示
- `src/ui/components/ProgressBar.tsx` - 进度条
- `src/ui/renderer/` - 自定义渲染器

### API 客户端

- `src/api/client.ts` - Anthropic API 封装
- `src/api/streaming.ts` - 流式响应处理

### 工具函数

- `src/utils/git.ts` - Git 操作
- `src/utils/fs.ts` - 文件系统
- `src/utils/logger.ts` - 日志系统
- `src/utils/token-counter.ts` - Token 计数

---

**文档版本**：v1.0  
**最后更新**：2026-03-31  
**作者**：Reverse Engineering Lab
