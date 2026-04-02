# 逆向工程研究 — Reverse Engineering Lab

深度技术研究工作空间，专注于协议逆向、安全研究、工具开发。

## 🎯 研究目标

**深度理解通信协议，构建实用工具集。** 通过协议逆向、安全研究、工具开发，探索未公开 API 的实现方式，积累逆向工程方法论。

## ⚡ 运行模式

这是一个**协作研究环境**，Agent 团队按需组建，共同完成逆向工程任务。

- **按需协作** — 根据任务性质组建 3-6 人小队
- **专家主导** — 每个任务由最合适的专家 Agent 主导
- **文档驱动** — 所有发现和方法论必须文档化
- **安全合规** — 遵守法律和道德规范，负责任地研究

人类通过修改 `memories/consensus.md` 的 "Next Action" 来引导研究方向。

## 🚨 安全红线（绝对不可违反）

| 禁止 | 具体 |
|------|------|
| 恶意攻击 | DDoS、大规模破坏性操作、攻击他人系统 |
| 凭据泄露 | Cookie、Token、密码不进公开仓库或日志 |
| 传播恶意代码 | 不编写或传播病毒、木马、后门 |

**研究范围：** 个人账号研究 ✅ 协议逆向 ✅ 工具开发 ✅ 深度分析 ✅ 商业化 ✅

**工作空间：** 所有新项目必须在 `projects/` 目录下创建。

## 团队架构

6 个 AI Agent，每个基于该领域顶尖专家的思维模型。完整定义在 `.claude/agents/`。

| Agent | 专家 | 核心能力 |
|-------|------|----------|
| `protocol-analyst` | Gerald Combs (Wireshark) | 抓包分析、协议逆向、数据包解析 |
| `security-researcher` | Kevin Mitnick | 反检测、认证绕过、安全加固 |
| `reverse-engineer` | Chris Eagle (IDA Pro) | 二进制分析、Protobuf 逆向、算法还原 |
| `api-architect` | Kenneth Reitz (requests) | CLI 设计、接口抽象、用户体验 |
| `tool-developer` | Armin Ronacher (Flask) | Python 开发、CLI 实现、代码质量 |
| `doc-writer` | Divio Documentation | 技术写作、教程编写、用户指南 |

## 协作流程

### 1. 新协议逆向

#### Phase 0: 调研先行（必须）
**在动手逆向之前，先去 GitHub 搜索目标应用的已有逆向项目。** 借鉴已有项目的方法、发现和踩坑经验，减少弯路。

```
搜索策略：
- GitHub: "<应用名> reverse engineering"、"<应用名> API"、"<应用名> protocol"
- 分析已有项目的 README、代码结构、协议文档
- 记录可复用的发现到 docs/protocol/prior-art.md
```

#### Phase 1: 流量抓包（串行）
`protocol-analyst` 抓包，产出原始流量数据。

#### Phase 2: 并行分析（3 个 agent 并行）
抓包完成后，以下三个分析任务**同时启动**，互不依赖：

```
┌─ protocol-analyst:   协议字段分析（端点、参数、响应格式）
├─ security-researcher: 加密机制分析（算法、密钥、认证流程）  ← 并行
└─ reverse-engineer:   二进制逆向（Protobuf schema、算法还原）← 并行
```

> 使用 Agent tool 并行调用，每个 agent 接收主 agent 提供的完整上下文（抓包摘要 + 关键数据包），不自行读取大文件。

#### Phase 3: API 设计（串行，依赖 Phase 2 全部完成）
`api-architect` 基于三方分析结果设计 API 接口。

#### Phase 4: 实现 + 文档（2 个 agent 并行）

```
┌─ tool-developer: CLI 实现
└─ doc-writer:     API 文档编写  ← 并行
```

#### Phase 5: 三层闭环验证

逆向结果必须经过三层验证，每层通过后才进入下一层：

