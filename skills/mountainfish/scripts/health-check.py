#!/usr/bin/env python3
"""
Mountainfish health-check — 记忆健康审计脚本
检查记忆库的 5 维健康指标：矛盾、过期、孤立、重复、铁律膨胀。

用法:
  python health-check.py                       # 快速检查（矛盾+过期+铁律膨胀）
  python health-check.py --full                # 全面审计（全部 5 维）
  python health-check.py --json                # JSON 输出
  python health-check.py --update-index        # 审计后刷新 index.md 统计
  python health-check.py --memory-dir <path>   # 指定记忆库目录
  python health-check.py --full --json         # 全面审计 + JSON

返回:
  exit 0 = 健康（无需关注）
  exit 1 = 需关注（有警告项）
  exit 2 = 需处理（有严重问题）
  exit 3 = 运行错误
"""

import json
import re
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


# ── 常量 ──────────────────────────────────────────────────────────

MAX_RULES = 5           # 铁律上限
MAX_GUIDELINES = 20     # 指南上限
EXPIRY_DAYS = 90        # 过期阈值（天）
SIMILARITY_THRESHOLD = 0.4  # 重复/矛盾检测的相似度阈值


# ── 数据结构 ──────────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """解析后的记忆条目"""
    file: str               # 来源文件（相对路径）
    heading: str            # 条目标题（### 行）
    tier: str               # rule | guideline | reference
    entry_type: str         # decision | convention | gotcha | pattern
    tags: List[str]         # 标签列表
    created: Optional[str]  # 创建日期 YYYY-MM-DD
    last_used: Optional[str]  # 最后使用/应用日期
    expires: Optional[str]  # 过期日期或 "never"
    body: str               # 条目正文（不含元数据注释行）
    line_start: int         # 在源文件中的起始行号

    @property
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires == "never" or not self.expires:
            return False
        if not self.last_used:
            return True  # 从未被使用
        try:
            last_date = datetime.strptime(self.last_used, "%Y-%m-%d")
            threshold = datetime.now() - timedelta(days=EXPIRY_DAYS)
            return last_date < threshold
        except ValueError:
            return False

    @property
    def age_days(self) -> Optional[int]:
        """距离上次使用的天数"""
        if not self.last_used:
            return None
        try:
            last_date = datetime.strptime(self.last_used, "%Y-%m-%d")
            return (datetime.now() - last_date).days
        except ValueError:
            return None


# ── 解析器 ────────────────────────────────────────────────────────

def parse_memory_file(filepath: str) -> List[MemoryEntry]:
    """解析单个记忆库文件，提取所有带 D8 元数据的条目"""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return entries

    current_section = None  # 当前所在的 ## 段落（铁律/指南/参考）
    entry_lines: List[str] = []
    entry_start = 0
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
                    entry_lines, entry_start, metadata
                )
                if entry:
                    entries.append(entry)

            # 开始新条目
            entry_lines = [line]
            entry_start = i + 1
            in_entry = True
            metadata = {}
            continue

        # 检测 HTML 注释元数据
        if in_entry:
            entry_lines.append(line)
            m_meta = re.match(r'<!--\s*(tier|type|tags|created|last-used|last-applied|expires)\s*:\s*(.+?)\s*-->', line)
            if m_meta:
                key = m_meta.group(1)
                value = m_meta.group(2)
                # last-applied 和 last-used 统一为 last_used
                if key == "last-applied":
                    metadata["last-used"] = value
                else:
                    metadata[key] = value

    # 保存最后一个条目
    if in_entry and entry_lines:
        entry = _build_entry(
            filepath, current_section or "reference",
            entry_lines, entry_start, metadata
        )
        if entry:
            entries.append(entry)

    return entries


