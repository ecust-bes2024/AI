# Protobuf 逆向工程指南

## 快速开始

### 1. 捕获 Protobuf 数据

```bash
# 使用 mitmproxy 拦截 HTTPS 流量
mitmproxy --mode regular --set block_global=false

# 或使用 mitmdump 保存流量
mitmdump -w traffic.flow
```

### 2. 盲解码（无 schema）

```bash
# protobuf-inspector：最直观的盲解码
echo -n "二进制数据" | protobuf_inspector

# 从文件解码
protobuf_inspector < message.bin

# bbpb：交互式解码
bbpb decode < message.bin
```

### 3. Schema 恢复

```bash
# pbtk：从应用中提取 proto 定义
pbtk-web-extract https://target-app.com    # Web 应用
pbtk-jar-extract app.jar                    # Java 应用
pbtk-from-binary app_binary                 # 二进制文件
```

### 4. 验证和测试

```bash
# 使用恢复的 schema 编码消息
protoc --encode=MessageType schema.proto < input.txt > output.bin

# 使用 schema 解码验证
protoc --decode=MessageType schema.proto < message.bin
```

## 常见 Protobuf 字段类型

| Wire Type | 含义 | 常见用途 |
|-----------|------|----------|
| 0 (Varint) | 变长整数 | int32, int64, bool, enum |
| 1 (64-bit) | 固定 64 位 | double, fixed64 |
| 2 (Length-delimited) | 长度前缀 | string, bytes, 嵌套消息 |
| 5 (32-bit) | 固定 32 位 | float, fixed32 |

## 逆向技巧

1. **对比法** — 改变一个输入，对比两次请求的差异
2. **枚举法** — 遍历可能的值，观察响应变化
3. **嵌套识别** — Wire Type 2 可能是字符串也可能是嵌套消息，用 protobuf-inspector 自动检测
4. **字段编号** — 字段编号通常是连续的，跳跃可能意味着废弃字段
