#!/usr/bin/env python3
"""Scan Agent tutorials 214-254 for undefined terms at first body occurrence.

Usage:
  python scripts/scan_body_term_first_use.py
  python scripts/scan_body_term_first_use.py --write-report scripts/reports/body-term-scan.md
  python scripts/scan_body_term_first_use.py --include-reuse   # show 轻微（沿用前驱篇）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_term_lexicon import ALIASES, SERIES_REUSE_OK, SKIP_TERMS, TERM_LEXICON  # noqa: E402

SERIES = list(range(214, 255))

GLOSSARY_TERM_RE = re.compile(r"\*\*([^*]+)\*\*（")
HOWTO_ROW_RE = re.compile(r"^\| ([^|]+) \|", re.M)
CODE_FENCE = re.compile(r"```[\s\S]*?```", re.M)
INLINE_CODE = re.compile(r"`[^`]+`")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
TOC_LINE = re.compile(r"^\s*\d+\.\s+\[")
SKIP_SECTIONS = {"目录", "和 RAG / 后端 / 前端的关系"}


@dataclass
class Finding:
    doc: int
    term: str
    line: int
    section: str
    severity: str
    message: str
    snippet: str


def doc_path(n: int) -> Path:
    return list(DOCS.glob(f"{n}.*-tutorial.md"))[0]


def canonical(term: str) -> str:
    return ALIASES.get(term, term)


def parse_glossary_terms(text: str) -> set[str]:
    """All **term**（ from front matter (before first ---)."""
    front = text.split("\n---\n", 1)[0]
    terms: set[str] = set()
    for m in GLOSSARY_TERM_RE.finditer(front):
        t = m.group(1).strip()
        terms.add(t)
        terms.add(canonical(t))
    return terms


def body_prose_lines(text: str) -> tuple[list[str], list[int]]:
    """Return prose lines and their 1-based line numbers in full file."""
    _, body, body_start = split_front_body(text)
    lines = body.splitlines()
    out_lines: list[str] = []
    out_nums: list[int] = []
    in_code = False
    skip_section = False
    current_sec = ""

    for i, ln in enumerate(lines):
        abs_line = body_start + i
        if ln.startswith("## "):
            current_sec = ln[3:].strip()
            skip_section = any(s in current_sec for s in SKIP_SECTIONS)
            continue
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or skip_section:
            continue
        if TOC_LINE.match(ln):
            continue
        if ln.strip().startswith("|") and "---" in ln:
            continue
        cleaned = IMAGE.sub(" ", ln)
        cleaned = INLINE_CODE.sub(" ", cleaned)
        out_lines.append(cleaned)
        out_nums.append(abs_line)
    return out_lines, out_nums


def split_front_body(text: str) -> tuple[str, str, int]:
    parts = text.split("\n---\n", 1)
    if len(parts) == 2:
        front, body = parts[0], parts[1]
        body_start = parts[0].count("\n") + 2
    else:
        front, body = "", text
        body_start = 1
    return front, body, body_start


def explained_in_early_body(body: str) -> set[str]:
    early = body[:3500]
    terms: set[str] = set()
    for m in GLOSSARY_TERM_RE.finditer(early):
        terms.add(canonical(m.group(1).strip()))
    if "### 本节术语速查" in early:
        block = early.split("### 本节术语速查", 1)[1]
        for m in HOWTO_ROW_RE.finditer(block[:1200]):
            cell = m.group(1).strip()
            if cell not in ("术语", "------") and cell:
                terms.add(canonical(cell))
    return terms


def section_name(lines: list[str], idx: int, line_nums: list[int]) -> str:
    # walk back in full file not available — use stored current from scan
    return "?"


def is_explained_inline(line: str, term: str) -> bool:
    if re.search(rf"\*\*{re.escape(term)}\*\*（", line):
        return True
    if re.search(rf"{re.escape(term)}（[^）]{{2,50}}）", line):
        return True
    return False


def scan_doc(n: int, include_reuse: bool) -> list[Finding]:
    text = doc_path(n).read_text(encoding="utf-8")
    explained = parse_glossary_terms(text)
    explained |= explained_in_early_body(split_front_body(text)[1])

    prose_lines, line_nums = body_prose_lines(text)
    prose = "\n".join(prose_lines)

    search: dict[str, str] = {}
    for term in TERM_LEXICON:
        search[term] = term
    for alias, canon in ALIASES.items():
        search[alias] = canon

    findings: list[Finding] = []
    seen: set[str] = set()

    for term, canon in sorted(search.items(), key=lambda x: -len(x[0])):
        if term in SKIP_TERMS or canon in SKIP_TERMS or canon in seen:
            continue
        intro_doc = TERM_LEXICON.get(canon, ("", "", "", 999))[3]
        if intro_doc > n:
            continue

        if re.match(r"^[A-Za-z_./-]+$", term):
            pat = re.compile(rf"(?<![A-Za-z0-9_./-]){re.escape(term)}(?![A-Za-z0-9_./-])")
        else:
            pat = re.compile(re.escape(term))

        m = pat.search(prose)
        if not m:
            continue
        seen.add(canon)

        line_idx = prose[: m.start()].count("\n")
        line_no = line_nums[line_idx] if line_idx < len(line_nums) else 0
        snippet = prose_lines[line_idx].strip()[:96] if line_idx < len(prose_lines) else ""

        if canon in explained:
            continue
        if is_explained_inline(prose_lines[line_idx], term) or is_explained_inline(prose_lines[line_idx], canon):
            continue

        if intro_doc < n and canon in SERIES_REUSE_OK:
            continue

        if intro_doc < n:
            if not include_reuse:
                continue
            sev, msg = "轻微", f"沿用 {intro_doc} 篇术语，本篇文首未列（可接受或补「沿用术语」行）"
        else:
            sev, msg = "中等", f"本篇应解释的核心术语「{canon}」在正文首现无文首双轨"

        findings.append(
            Finding(n, canon, line_no, "?", sev, msg, snippet)
        )

    return findings


def scan_all(include_reuse: bool) -> list[Finding]:
    out: list[Finding] = []
    for n in SERIES:
        out.extend(scan_doc(n, include_reuse))
    return out


def format_report(findings: list[Finding]) -> str:
    by_sev: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1

    lines = [
        "# 正文首现术语扫描报告（214–254）",
        "",
        f"合计 **{len(findings)}** 处 | "
        + " | ".join(f"{k} {v}" for k, v in sorted(by_sev.items())),
        "",
        "## 判定规则",
        "",
        "1. 扫描范围：`---` 后正文，**排除** `## 目录`、`和 RAG/后端/前端的关系`、代码块、TOC 行",
        "2. 已解释：文首 `### 核心术语` 或 §怎么做 术语速查表含该词",
        "3. **中等**：`introduced_in == 本篇` 但文首未解释",
        "4. **轻微**（默认不输出）：前驱篇已引入；加 `--include-reuse` 可见",
        "",
        "## 修复建议",
        "",
        "- 中等：`python scripts/fix_glossary_gaps.py` 或手动补文首术语块",
        "- 轻微：可在文首加 `**沿用术语：** RAG、Agent…（见 214）`",
        "",
    ]

    if not findings:
        lines.append("无中等问题；词表术语均已在本篇文首或速查表中解释。")
        return "\n".join(lines) + "\n"

    cur = None
    for f in sorted(findings, key=lambda x: (x.severity != "中等", x.doc, x.line)):
        if f.doc != cur:
            cur = f.doc
            lines.extend(["", f"## {f.doc} `{doc_path(f.doc).name}`", ""])
        lines.append(f"- **[{f.severity}]** `{f.term}` @ L{f.line} — {f.message}")
        if f.snippet:
            lines.append(f"  - `{f.snippet}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--include-reuse", action="store_true")
    parser.add_argument("--write-report", type=str, default="")
    parser.add_argument("start", nargs="?", type=int, default=214)
    parser.add_argument("end", nargs="?", type=int, default=254)
    args = parser.parse_args()

    global SERIES
    SERIES = list(range(args.start, args.end + 1))
    findings = scan_all(args.include_reuse)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        report = format_report(findings)
        if args.write_report:
            out = Path(args.write_report)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report, encoding="utf-8")
            print(f"Wrote {out} ({len(findings)} findings)", file=sys.stderr)
        else:
            sys.stdout.buffer.write(report.encode("utf-8"))

    return 1 if any(f.severity == "中等" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
