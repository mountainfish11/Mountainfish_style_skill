#!/usr/bin/env python3
"""
Mountainfish profiler — 代码风格画像工具
分析 C/C++ 项目的惯用写法，输出可直接沉淀到记忆库参考层的经验条目。

用法:
  python profiler.py <源码目录>                    # 单项目分析
  python profiler.py <源码目录> --source own        # 自己的项目（默认）
  python profiler.py <源码目录> --source reference  # 别人的项目
  python profiler.py <源码目录> --json             # JSON 输出
  python profiler.py <源码目录> --output report.md # 指定输出路径
  python profiler.py --compare a.md b.md           # 跨项目对比
  python profiler.py --compare a.md b.md --json    # 对比 + JSON

返回:
  exit 0 = 成功
  exit 1 = 运行错误（如目录不存在）
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 常量 ──────────────────────────────────────────────────────────

FILE_EXTENSIONS = [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"]

# 常见的 C 嵌入式惯用写法清单（用于 Phase 3 缺失检测）
KNOWN_IDIOMS: Dict[str, dict] = {
    "typedef_struct": {
        "category": "typedef struct 组织",
        "patterns": ["前置 typedef + 匿名 struct", "命名 tag + typedef 分离",
                      "typedef + struct 合写", "无 typedef 裸 struct"],
        "suggestion": "大型项目建议统一使用一种 struct 组织风格，通常推荐前置 typedef 减少依赖",
    },
    "dowhile_macro": {
        "category": "do-while(0) 宏包装",
        "patterns": ["do-while(0) 多语句宏", "裸多语句宏（无保护）",
                      "({ }) GCC 语句表达式", "static inline 函数替代宏"],
        "suggestion": "多语句宏应使用 do-while(0) 包裹，保证在任何控制流上下文中安全",
    },
    "callback_register": {
        "category": "callback 注册模式",
        "patterns": ["函数指针 struct 注册表", "__weak 弱符号回调",
                      "运行时回调链表/数组", "直接函数调用（无回调抽象）"],
        "suggestion": "驱动层建议使用回调注册表模式，用 const 函数指针 struct 存储所有回调入口",
    },
    "isr_protection": {
        "category": "ISR / 临界区写法",
        "patterns": ["portENTER_CRITICAL / portEXIT_CRITICAL",
                      "__disable_irq / __enable_irq", "basepri 掩码保护",
                      "volatile 标志位轮询（无锁）",
                      "裸标志位（无保护）"],
        "suggestion": "ISR 与主循环共享变量必须有临界区保护，推荐用 volatile + 关中断最小窗口",
    },
    "state_machine": {
        "category": "状态机实现",
        "patterns": ["switch-case 状态机", "函数指针跳转表",
                      "查表驱动（状态×事件→动作+次态）", "if-else 链（无显式状态）"],
        "suggestion": "≥5 个状态的状态机建议用查表或函数指针表实现，避免 switch-case 过长",
    },
    "ring_buffer": {
        "category": "环形缓冲区",
        "patterns": ["自定义 ring buffer struct", "CMSIS RTOS 消息队列",
                      "FreeRTOS StreamBuffer", "裸数组 + 手动取模"],
        "suggestion": "串口/传感器数据缓冲建议使用 ring buffer，避免频繁 malloc/free",
    },
    "error_handling": {
        "category": "错误传递方式",
        "patterns": ["return 错误码（int / error_t）", "goto fail 集中清理",
                      "assert 断言（仅开发期）", "全局 errno / 最后错误寄存器",
                      "无错误处理（void 返回）"],
        "suggestion": "库函数建议返回错误码，应用层可用 assert 捕获编程错误",
    },
    "include_guard": {
        "category": "头文件保护",
        "patterns": ["#ifndef / #define / #endif 经典守卫",
                      "#pragma once", "无头文件保护"],
        "suggestion": "优先使用 #pragma once（现代编译器均支持），兼容旧项目保留 #ifndef 双保险",
    },
    "volatile_usage": {
        "category": "volatile 使用",
        "patterns": ["ISR 共享变量 volatile", "MMIO 寄存器 volatile 指针",
                      "多线程共享变量 volatile（配合锁）",
                      "误用 volatile 替代并发同步"],
        "suggestion": "volatile ≠ 原子操作，多核/抢占场景下需配合临界区或原子操作",
    },
}

# 文件分类启发式规则
LAYER_RULES = {
    "driver": {
        "path_patterns": [r"/drv[_/]", r"/driver[_/]", r"/bsp[_/]", r"/hal[_/]", r"/periph"],
        "content_patterns": [
            r'#include\s*[<"](?:stm32|gd32|esp|nrf|mspm0|infineon|atmel)',
            r'\b(?:GPIO|USART|SPI|I2C|TIM|ADC|DMA|NVIC|EXTI)_?\w*\(',
            r'\b__attribute__\s*\(\s*\(\s*(?:weak|interrupt|section)\s*',
        ],
    },
    "app": {
        "path_patterns": [r"/app[_/]", r"/task[_/]", r"/main\.c$", r"/application"],
        "content_patterns": [
            r'#include\s*[<"]FreeRTOS\.h[>"]',
            r'\bxTaskCreate\s*\(',
            r'\b(?:app_|task_|thread_)\w+\s*\(',
        ],
    },
    "util": {
        "path_patterns": [r"/util[_/]", r"/common[_/]", r"/lib[_/]", r"/ringbuf", r"/list\.", r"/queue"],
        "content_patterns": [
            r'^//.*utility|^//.*helper|^//.*common',
        ],
    },
}


# ── 数据结构 ──────────────────────────────────────────────────────

@dataclass
class FileClassification:
    path: str
    layer: str        # driver / app / util / unknown
    confidence: str   # high / medium / low


@dataclass
class IdiomFinding:
    category: str
    pattern_name: str
    file: str
    line: int
    code: str                # 匹配行内容
    context_before: str = ""  # 前一行上下文
    context_after: str = ""   # 后一行上下文


@dataclass
class CategoryReport:
    category: str
    detected: bool
    findings: List[IdiomFinding] = field(default_factory=list)
    frequency: int = 0
    file_count: int = 0
    by_pattern: Counter = field(default_factory=Counter)
    by_layer: Counter = field(default_factory=Counter)
    suggestion: str = ""


@dataclass
class ProfileResult:
    directory: str
    timestamp: str
    source: str              # own | reference
    files_scanned: int
    lines_scanned: int
    layer_summary: Dict[str, int]   # layer → file count
    categories: List[CategoryReport]
    missing_patterns: List[dict]    # [{category, suggestion}]


# ── Phase 1: 文件分类 ─────────────────────────────────────────────

class ProjectClassifier:
    """识别项目隐含分层"""

    def __init__(self, directory: str):
        self.directory = Path(directory)

    def classify(self) -> List[FileClassification]:
        results = []
        for ext in FILE_EXTENSIONS:
            for fpath in self.directory.rglob(f"*{ext}"):
                rel = str(fpath.relative_to(self.directory)).replace("\\", "/")
                layer, confidence = self._classify_one(fpath, rel)
                results.append(FileClassification(
                    path=rel, layer=layer, confidence=confidence
                ))
        return results

    def _classify_one(self, fpath: Path, rel_path: str) -> Tuple[str, str]:
        scores = {"driver": 0, "app": 0, "util": 0}

        # 路径模式匹配
        for layer, rules in LAYER_RULES.items():
            for pat in rules["path_patterns"]:
                if re.search(pat, rel_path, re.IGNORECASE):
                    scores[layer] += 2

        # 内容模式匹配（采样前 80 行）
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                head = "".join(f.readline() for _ in range(80))
        except Exception:
            head = ""

        for layer, rules in LAYER_RULES.items():
            for pat in rules.get("content_patterns", []):
                m = re.search(pat, head, re.IGNORECASE | re.MULTILINE)
                if m:
                    scores[layer] += 3

        # 判定
        max_score = max(scores.values())
        if max_score == 0:
            return ("unknown", "low")

        best = [k for k, v in scores.items() if v == max_score]
        layer = best[0]
        second = sorted(scores.values(), reverse=True)[1]
        confidence = "high" if max_score >= 5 and max_score > second * 2 else ("medium" if max_score >= 3 else "low")
        return (layer, confidence)


# ── Phase 2: 惯用写法检测 ─────────────────────────────────────────

class IdiomDetector:
    """检测 5+ 类惯用写法"""

    def __init__(self, directory: str, classifications: List[FileClassification]):
        self.directory = Path(directory)
        self.classifications = {c.path: c for c in classifications}

    def detect_all(self) -> List[CategoryReport]:
        return [
            self._detect_typedef_struct(),
            self._detect_dowhile_macro(),
            self._detect_callback(),
            self._detect_isr(),
            self._detect_containers(),
            self._detect_error_handling(),
            self._detect_include_guard(),
            self._detect_volatile(),
        ]

    def _layer_of(self, rel_path: str) -> str:
        c = self.classifications.get(rel_path)
        return c.layer if c else "unknown"

    def _scan_files(self, regex: re.Pattern,
                    capture_groups: bool = False) -> List[IdiomFinding]:
        """在全部文件中搜索模式，返回匹配列表"""
        findings = []
        for rel_path, clf in self.classifications.items():
            fpath = self.directory / rel_path
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for i, line in enumerate(lines):
                m = regex.search(line)
                if not m:
                    continue
                findings.append(IdiomFinding(
                    category="",  # caller fills
                    pattern_name="",  # caller fills
                    file=rel_path,
                    line=i + 1,
                    code=line.strip()[:120],
                    context_before=lines[i - 1].strip()[:80] if i > 0 else "",
                    context_after=lines[i + 1].strip()[:80] if i + 1 < len(lines) else "",
                ))

        return findings

    # ── 1. typedef struct 组织 ─────────────────────────────────────

    def _detect_typedef_struct(self) -> CategoryReport:
        findings = []
        patterns = {
            "前置 typedef + 匿名 struct": re.compile(
                r'typedef\s+struct\s*(?:\w+(?:_t|_s|_tag))?\s*\{', re.MULTILINE),
            "命名 tag + typedef 分离": re.compile(
                r'typedef\s+struct\s+\w+\s+\w+_t\s*;'),
            "typedef + struct 合写": re.compile(
                r'typedef\s+(?:volatile\s+)?struct\s+\w*\s*\{[^}]*\}\s*\w+'),
            "无 typedef 裸 struct": re.compile(
                r'(?<!typedef\s)(?<!\w)struct\s+\w+\s*\{'),
        }
        report = CategoryReport(
            category="typedef struct 组织",
            detected=False,
            suggestion=KNOWN_IDIOMS["typedef_struct"]["suggestion"],
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    # ── 2. do-while(0) 宏 ──────────────────────────────────────────

    def _detect_dowhile_macro(self) -> CategoryReport:
        patterns = {
            "do-while(0) 多语句宏": re.compile(
                r'#define\s+\w+.*\\\s*\n.*do\s*\{.*\}while\s*\(\s*0\s*\)',
                re.DOTALL),
            "裸多语句宏（无保护）": re.compile(
                r'#define\s+\w+.*\\\s*\n(?!.*do\s*\{)'),
            "({ }) GCC 语句表达式": re.compile(
                r'#define\s+\w+.*\(\s*\{'),
        }

        # do-while(0) needs multiline matching across files
        findings = self._scan_multiline_macros()

        report = CategoryReport(
            category="do-while(0) 宏包装",
            detected=False,
            suggestion=KNOWN_IDIOMS["dowhile_macro"]["suggestion"],
        )

        for f in findings:
            f.category = report.category
            report.by_pattern[f.pattern_name] += 1
            report.by_layer[self._layer_of(f.file)] += 1

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    def _scan_multiline_macros(self) -> List[IdiomFinding]:
        """扫描多行宏（合并反斜杠续行后匹配）"""
        findings = []
        for rel_path, clf in self.classifications.items():
            fpath = self.directory / rel_path
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            # 找所有 #define 开头、\ 续行的宏
            for m in re.finditer(r'#define\s+(\w+)(.*?)(?=\n(?!.*\\\s*$))',
                                  content, re.DOTALL):
                body = m.group(2)
                name = m.group(1)

                # 计算行号
                line_no = content[:m.start()].count("\n") + 1

                if "do" in body and "while" in body and "0" in body:
                    pname = "do-while(0) 多语句宏"
                elif "({" in body or "({ " in body:
                    pname = "({ }) GCC 语句表达式"
                elif "\\" in body and len(body) > 30:
                    pname = "裸多语句宏（无保护）"
                else:
                    continue

                findings.append(IdiomFinding(
                    category="do-while(0) 宏包装",
                    pattern_name=pname,
                    file=rel_path,
                    line=line_no,
                    code=f"#define {name}{body[:100].strip()}",
                ))
        return findings

    # ── 3. callback 注册 ──────────────────────────────────────────

    def _detect_callback(self) -> CategoryReport:
        findings = []
        patterns = {
            "函数指针 struct 注册表": re.compile(
                r'(?:typedef\s+)?struct\s*\{[^}]*\w+\s*\(\s*\*\s*\w+\s*\)\s*\([^)]*\)[^}]*\}\s*\w+'),
            "__weak 弱符号回调": re.compile(
                r'__attribute__\s*\(\s*\(\s*weak'),
            "运行时回调注册函数": re.compile(
                r'(?:register|set|attach)_(?:callback|handler|isr|hook)\s*\('),
        }

        report = CategoryReport(
            category="callback 注册模式",
            detected=False,
            suggestion=KNOWN_IDIOMS["callback_register"]["suggestion"],
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    # ── 4. ISR / 临界区 ───────────────────────────────────────────

    def _detect_isr(self) -> CategoryReport:
        findings = []
        patterns = {
            "portENTER_CRITICAL": re.compile(
                r'\b(?:portENTER_CRITICAL|portEXIT_CRITICAL|taskENTER_CRITICAL|taskEXIT_CRITICAL)\s*\('),
            "__disable_irq / __enable_irq": re.compile(
                r'\b(?:__disable_irq|__enable_irq|__disable_interrupt|__enable_interrupt)\s*\('),
            "__set_BASEPRI 掩码": re.compile(
                r'\b(?:__set_BASEPRI|__get_BASEPRI|__set_PRIMASK)\s*\('),
            "volatile 标志位（ISR 共享）": re.compile(
                r'volatile\s+(?:uint\w+_t|int\w+_t|bool|unsigned|char)\s+\w+\s*;.*(?:flag|ready|done|pending|irq|isr)',
                re.IGNORECASE),
        }

        report = CategoryReport(
            category="ISR / 临界区写法",
            detected=False,
            suggestion=KNOWN_IDIOMS["isr_protection"]["suggestion"],
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    # ── 5. 容器/工具模式 ──────────────────────────────────────────

    def _detect_containers(self) -> CategoryReport:
        findings = []
        patterns = {
            "switch-case 状态机": re.compile(
                r'}\s*(?:else\s+)?(?:if\s*\(.*state|switch\s*\(.*state|case\s+STATE_)',
                re.IGNORECASE),
            "函数指针跳转表": re.compile(
                r'(?:typedef\s+)?\w+\s*\(\s*\*\s*\w+(?:\[\]|\[[^\]]+\])\s*\)\s*\([^)]*\)\s*=\s*\{'),
            "ring buffer struct": re.compile(
                r'(?:typedef\s+)?struct\s+\w*(?:ring|fifo|circ(?:ular)?)\w*\s*\{.*(?:head|tail|rd|wr|read|write|buf|buffer).*\}',
                re.DOTALL | re.IGNORECASE),
            "ring buffer typedef": re.compile(
                r'}\s*(?:ring|fifo|circ(?:ular)?)\w*\s*;', re.IGNORECASE),
            "侵入式链表": re.compile(
                r'struct\s+\w*(?:list|node|link)\w*\s*\{[^}]*struct\s+\w*(?:list|node|link)\w*\s*\*'),
        }

        report = CategoryReport(
            category="容器/工具模式",
            detected=False,
            suggestion="驱动/应用层建议统一使用项目内标准容器（ring buffer / 链表 / 状态机框架），避免各模块重复实现",
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    # ── 6. 错误处理 ───────────────────────────────────────────────

    def _detect_error_handling(self) -> CategoryReport:
        findings = []
        patterns = {
            "return 错误码": re.compile(
                r'\breturn\s+(?:-\d+|E[A-Z_]+|ERROR_\w+|err_\w+|ret\b)'),
            "goto fail 集中清理": re.compile(
                r'goto\s+(?:fail|err|cleanup|exit|out|done)\s*;'),
            "assert 断言": re.compile(
                r'\b(?:assert|ASSERT|configASSERT|DEV_ASSERT)\s*\('),
            "全局 errno": re.compile(
                r'\b(?:errno|last_error|g_error)\s*='),
        }

        report = CategoryReport(
            category="错误传递方式",
            detected=False,
            suggestion=KNOWN_IDIOMS["error_handling"]["suggestion"],
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    # ── 7. 头文件保护 ─────────────────────────────────────────────

    def _detect_include_guard(self) -> CategoryReport:
        findings = []
        patterns = {
            "#pragma once": re.compile(r'^#pragma\s+once'),
            "#ifndef 经典守卫": re.compile(r'^#ifndef\s+\w+_H\b'),
        }

        report = CategoryReport(
            category="头文件保护",
            detected=False,
            suggestion=KNOWN_IDIOMS["include_guard"]["suggestion"],
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report

    # ── 8. volatile 使用 ──────────────────────────────────────────

    def _detect_volatile(self) -> CategoryReport:
        findings = []
        patterns = {
            "volatile 全局变量": re.compile(
                r'^(?:static\s+)?volatile\s+\w[\w\s\*]+\s+\w+\s*[;=]', re.MULTILINE),
            "volatile 指针（MMIO）": re.compile(
                r'volatile\s+\w+\s*\*\s*\w+\s*=\s*\(.*\)\s*0x'),
        }

        report = CategoryReport(
            category="volatile 使用",
            detected=False,
            suggestion=KNOWN_IDIOMS["volatile_usage"]["suggestion"],
        )

        for pat_name, pat_regex in patterns.items():
            batch = self._scan_files(pat_regex)
            for f in batch:
                f.category = report.category
                f.pattern_name = pat_name
                report.by_pattern[pat_name] += 1
                report.by_layer[self._layer_of(f.file)] += 1
            findings.extend(batch)

        report.findings = findings
        report.frequency = len(findings)
        report.file_count = len(set(f.file for f in findings))
        report.detected = len(findings) > 0
        return report


# ── Phase 3: 缺失清单 ─────────────────────────────────────────────

def check_missing_patterns(categories: List[CategoryReport]) -> List[dict]:
    """对照 KNOWN_IDIOMS 检查哪些大类完全未被检测到"""
    detected_cats = {c.category for c in categories if c.detected}
    missing = []
    for idiom_key, idiom_info in KNOWN_IDIOMS.items():
        if idiom_info["category"] not in detected_cats:
            missing.append({
                "category": idiom_info["category"],
                "suggestion": idiom_info["suggestion"],
            })
    return missing


# ── --compare 模式 ────────────────────────────────────────────────

def _parse_profile_file(filepath: str) -> dict:
    """解析 .mountainfish-profile.md 文件，提取核心统计数据"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    # 提取 JSON 块（profile 文件末尾包含结构化数据）
    m = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def compare_profiles(profile_paths: List[str]) -> dict:
    """对比多个 profile 文件，输出四象限对比"""
    profiles = []
    for p in profile_paths:
        data = _parse_profile_file(p)
        if data:
            profiles.append({"path": p, "data": data})

    if len(profiles) < 2:
        return {"error": "需要至少 2 个有效的 profile 文件进行对比", "profiles": len(profiles)}

    # 提取每个 profile 的检测到的类别名
    profile_cats = {}
    for p in profiles:
        cats = set()
        for cat in p["data"].get("categories", []):
            if cat.get("detected"):
                cats.add(cat["category"])
        profile_cats[p["path"]] = cats

    all_cats = sorted(set().union(*profile_cats.values()))
    n = len(profiles)

    common = []      # 所有项目共有
    unique = []      # 仅 1 个项目有
    divergent = []   # 部分有部分无（但不全有也不全无）
    all_missing = [] # 全部缺失
    for cat in all_cats:
        count = sum(1 for cats in profile_cats.values() if cat in cats)
        if count == n:
            common.append(cat)
        elif count == 1:
            owner = [p for p, cats in profile_cats.items() if cat in cats][0]
            unique.append({"category": cat, "owner": owner})
        elif count == 0:
            all_missing.append(cat)
        else:
            haves = [p for p, cats in profile_cats.items() if cat in cats]
            lacks = [p for p, cats in profile_cats.items() if cat not in cats]
            divergent.append({"category": cat, "have": haves, "lack": lacks})

    # 检查 KNOWN_IDIOMS 中所有类别都有哪些未出现
    known_cats = {v["category"] for v in KNOWN_IDIOMS.values()}
    all_missing = sorted(known_cats - set(all_cats))

    return {
        "profiles": [p["path"] for p in profiles],
        "n_profiles": len(profiles),
        "all_categories": all_cats,
        "common": common,
        "unique": unique,
        "divergent": divergent,
        "all_missing": all_missing,
    }


