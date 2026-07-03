# /mountainfish_inject

将积累的经验注入到当前项目开发中。

## 模式说明

| 模式 | 触发方式 | 用途 |
|------|----------|------|
| **自动模式** | 讨论代码话题时自动触发 | 日常开发，静默注入 |
| **手动模式** | 显式调用 `/mountainfish_inject` | 精确控制注入内容 |

> 大多数情况下，自动模式已足够。手动模式用于需要精确控制的场景。

## 手动模式使用方式

```
/mountainfish_inject                # 注入所有相关经验
/mountainfish_inject code-style     # 只注入代码风格
/mountainfish_inject patterns       # 只注入设计模式
/mountainfish_inject anti-patterns  # 只注入避坑指南
/mountainfish_inject tech-stack     # 只注入技术栈
/mountainfish_inject structure      # 只注入项目结构
/mountainfish_inject conventions    # 只注入其他约定
```

## 手动模式执行流程

### Step 1: 确定注入范围

检查用户是否提供了参数 `$ARGUMENTS`：

- **无参数**：注入所有相关经验
- **有参数**：只注入指定分类的经验

### Step 2: 读取记忆库

根据注入范围，读取对应的记忆库文件：

```
~/.claude/skills/mountainfish/memory/
├── code-style.md         # 代码风格
├── patterns.md           # 设计模式
├── anti-patterns.md      # 避坑指南
├── tech-stack.md         # 技术栈偏好
├── project-structure.md  # 项目结构
└── conventions.md        # 其他约定
```

### Step 3: 注入到上下文

将筛选后的经验注入到当前会话上下文：

```
=== Mountainfish Inject 完成 ===

已注入经验：

代码风格：
- [相关规则 1]
- [相关规则 2]

设计模式：
- [相关模式 1]

避坑指南：
- [相关禁忌 1]

技术栈偏好：
- [相关偏好 1]

后续代码生成将遵循以上经验
```

### Step 4: 确认注入

在后续的代码生成中，Claude 将自动遵循注入的经验：
- 使用指定的命名规范
- 遵循偏好的代码风格
- 避免已知的反模式
- 采用偏好的技术栈

## 自动模式说明

当 SKILL.md 的触发条件匹配时（用户讨论代码相关话题），skill 会自动：

1. 读取记忆库相关文件
2. 根据话题筛选经验
3. 静默注入到上下文
4. 简短提示：`Mountainfish: 已加载 N 条相关经验`

自动模式在同一会话内首次触发时生效，不会重复注入。

## 注意事项

- 注入的经验仅在当前会话有效
- 不会修改实际代码，仅作为生成参考
- 如需永久更新经验，使用 `/mountainfish_integrate`
