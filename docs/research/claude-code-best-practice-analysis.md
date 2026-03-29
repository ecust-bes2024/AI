# claude-code-best-practice 深度分析报告

**调研日期**：2026-03-29
**仓库**：https://github.com/shanraisshan/claude-code-best-practice
**Star 数**：23.7k
**分析师**：Ben Thompson (AI)

---

## 一、项目概览

### 1.1 项目定位
这是一个社区驱动的 Claude Code 最佳实践知识库，由 Boris Cherny（Claude Code 创始人）的公开分享内容整理而成。项目口号是 "practice makes claude perfect"，曾登上 GitHub Trending #1。

### 1.2 内容结构
- **86 条技巧**：按 12 个类别组织（Prompting、Planning、CLAUDE.md、Agents、Commands、Skills、Hooks、Workflows、Git/PR、Debugging、Utilities、Daily）
- **8 大框架对比**：对比主流 Claude Code 开发工作流框架
- **实现示例**：包含 orchestration workflow、agent teams、scheduled tasks 等实战案例
- **最佳实践文档**：涵盖 skills、commands、agents、MCP、settings 等核心概念

### 1.3 信息来源可信度
**极高**。内容主要来自：
- Boris Cherny（Claude Code 创始人）的 X/Twitter 分享
- Thariq（Claude Code 核心工程师）的技术文章
- Anthropic 官方文档和博客
- 社区实践验证

---

## 二、8 大框架对比

### 2.1 框架列表（按 Star 数排序）

