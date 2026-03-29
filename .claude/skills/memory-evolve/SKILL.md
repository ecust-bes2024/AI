---
name: memory-evolve
description: GEPA 反思式进化闭环：基于使用效果数据，用 ASI + 定向变异自动优化记忆/规则/技能。让方法论自己进化。
user-invocable: true
triggers:
  - evolve
  - evolve-memory
---

# Memory Evolution — GEPA 反思式进化闭环

基于 GEPA 核心算法（ASI + Pareto 前沿 + 定向变异），分析记忆系统的使用效果，自动生成优化提案。

核心理念：不是随机改进，而是读"执行 trace"做定向变异。

## Instructions

### Step 1: 采集系统状态（Observe）

并行执行：

1. 运行健康检查：
```bash
bash /Users/jerry_hu/AI/.claude/hooks/check-stale-memories.sh
```

2. 读取所有 memory 文件的 frontmatter，提取：
   - feedback_count（引用次数 = 使用信号）
   - last_referenced（最近引用 = 活跃度）
   - maturity（成熟度 = 信任等级）
   - confidence + 衰减后的 effective confidence
   - type（fact/feedback/decision/reference）

3. 扫描最近的 git log（最近 20 条 commit），识别：
   - 哪些 memory 文件被修改过（= 活跃进化中）
   - 哪些 skill 文件被修改过（= 能力在迭代）
   - 哪些 CLAUDE.md 规则被调整过（= 规则在演变）

4. 检查 steering 文件，确认反馈追踪机制是否正常运行

### Step 2: 构建 ASI 诊断数据集（Reflect）

ASI = Actionable Side Information，不是标量分数，而是"为什么好/为什么差"的诊断信息。

对每条记忆生成诊断：

| 信号 | 诊断 | 含义 |
|------|------|------|
| feedback_count 高 + maturity 低 | 被频繁使用但未升级 | 应该晋升 |
| feedback_count 0 + age > 30天 | 从未被引用 | 可能无用或发现性差 |
| confidence 衰减 > 50% | 长期未验证 | 需要验证或归档 |
| 多条记忆 feedback_count 都高 | 同一领域多条活跃 | 可能需要合并为更强的单条 |
| 某条记忆被引用后用户纠正 | 记忆内容有误 | 需要修正或标记 harmful |
| /learn 产出只进了 Memory | 路由可能过于保守 | 检查是否应该升级为 Skill/Rule |

### Step 3: 生成进化提案（Mutate）

基于 ASI 诊断，生成定向变异提案。每个提案必须说明：
- **变异目标**：哪个文件
- **变异类型**：Promote / Demote / Merge / Split / Rewrite / Route-Change
- **ASI 依据**：为什么做这个变异（不是随机的）
- **预期效果**：变异后会怎样

#### 变异类型定义

**Promote（晋升）**
- candidate → established：feedback_count ≥ 3，内容被实践验证
- established → proven：feedback_count ≥ 10，无负面反馈
- Memory → Skill：某条记忆反复被引用来指导"如何做某事" → 应该变成 Skill
- Memory → Rule：某条记忆是"必须/禁止"类指令 → 应该进 CLAUDE.md

**Demote（降级）**
- proven → established：新证据表明内容部分过时
- established → candidate：长期未引用 + confidence 衰减严重
- 任何 → deprecated：被证伪

**Merge（合并）**
- 两条记忆覆盖同一主题 → 合并为一条更强的记忆
- 合并时保留所有独特信息，提升 confidence

**Split（拆分）**
- 一条记忆覆盖多个不相关主题 → 拆分为多条专注记忆

**Rewrite（重写）**
- 内容过时但主题仍有价值 → 保留框架，更新内容
- 操作层细节变化但战略层判断不变 → 只更新操作层

**Route-Change（路由变更）**
- Memory 中的"如何做"类内容 → 迁移为 Skill
- Memory 中的"必须/禁止"类内容 → 迁移为 CLAUDE.md Rule
- 过于具体的 Rule → 降级为 Memory

### Step 4: Pareto 前沿评估（Evaluate）

不追求单一最优，保持多样性：

对每个提案评估三个维度：
1. **实用性**：变异后是否更容易被引用和使用？
2. **准确性**：变异后内容是否更准确？
3. **精炼度**：变异后是否更紧凑、信噪比更高？

如果一个提案在某个维度上明显更好，即使其他维度持平，也值得保留（Pareto 最优）。

### Step 5: 输出进化报告

```markdown
## Evolution Report — [日期]

### 系统健康概览
- 记忆总数：X | 活跃(refs>0)：X | 休眠(refs=0)：X
- Maturity：candidate X / established X / proven X / deprecated X
- 平均 effective confidence：X.XX
- 最近 30 天变更：X 次

### ASI 诊断摘要
[关键发现，2-3 句话]

### 进化提案

| # | 类型 | 目标 | ASI 依据 | 预期效果 | Pareto 评估 |
|---|------|------|----------|----------|-------------|
| 1 | Promote | X.md | refs=5, 内容验证 | candidate→established | 实用↑ 准确= 精炼= |
| 2 | Merge | A+B | 80%重叠 | 1条更强记忆 | 实用= 准确= 精炼↑ |
| 3 | Route | C.md | "如何做"类内容 | Memory→Skill | 实用↑ 准确= 精炼= |

### 不建议变异的记忆
[列出状态良好、无需操作的记忆，说明为什么不动]
```

### Step 6: 执行已批准的变异

用户逐条确认后执行。每次变异后：
1. 更新目标文件
2. 更新 MEMORY.md 索引
3. 记录变异历史到 frontmatter（可选：添加 `evolved_from` 字段）
4. 重新运行健康检查确认改善

### Step 7: 记录进化轨迹

将本次进化的关键决策记录为一条新的 memory（type: decision），包含：
- 做了什么变异
- 为什么（ASI 依据）
- 预期效果
- 实际效果（下次 /evolve 时回顾）

这形成了进化的"执行 trace"，让下一次 /evolve 能读到上次的决策和效果，实现真正的闭环。

## Guidelines

- **定向变异，不是随机改进**：每个提案必须有 ASI 依据，不能"感觉应该改"
- **保守执行**：宁可不变，不可误变。不确定的提案标记为"观察中"
- **Pareto 多样性**：不要为了某个维度牺牲其他维度。保持记忆系统的多样性
- **永不删除**：deprecated 的记忆保留文件，标记归档，不物理删除
- **闭环追踪**：每次进化都记录 trace，下次进化时回顾效果
- **建议频率**：每 1-2 周运行一次，或在大量 /learn 吸收后运行

$ARGUMENTS
