---
name: codex-deep-search
description: 用 Codex CLI 做深度搜索，适合需要多来源综合、交叉验证、比普通 web_search 更深入的研究任务。用户明确说“deep search / 深度搜索 / 详细查一下 / 深挖一下”时优先考虑。
---

# Codex Deep Search

用于比 `web_search` 更深的研究任务。

## 什么时候用

- 主题复杂，单次搜索结果太浅
- 需要多来源交叉验证
- 用户明确要求深搜 / 深挖 / 详细查

## 使用方式

### 后台模式（推荐）

```bash
nohup bash ~/AI/skills/codex-deep-search/scripts/search.sh \
  --prompt "你的研究问题" \
  --task-name "custom-task" \
  --timeout 180 \
  > /tmp/codex-deep-search.log 2>&1 &
```

启动后告诉用户：任务已开始，结果会写到结果目录。不要轮询刷屏。

### 同步模式（短任务）

```bash
bash ~/AI/skills/codex-deep-search/scripts/search.sh \
  --prompt "简短问题" \
  --output ~/AI/tmp/search-result.md \
  --timeout 90
```

然后读取输出文件并总结。

## 参数

- `--prompt`：必填，研究问题
- `--output`：可选，输出文件
- `--task-name`：可选，任务名
- `--model`：可选，默认 `gpt-5.4`
- `--timeout`：可选，默认 `180`

## 输出位置

默认写到：
- `~/AI/tmp/codex-search-results/<task>/report.md`
- `~/AI/tmp/codex-search-results/<task>/meta.json`
- `~/AI/tmp/codex-search-results/<task>/task-output.txt`
- `~/AI/tmp/codex-search-results/latest-meta.json`（最近一次任务索引）

## 当前本地适配说明

这个版本已改成适配当前机器：
- 使用本机 `codex` 路径
- 默认模型改为 `gpt-5.4`
- 结果写入 `~/AI/tmp/codex-search-results`
- 每个任务单独目录，避免并发时 meta/log 互相覆盖
- timeout 兼容 macOS：优先 `timeout`，其次 `gtimeout`，再降级到 `python3` 包装
- 调用 codex 时显式加 `--add-dir ~/AI`，允许在 `workspace-write` 沙箱下写实验室目录
- 去掉原仓库里写死的 Ubuntu 路径
- 不默认依赖 Telegram 回调

## 当前已验证结果

- `gpt-5.4` 在本机 codex CLI 可正常启动并执行研究任务
- 但当前 codex 沙箱工作目录是 `~/.openclaw/workspace`，默认只能稳定写 `workspace` / `/tmp`
- 因此如果把输出目标直接设为 `~/AI/...`，Codex 本体可能无法落盘，只能退回写到 `/tmp`

## 吸收结论

这个 skill 值得吸收，但要以“本地适配版”使用，不要直接照搬原仓库脚本。
