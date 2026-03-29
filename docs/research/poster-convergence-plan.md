# Poster 收敛方案

**日期**: 2026-03-29

## 目标

把实验副本里已经证明有效的两条线，稳定收敛回正式 `poster`：

1. 保留现有规整主题，但升级字体系统
2. 保留强个性主题 `study-notes`

## 当前判断

### 可以立即收敛

- 原有 `research / technical / summary / project` 主题的字体系统升级
- `title_font / heading_font / label_font` 这套角色变量
- 更温和的字重和更合理的标题/二级标题高度

### 暂不立即收敛

- `study-notes` 主题

原因：

- 它方向对了
- 但还属于强风格主题
- 更适合先保留在实验室，继续做 1-2 轮内容适配验证

## 收敛顺序

### Phase 1

迁回正式 `poster`：

- 主题字体角色系统
- 现有主题的标题、二级标题、label 字体调整

目标：

- 让原有 poster “不那么死板”
- 不改变当前主题语义

### Phase 2

继续实验 `study-notes`：

- 再验证 2-3 类内容
  - 学习指南
  - cheatsheet
  - 技术概念卡

目标：

- 确认它不是只对 Spring Boot 这类内容成立

### Phase 3

如果验证稳定，再迁回正式 `poster`：

- 新增 `study-notes` 主题
- 加入自动主题判断
- 保留人工 override

## 推荐原则

- 默认主题保持稳
- 强个性主题作为可选项
- 自动判断只做建议，不替代人工指定

