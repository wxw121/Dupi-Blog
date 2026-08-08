#!/usr/bin/env python3
"""Spot-check audit for Agent tutorials 214-254 (beginner-tech-blog)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

ROADMAP_SECTIONS = [
    "你会学到什么",
    "它解决什么问题",
    "最小示例",
    "工程化版本",
    "常见失败模式",
    "什么时候不要这么做",
    "生产环境注意事项",
    "如何观测和评测",
    "面试怎么讲",
    "下一步",
]
NARRATIVE_OK = {237, 238, 239, 240}  # use 是什么/怎么做 + injected anchors

OPTIONAL_READ_EXPECTED = {228, 229, 230, 232, 233, 234, 235, 236}


def doc_path(n: int) -> Path:
    return list(DOCS.glob(f"{n}.*-tutorial.md"))[0]


def audit_one(n: int) -> list[tuple[str, str, str]]:
    """Return list of (severity, location, message)."""
    p = doc_path(n)
    t = p.read_text(encoding="utf-8")
    issues: list[tuple[str, str, str]] = []

    if "**档位：**" not in t:
        issues.append(("严重", "文首", "缺少档位"))
    if "**本文边界：**" not in t:
        issues.append(("严重", "文首", "缺少本文边界"))
    elif "前驱" not in t.split("**本文边界：**", 1)[1].split("\n", 1)[0]:
        issues.append(("中等", "文首", "本文边界未链前驱篇"))
    if "通俗说：" not in t:
        issues.append(("严重", "文首", "缺少通俗说术语"))
    if "对照上图" not in t:
        issues.append(("严重", "配图", "缺少图后收束"))

    imgs = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", t))
    conclusions = len(re.findall(r"对照上图", t))
    if imgs > conclusions:
        issues.append(("中等", "配图", f"图片 {imgs} 张，收束 {conclusions} 处"))

    if n in OPTIONAL_READ_EXPECTED and "### 要不要读" not in t:
        issues.append(("中等", "文首", "进阶篇缺少「要不要读」"))

    # 正文首现术语（中等=0 为通过）
    try:
        from scan_body_term_first_use import scan_doc

        medium = [f for f in scan_doc(n, include_reuse=False) if f.severity == "中等"]
        if medium:
            terms = ", ".join(f.term for f in medium[:3])
            issues.append(("中等", "术语", f"正文首现未解释: {terms}"))
    except Exception:
        pass

    if n not in NARRATIVE_OK:
        missing = [s for s in ROADMAP_SECTIONS if f"## {s}" not in t]
        if missing:
            issues.append(("中等", "结构", f"缺 Roadmap 节: {', '.join(missing[:3])}{'…' if len(missing)>3 else ''}"))

    if "打印各 Level 或 demo" in t and n not in (214,):
        issues.append(("轻微", "§最小示例", "预期输出文案仍为 Level 0 模板"))

    if re.search(r"\*\*动手路径：\*\*[^\n]+\n###", t):
        issues.append(("轻微", "文首", "动手路径与术语块之间缺空行"))

    demos = len(re.findall(r"def demo_\w+", t))
    mains = len(re.findall(r'if __name__ == "__main__"', t))
    if demos > 0 and mains == 0:
        issues.append(("中等", "代码", f"有 {demos} 个 demo_* 但无 __main__"))

    if "先抓住「要解决什么矛盾」" in t:
        issues.append(("轻微", "配图", "01 图收束仍为通用模板句"))
    if "建立本专题直觉" in t:
        issues.append(("中等", "配图", "01 图收束仍为模板句"))
    if "与下文 §最小示例 代码逐一对应" in t:
        issues.append(("中等", "配图", "02-flow 收束仍为模板句"))
    if "把全篇概念串成一张地图" in t:
        issues.append(("中等", "配图", "03 概念地图收束仍为模板句"))

    if n >= 250 and "## 综合实战" not in t:
        issues.append(("中等", "Part 7", "缺少 §综合实战"))

    if t.count("通俗说：") < 3:
        issues.append(("中等", "文首", f"通俗说仅 {t.count('通俗说：')} 处，建议 ≥3"))

    if n in {237, 239, 240} and not re.search(r"02-[^)]*flow", t):
        issues.append(("中等", "配图", "缺少 02-flow 引用"))

    for m in re.finditer(r"\]\(\.\./src/posts/ai-ml/([^)]+)\)", t):
        if not (ROOT / "src/posts/ai-ml" / m.group(1)).exists():
            issues.append(("严重", "链接", f"博客版不存在: {m.group(1)}"))

    return issues


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 214
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 254
    all_issues: dict[int, list] = {}
    sev_count = {"严重": 0, "中等": 0, "轻微": 0}
    for n in range(start, end + 1):
        try:
            iss = audit_one(n)
        except IndexError:
            iss = [("严重", "-", "文件不存在")]
        if iss:
            all_issues[n] = iss
            for s, _, _ in iss:
                sev_count[s] += 1

    print(f"# 抽检报告 {start}–{end}")
    print(f"有问题篇目: {len(all_issues)}/{end-start+1}")
    print(f"严重 {sev_count['严重']} | 中等 {sev_count['中等']} | 轻微 {sev_count['轻微']}\n")
    for n, iss in sorted(all_issues.items()):
        name = doc_path(n).name
        print(f"## {n} {name}")
        for sev, loc, msg in iss:
            print(f"  - [{sev}] {loc}: {msg}")
        print()
    clean = [n for n in range(start, end + 1) if n not in all_issues]
    if clean:
        print(f"[OK] 无问题抽检通过: {clean}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
