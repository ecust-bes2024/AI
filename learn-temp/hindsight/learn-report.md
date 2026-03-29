# /learn 分析报告：Hindsight — Agent 反思记忆系统

**源**: https://github.com/vectorize-io/hindsight
**类型**: 开源仓库 (MIT) — Agent 长期记忆基础设施
**作者**: Vectorize.io
**状态**: 生产级，LongMemEval SOTA，Fortune 500 企业在用

---

## 这是什么

Hindsight 是一个 agent 记忆系统，核心理念是让 agent **学习**而非仅仅**记忆**。它通过三个核心操作（Retain/Recall/Reflect）和自动化的"反思"机制（Consolidation），将原始对话事实逐步蒸馏为高层洞察。

与 RAG 和知识图谱的关键区别：不是简单检索，而是在存储时就用 LLM 提取结构化事实，在检索时用四路并行搜索+融合排序，在反思时用 agentic loop 分层推理。

---

## 核心价值

### 1. 四层记忆模型（实际是四种 fact_type）

| 层级 | fact_type | 来源 | 用途 |
|------|-----------|------|------|
| 世界事实 | `world` | Retain 时 LLM 提取 | 客观环境信息 |
| 经验事实 | `experience` | Retain 时 LLM 提取 | Agent 自身行为记录 |
| 观点 | `opinion` | Retain 时 LLM 提取 | 带 confidence_score (0-1) 的主观判断 |
| 观察 | `observation` | Consolidation 自动生成 | 从原始事实蒸馏的高层洞察 |

加上用户手动创建的 **Mental Models**（存在独立表中），形成五层知识金字塔。

### 2. 反思操作的触发条件和执行逻辑

**触发条件**：每次 Retain 操作完成后，自动触发 Consolidation 后台任务。

**执行逻辑**（`consolidation/consolidator.py`）：

```
1. 查询 consolidated_at IS NULL 的未处理记忆
2. 按 tag set 分组（安全隔离：不同 tag 的记忆不会共享 LLM 调用）
3. 对每批记忆：
   a. Recall 相关的已有 Observations
   b. 构建 prompt：新事实 + 已有观察 + Mission
   c. LLM 返回三种动作：
      - Create：新主题 → 创建新 observation
      - Update：已有主题有新证据 → 更新 observation
      - Delete：被新事实直接取代 → 删除旧 observation
   d. 自适应批次分裂：LLM 失败时对半分，直到 batch_size=1
4. 标记 consolidated_at，更新 proof_count 和 source_memory_ids
```

**关键设计**：Mission 驱动。每个 Bank 的 mission 定义"追踪什么"，默认是"追踪每个细节：名字、数字、日期、地点、关系"。

### 3. 从已有记忆自动生成新洞察

Consolidation prompt 的核心规则：
- **冗余**：同一信息不同措辞 → UPDATE 已有观察
- **矛盾/更新**：用时间标记捕获两种状态（"曾经X，现在Y"）
- **解析引用**：新事实提供具体值解析模糊占位符时 → UPDATE 嵌入解析值
- **永不合并**：不同人或无关主题的观察不合并

Observation 还有计算属性 **Trend**（基于证据时间戳）：
- `STABLE` — 证据分布在时间线上，持续到现在
- `STRENGTHENING` — 近期证据更多/更密
- `WEAKENING` — 证据主要是旧的，近期稀疏
- `NEW` — 所有证据在近期窗口内
- `STALE` — 近期窗口无证据

### 4. 记忆间关系发现算法

**Retain 阶段自动创建四种链接**（`MemoryLink` 表）：

| 链接类型 | 算法 | 权重 |
|----------|------|------|
| `temporal` | 时间接近的事实自动关联 | 0-1 |
| `semantic` | Embedding 余弦相似度超阈值 | 0-1 |
| `entity` | 共享同一实体的事实关联 | 0-1 |
| `causes/caused_by/enables/prevents` | LLM 提取因果关系 | 0-1 |