def _build_entry(filepath: str, tier: str, lines: List[str],
                 start: int, metadata: Dict[str, str]) -> Optional[MemoryEntry]:
    """从解析的行和元数据构建 MemoryEntry"""
    heading = lines[0].strip().lstrip("#").strip()

    # 尝试从 heading 末尾的 HTML 注释中提取 tier
    m_tier_inline = re.search(r'<!--\s*tier:\s*(rule|guideline|reference)\s*-->', heading)
    if m_tier_inline:
        tier = m_tier_inline.group(1)
        heading = re.sub(r'\s*<!--.*?-->\s*$', '', heading).strip()

    # 提取 body（排除注释行）
    body_lines = []
    for line in lines[1:]:
        if re.match(r'\s*<!--\s*(?:tier|type|tags|created|last-used|last-applied|expires)\s*:', line):
            continue
        body_lines.append(line)
    body = "".join(body_lines).strip()

    # 解析 tags
    tags_str = metadata.get("tags", "")
    tags = [t.strip() for t in tags_str.replace("#", "").split(",") if t.strip()]

    return MemoryEntry(
        file=os.path.basename(filepath),
        heading=heading,
        tier=metadata.get("tier", tier),
        entry_type=metadata.get("type", ""),
        tags=tags,
        created=metadata.get("created"),
        last_used=metadata.get("last-used"),
        expires=metadata.get("expires"),
        body=body,
        line_start=start,
    )


def load_all_entries(memory_dir: str) -> List[MemoryEntry]:
    """加载记忆库目录中的所有条目"""
    memory_dir = Path(memory_dir)
    if not memory_dir.exists():
        return []

    entries = []
    for md_file in sorted(memory_dir.glob("*.md")):
        if md_file.name == "index.md":
            continue
        entries.extend(parse_memory_file(str(md_file)))
    return entries


# ── 审计器 ────────────────────────────────────────────────────────

