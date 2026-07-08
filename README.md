# Mountainfish Style Skill

Claude Code 知识沉淀技能 - 自动收集、分析和应用编码经验。

## 版本

| 版本 | 日期 | 主题 |
|------|------|------|
| **v2.1.1** | 2026-07-08 | Token 优化：所有命令改用脚本预处理 |
| v2.1.0 | 2026-07-03 | 代码画像 /profiling + --compare 跨项目训练 |
| v2.0.0 | 2026-07-03 | 记忆分层架构 · 冲突裁决 · 验证门禁 · 健康审计 |
| v1.2.0 | — | 自动注入 |
| v1.1.0 | — | 代码风格分析 |
| v1.0.0 | — | 初始版本 |

## 功能概览

| 功能 | 说明 |
|------|------|
| 三级分层注入 | 铁律(≤5)·指南(≤20)·参考(无上限)，上下文 ≤2800 token |
| **脚本预处理**（v2.1.1） | 所有命令改用 Python 脚本分析，token 节省 83-92% |
| **代码画像**（v2.1） | 分析项目惯用写法 + 跨项目对比 + 输出可沉淀经验条目 |
| 任务后钩子 | 代码生成后自动扫描违规（最多 1 条） |
| 机械门禁 | check-style.py exit code 强制验证 |
| 健康审计 | 5 维检查：矛盾·过期·孤立·重复·铁律膨胀 |
| 冲突裁决 | 多源规范冲突时按优先级链自动裁决并告警 |
| 精确沉淀 | --type --tier 分类回流 + 反污染自检 |
| 代码分析 | 分析 C/C++ 源码的风格特征 |
| 配置生成 | 生成 mf_style.yaml 和 .clang-format |

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
├── AGENTS.md                          # Agent 配置
├── skills/
│   └── mountainfish/
│       ├── SKILL.md                   # Skill 主文件（v2.0 三级分层注入 + 任务后钩子）
│       ├── memory/                    # 记忆库（v2.0 三级分层）
│       │   ├── index.md               # 分层索引（统计 + 摘要）
│       │   ├── code-style.md          # 代码风格（铁律 / 指南 / 参考）
│       │   ├── patterns.md            # 设计模式（铁律 / 指南 / 参考）
│       │   ├── anti-patterns.md       # 避坑指南（铁律 / 指南 / 参考）
│       │   ├── tech-stack.md          # 技术栈（铁律 / 指南 / 参考）
│       │   ├── project-structure.md   # 项目结构（铁律 / 指南 / 参考）
│       │   └── conventions.md         # 其他约定（铁律 / 指南 / 参考）
│       └── scripts/
│           ├── analyzer.py            # 代码风格分析器
│           ├── profile_generator.py   # 配置生成器
│           ├── check-style.py         # [v2.0] 机械门禁：命名 / 反模式 / 技术栈检查
│           ├── health-check.py        # [v2.0] 健康审计：5 维检查 + --update-index
│           ├── profiler.py            # [v2.1] 代码画像：惯用写法检测 + 跨项目对比
│           └── memory-loader.py      # [v2.1.1] 记忆库分层加载：start/inject + 过滤
└── commands/
    ├── mountainfish_integrate.md      # [v2.0] 经验沉淀（+ --type --tier --health）
    ├── mountainfish_start.md          # [v2.1.1] 分层加载启动（调用 memory-loader.py）
    ├── mountainfish_inject.md         # [v2.1.1] 手动精确注入（调用 memory-loader.py + 过滤）
    └── mountainfish_profiling.md      # [v2.1.1] 代码画像（调用 profiler.py）
```

## 使用方式

### 自动模式（推荐）

讨论代码相关话题时，skill 自动激活并分层注入经验：
- 铁律（≤5 条）无条件全量注入，~500 token
- 指南（≤20 条）会话启动时注入标题+原则摘要，~800 token
- 参考（无上限）按标签/关键词匹配 Top-5，~1500 token

触发关键词：写代码、命名、代码风格、设计模式、重构、代码审查、调试/修复、项目结构。

### 手动命令

```bash
# 会话启动（分层加载）
/mountainfish_start

# 经验沉淀
/mountainfish_integrate                       # 从对话提取
/mountainfish_integrate --analyze ./src       # 分析 C/C++ 代码风格
/mountainfish_integrate --type gotcha --tier reference "描述"  # [v2.0] 精确沉淀
/mountainfish_integrate --health              # [v2.0] 健康快速检查
/mountainfish_integrate --health --full       # [v2.0] 健康全面审计

# 手动注入
/mountainfish_inject                          # 全部经验（≤3000 token）
/mountainfish_inject code-style               # 按分类
/mountainfish_inject --tier rule              # [v2.0] 按层级
/mountainfish_inject --tier guideline code-style  # [v2.0] 组合筛选
```

### 机械门禁

```bash
# 检查源码目录
python skills/mountainfish/scripts/check-style.py ./src

