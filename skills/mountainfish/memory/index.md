# Mountainfish 记忆库索引

> 运行 `python scripts/health-check.py --update-index` 自动刷新统计

## 分层统计

| 层级 | 数量 | 上限 | 状态 |
|------|------|------|------|
| 铁律 Rules | 0 | 5 | ⚪ |
| 指南 Guidelines | 5 | 20 | 🟢 |
| 参考 Reference | 0 | 无上限 | ⚪ |
| **总计** | **5** | — | — |

## 分类统计

| 分类 | 铁律 | 指南 | 参考 | 合计 |
|------|------|------|------|------|
| code-style | 0 | 2 | 0 | 2 |
| patterns | 0 | 1 | 0 | 1 |
| anti-patterns | 0 | 1 | 0 | 1 |
| tech-stack | 0 | 1 | 0 | 1 |
| project-structure | 0 | 0 | 0 | 0 |
| conventions | 0 | 0 | 0 | 0 |

## 最近更新

- 2026-07-03: 添加"参数传递优于全局变量"（指南 · patterns）
- 2026-07-03: 记忆系统架构升级至 v2.0（三级分层）

## 文件列表

| 文件 | 说明 |
|------|------|
| [code-style.md](./code-style.md) | 代码风格规范 |
| [patterns.md](./patterns.md) | 设计模式和最佳实践 |
| [anti-patterns.md](./anti-patterns.md) | 需要避免的写法 |
| [tech-stack.md](./tech-stack.md) | 技术栈偏好 |
| [project-structure.md](./project-structure.md) | 项目结构偏好 |
| [conventions.md](./conventions.md) | 其他约定 |
