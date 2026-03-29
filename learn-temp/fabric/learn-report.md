# Fabric 深度分析报告

## 这是什么

Fabric 是一个开源 AI 增强框架（40K+ stars, MIT），核心理念是将 AI prompt 组织为可复用的 **Pattern**（模式），通过 CLI-first 的方式让用户在终端中组合使用。Go 实现，支持 20+ AI provider，252 个内置 Pattern，9 种推理策略。

原作者 Daniel Miessler（安全领域知名人物），2024年1月创建，从 Python 迁移到 Go，目前处于 v1.4.x 活跃开发中。

## 核心价值

### 1. Pattern 系统 — AI 能力的原子单元

**定义格式极其简单：**
```
~/.config/fabric/patterns/<pattern_name>/
  system.md    # 系统提示词（核心，Markdown 格式）
  user.md      # 用户提示词模板（可选）
  README.md    # 说明文档（可选）
```

每个 Pattern 就是一个目录，里面放 `system.md`。没有 YAML frontmatter，没有 JSON schema，没有元数据文件。**纯 Markdown，人类可读可编辑。**

**Pattern 的内部结构约定（非强制）：**
```markdown
# IDENTITY and PURPOSE
（角色定义和目标）

# STEPS
（执行步骤）

# OUTPUT SECTIONS
（输出格式定义）

# OUTPUT INSTRUCTIONS
（输出约束）

# INPUT:
INPUT:
```

这个约定是社区共识，不是代码强制的。Pattern 本质上就是一个 system prompt 文本文件。

**关键设计决策：**
- Pattern 存储在 `~/.config/fabric/patterns/` 文件系统中
- 通过 `git clone` 从 GitHub 仓库拉取官方 Pattern（`data/patterns/`）
- 支持 Custom Patterns 目录，与官方 Pattern 合并但不覆盖
- Pattern 名就是目录名，通过 `-p <name>` 引用
- 支持 `{{input}}` 占位符和 `{{variable}}` 模板变量
- 支持 `{{plugin:namespace:operation:value}}` 内置插件调用（text/datetime/file/fetch/sys）
- 支持 `{{ext:name:operation:value}}` 外部扩展调用

### 2. Strategy 系统 — 推理策略叠加

```json
// strategies/cot.json
{
    "description": "Chain-of-Thought (CoT) Prompting",
    "prompt": "Think step by step to answer the question. Return the final answer in the required format."
}
```

Strategy 是独立于 Pattern 的推理增强层，通过 `--strategy cot` 叠加到任何 Pattern 上。Strategy prompt 被 prepend 到 system message 前面。

9 种内置策略：cot, cod, tot, aot, ltm, self-consistent, self-refine, reflexion, standard。

### 3. CLI-First 设计 — Unix 哲学的 AI 实现

```bash
# 核心用法：stdin | fabric -p pattern
pbpaste | fabric --pattern summarize
echo "text" | fabric -p analyze_claims --stream
fabric -y "https://youtube.com/watch?v=xxx" -p extract_wisdom

# 管道组合
pbpaste | fabric -p extract_wisdom | fabric -p summarize
curl -s url | fabric -p analyze_claims

# Pattern 可以直接作为命令别名
alias summarize='fabric --pattern summarize'
# 然后：pbpaste | summarize
```

**CLI 设计亮点：**
- `stdin` 作为输入，`stdout` 作为输出，完美融入 Unix 管道
- `-p` 选择 Pattern，`-m` 选择模型，`-s` 开启流式
- `-y` 直接处理 YouTube URL（内置 transcript 提取）
- `-u` 直接爬取网页（通过 Jina AI）
- `--dry-run` 预览发送给模型的内容
- `--strategy` 叠加推理策略
- `--serve` 启动 REST API 服务器
- `--serveOllama` 兼容 Ollama API（Pattern 作为 model 暴露）
- Shell completion 支持（zsh/bash/fish）
- YAML 配置文件支持（`~/.config/fabric/config.yaml`）
- Per-pattern model mapping（环境变量 `FABRIC_MODEL_PATTERN_NAME=vendor|model`）

### 4. 插件架构 — 多 Provider 统一接口

```
internal/plugins/
  ai/           # AI Provider 插件（20+）
    openai/
    anthropic/
    gemini/
    ollama/
    bedrock/
    azure/
    openai_compatible/  # 通用 OpenAI 兼容适配器
    ...
  db/fsdb/      # 文件系统数据库
  template/     # 模板引擎 + 扩展系统
  strategy/     # 推理策略
```

