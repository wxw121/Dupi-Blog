#!/usr/bin/env python3
"""Export compact image-generation manifest from enhanced agent prompts."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "scripts" / "_agent_batch_214_254.json"


def compact_prompt(text: str) -> str:
    """Extract infographic body after guidelines; prepend style prefix."""
    # Body starts after the final '---' separator following Style Guidelines
    marker = "\n---\n\n"
    idx = text.rfind(marker)
    body = text[idx + len(marker) :] if idx >= 0 else text
    body = re.sub(r"\nIMPORTANT:.*", "", body, flags=re.S).strip()
    style = (
        "hand-drawn-edu infographic, 16:9 landscape, warm cream paper #F5F0E8, "
        "macaron pastel cards, hand-drawn wavy lines, stick figures, doodle stars/sparkles, "
        "Simplified Chinese hand-lettered text, rich illustrations filling the canvas, "
        "footer takeaway banner. "
    )
    return style + body[:3500]


def main() -> None:
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    manifest = []
    for task in batch["tasks"]:
        prompt_path = ROOT / task["promptFiles"][0]
        text = prompt_path.read_text(encoding="utf-8")
        manifest.append(
            {
                "id": task["id"],
                "image": task["image"],
                "description": compact_prompt(text),
            }
        )
    out = ROOT / "scripts" / "_agent_gen_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(manifest)} entries -> {out}")


if __name__ == "__main__":
    main()
