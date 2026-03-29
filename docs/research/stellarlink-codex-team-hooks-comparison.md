# stellarlink/codex 与当前实验室的 Team / Hooks 对照

**日期**: 2026-03-29
**对象**:

- 外部候选: [stellarlinkco/codex](https://github.com/stellarlinkco/codex)
- 当前实验室:
  - [team-c](/Users/jerry_hu/AI/toolbox/skills/team-c/SKILL.md)
  - [team-c runtime](/Users/jerry_hu/AI/toolbox/skills/team-c/scripts/team_runtime.py)
  - [team-codex](/Users/jerry_hu/AI/toolbox/skills/team-codex/SKILL.md)

**目标**: 只对比 `team` 与 `hooks`，判断哪些能力实验室已经有，哪些对方更完整，以及哪些值得抄协议、不值得抄实现。

---

## 一、总判断

结论很直接：

- `team`：实验室已经有可运行的 `team-c`，但 `stellarlink/codex` 的 team 协议更完整
- `hooks`：实验室当前只有零散的 hook-like guardrail，对方已经做成通用事件系统

因此优先级应是：

1. 保留实验室现有 `team-c`，只吸收对方更完整的 team 协议
2. 新建一层实验室自己的 `hooks-codex` 设计，而不是直接搬整个 fork

---

## 二、Team 对照

### 2.1 `stellarlink/codex` 提供的 Team 能力

仓库文档显示，对方已经把 team 做成正式工具协议，而不是单纯 prompt workflow。

核心能力：

- `spawn_team`
- `wait_team`
- `close_team`
- `team_cleanup`
- `team_task_list`
- `team_task_claim`
- `team_task_claim_next`
- `team_task_complete`
- `team_message`
- `team_broadcast`
- `team_ask_lead`
- `team_inbox_pop`
- `team_inbox_ack`
- 成员级 `worktree: true`

持久化产物：

- `$CODEX_HOME/teams/<team_id>/config.json`
- `$CODEX_HOME/tasks/<team_id>/*.json`
- `$CODEX_HOME/teams/<team_id>/inbox/<thread_id>.jsonl`
- cursor / lock 文件

来源：

- [agent-teams.md](https://raw.githubusercontent.com/stellarlinkco/codex/main/docs/agent-teams.md)

### 2.2 实验室当前已有的 Team 能力

实验室当前已有：

- team manifest
- shared task board
- mailbox
- teammate lifecycle
- plan approval
- cleanup semantics
- in-process dashboard
- split-pane 脚本入口
- smoke test / dependency check

关键文件：

- [team-c skill](/Users/jerry_hu/AI/toolbox/skills/team-c/SKILL.md)
- [team_runtime.py](/Users/jerry_hu/AI/toolbox/skills/team-c/scripts/team_runtime.py)
- [runtime feature map](/Users/jerry_hu/AI/toolbox/skills/team-c/references/runtime-feature-map.md)

### 2.3 差异

`stellarlink/codex` 更强的点：

- team 是工具层协议，不只是 artifact-backed runtime
- 有 `claim_next`
- 有 durable inbox 的 cursor / ack 语义
- 有 `ask_lead`
- `worktree` 是 team member 的一等字段
- close 和 cleanup 分成两段

实验室当前更偏：

- workspace-backed team runtime
- artifact and script driven
- lead-mediated coordination

### 2.4 最值得吸收的 Team 协议

优先吸收这些，不建议整仓照搬：

1. `team_task_claim_next`
2. `team_inbox_pop / team_inbox_ack`
3. `team_ask_lead`
4. `worktree: true` 作为 teammate 配置字段
5. `close_team` 与 `team_cleanup` 的双阶段模型

### 2.5 不建议直接抄的 Team 部分

- 整个 fork 的 runtime 实现
- 它的目录布局
- 它的所有命令名
- 它的持久化位置直接使用 `$CODEX_HOME/teams/...`

原因：

- 实验室已经有自己的命名约定和目录结构
- 直接引入会带来长期同步成本
- 现在更需要协议增量，而不是 runtime 重写

---

## 三、Hooks 对照

### 3.1 `stellarlink/codex` 的 Hooks 能力

对方 hooks 已经是完整事件系统。

配置位置：

- `~/.codex/config.toml`
- `./.codex/config.toml`
- `SKILL.md` frontmatter scoped hooks

Handler 类型：

- `command`
- `prompt`
- `agent`

执行模型：

- matching hooks 并行
- identical handlers 去重
- `once`
- per-handler timeout
- async command hook

事件面：

- `user_prompt_submit`
- `pre_tool_use`
- `permission_request`
- `post_tool_use`
- `post_tool_use_failure`
- `stop`
- `subagent_start`
- `subagent_stop`
- `teammate_idle`
- `task_completed`
- `config_change`
- `worktree_create`
- `worktree_remove`

输出契约：

- `decision`
- `reason`
- `updatedInput`
- `additionalContext`
- permission decision 系列字段

来源：

- [hooks.md](https://raw.githubusercontent.com/stellarlinkco/codex/main/docs/hooks.md)

### 3.2 实验室当前的 Hooks 状态

实验室目前没有真正统一的 hooks runtime。

现有能力更像：

- hook-like guardrail
- workflow-level checks
- runtime-level blocking logic

典型例子：

- `team-c` 的 cleanup block
- `team-c` 的 plan approval gate
- dependency check / smoke test
- memory bridge 的运行链路检查

也就是说：

- 有局部 hook 效果
- 没有统一事件总线
- 没有通用 matcher / handler contract / scoped hooks

### 3.3 差异

`stellarlink/codex` 更强的点：

- 通用事件层
- 统一 handler contract
- skill-scoped hooks
- tool input rewrite
- permission gate 统一化
- worktree lifecycle hooks

实验室当前更弱的点：

- 没有正式 `hooks` 配置层
- 没有 `pre_tool_use / permission_request` 这种横切面
- 没有 `subagent_start / task_completed` 事件面

### 3.4 最值得吸收的 Hooks 协议

优先吸收这些概念：

1. 事件模型

- `pre_tool_use`
- `permission_request`
- `subagent_start`
- `subagent_stop`
- `teammate_idle`
- `task_completed`
- `worktree_create`
- `worktree_remove`

2. handler 类型分层

- `command`
- `prompt`
- `agent`

3. 输出字段约定

- `decision`
- `reason`
- `updatedInput`
- `additionalContext`

4. scoped hooks

- skill frontmatter 中定义 hooks
- 仅在 skill 激活时生效

### 3.5 不建议直接抄的 Hooks 部分

- 全量事件一次性接入
- 它的全部执行细节
- dedupe / async / every-event blocking 的重型行为一口气上满

原因：

- 实验室目前没有统一 hook runtime 基础
- 一次性全做会复杂度失控
- 应先做最值钱的事件子集

---

## 四、迁移草案

### 4.1 Team 迁移草案

不重写 `team-c`，只做协议增强。

建议阶段：

#### Phase 1

增强现有 `team-c`：

- 增加 `claim-next`
- 增加 `ask-lead`
- 为 mailbox 增加 cursor / ack 语义
- 将 `worktree` 变成 teammate metadata 字段

#### Phase 2

把 team runtime 和 Codex 子 agent 执行真正接起来：

- teammate state 与 agent state 对应
- task complete 时触发 lead-side artifact update
- team cleanup 时联动 worktree cleanup

#### Phase 3

如果仍需要，再考虑抽成更正式的 tool layer。

### 4.2 Hooks 迁移草案

建议新建一层实验室设计：

- `hooks-codex`

建议只先做这几个事件：

- `pre_tool_use`
- `permission_request`
- `subagent_start`
- `task_completed`
- `worktree_create`
- `worktree_remove`

建议只支持两类 handler 起步：

- `command`
- `agent`

先不急着做：

- prompt hook
- async hook
- dedupe
- 全事件覆盖

### 4.3 最小 MVP

如果只做最小 MVP，建议：

1. `hooks-codex` 先只支持 `pre_tool_use` 和 `permission_request`
2. `team-c` 先补 `claim-next` 和 `ask-lead`
3. `worktree_create/worktree_remove` 先作为 team runtime 级 hook，而不是全局 hook

---

## 五、建议决策

### 值得直接吸收

- team inbox / task claim / lead question 协议
- hooks 事件面与输出契约
- scoped hook 设计思想

### 值得轻包装后集成

- team worktree 生命周期
- permission hook 模型
- skill-scoped hook activation

### 只借鉴想法

- 整个 fork 的目录结构
- 全量 runtime 细节
- 所有命令名

### 不建议直接使用

- 把这个 fork 直接作为实验室长期主线

原因：

- 它是重型分叉
- 上游同步成本高
- 当前实验室已经有自己的结构和约定

---

## 六、一句话结论

如果只看 `team` 和 `hooks`：

- `team-c` 已经能用，但应继续抄协议补完整
- `hooks` 是更值得优先借鉴的一块，因为实验室当前还没有真正统一的 hooks runtime

