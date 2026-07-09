# /mountainfish_profiling

分析 C/C++ 项目的惯用写法，输出可直接沉淀到记忆库参考层的经验条目。跨项目调用以训练 skill 的基础风格知识库。

## 使用方式

```
# 单项目分析
/mountainfish_profiling ./src                    # 分析源码目录
/mountainfish_profiling ./src --json             # JSON 输出
/mountainfish_profiling ./src --output my.md     # 指定输出路径

# 跨项目对比
/mountainfish_profiling --compare project-a.md project-b.md
/mountainfish_profiling --compare a.md b.md c.md --json
```

**自然语言触发**（自动调用此命令）：
- "分析项目风格"
- "代码画像"
- "profiling"
- "看看这个项目的写法"
- "提取代码模式"

## 执行流程（v2.1 优化：脚本预处理）

> **核心原则**：正则分析由 Python 脚本完成，Claude 仅负责解读结果和生成报告。
> 这将 token 消耗从 O(文件数×模式数) 降低到 O(1)。

### Step 1: 调用 profiler 脚本

**必须使用 Bash 工具**调用脚本，不要手动读取源文件做分析：

```bash
# 单项目分析 — JSON 输出到临时文件
python ~/.claude/skills/mountainfish/scripts/profiler.py <源码目录> --json > /tmp/mf-profile.json

# 跨项目对比
python ~/.claude/skills/mountainfish/scripts/profiler.py --compare <profile1.md> <profile2.md> --json > /tmp/mf-compare.json
```

脚本自动完成：
- **Phase 1** 文件分类（路径 + 内容特征 → driver/app/util/unknown）
- **Phase 2** 8 类惯用写法检测（typedef struct / do-while(0) / callback / ISR / 容器 / 错误处理 / 头文件保护 / volatile）
- **Phase 3** 缺失清单（对照内置常见 C 嵌入式惯用写法清单）
- 输出 `.mountainfish-profile.md` 文件（D8 格式 + 嵌入 JSON）

### Step 2: 读取 JSON 结果

使用 Read 工具读取 `/tmp/mf-profile.json`，获取结构化数据。

### Step 3: 生成人类可读报告

根据 JSON 数据，输出以下报告格式：

```
================================================================
  Mountainfish Profiling Report
  项目: <directory>
  时间: <timestamp>
================================================================

📁 文件: <N> 个 | 行数: <N>

── 项目分层 ──
  驱动层     <N> 个文件  ████████
  应用层     <N> 个文件  ██████
  工具层     <N> 个文件  ████
  未分类     <N> 个文件  ██████████

── 惯用写法画像 ──

✅ <category>
   (<frequency> 处匹配, <file_count> 个文件)
   主要模式: <by_pattern top-3>
   按层分布: <by_layer>

❌ <category>
   💡 <suggestion>

── ⚠️ 值得关注的缺失 ──
  ❌ <category>
     📌 <suggestion>

── 建议的沉淀命令 ──
  /mountainfish_integrate --type pattern --tier reference \
    "<dir>: <category> 使用 '<pattern>' 模式（<N> 处）"
```

### Step 4: 报告解读与建议

基于 JSON 数据，额外提供：
- **项目成熟度评估**：缺失项数量和严重程度
- **风格一致性**：同一类别内模式集中度（是否统一）
- **安全信号**：临界区保护、错误处理等关键缺失的严重性

## --compare 模式

对比多个 `.mountainfish-profile.md` 文件，输出四象限报告：

| 象限 | 含义 | 建议 |
|------|------|------|
| 🟢 共性模式 | 所有项目共有 | → 指南候选，建议升级到指南层 |
| 🔵 特有模式 | 仅 1 个项目 | → 参考层候选 |
| 🟡 分歧模式 | 部分有部分无 | → 需人工裁决，哪个项目的写法更好 |
| 🔴 共同缺失 | 所有项目都未使用 | → 值得关注的空白，考虑引入该约定 |

## 使用场景

### 场景 1: 新项目入职

```
/mountainfish_profiling ./firmware
```

快速了解项目的代码组织方式和惯用写法，不必逐文件阅读。

### 场景 2: 跨项目训练 skill

```
# 项目 A
/mountainfish_profiling ./project-a/src

# 项目 B
/mountainfish_profiling ./project-b/firmware

# 对比共识
/mountainfish_profiling --compare project-a/.mountainfish-profile.md project-b/.mountainfish-profile.md
```

将共性模式通过 `/mountainfish_integrate` 沉淀为指南，特有模式沉淀为参考。

### 场景 3: 代码评审前准备

```
/mountainfish_profiling ./src
```

评审前了解项目的风格基线，判断 PR 中的新代码是否符合项目惯例。

## 注意事项

- `.mountainfish-profile.md` 建议提交到 Git（类似 `.clang-format`），供团队参考
- 分析基于正则匹配，存在误报/漏报，建议人工审核后沉淀
- profiler 仅分析源代码结构，不连接编译数据库，不展开宏
- 小项目（<10 个 .c 文件）可能样本不足，建议降低置信度预期
- 仅支持 C/C++ 项目
- **[v2.1] 不要手动读源文件做分析**，必须通过 profiler.py 脚本处理