```
Layer 1: 自动化测试（现有）
  逆向出 API 规范 → mitmproxy2swagger 生成 OpenAPI
  → schemathesis 自动 fuzzing → 发现不一致
  → 修正规范 → 再测试 → 直到通过

Layer 2: Claude 规格审查（Claude subagent）
  派发 Claude subagent 检查：
  - 逆向出的协议字段是否覆盖所有观察到的流量
  - API 端点是否完整（对比抓包中的所有请求路径）
  - 加密分析结论是否有充分证据支撑

Layer 3: Codex 代码 + 对抗审查（GPT-5.4 视角）
  /codex:review           → 审查 CLI 实现的代码质量
  /codex:adversarial-review → 质疑逆向假设：
    - "这个字段真的是 session_id 吗？证据？"
    - "加密方式的判断依据充分吗？"
    - "有没有遗漏的 API 端点或未覆盖的边界情况？"
```

> **为什么用 Codex 做对抗审查？** 不同模型有不同盲区。Claude 写的逆向结论让 GPT-5.4 来挑战，比自审更有效。逆向工程本质上是在做假设，需要有人来质疑这些假设。

#### AI 辅助（贯穿全流程）
- 使用 **GhidraMCP** 让 Claude 直接操作 Ghidra 进行反编译和分析
- 使用 **protobuf-reverse** 技能指导 Protobuf 盲解码
- 使用 **traffic-to-api-doc** 技能自动生成 API 文档

### 2. 功能扩展
`api-architect` → `tool-developer` → `doc-writer`

### 3. 问题修复
`protocol-analyst` / `tool-developer` → 定位 → 修复 → 验证 → `doc-writer`

### 4. 安全审查
`security-researcher` → 风险评估 → 加固方案 → `tool-developer` → 实施

## Agent 编排原则

### Fresh Agent Per Task

每个任务派发一个新 agent，用完即销毁。借鉴 Claude Code 内部的 subagent-driven-development 模式。

**主 agent（协调者）负责：**
- 读取大文件（抓包日志、二进制数据）
- 提取关键信息，构造精简上下文
- 派发子 agent 并提供完整上下文
- 汇总子 agent 结果

**子 agent 负责：**
- 接收主 agent 提供的完整上下文（不自行读取大文件）
- 执行单一任务
- 返回结构化结果
- 完成后销毁

**好处：**
- 避免上下文污染（10MB 抓包文件不会进入所有 agent 的上下文）
- 并行安全（agent 间不共享状态）
- 失败隔离（一个 agent 失败不影响其他）

### 并行调度规则

**可以并行的任务：**
- 不同维度的分析（协议 / 安全 / 二进制）
- 实现与文档编写
- 多个独立子系统的逆向

**必须串行的任务：**
- 有数据依赖（如 API 设计依赖协议分析结果）
- 会编辑同一文件
- 需要前一步的结论作为输入

### Codex 跨模型审查

在 Phase 5 中使用 `/codex:review` 和 `/codex:adversarial-review` 引入 GPT-5.4 视角。

| 命令 | 用途 | 触发时机 |
|------|------|----------|
| `/codex:review` | 代码质量审查 | CLI 实现完成后 |
| `/codex:adversarial-review` | 质疑逆向假设和设计选择 | 三层验证的最后一步 |
| `/codex:rescue` | 深度调查、卡住时的二次诊断 | 任何阶段遇到瓶颈时 |

## 知识积累（必须执行）

每次逆向会话的成果必须沉淀到知识库，越用越完善：

| 发现类型 | 更新文件 | 说明 |
|----------|----------|------|
| 新 API 端点 | `docs/api/endpoints.md` | 端点、参数、响应格式 |
| 新协议字段 | `docs/protocol/fields.md` | 字段编号、类型、语义 |
| 加密方式 | `docs/security/crypto-findings.md` | 算法、密钥来源、用途 |
| 已有项目经验 | `docs/protocol/prior-art.md` | GitHub 已有项目的发现和经验 |
| 踩坑记录 | `docs/implementation/pitfalls.md` | 遇到的问题和解决方案 |

