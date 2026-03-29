# 逆向工程项目技能缺口分析报告

**日期**: 2026-03-28
**调研范围**: GitHub, skills.sh/Playbooks, MCP Market, X/Twitter, Reddit, Clawhub
**目标**: 找出逆向工程项目中缺失的 Protobuf 工具和 WebSocket 调试工具

---

## 执行摘要

经过多平台调研，确认逆向工程项目在 Protobuf 和 WebSocket 两个领域存在工具缺口。Protobuf 生态成熟，有多个高质量 CLI 工具和 2 个 Claude 技能可用；WebSocket 调试工具以 CLI 为主，缺少专门的 Claude 技能和 MCP 服务器。未发现专门的 Protobuf MCP 服务器或 WebSocket MCP 服务器。建议优先引入 CLI 工具（protobuf-inspector, protoscope, wscat）和 Claude 技能（bufbuild/protobuf）。

---

## 一、Protobuf 工具调研结果

### 1.1 Claude 技能（Skills）

#### bufbuild/claude-plugins/protobuf [推荐 - 高优先级]
- **来源**: [playbooks.com](https://playbooks.com/skills/bufbuild/claude-plugins/protobuf) [1]
- **功能**: 设计、验证和排查 Protocol Buffer schema，支持 buf 工具链
- **特性**: .proto 文件检查、protovalidate 约束、buf.yaml/buf.gen.yaml 配置生成、lint 和 breaking change 检测
- **安装**: `npx playbooks add skill bufbuild/claude-plugins --skill protobuf`
- **评估**: 官方 Buf 团队出品，质量可靠。侧重 schema 设计而非逆向解码，但对理解和编写 proto 定义有帮助
- **可信度**: Confirmed

#### melodic-software/claude-code-plugins/protobuf-design [可选]
- **来源**: [playbooks.com](https://playbooks.com/skills/melodic-software/claude-code-plugins/protobuf-design) [2]
- **功能**: gRPC 服务设计和 Protocol Buffer schema 指导
- **特性**: proto3 语法、streaming 模式、schema 演进策略、C# 实现指导
- **安装**: `npx playbooks add skill melodic-software/claude-code-plugins --skill protobuf-design`
- **评估**: 偏向设计和开发，与逆向工程场景关联度中等
- **可信度**: Confirmed

### 1.2 CLI 工具

#### protobuf-inspector [推荐 - 高优先级]
- **来源**: [GitHub](https://github.com/mildsunrise/protobuf-inspector) [3] | 1.1k stars
- **功能**: 在没有 schema 的情况下解析 Protobuf 编码数据，输出彩色可读结构
- **特性**: 盲解析、自动检测嵌套消息、自定义字段定义、错误容错
- **安装**: `pip install protobuf-inspector`
- **评估**: 逆向工程核心工具，无需 .proto 文件即可解码，迭代式 schema 恢复
- **可信度**: Confirmed

#### pbtk (Protobuf Toolkit) [推荐 - 高优先级]
- **来源**: [GitHub](https://github.com/marin-m/pbtk) [4] | 1.6k stars
- **功能**: 完整的 Protobuf 逆向工程和 fuzzing 工具集
- **特性**: 从 Java/C++/Web 应用提取 proto 结构、转换为 .proto 文件、交互式消息编辑和重放、GUI fuzzing
- **安装**: `pipx install pbtk` 或 `sudo snap install pbtk`
- **评估**: 最全面的 Protobuf 逆向工具，从提取到 fuzzing 全流程覆盖
- **可信度**: Confirmed

#### protoscope [推荐 - 中优先级]
- **来源**: [GitHub](https://github.com/protocolbuffers/protoscope) [5] | 417 stars
- **功能**: Protobuf wire format 的人类可读语言，支持反汇编和重新组装
- **特性**: schema 无关的 wire format 操作、启发式解码、支持创建测试数据
- **安装**: `go install github.com/protocolbuffers/protoscope/cmd/protoscope@latest`
- **评估**: Google 官方工具，适合底层 wire format 分析和修改
- **可信度**: Confirmed

#### blackboxprotobuf (bbpb) [推荐 - 中优先级]
- **来源**: [GitHub](https://github.com/nccgroup/blackboxprotobuf) [6] | 709 stars
- **功能**: 无 schema 解码和修改 Protobuf 消息
- **特性**: Burp Suite 扩展、Python 库、CLI 工具、mitmproxy 插件
- **安装**: `pip install bbpb`
- **评估**: NCC Group 出品，安全测试导向，Burp Suite 集成是独特优势
- **可信度**: Confirmed

#### ProtoDeep [可选]
- **来源**: [GitHub](https://github.com/mxrch/ProtoDeep) [7] | 138 stars
- **功能**: 解码和分析 Protobuf 数据，基于 blackboxprotobuf
- **特性**: CLI 和 Python 库、自定义定义、数据匹配和过滤、导出功能
- **安装**: `pipx install protodeep`
- **评估**: 基于 blackboxprotobuf 的上层封装，提供更友好的界面
- **可信度**: Confirmed

#### protodec [可选]
- **来源**: [GitHub](https://github.com/Xpl0itR/protodec) [8] | 80 stars
- **功能**: 从编译后的 protobuf 类反编译回 .proto 定义
- **特性**: CIL 程序集和 Il2Cpp 格式支持、gRPC 服务方法提取
- **安装**: 需要 .NET SDK 编译
- **评估**: 针对 .NET/Unity 游戏逆向的专用工具
- **可信度**: Confirmed

#### buf CLI [参考]
- **来源**: [buf.build](https://buf.build/docs/cli/) [9]
- **功能**: 现代 Protobuf 工具链，替代 protoc
- **特性**: lint、breaking change 检测、代码生成、schema registry
- **安装**: `brew install bufbuild/buf/buf`
- **评估**: 开发导向工具，非逆向专用，但对 proto 文件管理有帮助
- **可信度**: Confirmed

### 1.3 MCP 服务器

**未发现专门的 Protobuf MCP 服务器。** 搜索了 GitHub、MCP Market 和社区资源，没有找到提供 Protobuf 解码/编码功能的 MCP 服务器。

**建议**: 可考虑自建一个轻量 MCP 服务器，封装 protobuf-inspector 或 blackboxprotobuf 的功能。

---

## 二、WebSocket 调试工具调研结果

### 2.1 Claude 技能（Skills）

**未发现专门的 WebSocket 调试 Claude 技能。** 搜索了 playbooks.com、skills.sh 和 GitHub awesome-claude-skills 列表，没有找到 WebSocket 调试相关技能。

### 2.2 CLI 工具

#### wscat [推荐 - 高优先级]
- **来源**: [GitHub](https://github.com/websockets/wscat) [10] | 2.7k stars
- **功能**: WebSocket 命令行客户端（"WebSocket cat"）
- **特性**: 连接/监听模式、SSL/TLS 支持、HTTP 认证、代理支持、自定义 header、ping/pong 控制
- **安装**: `npm install -g wscat`
- **评估**: 最流行的 WebSocket CLI 工具，简单直接，适合快速调试
- **可信度**: Confirmed

#### websocat [推荐 - 高优先级]
- **来源**: [GitHub](https://github.com/vi/websocat) [11]
- **功能**: 功能丰富的 WebSocket CLI 工具，支持管道和转发
- **特性**: ws/wss 支持、Unix socket 转发、多种模式（客户端/服务器/代理）、管道操作
- **安装**: `brew install websocat` 或 `cargo install websocat`
- **评估**: 比 wscat 更强大，支持复杂的管道和转发场景，适合逆向工程中的流量分析
- **可信度**: Confirmed

#### mitmproxy [推荐 - 中优先级]
- **来源**: [mitmproxy.org](https://mitmproxy.org/) [12]
- **功能**: 交互式 HTTPS 代理，支持 WebSocket 流量拦截
- **特性**: WebSocket 消息查看和修改、SSL/TLS 拦截、Python 脚本扩展、Web UI
- **安装**: `brew install mitmproxy` 或 `pipx install mitmproxy`
- **评估**: 全能型代理工具，WebSocket 支持是其功能之一，适合需要同时分析 HTTP 和 WS 流量的场景
- **可信度**: Confirmed

#### Burp Suite WebSocket 功能 [参考]
- **来源**: [PortSwigger](https://portswigger.net/web-security/websockets) [13]
- **功能**: WebSocket 消息历史、拦截和修改
- **特性**: WebSocket history、消息拦截、Turbo Intruder 扩展
- **评估**: 商业工具（Community 版免费），WebSocket 安全测试的行业标准
- **可信度**: Confirmed

#### websocket-inspector [不推荐]
- **来源**: [GitHub](https://github.com/ecthiender/websocket-inspector) [14] | 6 stars
- **功能**: Haskell TUI WebSocket 客户端
- **评估**: 星数过低，需要 Haskell 编译环境，不推荐
- **可信度**: Confirmed

### 2.3 MCP 服务器

**未发现专门的 WebSocket 调试 MCP 服务器。** 找到的 WebSocket 相关 MCP 服务器（如 virajsharma2000/mcp-websocket [15]）是用 WebSocket 作为 MCP 传输层，而非提供 WebSocket 调试功能。

---

## 三、其他可能遗漏的逆向工程工具

### 3.1 相关博客和资源

- [逆向飞书思维导图 Protobuf](https://blog.skyju.cc/post/feishu-mindmap-protobuf-reverse-engineering-w-claude-code/) [16] - 使用 Claude Code 逆向飞书 Protobuf 的实战案例
- [Breaking Protocol Buffers: Reverse Engineering gRPC Binaries](https://ioactive.com/breaking-protocol-buffers-reverse-engineering-grpc-binaries/) [17] - IOActive 的 gRPC 逆向方法论
- [Inspecting Protobuf Messages](https://kmcd.dev/posts/inspecting-protobuf-messages/) [18] - Protobuf 消息检查工具对比
- [WebSocket Proxy and Interception Tools](https://tests.ws/testing/websocket-proxy-tools) [19] - WebSocket 代理工具汇总

---

## 四、优先级排序和引入建议

### 第一优先级（立即引入）

| 工具 | 类型 | 安装命令 | 理由 |
|------|------|----------|------|
| protobuf-inspector | CLI | `pip install protobuf-inspector` | 逆向核心：无 schema 解码 |
| pbtk | CLI | `pipx install pbtk` | 最全面的 Protobuf 逆向工具集 |
| wscat | CLI | `npm install -g wscat` | 最流行的 WebSocket CLI |
| bufbuild/protobuf | Claude 技能 | `npx playbooks add skill bufbuild/claude-plugins --skill protobuf` | 官方 Buf 团队出品 |

### 第二优先级（按需引入）

| 工具 | 类型 | 安装命令 | 理由 |
|------|------|----------|------|
| protoscope | CLI | `go install github.com/protocolbuffers/protoscope/cmd/protoscope@latest` | Google 官方 wire format 工具 |
| blackboxprotobuf | CLI | `pip install bbpb` | Burp Suite 集成 |
| websocat | CLI | `brew install websocat` | 高级 WebSocket 管道操作 |
| mitmproxy | CLI | `brew install mitmproxy` | 全能代理（如未安装） |

### 第三优先级（特定场景）

| 工具 | 类型 | 场景 |
|------|------|------|
| protodec | CLI | .NET/Unity 游戏逆向 |
| ProtoDeep | CLI | 需要更友好的 Protobuf 分析界面 |
| protobuf-design 技能 | Claude 技能 | gRPC 服务设计（非逆向） |

### 建议自建

| 工具 | 类型 | 理由 |
|------|------|------|
| Protobuf MCP Server | MCP 服务器 | 封装 protobuf-inspector/bbpb，提供 decode/encode 工具给 Claude |
| WebSocket Debug MCP Server | MCP 服务器 | 封装 wscat/websocat，提供 WS 连接和消息监控给 Claude |

---

## 五、信息盲区

1. **Clawhub 平台**: 搜索未返回有效结果，无法确认该平台是否有相关工具
2. **X/Twitter**: 搜索 API 返回 502 错误，社区讨论信息不完整
3. **skills.sh 直接搜索**: API 返回 502 错误，通过 playbooks.com 间接获取了技能信息
4. **自建 MCP 服务器的可行性**: 未评估开发工作量，需要进一步调研

---

## 参考文献

[1] Buf Build. "protobuf skill". playbooks.com. https://playbooks.com/skills/bufbuild/claude-plugins/protobuf
[2] Melodic Software. "protobuf-design skill". playbooks.com. https://playbooks.com/skills/melodic-software/claude-code-plugins/protobuf-design
[3] mildsunrise. "protobuf-inspector". GitHub. https://github.com/mildsunrise/protobuf-inspector
[4] marin-m. "pbtk: A toolset for reverse engineering and fuzzing Protobuf-based apps". GitHub. https://github.com/marin-m/pbtk
[5] Protocol Buffers. "protoscope". GitHub. https://github.com/protocolbuffers/protoscope
[6] NCC Group. "blackboxprotobuf". GitHub. https://github.com/nccgroup/blackboxprotobuf
[7] mxrch. "ProtoDeep". GitHub. https://github.com/mxrch/ProtoDeep
[8] Xpl0itR. "protodec". GitHub. https://github.com/Xpl0itR/protodec
[9] Buf Build. "Buf CLI Documentation". https://buf.build/docs/cli/
[10] websockets. "wscat". GitHub. https://github.com/websockets/wscat
[11] vi. "websocat". GitHub. https://github.com/vi/websocat
[12] mitmproxy project. "mitmproxy". https://mitmproxy.org/
[13] PortSwigger. "Testing for WebSockets security vulnerabilities". https://portswigger.net/web-security/websockets
[14] ecthiender. "websocket-inspector". GitHub. https://github.com/ecthiender/websocket-inspector
[15] virajsharma2000. "mcp-websocket". GitHub. https://github.com/virajsharma2000/mcp-websocket
[16] skyju. "逆向飞书思维导图 Protobuf". https://blog.skyju.cc/post/feishu-mindmap-protobuf-reverse-engineering-w-claude-code/
[17] IOActive. "Breaking Protocol Buffers". https://ioactive.com/breaking-protocol-buffers-reverse-engineering-grpc-binaries/
[18] kmcd.dev. "Inspecting Protobuf Messages". https://kmcd.dev/posts/inspecting-protobuf-messages/
[19] tests.ws. "WebSocket Proxy and Interception Tools". https://tests.ws/testing/websocket-proxy-tools
