# [目标应用] 逆向工程

## 目标
[描述逆向目标和动机]

## Phase 0: 调研（必须先完成）

### GitHub 已有项目
| 项目 | Stars | 可复用内容 | 链接 |
|------|-------|-----------|------|
| | | | |

### 技术栈判断
- 通信协议: [HTTP/WebSocket/gRPC/TCP]
- 序列化: [Protobuf/JSON/MessagePack/自定义]
- 加密: [TLS/自定义加密/无]
- 认证: [Cookie/Token/OAuth/自定义]

## 工具链
- 抓包: mitmproxy / Wireshark
- 解码: protobuf-inspector / bbpb
- 文档: mitmproxy2swagger
- 测试: schemathesis

## 安全原则
- 不泄露凭据（Cookie、Token 不进入日志或公开仓库）
- 避免破坏性操作
- 模拟正常用户行为，降低封禁风险

## 目录结构
```
traffic/     # 抓包数据（.flow, .pcap）
proto/       # .proto 定义文件
api-spec/    # OpenAPI 规范
src/         # 源代码
docs/        # 项目文档
```
