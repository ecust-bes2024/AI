# Everything Claude Code 深度分析报告

**分析日期**: 2026-03-29
**仓库**: https://github.com/affaan-m/everything-claude-code
**版本**: v1.9.0
**Stars**: 50K+ | **Forks**: 6K+ | **贡献者**: 30

---

## 项目概览

### 是什么
Everything Claude Code (ECC) 是一个 **AI Agent Harness 性能优化系统**，来自 Anthropic Hackathon 获奖项目。它不是一个独立工具，而是一个 **Claude Code 插件 + 规则集合**，通过以下方式增强 Claude Code：

- **30 个专业化 Agent**：planner、architect、code-reviewer、security-reviewer、语言特定 reviewer（Go/Python/Java/Kotlin/Rust/C++/TypeScript）、build-error resolver
- **135+ Skills**：按领域组织（backend/frontend patterns、TDD、security、Django/Laravel/Spring Boot/Go/C++/Python/Perl）
- **60+ Commands**：planning、testing、code review、build fixes、refactoring、multi-agent orchestration
- **Hook 系统**：PreToolUse、PostToolUse、SessionStart/End、Stop hooks 用于自动化和持续学习
- **多语言规则**：TypeScript、Python、Go、Swift、PHP、Java、Kotlin、Rust、C++、Perl

### 核心架构

```
ECC 插件
├── Plugin 层（通过 marketplace 安装）
│   ├── agents/          # 30 个专业化 subagent
│   ├── skills/          # 135+ 工作流定义
│   ├── commands/        # 60+ slash commands
│   └── hooks/           # 生命周期自动化
│
└── Rules 层（手动安装到 ~/.claude/rules/）
    ├── common/          # 语言无关规则
    ├── typescript/      # TS 特定规则
    ├── python/          # Python 特定规则
    └── [其他语言]/
```

**关键设计**：
- Plugin 提供 **行为编排**（agents、skills、commands）
- Rules 提供 **知识注入**（语言规范、最佳实践、模式库）
- Hooks 提供 **自动化触发**（session lifecycle、pattern extraction、quality gates）

### 安装方式

**Phase 1: Plugin 安装**（即时可用）
```bash
/plugin marketplace add affaan-m/everything-claude-code
/plugin install everything-claude-code@everything-claude-code
```

**Phase 2: Rules 安装**（必需，手动）
```bash
git clone https://github.com/affaan-m/everything-claude-code.git
cd everything-claude-code
npm install
./install.sh --profile full  # 或指定语言：typescript python golang
```

Rules 复制到 `~/.claude/rules/`，按语言目录组织。

---

## 持续学习机制深度分析

### 架构演进：v1 → v2

#### v1: Session-End Extraction（当前稳定版）

**触发机制**：
- Stop hook 在 session 结束时触发
- `evaluate-session.sh` 脚本检查 transcript 长度
- 如果 message_count ≥ MIN_SESSION_LENGTH（默认 10），触发 Claude 评估

**提取内容**：
1. **Error resolution patterns**：症状 → 根因 → 修复 → 复用性
2. **Debugging techniques**：非显而易见的步骤、工具组合、诊断方法
3. **Workarounds**：库怪癖、API 限制、版本特定修复
4. **Project-specific patterns**：代码库约定、架构决策、集成模式

**存储格式**：
- 位置：`~/.claude/skills/learned/[pattern-name].md`
- 结构：
  ```markdown
  ## Problem
  [描述]

  ## Solution/Pattern
  [解释]

  ## Code Examples
  [如果适用]

  ## Trigger Conditions
  [何时应用此模式]
  ```

**质量控制**（通过 `/learn-eval`）：
- Grep 现有 skills 目录检查重复
- 检查 MEMORY.md 避免冗余
- 评估是否应该 append 到现有 skill
- 四种判决：Save / Improve then Save / Absorb into [X] / Drop

**复用机制**：
- Skills 自动加载到 Claude Code context
- 通过 skill name 触发（如 `/learned-pattern-name`）
- 或通过 trigger conditions 自动激活

#### v2: Atomic Instincts（实验版）

**核心改进**：
- **从 Stop hook 迁移到 100% 可靠 hooks**（可能是 PostToolUse）
- **从完整 skills 转向原子 instincts**：
  - 更细粒度（0.3-0.9 加权置信度）
  - 项目作用域隔离（防止跨项目污染）
- **后台 agent（Haiku）分析**：不占用主 context
- **演进机制**：
  - `/evolve`：聚类相关 instincts
  - `/promote`：将行为提升为 skills/commands/agents