class HealthChecker:
    """记忆健康审计器"""

    def __init__(self, memory_dir: str):
        self.memory_dir = Path(memory_dir)
        self.entries = load_all_entries(memory_dir)
        self.issues: List[dict] = []
        self.stats: Dict = {}

    # ── 维度 1: 矛盾/冲突检测 ─────────────────────────────────────

    def check_conflicts(self) -> List[dict]:
        """检测同一主题不同条目是否存在矛盾表述（关键词重叠 + 对立词检测）"""
        conflicts = []

        # 对立词模式（英文 + 中文）
        opposition_patterns = [
            (r'\b(?:必须|必须用|必须使用|强烈建议|一定要)\b',
             r'\b(?:避免|禁止|不要|不应|不该|勿|不能)\b'),
            (r'\b(?:always|must|required|mandatory)\b',
             r'\b(?:avoid|never|don\'t|should not|must not|prohibit)\b'),
            (r'\b(?:推荐|建议|最好|优先)\b',
             r'\b(?:不推荐|不建议|避免|弃用|deprecated)\b'),
        ]

        # 计算条目间的关键词重叠
        for i in range(len(self.entries)):
            for j in range(i + 1, len(self.entries)):
                e1, e2 = self.entries[i], self.entries[j]

                # 标签交集
                tags1 = set(e1.tags)
                tags2 = set(e2.tags)
                tag_overlap = tags1 & tags2

                # 关键词重叠（从标题提取）
                words1 = set(re.findall(r'\w+', e1.heading.lower()))
                words2 = set(re.findall(r'\w+', e2.heading.lower()))
                word_overlap = words1 & words2

                # 需要标签交集 + 关键词重叠才继续
                if not tag_overlap or len(word_overlap) < 2:
                    continue

                # 检测对立词
                for pos_pattern, neg_pattern in opposition_patterns:
                    pos_in_e1 = bool(re.search(pos_pattern, e1.body, re.IGNORECASE))
                    neg_in_e2 = bool(re.search(neg_pattern, e2.body, re.IGNORECASE))

                    # 反向检查
                    neg_in_e1 = bool(re.search(neg_pattern, e1.body, re.IGNORECASE))
                    pos_in_e2 = bool(re.search(pos_pattern, e2.body, re.IGNORECASE))

                    if (pos_in_e1 and neg_in_e2) or (neg_in_e1 and pos_in_e2):
                        conflicts.append({
                            "dimension": "矛盾/冲突",
                            "severity": "warning",
                            "entry_a": f"{e1.file}:{e1.heading}",
                            "entry_b": f"{e2.file}:{e2.heading}",
                            "detail": f"两个条目在标签重叠（{', '.join(sorted(tag_overlap))})"
                                       f"的情况下使用了可能矛盾的表述",
                            "suggestion": f"检查 '{e1.heading}' 和 '{e2.heading}' 是否矛盾，"
                                         f"如不矛盾则添加互相引用",
                        })
                        break  # 每对只报一次

        return conflicts

    # ── 维度 2: 过期内容检测 ─────────────────────────────────────

    def check_expired(self) -> List[dict]:
        """检测 last-used 超过 90 天且未标记永久保留的条目"""
        expired = []

        for entry in self.entries:
            if entry.tier == "rule" and entry.expires == "never":
                continue  # 铁律标记永久的不检查

            age = entry.age_days
            if age is not None and age > EXPIRY_DAYS:
                if entry.expires != "never":
                    expired.append({
                        "dimension": "过期内容",
                        "severity": "warning",
                        "entry": f"{entry.file}:{entry.heading}",
                        "tier": entry.tier,
                        "last_used": entry.last_used,
                        "age_days": age,
                        "detail": f"上次使用 {entry.last_used}（{age} 天前），超过 {EXPIRY_DAYS} 天阈值",
                        "suggestion": f"检查 '{entry.heading}' 是否仍适用，"
                                     f"更新 last-used 或标记 expires: never，或考虑归档",
                    })

        return expired

    # ── 维度 3: 孤立条目检测（仅 full 模式）───────────────────────

    def check_orphans(self) -> List[dict]:
        """检测参考条目是否被其他条目引用"""
        orphans = []

        # 构建所有条目正文的全文搜索索引
        ref_entries = [e for e in self.entries if e.tier == "reference"]
        if not ref_entries:
            return []

        all_text = " ".join(e.body + " " + e.heading for e in self.entries)

        for entry in ref_entries:
            # 检查条目标题是否在其他条目正文中被提及
            heading_keywords = re.findall(r'\w+', entry.heading)
            if len(heading_keywords) < 3:
                continue

            # 取标题中最具特征的关键词（长度 > 2 的词）
            key_terms = [w for w in heading_keywords if len(w) > 2]
            if not key_terms:
                continue

            # 检查在其他条目的正文中是否出现
            referenced = False
            for other in self.entries:
                if other is entry:
                    continue
                # 标题中出现至少 2 个关键词算引用
                matches = sum(1 for term in key_terms if term.lower() in other.body.lower())
                if matches >= 2:
                    referenced = True
                    break

            if not referenced:
                orphans.append({
                    "dimension": "孤立条目",
                    "severity": "info",
                    "entry": f"{entry.file}:{entry.heading}",
                    "tier": entry.tier,
                    "detail": "该参考条目未被任何其他条目引用",
                    "suggestion": f"考虑将 '{entry.heading}' 合并到相关条目，或添加交叉引用",
                })

        return orphans

    # ── 维度 4: 重复内容检测（仅 full 模式）───────────────────────

    def check_duplicates(self) -> List[dict]:
        """检测两个条目覆盖同一主题但没有互相引用"""
        duplicates = []

        for i in range(len(self.entries)):
            for j in range(i + 1, len(self.entries)):
                e1, e2 = self.entries[i], self.entries[j]

                # 标签交集
                tags1 = set(e1.tags)
                tags2 = set(e2.tags)
                if not tags1 or not tags2:
                    continue

                tag_similarity = len(tags1 & tags2) / len(tags1 | tags2)

                # 标题关键词重叠
                words1 = set(re.findall(r'\w+', e1.heading.lower()))
                words2 = set(re.findall(r'\w+', e2.heading.lower()))
                if not words1 or not words2:
                    continue

                # 过滤常见的停用词
                stopwords = {"的", "在", "和", "是", "用", "与", "the", "a", "an", "is",
                            "to", "in", "of", "for", "and", "or", "not", "be", "on",
                            "使用", "参数", "传递", "全局", "变量", "优于"}
                words1 = words1 - stopwords
                words2 = words2 - stopwords

                if not words1 or not words2:
                    continue

                word_similarity = len(words1 & words2) / len(words1 | words2)

                # 标签相似度高 + 关键词重叠高 = 可能重复
                if tag_similarity >= 0.5 and word_similarity >= SIMILARITY_THRESHOLD:
                    # 检查是否已互相引用（标题出现在对方正文中）
                    refs_e1_in_e2 = e1.heading.lower() in e2.body.lower()
                    refs_e2_in_e1 = e2.heading.lower() in e1.body.lower()

                    if not (refs_e1_in_e2 or refs_e2_in_e1):
                        duplicates.append({
                            "dimension": "重复内容",
                            "severity": "info",
                            "entry_a": f"{e1.file}:{e1.heading}",
                            "entry_b": f"{e2.file}:{e2.heading}",
                            "tag_similarity": f"{tag_similarity:.0%}",
                            "word_similarity": f"{word_similarity:.0%}",
                            "detail": f"标签相似度 {tag_similarity:.0%}，关键词重叠 {word_similarity:.0%}，"
                                     f"但无互引用",
                            "suggestion": f"考虑合并 '{e1.heading}' 和 '{e2.heading}'，"
                                         f"或添加互相引用",
                        })

        return duplicates

    # ── 维度 5: 铁律膨胀检测 ─────────────────────────────────────

    def check_rule_overflow(self) -> List[dict]:
        """检测铁律是否超过 5 条上限"""
        rule_entries = [e for e in self.entries if e.tier == "rule"]
        overflow = []

        if len(rule_entries) > MAX_RULES:
            overflow.append({
                "dimension": "铁律膨胀",
                "severity": "warning",
                "count": len(rule_entries),
                "limit": MAX_RULES,
                "detail": f"铁律 {len(rule_entries)} 条，超过上限 {MAX_RULES} 条",
                "suggestion": f"考虑将 {len(rule_entries) - MAX_RULES} 条铁律降级为指南。"
                             f"建议降级最不常用的铁律。",
                "rules": [
                    f"{e.file}:{e.heading} (last-used: {e.last_used or '未知'})"
                    for e in rule_entries
                ],
            })

        return overflow

    # ── 运行审计 ─────────────────────────────────────────────────

    def run(self, full: bool = False) -> Dict:
        """运行健康检查，返回报告"""
        all_issues = []

        # 快速模式：矛盾 + 过期 + 铁律膨胀
        all_issues.extend(self.check_conflicts())
        all_issues.extend(self.check_expired())
        all_issues.extend(self.check_rule_overflow())

        # 全面模式：加上孤立 + 重复
        if full:
            all_issues.extend(self.check_orphans())
            all_issues.extend(self.check_duplicates())

        # 统计
        by_dimension = defaultdict(int)
        by_severity = defaultdict(int)
        for issue in all_issues:
            by_dimension[issue["dimension"]] += 1
            by_severity[issue["severity"]] += 1

        # 总体评级
        if by_severity.get("error", 0) > 0:
            overall = "🔴 需处理"
        elif by_severity.get("warning", 0) > 0:
            overall = "🟡 需关注"
        else:
            overall = "🟢 良好"

        dim_names = ["矛盾/冲突", "过期内容", "铁律膨胀"]
        if full:
            dim_names += ["孤立条目", "重复内容"]

        dim_counts = {d: by_dimension.get(d, 0) for d in dim_names}

        self.stats = {
            "total_entries": len(self.entries),
            "rule_count": sum(1 for e in self.entries if e.tier == "rule"),
            "guideline_count": sum(1 for e in self.entries if e.tier == "guideline"),
            "reference_count": sum(1 for e in self.entries if e.tier == "reference"),
            "memory_dir": str(self.memory_dir),
        }

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "mode": "全面审计" if full else "快速检查",
            "overall": overall,
            "dimensions": dim_counts,
            "by_severity": dict(by_severity),
            "stats": self.stats,
            "issues": all_issues,
        }

    # ── 更新 index.md ─────────────────────────────────────────────

    def update_index(self) -> bool:
        """刷新 index.md 中的分层统计和最近更新"""
        index_path = self.memory_dir / "index.md"
        if not index_path.exists():
            print(f"[ERROR] index.md 不存在: {index_path}", file=sys.stderr)
            return False

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[ERROR] 无法读取 index.md: {e}", file=sys.stderr)
            return False

        # 统计各层级数量
        rule_count = sum(1 for e in self.entries if e.tier == "rule")
        guideline_count = sum(1 for e in self.entries if e.tier == "guideline")
        reference_count = sum(1 for e in self.entries if e.tier == "reference")

        # 更新分层统计表（替换第一个表中的数字）
        # 铁律行
        content = re.sub(
            r'(\|\s*铁律\s*Rules\s*\|)\s*\d+\s*(\|)',
            rf'\1 {rule_count} \2',
            content
        )
        # 指南行
        content = re.sub(
            r'(\|\s*指南\s*Guidelines?\s*\|)\s*\d+\s*(\|)',
            rf'\1 {guideline_count} \2',
            content
        )
        # 参考行
        content = re.sub(
            r'(\|\s*参考\s*Reference\s*\|)\s*\d+\s*(\|)',
            rf'\1 {reference_count} \2',
            content
        )
        # 总计行（格式: | **总计** | **N** | ...）
        total = rule_count + guideline_count + reference_count
        content = re.sub(
            r'(\|\s*\*\*总计\*\*\s*\|)\s*\*{1,2}\d+\*{1,2}\s*(\|)',
            rf'\1 **{total}** \2',
            content
        )

        # 更新状态列（最后一列，格式：| 层级 | 数量 | 上限 | 状态 |）
        rule_status = ("🔴 需降级" if rule_count > MAX_RULES else
                       "⚪" if rule_count == 0 else "🟢")
        guideline_status = ("🟡 接近上限" if guideline_count > MAX_GUIDELINES * 0.8 else
                           "⚪" if guideline_count == 0 else "🟢")
        content = re.sub(
            r'(\|\s*铁律\s*Rules\s*\|\s*\d+\s*\|\s*\d+\s*\|)\s*\S+\s*(\|)',
            rf'\1 {rule_status} \2',
            content
        )
        content = re.sub(
            r'(\|\s*指南\s*Guidelines?\s*\|\s*\d+\s*\|\s*\d+\s*\|)\s*\S+\s*(\|)',
            rf'\1 {guideline_status} \2',
            content
        )

        # 更新分类统计表
        categories = ["code-style", "patterns", "anti-patterns", "tech-stack",
                      "project-structure", "conventions"]
        cat_file_map = {
            "code-style": "code-style.md",
            "patterns": "patterns.md",
            "anti-patterns": "anti-patterns.md",
            "tech-stack": "tech-stack.md",
            "project-structure": "project-structure.md",
            "conventions": "conventions.md",
        }

        for cat in categories:
            fname = cat_file_map[cat]
            cat_entries = [e for e in self.entries if e.file == fname]
            r = sum(1 for e in cat_entries if e.tier == "rule")
            g = sum(1 for e in cat_entries if e.tier == "guideline")
            ref = sum(1 for e in cat_entries if e.tier == "reference")
            total_cat = r + g + ref

            # 替换该分类行（格式: | cat | r | g | ref | total |）
            content = re.sub(
                rf'(\|\s*{re.escape(cat)}\s*\|)\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*(\|)',
                rf'\1 {r} | {g} | {ref} | {total_cat} \2',
                content
            )

        # 添加最近更新条目
        today = datetime.now().strftime("%Y-%m-%d")
        new_update_line = f"- {today}: 记忆健康检查完成（{self.stats['total_entries']} 条，{report_summary_line(self.stats)}）"

        # 找到 ## 最近更新 段落，在第一行后插入
        update_section = re.search(r'(## 最近更新\n)', content)
        if update_section:
            insert_pos = update_section.end()
            # 检查是否已有今天的条目
            if today not in content[insert_pos:insert_pos + 200]:
                content = content[:insert_pos] + new_update_line + "\n" + content[insert_pos:]

        try:
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] index.md 统计已刷新")
            return True
        except Exception as e:
            print(f"[ERROR] 无法写入 index.md: {e}", file=sys.stderr)
            return False


