# lark-cli — 飞书逆向工程

飞书(Feishu/Lark) 命令行工具。使用用户 Cookie 认证（非机器人 Token），通过逆向工程实现消息发送、搜索联系人、WebSocket 实时监听。

## 🎯 项目目标

**深度理解飞书协议，构建完整的 CLI 工具集。** 通过协议逆向、安全研究、工具开发，打造功能完善、安全可靠的飞书命令行工具。

## 技术架构

### 认证流程
Cookie string → `LarkAPI.__init__` 获取 CSRF token → 获取 user ID → 所有 API 调用使用 cookie + CSRF token

### API 通信
所有飞书 API 调用通过单一网关端点 (`/im/gateway/`) 使用 protobuf 编码的请求/响应体。每个 API 操作有数字命令 ID（如 cmd=5 发送消息，cmd=13 创建会话，cmd=11021 搜索）通过 `x-command` header 传递。

### 模块职责
- `lark_cli.py` — CLI 入口，argparse 命令解析
- `lark_api.py` — `LarkAPI` 类：认证、搜索、发送、创建会话、解析名称、构建 WebSocket URL
- `lark_proto.py` — 构建和解码 protobuf 消息，每个 API 命令有 `build_*` 和 `decode_*` 函数对
- `lark_daemon.py` — 异步 WebSocket 监听器，自动重连，解码推送消息，解析发送者/群组名称（缓存）
- `lark_utils.py` — ID/key 生成器（request ID、CID、MD5 access key）
- `proto_pb2.py` — 自动生成的 protobuf 模块，不要手动编辑

### WebSocket 流程
获取 app key → 生成 access key → 获取 frontier ticket → 连接 `wss://msg-frontier.feishu.cn/ws/v2` → 接收消息用 `build_ack_frame` 确认 → 通过 `Frame → Packet → PushMessagesRequest` protobuf 链解码

## 命令使用

```bash
# 配置
python3 lark_cli.py setup              # 交互式 Cookie 配置

# 基础功能
python3 lark_cli.py me                 # 查看当前用户
python3 lark_cli.py search "query"     # 搜索用户/群组
python3 lark_cli.py send --to "name" --msg "text"
python3 lark_cli.py send --chat-id "oc_xxx" --msg "text"
python3 lark_cli.py notify "text"      # 发给自己
python3 lark_cli.py watch              # 实时监听消息
python3 lark_cli.py watch --json       # JSON 行输出
```

## 关键细节

- 配置存储：`~/.config/lark-cli/config.json` (cookie, self_chat_id)
- `proto_pb2.py` 是 ~51KB 自动生成代码 — 只读
- `commands/lark.md` 是 Claude Code 斜杠命令模板（复制到 `~/.claude/commands/`）
- 会话类型：`1` = P2P，`2` = Group（protobuf）；映射为 `"p2p"`/`"group"`（JSON）
- 消息类型 `4` = 文本消息（当前唯一解码的类型）

## 安全原则

- **不泄露凭据** — Cookie、Token 不进入日志或公开仓库
- **避免破坏性操作** — 不进行 DDoS 或大规模攻击
- **反检测策略** — 模拟正常用户行为，降低封禁风险
