#!/usr/bin/env python3
"""Enhance agent-series (214-254) infographic prompts and build baoyu-image-gen batch file."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SKILL = Path.home() / ".codex" / "skills" / "baoyu-infographic" / "references"

STYLE_BLOCK = """Style Guidelines (hand-drawn-edu — MUST follow strictly):
- Background: Warm cream (#F5F0E8) with subtle paper grain texture
- Macaron pastel rounded cards as distinct information zones (Mint #B5E5CF, Blue #A8D8EA, Lavender #D5C6E0, Peach #FFD5C2)
- Hand-drawn wavy connection lines and arrows with slight wobble — NO perfect geometry
- Simple stick-figure characters and cartoon icons (clipboard, lock, checkmark, lightbulb) in each zone
- Doodle decorations: small stars, underlines, spirals, sparkles
- Hand-lettered Simplified Chinese text, legible but organic (not mechanical)
- Generous whitespace between zones; maximum 4 macaron colors per image
- Bold centered takeaway quote or footer banner at bottom
- Include at least one stick figure per major section
- NO flat vector icons, NO corporate aesthetic, NO pure white background"""

LAYOUT_FILES = {
    "binary-comparison": "layouts/binary-comparison.md",
    "linear-progression": "layouts/linear-progression.md",
    "bento-grid": "layouts/bento-grid.md",
    "hub-spoke": "layouts/hub-spoke.md",
    "comparison-matrix": "layouts/comparison-matrix.md",
    "flow-left-right": "layouts/linear-progression.md",
    "flowchart": "layouts/linear-progression.md",
}


def load_layout_guidelines(layout: str) -> str:
    rel = LAYOUT_FILES.get(layout, f"layouts/{layout}.md")
    path = SKILL / rel
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"Layout: {layout}"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2].lstrip("\n")
    return meta, body


def enhance_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    layout = meta.get("layout", "bento-grid")
    layout_guide = load_layout_guidelines(layout)
    title_m = re.search(r"Title:\s*(.+)", body)
    title = title_m.group(1).strip() if title_m else path.stem

    enhanced = f"""---
layout: {layout}
style: hand-drawn-edu
aspect_ratio: 16:9
language: zh
---

Create a professional educational infographic.
- Type: Infographic
- Layout: {layout}
- Style: hand-drawn-edu
- Aspect Ratio: 16:9
- Language: zh (Simplified Chinese)

## Layout Guidelines

{layout_guide}

## Style Guidelines

{STYLE_BLOCK}

---

{body.strip()}

IMPORTANT: Render ALL text in Simplified Chinese with hand-drawn lettering. Fill the canvas richly with illustrations, icons, and stick figures — do NOT leave large empty colored boxes with tiny text in the corner.
"""
    return enhanced


def slug_from_doc(num: int) -> str | None:
    arts = sorted(DOCS.glob(f"{num}.*-tutorial.md"))
    if not arts:
        return None
    name = arts[0].name
    return re.sub(r"-tutorial\.md$", "", re.sub(r"^\d+\.", "", name))


def collect_jobs() -> list[dict]:
    jobs: list[dict] = []
    for num in range(214, 255):
        slug = slug_from_doc(num)
        if not slug:
            continue
        prompt_dir = ROOT / "image" / slug / "prompts"
        if not prompt_dir.is_dir():
            continue
        for p in sorted(prompt_dir.glob("*.md")):
            png = p.parent.parent / f"{p.stem}.png"
            jobs.append({"num": num, "slug": slug, "prompt": p, "png": png})
    return jobs


def backup_png(png: Path) -> None:
    if not png.exists():
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = png.with_name(f"{png.stem}-backup-{ts}{png.suffix}")
    shutil.move(str(png), str(backup))
    print(f"backup {png.name} -> {backup.name}")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--enhance-prompts", action="store_true", help="Rewrite prompts with full style guidelines")
    ap.add_argument("--write-batch", action="store_true", help="Write scripts/_agent_batch_214_254.json")
    ap.add_argument("--backup", action="store_true", help="Backup existing PNGs before regen")
    ap.add_argument("--list", action="store_true", help="List job count")
    args = ap.parse_args()

    jobs = collect_jobs()
    if args.list or not any([args.enhance_prompts, args.write_batch, args.backup]):
        print(f"jobs: {len(jobs)} images across {len({j['slug'] for j in jobs})} slugs")
        return

    if args.enhance_prompts:
        for job in jobs:
            p: Path = job["prompt"]
            enhanced = enhance_prompt(p)
            backup = p.with_name(f"{p.stem}-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
            if not any(p.parent.glob(f"{p.stem}-backup-*.md")):
                shutil.copy2(p, backup)
            p.write_text(enhanced, encoding="utf-8")
        print(f"enhanced {len(jobs)} prompts")

    if args.backup:
        for job in jobs:
            backup_png(job["png"])

    if args.write_batch:
        tasks = []
        for job in jobs:
            tasks.append(
                {
                    "id": f"{job['slug']}/{job['png'].name}",
                    "promptFiles": [str(job["prompt"].relative_to(ROOT))],
                    "image": str(job["png"].relative_to(ROOT)),
                    "ar": "16:9",
                    "quality": "2k",
                }
            )
        batch = {"jobs": 4, "tasks": tasks}
        out = ROOT / "scripts" / "_agent_batch_214_254.json"
        out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {out} ({len(tasks)} tasks)")


if __name__ == "__main__":
    main()
