# API 端点清单

> 每次发现新端点时更新此文件

## 飞书 (lark-cli)

| 端点 | CMD ID | 方法 | 说明 | 发现日期 |
|------|--------|------|------|----------|
| `/im/gateway/` | 5 | POST (protobuf) | 发送消息 | 2026-03 |
| `/im/gateway/` | 13 | POST (protobuf) | 创建会话 | 2026-03 |
| `/im/gateway/` | 11021 | POST (protobuf) | 搜索联系人 | 2026-03 |
| `wss://frontier-im.feishu.cn/ws/v2` | - | WebSocket | 实时消息 | 2026-03 |