def report_summary_line(stats: Dict) -> str:
    """生成简短摘要行"""
    return (f"铁律{stats['rule_count']}/指南{stats['guideline_count']}"
            f"/参考{stats['reference_count']}")


# ── 输出 ──────────────────────────────────────────────────────────

def print_report(report: Dict) -> None:
    """打印人类可读的健康报告"""
    dims = report["dimensions"]
    sev = report["by_severity"]

    print("\n" + "=" * 60)
    print(f"  Mountainfish 健康报告 — {report['date']}")
    print(f"  模式: {report['mode']}")
    print("=" * 60)

    print(f"\n📊 概览:")
    for dim, count in dims.items():
        icon = "✅" if count == 0 else "⚠️"
        print(f"  {icon} {dim}: {count}")
    print(f"\n  总体: {report['overall']}")

    stats = report["stats"]
    print(f"\n📚 记忆库规模:")
    print(f"  条目: {stats['total_entries']} 条 "
          f"(铁律 {stats['rule_count']} / 指南 {stats['guideline_count']} "
          f"/ 参考 {stats['reference_count']})")

    if report["issues"]:
        print(f"\n── 问题详情 ({len(report['issues'])} 项) ──")
        for issue in report["issues"]:
            icon = {"error": "❌", "warning": "⚠️", "info": "💡"}.get(
                issue.get("severity", "info"), "•"
            )
            print(f"\n{icon} [{issue['dimension']}] {issue.get('detail', '')}")
            if "suggestion" in issue:
                print(f"   📌 {issue['suggestion']}")

            # 显示涉及条目
            if "entry" in issue:
                print(f"   → {issue['entry']}")
            elif "entry_a" in issue and "entry_b" in issue:
                print(f"   → A: {issue['entry_a']}")
                print(f"   → B: {issue['entry_b']}")

            # 铁律膨胀的额外信息
            if "rules" in issue:
                for rule in issue["rules"]:
                    print(f"   → {rule}")

    print("\n" + "=" * 60)

    # 无问题时打印建议操作
    if not report["issues"]:
        print("\n📌 无需操作，记忆库健康。")
    else:
        print(f"\n📌 共 {len(report['issues'])} 项需关注，详情如上。")


