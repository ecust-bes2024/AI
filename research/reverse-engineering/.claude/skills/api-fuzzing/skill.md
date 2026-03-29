---
name: api-fuzzing
description: "基于 OpenAPI 的自动化 API 模糊测试。当需要对逆向出的 API 进行自动化测试、发现边界问题、或验证 API 行为时使用。"
---

# API 模糊测试

基于 OpenAPI 规范对逆向出的 API 进行自动化测试。

## 工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| `schemathesis` | 基于 OpenAPI 的智能 fuzzing | `st run spec.yml` |
| `ffuf` | Web 路径/参数 fuzzing | `ffuf -u URL -w wordlist` |

## 标准工作流

### Phase 1: 准备 OpenAPI 规范

```bash
# 如果已有规范
st run api_spec.yml --base-url=https://target.com

# 如果没有，先用 traffic-to-api-doc 技能生成
mitmproxy2swagger -i traffic.flow -o api_spec.yml -p https://target.com --examples
```

### Phase 2: Schemathesis 自动测试

```bash
# 基础测试（所有端点）
st run api_spec.yml --base-url=https://target.com

# 带认证
st run api_spec.yml --base-url=https://target.com \
  -H "Cookie: session=xxx"

# 指定测试策略
st run api_spec.yml --base-url=https://target.com \
  --hypothesis-max-examples=100 \
  --stateful=links

# 只测试特定端点
st run api_spec.yml --base-url=https://target.com \
  -E /api/v1/messages

# 输出详细报告
st run api_spec.yml --base-url=https://target.com \
  --cassette-path=results.yaml
```

### Phase 3: FFUF 路径发现

```bash
# 发现隐藏 API 端点
ffuf -u https://target.com/api/FUZZ -w /path/to/wordlist.txt

# 参数 fuzzing
ffuf -u "https://target.com/api/search?FUZZ=test" \
  -w /path/to/params.txt

# 带认证和速率限制
ffuf -u https://target.com/api/FUZZ \
  -w wordlist.txt \
  -H "Cookie: session=xxx" \
  -rate 10
```

### Phase 4: 分析结果

```bash
# 查看 schemathesis 测试结果
st replay results.yaml

# 常见发现类型：
# - 500 Internal Server Error（服务器崩溃）
# - 意外的 200 响应（权限绕过）
# - 响应格式不一致（未处理的边界情况）
# - 超时（性能问题）
```

## 测试策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 边界值 | 空值、超长字符串、极大/极小数字 | 所有参数 |
| 类型混淆 | 字符串传数字、数组传对象 | 弱类型 API |
| 注入 | SQL、XSS、命令注入 payload | 用户输入字段 |
| 认证绕过 | 无 token、过期 token、他人 token | 认证端点 |
| 并发 | 同时发送相同请求 | 交易/计数类 API |

## 安全提醒

- 只对自己拥有或获得授权的系统进行 fuzzing
- 设置合理的速率限制（`-rate` 参数）
- 避免在生产环境进行破坏性测试
- 记录所有测试活动，便于审计
