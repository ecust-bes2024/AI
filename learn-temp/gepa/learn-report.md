# GEPA (Genetic-Pareto) 深度分析报告

## 这是什么

GEPA 是 UC Berkeley 开发的文本参数优化框架。核心思路：用 LLM 读执行 trace 来诊断失败原因，然后做定向变异（而非随机变异），通过 Pareto 前沿保持多样性。MIT 协议，v0.1.1，已被 Shopify/Databricks/Dropbox/OpenAI/Pydantic/MLflow 等 50+ 生产环境使用。

## 核心价值

### 1. 反射式进化算法（核心创新）

传统优化器只知道 candidate 失败了（标量 reward），不知道为什么。GEPA 的关键突破：

**Actionable Side Information (ASI)** — 文本优化的"梯度"类比：
- RL 的梯度告诉数值优化器往哪个方向走
- ASI 告诉 LLM proposer *为什么*失败、*怎么*修复
- ASI 可以是错误信息、profiling 数据、推理日志、甚至图片

**五步循环：**
1. **Select** — 从 Pareto 前沿按频率加权随机选一个 candidate
2. **Execute** — 在 minibatch 上执行，捕获完整执行 trace
3. **Reflect** — LLM 读 trace（错误信息、profiler 输出、推理日志）诊断失败
4. **Mutate** — 基于诊断结果生成改进的 candidate（定向变异）
5. **Accept** — 如果 minibatch 上 sum(scores) 严格提升，加入候选池，更新 Pareto 前沿

### 2. Pareto 前沿多样性保持

不是只保留"最好的"，而是保留"在某些任务上最好的"：

**四种 Frontier 类型：**
- `instance` — 每个验证样本独立追踪最佳 candidate
- `objective` — 每个目标指标独立追踪
- `hybrid` — 同时追踪 instance 和 objective
- `cartesian` — 样本 × 目标的笛卡尔积

**Candidate 选择机制：**
- `ParetoCandidateSelector` — 从 Pareto 前沿按频率加权随机采样（核心策略）
- 先用 `remove_dominated_programs` 去除被支配的 candidate
- 每个 candidate 在前沿中出现的频率 = 它的采样权重
- 这确保了"在某些任务上独特优秀"的 candidate 不会被平均分数淹没

### 3. 系统感知合并（Merge）

当两个 Pareto 最优 candidate 在不同任务上擅长时，尝试合并它们的优势：

**合并逻辑：**
- 找两个 candidate 的共同祖先
- 对每个 component：如果一个 candidate 保留了祖先的值而另一个改变了，用改变的那个
- 如果两个都改变了，选分数更高的那个
- 合并后在 subsample 上评估，必须 >= max(两个父代) 才接受

### 4. 效率优势来源（100-500 vs RL 5000-25000+）

**为什么比 RL 快 35x：**
1. **信息密度**：RL 把执行 trace 压缩成标量 reward，丢失了"为什么失败"的信息。GEPA 让 LLM 读完整 trace，每次评估提取的信息量远大于 RL
2. **定向变异 vs 随机探索**：RL 在参数空间随机探索，GEPA 基于诊断做定向修改
3. **Minibatch 接受测试**：只需在小 batch 上证明改进就接受，不需要全量评估
4. **评估缓存**：`EvaluationCache` 按 (candidate_hash, example_id) 缓存结果，避免重复评估
5. **Pareto 保持多样性**：不会因为平均分数下降而丢弃在特定任务上优秀的 candidate

### 5. optimize_anything：三种优化模式

统一 API 支持三种范式：
1. **Single-Task Search** — 解决一个难题（如圆填充、数学优化）
2. **Multi-Task Search** — 解决一批相关问题，跨任务迁移（如 CUDA kernel 生成）
3. **Generalization** — 构建泛化到未见问题的技能（如 prompt 优化、agent 架构发现）

### 6. gskill：自动学习 coding agent 技能

最令人兴奋的应用：
- 用 SWE-smith 从 GitHub 仓库自动生成可验证任务
- 用 GEPA 进化 agent 的 skill 文件
- 在 gpt-5-mini 上学到的技能可以迁移到 Claude Code
- Jinja: 55% → 82%，Bleve: 24% → 93%
- 技能跨模型迁移：Claude Haiku 4.5 在 Bleve 上 79.3% → 100%

## 架构解剖

