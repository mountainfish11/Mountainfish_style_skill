# /mountainfish_integrate

将经验文档整合到 Mountainfish 记忆库（v2.0 三级分层 + 分类标签）。

## 使用方式

```
# 基础用法
/mountainfish_integrate                  # 分析当前对话，提取代码风格经验
/mountainfish_integrate ./my-notes       # 扫描指定目录的 .md 文件
/mountainfish_integrate ./code-style.md  # 指定具体文件
/mountainfish_integrate ./.mountainfish-profile.md  # 消费 profiler 输出的画像文件

# 代码风格分析
/mountainfish_integrate --analyze ./src           # 分析源码目录的代码风格
/mountainfish_integrate --analyze ./src --json    # 输出 JSON 格式报告
/mountainfish_integrate --profile                 # 生成 mf_style.yaml 配置
/mountainfish_integrate --apply                   # 生成 .clang-format 配置

# 精确沉淀（v2.0 新增）
/mountainfish_integrate --type gotcha --tier reference \
  "GD32F470 USART1 波特率配置需要额外分频"

/mountainfish_integrate --type convention --tier guideline \
  "所有外设驱动统一用 BSP 层封装"

# 记忆健康检查（v2.0 新增）
/mountainfish_integrate --health                  # 快速健康检查
/mountainfish_integrate --health --full            # 全面审计
```

**自然语言触发**（自动调用此命令）：
- "沉淀到mountainfish"
- "记录代码风格"
- "总结经验"
- "记录刚才的分析"
- "检查记忆健康"

## 执行流程

### Step 0: 确定模式

- `--health` → 跳转到 Step H（健康检查）
- `--analyze` → 跳转到 Step A（代码分析）
- `--type ...` → 跳转到 Step P（精确沉淀）
- 传入 `.mountainfish-profile.md` → 跳转到 Step F（消费画像文件）
- 其他 → 进入 Step 1（传统模式）

---

### Step 1-6: 传统模式（文件/对话提取）

同 v1.x 流程，升级点：

#### Step 3 增强：经验分类

提取经验时，AI 自动建议：

| 类型 | 含义 | 示例 |
|------|------|------|
| `decision` | 设计决策（为什么选 A 不选 B） | "用 FreeRTOS 而非裸机轮询" |
| `convention` | 约定（团队统一做法） | "所有外设驱动统一用 BSP 层" |
| `gotcha` | 坑（非显然的行为/问题） | "GD32F470 USART1 波特率需额外分频" |
| `pattern` | 可复用模式（验证过的解法） | "参数传递优于全局变量" |

同时建议层级：

| 层级 | 条件 |
|------|------|
| `rule`（铁律） | 绝对不能违反，每个项目都适用 |
| `guideline`（指南） | 强烈建议，大多数场景适用 |
| `reference`（参考） | 特定场景下的经验，按需检索 |

#### Step 4 增强：反污染自检

写入前必须通过：

- [ ] 这条经验换个项目还成立吗？不成立 → 降级为参考或留在对话记录
- [ ] 是"可执行规范"还是"一次性事实"？纯事实记录 → 不沉淀
- [ ] 已有记忆是否已覆盖？覆盖 → 更新已有条目，不新建
- [ ] 铁律 ≤5 条检查：如建议升级为铁律但已满 → 提醒用户降级最不常用的铁律

#### Step 5 增强：写入格式

按 D8 规范（三级条目模板）写入，包含 HTML 注释元数据：

```
<!-- tier: rule|guideline|reference -->
<!-- type: decision|convention|gotcha|pattern -->
<!-- tags: C, 嵌入式, FreeRTOS -->
<!-- created: YYYY-MM-DD -->
<!-- last-applied|last-used: YYYY-MM-DD -->
<!-- expires: YYYY-MM-DD|never -->
```

---

### Step P: 精确沉淀模式

```
/mountainfish_integrate --type <type> --tier <tier> "<一句话描述>"
```

1. 解析参数：类型 + 层级 + 描述
2. AI 根据描述展开：规则/原则/场景 + 代码示例（如果可用）
3. 反污染自检（同上）
4. 用户确认 → 写入对应记忆库文件的对应层级段落
5. 更新 index.md 分层统计

---

### Step A: 代码分析模式

同 v1.x，使用 `scripts/analyzer.py` 和 `scripts/profile_generator.py`。

---

### Step F: 消费画像文件（v2.1 新增）

当传入 `/mountainfish_profiling` 生成的 `.mountainfish-profile.md` 文件时：

1. 解析文件中的 D8 格式条目（每个 ✅ 检测到的模式即为一条经验）
2. 提取嵌入式 JSON 块中的元数据（频率、分布、按层分解）
3. 反污染自检（同 Step 4）
4. 逐条确认 → 写入记忆库对应的分类文件和层级

画像文件中的 ❌ 缺失项不会沉淀为经验，但可能触发建议：
- 关键缺失项（如"未检测到任何临界区保护"）→ 询问用户是否需要建立规范

---

### Step H: 记忆健康检查（v2.0 新增）

```
/mountainfish_integrate --health          # 快速模式：矛盾 + 过期 + 铁律膨胀
/mountainfish_integrate --health --full   # 全面审计：全部 5 维
```

**检查维度：**

| 维度 | 检测内容 | 快速 | 全面 |
|------|----------|------|------|
| 矛盾/冲突 | 同一主题不同条目说法矛盾 | ✅ | ✅ |
| 过期内容 | `last-used` 超过 90 天且未标记永久 | ✅ | ✅ |
| 铁律膨胀 | 铁律超过 5 条 | ✅ | ✅ |
| 孤立条目 | 参考条目零引用 + 无索引 | — | ✅ |
| 重复内容 | 两个条目覆盖同一主题无互相引用 | — | ✅ |

**输出格式：**

```
=== Mountainfish 健康报告 — 2026-07-03 ===

📊 概览:
- 矛盾: 0 | 过期: 2 | 铁律膨胀: 否 | 孤立: 1 | 重复: 0
- 总体: 🟢 良好 / 🟡 需关注 / 🔴 需处理

⚠️ 过期内容:
1. patterns.md: "参数传递优于全局变量" — 上次应用 2026-04-01（93 天前）

📌 建议操作:
1. 检查 patterns.md "参数传递..." 是否仍适用，更新 last-applied 或归档
```

---

## 输出报告

```
=== Mountainfish Integrate 完成 ===

📄 扫描文件：X 个
📝 提取经验：Y 条

按层级：
- 铁律：+N 条（总 N/5）
- 指南：+N 条（总 N/20）
- 参考：+N 条

按分类：
- decision: N 条
- convention: N 条
- gotcha: N 条
- pattern: N 条

✅ 已更新记忆库
```
