# /learn 分析：Self-Learning with Claude

**源**：https://bitfloorsghost.substack.com/p/self-learning-with-claude
**作者**：Bitfloorsghost | **日期**：2026-02-15
**类型**：博客文章（架构设计 + 引导 prompt）

---

## 这是什么

一篇描述 Claude Code 自学习记忆系统的文章。核心是一个 **mega-prompt**，粘贴到 Claude Code 后让它自动构建三层记忆架构。文章本身不提供可执行代码，而是提供架构规范和 CLAUDE.md 指令，由 Claude 自行生成 hook 脚本和目录结构。

## 核心价值

### 战略层：三层时间分层记忆模型

| 层 | 路径 | 时间属性 | 用途 |
|---|---|---|---|
| Activity Logs | `~/.claude/logs/YYYY-MM-DD.md` | 热（当天+昨天加载） | 时间戳日志，格式 `## HH:MM - [project] description` + bullet points |
| Notes | `~/.claude/notes/*.md` | 温（永久加载） | 按主题组织的持久知识：`session-lessons.md`、`environment.md`、`coding-standards.md` 等 |
| Last Session | `~/.claude/notes/last-session.md` | 冷→热（启动时加载） | 上次停在哪、做完什么、下一步什么、什么阻塞 |

关键洞察：记忆需要不同时间层级（hot/warm/cold storage 模式应用于 AI 记忆）。

### 操作层：五个可移植机制

**1. 两个 Hook（概念规范，非实际代码）**

- **SessionStart "load-notes"**：
  - 加载 `~/.claude/notes/` 全部 markdown
  - 加载当前项目的 `notes/` 目录
  - 加载今天 + 昨天的 activity logs
  - 检查 notes 文件 > 50 行 → 警告合并重分配
  - 检查 activity logs > 14 天 → 警告归档为月度摘要

- **PreCompact "pre-compact-lessons"**：
  - 提醒写入未记录的 learnings 到正确 notes 文件
  - 更新 activity log 当前状态
  - 更新 last-session（状态 + 下一步）

**2. 智能路由决策树**

```
学到新东西 →
  ├─ 项目特定？ → 该项目的 notes/ 目录
  ├─ 匹配主题文件（environment/coding-standards）？ → 写入该文件
  ├─ 全局模式且出现 ≥2 次？ → global session-lessons.md
  ├─ 一次性观察？ → activity log only
  └─ 不确定？ → 默认项目级别
```

**3. 自修剪机制（"pruning only makes things denser"）**

三种操作，零删除：
- **压缩**：session-lessons > 50 行时合并重复条目
- **移动**：错放的条目重定位到正确文件
- **晋升**：activity log 中反复出现的观察 → 永久 notes

时间触发：activity logs > 14 天 → 归档为月度摘要，删除日文件。

**4. 即时提交原则**

> "Write learnings the moment you have them. Don't wait until end of session. Every insight is one crash or timeout away from being lost."

纠正发生时立即写入，不等 session 结束。这是崩溃恢复思维应用于知识管理。

**5. 复合学习循环**

```
纠正 → 立即记录 → 下次 session 加载 → 不再犯同样错误
                                          ↓
                              "训练一个写自己训练数据的系统"
```

## 直接可用性

**仅借鉴想法** — 原因：

1. 文章是一个 prompt 规范，不是可执行工具/组件
2. 没有实际 hook 脚本代码（让 Claude 自己生成）
3. 我们已有结构化记忆系统（frontmatter + MEMORY.md 索引）
4. 文件结构与我们现有系统不兼容

## 值得学习

1. **时间分层**：hot/warm/cold 三层是比我们当前扁平分类更好的时间模型
2. **Hook 自动化**：SessionStart 加载 + PreCompact 保存，消除人工摩擦
3. **路由决策树**：简单确定性的 4 级路由，比"凭感觉分类"更可靠
4. **即时提交**：纠正时立即写入，不攒到 session 结束
5. **修剪 = 致密化**：永不删除，只压缩/移动/晋升

## 不要复制

1. **具体文件结构**（`~/.claude/logs/`、`~/.claude/notes/`）— 与我们现有系统冲突
2. **50 行阈值 / 14 天归档** — 任意数字，缺乏依据
3. **Mega-prompt 引导方式** — 我们的系统已经更结构化
4. **无分类的扁平 notes** — 我们的 frontmatter 分类更可查询
5. **Activity log 层** — 对我们的使用场景过于冗余（我们有 git log）

## 与我们现有系统的对比

| 维度 | 我们的系统 | 文章系统 |
|---|---|---|
| 存储 | `memory/` + MEMORY.md 索引 | `logs/` + `notes/` + `last-session.md` |
| 分类 | frontmatter type (user/feedback/project/reference) | 无分类，按文件名组织 |
| 加载 | 手动/按需 | Hook 自动加载 |
| 时间模型 | 无（全部持久） | 三层（热/温/冷） |
| 修剪 | 手动维护 | 自动检测 + 规则触发 |
| 路由 | 按 type 分类 | 4 级决策树 |
| 即时性 | 无特别要求 | 纠正时立即写入 |

## 建议动作

**absorb-partially** — 提取五个可移植机制作为原则，增强现有系统，不替换。

## 建议落地形式

**memory + feedback** — 原因：

- 五个机制作为设计原则存入 memory（影响未来记忆系统演进方向）
- "即时提交"和"修剪=致密化"作为 feedback 规则（影响日常行为）
- 不需要新 skill（我们的记忆系统已有维护流程）
- 不需要 code module（没有可复用代码）
- Hook 实现可作为未来 TODO，但不急迫

## 最佳下一步

将"三层时间模型"和"路由决策树"记录为记忆系统演进方向的 memory。将"即时提交原则"和"修剪=致密化"记录为 feedback。如果未来要增强记忆系统，这些是设计约束。
