#!/usr/bin/env python3
"""Batch insert infographic refs from image/{slug}/README.md into tutorial articles."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMG_REF = re.compile(r"!\[[^\]]*\]\((?:\.\./)?image/[^)]+\)")
README_ROW = re.compile(
    r"\|\s*`([^`]+\.png)`\s*\|[^|]*\|\s*(?:§(\d+)|§([^|]+))\s*([^|]*)\|",
    re.IGNORECASE,
)
SECTION_HDR = re.compile(r"^##\s+(.+)$", re.MULTILINE)
READ_DIAG = re.compile(r"读下图|读决策图|下面这张图", re.IGNORECASE)


def article_paths(min_num: int, max_num: int) -> list[Path]:
    paths: list[Path] = []
    for base in (ROOT, DOCS):
        for article in sorted(base.glob("[0-9]*.md")):
            num = int(article.name.split(".", 1)[0])
            if min_num <= num <= max_num:
                paths.append(article)
    return paths


def image_prefix(article: Path) -> str:
    return "../image/" if article.parent.name == "docs" else "image/"


def slug_from_article(path: Path) -> str:
    name = path.name
    return re.sub(r"-tutorial\.md$", "", re.sub(r"^\d+\.", "", name))


def find_article(slug: str) -> Path | None:
    hits = sorted(ROOT.glob(f"*.{slug}-tutorial.md"))
    return hits[0] if hits else None


def parse_readme(readme: Path) -> list[tuple[str, int | None, str | None, str]]:
    text = readme.read_text(encoding="utf-8")
    rows: list[tuple[str, int | None, str | None, str]] = []
    for m in README_ROW.finditer(text):
        png = m.group(1)
        sec_num = int(m.group(2)) if m.group(2) else None
        sec_title = (m.group(3) or m.group(4) or "").strip() or None
        alt = sec_title or png.replace(".png", "").replace("-", " ")
        rows.append((png, sec_num, sec_title, alt))
    return rows


def section_bounds(content: str, sec_num: int | None, sec_title: str | None) -> tuple[int, int] | None:
    starts: list[tuple[int, str]] = [(m.start(), m.group(1).strip()) for m in SECTION_HDR.finditer(content)]
    if sec_title:
        for i, (pos, title) in enumerate(starts):
            if sec_title in title or title in sec_title:
                end = starts[i + 1][0] if i + 1 < len(starts) else len(content)
                return pos, end
    if sec_num is not None:
        num_starts = [(m.start(), int(m.group(1))) for m in re.finditer(r"^##\s+(\d+)\.\s+", content, re.M)]
        for i, (pos, num) in enumerate(num_starts):
            if num == sec_num:
                end = num_starts[i + 1][0] if i + 1 < len(num_starts) else len(content)
                return pos, end
        if sec_num >= 10 and num_starts:
            pos, _ = num_starts[-1]
            return pos, len(content)
    return None


def pick_anchor_line(section: str) -> int | None:
    """Return index in section where image line should be inserted (after this line)."""
    lines = section.splitlines(keepends=True)
    offset = 0
    for line in lines:
        stripped = line.strip()
        if READ_DIAG.search(stripped):
            return offset + len(line)
        offset += len(line)
    # before mermaid
    offset = 0
    for line in lines:
        if line.strip().startswith("```mermaid"):
            return offset
        offset += len(line)
    # after first non-empty paragraph following header
    offset = 0
    passed_header = False
    non_empty_after_header = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## "):
            passed_header = True
            offset += len(line)
            continue
        if not passed_header:
            offset += len(line)
            continue
        if not stripped:
            offset += len(line)
            continue
        if stripped.startswith("|") or stripped.startswith("```"):
            offset += len(line)
            continue
        non_empty_after_header += 1
        offset += len(line)
        if non_empty_after_header >= 1 and (i + 1 >= len(lines) or not lines[i + 1].strip().startswith("|")):
            return offset
    return len(section)


def alt_from_png(png: str, sec_title: str) -> str:
    if sec_title and "概念" not in sec_title[:4]:
        return sec_title.split("后")[0].strip() or sec_title
    base = png.replace(".png", "")
    parts = base.split("-", 1)
    return sec_title or (parts[1].replace("-", " ") if len(parts) > 1 else base)


def insert_images(article: Path, slug: str, rows: list[tuple[str, int | None, str | None, str]], dry_run: bool = False) -> int:
    content = article.read_text(encoding="utf-8")
    prefix = image_prefix(article)
    inserted = 0
    for png, sec_num, sec_title, sec_alt in rows:
        img_line = f"![{alt_from_png(png, sec_alt or '')}]({prefix}{slug}/{png})"
        if img_line in content:
            continue
        png_path = ROOT / "image" / slug / png
        if not png_path.exists():
            continue
        sec = section_bounds(content, sec_num, sec_title)
        if sec is None:
            continue
        sec_start, sec_end = sec
        section = content[sec_start:sec_end]
        rel_pos = pick_anchor_line(section)
        abs_pos = sec_start + rel_pos
        block = f"\n{img_line}\n"
        content = content[:abs_pos] + block + content[abs_pos:]
        inserted += 1
    if inserted and not dry_run:
        article.write_text(content, encoding="utf-8")
    return inserted


def list_pending() -> list[dict]:
    pending = []
    seen: set[str] = set()
    for article in article_paths(0, 9999):
        if article.name in seen:
            continue
        seen.add(article.name)
        if IMG_REF.search(article.read_text(encoding="utf-8")):
            continue
        slug = slug_from_article(article)
        img_dir = ROOT / "image" / slug
        readme = img_dir / "README.md"
        if not readme.exists():
            continue
        rows = parse_readme(readme)
        pngs = {p.name for p in img_dir.glob("*.png")}
        need = [r for r in rows if r[0] not in pngs]
        have = [r for r in rows if r[0] in pngs]
        pending.append(
            {
                "article": article.name,
                "slug": slug,
                "total": len(rows),
                "have_png": len(have),
                "need_gen": len(need),
                "need_files": [r[0] for r in need],
            }
        )
    return pending


def insert_all(min_num: int = 0, max_num: int = 9999) -> None:
    count = 0
    seen: set[str] = set()
    for article in article_paths(min_num, max_num):
        if article.name in seen:
            continue
        seen.add(article.name)
        slug = slug_from_article(article)
        readme = ROOT / "image" / slug / "README.md"
        if not readme.exists():
            continue
        content = article.read_text(encoding="utf-8")
        rows = parse_readme(readme)
        n = insert_images(article, slug, rows)
        if n:
            print(f"OK {article.name}: inserted {n}")
            count += 1
    print(f"Updated {count} articles")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "insert"
    if cmd == "list":
        for p in list_pending():
            print(f"{p['article']}: {p['have_png']}/{p['total']} png, need {p['need_gen']}")
    elif cmd == "insert":
        lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        hi = int(sys.argv[3]) if len(sys.argv) > 3 else 9999
        insert_all(lo, hi)
    else:
        print("Usage: batch-infographic.py [list|insert] [min_num] [max_num]")


if __name__ == "__main__":
    main()
