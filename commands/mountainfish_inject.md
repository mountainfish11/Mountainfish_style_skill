# /mountainfish_inject

将积累的经验注入到当前项目开发中。

## 模式说明

| 模式 | 触发方式 | 用途 |
|------|----------|------|
| **自动模式** | 讨论代码话题时自动触发 | 日常开发，按需检索注入 |
| **手动模式** | 显式调用 `/mountainfish_inject` | 精确控制注入内容和范围 |

> 大多数情况下，自动模式已足够。手动模式用于需要精确控制的场景。

## 手动模式使用方式

```
# 基础用法（按分类）
/mountainfish_inject                 # 注入全部相关经验（不超过 3000 token）
/mountainfish_inject code-style      # 只注入代码风格
/mountainfish_inject patterns        # 只注入设计模式
/mountainfish_inject anti-patterns   # 只注入避坑指南
/mountainfish_inject tech-stack      # 只注入技术栈
/mountainfish_inject structure       # 只注入项目结构
/mountainfish_inject conventions     # 只注入其他约定

# 按层级注入（v2.0 新增）
/mountainfish_inject --tier rule        # 只注入铁律
/mountainfish_inject --tier guideline   # 只注入指南
/mountainfish_inject --tier reference   # 只注入参考

# 组合筛选
/mountainfish_inject --tier rule --category patterns   # 铁律中的设计模式
/mountainfish_inject --tier guideline code-style        # 指南中的代码风格

# 指定来源（v2.2 新增）
/mountainfish_inject --source reference                 # 仅注入外部经验
/mountainfish_inject --source both                      # 同时注入自己的 + 外部经验
```

## 手动模式执行流程（v2.1 优化：脚本预处理）

> **核心原则**：记忆解析和过滤由 Python 脚本完成，Claude 仅负责展示结果。

### Step 1: 确定注入范围

根据用户参数构建脚本参数：

| 用户输入 | 脚本参数 |
|----------|----------|
| 无参数 | `--mode inject --source both`（全部） |
| `code-style` | `--mode inject --source both --category code-style` |
| `--tier rule` | `--mode inject --tier rule` |
| `--source reference` | `--mode inject --source reference` |
| `--tier guideline code-style` | `--mode inject --tier guideline --category code-style` |

### Step 2: 调用 memory-loader 脚本

**必须使用 Bash 工具**调用脚本：

```bash
# 全部注入（自己的 + 外部）
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --source both

# 仅外部经验
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --source reference

# 按层级过滤
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --tier rule

# 按分类过滤
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --category patterns

# 组合过滤
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --tier guideline --category code-style

# 按标签过滤
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --tags "C,嵌入式"

# JSON 输出（用于程序化处理）
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode inject --tier rule --json
```

### Step 3: 展示注入结果

将脚本输出直接展示给用户：

```
=== Mountainfish Inject 完成 ===

🔴 铁律（X 条，无条件遵循）：
- [规则 1]
- [规则 2]

🟡 指南（X 条）：
- [指南 1 标题]: [原则]  `#标签`

🟢 参考（X 条）：
- [参考 1 标题]: [场景]  `#标签`

token 用量: ~XXXX / 3000
后续代码生成将遵循以上经验
```

### Step 4: 确认注入

在后续的代码生成中，Claude 将自动遵循注入的经验：
- 铁律无条件执行
- 指南作为默认选择
- 参考按需采纳

## 自动模式说明

当 SKILL.md 的触发条件匹配时（用户讨论代码相关话题），skill 会自动：
1. 检查是否已完成 `start` 全量加载
2. 如未加载 → 先执行 `/mountainfish_start`
3. 按标签/关键词调用 memory-loader.py 检索指南全文 + 参考条目
4. Top-K（≤5 条），token 上限 1500
5. 简提示：`💡 Mountainfish: 铁律 X 条 | 指南 X 条 | 参考 X 条`

## 注意事项

- 注入的经验仅在当前会话有效
- 不会修改实际代码，仅作为生成参考
- 如需永久更新经验，使用 `/mountainfish_integrate`
- 手动注入不会覆盖已加载的铁律（铁律始终生效）
- **[v2.1] 不要手动读 memory 文件**，必须通过 memory-loader.py 脚本处理
