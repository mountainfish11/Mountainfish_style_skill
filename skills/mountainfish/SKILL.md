---
name: mountainfish
description: |
  Mountainfish 知识沉淀技能 - 帮助开发者积累和应用编码经验
  TRIGGER when:
    - 用户调用 /mountainfish_integrate, /mountainfish_start, /mountainfish_inject 或 /mountainfish_profiling
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
    - 用户说 "分析项目风格"、"代码画像"、"profiling"、"看看这个项目的写法"、"提取代码模式"
  DO NOT TRIGGER when: 无关任务（如文档翻译、纯数学计算等）
version: 2.1.2
---

# Mountainfish Skill

将编码经验系统化沉淀，并在开发时自动应用。

## 核心功能

| 命令 | 用途 | 核心脚本 |
|------|------|----------|
| `/mountainfish_start` | 会话启动时分层加载记忆 | `memory-loader.py` |
| `/mountainfish_inject` | 手动精确注入指定经验 | `memory-loader.py` |
| `/mountainfish_integrate` | 沉淀经验到记忆库（支持分类） | `health-check.py` / `analyzer.py` |
| `/mountainfish_profiling` | 分析项目惯用写法，输出风格画像 | `profiler.py` |

## v2.1 Token 优化

所有命令的正则分析/记忆解析由 Python 脚本完成，Claude 仅负责解读结果和生成报告。

| 命令 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| `profiling` (50 文件) | ~40k token | ~3k token | 92% |
| `start` | ~5k token | ~500 token | 90% |
| `inject` | ~8k token | ~1k token | 87% |
| `integrate --health` | ~3k token | ~500 token | 83% |

**原则**：不要手动读源文件或记忆库文件做分析，必须通过对应脚本处理。

## 记忆库结构（v2.0 三级分层）

```
.claude/skills/mountainfish/memory/
├── index.md              # 分层索引和统计
├── code-style.md         # 铁律 / 指南 / 参考
├── patterns.md           # 铁律 / 指南 / 参考
├── anti-patterns.md      # 铁律 / 指南 / 参考
├── tech-stack.md         # 铁律 / 指南 / 参考
├── project-structure.md  # 铁律 / 指南 / 参考
└── conventions.md        # 铁律 / 指南 / 参考
```

### 三级分层

| 层级 | 数量上限 | 注入时机 | token 预算 |
|------|----------|----------|------------|
| 铁律 Rules | ≤5 | 每次对话无条件注入 | ~500 |
| 指南 Guidelines | ≤20 | 会话启动注入摘要，需要时展开 | ~800 |
| 参考 Reference | 无上限 | 标签/关键词匹配，Top-K(≤5) | ~1500 |

---

## 自动注入流程（v2.0）

当本 skill 被触发时，**按以下分层流程执行**：

### Step 0: 检查会话状态

检查当前会话是否已完成 `/mountainfish_start` 的全量加载：

- **已加载** → 跳过 Step 1（铁律+指南摘要），直接进入 Step 2（按需检索）
- **未加载** → 执行完整流程

### Step 1: 注入铁律 + 指南摘要（仅首次触发时执行）

读取以下内容：

```
~/.claude/skills/mountainfish/memory/index.md          # 分层索引
各 memory/*.md 中 ## 铁律 部分                           # 全部铁律（≤5 条，~500 token）
各 memory/*.md 中 ## 指南 部分的标题+原则行               # 摘要列表（~800 token）
```

注入后设置会话标记：`[Mountainfish: loaded]`

### Step 2: 按需检索指南全文 + 参考条目

根据用户当前话题标签匹配：

| 用户话题 | 匹配标签 |
|----------|----------|
| 写代码/实现功能 | #实现 #架构 |
| 命名相关 | #命名 |
| 代码风格/格式 | #格式 |
| 设计模式/架构 | #架构 #设计模式 |
| 重构/优化 | #重构 #优化 |
| 代码审查 | #审查 |
| 调试/修复 | #调试 #排错 |
| 项目结构 | #项目结构 |

检索逻辑：
1. 从指南全文 + 参考条目中按标签/关键词匹配
2. 取 Top-K（≤5 条），token 上限 1500
3. 同一会话不重复注入同一条目

### Step 3: 注入到上下文

静默注入，简短提示：

```
💡 Mountainfish: 铁律 X 条 | 指南 X 条 | 参考 X 条
```

### Step 4: 遵循注入经验

在本次对话的后续代码生成中，自动遵循注入的经验。如检测到多源冲突（Mountainfish vs Trellis vs CLAUDE.md vs 用户指令），按以下优先级裁决：

```
用户当场指令 > Mountainfish 铁律 > Trellis spec > Mountainfish 指南 > CLAUDE.md
```

检测到冲突时主动报告：

```
⚠️ 规范冲突: [来源A] 要求 X，[来源B] 要求 Y。
   按优先级使用 [来源A]。是否将 Y 加入抑制列表？
```

---

## 任务后钩子（Post-Task Hook）

**代码生成完成后自动触发**。扫描生成的代码是否违反铁律和指南：

| 优先级 | 触发条件 | 检查内容 |
|--------|----------|----------|
| 高 | 铁律违反 | 代码是否违反铁律中的规则 |
| 中 | 反模式命中 | 代码是否匹配已知 bad pattern |
| 低 | 指南偏离 | 代码是否偏离指南建议 |

行为规则：
- 最多报 1 条最高优先级违规
- 用户确认 → 修正代码
- 用户拒绝 3 次同类违规 → 提议将对应规则降级或抑制
- 用户说 "安静模式" → 跳过所有钩子

---

## 使用流程

```
1. 平时写 .md 总结编码经验
2. /mountainfish_integrate → 沉淀到记忆库（带类型+层级分类）
3. /mountainfish_start → 会话启动时加载分层记忆
4. 讨论代码话题 → 自动按需检索注入
5. /mountainfish_profiling → 分析项目风格，提取惯用写法画像
6. 代码生成后 → 任务后钩子扫描违规
```

## 注意事项

- 记忆库文件可手动编辑，但建议通过 integrate 命令沉淀
- 不执行记忆中的代码，仅作为参考
- 建议定期运行 `/mountainfish_integrate --health` 检查记忆健康
- 自动注入在同一会话内首次触发时执行全量加载，后续仅按需检索
- 上下文预算总计 ≤ 2800 token
