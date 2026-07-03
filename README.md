<<<<<<< HEAD
# Mountainfish Style Skill

Claude Code 知识沉淀技能 - 自动收集、分析和应用编码经验。

## 功能概览

| 功能 | 说明 |
|------|------|
| 自动注入 | 讨论代码话题时自动加载记忆库经验 |
| 代码分析 | 分析 C/C++ 源码的风格特征 |
| 配置生成 | 生成 mf_style.yaml 和 .clang-format |
| 经验沉淀 | 从对话/文件中提取经验到记忆库 |

## 安装

将文件复制到 Claude Code 配置目录：

```bash
# 复制 skill 文件
cp -r skills/mountainfish ~/.claude/skills/

# 复制命令文件
cp commands/mountainfish_*.md ~/.claude/commands/
```

## 目录结构

```
Mountainfish_style_skill/
├── README.md                          # 本文件
├── skills/
│   └── mountainfish/
│       ├── SKILL.md                   # Skill 主文件（触发条件 + 行为指令）
│       ├── memory/                    # 记忆库
│       │   ├── index.md               # 索引和摘要
│       │   ├── code-style.md          # 代码风格
│       │   ├── patterns.md            # 设计模式
│       │   ├── anti-patterns.md       # 避坑指南
│       │   ├── tech-stack.md          # 技术栈偏好
│       │   ├── project-structure.md   # 项目结构
│       │   └── conventions.md         # 其他约定
│       └── scripts/
│           ├── analyzer.py            # 代码风格分析器
│           └── profile_generator.py   # 配置生成器
└── commands/
    ├── mountainfish_integrate.md      # 经验沉淀命令
    ├── mountainfish_start.md          # 记忆加载命令
    └── mountainfish_inject.md         # 手动注入命令
```

## 使用方式

### 自动模式（推荐）

讨论代码相关话题时，skill 自动激活并注入经验：

- "帮我写一个函数"
- "这个变量怎么命名"
- "重构这段代码"
- "检查代码风格"

### 手动命令

```bash
/mountainfish_integrate              # 沉淀经验到记忆库
/mountainfish_integrate --analyze ./src  # 分析 C/C++ 代码风格
/mountainfish_integrate --profile    # 生成 mf_style.yaml
/mountainfish_integrate --apply      # 生成 .clang-format
/mountainfish_start                  # 加载记忆库
/mountainfish_inject                 # 手动注入经验
/mountainfish_inject code-style      # 只注入代码风格
```

### 代码风格分析

```bash
# 分析源码目录
/mountainfish_integrate --analyze ./src

# 输出 JSON 报告
/mountainfish_integrate --analyze ./src --json

# 生成风格配置
/mountainfish_integrate --profile

# 生成 .clang-format
/mountainfish_integrate --apply
```

## 记忆库管理

记忆库文件位于 `skills/mountainfish/memory/`，可手动编辑：

- `code-style.md` - 命名规范、格式偏好、注释风格
- `patterns.md` - 设计模式、架构决策
- `anti-patterns.md` - 反模式、踩坑记录
- `tech-stack.md` - 库/框架偏好
- `project-structure.md` - 目录组织
- `conventions.md` - Git、测试、文档约定

## 版本

- v1.2.0 - 自动注入功能
- v1.1.0 - 代码风格分析
- v1.0.0 - 初始版本
=======
# Mountainfish_style_skill
Claude Code 知识沉淀技能 - 自动收集、分析和应用编码经验
>>>>>>> eda37c2358e4af0c52fa8afdbccfc96e4fd2cb3a
