---
description: 通过飞书发送消息、搜索用户或监听消息
allowed-tools: Bash(python3*), Read
argument-hint: <send/search/watch> <参数>
---

使用 lark-cli 操作飞书。工作目录: `~/Code/lark-cli`

## 命令映射

根据 `$ARGUMENTS` 解析并执行对应命令：

### 发送消息
- `给<用户名>发<内容>` 或 `send <用户名> <内容>` 或 `<用户名> <内容>`
  → `cd ~/Code/lark-cli && python3 lark_cli.py send --to "<用户名>" --msg "<内容>"`

### 通知自己
- `notify <内容>` 或 `通知 <内容>`
  → `cd ~/Code/lark-cli && python3 lark_cli.py notify "<内容>"`

### 搜索
- `search <关键词>` 或 `搜索 <关键词>`
  → `cd ~/Code/lark-cli && python3 lark_cli.py search "<关键词>"`

### 查看当前用户
- `me` 或 `我是谁`
  → `cd ~/Code/lark-cli && python3 lark_cli.py me`

### 监听消息
- `watch` 或 `监听`
  → `cd ~/Code/lark-cli && python3 lark_cli.py watch --json`

### 配置
- `setup` 或 `配置`
  → `cd ~/Code/lark-cli && python3 lark_cli.py setup`

## 参数

$ARGUMENTS

## 智能解析

如果参数不匹配以上任何模式，默认将第一个词作为用户名，其余作为消息内容，执行 send 命令。

## 错误处理

- 如果命令报 `No cookie found`，提示用户运行 `lark setup` 或 `/lark setup`
- 如果报 cookie 验证失败，说明 cookie 已过期，需要重新获取
