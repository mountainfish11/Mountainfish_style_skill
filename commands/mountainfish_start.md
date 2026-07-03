# /mountainfish_start

开发会话开始时，加载 Mountainfish 记忆库。

## 使用方式

```
/mountainfish_start
```

## 执行流程

### Step 1: 检查记忆库

检查 `~/.claude/skills/mountainfish/memory/` 目录是否存在：

- **不存在**：提示用户先使用 `/mountainfish_integrate` 积累经验
- **存在**：继续执行

### Step 2: 读取索引

读取 `~/.claude/skills/mountainfish/memory/index.md`，获取：
- 各分类的经验数量
- 最近更新时间

### Step 3: 加载记忆内容

读取所有记忆库文件：
- `code-style.md`
- `patterns.md`
- `anti-patterns.md`
- `tech-stack.md`
- `project-structure.md`
- `conventions.md`

### Step 4: 提取核心原则

从记忆中提取最重要的 3-5 条原则（优先级最高或最近添加的）

### Step 5: 输出摘要

输出记忆加载摘要：

```
=== Mountainfish Skill 记忆加载 ===

📚 已积累经验：
- 代码风格：X 条规则
- 设计模式：X 种偏好
- 避坑指南：X 条禁忌
- 技术栈：X 项偏好
- 项目结构：X 条约定
- 其他约定：X 条

💡 核心原则：
1. [最重要的原则]
2. [第二重要的原则]
3. [第三重要的原则]

📅 最近更新：YYYY-MM-DD

✅ 记忆已就绪，开发时将自动应用
```

### Step 6: 设置上下文

将记忆内容注入到当前会话上下文中，使后续的代码生成能够遵循这些经验。
