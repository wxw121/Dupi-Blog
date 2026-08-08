#!/usr/bin/env python3
"""Fix glossary gaps identified by body-term scan."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_term_glossary_gaps import GLOSSARY_GAP_FIX  # noqa: E402


def doc_path(n: int) -> Path:
    return list(DOCS.glob(f"{n}.*-tutorial.md"))[0]


def format_entry(term: str, en: str, defn: str, tongsu: str) -> str:
    return f"**{term}**（{en}）：{defn}\n通俗说：{tongsu}。"


def apply_doc(n: int) -> bool:
    items = GLOSSARY_GAP_FIX.get(n)
    if not items:
        return False
    p = doc_path(n)
    text = p.read_text(encoding="utf-8")
    marker = "### 核心术语（本篇首次出现）"
    if marker not in text:
        return False
    head, rest = text.split(marker, 1)
    section, tail = rest.split("\n---\n", 1)
    additions = []
    for term, en, defn, tongsu in items:
        if re.search(rf"\*\*{re.escape(term)}\*\*", section):
            continue
        additions.append(format_entry(term, en, defn, tongsu))
    if not additions:
        return False
    new_section = section.rstrip() + "\n" + "\n".join(additions) + "\n"
    p.write_text(head + marker + new_section + "---\n" + tail, encoding="utf-8")
    return True


def main() -> int:
    changed = [n for n in GLOSSARY_GAP_FIX if apply_doc(n)]
    print(f"Glossary gaps fixed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