每个 AI provider 实现 `Vendor` 接口，通过 `PluginRegistry` 统一管理。支持运行时切换模型和 provider。

### 5. Extension 系统 — Pattern 内的外部工具调用

Extension 允许 Pattern 在模板处理阶段调用外部命令：

```markdown
# 在 Pattern 中使用
{{ext:myext:operation:value}}
```

Extension 通过 YAML 配置注册，指定可执行文件和命令模板。这是 Fabric 的"函数调用"机制，但发生在 prompt 构建阶段而非 LLM 推理阶段。

## 架构分析

### 数据流

```
User Input (stdin/args/youtube/url)
  → CLI Flags 解析
  → Pattern 加载 (fsdb)
  → Template 变量替换 ({{input}}, {{var}}, {{plugin:...}}, {{ext:...}})
  → Strategy 叠加 (prepend to system message)
  → Context 叠加 (prepend to system message)
  → Session 管理 (历史消息)
  → Vendor 路由 (model → vendor mapping)
  → AI API 调用 (stream/non-stream)
  → Output (stdout/file/clipboard)
```

### 存储结构

```
~/.config/fabric/
  .env                    # API keys 和配置
  config.yaml             # CLI 默认值
  patterns/               # 官方 Pattern（git clone）
    extract_wisdom/
      system.md
    summarize/
      system.md
    ...
  custom_patterns/        # 用户自定义 Pattern
  strategies/             # 推理策略 JSON
  contexts/               # 持久化上下文
  sessions/               # 会话历史
  extensions/             # 扩展注册表
```

## 直接可用性

**轻包装可用** — Fabric 作为 CLI 工具可以直接安装使用，但与我们的 Skills 系统是不同层次的东西。

理由：
- Fabric 是面向终端用户的 AI CLI 工具
- 我们的 Skills 是面向 AI Agent 的能力定义系统
- 两者解决不同问题：Fabric 解决"人如何高效使用 AI"，Skills 解决"AI Agent 如何结构化执行任务"
- Fabric 的 Pattern 库（252个）作为 prompt 参考库有直接价值

## 值得学习

### 1. Pattern 格式的极简主义（最重要的借鉴）

Fabric 证明了一个关键洞察：**AI 能力单元的最佳格式就是纯文本 prompt，不需要复杂的元数据和配置。**

- 一个目录 + 一个 `system.md` = 一个完整的 AI 能力
- 目录名就是能力名，零配置
- Markdown 格式，人类可读可编辑，AI 也能理解
- 没有 schema 验证，没有版本号，没有依赖声明

这与我们的 Skills 系统形成鲜明对比：我们的 SKILL.md 包含更多结构（参数、触发条件、工作流步骤），但也更重。

**借鉴点：** 对于简单的、单步的 AI 能力，Fabric 的极简格式是更优解。复杂的多步工作流才需要我们 Skills 的结构化定义。

### 2. Unix 管道哲学的 AI 实现

```bash
# Fabric 的组合方式
input | fabric -p step1 | fabric -p step2 | fabric -p step3
```

这是真正的 Unix 哲学：每个 Pattern 做一件事，通过管道组合。这比在一个 prompt 里塞所有逻辑更灵活、更可调试。

**借鉴点：** 我们的 Skills 倾向于在一个 Skill 内完成所有步骤。可以考虑支持 Skill 的管道式组合。

### 3. Strategy 作为正交维度

Strategy 与 Pattern 完全解耦：任何 Pattern 都可以叠加任何 Strategy。这是一个优雅的设计——推理方法和任务定义是两个独立的关注点。

**借鉴点：** 我们可以将推理策略（CoT、ToT 等）从 Skill 定义中抽离，作为独立的可组合层。

### 4. Pattern 别名 = 命令

```bash
alias summarize='fabric --pattern summarize'
# 然后直接：pbpaste | summarize
```

每个 Pattern 都可以变成一个 shell 命令。这让 AI 能力融入了用户的日常工具链。

### 5. 252 个 Pattern 的分类学