**实体解析**（`entity_resolver.py`）：
- spaCy NER 提取 + SequenceMatcher 消歧
- 两种策略：`full`（全量加载匹配）或 `trigram`（pg_trgm GIN 索引，大规模 bank 更快）
- 维护 `EntityCooccurrence` 物化缓存，用于图检索

**Recall 四路并行检索**（TEMPR）：
1. **Semantic** — pgvector HNSW 向量相似度
2. **BM25** — PostgreSQL 全文搜索
3. **Graph** — 实体共现图遍历（BFS/MPFP/LinkExpansion 可选）
4. **Temporal** — 时间感知搜索，支持"去年春天"等自然语言时间

四路结果通过 **Reciprocal Rank Fusion** (k=60) 合并，再经 cross-encoder reranking。

### 5. MCP 协议集成

基于 **FastMCP** 实现，支持两种传输：
- **stdio** — Claude Code 本地集成（`mcp_local.py`）
- **HTTP** — API 服务器集成（`api/mcp.py`）

完整工具集（27个 MCP tools）：
- 核心：`retain`, `recall`, `reflect`
- Bank 管理：`list_banks`, `create_bank`, `get_bank`, `update_bank`, `delete_bank`
- Mental Models：`list/get/create/update/delete/refresh_mental_model`
- Directives：`list/create/delete_directive`
- 记忆浏览：`list/get/delete_memory`, `list/get/delete_document`
- 运维：`list/get/cancel_operation`, `list_tags`, `get_bank_stats`, `clear_memories`

安全特性：
- Bank 级别工具过滤（`mcp_enabled_tools` 配置）
- Tag 隔离（不同 tag 的记忆不会交叉泄露）
- 审计日志（所有工具调用）
- 多租户 schema 隔离

---

## 数据结构详解

### 核心表结构

```
MemoryUnit (memory_units)
├── id: UUID (PK)
├── bank_id: Text
├── document_id: Text (FK → documents)
├── text: Text — 事实文本
├── embedding: Vector(EMBEDDING_DIM) — pgvector HNSW
├── context: Text — 分类上下文
├── event_date: Timestamp — 事件时间
├── occurred_start/end: Timestamp — 时间范围
├── mentioned_at: Timestamp — 提及时间
├── fact_type: Enum('world','experience','opinion','observation')
├── confidence_score: Float (0-1, opinion only)
├── source_memory_ids: UUID[] — observation 的来源记忆
├── proof_count: Int — 支持证据数量
├── consolidated_at: Timestamp — 已处理标记
├── tags: Text[] — 作用域标签
└── metadata: JSONB

Entity (entities)
├── id: UUID (PK)
├── canonical_name: Text
├── bank_id: Text
├── mention_count: Int
├── first_seen/last_seen: Timestamp
└── metadata: JSONB

MemoryLink (memory_links)
├── from_unit_id: UUID (FK)
├── to_unit_id: UUID (FK)
├── link_type: Enum('temporal','semantic','entity','causes','caused_by','enables','prevents')
├── entity_id: UUID (FK, nullable)
└── weight: Float (0-1)

Bank (banks)
├── bank_id: Text (PK)
├── disposition: JSONB {skepticism:3, literalism:3, empathy:3}
└── background: Text (mission)
```

### Reflect Agent 工具链

```
reflect_async(query)
  → run_reflect_agent() — agentic loop
    ├── Iteration 1..N (budget-controlled):
    │   ├── LLM with tools → tool_calls
    │   ├── search_mental_models(q) → 用户策展的高质量摘要
    │   ├── search_observations(q) → 自动合成的知识 + freshness
    │   ├── recall(q) → 原始事实（ground truth）
    │   ├── expand(ids, depth) → chunk/document 上下文
    │   └── done(answer) → 最终回答
    ├── Context overflow guard → 强制合成
    └── Last iteration → 移除工具，强制文本回答
```

---

## 直接可用性

**轻包装可用** — 原因：

