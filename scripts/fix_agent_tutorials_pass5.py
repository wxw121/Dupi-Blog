#!/usr/bin/env python3
"""Pass 5: series rename links, 02-flow 237/239/240, glossary ≥3, §怎么做术语表."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
POSTS = ROOT / "src/posts/ai-ml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_tutorial_pass5_data import (  # noqa: E402
    FLOW_02_INSERT,
    GLOSSARY_APPEND,
    HOWTO_TERM_TABLE,
    SERIES_LINK_LABEL,
    SERIES_NEW,
    SERIES_OLD,
    TONGSU_SHORT,
)

SERIES = list(range(214, 255))


def doc_path(n: int) -> Path:
    return list(DOCS.glob(f"{n}.*-tutorial.md"))[0]


def format_term(term: str, english: str, defn: str) -> str:
    plain = TONGSU_SHORT.get(term, defn.split("，")[0] if "，" in defn else defn[:28])
    return f"**{term}**（{english}）：{defn}\n通俗说：{plain}。"


def refresh_glossary_terms(text: str, n: int) -> str:
    """Rewrite appended terms with correct 通俗说 (idempotent)."""
    items = GLOSSARY_APPEND.get(n)
    if not items:
        return text
    for term, en, defn in items:
        block = format_term(term, en, defn)
        pat = rf"\*\*{re.escape(term)}\*\*（[^）]+）：[^\n]+\n通俗说：[^\n]+\n"
        if re.search(pat, text):
            text = re.sub(pat, block + "\n", text, count=1)
    text = re.sub(r"。\n通俗说：[^。]+。。\n", lambda m: m.group(0).replace("。。", "。"), text)
    text = text.replace("。。", "。")
    return text


def append_glossary(text: str, n: int) -> str:
    items = GLOSSARY_APPEND.get(n)
    if not items:
        return text
    block_start = "### 核心术语（本篇首次出现）"
    if block_start not in text:
        return text
    head, rest = text.split(block_start, 1)
    section, tail = rest.split("\n---\n", 1) if "\n---\n" in rest else (rest, "")
    additions = []
    for term, en, tongsu in items:
        if term in section or f"**{term}**" in section:
            continue
        additions.append(format_term(term, en, tongsu))
    if not additions:
        return text
    new_section = section.rstrip() + "\n" + "\n".join(additions) + "\n"
    if tail:
        return head + block_start + new_section + "---\n" + tail
    return head + block_start + new_section


def insert_flow_02(text: str, n: int) -> str:
    block = FLOW_02_INSERT.get(n)
    if not block:
        return text
    if "02-" in text and "flow" in text:
        return text
    anchor = "## 怎么做"
    m = re.search(r"^## 怎么做[^\n]*\n", text, re.M)
    if not m:
        return text
    insert_at = m.end()
    return text[:insert_at] + block.strip() + "\n\n" + text[insert_at:]


def insert_howto_table(text: str, n: int) -> str:
    table = HOWTO_TERM_TABLE.get(n)
    if not table:
        return text
    if "### 本节术语速查" in text:
        return text
    m = re.search(r"^## 怎么做[^\n]*\n", text, re.M)
    if not m:
        return text
    start = m.end()
    sub = text[start:]
    fm = re.search(
        r"!\[[^\]]*\]\([^)]*02-[^)]*flow[^)]*\)\n对照上图：[^\n]+\n",
        sub,
    )
    insert_at = start + fm.end() if fm else start
    return text[:insert_at] + table.strip() + "\n\n" + text[insert_at:]


def update_series_links(text: str) -> str:
    text = text.replace(SERIES_OLD, SERIES_NEW)
    text = text.replace("agent-rag-series-239-248", "agent-rag-series-238-254")
    text = re.sub(
        r"Agent/RAG 工程系列 239–248",
        SERIES_LINK_LABEL,
        text,
    )
    text = re.sub(
        r"Agent/RAG 工程系列 239-248",
        SERIES_LINK_LABEL,
        text,
    )
    return text


def add_series_footer_239_plus(text: str, n: int) -> str:
    if n < 239 or n > 249:
        return text
    if "**系列导读：**" in text or "agent-rag-series-238-254" in text.split("## 目录")[0]:
        return text
    marker = "**环境要求：**"
    if marker not in text:
        return text
    footer = (
        f"\n> **系列导读：** [{SERIES_LINK_LABEL}](../src/posts/ai-ml/{SERIES_NEW}) · "
        f"[`examples/rag-agent-lab`](../examples/rag-agent-lab/)\n"
    )
    return text.replace(marker, footer + "\n" + marker, 1)


def process_one(n: int) -> bool:
    p = doc_path(n)
    original = p.read_text(encoding="utf-8")
    text = original
    text = update_series_links(text)
    text = append_glossary(text, n)
    text = refresh_glossary_terms(text, n)
    text = insert_flow_02(text, n)
    text = insert_howto_table(text, n)
    text = add_series_footer_239_plus(text, n)
    if text != original:
        p.write_text(text, encoding="utf-8")
        return True
    return False


def patch_repo_files() -> list[str]:
    changed: list[str] = []
    targets = [
        ROOT / "examples/rag-agent-lab/README.md",
        ROOT / "scripts/fix_agent_tutorials.py",
        POSTS / "239-query-planning-rag-agent.md",
    ]
    for p in targets:
        if not p.exists():
            continue
        old = p.read_text(encoding="utf-8")
        new = update_series_links(old)
        if new != old:
            p.write_text(new, encoding="utf-8")
            changed.append(str(p.relative_to(ROOT)))
    return changed


def main() -> int:
    changed_docs = [n for n in SERIES if process_one(n)]
    repo = patch_repo_files()
    print(f"Pass 5: updated {len(changed_docs)} tutorials: {changed_docs}")
    if repo:
        print(f"Pass 5: updated repo files: {repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
