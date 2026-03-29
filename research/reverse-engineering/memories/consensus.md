# 共识记忆

## 研究方向

**深度理解通信协议，构建实用工具集。** 通过协议逆向、安全研究、工具开发，探索未公开 API 的实现方式，积累逆向工程方法论。

## 当前项目

### lark-cli（飞书 CLI 工具）
- **位置**: `projects/lark-cli/`
- **状态**: 基础功能完成，进入增强阶段
- **技术**: Protobuf + WebSocket + Cookie 认证

## 核心工作流（2026-03-29 更新）

### 管线化逆向流程
1. **Phase 0 调研先行** — 先搜 GitHub 已有项目，借鉴经验减少弯路
2. **Phase 1-3 管线并行** — 抓包/解码/开发可并行推进
3. **Phase 4 闭环验证** — 逆向→规范→测试→修正→再测试
4. **知识积累** — 每次会话必须更新知识库

### 知识库位置
- `docs/api/endpoints.md` — API 端点清单
- `docs/protocol/fields.md` — 协议字段清单
- `docs/protocol/prior-art.md` — GitHub 已有项目经验
- `docs/security/crypto-findings.md` — 加密发现
- `docs/implementation/pitfalls.md` — 踩坑记录

## 工具链

- **74 个 Claude 技能**（含 6 个自研逆向核心技能）
- **4 个 MCP 服务器**（Semgrep, mcp-security-audit, secops-mcp, GhidraMCP）
- **9 个 CLI 工具**（protobuf-inspector, pbtk, bbpb, wscat, websocat, mitmproxy, mitmproxy2swagger, schemathesis, grpcurl）

## Next Action

- 使用优化后的流程对 lark-cli 进行增强
- 补充 lark-cli 的知识库条目
- 探索新的逆向目标
