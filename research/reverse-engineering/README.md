# 逆向工程研究

深度技术研究工作空间，专注于协议逆向、安全研究、工具开发。

## 目录结构

```
reverse-engineering/
├── .claude/          # Agent Teams 配置
│   ├── agents/       # 6 个专家 Agent 定义
│   ├── skills/       # 逆向工程专用技能
│   └── settings.json # Agent Teams 设置
├── memories/         # 共识记忆
│   └── consensus.md  # 当前状态和下一步行动
├── docs/            # 研究文档
│   ├── protocol/    # 协议分析报告
│   ├── security/    # 安全研究笔记
│   ├── api/         # API 设计文档
│   ├── implementation/ # 实现细节
│   └── reverse/     # 逆向分析笔记
└── projects/        # 具体项目
    └── lark-cli/    # 飞书 CLI 工具
```

## Agent 团队

| Agent | 专家 | 核心能力 |
|-------|------|----------|
| `protocol-analyst` | Gerald Combs | 抓包分析、协议逆向 |
| `security-researcher` | Kevin Mitnick | 反检测、安全加固 |
| `reverse-engineer` | Chris Eagle | 二进制分析、算法还原 |
| `api-architect` | Kenneth Reitz | CLI 设计、接口抽象 |
| `tool-developer` | Armin Ronacher | Python 开发、代码质量 |
| `doc-writer` | Divio Documentation | 技术写作、用户指南 |

## 当前项目

### lark-cli
飞书命令行工具，通过协议逆向实现消息发送、搜索、实时监听。

- 技术栈：Python 3 + Protobuf + WebSocket
- 状态：基础功能完成，进入增强阶段
- 文档：`projects/lark-cli/README.md`

## 使用 Agent Teams

```bash
# 进入项目目录
cd ~/AI/research/reverse-engineering

# 启动 Claude Code，Agent Teams 会自动加载
claude

# 在对话中调用 Agent
# 例如：让 protocol-analyst 分析新的 API 端点
# 例如：让 tool-developer 实现新功能
```

## 协作流程

- **新协议逆向**：protocol-analyst → security-researcher → reverse-engineer → api-architect → tool-developer → doc-writer
- **功能扩展**：api-architect → tool-developer → doc-writer
- **问题修复**：定位 → 修复 → 验证 → 文档更新

---

详细说明见 `CLAUDE.md`
