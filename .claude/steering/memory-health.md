# Memory Health — 自动 Stale 检测

每次新对话开始时，如果用户的第一条消息涉及记忆系统、/learn、方法论、或知识管理相关话题，运行以下命令检查记忆健康状态：

```bash
bash /Users/jerry_hu/AI/.claude/hooks/check-stale-memories.sh
```

根据输出结果：
- 如果有 STALE 记忆：主动告知用户哪些记忆已过期，建议验证或归档
- 如果有 AGING 记忆：在相关话题时顺带提醒
- 如果全部 HEALTHY：不需要提及

当用户明确要求检查记忆健康时，无条件运行检查。

## 验证记忆的操作

当需要验证一条记忆时：
1. 检查记忆中引用的项目/工具/API 是否仍然存在
2. 检查记忆中的数据点是否仍然准确
3. 验证通过：更新 `last_verified` 为今天，根据验证次数考虑升级 `maturity`
4. 验证失败：降低 `confidence`，严重过时则标记 `maturity: deprecated`

## 成熟度升级规则（参考 CASS）

- candidate → established：被验证或引用 ≥ 3 次
- established → proven：被验证 ≥ 10 次且无负面反馈
- 任何 → deprecated：被证伪或严重过时