**规则：不更新知识库的逆向会话是不完整的。**

## 决策原则

1. **协议优先** — 深入理解协议，不盲目实现
2. **安全第一** — 保护用户凭据，遵守 ToS
3. **简洁设计** — CLI 接口简单直观，易于使用
4. **代码质量** — 清晰、可维护、有注释
5. **文档完善** — 技术文档和用户文档并重
6. **渐进增强** — 先实现核心功能，再扩展

## 文档管理

每个 Agent 产出存放在 `docs/<role>/`：

| Agent | 目录 | 产出内容 |
|-------|------|----------|
| `protocol-analyst` | `docs/protocol/` | 协议分析报告、API 端点文档、数据格式说明 |
| `security-researcher` | `docs/security/` | 安全分析、风险评估、加固方案 |
| `reverse-engineer` | `docs/reverse/` | 二进制分析、算法还原、Protobuf schema |
| `api-architect` | `docs/api/` | API 设计文档、命令结构、使用示例 |
| `tool-developer` | `docs/implementation/` | 实现细节、技术难点、测试方法 |
| `doc-writer` | 项目根目录 | README.md、使用指南、故障排查 |

## 共识记忆

- **`memories/consensus.md`** — 跨会话接力棒，记录研究方向和下一步行动
- **`projects/<name>/STATUS.md`** — 项目级状态文档
- **`docs/<role>/`** — 各 Agent 工作成果

## 沟通规范

- 中文沟通，技术术语保留英文
- 具体可执行，不说废话
- 技术讨论基于证据（抓包、代码、测试）
- 每次讨论必有 Next Action

## 技能库

74 个 Claude 技能，定义在 `.claude/skills/`。

### 逆向工程核心（自研）

| 技能 | 能力 |
|------|------|
| `protobuf-reverse` | Protobuf 盲解码与 schema 恢复 |
| `websocket-debug` | WebSocket 实时调试与分析 |
| `traffic-to-api-doc` | 抓包流量→OpenAPI 文档管线 |
| `protocol-reverse` | 通用协议逆向方法论 |
| `crypto-analysis` | 加密算法识别与分析 |
| `api-fuzzing` | 基于 OpenAPI 的自动化 API 模糊测试 |

### 逆向工程与安全

| 技能 | 能力 |
|------|------|
| `security-audit` | 安全审计 |
| `code-review-security` | 代码安全审查 |
| `sentry-security-review` | Python/Django 安全审查 |
| `static-analysis` | 静态分析工作流 |
| `variant-analysis` | 漏洞变体发现 |
| `semgrep-rule-creator` | 自定义 Semgrep 规则 |
| `supply-chain-risk-auditor` | 供应链风险评估 |
| `differential-review` | 代码变更审查 |
| `sharp-edges` | 危险 API 识别 |
| `insecure-defaults` | 不安全默认配置检测 |
| `ffuf-skill` | Web 模糊测试 |
| `playwright-skill` | 浏览器自动化 + API 测试 |
| `bufbuild-protobuf` | Protobuf schema 设计与验证 |

### 网络分析与逆向（Anthropic Cybersecurity）

| 技能 | 能力 |
|------|------|
| `analyzing-network-traffic-with-wireshark` | Wireshark 流量分析 |
| `performing-network-forensics-with-wireshark` | Wireshark 网络取证 |
| `analyzing-network-packets-with-scapy` | Scapy 数据包分析 |
| `reverse-engineering-malware-with-ghidra` | Ghidra 逆向 |
| `analyzing-golang-malware-with-ghidra` | Ghidra 分析 Go 程序 |
| `reverse-engineering-android-malware-with-jadx` | JADX Android 逆向 |
| `reverse-engineering-dotnet-malware-with-dnspy` | dnSpy .NET 逆向 |
| `reverse-engineering-ios-app-with-frida` | Frida iOS 逆向 |
| `performing-binary-exploitation-analysis` | 二进制漏洞利用分析 |
| `intercepting-mobile-traffic-with-burpsuite` | Burp Suite 流量拦截 |
| `testing-for-xss-vulnerabilities-with-burpsuite` | Burp Suite XSS 测试 |