Fabric 的 Pattern 库覆盖了广泛的使用场景：
- 内容分析：analyze_claims, analyze_paper, analyze_prose
- 内容创作：create_summary, create_essay, create_art_prompt
- 代码相关：explain_code, create_coding_project, coding_master
- 安全相关：analyze_malware, analyze_threat_report
- 个人效率：extract_wisdom, rate_content, summarize
- 商业分析：analyze_sales_call, analyze_product_feedback

这个分类和命名约定（`verb_noun` 格式）值得参考。

### 6. Ollama 兼容模式的巧妙设计

`--serveOllama` 让 Fabric 伪装成 Ollama 服务器，Pattern 作为 model 暴露。任何支持 Ollama API 的应用都可以直接使用 Fabric 的 Pattern。这是一种聪明的集成策略。

## 不要复制

### 1. 单步 prompt 的局限性

Fabric 的 Pattern 本质上是单步 prompt——一次 LLM 调用完成所有工作。对于复杂任务（多步推理、条件分支、工具调用、人机交互），这个模型不够用。

我们的 Skills 系统支持多步工作流、Agent 协作、工具调用，这是 Fabric 做不到的。不要为了简化而丢掉这些能力。

### 2. 文件系统作为数据库

Fabric 用文件系统（fsdb）存储一切：Pattern、Session、Context。这在单用户 CLI 场景下可以，但不适合多 Agent 协作场景。

### 3. Git clone 作为分发机制

Pattern 通过 `git clone` 整个仓库来更新。252 个 Pattern 全量下载，没有按需加载。这在 Pattern 数量增长后会成为问题。

### 4. 硬编码的 `create_coding_feature` 特殊处理

`chatter.go:190` 中对 `create_coding_feature` Pattern 有硬编码的文件变更处理逻辑。这是一个设计缺陷——Pattern 应该是纯粹的 prompt，不应该有特殊的后处理逻辑。

### 5. 模板变量的简单替换

`{{variable}}` 只是字符串替换，没有类型系统、默认值、验证。对于简单场景够用，但不适合需要结构化输入的复杂 Skill。

## 与我们 Skills 系统的对比

| 维度 | Fabric Pattern | 我们的 Skill |
|------|---------------|-------------|
| 格式 | 纯 Markdown（system.md） | 结构化 Markdown（SKILL.md + frontmatter） |
| 复杂度 | 极简，一个文件 | 中等，支持参数、触发条件、多步骤 |
| 执行模型 | 单步 LLM 调用 | 多步工作流，Agent 可解释执行 |
| 组合方式 | Unix 管道（外部组合） | 内部引用和编排 |
| 分发 | git clone 整个仓库 | 本地目录，按需加载 |
| 用户 | 终端用户（人） | AI Agent |
| 推理策略 | 独立的 Strategy 层 | 嵌入在 Skill 定义中 |
| 工具调用 | Extension（模板阶段） | Agent 原生工具调用 |
| 上下文 | Context 文件 + Session | Agent 对话上下文 |
| 变量 | 简单字符串替换 | 参数化（类型、默认值） |

**核心差异：** Fabric Pattern 是给人用的 prompt 模板，我们的 Skill 是给 Agent 用的能力定义。两者不是竞争关系，而是不同抽象层次。

## 建议动作

**learn-idea-only** — 借鉴 Fabric 的设计哲学和 Pattern 库，但不直接集成或包装。

理由：
1. Fabric 解决的问题（人 → AI CLI）与我们的问题（Agent 能力定义）不同
2. 直接使用 Fabric 需要 Go 运行时，增加依赖
3. Pattern 库的价值在于 prompt 内容本身，可以直接参考而不需要 Fabric 框架
4. 我们的 Skills 系统已经比 Fabric 更强大（多步、Agent 协作、工具调用）

## 建议落地形式

**memory** — 将以下设计原则记录为持久记忆：

1. **极简格式原则**：简单 AI 能力用纯 Markdown 定义就够了，不需要过度结构化
2. **正交组合原则**：推理策略（Strategy）应该与任务定义（Pattern/Skill）解耦
3. **Pattern 命名约定**：`verb_noun` 格式（analyze_claims, extract_wisdom, create_summary）
4. **Pattern 内部结构**：IDENTITY → STEPS → OUTPUT SECTIONS → OUTPUT INSTRUCTIONS → INPUT

## 最佳下一步

将 Fabric 的 Pattern 设计哲学和 252 个 Pattern 的命名/结构约定记录为 memory，作为未来设计 Skill 时的参考基准。不需要安装或集成 Fabric 本身。