**v2 优势**：
- 更轻量（不阻塞主流程）
- 更精确（置信度加权）
- 更安全（项目隔离）
- 更灵活（可演进）

**v2 劣势**：
- 实验性（未稳定）
- 复杂度更高（需要额外的 instinct 管理）
- 文档不完整

### 与用户 `/lesson` 的对比

| 维度 | 用户 `/lesson` | ECC Continuous Learning v1 | ECC v2 Instincts |
|------|----------------|----------------------------|------------------|
| **触发方式** | 手动触发 | 自动（Stop hook） | 自动（PostToolUse hook） |
| **提取时机** | 用户指定时 | 每次 session 结束 | 每次工具调用后 |
| **提取内容** | 技术层（坑+修复）+ 原则层（决策规则） | Error patterns + Debugging + Workarounds + Project patterns | 原子 instincts（加权置信度） |
| **存储位置** | Memory system（mcp__memory__memory_store） | `~/.claude/skills/learned/` | Instinct DB（项目作用域） |
| **存储格式** | 文本记忆（< 500 字符） | Markdown skill 文件 | 结构化 instinct（JSON） |
| **质量控制** | 无（用户判断） | `/learn-eval` 四级判决 | 置信度加权 + 聚类 |
| **复用机制** | Memory recall（搜索） | Skill 自动加载 + 触发 | 后台 agent 推荐 |
| **作用域** | Global memory | Global skills（可选 project-level） | Project-scoped instincts |
| **验证** | Memory recall 搜索 | Skill 文件存在性 | Instinct DB 查询 |

**关键差异**：

1. **自动化程度**：
   - `/lesson`：完全手动，用户决定何时提取
   - ECC v1：半自动，session 结束时自动评估，但需要用户确认
   - ECC v2：全自动，后台持续提取，用户可选演进

2. **存储粒度**：
   - `/lesson`：两层（技术层 + 原则层），每条 < 500 字符
   - ECC v1：完整 skill 文件（可能数百行）
   - ECC v2：原子 instinct（最细粒度）

3. **检索方式**：
   - `/lesson`：基于语义搜索（memory recall）
   - ECC v1：基于 skill name 和 trigger conditions
   - ECC v2：基于置信度加权推荐

4. **质量保证**：
   - `/lesson`：无（依赖用户判断）
   - ECC v1：`/learn-eval` 四级判决（Save/Improve/Absorb/Drop）
   - ECC v2：置信度加权 + 聚类去重

5. **跨项目隔离**：
   - `/lesson`：无（global memory）
   - ECC v1：可选（global 或 project-level skills）
   - ECC v2：强制（project-scoped instincts）

---

## 直接复用评估

### 能否直接用？

**结论**：**不建议直接全量使用**，但可以 **部分吸收**。

**原因**：

#### 优势
1. **成熟度高**：50K+ stars，10+ 月迭代，997+ 测试
2. **架构清晰**：Plugin + Rules 分离，易于理解
3. **功能丰富**：30 agents + 135 skills + 60 commands
4. **持续学习机制完整**：v1 稳定，v2 实验性但有前瞻性

#### 劣势
1. **体积庞大**：135 skills + 60 commands + 30 agents，会显著增加 context 负担
2. **规则冲突风险**：
   - 用户已有 `~/.claude/CLAUDE.md` 全局规则
   - 用户已有项目级 `CLAUDE.md`
   - ECC 的 `~/.claude/rules/` 可能与用户规则冲突
3. **依赖复杂**：
   - 需要 Node.js ≥18
   - 需要 npm/yarn/pnpm
   - 需要手动安装 rules（plugin 无法自动分发）
4. **学习曲线**：
   - 135 skills 需要时间熟悉
   - Hook 系统需要理解生命周期
   - Instinct 管理（v2）需要额外学习
5. **维护成本**：
   - 需要跟随 ECC 更新
   - 需要处理与用户现有 skills 的冲突
   - 需要管理 learned skills 的增长

### 能否只取持续学习模块？

**结论**：**可以，但需要轻度改造**。

**可行性分析**：

#### 可独立提取的部分
1. **`/learn` command**：
   - 文件：`commands/learn.md`
   - 依赖：无（纯 prompt）
   - 功能：从 session 提取 patterns
   - 复用难度：**低**

2. **`/learn-eval` command**：
   - 文件：`commands/learn-eval.md`
   - 依赖：需要 Grep 现有 skills 和 MEMORY.md
   - 功能：质量控制（四级判决）
   - 复用难度：**中**（需要适配用户的 memory 系统）

