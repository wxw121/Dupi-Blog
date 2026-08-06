#!/usr/bin/env python3
"""Report AI vs placeholder infographic regeneration status for agent series 214-254."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMG = ROOT / "image"
THRESHOLD = 200_000  # bytes; AI images are typically >2MB, Pillow placeholders <100KB


def main() -> None:
    ai: list[str] = []
    placeholder: list[str] = []
    for doc in sorted(DOCS.glob("*.md")):
        m = re.match(r"^(\d+)\.", doc.name)
        if not m or not (214 <= int(m.group(1)) <= 254):
            continue
        slug = re.sub(r"-tutorial\.md$", "", re.sub(r"^\d+\.", "", doc.name))
        d = IMG / slug
        if not d.is_dir():
            continue
        for png in sorted(d.glob("*.png")):
            if "backup" in png.name:
                continue
            rel = f"{slug}/{png.name}"
            if png.stat().st_size >= THRESHOLD:
                ai.append(rel)
            else:
                placeholder.append(rel)
    prog_path = ROOT / "scripts" / "_agent_gen_progress.json"
    prog = json.loads(prog_path.read_text(encoding="utf-8")) if prog_path.exists() else {"completed": []}
    print(f"AI-regenerated: {len(ai)} / {len(ai)+len(placeholder)}")
    print(f"Placeholder remaining: {len(placeholder)}")
    print(f"Progress file: {len(prog.get('completed', []))} marked complete")
    if placeholder[:5]:
        print("Next placeholders:", placeholder[:5])


if __name__ == "__main__":
    main()
