---
name: protobuf-reverse
description: "Protobuf 盲解码与 schema 恢复。当需要解码未知 Protobuf 数据、从二进制提取 .proto 定义、分析 Protobuf wire format 时使用。"
---

# Protobuf 逆向工程

无 schema 情况下解码、分析和恢复 Protobuf 协议定义。

## 工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| `protobuf_inspector` | 盲解码，彩色输出 | `protobuf_inspector < data.bin` |
| `bbpb` | 无 schema 解码/编码 | `bbpb decode < data.bin` |
| `pbtk` | 从二进制提取 .proto | `pbtk-from-binary app.apk` |

## 标准工作流

### Phase 1: 盲解码（无任何 schema）

```bash
# 方法 1: protobuf-inspector 自动解析
echo -n "BINARY_DATA" | protobuf_inspector

# 方法 2: bbpb 解码为 JSON
bbpb decode < captured_data.bin

# 方法 3: Python 脚本解码
python3 -c "
from blackboxprotobuf import decode_message
with open('data.bin', 'rb') as f:
    msg, typedef = decode_message(f.read())
    print(msg)
    print(typedef)
"
```

### Phase 2: 类型推断与优化

```python
# 使用 blackboxprotobuf 渐进式优化类型定义
from blackboxprotobuf import decode_message, encode_message

# 第一次解码，获取自动推断的 typedef
msg, typedef = decode_message(raw_data)

# 根据观察修正字段类型
typedef['1']['type'] = 'string'  # 修正为字符串
typedef['2']['type'] = 'uint64'  # 修正为无符号整数

# 用修正后的 typedef 重新解码
msg, _ = decode_message(raw_data, typedef)
```

### Phase 3: Schema 恢复

```bash
# 从 APK/二进制提取完整 .proto 定义
pbtk-from-binary target.apk

# 从 Web 应用提取
pbtk-web-extract https://target.com

# 从 JAR 文件提取
pbtk-jar-extract target.jar
```

### Phase 4: 验证与文档化

```python
# 用恢复的 schema 编译并验证
# protoc --python_out=. recovered.proto

# 对比盲解码和 schema 解码结果
import recovered_pb2
msg = recovered_pb2.MessageType()
msg.ParseFromString(raw_data)
```

## Wire Format 速查

| Wire Type | 含义 | 编码方式 |
|-----------|------|----------|
| 0 | Varint | int32, int64, uint32, uint64, sint32, sint64, bool, enum |
| 1 | 64-bit | fixed64, sfixed64, double |
| 2 | Length-delimited | string, bytes, embedded messages, packed repeated |
| 5 | 32-bit | fixed32, sfixed32, float |

## 常见陷阱

- Wire Type 2 可能是 string、bytes 或嵌套消息，需要尝试递归解码
- 字段编号跳跃可能意味着废弃字段或 oneof
- packed repeated 字段看起来像单个 bytes 字段
- sint32/sint64 使用 ZigZag 编码，负数不会产生 10 字节 varint

## 与 mitmproxy 集成

```python
# mitmproxy addon: 实时解码 Protobuf 流量
from mitmproxy import http
from blackboxprotobuf import decode_message

def response(flow: http.HTTPFlow):
    if "protobuf" in flow.response.headers.get("content-type", ""):
        msg, typedef = decode_message(flow.response.content)
        flow.response.comment = str(msg)
```