3. **`continuous-learning` skill**：
   - 文件：`skills/continuous-learning/SKILL.md`
   - 依赖：`evaluate-session.sh` 脚本
   - 功能：Stop hook 触发的自动评估
   - 复用难度：**中**（需要配置 hooks）

4. **`evaluate-session.sh` 脚本**：
   - 文件：`skills/continuous-learning/evaluate-session.sh`
   - 依赖：transcript_path（由 Claude Code 提供）
   - 功能：检查 session 长度，触发评估
   - 复用难度：**低**（纯 shell 脚本）

#### 不可独立提取的部分
1. **Hooks 系统**：
   - 需要 `hooks/hooks.json` 配置
   - 需要 `scripts/hooks/` 实现
   - 与 ECC 的整体架构深度耦合
   - 复用难度：**高**（需要理解整个 hook lifecycle）

2. **Instinct 系统（v2）**：
   - 需要 instinct DB
   - 需要后台 agent（Haiku）
   - 需要 `/evolve` 和 `/promote` 命令
   - 复用难度：**极高**（实验性，文档不完整）

### 集成成本和风险

#### 成本
1. **时间成本**：
   - 理解 ECC 架构：2-4 小时
   - 提取持续学习模块：4-8 小时
   - 适配到用户环境：8-16 小时
   - 测试和调试：4-8 小时
   - **总计**：18-36 小时

2. **维护成本**：
   - 跟随 ECC 更新：每月 1-2 小时
   - 处理冲突：每月 0-2 小时
   - 管理 learned skills：每周 0.5-1 小时

#### 风险
1. **规则冲突**：
   - ECC 的 `~/.claude/rules/` 可能覆盖用户规则
   - 需要手动 merge 或选择性安装

2. **Context 膨胀**：
   - 135 skills 会显著增加 context 使用
   - 可能影响 Claude Code 性能

3. **Learned skills 增长**：
   - 每次 session 可能生成新 skill
   - 需要定期清理和合并

4. **依赖锁定**：
   - 一旦依赖 ECC，升级可能破坏现有 learned skills
   - 需要版本管理策略

---

## 对 `/lesson` 的优化建议

基于 ECC 的实现，以下是可以借鉴来提升用户 `/lesson` 的具体做法：

### 1. 引入质量控制机制（借鉴 `/learn-eval`）

**当前问题**：
- `/lesson` 无质量控制，用户决定存什么
- 可能存储重复、低质量或过于具体的教训

**改进方案**：
在 `/lesson` 存储前增加评估步骤：

```markdown
## 评估维度
1. **唯一性检查**：
   - 使用 `mcp__memory__memory_recall` 搜索相似教训
   - 如果已存在，询问是否 merge 或 skip

2. **质量评估**：
   - 是否足够具体？（有症状、根因、修复）
   - 是否足够通用？（不是一次性问题）
   - 是否有可操作性？（有预防措施）

3. **四级判决**：
   - **Save**：唯一、高质量、可复用
   - **Improve then Save**：有价值但需要细化
   - **Merge into existing**：与现有教训相似，应合并
   - **Drop**：重复、低质量或过于具体

## 实现
在 `/lesson` 中增加一个评估步骤：
1. 提取教训后，先 recall 相似记忆
2. 展示评估结果和建议判决
3. 询问用户确认
4. 根据判决执行 save/improve/merge/drop
```

### 2. 增加自动触发机制（借鉴 Stop hook）

**当前问题**：
- `/lesson` 完全手动，用户可能忘记提取
- 有价值的教训可能丢失

**改进方案**：
在 `~/.claude/hooks/hooks.json` 中增加 Stop hook：

```json
{
  "Stop": [
    {
      "name": "lesson-reminder",
      "command": "~/.claude/skills/lesson/check-session.sh",
      "description": "检查 session 是否包含值得提取的教训",
      "timeout": 5000
    }
  ]
}
```

`check-session.sh` 逻辑：
```bash
#!/bin/bash
# 读取 transcript
transcript_path=$(echo "$stdin_data" | jq -r '.transcript_path // empty')

# 检查是否包含关键词（bug、fix、error、solution、workaround）
if grep -qE "(bug|fix|error|solution|workaround)" "$transcript_path"; then
  echo "💡 本次 session 可能包含值得提取的教训。运行 /lesson 来保存？"
fi
```

**注意**：这只是提醒，不是自动提取（保持用户控制）。

