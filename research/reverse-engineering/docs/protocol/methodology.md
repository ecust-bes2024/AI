# 协议逆向方法论

## 标准流程

### Phase 1: 侦察（Reconnaissance）
1. **确定目标** — 明确要逆向的协议和功能
2. **环境准备** — 配置抓包工具（Wireshark/mitmproxy/Charles）
3. **流量捕获** — 操作目标应用，捕获网络流量
4. **初步分类** — 区分 HTTP/WebSocket/TCP/UDP 流量

### Phase 2: 分析（Analysis）
1. **端点识别** — 列出所有 API 端点和参数
2. **编码识别** — 判断数据格式（JSON/Protobuf/MessagePack/自定义）
3. **认证分析** — 理解认证机制（Cookie/Token/OAuth）
4. **会话管理** — 分析会话建立和维持方式

### Phase 3: 解码（Decoding）
1. **Protobuf 解码** — 使用 protobuf-inspector/bbpb 盲解析
2. **Schema 恢复** — 逐步还原 .proto 定义
3. **字段映射** — 将字段与业务含义对应
4. **验证** — 构造请求验证理解是否正确

### Phase 4: 实现（Implementation）
1. **API 封装** — 将协议理解转化为可用的 API
2. **CLI 开发** — 构建命令行工具
3. **测试** — 验证功能正确性
4. **文档** — 记录协议细节和使用方法

### Phase 5: 维护（Maintenance）
1. **版本追踪** — 监控目标应用更新
2. **协议变更** — 检测和适配协议变化
3. **安全更新** — 更新认证和反检测策略

## 工具链

### 抓包
- **Wireshark** — 全协议抓包分析
- **mitmproxy** — HTTPS/WebSocket 代理拦截
- **Charles** — HTTP 代理（GUI）

### Protobuf 逆向
- **protobuf-inspector** — 无 schema 解码，彩色输出
- **pbtk** — 完整工具集（提取、转换、fuzzing）
- **bbpb** — 无 schema 解码 + Burp Suite 集成
- **protoscope** — Wire format 底层分析

### WebSocket 调试
- **wscat** — WebSocket CLI 客户端
- **websocat** — 高级管道操作和转发

### 安全测试
- **Burp Suite** — Web 安全测试平台
- **ffuf** — Web 模糊测试
- **Nmap** — 端口扫描（通过 secops-mcp）
