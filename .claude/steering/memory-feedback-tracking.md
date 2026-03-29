---
description: 记忆引用追踪 — 每次使用记忆时更新 feedback_count 和 maturity
globs:
---

# Memory Feedback Tracking

当你在回答中引用或使用了 `memory/*.md` 文件中的知识时，必须更新该文件的 frontmatter：

## 操作步骤

1. `feedback_count` +1
2. `last_referenced` 更新为今天日期（YYYY-MM-DD）
3. 检查 maturity 是否需要升级：
   - `candidate` → `established`：当 feedback_count >= 3
   - `established` → `proven`：当 feedback_count >= 10 且无负面反馈记录
4. 如果记忆内容被证伪或与现实矛盾：降低 `confidence`（至少 -0.2），设置 `maturity: deprecated`

## 判断标准

"引用或使用"包括：
- 直接引用记忆中的原则、模式、checklist 来指导当前工作
- 基于记忆中的知识做出技术决策
- 向用户解释时援引记忆中的概念

不包括：
- 仅仅读取记忆文件做健康检查
- 更新记忆文件本身的元数据
- 列出记忆索引
