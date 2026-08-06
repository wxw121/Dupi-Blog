#!/usr/bin/env python3
"""DEPRECATED: Pillow placeholder renderer — NOT real hand-drawn-edu style.

Use baoyu-image-gen batch or Cursor GenerateImage instead.
See scripts/regen_agent_infographics_214_254.py and scripts/README.md.
"""
from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1536, 1024
BG = "#F5F0E8"
COLORS = ["#B5E5CF", "#A8D8EA", "#D5C6E0", "#FFD5C2", "#FFE5A0", "#C9E4DE"]
INK = "#3D3D3D"
MUTED = "#6B6B6B"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def parse_prompt(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    layout = "linear-progression"
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta, body = parts[1], parts[2]
            m = re.search(r"layout:\s*(\S+)", meta)
            if m:
                layout = m.group(1)
            text = body
    title = ""
    m = re.search(r"Title:\s*(.+)", text)
    if m:
        title = m.group(1).strip()
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("Create ") or s.startswith("Layout:") or s.startswith("Style:"):
            continue
        if s.startswith("Title:") or s.startswith("Footer:") or s.startswith("All text"):
            continue
        if s.startswith("Note:"):
            lines.append(s.replace("Note:", "注：").strip())
            continue
        lines.append(s)
    return {"layout": layout, "title": title, "lines": lines}


def wrap_lines(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    out: list[str] = []
    for para in text.split("\n"):
        if not para.strip():
            continue
        avg = max(1, int(max_width / max(font.size, 1)))
        out.extend(textwrap.wrap(para, width=avg) or [para])
    return out


def draw_wavy_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=outline, width=3)
    draw.line([(x0 + 8, y1 - 6), (x1 - 12, y1 - 10)], fill=outline, width=2)
    draw.line([(x0 + 10, y0 + 8), (x1 - 8, y0 + 12)], fill=outline, width=2)


def draw_title(draw: ImageDraw.ImageDraw, title: str, y: int = 36) -> int:
    font = load_font(42, bold=True)
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), title, font=font, fill=INK)
    return y + 70


def draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    lines: list[str],
    color: str,
    title: str | None = None,
) -> None:
    draw_wavy_rect(draw, box, color, INK)
    x0, y0, x1, y1 = box
    pad = 24
    tf = load_font(28, bold=True)
    bf = load_font(24)
    cy = y0 + pad
    if title:
        draw.text((x0 + pad, cy), title, font=tf, fill=INK)
        cy += 38
    max_w = x1 - x0 - pad * 2
    for line in lines:
        for wl in wrap_lines(line, bf, max_w):
            if cy > y1 - pad - 24:
                return
            draw.text((x0 + pad, cy), wl, font=bf, fill=INK)
            cy += 30


def draw_arrow_h(draw: ImageDraw.ImageDraw, x0: int, y: int, x1: int) -> None:
    draw.line([(x0, y), (x1 - 14, y)], fill=MUTED, width=4)
    draw.polygon([(x1, y), (x1 - 16, y - 8), (x1 - 16, y + 8)], fill=MUTED)


