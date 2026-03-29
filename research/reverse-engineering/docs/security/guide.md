# 安全研究指南

## 反检测策略

### Cookie/Token 管理
- 定期刷新 Cookie，避免过期
- 模拟正常用户的请求频率（1-3 秒间隔）
- 使用真实的 User-Agent 和 Header

### 请求伪装
- 保持 Header 顺序与浏览器一致
- 携带 Referer 和 Origin
- 支持 gzip/br 压缩

### 频率控制
- 随机延迟（1-5 秒）
- 指数退避（遇到 429 时）
- 避免并发请求

## 风险评估模板

| 维度 | 低风险 | 中风险 | 高风险 |
|------|--------|--------|--------|
| 检测概率 | 正常用户行为 | 异常频率 | 自动化特征明显 |
| 封禁后果 | 临时限制 | 账号封禁 | IP 封禁 |
| 恢复难度 | 等待即可 | 需要新账号 | 需要换 IP |

## 凭据安全

```bash
# 使用环境变量存储敏感信息
export LARK_COOKIE="your_cookie_here"

# 配置文件权限
chmod 600 ~/.config/lark-cli/config.json

# .gitignore 必须包含
*.cookie
config.json
.env
```
