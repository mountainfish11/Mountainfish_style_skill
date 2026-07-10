#!/usr/bin/env python3
"""
Mountainfish memory-loader — 记忆库分层加载脚本
从 memory/*.md 文件中按层级提取内容，支持过滤，输出结构化数据。

用法:
  # start 模式：铁律全文 + 指南摘要 + 参考索引
  python memory-loader.py --mode start
  python memory-loader.py --mode start --source both    # 同时加载 memory + reference

  # inject 模式：按条件过滤条目
  python memory-loader.py --mode inject
  python memory-loader.py --mode inject --tier rule
  python memory-loader.py --mode inject --tier guideline --category patterns
  python memory-loader.py --mode inject --tags "C,嵌入式"

  # 指定来源
  python memory-loader.py --mode start --source memory     # 仅自己的经验（默认）
  python memory-loader.py --mode start --source reference  # 仅外部经验
  python memory-loader.py --mode start --source both       # 同时加载

  # 指定记忆库目录
  python memory-loader.py --mode start --memory-dir <path>

  # JSON 输出
  python memory-loader.py --mode start --json

返回:
  exit 0 = 成功
  exit 1 = 记忆库为空或不存在
  exit 2 = 参数错误
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


# ── 数据结构 ──────────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """解析后的记忆条目"""
    file: str               # 来源文件（不含路径）
    heading: str            # 条目标题
    tier: str               # rule | guideline | reference
    entry_type: str         # decision | convention | gotcha | pattern
    tags: List[str]         # 标签列表
    created: Optional[str]  # 创建日期
    last_used: Optional[str]  # 最后使用日期
    principle: str = ""     # 指南原则（一行摘要）
    body: str = ""          # 条目正文
    source: str = "memory"  # memory | reference — 经验来源


# ── 解析器 ────────────────────────────────────────────────────────

def parse_memory_file(filepath: str, source: str = "memory") -> List[MemoryEntry]:
    """解析单个记忆库文件，提取所有带 D8 元数据的条目"""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return entries

    current_section = None  # 当前 ## 段落（铁律/指南/参考）
    entry_lines: List[str] = []
    in_entry = False
    metadata: Dict[str, str] = {}

    for i, line in enumerate(lines):
        # 检测 ## 段落
        m_section = re.match(r'^##\s+(铁律|指南|参考)', line)
        if m_section:
            tier_map = {"铁律": "rule", "指南": "guideline", "参考": "reference"}
            current_section = tier_map.get(m_section.group(1))
            continue

        # 检测 ### 条目标题
        m_heading = re.match(r'^###\s+(.+)', line)
        if m_heading:
            # 保存上一个条目
            if in_entry and entry_lines:
                entry = _build_entry(
                    filepath, current_section or "reference",
                    entry_lines, metadata, source
                )
                if entry:
                    entries.append(entry)

            # 开始新条目
            entry_lines = [line]
            in_entry = True
            metadata = {}
            continue

        # 收集条目内容
        if in_entry:
            entry_lines.append(line)
            m_meta = re.match(
                r'<!--\s*(tier|type|tags|created|last-used|last-applied|expires)\s*:\s*(.+?)\s*-->',
                line
            )
            if m_meta:
                key = m_meta.group(1)
                value = m_meta.group(2)
                if key == "last-applied":
                    metadata["last-used"] = value
                else:
                    metadata[key] = value

    # 保存最后一个条目
    if in_entry and entry_lines:
        entry = _build_entry(
            filepath, current_section or "reference",
            entry_lines, metadata, source
        )
        if entry:
            entries.append(entry)

    return entries


def _build_entry(filepath: str, section_tier: str,
                 lines: List[str], metadata: Dict[str, str],
                 source: str = "memory") -> Optional[MemoryEntry]:
    """从解析的行和元数据构建 MemoryEntry"""
    heading = lines[0].strip().lstrip("#").strip()

    # 从 heading 末尾的 HTML 注释中提取 tier（可能被反引号包裹）
    m_tier_inline = re.search(r'`?<!--\s*tier:\s*(rule|guideline|reference)\s*-->`?', heading)
    if m_tier_inline:
        tier = m_tier_inline.group(1)
        heading = re.sub(r'\s*`?<!--.*?-->`?\s*$', '', heading).strip()
    else:
        tier = metadata.get("tier", section_tier)

    # 提取原则行（指南条目的一行摘要）
    principle = ""
    # 提取 body（排除注释行）
    body_lines = []
    for line in lines[1:]:
        if re.match(r'\s*<!--\s*(?:tier|type|tags|created|last-used|last-applied|expires)\s*:', line):
            continue
        body_lines.append(line)
        # 提取 **原则** 行
        m_principle = re.match(r'\*\*原则\*\*\s*[:：]\s*(.+)', line.strip())
        if m_principle:
            principle = m_principle.group(1).strip()

    body = "".join(body_lines).strip()

    # 解析 tags
    tags_str = metadata.get("tags", "")
    tags = [t.strip() for t in tags_str.replace("#", "").split(",") if t.strip()]

    # 跳过空条目（如"（待添加）"）
    if "待添加" in body and len(body) < 20:
        return None

    return MemoryEntry(
        file=os.path.basename(filepath),
        heading=heading,
        tier=tier,
        entry_type=metadata.get("type", ""),
        tags=tags,
        created=metadata.get("created"),
        last_used=metadata.get("last-used"),
        principle=principle,
        body=body,
        source=source,
    )


def load_all_entries(memory_dir: str, source: str = "memory") -> List[MemoryEntry]:
    """加载记忆库目录中的所有条目"""
    memory_dir = Path(memory_dir)
    if not memory_dir.exists():
        return []

    entries = []
    for md_file in sorted(memory_dir.glob("*.md")):
        if md_file.name == "index.md":
            continue
        entries.extend(parse_memory_file(str(md_file), source))
    return entries


def load_entries_from_both(memory_dir: str, reference_dir: str) -> List[MemoryEntry]:
    """同时加载 memory/ 和 reference/ 目录的条目"""
    entries = []
    entries.extend(load_all_entries(memory_dir, source="memory"))
    entries.extend(load_all_entries(reference_dir, source="reference"))
    return entries


# ── 过滤器 ────────────────────────────────────────────────────────

def filter_entries(entries: List[MemoryEntry],
                   tier: Optional[str] = None,
                   category: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> List[MemoryEntry]:
    """按条件过滤条目"""
    result = entries

    if tier:
        result = [e for e in result if e.tier == tier]

    if category:
        # category 映射到文件名前缀
        cat_file_map = {
            "code-style": "code-style.md",
            "patterns": "patterns.md",
            "anti-patterns": "anti-patterns.md",
            "tech-stack": "tech-stack.md",
            "project-structure": "project-structure.md",
            "conventions": "conventions.md",
        }
        target_file = cat_file_map.get(category, f"{category}.md")
        result = [e for e in result if e.file == target_file]

    if tags:
        filter_tags = {t.strip().lower() for t in tags}
        result = [
            e for e in result
            if filter_tags & {t.lower() for t in e.tags}
        ]

    return result


# ── 输出格式 ──────────────────────────────────────────────────────

def format_start_output(entries: List[MemoryEntry], memory_dir: str) -> str:
    """start 模式输出：铁律全文 + 指南摘要 + 参考索引"""
    rules = [e for e in entries if e.tier == "rule"]
    guidelines = [e for e in entries if e.tier == "guideline"]
    references = [e for e in entries if e.tier == "reference"]

    # 按来源统计
    mem_rules = [e for e in rules if e.source == "memory"]
    ref_guidelines = [e for e in guidelines if e.source == "reference"]
    mem_guidelines = [e for e in guidelines if e.source == "memory"]
    ref_references = [e for e in references if e.source == "reference"]
    mem_references = [e for e in references if e.source == "memory"]

    lines = []
    lines.append("=== Mountainfish 记忆加载 ===")
    lines.append("")

    # 铁律全文
    lines.append("## 铁律（以下规则无条件遵循）")
    if rules:
        for e in rules:
            lines.append(f"### {e.heading}")
            if e.body:
                lines.append(e.body)
            lines.append("")
    else:
        lines.append("（无铁律）")
        lines.append("")

    # 指南摘要（自己的经验）
    lines.append("## 指南摘要（自己的经验）")
    if mem_guidelines:
        for e in mem_guidelines:
            tag_str = " ".join(f"`#{t}`" for t in e.tags) if e.tags else ""
            principle_str = e.principle if e.principle else "(无原则描述)"
            lines.append(f"- **{e.heading}**: {principle_str}  {tag_str}")
    else:
        lines.append("（无指南）")
    lines.append("")

    # 指南摘要（外部经验）
    if ref_guidelines:
        lines.append("## 指南摘要（外部经验 [外部]）")
        for e in ref_guidelines:
            tag_str = " ".join(f"`#{t}`" for t in e.tags) if e.tags else ""
            principle_str = e.principle if e.principle else "(无原则描述)"
            lines.append(f"- [外部] **{e.heading}**: {principle_str}  {tag_str}")
        lines.append("")

    # 参考索引（自己的经验）
    lines.append("## 参考索引（自己的经验）")
    if mem_references:
        for e in mem_references:
            tag_str = " ".join(f"`#{t}`" for t in e.tags) if e.tags else ""
            lines.append(f"- {e.heading}  {tag_str}")
    else:
        lines.append("（无参考）")
    lines.append("")

    # 参考索引（外部经验）
    if ref_references:
        lines.append("## 参考索引（外部经验 [外部]）")
        for e in ref_references:
            tag_str = " ".join(f"`#{t}`" for t in e.tags) if e.tags else ""
            lines.append(f"- [外部] {e.heading}  {tag_str}")
        lines.append("")

    # 统计
    total_mem = len(mem_rules) + len(mem_guidelines) + len(mem_references)
    total_ref = len(ref_guidelines) + len(ref_references)
    lines.append(f"token 估算: 铁律 ~{len(rules) * 100} | 指南摘要 ~{len(guidelines) * 30} | 参考索引 ~{len(references) * 15}")
    lines.append(f"来源: 自己的经验 {total_mem} 条 | 外部经验 {total_ref} 条")

    return "\n".join(lines)


def format_inject_output(entries: List[MemoryEntry]) -> str:
    """inject 模式输出：过滤后的条目"""
    rules = [e for e in entries if e.tier == "rule"]
    guidelines = [e for e in entries if e.tier == "guideline"]
    references = [e for e in entries if e.tier == "reference"]

    lines = []
    lines.append("=== Mountainfish Inject 完成 ===")
    lines.append("")

    if rules:
        lines.append(f"🔴 铁律（{len(rules)} 条，无条件遵循）：")
        for e in rules:
            src_tag = " [外部]" if e.source == "reference" else ""
            lines.append(f"-{src_tag} {e.heading}")
            if e.body:
                # 截取前 200 字符
                body_preview = e.body[:200]
                if len(e.body) > 200:
                    body_preview += "..."
                lines.append(f"  {body_preview}")
        lines.append("")

    if guidelines:
        lines.append(f"🟡 指南（{len(guidelines)} 条）：")
        for e in guidelines:
            tag_str = " ".join(f"`#{t}`" for t in e.tags) if e.tags else ""
            principle_str = e.principle if e.principle else "(无原则描述)"
            src_tag = " [外部]" if e.source == "reference" else ""
            lines.append(f"-{src_tag} **{e.heading}**: {principle_str}  {tag_str}")
        lines.append("")

    if references:
        lines.append(f"🟢 参考（{len(references)} 条）：")
        for e in references:
            tag_str = " ".join(f"`#{t}`" for t in e.tags) if e.tags else ""
            src_tag = " [外部]" if e.source == "reference" else ""
            lines.append(f"-{src_tag} {e.heading}  {tag_str}")
        lines.append("")

    if not entries:
        lines.append("（无匹配条目）")

    return "\n".join(lines)


def to_json(entries: List[MemoryEntry], mode: str, memory_dir: str) -> dict:
    """JSON 输出"""
    if mode == "start":
        rules = [e for e in entries if e.tier == "rule"]
        guidelines = [e for e in entries if e.tier == "guideline"]
        references = [e for e in entries if e.tier == "reference"]
        mem_entries = [e for e in entries if e.source == "memory"]
        ref_entries = [e for e in entries if e.source == "reference"]
        return {
            "mode": "start",
            "memory_dir": memory_dir,
            "stats": {
                "rules": len(rules),
                "guidelines": len(guidelines),
                "references": len(references),
                "total": len(entries),
                "from_memory": len(mem_entries),
                "from_reference": len(ref_entries),
            },
            "rules": [asdict(e) for e in rules],
            "guidelines": [
                {"heading": e.heading, "principle": e.principle, "tags": e.tags, "source": e.source}
                for e in guidelines
            ],
            "references": [
                {"heading": e.heading, "tags": e.tags, "source": e.source}
                for e in references
            ],
        }
    else:
        return {
            "mode": "inject",
            "count": len(entries),
            "entries": [asdict(e) for e in entries],
        }


# ── CLI ───────────────────────────────────────────────────────────

def get_default_memory_dir() -> str:
    """获取默认记忆库目录"""
    script_dir = Path(__file__).resolve().parent
    memory_dir = script_dir.parent / "memory"
    if memory_dir.exists():
        return str(memory_dir)
    return str(memory_dir)


def get_reference_dir() -> str:
    """获取外部经验目录"""
    script_dir = Path(__file__).resolve().parent
    ref_dir = script_dir.parent / "reference"
    return str(ref_dir)


def _setup_encoding():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    _setup_encoding()

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # 解析参数
    mode = "start"
    json_output = "--json" in sys.argv
    memory_dir = get_default_memory_dir()
    source = "memory"
    tier = None
    category = None
    tags = None

    for i, arg in enumerate(sys.argv):
        if arg == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1]
        elif arg == "--memory-dir" and i + 1 < len(sys.argv):
            memory_dir = sys.argv[i + 1]
        elif arg == "--source" and i + 1 < len(sys.argv):
            source = sys.argv[i + 1]
        elif arg == "--tier" and i + 1 < len(sys.argv):
            tier = sys.argv[i + 1]
        elif arg == "--category" and i + 1 < len(sys.argv):
            category = sys.argv[i + 1]
        elif arg == "--tags" and i + 1 < len(sys.argv):
            tags = [t.strip() for t in sys.argv[i + 1].split(",")]

    if mode not in ("start", "inject"):
        print(f"[ERROR] 未知模式: {mode}，支持 start / inject", file=sys.stderr)
        sys.exit(2)

    if source not in ("memory", "reference", "both"):
        print(f"[ERROR] 未知 --source: {source}，支持 memory / reference / both", file=sys.stderr)
        sys.exit(2)

    # 加载条目
    if source == "both":
        reference_dir = get_reference_dir()
        if mode == "start":
            entries = load_entries_from_both(memory_dir, reference_dir)
        else:
            # inject 模式 + both: 从两个目录加载然后过滤
            entries = load_entries_from_both(memory_dir, reference_dir)
            entries = filter_entries(entries, tier=tier, category=category, tags=tags)
            # 已过滤，跳过后续过滤
            tier = None
            category = None
            tags = None
    elif source == "reference":
        reference_dir = get_reference_dir()
        entries = load_all_entries(reference_dir, source="reference")
    else:
        entries = load_all_entries(memory_dir, source="memory")

    if not entries:
        print(f"[WARN] 记忆库为空: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    # inject 模式：过滤
    if mode == "inject":
        entries = filter_entries(entries, tier=tier, category=category, tags=tags)

    # 输出
    if json_output:
        data = to_json(entries, mode, memory_dir)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif mode == "start":
        print(format_start_output(entries, memory_dir))
    else:
        print(format_inject_output(entries))

    sys.exit(0)


if __name__ == "__main__":
    main()