# 仅检查命名规范
python skills/mountainfish/scripts/check-style.py ./src --naming

# JSON 输出
python skills/mountainfish/scripts/check-style.py ./src --json
```

### 健康审计

```bash
# 快速检查（矛盾 + 过期 + 铁律膨胀）
python skills/mountainfish/scripts/health-check.py

# 全面审计（5 维）
python skills/mountainfish/scripts/health-check.py --full

# 刷新 index.md 统计
python skills/mountainfish/scripts/health-check.py --update-index
```

### 代码画像（v2.1 新增）

```bash
# 分析项目惯用写法
python skills/mountainfish/scripts/profiler.py ./src

# 跨项目对比
python skills/mountainfish/scripts/profiler.py --compare a-profile.md b-profile.md

# JSON 输出
python skills/mountainfish/scripts/profiler.py ./src --json
```

## 记忆库管理

记忆库位于 `skills/mountainfish/memory/`，采用 **v2.0 三级分层架构**：

| 层级 | 数量上限 | 注入时机 | 示例 |
|------|----------|----------|------|
| 铁律 Rules | ≤5 | 每次会话无条件全量注入 | "参数传递优于全局变量"（如升级为铁律） |
| 指南 Guidelines | ≤20 | 会话启动注入摘要，按需展开 | "所有外设驱动统一用 BSP 层封装" |
| 参考 Reference | 无上限 | 标签/关键词匹配 Top-5 检索 | "GD32F470 USART1 需额外分频" |

每个条目遵循 D8 格式规范，包含元数据：
```markdown
### 条目名  `<!-- tier: guideline -->`
**原则**: 一句话
<!-- type: pattern -->
<!-- tags: C, 嵌入式, FreeRTOS -->
<!-- created: 2026-07-03 -->
<!-- last-applied: 2026-07-03 -->
```

### 经验分类

| 类型 | 含义 | 示例 |
|------|------|------|
| `decision` | 设计决策（为什么选 A 不选 B） | "用 FreeRTOS 而非裸机轮询" |
| `convention` | 约定（团队统一做法） | "所有外设驱动统一用 BSP 层" |
| `gotcha` | 坑（非显然的行为/问题） | "GD32F470 USART1 波特率需额外分频" |
| `pattern` | 可复用模式（验证过的解法） | "参数传递优于全局变量" |

## 架构决策（v2.0.0）

| # | 决策 | 方案 |
|---|------|------|
| D1 | 记忆分层 | 铁律(≤5) / 指南(≤20) / 参考(无上限) |
| D2 | 冲突处理 | 用户指令 > 铁律 > Trellis > 指南 > CLAUDE.md，渐进确认 |
| D3 | 检索机制 | 标签过滤 + 关键词匹配（语义检索留待未来） |
| D4 | 验证机制 | 软钩子（任务后 1 条提示）+ 硬脚本（check-style.py） |
| D5 | 经验回流 | integrate 增强（--type --tier + 反污染自检） |
| D6 | 上下文预算 | ≤2800 token（铁律 500 + 指南摘要 800 + 参考 Top-5 1500） |
| D7 | 健康检查 | 5 维审计（矛盾·过期·孤立·重复·膨胀）+ --update-index |
| D8 | 条目格式 | 三级各自统一模板 + HTML 注释元数据 |
| D9 | 命令行为 | start(分层加载) / 自动触发(按需筛选) / inject(手动精确) |
| D10 | 代码画像 | profiling 先分类后分析 + 定量统计 + 缺失清单（吸收 auto-embedded 启示） |

## 版本日志

### v2.1.1 — Token 优化：所有命令改用脚本预处理 (2026-07-08)

**背景**：v2.1.0 的 profiling 命令虽然功能完整，但让 Claude 亲自读每个源文件做正则匹配，token 消耗 = O(文件数 × 模式数)。进一步审查发现 start / inject / integrate 命令也存在类似问题——Claude 手动读取 6 个 memory 文件做解析，而非调用已有脚本。

**核心变更**：

- **所有命令改为脚本预处理**：正则分析/记忆解析由 Python 脚本完成，Claude 仅负责解读 JSON 结果和生成报告
- **新增 `memory-loader.py`**：记忆库分层加载脚本，支持 `--mode start`（铁律全文 + 指南摘要 + 参考索引）和 `--mode inject`（按 tier/category/tags 过滤），输出 JSON 或格式化文本
- **profiling → `profiler.py`**：命令定义改为调用已有脚本，不手动读源文件
- **start → `memory-loader.py --mode start`**：从 6 个 memory 文件中按层级提取，替代 Claude 逐文件读取
- **inject → `memory-loader.py --mode inject`**：支持 `--tier` / `--category` / `--tags` 过滤参数
- **integrate --health → `health-check.py`**：引用已有脚本，不手动分析记忆库
- **integrate --analyze → `analyzer.py`**：引用已有脚本，不手动读源文件

**Token 节省**：

| 命令 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| `profiling` (50 文件) | ~40k token | ~3k token | **92%** |
| `start` | ~5k token | ~500 token | **90%** |
| `inject` | ~8k token | ~1k token | **87%** |
| `integrate --health` | ~3k token | ~500 token | **83%** |

**新增文件**：
- `scripts/memory-loader.py` — 记忆库分层加载脚本（~250 行）

**修改文件**（5 个）：
- `commands/mountainfish_profiling.md` — 流程改为调用 profiler.py
- `commands/mountainfish_start.md` — 重写为调用 memory-loader.py
- `commands/mountainfish_inject.md` — 重写为调用 memory-loader.py
- `commands/mountainfish_integrate.md` — Step H 引用 health-check.py，Step A 引用 analyzer.py
- `SKILL.md` — 版本号更新，新增 token 优化对照表

**设计原则**：不要手动读源文件或记忆库文件做分析，必须通过对应脚本处理。

---

### v2.1.0 — 代码画像 + 跨项目训练 (2026-07-03)

**背景**：v2.0.0 解决了"经验如何存储和注入"，但没有解决"经验从哪里来"。用户在多个项目中积累了不同的写法习惯，但缺少工具从代码中提取这些模式。同时吸收了 auto-embedded 的 4 点启示（先分类后分析、定量统计、缺失清单、零依赖）。

**核心变更**：

- **新命令 `/mountainfish_profiling`**：分析 C/C++ 项目的惯用写法，输出可直接沉淀到记忆库参考层的经验条目
- **三阶段分析管线**：Phase 1 文件分层分类（驱动/应用/工具/未分类）→ Phase 2 8 类惯用写法检测 → Phase 3 缺失清单对照
- **定量统计取代定性检测**：每种模式附带频率分布、按层分解、主流模式标记，而非仅"有/无"
- **缺失清单**：维护 9 类常见 C 嵌入式惯用写法清单，标注项目未使用的模式（缺失项往往比存在项更有信号）
- **`--compare` 模式**：四象限对比（共性/特有/分歧/共同缺失），多项目共识 → 指南候选，共同缺失 → 值得关注的空白
- **完整闭环**：观察（profiling）→ 学习（integrate）→ 查询（inject）→ 应用（start + auto-inject）

**新增文件**：
- `scripts/profiler.py` — 代码画像脚本（~550 行，零外部依赖）
- `commands/mountainfish_profiling.md` — 命令文档

**修改文件**：
- `SKILL.md` — 加 trigger 关键词，核心功能表加入 profiling，使用流程更新
- `README.md` — 版本号升级到 v2.1.0，功能概览/目录结构/使用方式/架构决策/版本日志更新

### v2.0.0 — 记忆分层架构 (2026-07-03)

**背景**：随着经验条目持续增长（10 → 100+），v1.x 的全量注入模式导致上下文膨胀、规则稀释、多源规范冲突时无明确裁决机制，且缺乏验证手段确保规则被实际遵循。

**核心变更**：

- **记忆分层**：引入三级模型（铁律≤5 / 指南≤20 / 参考无上限），按层级控制注入时机和 token 预算（总计 ≤2800）
- **冲突裁决**：建立优先级链（用户当场指令 > 铁律 > Trellis spec > 指南 > CLAUDE.md），冲突时自动裁决并告警，支持渐进式确认
- **双重验证**：软钩子（任务后自动扫描，最多报 1 条最高优先级违规）+ 硬脚本（check-style.py，exit code 强制验证）
- **经验回流**：integrate 命令增加 --type（decision/convention/gotcha/pattern）和 --tier（rule/guideline/reference）参数，加入反污染自检（4 项检查）
- **健康审计**：新增 health-check.py，5 维检查（矛盾/过期>90天/孤立/重复/铁律膨胀），支持 --update-index 自动刷新统计
- **条目标准化**：D8 统一格式，每条记忆带 HTML 注释元数据（tier/type/tags/created/last-used/expires）
- **命令语义重定义**：start（会话启动分层加载）、auto-inject（关键词匹配按需检索）、inject（手动精确控制，支持 --tier --category 组合筛选）

**新增文件**：
- `scripts/check-style.py` — 机械门禁脚本（467 行）
- `scripts/health-check.py` — 记忆健康审计脚本（~450 行）

**修改文件**（11 个）：
- `SKILL.md`、`memory/index.md`、`memory/*.md`（6 个）、`commands/mountainfish_*.md`（3 个）

**参考系统**：MindOS（治理分层、任务后钩子）、auto-embedded（机械门禁、promote 回流、类型标签）

### v1.2.0 — 自动注入

- 讨论代码话题时自动触发 skill
- 基于关键词匹配注入相关记忆

### v1.1.0 — 代码风格分析

- analyzer.py 分析 C/C++ 源码风格
- profile_generator.py 生成 .clang-format

### v1.0.0 — 初始版本

- 基础经验积累和注入
- 三个命令：integrate / start / inject
