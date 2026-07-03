#!/usr/bin/env python3
"""
Mountainfish check-style — 机械门禁脚本
检查源码是否违反记忆库中的铁律和指南。

用法（工程根或源码目录执行）:
  python check-style.py <源码目录>                  # 全部检查
  python check-style.py <源码目录> --naming          # 仅命名规范
  python check-style.py <源码目录> --anti-patterns   # 仅反模式
  python check-style.py <源码目录> --tech-stack      # 仅技术栈
  python check-style.py <源码目录> --config rules.yaml  # 使用自定义配置
  python check-style.py <源码目录> --json            # JSON 输出

返回:
  exit 0 = 通过
  exit 1 = 发现违规
  exit 2 = 运行错误（如目录不存在）
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 默认检查规则（从记忆库铁律/指南同步）──────────────────────────

DEFAULT_RULES: Dict[str, List[dict]] = {
    "naming": [
        {
            "id": "N1",
            "description": "函数命名风格不一致（建议使用 snake_case）",
            "patterns": [
                # 检测 pascalCase / camelCase 风格的 C 函数定义
                r'(?:static\s+)?(?:inline\s+)?(?:void|int|char|float|double|bool|'
                r'uint\d+_t|int\d+_t|unsigned|long|short|struct\s+\w+)\s+'
                r'([A-Z][a-z]+[A-Z][a-zA-Z]*)\s*\(',
            ],
            "severity": "warning",
            "message": "函数 '{match}' 使用了疑似 PascalCase/camelCase 命名，建议使用 snake_case",
        },
        {
            "id": "N2",
            "description": "常量未使用 UPPER_SNAKE_CASE",
            "patterns": [
                r'#define\s+([a-z][a-z_0-9]*)\s+(?!\()',
            ],
            "severity": "warning",
            "message": "#define '{match}' 建议使用 UPPER_SNAKE_CASE",
        },
    ],
    "anti_patterns": [
        {
            "id": "A1",
            "description": "全局变量模式（指南：参数传递优于全局变量）",
            "patterns": [
                # static 全局变量定义（非 const）
                r'^(static\s+)(?!const\s+)(\w[\w\s\*]+)\s+(\w+)\s*=',

                # 非 static 全局变量
                r'^(?!(?:static|const|#|typedef|struct|enum|union|extern)\s+)'
                r'(\w[\w\s\*]+)\s+(\w+)\s*=\s*\{',
            ],
            "severity": "warning",
            "message": "检测到可能的全局变量 '{match}'，指南建议使用参数传递",
        },
        {
            "id": "A2",
            "description": "魔数未标注来源",
            "patterns": [
                # 检测赋值/比较中的裸数字（非 0/1/-1/指针常见值）
                r'(?<![a-zA-Z_#\d])(\d{4,})(?![a-zA-Z_#\d])',
            ],
            "severity": "info",
            "message": "检测到可能的魔数 '{match}'，建议标注来源（如 @datasheet p.XX）",
        },
    ],
    "tech_stack": [
        {
            "id": "T1",
            "description": "stdio.h 在嵌入式固件中的使用（建议用专用日志宏）",
            "patterns": [
                r'#include\s*[<"]stdio\.h[>"]',
                r'\bprintf\s*\(',
            ],
            "severity": "info",
            "message": "检测到 stdio/printf 使用，嵌入式固件建议使用专用日志宏",
        },
    ],
}


class StyleChecker:
    """风格检查器"""

    def __init__(self, rules: Optional[Dict] = None):
        self.rules = rules or DEFAULT_RULES
        self.violations: List[dict] = []
        self.files_checked = 0
        self.lines_checked = 0

    def check_file(self, filepath: str) -> bool:
        """检查单个文件，返回是否有违规"""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"  [SKIP] 无法读取 {filepath}: {e}", file=sys.stderr)
            return False

        self.files_checked += 1
        self.lines_checked += len(lines)

        has_violations = False

        for line_no, line in enumerate(lines, 1):
            for category, category_rules in self.rules.items():
                for rule in category_rules:
                    for pattern in rule.get("patterns", []):
                        try:
                            m = re.search(pattern, line)
                        except re.error:
                            continue
                        if m:
                            # 提取匹配的标识符
                            match_name = ""
                            for g in m.groups():
                                if g and len(g) > 1 and not g.startswith(("static", "const")):
                                    match_name = g
                                    break
                            if not match_name:
                                match_name = m.group(0)[:50]

                            violation = {
                                "file": filepath,
                                "line": line_no,
                                "rule_id": rule["id"],
                                "category": category,
                                "severity": rule.get("severity", "error"),
                                "message": rule["message"].format(match=match_name),
                                "code": line.strip()[:120],
                            }
                            self.violations.append(violation)
                            has_violations = True

        return has_violations

    def check_directory(self, directory: str, extensions: List[str] = None) -> int:
        """检查目录中的所有源文件，返回违规数"""
        if extensions is None:
            extensions = [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"]

        directory = Path(directory)
        if not directory.exists():
            print(f"[ERROR] 目录不存在: {directory}", file=sys.stderr)
            return -1

        files = []
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))

        if not files:
            print(f"[WARN] 未找到匹配的源文件 ({', '.join(extensions)})", file=sys.stderr)
            return 0

        for filepath in sorted(files):
            self.check_file(str(filepath))

        return len(self.violations)

    def get_report(self) -> Dict:
        """生成检查报告"""
        by_severity = {"error": 0, "warning": 0, "info": 0}
        by_category = {}
        for v in self.violations:
            by_severity[v["severity"]] = by_severity.get(v["severity"], 0) + 1
            by_category[v["category"]] = by_category.get(v["category"], 0) + 1

        return {
            "summary": {
                "files_checked": self.files_checked,
                "lines_checked": self.lines_checked,
                "violations": len(self.violations),
                "by_severity": by_severity,
                "by_category": by_category,
            },
            "violations": self.violations,
        }


def print_report(report: Dict) -> None:
    """打印人类可读报告"""
    s = report["summary"]
    print("\n" + "=" * 60)
    print("Mountainfish check-style 报告")
    print("=" * 60)
    print(f"\n文件: {s['files_checked']} 个 | 行数: {s['lines_checked']} 行")
    print(f"违规: {s['violations']} 处 "
          f"(error: {s['by_severity'].get('error', 0)}, "
          f"warning: {s['by_severity'].get('warning', 0)}, "
          f"info: {s['by_severity'].get('info', 0)})")

    if s["violations"] == 0:
        print("\n✅ 全部通过，未发现违规")
        return

    print("\n── 违规列表 ──")
    for v in report["violations"]:
        icon = {"error": "❌", "warning": "⚠️", "info": "💡"}.get(v["severity"], "•")
        print(f"\n{icon} [{v['rule_id']}] {v['file']}:{v['line']}")
        print(f"   {v['message']}")
        print(f"   → {v['code']}")

    print("\n" + "=" * 60)


def _setup_encoding():
    """修复 Windows 下 GBK 编码问题"""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    """主函数"""
    _setup_encoding()
    if len(sys.argv) < 2:
        print("用法: python check-style.py <源码目录> [选项]")
        print("选项:")
        print("  --naming        仅检查命名规范")
        print("  --anti-patterns 仅检查反模式")
        print("  --tech-stack    仅检查技术栈一致性")
        print("  --config <yaml> 使用自定义规则配置")
        print("  --json          JSON 格式输出")
        print("返回: exit 0=通过, 1=违规, 2=错误")
        sys.exit(2)

    directory = sys.argv[1]
    json_output = "--json" in sys.argv

    # 过滤检查类别
    want_all = not any(f in sys.argv for f in ("--naming", "--anti-patterns", "--tech-stack"))

    rules = DEFAULT_RULES.copy()
    if not want_all:
        filtered = {}
        if "--naming" in sys.argv:
            filtered["naming"] = rules["naming"]
        if "--anti-patterns" in sys.argv:
            filtered["anti_patterns"] = rules["anti_patterns"]
        if "--tech-stack" in sys.argv:
            filtered["tech_stack"] = rules["tech_stack"]
        rules = filtered

    checker = StyleChecker(rules)
    violations = checker.check_directory(directory)

    if violations < 0:
        sys.exit(2)  # 运行错误

    report = checker.get_report()

    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)

    # exit 1 if violations found
    sys.exit(1 if report["summary"]["violations"] > 0 else 0)


if __name__ == "__main__":
    main()
