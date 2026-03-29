---
name: websocket-debug
description: "WebSocket 实时调试与分析。当需要连接、监听、拦截、修改 WebSocket 消息，或分析 WebSocket 协议时使用。"
---

# WebSocket 调试

实时连接、监听、拦截和分析 WebSocket 通信。

## 工具链

| 工具 | 用途 | 安装 |
|------|------|------|
| `wscat` | 交互式 WebSocket 客户端 | 已安装 |
| `websocat` | 高级 WebSocket 管道操作 | 已安装 |
| `mitmproxy` | WebSocket 流量拦截 | 已安装 |

## 快速连接

```bash
# wscat 交互式连接
wscat -c "wss://target.com/ws"

# 带自定义 Header
wscat -c "wss://target.com/ws" -H "Cookie: session=xxx" -H "Origin: https://target.com"

# websocat 连接（支持管道）
websocat wss://target.com/ws

# 二进制模式
websocat -b wss://target.com/ws
```

## 流量拦截

### mitmproxy 拦截 WebSocket

```bash
# 启动代理，拦截 WebSocket
mitmproxy --mode regular

# 命令行模式，保存流量
mitmdump -w ws_traffic.flow

# Web UI 模式
mitmweb
```

### mitmproxy addon: WebSocket 消息日志

```python
# ws_logger.py
from mitmproxy import http, ctx
import json

def websocket_message(flow: http.HTTPFlow):
    msg = flow.websocket.messages[-1]
    direction = "→" if msg.from_client else "←"

    # 尝试 JSON 解码
    try:
        data = json.loads(msg.content)
        ctx.log.info(f"{direction} {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        ctx.log.info(f"{direction} [binary] {len(msg.content)} bytes")
        ctx.log.info(f"  hex: {msg.content[:50].hex()}")
```

```bash
# 使用 addon
mitmdump -s ws_logger.py
```

### mitmproxy addon: WebSocket + Protobuf 解码

```python
# ws_protobuf_decoder.py
from mitmproxy import http, ctx
from blackboxprotobuf import decode_message

def websocket_message(flow: http.HTTPFlow):
    msg = flow.websocket.messages[-1]
    direction = "→ CLIENT" if msg.from_client else "← SERVER"

    try:
        decoded, typedef = decode_message(msg.content)
        ctx.log.info(f"{direction}: {decoded}")
    except:
        ctx.log.info(f"{direction}: [raw] {msg.content[:100]}")
```

## 消息重放与修改

```bash
# websocat: 从文件发送消息
cat messages.txt | websocat wss://target.com/ws

# websocat: 双向管道
websocat -E wss://target.com/ws cmd:"cat"

# websocat: 自动重连
websocat --autoreconnect wss://target.com/ws

# Python: 自动化 WebSocket 交互
python3 -c "
import asyncio, websockets, json

async def main():
    async with websockets.connect('wss://target.com/ws',
        extra_headers={'Cookie': 'session=xxx'}) as ws:
        await ws.send(json.dumps({'type': 'ping'}))
        response = await ws.recv()
        print(f'Received: {response}')

asyncio.run(main())
"
```

## 分析技巧

1. **识别消息格式** — 先用文本模式连接，观察是 JSON、Protobuf 还是自定义格式
2. **心跳检测** — 观察定期发送的 ping/pong 或自定义心跳消息
3. **认证流程** — 连接后通常需要发送认证消息（token/cookie）
4. **消息分类** — 按 type/cmd 字段分类，建立消息类型清单
5. **重放测试** — 修改关键字段后重放，观察服务器响应变化
