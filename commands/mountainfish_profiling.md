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

## 执行流程

### Phase 1: 文件分类

按路径命名和代码特征，将源文件归类到项目的隐含分层：

| 层级 | 识别特征 |
|------|----------|
| 驱动层 | `drv_*` 前缀、包含 vendor HAL 头（stm32/gd32/esp/nrf）、直接操作寄存器 |
| 应用层 | `app_*` / `task_*` 前缀、包含 FreeRTOS 头、调用 xTaskCreate |
| 工具层 | `util_*` / `ringbuf_*` / `list_*` 前缀、无 vendor 依赖 |
| 未分类 | 无法匹配以上任何规则 |

每种分类附置信度（高/中/低），低置信度时该文件不参与分层统计。

### Phase 2: 惯用写法检测

按层检测 8 类惯用写法：

| 类别 | 检测内容 |
|------|---------|
| typedef struct 组织 | 前置 typedef 匿名 struct / 命名 tag 分离 / 合写 / 裸 struct |
| do-while(0) 宏 | 安全多语句宏 / 裸多语句宏 / GCC 语句表达式 |
| callback 注册 | 函数指针 struct 注册表 / `__weak` 弱符号 / 运行时注册 |
| ISR / 临界区 | FreeRTOS 临界区 / CMSIS 关中断 / BASEPRI 掩码 / volatile 标志位 |
| 容器/工具模式 | switch-case 状态机 / 函数指针跳转表 / ring buffer / 侵入式链表 |
| 错误传递 | return 错误码 / goto fail / assert / 全局 errno |
| 头文件保护 | `#pragma once` / `#ifndef` 经典守卫 |
| volatile 使用 | ISR 共享变量 / MMIO 指针 / 并发同步 |

每种模式附带：
- **频率和分布**（出现次数、涉及文件数）
- **按层分解**（驱动层用 vs 应用层用，语义不同）
- **主流模式标记**（最多 3 种主要模式）

### Phase 3: 缺失清单

对照内置的常见 C 嵌入式惯用写法清单，标注该项目未使用的模式。缺失项往往比存在项更能揭示项目成熟度——例如："该项目没有任何临界区保护"是值得关注的安全信号。

### 输出

- **终端**：分层摘要 → 惯用写法画像（✅检测到 / ❌未检测到） → 缺失清单 → 建议的 integrate 命令
- **文件**：`.mountainfish-profile.md`（D8 格式条目 + 元数据 + 结构化 JSON），可直接被 `/mountainfish_integrate <file>` 消费

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

## 输出报告示例

```
================================================================
  Mountainfish Profiling Report
  项目: ./firmware
  时间: 2026-07-03
================================================================

📁 文件: 42 个 | 行数: 8230

── 项目分层 ──
  驱动层     12 个文件  ████████████
  应用层      8 个文件  ████████
  工具层      3 个文件  ███
  未分类     19 个文件  ███████████████████

── 惯用写法画像 ──

✅ typedef struct 组织
   (28 处匹配, 15 个文件, 分布: {'前置 typedef + 匿名 struct': 22, ...})
   按层: {'driver': 18, 'app': 8, 'util': 2}

❌ do-while(0) 宏包装
   💡 多语句宏应使用 do-while(0) 包裹，保证在任何控制流上下文中安全

...

── ⚠️ 值得关注的缺失 ──
  ❌ ISR / 临界区写法
     📌 该项目未检测到任何临界区保护，ISR 共享变量可能存在竞态条件

── 建议的沉淀命令 ──
  /mountainfish_integrate --type pattern --tier reference \
    "./firmware: typedef struct 组织 使用 '前置 typedef + 匿名 struct' 模式（28 处）"
```

## 注意事项

- `.mountainfish-profile.md` 建议提交到 Git（类似 `.clang-format`），供团队参考
- 分析基于正则匹配，存在误报/漏报，建议人工审核后沉淀
- profiler 仅分析源代码结构，不连接编译数据库，不展开宏
- 小项目（<10 个 .c 文件）可能样本不足，建议降低置信度预期
- 仅支持 C/C++ 项目