```
GEPAEngine (主循环)
├── ReflectiveMutationProposer (反射式变异)
│   ├── CandidateSelector (从 Pareto 前沿选 candidate)
│   ├── BatchSampler (epoch-shuffled minibatch)
│   ├── ComponentSelector (round-robin 或 all)
│   ├── GEPAAdapter.evaluate(capture_traces=True) → 执行 + 捕获 trace
│   ├── GEPAAdapter.make_reflective_dataset() → 构建反射数据集
│   └── InstructionProposalSignature → LLM 生成新指令
├── MergeProposer (合并两个 Pareto 最优 candidate)
├── GEPAState (持久化状态：candidates, Pareto 前沿, 评估缓存)
└── EvaluationPolicy (全量评估 or 增量评估)
```

**关键接口 — GEPAAdapter：**
- `evaluate(batch, candidate, capture_traces)` — 执行 candidate，返回 scores + trajectories
- `make_reflective_dataset(candidate, eval_batch, components_to_update)` — 从 trace 构建反射数据集
- `propose_new_texts` (可选) — 自定义提案逻辑

**InstructionProposalSignature 的默认 prompt：**
```
我给了助手以下指令来执行任务：
<curr_param>

以下是不同任务输入的示例，以及助手的响应和反馈：
<side_info>

你的任务是写一个新的指令...
识别所有领域特定的事实信息...
如果助手使用了可泛化的策略，也包含在指令中...
```

## 直接可用性

**直接可用** — 作为 Python 库 `pip install gepa`

**集成成本：低**
- 实现 `GEPAAdapter` 接口（evaluate + make_reflective_dataset）
- 或直接用 `optimize_anything` API（更简单，只需 evaluator 函数）

**维护成本：低**
- MIT 协议，活跃维护
- 已集成到 DSPy、MLflow、Pydantic、Comet ML 等主流框架

## 值得学习

### 战略层（趋势/范式判断）

1. **"文本即可优化参数"范式** — 任何可序列化为文本且可度量的东西都能优化。这是一个比 prompt engineering 大得多的范式
2. **ASI > 标量 Reward** — 信息密度决定优化效率。RL 的根本瓶颈不是算法，是信息压缩损失
3. **Pareto 前沿 > 单一最优** — 在多任务场景下，保持多样性比追求单一最优更重要
4. **反射式进化 > 随机变异** — LLM 读 trace 做定向变异，是进化算法的范式升级
5. **技能可跨模型迁移** — 在弱模型上学到的技能可以提升强模型，这意味着优化成本可以大幅降低

### 操作层（可复用的原则/checklist）

1. **Adapter 模式** — evaluate + make_reflective_dataset 的分离设计，让优化引擎与具体系统解耦
2. **Minibatch 接受测试** — 不需要全量评估就能判断改进，大幅降低评估成本
3. **评估缓存** — 按 (candidate_hash, example_id) 缓存，避免重复评估
4. **Component 轮转更新** — 多组件系统中，round-robin 逐个更新而非同时更新所有
5. **合并需要共同祖先** — 不是随机合并两个好的 candidate，而是找到它们的共同祖先来指导合并
6. **oa.log() 模式** — 在 evaluator 内部用 log 捕获诊断信息，比返回值更灵活
7. **三种优化模式统一** — single-task / multi-task / generalization 用同一个 API

## 不要复制

1. **DSPy 耦合** — GEPA 与 DSPy 有历史耦合（原名 MIPRO v2），独立使用时不需要 DSPy 依赖
2. **LiteLLM 依赖** — 如果已有自己的 LLM 调用层，不需要引入 LiteLLM
3. **具体的 prompt 模板** — InstructionProposalSignature 的默认 prompt 是为通用场景设计的，具体应用需要定制
4. **Cloudpickle 序列化** — 状态持久化用 pickle，在跨版本兼容性上有风险

## 建议动作

**absorb-partially** — 核心算法思想极其有价值，但完整框架对我们的场景可能过重。

建议：
1. **直接使用 `optimize_anything` API** 用于 prompt/skill 优化场景
2. **提取核心算法思想** 用于方法论自动优化：
   - ASI（Actionable Side Information）模式
   - Pareto 前沿多样性保持
   - 反射式定向变异
   - Minibatch 接受测试
3. **gskill 模式** 可以直接应用到 Auto Company 的 agent 技能进化

## 建议落地形式

1. **memory** — 核心算法原则和设计模式（ASI、Pareto 前沿、反射式变异）
2. **TODO-design-doc** — 将 GEPA 思路应用到 Auto Company 方法论自动优化的设计文档
3. **external-tool-integration** — 直接使用 `gepa` 库进行 prompt/skill 优化

## 最佳下一步

将 GEPA 的核心思想（ASI + Pareto 前沿 + 反射式变异）提炼为记忆，然后评估是否在 Auto Company 中直接集成 `optimize_anything` 来进化 agent 技能。
