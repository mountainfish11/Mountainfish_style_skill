---
name: mountainfish
description: |
  Mountainfish 知识沉淀技能 - 帮助开发者积累和应用编码经验
  TRIGGER when:
    - 用户调用 /mountainfish_integrate, /mountainfish_start, 或 /mountainfish_inject
    - 用户说 "沉淀到mountainfish"、"记录代码风格"、"总结经验"、"沉淀经验"
    - 用户说 "记录刚才的分析"、"保存代码规范"、"记录到mountainfish"
    - 用户讨论代码风格、命名规范、设计模式等话题
    - 用户提到写代码、实现、编写、写函数、写类、写模块
    - 用户提到命名、变量名、函数名、怎么命名、取名
    - 用户提到代码风格、格式、缩进、大括号、排版
    - 用户提到设计模式、架构、模式、最佳实践
    - 用户提到重构、优化、改进代码、代码质量
    - 用户提到 review、检查代码、看看代码、代码审查
    - 用户提到 bug、错误、修复、调试、排查
    - 用户提到目录结构、模块划分、文件组织
  DO NOT TRIGGER when: 无关任务（如文档翻译、纯数学计算等）
version: 1.2.0
---

# Mountainfish Skill

将编码经验系统化沉淀，并在开发时自动应用。

## 核心功能

| 命令 | 用途 |
|------|------|
| `/mountainfish_integrate` | 将经验文档整合到记忆库 |
| `/mountainfish_start` | 开发时加载记忆库 |
| `/mountainfish_inject` | 手动精确注入指定经验 |

## 记忆库结构

```
.claude/skills/mountainfish/memory/
├── index.md              # 索引和摘要
├── code-style.md         # 代码风格
├── patterns.md           # 设计模式
├── anti-patterns.md      # 避坑指南
├── tech-stack.md         # 技术栈偏好
├── project-structure.md  # 项目结构
└── conventions.md        # 其他约定
```

## 自动注入行为（重要）

当本 skill 被触发时，**必须执行以下自动注入流程**：

### Step 1: 读取记忆库

读取以下文件（按相关性选择，至少读取 index.md + code-style.md）：

```
~/.claude/skills/mountainfish/memory/index.md        # 必读：获取记忆概览
~/.claude/skills/mountainfish/memory/code-style.md    # 必读：代码风格规则
~/.claude/skills/mountainfish/memory/patterns.md      # 可选：设计模式
~/.claude/skills/mountainfish/memory/anti-patterns.md # 可选：避坑指南
```

### Step 2: 判断注入内容

根据用户当前话题，选择相关记忆注入：

| 用户话题 | 注入文件 |
|----------|----------|
| 写代码/实现功能 | code-style.md + patterns.md |
| 命名相关 | code-style.md（命名部分） |
| 代码风格/格式 | code-style.md |
| 设计模式/架构 | patterns.md |
| 重构/优化 | code-style.md + anti-patterns.md |
| 代码审查 | code-style.md + anti-patterns.md |
| 调试/修复 | anti-patterns.md |
| 项目结构 | project-structure.md |

### Step 3: 注入到上下文

将筛选后的经验作为上下文参考注入，**静默注入，不输出冗长提示**。

注入后简短提示：
```
💡 Mountainfish: 已加载 N 条相关经验
```

### Step 4: 后续行为

在本次对话的后续代码生成中，自动遵循注入的经验：
- 使用记忆库中的命名规范
- 遵循偏好的代码风格
- 避免已知的反模式
- 采用偏好的技术栈

## 使用流程

```
1. 平时写 .md 总结编码经验
2. /mountainfish_integrate → 沉淀到记忆库
3. 开始新会话，讨论代码话题 → 自动注入经验（无需手动调用）
4. /mountainfish_inject → 需要精确控制时手动注入
```

## 注意事项

- 记忆库文件可手动编辑
- 不执行记忆中的代码，仅作为参考
- 建议定期整理和更新记忆
- 自动注入在同一会话内首次触发时生效