# ── 输出 ──────────────────────────────────────────────────────────

def print_terminal_report(result: ProfileResult) -> None:
    """打印终端人类可读报告"""
    source_label = {"own": "自己的项目", "reference": "别人的项目"}.get(result.source, result.source)
    print("\n" + "=" * 64)
    print("  Mountainfish Profiling Report")
    print(f"  项目: {result.directory}")
    print(f"  来源: {source_label}")
    print(f"  时间: {result.timestamp}")
    print("=" * 64)

    print(f"\n📁 文件: {result.files_scanned} 个 | 行数: {result.lines_scanned}")

    # 分层摘要
    print(f"\n── 项目分层 ──")
    layer_labels = {"driver": "驱动层", "app": "应用层", "util": "工具层", "unknown": "未分类"}
    for layer in ["driver", "app", "util", "unknown"]:
        count = result.layer_summary.get(layer, 0)
        label = layer_labels[layer]
        bar = "█" * min(count, 30)
        print(f"  {label:6s} {count:3d} 个文件  {bar}")

    # 各类惯用写法
    print(f"\n── 惯用写法画像 ──")
    for cat in result.categories:
        icon = "✅" if cat.detected else "❌"
        freq_info = ""
        if cat.detected:
            freq_info = (f"({cat.frequency} 处匹配, "
                        f"{cat.file_count} 个文件, "
                        f"分布: {dict(cat.by_pattern)})")
        print(f"\n{icon} {cat.category}")
        if freq_info:
            print(f"   {freq_info}")
        if cat.by_layer:
            print(f"   按层: {dict(cat.by_layer)}")
        if not cat.detected:
            print(f"   💡 {cat.suggestion}")

    # 缺失清单
    if result.missing_patterns:
        print(f"\n── ⚠️ 值得关注的缺失 ──")
        for mp in result.missing_patterns:
            print(f"  ❌ {mp['category']}")
            print(f"     📌 {mp['suggestion']}")
    else:
        print(f"\n── 缺失清单 ──")
        print(f"  ✅ 所有常见模式均已覆盖")

    # 建议的 integrate 命令
    print(f"\n── 建议的沉淀命令 ──")
    source_flag = f"--source {result.source} "
    suggested = 0
    for cat in result.categories:
        if cat.detected and cat.frequency >= 3:
            main_pattern = cat.by_pattern.most_common(1)[0][0] if cat.by_pattern else ""
            desc = f"{result.directory}: {cat.category} 使用 '{main_pattern}' 模式（{cat.frequency} 处）"
            print(f"  /mountainfish_integrate {source_flag}--type pattern --tier reference \\")
            print(f"    \"{desc}\"")
            suggested += 1
    if suggested == 0:
        print(f"  （检测到的模式样本不足，建议在更大项目中运行 profiling）")

    print("\n" + "=" * 64)