# ── CLI ───────────────────────────────────────────────────────────

def get_default_memory_dir() -> str:
    """获取默认记忆库目录"""
    script_dir = Path(__file__).resolve().parent
    memory_dir = script_dir.parent / "memory"
    if memory_dir.exists():
        return str(memory_dir)

    # fallback: 尝试从 SKILL.md 所在目录找
    skill_dir = script_dir.parent
    memory_dir = skill_dir / "memory"
    return str(memory_dir)


def _setup_encoding():
    """确保 Windows 控制台支持 emoji 输出"""
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

    full_mode = "--full" in sys.argv
    json_output = "--json" in sys.argv
    update_index = "--update-index" in sys.argv

    # 确定记忆库目录
    memory_dir = get_default_memory_dir()
    for i, arg in enumerate(sys.argv):
        if arg == "--memory-dir" and i + 1 < len(sys.argv):
            memory_dir = sys.argv[i + 1]
            break

    if not os.path.isdir(memory_dir):
        print(f"[ERROR] 记忆库目录不存在: {memory_dir}", file=sys.stderr)
        print("使用 --memory-dir <path> 指定记忆库目录", file=sys.stderr)
        sys.exit(3)

    checker = HealthChecker(memory_dir)

    if not checker.entries:
        print("[WARN] 未找到任何记忆条目（无 D8 元数据或记忆库为空）", file=sys.stderr)

    report = checker.run(full=full_mode)

    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)

    if update_index:
        checker.update_index()

    # 退出码
    sev = report.get("by_severity", {})
    if sev.get("error", 0) > 0:
        sys.exit(2)
    elif sev.get("warning", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
