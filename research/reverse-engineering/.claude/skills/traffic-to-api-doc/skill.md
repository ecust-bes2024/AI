---
name: traffic-to-api-doc
description: "从抓包流量自动生成 API 文档。当需要将 mitmproxy 抓包数据转换为 OpenAPI 规范、生成 API 文档、或逆向未公开 API 时使用。"
---

# 流量→API 文档管线

从网络抓包自动生成 OpenAPI 3.0 规范文档。

## 工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| `mitmproxy` | 流量捕获 | `mitmdump -w traffic.flow` |
| `mitmproxy2swagger` | 生成 OpenAPI | `mitmproxy2swagger -i traffic.flow -o spec.yml` |
| `schemathesis` | 验证 API | `st run spec.yml --base-url=...` |

## 标准工作流

### Phase 1: 捕获流量

```bash
# 启动 mitmproxy 保存流量
mitmdump -w traffic.flow

# 或使用 mitmweb 可视化
mitmweb -w traffic.flow

# 配置目标应用使用代理
# HTTP_PROXY=http://127.0.0.1:8080
# HTTPS_PROXY=http://127.0.0.1:8080
```

### Phase 2: 生成 OpenAPI 规范

```bash
# 第一遍：识别 API 端点（生成初始 spec）
mitmproxy2swagger -i traffic.flow -o api_spec.yml -p https://target.com

# 编辑 api_spec.yml：
# - 将需要的端点从 ignore: 改为正常状态
# - 删除不需要的端点

# 第二遍：生成详细规范（含参数、响应示例）
mitmproxy2swagger -i traffic.flow -o api_spec.yml -p https://target.com --examples
```

### Phase 3: 从 HAR 文件生成

```bash
# 浏览器 DevTools → Network → Export HAR
mitmproxy2swagger -i traffic.har -o api_spec.yml -p https://target.com --examples
```

### Phase 4: 验证与完善

```bash
# 用 schemathesis 验证 API 规范
st run api_spec.yml --base-url=https://target.com

# 或 dry-run 模式（不实际发请求）
st run api_spec.yml --dry-run
```

## 输出示例

```yaml
openapi: "3.0.0"
info:
  title: "Target API (Reverse Engineered)"
  version: "1.0.0"
paths:
  /api/v1/messages/send:
    post:
      summary: "发送消息"
      requestBody:
        content:
          application/x-protobuf:
            example: "base64_encoded_data"
      responses:
        "200":
          description: "成功"
```

## 技巧

1. **多次操作** — 重复执行目标功能，捕获更多请求变体
2. **过滤噪音** — 用 `mitmproxy2swagger -p` 指定 API 前缀，过滤无关请求
3. **参数化路径** — 将 `/users/12345` 改为 `/users/{id}`
4. **认证信息** — 记录 Cookie/Token 格式，标注在 securitySchemes 中
5. **Protobuf 端点** — content-type 为 protobuf 的端点需要额外用 protobuf-reverse 技能解码
