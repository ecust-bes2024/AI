# GitHub 方法论内化项目研究报告

> 调研日期：2026-03-29
> 调研范围：GitHub 开源项目 + Gist，覆盖 agent memory、cursor rules、CLAUDE.md、AI second brain、knowledge management、prompt evolution 等关键词
> 信息可信度标注：confirmed = 直接验证 | likely = 多源交叉 | speculative = 单一来源推测

---

## 一、核心发现

**结论先行**：GitHub 上"方法论内化给 AI agent"的实现分为四个清晰的层次，从低到高：

1. **静态规则集合**（最多，最成熟）— 把人类知识写成 rules 文件喂给 AI
2. **持久化记忆系统**（快速增长）— 让 AI 跨会话记住学到的东西
3. **知识图谱引擎**（技术最深）— 不只记住，还要理解关系和结构
4. **反思进化系统**（最前沿）— AI 自己优化自己的方法论

我们的 `/learn` 功能横跨第 1-2 层，有向第 4 层进化的潜力。

---

## 二、项目清单（按实现模式分类）

### A. 静态配置型 — "把方法论写成规则"

| 项目 | Stars | 核心功能 | 技术栈 |
|------|-------|----------|--------|
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | 38,746 | Cursor AI 规则文件的最大集合，按语言/框架分类 | Markdown |
| [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | 23,766 | Claude Code 最佳实践集合 | Markdown |
| [coleam00/context-engineering-intro](https://github.com/coleam00/context-engineering-intro) | 12,989 | "Context Engineering" 方法论，系统化管理 AI 上下文 | Markdown |
| [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure) | 10,670 | 个人 AI 基础设施，TELOS 文档体系 + 技能系统 + 三层记忆 | Python/Shell |
| [spdustin/ChatGPT-AutoExpert](https://github.com/spdustin/ChatGPT-AutoExpert) | 6,662 | ChatGPT 超级自定义指令，让 AI 自动切换专家角色 | Markdown |
| [steipete/agent-rules](https://github.com/steipete/agent-rules) | 5,654 | 跨 agent 通用规则集（Claude Code + Cursor） | Markdown |
| [sanjeed5/awesome-cursor-rules-mdc](https://github.com/sanjeed5/awesome-cursor-rules-mdc) | 3,422 | Cursor .mdc 规则文件集合 | Markdown |
| [NeekChaw/RIPER-5](https://github.com/NeekChaw/RIPER-5) | 2,572 | "神级 Cursor Rule"，结构化的 AI 编码工作流 | Markdown |
| [instructa/ai-prompts](https://github.com/instructa/ai-prompts) | 1,026 | 跨工具 AI 提示词集合（Cursor/Cline/Windsurf/Copilot） | Markdown |
| [botingw/rulebook-ai](https://github.com/botingw/rulebook-ai) | 584 | 通用规则管理 CLI，Pack 模型 + memory bank + 多工具同步 | TypeScript |
| [nickbaumann98/cline_docs](https://github.com/nickbaumann98/cline_docs) | 579 | Cline Memory Bank 系统，6 个结构化 Markdown 文件 | Markdown |
| [josix/awesome-claude-md](https://github.com/josix/awesome-claude-md) | 180 | CLAUDE.md 最佳实践集合与分析 | Markdown |

### B. 动态学习型 — "让 AI 记住并学习"

| 项目 | Stars | 核心功能 | 技术栈 |
|------|-------|----------|--------|
| [danielmiessler/fabric](https://github.com/danielmiessler/fabric) | 40,222 | AI 增强框架，Pattern 系统（可复用任务提示词），CLI + REST API | Go |
| [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) | 6,547 | 仿生记忆系统：世界事实 + 经验 + 心智模型三层，自动反思生成新洞察 | Python |
| [basicmachines-co/basic-memory](https://github.com/basicmachines-co/basic-memory) | 2,717 | Markdown 语义图谱，双向同步 Obsidian，MCP 协议集成 | Python/SQLite |
| [Gentleman-Programming/engram](https://github.com/Gentleman-Programming/engram) | 1,985 | 编码 agent 持久记忆，SQLite+FTS5，MCP/HTTP/CLI/TUI 多接口 | Go |
| [agiresearch/A-mem](https://github.com/agiresearch/A-mem) | 940 | A-MEM：NeurIPS 2025 论文，Agentic Memory for LLM Agents | Python |
| [coleam00/mcp-mem0](https://github.com/coleam00/mcp-mem0) | 664 | Mem0 的 MCP 服务器封装，长期 agent 记忆 | Python |
| [AVIDS2/memorix](https://github.com/AVIDS2/memorix) | 337 | 跨 agent 记忆层（MCP），兼容 Cursor/Claude Code/Codex/Windsurf 等 | TypeScript |
| [Dicklesworthstone/cass_memory_system](https://github.com/Dicklesworthstone/cass_memory_system) | 299 | 程序性记忆：三层认知架构（情景→工作→程序性），置信度衰减机制 | Python |
| [gavdalf/total-recall](https://github.com/gavdalf/total-recall) | 244 | 五层观察式记忆，自主监控，~$0.10/月 | Python |

### C. 知识图谱引擎型 — "不只记住，还要理解"

| 项目 | Stars | 核心功能 | 技术栈 |
|------|-------|----------|--------|
| [QuivrHQ/quivr](https://github.com/QuivrHQ/quivr) | 39,071 | GenAI 第二大脑，RAG 框架，支持多种 LLM 和向量存储 | Python |
| [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | 33,672 | AI 第二大脑，自托管，深度研究 + 自动化调度 + 自定义 agent | Python |
| [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory) | 20,209 | 极速可扩展的记忆 API，为 AI 时代设计 | TypeScript |
| [topoteretes/cognee](https://github.com/topoteretes/cognee) | 14,743 | 知识引擎：向量搜索 + 图数据库 + 认知科学，6 行代码集成 | Python |
| [coleam00/Archon](https://github.com/coleam00/Archon) | 13,844 | AI 编码助手的知识和任务管理骨架 | Python |
| [reorproject/reor](https://github.com/reorproject/reor) | 8,545 | 本地优先的 AI 个人知识管理，面向"高熵人群" | TypeScript/Electron |

### D. 反思进化型 — "AI 自己优化自己"

| 项目 | Stars | 核心功能 | 技术栈 |
|------|-------|----------|--------|
| [gepa-ai/gepa](https://github.com/gepa-ai/gepa) | 3,029 | 反思式文本进化：遗传-帕累托优化，LLM 分析失败原因后定向变异 | Python |
| [yizhongw/self-instruct](https://github.com/yizhongw/self-instruct) | ~6,000 | 自指令：LLM 用自己生成的指令数据对齐自己 | Python |

---

## 三、技术实现分析

### 3.1 静态配置型的实现模式

**核心机制**：人类手写规则 → 放入约定位置 → AI 启动时加载

| 实现方式 | 代表项目 | 加载机制 |
|----------|----------|----------|
| `.cursorrules` / `.mdc` 文件 | awesome-cursorrules | Cursor IDE 自动读取项目根目录文件 |
| `CLAUDE.md` 文件 | awesome-claude-md, claude-code-best-practice | Claude Code 自动加载项目/全局配置 |
| `.github/copilot-instructions.md` | awesome-copilot-instructions | GitHub Copilot 读取仓库级指令 |
| Memory Bank（6 文件结构） | cline_docs | Cline 每次任务开始时强制读取全部文件 |
| Pack 模型（统一生成多格式） | rulebook-ai | CLI 工具将 Pack 定义翻译为各工具的原生格式 |

**关键洞察** (confirmed)：
- 这是目前最主流的方式，38K+ stars 的 awesome-cursorrules 证明了需求规模
- 本质是"人类专家知识的序列化"——把方法论写成 AI 能理解的指令
- 局限：纯手工维护，不会自动进化，跨工具需要重复适配

### 3.2 动态学习型的实现模式

**核心机制**：AI 工作过程中自动提取经验 → 持久化存储 → 下次会话检索

三种主要技术路线：

**路线 A：文件系统 + 全文搜索**
- 代表：Engram（SQLite + FTS5）、Basic Memory（Markdown + SQLite）
- 优势：零依赖，本地优先，人类可读
- 劣势：语义理解有限，依赖关键词匹配

**路线 B：MCP 协议集成**
- 代表：memorix、mcp-mem0、Engram
- 优势：跨 agent 通用（Cursor/Claude Code/Codex 都支持 MCP）
- 劣势：需要 MCP 运行时支持

**路线 C：认知架构模拟**
- 代表：CASS（三层认知）、Hindsight（仿生三通道）、A-MEM（Agentic Memory）
- 优势：更接近人类记忆的工作方式，有遗忘和强化机制
- 劣势：复杂度高，需要额外计算资源

**关键洞察** (confirmed)：
- CASS 的"置信度衰减"机制值得关注：规则每 90 天不被验证就衰减，有害标记 4x 权重
- Hindsight 的"反思"操作是突破点：不只存储，还会对已有记忆进行二次分析生成新洞察
- Engram 的极简设计（单二进制文件 + SQLite）是工程上的最佳实践

### 3.3 知识图谱引擎型的实现模式

**核心机制**：文档 → 实体/关系提取 → 图结构存储 → 图遍历检索

- Cognee：向量搜索 + 图数据库 + 本体论锚定，6 行代码集成
- Basic Memory：Markdown wiki-link 构建语义图谱，双向同步 Obsidian
- Khoj：自托管 AI 第二大脑，支持深度研究和自动化调度

**关键洞察** (likely)：
- 图结构比纯向量检索更适合"方法论内化"——方法论本身就是概念间的关系网络
- 但图数据库的维护成本高，对一人公司来说可能过重

### 3.4 反思进化型的实现模式

**核心机制**：候选方案 → 执行 → 分析失败原因 → 定向变异 → 迭代

- GEPA 的核心创新：不用 RL 的标量奖励，而是让 LLM 读完整的执行 trace 来理解"为什么失败"
- 只需 100-500 次评估（vs RL 的 5000-25000+），效率高一个数量级
- 支持 Pareto 前沿上的多目标优化

**关键洞察** (likely)：
- 这是最接近"吸星大法"理想形态的技术——AI 不只是被动接收规则，而是主动优化自己的方法论
- 但目前主要用于 prompt 优化，还没有人把它用于"从外部资源自动提取并内化方法论"

---

## 四、与 /learn 的对比分析

### 我们的 /learn 做了什么

`/learn` 是一个"分析外部资源后决定是否吸收内化"的技能。核心流程：
1. 输入外部资源（仓库、文章、代码、工作流等）
2. 分析资源内容，提取关键信息
3. 决定是否内化、如何内化
4. 产出分两层：战略层（趋势/范式）+ 操作层（原则/checklist）

### 对比矩阵

| 维度 | /learn | 静态规则集合 | 动态记忆系统 | 知识图谱引擎 | 反思进化 |
|------|--------|-------------|-------------|-------------|---------|
| 知识来源 | 外部资源（主动吸收） | 人类手写 | AI 工作经验 | 文档/对话 | 执行 trace |
| 内化方式 | LLM 分析 + 人类决策 | 直接复制 | 自动提取 | 实体/关系提取 | 遗传变异 |
| 存储形式 | Markdown 记忆文件 | 规则文件 | DB/文件 | 图数据库 | 候选池 |
| 进化能力 | 无（一次性） | 无 | 有限（衰减） | 有限（图更新） | 强（自动优化） |
| 跨工具 | Claude Code 专属 | 工具特定 | MCP 跨工具 | API 跨工具 | 框架内 |
| 人类参与 | 触发 + 审批 | 全程手工 | 最小 | 最小 | 最小 |

### /learn 的独特优势

1. **主动吸收外部知识**：大多数系统只处理"自己产生的经验"，/learn 能从外部资源主动提取
2. **两层产出**：战略层 + 操作层的分离是独特的，其他系统没有这个区分
3. **人类审批门控**：在自动化和可控性之间取得平衡

### /learn 的差距

1. **不会自动进化**：吸收后的知识是静态的，不会随使用反馈自动优化
2. **没有置信度机制**：不知道哪些内化的知识有效、哪些过时
3. **没有跨会话记忆**：每次 /learn 是独立的，不会积累"学习经验"
4. **没有关系图谱**：内化的知识是扁平的，不理解概念间的关系

---

## 五、值得借鉴的设计理念

### 5.1 CASS 的置信度衰减机制 (HIGH PRIORITY)

**理念**：内化的规则不是永恒的，应该有"保质期"。
- 每 90 天不被验证就衰减
- 有害标记权重 4x
- 规则从 candidate → established → proven 逐步成熟

**对 /learn 的启示**：内化的方法论应该有 freshness score，长期不被使用或被证明无效的应该自动降权或标记过时。

### 5.2 Hindsight 的反思操作 (HIGH PRIORITY)

**理念**：不只存储原始记忆，还要定期"反思"已有记忆生成新洞察。
- 世界事实 + 经验 → 心智模型
- 自动发现记忆间的新连接

**对 /learn 的启示**：定期对已内化的知识进行"元分析"——哪些知识被频繁使用？哪些互相矛盾？能否合并或升级？

### 5.3 Fabric 的 Pattern 系统 (MEDIUM PRIORITY)

**理念**：把 AI 能力模块化为可复用的 Pattern，用户可以组合、分享、迭代。
- 40K+ stars 证明了"可复用 AI 能力单元"的巨大需求
- CLI 优先的设计让 Pattern 可以嵌入任何工作流

**对 /learn 的启示**：内化的方法论可以输出为可复用的 Skill/Pattern，而不只是记忆文件。

### 5.4 GEPA 的反思式进化 (LONG TERM)

**理念**：让 AI 读完整的执行 trace 来理解失败原因，然后定向改进。
- 比 RL 高效一个数量级
- 支持多目标优化

**对 /learn 的启示**：未来可以让 /learn 不只是"一次性吸收"，而是"持续优化"——根据实际使用效果自动调整内化的方法论。

### 5.5 Rulebook-AI 的跨工具同步 (MEDIUM PRIORITY)

**理念**：一份规则定义，自动生成多个工具的原生格式。
- Pack 模型 + `project sync` 命令
- 支持 Cursor/Copilot/Claude Code/Gemini CLI 等

**对 /learn 的启示**：内化的知识不应该锁定在 Claude Code 里，应该能导出为其他工具的格式。

### 5.6 Context Engineering 的系统化方法 (MEDIUM PRIORITY)

**理念**：把 AI 上下文管理当作工程学科来对待。
- 12K+ stars 说明"context engineering"正在成为一个独立领域
- 核心观点：AI 的输出质量 = f(上下文质量)

**对 /learn 的启示**：/learn 本质上就是 context engineering 的一种实现——通过吸收外部知识来提升 AI 的上下文质量。

---

## 六、信息盲区

以下是本次调研未能覆盖的领域：

1. **闭源产品**：ChatGPT Memory、Claude Projects 的内部实现细节无法获取
2. **企业级方案**：Notion AI、Confluence AI 等企业知识管理工具的 AI 内化机制
3. **学术前沿**：NeurIPS/ICML 2025-2026 关于 agent memory 的最新论文（A-MEM 只是冰山一角）
4. **中文社区**：国内的 AI agent 方法论内化实践（飞书/钉钉生态）
5. **实际效果数据**：这些项目的实际使用效果和用户反馈数据有限

---

## 七、战略建议

基于以上分析，对"吸星大法"功能的建议优先级：

| 优先级 | 建议 | 理由 |
|--------|------|------|
| P0 | 给 /learn 产出添加置信度和 freshness 机制 | CASS 验证了这个模式，防止知识腐化 |
| P0 | 实现"反思"功能：定期元分析已内化知识 | Hindsight 证明了反思能产生新洞察 |
| P1 | 将内化知识输出为可复用 Skill/Pattern | Fabric 40K stars 证明了需求 |
| P1 | 支持跨工具格式导出 | Rulebook-AI 的 Pack 模型是好参考 |
| P2 | 引入 GEPA 式的反思进化机制 | 长期方向，让方法论自动优化 |
| P2 | 构建知识关系图谱 | 理解概念间关系，但实现成本高 |
