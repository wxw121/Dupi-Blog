#!/usr/bin/env python3
"""Insert **本文边界：** into Agent tutorials 214-254 from agent_tutorial_config.BOUNDARY."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from agent_tutorial_config import BOUNDARY, SERIES_DOCS

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def doc_path(num: int) -> Path:
    return list(DOCS.glob(f"{num}.*-tutorial.md"))[0]


def insert_boundary(text: str, boundary: str) -> str:
    if "**本文边界：**" in text:
        # Update existing if different (optional: skip)
        return re.sub(
            r"\*\*本文边界：\*\*[^\n]*",
            f"**本文边界：** {boundary}",
            text,
            count=1,
        )
    # Insert after **档位：** line
    m = re.search(r"(\*\*档位：\*\*[^\n]*\n)", text)
    if not m:
        return text
    return text[: m.end()] + f"**本文边界：** {boundary}\n" + text[m.end() :]


def main() -> int:
    nums = SERIES_DOCS
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        nums = [int(sys.argv[1])]
    for n in nums:
        if n not in BOUNDARY:
            print(f"skip {n}: no boundary in config")
            continue
        p = doc_path(n)
        t = p.read_text(encoding="utf-8")
        new = insert_boundary(t, BOUNDARY[n])
        if new != t:
            p.write_text(new, encoding="utf-8")
            print(f"OK {n} {p.name}")
        else:
            print(f"unchanged {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