### 3. 增加分类和置信度（借鉴 v2 Instincts）

**当前问题**：
- `/lesson` 只有两层（技术层 + 原则层）
- 没有置信度标记
- 难以区分"确定有效"和"可能有效"的教训

**改进方案**：
在存储时增加置信度和更细的分类：

```markdown
## 存储格式升级
技术层：
```
坑: [症状]. 原因: [根因]. 修复: [解决方案]. 预防: [如何避免]. 置信度: [0.7-1.0].
```

原则层：
```
决策原则([标签]): [行为规则]. 触发: [何时]. 动作: [做什么]. 置信度: [0.7-1.0]. 适用范围: [global/project/language].
```

## 置信度定义
- **0.9-1.0**：已验证有效（多次复现）
- **0.8-0.9**：高度可信（单次验证）
- **0.7-0.8**：可能有效（理论推导）

## 适用范围
- **global**：跨项目通用
- **project**：特定项目
- **language**：特定语言/框架
```

### 4. 增加教训演进机制（借鉴 `/evolve` 和 `/promote`）

**当前问题**：
- 教训存储后就固化了
- 没有机制将多个相关教训聚合
- 没有机制将高频教训提升为 skill

**改进方案**：
增加两个新命令：

#### `/lesson-evolve`：聚合相关教训
```markdown
## 功能
1. 使用 `mcp__memory__memory_recall` 搜索相关教训
2. 识别重复或相关的教训
3. 建议合并为更通用的原则
4. 更新 memory 或创建新的高层原则

## 示例
输入：
- 教训 1：npm install 后 MODULE_NOT_FOUND
- 教训 2：yarn install 后依赖版本不匹配
- 教训 3：pnpm install 后 peer dependency 警告

输出：
- 合并为：依赖管理最佳实践（使用 lock file、定期清理 node_modules、CI 用 ci 命令）
```

#### `/lesson-promote`：提升为 skill
```markdown
## 功能
1. 识别高频或高价值教训
2. 将其转化为可复用的 skill
3. 生成 skill 文件到 `~/.claude/skills/learned/`

## 触发条件
- 教训被 recall 超过 5 次
- 教训置信度 ≥ 0.9
- 教训包含可操作的步骤

## 示例
教训：
```
坑: npm install 后项目无法启动. 原因: package-lock.json 不同步. 修复: 删除 node_modules 和 lock 文件重装. 预防: 提交前确保 lock 文件更新. 置信度: 0.95.
```

提升为 skill：
```markdown
---
name: npm-dependency-reset
description: 修复 npm 依赖不同步问题
---

# npm 依赖重置

## 触发条件
- npm install 后报 MODULE_NOT_FOUND
- 依赖版本不匹配
- package-lock.json 与 node_modules 不一致

## 步骤
1. 删除 node_modules 和 package-lock.json
2. 运行 npm install
3. 验证项目启动
4. 提交更新后的 package-lock.json
```
```

### 5. 增加项目作用域隔离（借鉴 v2 Project-scoped）

**当前问题**：
- `/lesson` 存储到 global memory
- 项目特定的教训可能污染其他项目

**改进方案**：
在存储时增加 `scope` 参数：

```markdown
## 存储时判断作用域
1. 如果当前在项目目录下（有 CLAUDE.md 或 .git）：
   - 询问：这个教训是项目特定的还是通用的？
   - 项目特定：使用 `scope: "project:<project_name>"`
   - 通用：使用 `scope: "global"`

2. 使用 `mcp__memory__memory_store` 的 `scope` 参数：
   ```
   mcp__memory__memory_store(
     text="...",
     category="fact",
     importance=0.8,
     scope="project:my-app"  # 或 "global"
   )
   ```

3. Recall 时优先匹配当前项目：
   ```
   mcp__memory__memory_recall(
     query="...",
     scope="project:my-app"  # 先搜索项目 scope
   )
   ```
   如果项目 scope 无结果，再搜索 global scope。
```

### 6. 增加教训可视化（借鉴 ECC 的 instinct-export）

**当前问题**：
- 教训存储后难以浏览
- 没有全局视图

**改进方案**：
增加 `/lesson-export` 命令：

