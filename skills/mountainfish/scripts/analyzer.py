#!/usr/bin/env python3
"""
Mountainfish Style Analyzer
分析 C/C++ 代码风格特征
"""

import os
import re
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


class StyleAnalyzer:
    """代码风格分析器"""

    def __init__(self):
        self.indent_stats = Counter()  # 缩进统计
        self.brace_style_stats = Counter()  # 大括号风格统计
        self.naming_stats = {
            'functions': Counter(),
            'variables': Counter(),
            'classes': Counter(),
            'constants': Counter()
        }
        self.comment_stats = Counter()  # 注释风格统计
        self.line_count = 0
        self.file_count = 0

    def analyze_file(self, filepath: str) -> bool:
        """分析单个文件"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            self.file_count += 1
            self.line_count += len(lines)

            # 分析缩进
            self._analyze_indentation(lines)

            # 分析大括号风格
            self._analyze_brace_style(lines)

            # 分析命名规范
            self._analyze_naming(content)

            # 分析注释风格
            self._analyze_comments(lines)

            return True
        except Exception as e:
            print(f"  [ERROR] 无法分析文件 {filepath}: {e}", file=sys.stderr)
            return False

    def _analyze_indentation(self, lines: List[str]):
        """分析缩进风格"""
        for line in lines:
            if not line.strip():  # 跳过空行
                continue

            # 计算前导空格/Tab
            leading = len(line) - len(line.lstrip())
            if leading == 0:
                continue

            if line[0] == '\t':
                self.indent_stats['tab'] += 1
            else:
                # 检测空格数量
                spaces = len(line) - len(line.lstrip(' '))
                if spaces % 4 == 0:
                    self.indent_stats['4_spaces'] += 1
                elif spaces % 2 == 0:
                    self.indent_stats['2_spaces'] += 1
                else:
                    self.indent_stats['other'] += 1

    def _analyze_brace_style(self, lines: List[str]):
        """分析大括号风格"""
        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测独立行的大括号
            if stripped == '{':
                # 检查前一行
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line.endswith(')') or prev_line.endswith('else'):
                        # Allman 风格：大括号独占一行
                        self.brace_style_stats['allman'] += 1
                    else:
                        self.brace_style_stats['other'] += 1
            elif stripped.endswith('{'):
                # K&R 风格：大括号在行尾
                if '{' in stripped and stripped.index('{') > 0:
                    self.brace_style_stats['kr'] += 1

    def _analyze_naming(self, content: str):
        """分析命名规范"""
        # 函数定义模式
        func_patterns = [
            r'(?:int|void|char|float|double|bool|unsigned|long|short|struct|enum)\s+(\w+)\s*\(',  # C 函数
            r'(\w+)::(\w+)\s*\(',  # C++ 类方法
            r'def\s+(\w+)\s*\(',  # Python 函数（兼容）
        ]

        for pattern in func_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                name = match if isinstance(match, str) else match[-1]
                self._classify_naming(name, 'functions')

        # 变量声明模式
        var_patterns = [
            r'(?:int|char|float|double|bool|unsigned|long|short)\s+(\w+)\s*[=;]',
            r'auto\s+(\w+)\s*=',
            r'const\s+\w+\s+(\w+)\s*=',
        ]

        for pattern in var_patterns:
            matches = re.findall(pattern, content)
            for name in matches:
                self._classify_naming(name, 'variables')

        # 类名模式
        class_pattern = r'(?:class|struct)\s+(\w+)'
        matches = re.findall(class_pattern, content)
        for name in matches:
            self._classify_naming(name, 'classes')

        # 常量模式
        const_pattern = r'#define\s+(\w+)'
        matches = re.findall(const_pattern, content)
        for name in matches:
            self._classify_naming(name, 'constants')

    def _classify_naming(self, name: str, category: str):
        """分类命名风格"""
        if not name or len(name) < 2:
            return

        # 跳过常见关键字
        keywords = {'if', 'else', 'for', 'while', 'return', 'switch', 'case', 'break',
                    'continue', 'do', 'goto', 'default', 'typedef', 'sizeof', 'NULL'}
        if name in keywords:
            return

        if name.isupper() and '_' in name:
            self.naming_stats[category]['UPPER_SNAKE_CASE'] += 1
        elif '_' in name and name.islower():
            self.naming_stats[category]['snake_case'] += 1
        elif name[0].isupper() and not name.isupper():
            self.naming_stats[category]['PascalCase'] += 1
        elif name[0].islower() and not '_' in name and any(c.isupper() for c in name[1:]):
            self.naming_stats[category]['camelCase'] += 1

    def _analyze_comments(self, lines: List[str]):
        """分析注释风格"""
        for line in lines:
            stripped = line.strip()

            if stripped.startswith('//'):
                self.comment_stats['line_comment'] += 1
            elif stripped.startswith('/*'):
                self.comment_stats['block_comment_start'] += 1
            elif stripped.startswith('*') and not stripped.startswith('*/'):
                self.comment_stats['block_comment_line'] += 1
            elif stripped.endswith('*/'):
                self.comment_stats['block_comment_end'] += 1
            elif 'TODO' in stripped or 'FIXME' in stripped or 'HACK' in stripped:
                self.comment_stats['todo_comments'] += 1

    def get_report(self) -> Dict:
        """生成分析报告"""
        report = {
            'summary': {
                'files': self.file_count,
                'lines': self.line_count
            },
            'indentation': self._get_indentation_result(),
            'brace_style': self._get_brace_style_result(),
            'naming': self._get_naming_result(),
            'comments': self._get_comment_result()
        }
        return report

    def _get_indentation_result(self) -> str:
        """获取缩进风格结果"""
        if not self.indent_stats:
            return 'unknown'

        total = sum(self.indent_stats.values())
        if total == 0:
            return 'unknown'

        # 多数票决
        most_common = self.indent_stats.most_common(1)[0]
        style, count = most_common
        percentage = count / total * 100

        if percentage > 60:  # 超过60%认为是主要风格
            return style
        return 'mixed'

    def _get_brace_style_result(self) -> str:
        """获取大括号风格结果"""
        if not self.brace_style_stats:
            return 'unknown'

        total = sum(self.brace_style_stats.values())
        if total == 0:
            return 'unknown'

        kr_count = self.brace_style_stats.get('kr', 0)
        allman_count = self.brace_style_stats.get('allman', 0)

        if kr_count > allman_count:
            return 'K&R'
        elif allman_count > kr_count:
            return 'Allman'
        return 'mixed'

    def _get_naming_result(self) -> Dict:
        """获取命名风格结果"""
        result = {}
        for category, stats in self.naming_stats.items():
            if stats:
                most_common = stats.most_common(1)[0]
                result[category] = most_common[0]
            else:
                result[category] = 'unknown'
        return result

    def _get_comment_result(self) -> Dict:
        """获取注释风格结果"""
        return dict(self.comment_stats)


def analyze_directory(directory: str, extensions: List[str] = None) -> Dict:
    """分析目录中的所有源文件"""
    if extensions is None:
        extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']

    analyzer = StyleAnalyzer()
    directory = Path(directory)

    if not directory.exists():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        return {}

    print(f"\n=== Mountainfish Code Style Analysis ===\n")
    print(f"Scanning: {directory.absolute()}")
    print(f"File types: {', '.join(extensions)}\n")

    # 扫描所有匹配的文件
    files = []
    for ext in extensions:
        files.extend(directory.rglob(f'*{ext}'))

    print(f"Found {len(files)} files\n")

    # 分析每个文件
    for filepath in files:
        print(f"  Analyzing: {filepath.relative_to(directory)}")
        analyzer.analyze_file(str(filepath))

    # 生成报告
    report = analyzer.get_report()
    return report


def print_report(report: Dict):
    """打印分析报告"""
    print("\n" + "="*50)
    print("Mountainfish Style Analysis Report")
    print("="*50)

    summary = report.get('summary', {})
    print(f"\n[Statistics]")
    print(f"  - Files: {summary.get('files', 0)}")
    print(f"  - Lines: {summary.get('lines', 0)}")

    print(f"\n[Indentation Style]")
    indent = report.get('indentation', 'unknown')
    indent_map = {
        '4_spaces': '4 Spaces',
        '2_spaces': '2 Spaces',
        'tab': 'Tab',
        'mixed': 'Mixed',
        'unknown': 'Unknown'
    }
    print(f"  - {indent_map.get(indent, indent)}")

    print(f"\n[Brace Style]")
    brace = report.get('brace_style', 'unknown')
    print(f"  - {brace}")

    print(f"\n[Naming Convention]")
    naming = report.get('naming', {})
    naming_map = {
        'snake_case': 'snake_case',
        'camelCase': 'camelCase',
        'PascalCase': 'PascalCase',
        'UPPER_SNAKE_CASE': 'UPPER_SNAKE_CASE',
        'unknown': 'Unknown'
    }
    for category, style in naming.items():
        print(f"  - {category}: {naming_map.get(style, style)}")

    print(f"\n[Comments]")
    comments = report.get('comments', {})
    if comments:
        print(f"  - Line comments (//): {comments.get('line_comment', 0)}")
        print(f"  - Block comments: {comments.get('block_comment_start', 0)}")
        print(f"  - TODO/FIXME: {comments.get('todo_comments', 0)}")
    else:
        print(f"  - No comments detected")

    print("\n" + "="*50)


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
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h", "help"):
        print("Mountainfish Style Analyzer — 分析 C/C++ 代码风格特征")
        print()
        print("用法: python analyzer.py <directory> [--json]")
        print()
        print("参数:")
        print("  <directory>   要分析的源码目录")
        print("  --json        以 JSON 格式输出结果")
        print()
        print("示例:")
        print("  python analyzer.py ./src")
        print("  python analyzer.py ./src --json")
        sys.exit(0)

    directory = sys.argv[1]
    json_output = '--json' in sys.argv

    # 如果是 JSON 输出模式，静默分析
    if json_output:
        import json
        analyzer = StyleAnalyzer()
        directory_path = Path(directory)

        if not directory_path.exists():
            print(json.dumps({"error": "Directory not found"}))
            sys.exit(1)

        # 扫描所有匹配的文件
        extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']
        files = []
        for ext in extensions:
            files.extend(directory_path.rglob(f'*{ext}'))

        # 分析每个文件
        for filepath in files:
            analyzer.analyze_file(str(filepath))

        report = analyzer.get_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        report = analyze_directory(directory)
        print_report(report)


if __name__ == '__main__':
    main()
