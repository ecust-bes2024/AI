# lark-cli

飞书(Feishu/Lark) 命令行消息工具。使用用户 Cookie 认证（非机器人 Token），支持发消息、搜索联系人、WebSocket 实时监听。

## 安装

```bash
cd ~/Code/lark-cli
pip install -r requirements.txt
```

依赖：`requests`、`protobuf>=5.28.0`、`websockets`

## 配置

### 快速配置（推荐）

```bash
python3 lark_cli.py setup
```

按提示操作：打开飞书网页版 → F12 → 复制 Cookie → 自动验证并保存。

### 手动配置

Cookie 来源（二选一）：

- **环境变量**：`export LARK_COOKIE="your_cookie_string"`
- **配置文件**：`~/.config/lark-cli/config.json`
  ```json
  { "cookie": "your_cookie_string" }
  ```

### 获取 Cookie

1. 打开 https://www.feishu.cn/messenger/
2. 登录账号
3. F12 → Application → Cookies，复制所有 Cookie
   （或在 Console 执行 `document.cookie`）

## 使用

```bash
# 查看当前登录用户
python3 lark_cli.py me

# 搜索用户/群组
python3 lark_cli.py search "张三"

# 发消息（按用户名搜索）
python3 lark_cli.py send --to "张三" --msg "你好"

# 发消息（指定 chat_id）
python3 lark_cli.py send --chat-id "oc_xxx" --msg "你好"

# 给自己发消息
python3 lark_cli.py notify "提醒内容"

# 实时监听消息（人类可读）
python3 lark_cli.py watch

# 实时监听消息（JSON 行，适合管道处理）
python3 lark_cli.py watch --json
```

### watch --json 输出格式

```json
{
  "from_id": "123456",
  "from_name": "张三",
  "chat_id": "oc_xxx",
  "chat_type": "p2p",
  "group_name": null,
  "content": "消息内容",
  "is_from_me": false,
  "timestamp": 1709453000
}
```

`chat_type`：`p2p`（单聊）或 `group`（群聊）。群聊时 `group_name` 为群名。

## Claude Code 集成

将 `commands/lark.md` 复制到 Claude Code 命令目录即可使用 `/lark` 斜杠命令：

```bash
cp commands/lark.md ~/.claude/commands/lark.md
```

用法示例：
- `/lark send 张三 你好`
- `/lark search 项目组`
- `/lark notify 任务完成`
- `/lark me`

## 项目结构

```
lark_cli.py      # CLI 入口，命令解析与分发
lark_api.py      # Feishu API 客户端（认证、消息、搜索）
lark_daemon.py   # WebSocket 实时消息监听
lark_proto.py    # Protobuf 消息构建与解码
lark_utils.py    # 工具函数（request ID、access key 生成）
proto_pb2.py     # 编译后的 protobuf 定义
commands/        # Claude Code slash command 模板
```

## 致谢

本项目基于 [LarkAgentX](https://github.com/cv-cat/LarkAgentX) 的协议分析和 Protobuf 逆向成果，在此基础上重构为轻量级 CLI 工具。感谢原作者的贡献。

## 注意事项

- Cookie 会过期，过期后需重新执行 `lark setup`
- 本工具使用用户凭据，非官方 API，仅供个人使用
