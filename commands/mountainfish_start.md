# /mountainfish_start

开发会话开始时，分层加载 Mountainfish 记忆库。

## 使用方式

```
/mountainfish_start
```

## 执行流程（v2.1 优化：脚本预处理）

> **核心原则**：记忆解析由 Python 脚本完成，Claude 仅负责展示结果。
> 避免 Claude 逐文件读取 memory/*.md 做解析。

### Step 1: 调用 memory-loader 脚本

**必须使用 Bash 工具**调用脚本：

```bash
python ~/.claude/skills/mountainfish/scripts/memory-loader.py --mode start
```

脚本自动完成：
- 扫描 `memory/*.md`（跳过 index.md）
- 解析 D8 元数据（tier/type/tags）
- 提取铁律全文 + 指南摘要（标题+原则行）+ 参考索引
- 输出分层内容，token 极低（~150 for 5 条指南）

### Step 2: 展示加载结果

将脚本输出直接展示给用户，格式：

```
=== Mountainfish 记忆就绪 ===

📚 记忆库:
- 铁律: X 条（无条件生效）
- 指南: X 条（按需加载全文）
- 参考: X 条（标签匹配检索）

🔴 核心铁律：
1. [铁律 1 标题]
2. [铁律 2 标题]

🟡 指南摘要：
- [指南 1 标题]: [原则一句话]  `#标签`
- [指南 2 标题]: [原则一句话]  `#标签`

📅 最近更新：YYYY-MM-DD
✅ 记忆已就绪
```

### Step 3: 设置会话标记

在当前会话上下文中设置 `[Mountainfish: loaded]`，后续自动触发跳过全量加载，仅做按需检索。

## 注意事项

- 记忆库路径：`skills/mountainfish/memory/`
- 铁律 ≤5 条无条件注入，指南 ≤20 条注入摘要
- 后续讨论代码话题时，自动按需检索指南全文 + 参考条目
- **[v2.1] 不要手动读 memory 文件**，必须通过 memory-loader.py 脚本处理