def write_profile_file(result: ProfileResult, output_path: str) -> None:
    """写入 .mountainfish-profile.md"""
    lines = []
    lines.append(f"# Mountainfish Profile: {result.directory}")
    lines.append("")
    lines.append(f"> 生成时间: {result.timestamp}")
    lines.append(f"> 来源: {'自己的项目' if result.source == 'own' else '别人的项目'}")
    lines.append(f"> 文件: {result.files_scanned} 个 | 行数: {result.lines_scanned}")
    lines.append("")
    lines.append("## 项目分层")
    lines.append("")
    lines.append("| 分层 | 文件数 |")
    lines.append("|------|--------|")
    layer_labels = {"driver": "驱动层", "app": "应用层", "util": "工具层", "unknown": "未分类"}
    for layer in ["driver", "app", "util", "unknown"]:
        count = result.layer_summary.get(layer, 0)
        lines.append(f"| {layer_labels[layer]} | {count} |")
    lines.append("")

    lines.append("## 惯用写法画像")
    lines.append("")
    for cat in result.categories:
        lines.append(f"### {cat.category}  `<!-- tier: reference -->`")
        lines.append("")
        if cat.detected:
            lines.append(f"**检测到**: 是 ({cat.frequency} 处匹配, {cat.file_count} 个文件)")
            lines.append("")
            lines.append(f"**主要模式**: {dict(cat.by_pattern.most_common(3)) if cat.by_pattern else 'N/A'}")
            lines.append("")
            if cat.by_layer:
                lines.append(f"**按层分布**: {dict(cat.by_layer)}")
                lines.append("")
        else:
            lines.append("**检测到**: 否")
            lines.append("")
            lines.append(f"**建议**: {cat.suggestion}")
            lines.append("")
        lines.append(f"<!-- type: pattern -->")
        lines.append(f"<!-- created: {result.timestamp} -->")
        lines.append(f"<!-- last-used: {result.timestamp} -->")
        lines.append("")
    lines.append("")

    # 缺失清单
    lines.append("## 缺失清单")
    lines.append("")
    for mp in result.missing_patterns:
        lines.append(f"- ❌ **{mp['category']}**: {mp['suggestion']}")
    lines.append("")

    # 内嵌 JSON（供 --compare 解析）
    lines.append("## 结构化数据")
    lines.append("")
    lines.append("```json")
    json_data = {
        "directory": result.directory,
        "timestamp": result.timestamp,
        "source": result.source,
        "files_scanned": result.files_scanned,
        "lines_scanned": result.lines_scanned,
        "layer_summary": result.layer_summary,
        "categories": [
            {
                "category": c.category,
                "detected": c.detected,
                "frequency": c.frequency,
                "file_count": c.file_count,
                "by_pattern": dict(c.by_pattern),
                "by_layer": dict(c.by_layer),
            }
            for c in result.categories
        ],
    }
    lines.append(json.dumps(json_data, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def print_compare_report(result: dict) -> None:
    """打印 --compare 终端报告"""
    print("\n" + "=" * 64)
    print("  Mountainfish Profile Compare")
    print(f"  对比 {result['n_profiles']} 个项目")
    print("=" * 64)

    print(f"\n📊 涵盖 {len(result['all_categories'])} 种惯用写法类别")

    if result["common"]:
        print(f"\n🟢 共性模式（所有项目共有，→ 指南候选）:")
        for cat in result["common"]:
            print(f"  ✅ {cat}")

    if result["unique"]:
        print(f"\n🔵 特有模式（仅 1 个项目，→ 参考层候选）:")
        for item in result["unique"]:
            print(f"  • {item['category']} → {os.path.basename(item['owner'])}")

    if result["divergent"]:
        print(f"\n🟡 分歧模式（部分有部分无，需人工裁决）:")
        for item in result["divergent"]:
            have_names = [os.path.basename(p) for p in item["have"]]
            lack_names = [os.path.basename(p) for p in item["lack"]]
            print(f"  ⚠️ {item['category']}: {have_names} 有 / {lack_names} 无")

    if result["all_missing"]:
        print(f"\n🔴 共同缺失（所有项目都未使用，→ 值得关注的空白）:")
        for cat in result["all_missing"]:
            suggestion = KNOWN_IDIOMS.get("", {}).get("suggestion", "")
            # Look up suggestion
            for k, v in KNOWN_IDIOMS.items():
                if v["category"] == cat:
                    print(f"  ❌ {cat}: {v['suggestion']}")
                    break
            else:
                print(f"  ❌ {cat}")

    print("\n" + "=" * 64)


# ── CLI ───────────────────────────────────────────────────────────

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

    json_output = "--json" in sys.argv

    # 解析 --source
    source = "own"
    for i, arg in enumerate(sys.argv):
        if arg == "--source" and i + 1 < len(sys.argv):
            val = sys.argv[i + 1]
            if val in ("own", "reference"):
                source = val
            else:
                print(f"[WARN] 未知 --source 值: {val}，使用默认值 'own'", file=sys.stderr)
            break

    # --compare 模式
    if "--compare" in sys.argv:
        # 收集 compare 后面的所有 profile 文件路径
        profile_paths = []
        capture = False
        for arg in sys.argv[1:]:
            if arg == "--compare":
                capture = True
            elif arg == "--json":
                continue
            elif capture and not arg.startswith("--"):
                profile_paths.append(arg)

        if len(profile_paths) < 2:
            print("[ERROR] --compare 需要至少 2 个 .mountainfish-profile.md 文件路径",
                  file=sys.stderr)
            sys.exit(1)

        result = compare_profiles(profile_paths)
        if json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_compare_report(result)
        sys.exit(0)

    # 单项目分析模式
    if len(sys.argv) < 2:
        print("用法: python profiler.py <源码目录> [选项]", file=sys.stderr)
        print("选项:", file=sys.stderr)
        print("  --json             JSON 输出", file=sys.stderr)
        print("  --output <path>    指定 profile 文件输出路径", file=sys.stderr)
        print("  --compare a.md b.md  跨项目对比", file=sys.stderr)
        sys.exit(1)

    directory = sys.argv[1]
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"[ERROR] 目录不存在: {directory}", file=sys.stderr)
        sys.exit(1)

    # 确定输出路径
    output_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            break
    if output_path is None:
        output_path = str(dir_path / ".mountainfish-profile.md")

    # Phase 1: 文件分类
    classifier = ProjectClassifier(directory)
    classifications = classifier.classify()
    if not classifications:
        print(f"[WARN] 未找到 C/C++ 源文件", file=sys.stderr)
        sys.exit(0)

    # 统计
    files_scanned = len(classifications)
    lines_scanned = 0
    for clf in classifications:
        try:
            with open(dir_path / clf.path, "r", encoding="utf-8", errors="ignore") as f:
                lines_scanned += sum(1 for _ in f)
        except Exception:
            pass

    layer_summary = dict(Counter(c.layer for c in classifications))

    # Phase 2: 惯用写法检测
    detector = IdiomDetector(directory, classifications)
    categories = detector.detect_all()

    # Phase 3: 缺失清单
    missing = check_missing_patterns(categories)

    result = ProfileResult(
        directory=str(dir_path.resolve()),
        timestamp=datetime.now().strftime("%Y-%m-%d"),
        source=source,
        files_scanned=files_scanned,
        lines_scanned=lines_scanned,
        layer_summary=layer_summary,
        categories=categories,
        missing_patterns=missing,
    )

    if json_output:
        # 简化的 JSON 输出（仅核心数据）
        json_data = {
            "directory": result.directory,
            "timestamp": result.timestamp,
            "source": result.source,
            "files_scanned": result.files_scanned,
            "lines_scanned": result.lines_scanned,
            "layer_summary": result.layer_summary,
            "categories": [
                {
                    "category": c.category,
                    "detected": c.detected,
                    "frequency": c.frequency,
                    "file_count": c.file_count,
                    "by_pattern": dict(c.by_pattern),
                    "by_layer": dict(c.by_layer),
                }
                for c in result.categories
            ],
            "missing_patterns": result.missing_patterns,
        }
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
    else:
        print_terminal_report(result)

    # 写入 profile 文件
    write_profile_file(result, output_path)
    print(f"[OK] Profile 已写入: {output_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
