# AI 实验室

个人 AI 研究与开发工作空间。

## 目录结构

```
~/AI/
├── research/          # 深度技术研究
├── lab/               # 实验验证
├── toolbox/           # 工具扩展
├── projects/          # 完整项目
└── sandbox/           # 临时测试
```

## 分类标准

| 分类 | 性质 | 产出 | 生命周期 | 示例 |
|------|------|------|---------|------|
| **research/** | 技术探索 | 知识、方法论 | 长期 | 逆向工程、Agent Teams 研究 |
| **lab/** | 实验验证 | 原型、数据 | 中期 | 海报生成、文本比较 |
| **toolbox/** | 工具开发 | 可复用组件 | 长期 | Skills、MCP 服务器 |
| **projects/** | 产品开发 | 可交付应用 | 长期 | 开源项目、完整应用 |
| **sandbox/** | 临时测试 | 临时文件 | 短期 | learn-temp、测试环境 |

## 当前项目

### research/ - 技术研究
- `auto-company/` - Agent Teams 协作研究
- `reverse-engineering/` - 逆向工程研究

### lab/ - 实验项目
- `claude-mem-poster/` - 海报生成实验
- `humanizer-compare/` - 文本人性化比较

### toolbox/ - 工具集
- `mcp/openclaw-memory-bridge/` - 内存桥接 MCP 服务器
- `skills/` - 自定义 Skills

### projects/ - 正式项目
- `Skill_Seekers/` - 开源项目

### sandbox/ - 临时区
- `learn-temp/` - /learn 命令输出
- `scrape_env/` - Python 虚拟环境
- `skill-seekers-real/` - 真实测试
- `skill-seekers-smoke/` - 冒烟测试

## 使用规范

1. **新项目归类**：根据项目性质选择对应目录
2. **临时文件**：统一放 sandbox/，定期清理
3. **工具复用**：可复用的工具放 toolbox/
4. **实验记录**：lab/ 中的实验保留关键数据和结论
5. **研究产出**：research/ 中的项目应有文档记录方法论

## 清理策略

- **sandbox/** - 每月清理，保留最近 30 天
- **lab/** - 实验结束后归档或删除
- **其他目录** - 长期保留，按需清理

---

最后更新：2026-03-28