def render_binary_comparison(draw: ImageDraw.ImageDraw, spec: dict) -> None:
    y = draw_title(draw, spec["title"] or "对照图")
    mid = W // 2
    gap = 40
    box_h = H - y - 80
    left_lines, right_lines = [], []
    mode = "left"
    for line in spec["lines"]:
        if line.upper().startswith("LEFT") or line.startswith("左"):
            mode = "left"
            line = re.sub(r"^(LEFT|左)[：:]\s*", "", line)
        elif line.upper().startswith("RIGHT") or line.startswith("右"):
            mode = "right"
            line = re.sub(r"^(RIGHT|右)[：:]\s*", "", line)
        elif line.startswith("Center:") or line.startswith("中间"):
            continue
        if mode == "left":
            left_lines.append(line)
        else:
            right_lines.append(line)
    lw = (W - gap * 3) // 2
    draw_card(draw, (gap, y, gap + lw, y + box_h), left_lines[:8], COLORS[0], "方案 A")
    draw_card(draw, (mid + gap // 2, y, mid + gap // 2 + lw, y + box_h), right_lines[:8], COLORS[1], "方案 B")
    draw.line([(mid, y + 40), (mid, y + box_h - 40)], fill=MUTED, width=3)


def render_linear_progression(draw: ImageDraw.ImageDraw, spec: dict) -> None:
    y = draw_title(draw, spec["title"] or "流程图")
    items = []
    for line in spec["lines"]:
        if "→" in line:
            parts = [p.strip() for p in line.split("→")]
            items.extend(parts)
        elif re.match(r"^\d+[\.、]", line):
            items.append(re.sub(r"^\d+[\.、]\s*", "", line))
        elif line.startswith("Flow:") or line.startswith("流程"):
            continue
        elif len(line) < 60:
            items.append(line)
    items = items[:6] or spec["lines"][:6]
    n = len(items)
    gap = 30
    box_w = max(180, (W - gap * (n + 1)) // max(n, 1))
    cy = y + (H - y - 160) // 2
    x = gap
    for i, item in enumerate(items):
        box = (x, cy, x + box_w, cy + 140)
        draw_card(draw, box, [item], COLORS[i % len(COLORS)])
        if i < n - 1:
            draw_arrow_h(draw, x + box_w + 6, cy + 70, x + box_w + gap - 6)
        x += box_w + gap


def render_bento_grid(draw: ImageDraw.ImageDraw, spec: dict) -> None:
    y = draw_title(draw, spec["title"] or "概念地图")
    cells = []
    for line in spec["lines"]:
        if re.match(r"^\d+\.", line):
            cells.append(re.sub(r"^\d+\.\s*", "", line))
        elif line.startswith("Cells"):
            continue
    cells = cells[:8] or spec["lines"][:8]
    cols, rows = 4, 2
    pad = 36
    gw = (W - pad * 2 - 30) // cols
    gh = (H - y - pad - 20) // rows
    for i, cell in enumerate(cells):
        r, c = divmod(i, cols)
        x0 = pad + c * (gw + 10)
        y0 = y + r * (gh + 10)
        draw_card(draw, (x0, y0, x0 + gw, y0 + gh), [cell], COLORS[i % len(COLORS)])


def render_hub_spoke(draw: ImageDraw.ImageDraw, spec: dict) -> None:
    y = draw_title(draw, spec["title"] or "架构图")
    hub = spec["title"] or "核心"
    spokes = [ln for ln in spec["lines"] if ln and not ln.startswith("core")][:6]
    cx, cy = W // 2, y + (H - y) // 2 + 10
    draw_wavy_rect(draw, (cx - 150, cy - 70, cx + 150, cy + 70), COLORS[2], INK)
    hf = load_font(30, bold=True)
    bbox = draw.textbbox((0, 0), hub, font=hf)
    draw.text((cx - (bbox[2] - bbox[0]) // 2, cy - 18), hub, font=hf, fill=INK)
    positions = [
        (120, cy - 60),
        (W - 420, cy - 60),
        (120, cy + 40),
        (W - 420, cy + 40),
        (cx - 200, cy + 150),
        (cx + 20, cy + 150),
    ]
    for i, (sp, (x, sy)) in enumerate(zip(spokes, positions)):
        draw_card(draw, (x, sy, x + 300, sy + 100), [sp], COLORS[i % len(COLORS)])


def render_flow(draw: ImageDraw.ImageDraw, spec: dict) -> None:
    y = draw_title(draw, spec["title"] or "流程")
    items = []
    for line in spec["lines"]:
        if "→" in line:
            items.extend([p.strip() for p in line.split("→")])
        elif re.match(r"^\d+", line):
            items.append(re.sub(r"^\d+[\.、]\s*", "", line))
        elif len(line) < 80:
            items.append(line)
    items = items[:7] or spec["lines"][:7]
    x0, x1 = 180, W - 180
    step = max(90, (H - y - 120) // max(len(items), 1))
    cy = y + 20
    for i, item in enumerate(items):
        box = (x0, cy, x1, cy + 72)
        draw_card(draw, box, [item], COLORS[i % len(COLORS)])
        if i < len(items) - 1:
            draw.line([(W // 2, cy + 72), (W // 2, cy + step - 8)], fill=MUTED, width=3)
            draw.polygon([(W // 2, cy + step), (W // 2 - 8, cy + step - 14), (W // 2 + 8, cy + step - 14)], fill=MUTED)
        cy += step


def render_png(spec: dict, out_path: Path) -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    layout = spec["layout"].lower()
    if "binary" in layout or "comparison" in layout:
        render_binary_comparison(draw, spec)
    elif "bento" in layout:
        render_bento_grid(draw, spec)
    elif "hub" in layout:
        render_hub_spoke(draw, spec)
    elif "flow" in layout and "linear" not in layout:
        render_flow(draw, spec)
    else:
        render_linear_progression(draw, spec)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", help="Single prompt .md file")
    ap.add_argument("--slug", help="Render all prompts under image/{slug}/prompts/")
    ap.add_argument("--all-agent", action="store_true", help="Render 214-254 agent infographics")
    args = ap.parse_args()

    jobs: list[tuple[Path, Path]] = []
    if args.prompt:
        p = Path(args.prompt)
        out = p.parent.parent / (p.stem + ".png")
        jobs = [(p, out)]
    elif args.slug:
        prompt_dir = ROOT / "image" / args.slug / "prompts"
        for p in sorted(prompt_dir.glob("*.md")):
            jobs.append((p, p.parent.parent / (p.stem + ".png")))
    elif args.all_agent:
        for d in sorted((ROOT / "image").iterdir()):
            readme = d / "README.md"
            if not readme.exists():
                continue
            if not any(readme.read_text(encoding="utf-8").find("AI Agent") >= 0 for _ in [0]):
                # include dirs with agent tutorial prompts numbered 214+
                pass
            prompts = d / "prompts"
            if not prompts.is_dir():
                continue
            # only agent batch: check for 01-* pattern and article exists
            slug = d.name
            arts = list((ROOT / "docs").glob(f"*.{slug}-tutorial.md"))
            if not arts:
                continue
            num = int(arts[0].name.split(".")[0])
            if num < 214 or num > 254:
                continue
            for p in sorted(prompts.glob("*.md")):
                jobs.append((p, d / (p.stem + ".png")))
    else:
        ap.error("Specify prompt file, --slug, or --all-agent")

    for prompt, out in jobs:
        spec = parse_prompt(prompt)
        render_png(spec, out)
        print(f"OK {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