| 框架 | Star | 独特性 | 规划方式 | Agents | Commands | Skills |
|------|------|--------|---------|--------|----------|--------|
| [Superpowers](https://github.com/obra/superpowers) | 120k | TDD-first, Iron Laws, whole-plan review | Skills | 5 | 3 | 14 |
| [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) | 114k | instinct scoring, AgentShield, multi-lang rules | Agents | 28 | 63 | 125 |
| [Spec Kit](https://github.com/github/spec-kit) | 83k | spec-driven, constitution, 22+ tools | Commands | 0 | 9+ | 0 |
| [gstack](https://github.com/garrytan/gstack) | 54k | role personas, /codex review, parallel sprints | Skills | 0 | 0 | 29 |
| [Get Shit Done](https://github.com/gsd-build/get-shit-done) | 44k | fresh 200K contexts, wave execution, XML plans | Agents | 18 | 57 | 0 |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 43k | full SDLC, agent personas, 22+ platforms | Skills | 0 | 0 | 43 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | 35k | delta specs, brownfield, artifact DAG | Commands | 0 | 11 | 0 |
| [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin) | 11k | Compound Learning, Multi-Platform CLI, Plugin Marketplace | Skills | 47 | 4 | 43 |

### 2.2 框架分类模式

**三种架构偏好**：
1. **Agent-heavy**：Everything Claude Code (28 agents), Compound Engineering (47 agents), Get Shit Done (18 agents)
2. **Skill-heavy**：Superpowers (14 skills), gstack (29 skills), BMAD-METHOD (43 skills)
3. **Command-heavy**：Spec Kit (9+ commands), OpenSpec (11 commands)

**核心洞察**：
- **所有框架都收敛到同一模式**：Research → Plan → Execute → Review → Ship
- **规划方式差异**：Skills 适合渐进式披露，Agents 适合隔离上下文，Commands 适合工作流编排
- **组件数量不代表质量**：Superpowers 只有 14 个 skills 但 120k stars，说明精简聚焦更重要

### 2.3 用户体系的定位

**你的体系特征**：
- **39 个 Skills**（lark 系列占主导，覆盖飞书全栈能力）
- **0 个 Agents**（未使用 subagent 模式）
- **Commands 未知**（未检查到 .claude/commands 目录）
- **Hooks 未知**（未检查到 .claude/hooks 目录）

**对标分析**：
- 接近 **gstack 模式**（skill-heavy，0 agents）
- 但你的 skills 更垂直（飞书生态），而非通用开发工作流
- **缺失**：规划类 skill（如 autoplan）、验证类 skill（如 product verification）、代码质量类 skill（如 simplify）

**建议定位**：
你的体系是 **"垂直领域专家 + 通用工具箱"** 混合模式：
- 飞书生态 → 垂直领域专家（lark-* skills）
- 通用能力 → 工具箱（pdf, xlsx, docx, playwright-cli, scrapling）
- **缺口**：开发工作流编排（planning, code review, git workflow）

---

## 三、86 条技巧精选（高级用户增量价值）

### 过滤标准
- ❌ 入门级内容（如"使用 plan mode"、"创建 skills"）
- ❌ 你已经在用的（如 skills、memory 系统）
- ✅ 非显而易见的技巧
- ✅ 对深度用户有增量价值的

### 3.1 Prompting（3 条 → 保留 2 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **挑战 Claude**："grill me on these changes and don't make a PR until I pass your test" 或 "prove to me this works"，让 Claude diff main 和你的分支 | ⭐⭐⭐ 反转主从关系，让 Claude 当审查者 | Boris |
| **优雅重构提示词**："knowing everything you know now, scrap this and implement the elegant solution" | ⭐⭐ 触发 Claude 的"重新思考"模式 | Boris |

### 3.2 Planning/Specs（6 条 → 保留 2 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **AskUserQuestion 工具**：从最小 spec 开始，让 Claude 用 AskUserQuestion 工具采访你，然后新开 session 执行 | ⭐⭐⭐ 你可能不知道这个工具 | Thariq |
| **Prototype > PRD**：构建 20-30 个版本而不是写 spec，构建成本低所以多试 | ⭐⭐⭐ 反直觉，但符合 AI 时代的快速迭代 | Boris |

### 3.3 CLAUDE.md（7 条 → 保留 3 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **`<important if="...">` 标签**：用条件标签包裹领域特定规则，防止 CLAUDE.md 变长后被忽略 | ⭐⭐⭐ 解决"Claude 忽略 CLAUDE.md"的核心技巧 | Dex |
| **settings.json 优先**：harness 强制行为（attribution, permissions, model）放 settings.json，不要放 CLAUDE.md | ⭐⭐ 区分"建议"和"强制"的边界 | davila7 |
| **"run tests" 测试**：任何开发者应该能启动 Claude，说"run the tests"就能一次成功 | ⭐⭐ 衡量 CLAUDE.md 质量的标准 | Dex |

### 3.4 Agents（4 条 → 保留 2 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **功能特定 subagent**：用 feature-specific subagents + skills，而不是通用的 qa/backend engineer 角色 | ⭐⭐⭐ 你目前没用 agents，这是关键设计原则 | Boris |
| **Test Time Compute**：独立上下文窗口产生更好结果；一个 agent 引入的 bug，另一个 agent（同模型）能可靠发现 | ⭐⭐⭐ 解释了为什么 subagent 有效 | Boris |

### 3.5 Commands（3 条 → 保留 1 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **每日多次的任务 → skill/command**：构建 `/techdebt`、context-dump、analytics commands | ⭐⭐ 你可能还没系统化这个流程 | Boris |

### 3.6 Skills（9 条 → 保留 6 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **`context: fork`**：skill 在隔离 subagent 中运行，主上下文只看到最终结果，不看中间 tool calls | ⭐⭐⭐ 你可能不知道这个配置 | Lydia |
| **Gotchas section**：每个 skill 都建 Gotchas 部分，最高信号内容，随时间添加 Claude 的失败点 | ⭐⭐⭐ 你的 skills 可能缺这个 | Thariq |
| **description 是触发器**：description 字段是给模型的触发条件，不是给人看的摘要 | ⭐⭐ 写法差异很大 | Thariq |
| **不要陈述显而易见的**：只写能推动 Claude 超越默认行为的信息 | ⭐⭐ 减少噪音 | Thariq |
| **不要 railroad Claude**：给目标和约束，不要给逐步指令 | ⭐⭐ 你的 skills 可能过于详细 | Thariq |
| **嵌入 `` !`command` ``**：在 SKILL.md 中嵌入动态 shell 输出，Claude 调用时运行，模型只看到结果 | ⭐⭐⭐ 高级技巧，你可能不知道 | Lydia |

### 3.7 Hooks（5 条 → 保留 4 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **On-demand hooks**：在 skills 中注册 hooks，如 `/careful` 阻止破坏性命令，`/freeze` 阻止目录外编辑 | ⭐⭐⭐ 你可能没用过 hooks | Thariq |
| **PreToolUse hook 测量 skill 使用率**：找到流行或触发不足的 skills | ⭐⭐ 数据驱动优化 | Thariq |
| **PostToolUse hook 自动格式化**：Claude 生成代码后，hook 处理最后 10% 格式化，避免 CI 失败 | ⭐⭐ 你可能在手动做这个 | Boris |
| **Stop hook 验证工作**：在 turn 结束时提示 Claude 继续或验证工作 | ⭐⭐ 质量保证机制 | Boris |

### 3.8 Workflows（7 条 → 保留 3 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **50% 手动 compact**：避免 agent dumb zone，在 50% 时手动 `/compact` | ⭐⭐ 性能优化 | - |
| **ultrathink 关键词**：在 prompt 中使用 ultrathink 触发高强度推理 | ⭐⭐ 你可能不知道这个关键词 | - |
| **Esc Esc 或 /rewind**：Claude 跑偏时用 rewind，不要在同一上下文中修复 | ⭐⭐ 避免上下文污染 | - |

### 3.9 Workflows Advanced（6 条 → 保留 4 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **ASCII 图表**：大量使用 ASCII 图表理解架构 | ⭐⭐ 简单但有效 | Boris |
| **`/permissions` 通配符**：用 `Bash(npm run *)`, `Edit(/docs/**)` 而不是 dangerously-skip-permissions | ⭐⭐⭐ 安全的便利性 | Boris |
| **`/sandbox`**：文件和网络隔离，减少 84% 权限提示 | ⭐⭐⭐ 你可能没开启 | Boris |
| **Product verification skills**：值得花一周时间完善 signup-flow-driver, checkout-verifier | ⭐⭐⭐ 投资回报率高 | Thariq |

### 3.10 Git/PR（5 条 → 保留 3 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **PR 大小分布**：p50 = 118 行，p90 = 498 行，p99 = 2978 行（Boris 一天 141 个 PR，45K 行变更） | ⭐⭐⭐ 量化标准 | Boris |
| **Always squash merge**：干净线性历史，一个 commit 一个功能，易于 revert 和 bisect | ⭐⭐ 高速 AI 辅助工作流的必备 | Boris |
| **@claude on PR**：在同事 PR 上 tag @claude 自动生成 lint 规则 | ⭐⭐⭐ 自动化代码审查 | Boris |

### 3.11 Debugging（7 条 → 保留 3 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **截图习惯**：卡住时养成截图分享给 Claude 的习惯 | ⭐ 简单但常被忽略 | - |
| **后台任务调试**：让 Claude 把终端作为后台任务运行，更好地调试 | ⭐⭐ 你可能在前台运行 | - |
| **Agentic search > RAG**：glob + grep 胜过向量数据库，因为代码会漂移且权限复杂 | ⭐⭐⭐ Claude Code 团队的实践结论 | Boris |

### 3.12 Utilities（5 条 → 保留 2 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **Wispr Flow**：语音 prompting，10x 生产力 | ⭐⭐ 你可能没试过 | - |
| **Status line**：上下文感知和快速 compact | ⭐⭐ 你可能没配置 | Boris |

### 3.13 Daily（3 条 → 保留 1 条）

| 技巧 | 增量价值 | 来源 |
|------|---------|------|
| **每日更新 + 读 changelog**：Claude Code 迭代快，每天更新并读 changelog | ⭐ 基础但重要 | - |

---

## 四、对你最有价值的内容（Top 15）

### 4.1 立即可用（技术层面）

1. **`context: fork` 配置**：让 skills 在隔离 subagent 中运行，主上下文只看结果
2. **`` !`command` `` 嵌入**：在 SKILL.md 中注入动态 shell 输出
3. **`<important if="...">` 标签**：防止 CLAUDE.md 被忽略
4. **`/permissions` 通配符**：安全地预批准命令
5. **`/sandbox`**：减少 84% 权限提示

### 4.2 架构层面（需要重构）

6. **Hooks 系统**：你完全没用，但这是质量保证和自动化的关键
7. **Subagents 模式**：你没用 agents，但 test time compute 原理说明了为什么需要
8. **Product verification skills**：值得投资一周时间构建

### 4.3 工作流层面（习惯养成）

9. **挑战 Claude**：让 Claude 当审查者，反转主从关系
10. **Prototype > PRD**：构建 20-30 个版本而不是写 spec
11. **PR 大小量化**：p50 = 118 行，p90 = 498 行
12. **Always squash merge**：高速工作流的必备
13. **50% 手动 compact**：避免 agent dumb zone

### 4.4 元认知层面（思维模式）

14. **Agentic search > RAG**：Claude Code 团队的实践结论，验证了你的方向
15. **"不要 railroad Claude"**：给目标和约束，不要给逐步指令

---

## 五、结论与建议

### 5.1 你的体系优势

1. **垂直领域深度**：飞书生态覆盖完整，这是差异化优势
2. **工具箱丰富**：pdf, xlsx, docx, playwright-cli 等通用工具齐全
3. **Skills 数量合理**：39 个 skills 接近 gstack (29) 和 BMAD (43)，不过度膨胀

### 5.2 你的体系缺口

1. **Hooks 缺失**：完全没用，但这是自动化和质量保证的关键
2. **Agents 缺失**：没用 subagent 模式，错过了 test time compute 的优势
3. **开发工作流缺失**：没有 planning、code review、git workflow 类 skills
4. **Commands 未知**：不确定是否有工作流编排

### 5.3 建议动作（优先级排序）

#### 高优先级（立即行动）

1. **启用 `/sandbox`**：一行配置，减少 84% 权限提示
2. **配置 `/permissions` 通配符**：预批准常用命令
3. **在现有 skills 中添加 Gotchas section**：捕获 Claude 的失败模式
4. **检查 skills 的 description 字段**：确保是触发器而非摘要

#### 中优先级（本周完成）

5. **创建第一个 Hook**：PostToolUse hook 自动格式化代码
6. **创建第一个 Agent**：code-reviewer subagent，用于 PR 审查
7. **添加 `<important if="...">` 标签**：在 CLAUDE.md 中包裹关键规则
8. **构建 `/techdebt` command**：自动识别和消除重复代码

#### 低优先级（长期投资）

9. **Product verification skill**：为你的核心产品构建验证流程
10. **学习 8 大框架**：深入研究 Superpowers 和 Everything Claude Code
11. **构建 planning skill**：标准化你的规划流程
12. **探索 `context: fork`**：让计算密集型 skills 隔离运行

### 5.4 落地形式

**建议创建**：
- `~/.claude/hooks/post-tool-use-format.sh`：自动格式化 hook
- `~/.claude/agents/code-reviewer.md`：代码审查 agent
- `~/.claude/commands/techdebt.md`：技术债务识别 command
- `~/.claude/skills/*/SKILL.md`：在每个 skill 中添加 Gotchas section

**建议更新**：
- `~/.claude/settings.json`：添加 sandbox、permissions 配置
- `CLAUDE.md`：添加 `<important if="...">` 标签
- 所有 skills 的 `description` 字段：改为触发器语言

---

## 六、附录：框架独特性解读

### Superpowers (120k stars)
- **TDD-first**：测试驱动开发优先
- **Iron Laws**：不可违反的硬性规则
- **Whole-plan review**：完整计划审查机制

### Everything Claude Code (114k stars)
- **Instinct scoring**：直觉评分系统
- **AgentShield**：Agent 安全防护
- **Multi-lang rules**：多语言规则支持

### Spec Kit (83k stars)
- **Spec-driven**：规格驱动开发
- **Constitution**：宪法式规则系统
- **22+ tools**：22+ 工具集成

### gstack (54k stars)
- **Role personas**：角色人设系统
- **/codex review**：Codex 审查集成
- **Parallel sprints**：并行冲刺

### Get Shit Done (44k stars)
- **Fresh 200K contexts**：每次新鲜 200K 上下文
- **Wave execution**：波次执行模式
- **XML plans**：XML 格式计划

### BMAD-METHOD (43k stars)
- **Full SDLC**：完整软件开发生命周期
- **Agent personas**：Agent 人设系统
- **22+ platforms**：22+ 平台支持

### OpenSpec (35k stars)
- **Delta specs**：增量规格
- **Brownfield**：棕地项目支持
- **Artifact DAG**：产物有向无环图

### Compound Engineering (11k stars)
- **Compound Learning**：复合学习
- **Multi-Platform CLI**：多平台 CLI
- **Plugin Marketplace**：插件市场

---

**报告完成时间**：2026-03-29
**下一步**：根据建议动作优先级，逐步完善你的 Claude Code 体系