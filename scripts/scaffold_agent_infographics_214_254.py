#!/usr/bin/env python3
"""Scaffold infographics for AI Agent tutorials 214-254, render PNGs, insert markdown refs."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STYLE_FOOTER = """Style: hand-drawn-edu, cream #F5F0E8, macaron pastels, stick figures, Simplified Chinese.

All text Simplified Chinese. Legible, generous whitespace."""

# Per-slug image plan: (png, layout, section_heading_substr, alt, body)
# section_heading_substr matches ## heading containing this text
IMAGE_PLANS: dict[str, list[tuple[str, str, str, str, str]]] = {}


def slug_from_path(p: Path) -> str:
    return re.sub(r"-tutorial\.md$", "", re.sub(r"^\d+\.", "", p.name))


def extract_text_block(content: str, limit: int = 6) -> list[str]:
    lines: list[str] = []
    in_block = False
    for line in content.splitlines():
        if line.strip() == "```text":
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if in_block:
            s = line.strip()
            if s and not s.endswith(":"):
                lines.append(s)
            if len(lines) >= limit:
                break
    return lines


def learn_bullets(content: str, limit: int = 8) -> list[str]:
    m = re.search(r"## 你会学到什么\n\n((?:- .+\n?)+)", content)
    if not m:
        return []
    return [ln[2:].strip() for ln in m.group(1).splitlines() if ln.startswith("- ")][:limit]


def short_title(full: str) -> str:
    return re.sub(r"^AI Agent 工程（[^）]+）：", "", full).strip()


def plan_for_article(num: int, path: Path) -> list[tuple[str, str, str, str, str]]:
    content = path.read_text(encoding="utf-8")
    slug = slug_from_path(path)
    title_m = re.search(r"^# (.+)$", content, re.M)
    full_title = title_m.group(1) if title_m else slug
    topic = short_title(full_title)
    text_lines = extract_text_block(content, 8)
    bullets = learn_bullets(content)

    # Image 1: core idea — binary or hub
    idea_lines = text_lines[:6] if text_lines else bullets[:4]
    if len(idea_lines) >= 2:
        mid = len(idea_lines) // 2
        body1 = f"Title: {topic}核心思想\n\nLEFT: {topic}要解决什么\n" + "\n".join(idea_lines[:mid]) + f"\n\nRIGHT: 工程化关键点\n" + "\n".join(idea_lines[mid:])
        layout1 = "binary-comparison"
    else:
        body1 = f"Title: {topic}核心思想\n\n" + "\n".join(bullets[:4] or [topic])
        layout1 = "hub-spoke"

    # Image 2: flow from first text block or lifecycle
    flow_src = text_lines if text_lines else bullets[:5]
    flow_body = "Title: " + topic + "流程\n\nFlow:\n" + "\n".join(f"→ {ln}" if "→" not in ln else ln for ln in flow_src[:5])
    if not flow_src:
        flow_body = f"Title: {topic}执行流程\n\n1. 接收输入\n2. 校验与决策\n3. 执行动作\n4. 记录观测\n5. 输出结果"

    # Image 3: concept map from bullets
    cells = bullets[:8] or [topic, "最小示例", "工程化", "观测评测", "常见陷阱", "生产注意", "面试要点", "系列衔接"]
    map_body = f"Title: {topic}概念地图\n\nCells:\n" + "\n".join(f"{i+1}. {c}" for i, c in enumerate(cells))

    # Section anchors
    headings = re.findall(r"^## (.+)$", content, re.M)

    def pick_section(keys: tuple[str, ...], fallback: str) -> str:
        for key in keys:
            for h in headings:
                if key in h:
                    return h
        return fallback

    sec1 = pick_section(("核心概念", "是什么", "为什么", "它解决什么问题"), headings[2] if len(headings) > 2 else headings[0])
    sec2 = pick_section(("工程化版本", "最小示例", "怎么做"), "最小示例")
    sec3 = pick_section(("下一步",), "下一步")

    short = slug if len(slug) <= 28 else slug[:28].rstrip("-")
    return [
        (f"01-{short}-idea.png", layout1, sec1, f"{topic} 核心思想", body1),
        (f"02-{short}-flow.png", "linear-progression", sec2, f"{topic} 流程", flow_body),
        ("03-concept-map.png", "bento-grid", sec3, f"{topic} 概念地图", map_body),
    ]


def write_prompt(path: Path, layout: str, body: str) -> None:
    path.write_text(
        f"---\nlayout: {layout}\nstyle: hand-drawn-edu\naspect_ratio: 16:9\nlanguage: zh\n---\n\n"
        f"Create a professional educational infographic, 16:9 landscape.\n"
        f"Layout: {layout}.\n{STYLE_FOOTER}\n\n{body.strip()}\n",
        encoding="utf-8",
    )


def scaffold_article(num: int, path: Path) -> str:
    slug = slug_from_path(path)
    plans = plan_for_article(num, path)
    base = ROOT / "image" / slug
    prompts = base / "prompts"
    prompts.mkdir(parents=True, exist_ok=True)
    rows = []
    for png, layout, section, alt, body in plans:
        stem = Path(png).stem
        write_prompt(prompts / f"{stem}.md", layout, body)
        rows.append(f"| `{png}` | {layout} | §{section} |")
    title = short_title(re.search(r"^# (.+)$", path.read_text(encoding="utf-8"), re.M).group(1))
    readme = (
        f"# {title}信息图（AI Agent 工程 #{num}）\n\n"
        "| 文件 | 布局 | 插入位置 |\n|------|------|----------|\n"
        + "\n".join(rows)
        + "\n\n风格：hand-drawn-edu · 16:9 · 中文\n\nPrompt 见 `prompts/`。\n"
    )
    (base / "README.md").write_text(readme, encoding="utf-8")
    return slug


def insert_refs(path: Path, slug: str, plans: list[tuple[str, str, str, str, str]]) -> int:
    content = path.read_text(encoding="utf-8")
    inserted = 0
    for png, _layout, section, alt, _body in plans:
        img_line = f"![{alt}](../image/{slug}/{png})"
        if img_line in content:
            continue
        pattern = re.compile(rf"^(## {re.escape(section)}\s*)$", re.M)
        m = pattern.search(content)
        if not m:
            # fuzzy: heading contains section key
            for hm in re.finditer(r"^## (.+)$", content, re.M):
                if section in hm.group(1):
                    m = hm
                    break
        if not m:
            continue
        line_end = content.find("\n", m.end())
        if line_end == -1:
            line_end = len(content)
        lead = f"\n读下图时，先看「{alt}」建立直觉。\n\n{img_line}\n"
        content = content[: line_end + 1] + lead + content[line_end + 1 :]
        inserted += 1
    if inserted:
        path.write_text(content, encoding="utf-8")
    return inserted


def main() -> None:
    nums = range(214, 255)
    slugs: list[str] = []
    for num in nums:
        arts = sorted(DOCS.glob(f"{num}.*-tutorial.md"))
        if not arts:
            print(f"SKIP missing {num}")
            continue
        path = arts[0]
        slug = scaffold_article(num, path)
        plans = plan_for_article(num, path)
        n = insert_refs(path, slug, plans)
        slugs.append(slug)
        print(f"OK {num} {slug}: refs={n}")

    # render all PNGs — use AI generation (baoyu-image-gen), NOT Pillow placeholder
    print("NOTE: PNG rendering skipped. Run:")
    print("  python scripts/regen_agent_infographics_214_254.py --enhance-prompts --write-batch")
    print("  npx -y bun ~/.codex/skills/baoyu-image-gen/scripts/main.ts --batchfile scripts/_agent_batch_214_254.json")
    print("Or regenerate via baoyu-infographic / Cursor GenerateImage with hand-drawn-edu style.")
    print(f"Done {len(slugs)} articles")


if __name__ == "__main__":
    main()
