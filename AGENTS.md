# Workspace Rules

## OpenClaw Memory Bridge

This workspace uses OpenClaw `memory-lancedb-pro` as the single long-term memory backend.

### Default Memory Workflow

- For prior preferences, stable decisions, lessons learned, naming preferences, workflow habits, and ongoing conventions:
  run `./codex-memory recall "<query>" --json` before answering if memory could help.
- For durable new information learned during the conversation:
  store it with `./codex-memory store "<text>" --category <category> --json`.
- Prefer these categories:
  `preference`, `decision`, `fact`, `entity`, `reflection`, `other`
- Default write scope is `agent:main`.
- Default read behavior spans all available scopes so migrated Claude memories in `global` remain visible.

### What To Store

- User preferences that should affect future replies
- Repeatedly useful implementation lessons
- Durable decisions about tools, workflow, or project direction
- Important identity/context facts that are likely to matter later

### What Not To Store

- One-off transient task chatter
- Raw logs unless the log itself encodes a reusable lesson
- Information already captured in code or docs unless the memory is about behavior or workflow

### Commands

- Recall:
  `./codex-memory recall "<query>" --json`
- Store:
  `./codex-memory store "<text>" --category fact --importance 0.7 --json`
- Update:
  `./codex-memory update <memoryId> --text "<text>" --json`
- Forget:
  `./codex-memory forget <memoryId> --json`
- Stats:
  `./codex-memory stats --json`

## 代码质量原则

适用范围：脚本、自动化、工具链、后端、前端与 AI 工作流代码。

使用方式：
- 作为默认写码与 review 准则，不作为脱离上下文的硬性教条。
- 当这些原则与业务需求、正确性、性能边界、现有架构或语言/框架惯例冲突时，以后者为准。
- 代码审查时可直接按编号引用。

1. 组合小步骤
将一个功能拆成多个可识别的小步骤。函数内部尽量保持同一抽象层级；如果一段逻辑需要一整段话才能解释，就继续拆。

2. 按意图命名
名称描述“要达成什么”，不要描述“内部怎么做”。如果实现方式以后可能变化，名字就不该绑死在当前算法上。

3. 优先清晰代码，再写注释
先通过重命名、提取函数、拆分表达式提升可读性。注释主要用于说明约束、原因、权衡和兼容性，不重复代码表面行为。

4. 先处理边界和失败路径
优先使用 guard clauses 提前处理空值、非法输入、异常条件和提前返回，让主流程保持平直可读。

5. 一个函数只承担一个主要责任
函数可以有多个步骤，但这些步骤应共同服务于同一个目标。不要把查询、计算、副作用、格式化、持久化揉成一个大块。

6. 同一份知识只写一次
重复的不只是代码，还包括规则、字段映射、魔法值、协议假设和错误处理分支。重复出现时，提取成单一可信来源。

7. 查询与修改分离
回答问题的函数尽量无副作用；修改状态的函数尽量不混入额外返回语义。布尔查询优先使用 `is`、`has`、`can` 一类命名。

8. 用解释性变量和小函数降低认知负担
复杂条件、拼装逻辑和多段转换不要一次写完。中间结果应有能表达业务含义的名字，而不是只暴露类型或临时实现细节。

9. 隐藏实现细节，稳定对外接口
优先让调用方依赖清晰的行为边界，而不是内部状态布局。不要随意暴露可变内部集合、临时字段或偶然的数据结构。

10. 只在收益明确时引入抽象
多态、策略、继承、回调封装、方法对象等模式都是手段，不是目标。先写清楚，再在重复、分支扩散或变更成本上升时抽象。

11. 返回值要有意义
函数只在调用方真正需要时返回值。不要习惯性返回内部状态、`self` 或无实际用途的信息；返回值应服务调用者决策。

12. 逐步重构，不一次性追求完美
代码质量改进应随着开发持续进行。优先解决当前摩擦最大的点，每次把代码收敛到更清楚一点，而不是一次引入整套模式。

## 项目表达模板触发

当用户需要讲清一个项目，而不是编写正式技术设计文档时，优先使用 [project-talk-template.md](/Users/jerry_hu/AI/templates/project-talk-template.md) 中的结构整理输出。

适用触发词或场景：
- 面试讲项目
- 述职、晋升、周报、月报中的项目成果表述
- 给老板、产品、客户或非技术方解释项目
- demo、复盘、项目介绍、项目总结
- 让 AI 将零散项目材料整理成 30 秒、1 分钟、3 分钟版本

默认输出偏好：
- 先结论，后细节
- 使用“问题-方案-价值”结构
- 明确个人贡献、关键决策、量化结果
- 不写营销腔，不夸大，不把实现细节堆成流水账

不适用场景：
- 正式技术方案设计文档
- API 文档
- 架构说明书
- 需要严格规格、接口、时序、约束定义的工程文档
