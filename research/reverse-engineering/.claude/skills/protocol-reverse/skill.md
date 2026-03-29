---
name: protocol-reverse
description: "通用协议逆向工程方法论。当需要分析未知网络协议、推断消息格式和状态机、或对协议进行建模时使用。"
---

# 协议逆向工程

系统化分析未知网络协议，推断消息格式、字段语义和状态机。

## 方法论

### Phase 1: 流量采集与分类

```bash
# Wireshark 抓包
tshark -i en0 -w capture.pcap -f "host target.com"

# mitmproxy 抓 HTTP/WebSocket
mitmdump -w traffic.flow

# 按协议分类
tshark -r capture.pcap -T fields -e frame.protocols | sort | uniq -c | sort -rn
```

### Phase 2: 消息格式推断

**手动分析**：
1. 收集同类型消息的多个样本
2. 对齐比较，找出固定字段和可变字段
3. 识别长度字段、类型字段、序列号
4. 确定字节序（大端/小端）

**自动推断（Netzob）**：
```python
from netzob.all import *

# 导入 PCAP
messages = PCAPImporter.readFile("capture.pcap").values()

# 自动推断消息格式
symbol = Symbol(messages=messages)
Format.splitStatic(symbol)
Format.splitAligned(symbol)

# 查看推断结果
print(symbol)
```

### Phase 3: 字段语义识别

| 模式 | 可能含义 |
|------|----------|
| 前 2-4 字节固定 | 魔数（Magic Number） |
| 递增整数 | 序列号/消息 ID |
| 固定长度 + 可变内容 | 长度前缀 + 载荷 |
| 重复出现的小整数 | 消息类型/命令 ID |
| 32 字节 hex | SHA-256 哈希 |
| 16 字节 hex | MD5 哈希或 UUID |
| Unix 时间戳范围 | 时间字段 |

### Phase 4: 状态机推断

```python
from netzob.all import *

# 基于流量推断协议状态机
automata = Automata.generateFromTraces(messages)
automata.generateDotCode()  # 输出 Graphviz 格式
```

### Phase 5: 验证与文档化

1. **构造请求** — 根据推断的格式构造测试请求
2. **修改字段** — 逐个修改字段值，观察服务器响应
3. **边界测试** — 发送超长/超短/畸形消息
4. **文档记录** — 将发现写入 `docs/protocol/` 目录

## 协议类型速查

| 特征 | 协议类型 | 分析方法 |
|------|----------|----------|
| 文本可读 | HTTP/JSON/XML | 直接阅读 |
| 二进制 + Varint | Protobuf/gRPC | 用 protobuf-reverse 技能 |
| 二进制 + 固定头部 | 自定义二进制协议 | Wireshark + 手动分析 |
| TLV 结构 | ASN.1/BER | OpenSSL asn1parse |
| 压缩数据 | gzip/zlib/brotli | 先解压再分析 |

## 输出模板

```markdown
# [协议名称] 协议分析报告

## 概述
- 传输层: TCP/UDP/WebSocket
- 端口: XXXX
- 加密: TLS/明文
- 序列化: Protobuf/JSON/自定义

## 消息格式
| 偏移 | 长度 | 字段 | 类型 | 说明 |
|------|------|------|------|------|

## 消息类型
| CMD ID | 名称 | 方向 | 说明 |
|--------|------|------|------|

## 状态机
[连接] → [认证] → [就绪] → [数据交换]
```