```markdown
## 功能
1. 导出所有教训为结构化格式（YAML/JSON/Markdown）
2. 按分类、置信度、适用范围组织
3. 生成可读的教训手册

## 输出格式
```yaml
lessons:
  technical:
    - symptom: "npm install 后 MODULE_NOT_FOUND"
      root_cause: "package-lock.json 不同步"
      fix: "删除 node_modules 和 lock 文件重装"
      prevention: "提交前确保 lock 文件更新"
      confidence: 0.95
      scope: "global"
      recall_count: 12
      last_used: "2026-03-28"

  principles:
    - rule: "依赖管理优先使用 npm ci"
      trigger: "CI/CD 环境或需要精确复现"
      action: "运行 npm ci 确保与 lock 文件一致"
      confidence: 0.9
      scope: "global"
      recall_count: 8
      last_used: "2026-03-25"
```

## 可选：生成 poster
```bash
/lesson-export --format markdown --output ~/AI/lessons-handbook.md
/poster ~/AI/lessons-handbook.md --theme technical
```
```

---

## 结论

### 建议动作：**absorb-partially**（部分吸收）

**不建议**：
- ❌ **direct-use**：体积太大，规则冲突风险高，学习曲线陡峭
- ❌ **wrap-lightly**：ECC 是 plugin，不是独立工具，无法轻度包装

**建议**：
- ✅ **absorb-partially**：提取持续学习机制的核心思想和具体实现，适配到用户现有的 `/lesson` 体系

### 具体行动计划

#### 短期（1-2 周）
1. **增加质量控制**：
   - 在 `/lesson` 中增加评估步骤（唯一性检查 + 四级判决）
   - 实现 improve/merge/drop 逻辑

2. **增加自动提醒**：
   - 创建 `check-session.sh` 脚本
   - 配置 Stop hook 提醒用户运行 `/lesson`

3. **增加置信度和作用域**：
   - 升级存储格式（增加 confidence 和 scope）
   - 适配 `mcp__memory__memory_store` 的 scope 参数

#### 中期（1-2 月）
4. **增加教训演进**：
   - 实现 `/lesson-evolve`（聚合相关教训）
   - 实现 `/lesson-promote`（提升为 skill）

5. **增加可视化**：
   - 实现 `/lesson-export`（导出教训手册）
   - 可选：集成 `/poster` 生成可视化

#### 长期（3-6 月，可选）
6. **研究 v2 Instincts**：
   - 如果 ECC v2 稳定，考虑借鉴原子 instinct 机制
   - 评估是否值得从 memory 迁移到 instinct DB

### 不建议做的事
- ❌ 不要全量安装 ECC（135 skills + 60 commands 太重）
- ❌ 不要直接复制 ECC 的 hooks 系统（与用户环境耦合度高）
- ❌ 不要尝试提取 v2 Instincts（实验性，文档不完整）
- ❌ 不要安装 ECC 的 rules（可能与用户规则冲突）

### 最终评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **问题适配** | ⭐⭐⭐⭐ | ECC 的持续学习机制与用户需求高度匹配 |
| **集成成本** | ⭐⭐ | 全量集成成本高，部分吸收成本中等 |
| **维护成本** | ⭐⭐ | 全量维护成本高，部分吸收维护成本低 |
| **依赖风险** | ⭐⭐⭐ | 部分吸收无依赖风险，全量有规则冲突风险 |
| **可替换性** | ⭐⭐⭐⭐⭐ | 部分吸收完全可控，可随时调整 |
| **重建理由** | ⭐⭐⭐⭐ | 核心思想值得借鉴，但需要适配用户环境 |

**综合评分**：⭐⭐⭐⭐（4/5）

**一句话总结**：
ECC 的持续学习机制设计优秀，但体积庞大且与用户环境耦合度高。建议 **部分吸收核心思想**（质量控制、自动提醒、置信度、作用域、演进机制），而不是直接使用整个系统。

---

## 附录：关键文件清单

### 值得深入研究的文件
1. `commands/learn.md` - 核心学习命令
2. `commands/learn-eval.md` - 质量控制机制
3. `skills/continuous-learning/SKILL.md` - v1 持续学习 skill
4. `skills/continuous-learning/evaluate-session.sh` - Session 评估脚本
5. `skills/continuous-learning-v2/SKILL.md` - v2 实验性实现
6. `hooks/hooks.json` - Hook 配置
7. `hooks/README.md` - Hook 系统文档

### 可选参考的文件
8. `commands/save-session.md` - Session 状态持久化
9. `commands/resume-session.md` - Session 恢复
10. `commands/instinct-export.md` - Instinct 导出
11. `commands/rules-distill.md` - 规则提炼

---

**报告生成时间**：2026-03-29
**分析者**：Ben Thompson（调研分析师 Agent）
**报告位置**：`/Users/jerry_hu/AI/research/everything-claude-code-analysis/analysis.md`