- 问题适配：★★★★☆ — 解决 agent 长期记忆的核心问题，三通道模型+反思机制正是我们需要的
- 集成成本：★★★☆☆ — Docker 一键部署，MCP 原生支持 Claude Code，但需要 PostgreSQL + pgvector
- 维护成本：★★★☆☆ — MIT 开源，活跃维护，但依赖 PostgreSQL 运维
- 依赖风险：★★★☆☆ — 需要 LLM API（OpenAI/Anthropic/etc），PostgreSQL，pgvector
- 可替换性：★★★★☆ — MCP 接口标准化，可以在本地接口后面替换
- 重建理由：★★☆☆☆ — 核心价值在 consolidation 算法和 TEMPR 检索，重建成本极高

---

## 值得学习

### 战略层

1. **"学习而非记忆"范式** — 记忆系统的价值不在存储和检索，而在从经验中提炼洞察。这是从 RAG 到 Agent Memory 的范式跃迁。

2. **Consolidation 作为核心差异化** — 大多数记忆系统只做 store+retrieve。Hindsight 的 consolidation（自动从原始事实生成 observations）是真正的护城河。这不是 RAG，是认知。

3. **分层知识金字塔** — Raw Facts → Observations → Mental Models 的三层结构，对应人类认知的 感知→归纳→心智模型。每层有不同的生成方式、更新频率和信任度。

### 操作层

4. **TEMPR 四路并行检索 + RRF 融合** — 不依赖单一检索策略，四路并行（语义/关键词/图/时间）+ Reciprocal Rank Fusion 合并。这是检索质量的关键。

5. **Mission-driven Consolidation** — Bank 的 mission 定义"追踪什么"，让同一个引擎服务不同用途的 agent。这比硬编码规则灵活得多。

6. **Observation Trend 计算** — 从证据时间戳自动计算趋势（stable/strengthening/weakening/new/stale），让 agent 知道哪些知识在变化。

7. **Tag 隔离安全模型** — 不同 tag 的记忆在 consolidation 和 reflect 中完全隔离，防止信息泄露。这是多租户/多用户场景的关键。

8. **自适应批次分裂** — Consolidation 失败时对半分批重试，直到单条记忆级别。优雅降级而非全批失败。

9. **Reflect Agent 的 Context Budget Guard** — 在 token 预算耗尽前主动强制合成，而非等到 context overflow 报错。

10. **PostgreSQL 单存储层** — 不引入额外的向量数据库，pgvector HNSW 够用。Boring Technology 原则的典范。

---

## 不要复制

1. **PostgreSQL 深度耦合** — 整个系统围绕 PostgreSQL + pgvector 构建，包括 schema migration、fq_table() 多租户隔离、asyncpg 连接池。如果我们的技术栈不同，不要照搬。

2. **LLM Provider 抽象层** — 支持 7+ 个 LLM provider 的抽象层（OpenAI/Anthropic/Gemini/Groq/Ollama/LMStudio/LiteLLM），对我们来说过度工程。

3. **FastMCP 2.x/3.x 兼容层** — `_apply_bank_tool_filtering` 里同时兼容 FastMCP 2.x 和 3.x 的 monkey-patching，这是库版本兼容的技术债。

4. **spaCy NER 依赖** — 实体提取用 spaCy，这是一个重量级依赖。如果只需要简单实体识别，LLM 本身就够了。

5. **7954 行的 memory_engine.py** — 这是一个 God Object，所有核心逻辑都在一个文件里。不要复制这种代码组织方式。

---

## 建议动作

**wrap-lightly** — 轻度包装后集成

原因：Hindsight 的核心价值（consolidation 算法、TEMPR 检索、分层知识模型）重建成本极高，且已经是 SOTA。但它是一个完整的服务端系统，需要在本地接口后面包装以保持控制。

## 建议落地形式

**memory + external-tool-integration**

1. **Memory**：将三通道记忆模型、consolidation 触发逻辑、TEMPR 检索策略、observation trend 计算等核心设计原则存为记忆，指导我们自己的记忆系统设计。

2. **External-tool integration**：通过 MCP 或 Docker API 将 Hindsight 作为外部记忆后端集成，在本地包装一层控制接口。

---

## 最佳下一步

"要我设计一个轻量包装层，通过 MCP 将 Hindsight 集成为 Auto Company 的 agent 记忆后端？还是先把核心设计原则存为记忆，等需要时再决定集成方案？"