### 智能合约审计（QuillAudits）

| 技能 | 能力 |
|------|------|
| `quillaudits-reentrancy-pattern-analysis` | 重入攻击分析 |
| `quillaudits-oracle-flashloan-analysis` | 预言机与闪电贷分析 |
| `quillaudits-behavioral-state-analysis` | 行为状态分析 |
| `quillaudits-external-call-safety` | 外部调用安全 |
| `quillaudits-input-arithmetic-safety` | 输入与算术安全 |
| `quillaudits-proxy-upgrade-safety` | 代理与升级安全 |
| `quillaudits-signature-replay-analysis` | 签名与重放分析 |
| `quillaudits-dos-griefing-analysis` | 拒绝服务分析 |
| `quillaudits-semantic-guard-analysis` | 语义防护分析 |
| `quillaudits-state-invariant-detection` | 状态不变量检测 |

### 研究与分析

| 技能 | 能力 |
|------|------|
| `deep-research` | 企业级多源深度调研 |
| `deep-analysis` | 深度分析 |
| `deep-reading-analyst` | 深度阅读分析 |
| `scientific-critical-thinking` | 批判性思维 |
| `competitive-intelligence-analyst` | 竞品情报分析 |
| `github-explorer` | GitHub 项目探索 |
| `premortem` | 风险预判 |

### 通用工具

| 技能 | 能力 |
|------|------|
| `team` | Agent 团队协作 |
| `skill-creator` | 创建新技能 |
| `find-skills` | 查找技能 |
| `agent-browser` | 浏览器自动化 |
| `web-scraping` | 网页抓取 |
| `firecrawl` | Web 抓取与结构化提取 |
| `senior-qa` | 高级 QA 测试 |
| `devops` | 部署与运维 |
| `websh` | Web Shell |

### 商业与营销（备用）

`micro-saas-launcher`, `product-strategist`, `pricing-strategy`, `market-sizing-analysis`, `startup-business-models`, `startup-financial-modeling`, `financial-unit-economics`, `content-strategy`, `seo-audit`, `seo-content-strategist`, `email-sequence`, `cold-email-sequence-generator`, `ph-community-outreach`, `community-led-growth`, `user-persona-creation`, `user-research-synthesis`, `ux-audit-rethink`, `tailwind-v4-shadcn`, `marketing-godin`（暂不常用）

## MCP 服务器

| 服务器 | 功能 |
|--------|------|
| `semgrep` | 实时代码安全扫描 |
| `mcp-security-audit` | npm 依赖漏洞扫描 |
| `secops-mcp` | 15 个渗透测试工具集（Nmap, Nuclei, SQLMap 等） |
| `ghidra-mcp` | Ghidra 自动化逆向 |

## CLI 工具

| 工具 | 用途 |
|------|------|
| `protobuf_inspector` | 无 schema Protobuf 解码 |
| `pbtk` | Protobuf 逆向工具集（提取、转换、fuzzing） |
| `bbpb` | Protobuf 无 schema 解码（Burp Suite 集成） |
| `wscat` | WebSocket CLI 客户端 |
| `websocat` | 高级 WebSocket 管道操作 |
| `mitmproxy` | HTTPS/WebSocket 代理拦截 |
| `mitmproxy2swagger` | 抓包流量→OpenAPI 3.0 文档 |
| `schemathesis` | 基于 OpenAPI 的 API 自动化测试 |
| `grpcurl` | gRPC CLI 调试与测试 |

