# /mountainfish_integrate

将经验文档整合到 Mountainfish 记忆库。

## 使用方式

```
# 基础用法
/mountainfish_integrate                  # 分析当前对话，提取代码风格经验
/mountainfish_integrate ./my-notes       # 扫描指定目录的 .md 文件
/mountainfish_integrate ./code-style.md  # 指定具体文件

# 代码风格分析（新功能）
/mountainfish_integrate --analyze ./src           # 分析源码目录的代码风格
/mountainfish_integrate --analyze ./src --json    # 输出 JSON 格式报告
/mountainfish_integrate --profile                 # 生成 mf_style.yaml 配置
/mountainfish_integrate --apply                   # 生成 .clang-format 配置
```

**自然语言触发**（自动调用此命令）：
- "沉淀到mountainfish"
- "记录代码风格"
- "总结经验"
- "记录刚才的分析"
- "分析代码风格"
- "生成风格配置"

## 执行流程

### Step 1: 确定输入源和模式

检查用户是否提供了参数 `$ARGUMENTS`：

**代码风格分析模式**（新功能）：
- `--analyze <目录>`：运行代码风格分析器
  ```bash
  python ~/.claude/skills/mountainfish/scripts/analyzer.py <目录>
  ```
- `--profile`：生成 mf_style.yaml 配置文件
  ```bash
  python ~/.claude/skills/mountainfish/scripts/profile_generator.py report.json
  ```
- `--apply`：生成 .clang-format 配置文件
  ```bash
  python ~/.claude/skills/mountainfish/scripts/profile_generator.py report.json --clang-format
  ```

**传统模式**：
- **有参数**：检查是目录还是文件
  - 目录：扫描目录下所有 `.md` 文件
  - 文件：直接读取该文件
- **无参数**：**智能模式** - 分析当前对话内容，提取代码风格相关经验

### Step 2: 读取并分析内容

**模式 A：文件输入**
对于每个找到的 `.md` 文件，读取并分析内容。

**模式 B：对话提取（无参数时）**
分析当前对话内容，识别以下类型的讨论：
- 代码风格讨论（命名规范、格式偏好、注释风格）
- 设计模式讨论（架构决策、模式选择）
- 问题解决方案（踩坑记录、调试经验）
- 技术栈偏好（库/框架选择、工具使用）
- 项目结构讨论（目录组织、模块划分）

**内容分类判断**：
- **代码风格**：命名规范、格式、注释 → `code-style.md`
- **设计模式**：架构、模式、最佳实践 → `patterns.md`
- **避坑指南**：反模式、错误、踩坑 → `anti-patterns.md`
- **技术栈**：库、框架、工具偏好 → `tech-stack.md`
- **项目结构**：目录、文件组织 → `project-structure.md`
- **其他约定**：Git、测试、文档 → `conventions.md`

### Step 3: 提取关键经验

从每个文件中提取：
- 具体的规则和约定
- 代码示例
- 原因和背景（为什么这样做）

### Step 4: 写入记忆库

将提取的经验追加到对应的记忆库文件中：
- 使用清晰的标题和分隔符
- 保留原始的代码示例
- 添加来源标记

### Step 5: 更新索引

更新 `~/.claude/skills/mountainfish/memory/index.md`：
- 更新各分类的条目数量
- 添加最近更新记录

### Step 6: 输出报告

输出整合结果：

```
=== Mountainfish Integrate 完成 ===

📄 扫描文件：X 个
📝 提取经验：Y 条

按分类：
- 代码风格：+N 条
- 设计模式：+N 条
- 避坑指南：+N 条
- 技术栈：+N 条
- 项目结构：+N 条
- 其他约定：+N 条

✅ 已更新记忆库
```
