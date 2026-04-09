---
name: memory-consolidation
description: 对记忆文件进行元分析，发现矛盾、冗余、stale 记忆，建议合并/修剪/晋升操作。定期反思，让记忆系统越用越精炼。
user-invocable: true
triggers:
  - consolidate
  - reflect
---

# Memory Consolidation — 记忆反思与致密化

定期对所有记忆做元分析，发现问题，提出操作建议。修剪 = 致密化，永不丢失信息。

## Instructions

### Step 1: 收集记忆

读取 `~/.Codex/projects/-Users-jerry-hu-AI/memory/` 下所有 `.md` 文件（排除 MEMORY.md）。

对每个文件提取：
- frontmatter 字段：name, description, type, confidence, last_verified, maturity, feedback_count
- 正文内容摘要（战略层 + 操作层要点）

### Step 2: 获取衰减状态

执行：
```bash
bash /Users/jerry_hu/AI/.Codex/hooks/check-stale-memories.sh
```

记录每个记忆的健康状态（HEALTHY / AGING / STALE）。

### Step 3: 五项分析

依次执行以下分析，每项独立输出发现：

#### 3.1 冗余检测

比较所有记忆对，找出：
- 同一信息的不同措辞（如两个记忆都在讲"约定优于配置"）
- 一个记忆是另一个的子集（A 的内容完全被 B 覆盖）
- 来源相同但拆分过细的记忆

判断标准：如果合并后不丢失信息且更紧凑，就是冗余。

#### 3.2 矛盾检测

找出互相矛盾的记忆对：
- 对同一主题给出相反建议
- 原则冲突（如一个说"简单优先"，另一个推荐复杂方案）
- 时间演变导致的矛盾（早期认知 vs 后期认知）

处理原则：不删除任一方，而是用时间标记捕获演变（"曾经认为X，现在认为Y，因为Z"）。

#### 3.3 Stale 检测

基于 Step 2 的衰减数据：
- STALE（>90天）：标记需要验证或归档
- AGING（>45天）：标记需要关注
- 检查 confidence 衰减后是否低于 0.3（建议归档）

#### 3.4 关系发现

识别记忆间的关联：
- 主题聚类：哪些记忆属于同一知识领域？
- 引用关系：记忆 A 的内容是否引用或依赖记忆 B？
- 互补关系：两个记忆从不同角度描述同一概念？

输出聚类结果，标注孤立记忆（没有关联的记忆可能需要补充上下文）。

#### 3.5 晋升候选

找出满足晋升条件的记忆：
- maturity 为 `candidate` 但 feedback_count >= 3 → 建议升级为 `established`
- 多次被引用或验证的记忆 → 建议提升 confidence
- 内容已被实践验证的记忆 → 建议更新 last_verified

### Step 4: 输出报告

```markdown
## Consolidation Report — [日期]

### 记忆总览
- 总数：X 条
- 类型分布：fact X / feedback X / project X / reference X
- Maturity 分布：candidate X / established X / core X
- 平均 confidence：X.XX
- 健康状态：HEALTHY X / AGING X / STALE X

### 发现的问题

#### 冗余（X 组）
| 记忆 A | 记忆 B | 重叠内容 | 建议 |
|--------|--------|----------|------|

#### 矛盾（X 组）
| 记忆 A | 记忆 B | 冲突点 | 建议 |
|--------|--------|--------|------|

#### Stale（X 条）
| 记忆 | 天数 | 衰减后 confidence | 建议 |
|------|------|-------------------|------|

### 关系图谱
[聚类结果，用缩进列表表示]

### 晋升候选（X 条）
| 记忆 | 当前 maturity | feedback_count | 建议操作 |
|------|--------------|----------------|----------|

### 建议操作清单

| # | 操作 | 目标 | 说明 |
|---|------|------|------|
| 1 | Merge | A + B → C | [合并理由] |
| 2 | Update | X | [更新内容] |
| 3 | Promote | Y | candidate → established |
| 4 | Archive | Z | [归档理由，内容保留到归档说明中] |
```

### Step 5: 等待确认后执行

逐条列出建议操作，等待用户确认。

- **Merge**：创建新记忆文件，内容合并两个来源，删除原文件，更新 MEMORY.md
- **Update**：编辑记忆文件的 frontmatter 或正文
- **Promote**：更新 maturity 字段
- **Archive**：在记忆正文顶部添加 `> ARCHIVED: [原因]`，降低 confidence 到 0.1，不删除文件

永不删除记忆文件。修剪 = 致密化。

## Guidelines

- 永不合并无关主题的记忆，即使它们看起来相似
- 矛盾不是错误，是认知演变的证据——用时间线记录
- 合并时保留两个来源的所有独特信息
- 报告要具体：指出哪一行/哪个观点冲突，不要泛泛而谈
- 操作建议要保守：宁可不动，不可误合

$ARGUMENTS
