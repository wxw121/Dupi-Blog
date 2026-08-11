#!/usr/bin/env python3
"""Rename frontend tutorial files and update references repo-wide."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SUFFIX = "（front-end）"
FOOTER = (
    "\n\n---\n\n"
    "> **系列标注：** front-end（前端技术篇）\n"
)

# A 基础前置 19–23 + F2/G 前端 171–184（与路线图 F2 对齐）
FRONTEND_NUMBERS = list(range(13, 17)) + list(range(171, 185))

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".baoyu-skills",
    "assets",
}


def tutorial_path(num: int) -> Path | None:
    matches = sorted(DOCS.glob(f"{num}.*-tutorial.md"))
    if not matches:
        return None
    if len(matches) > 1:
        # prefer without suffix if duplicate
        for p in matches:
            if SUFFIX not in p.name:
                return p
    return matches[0]


def new_name(old: Path) -> str:
    stem = old.stem  # e.g. 13.typescript-basics-tutorial
    if stem.endswith(SUFFIX):
        return old.name
    if not stem.endswith("-tutorial"):
        raise ValueError(f"unexpected tutorial stem: {stem}")
    return f"{stem}{SUFFIX}.md"


def collect_renames() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for num in FRONTEND_NUMBERS:
        old = tutorial_path(num)
        if old is None:
            print(f"WARN: missing tutorial #{num}", file=sys.stderr)
            continue
        new = old.with_name(new_name(old))
        if old != new:
            pairs.append((old, new))
    return pairs


def replace_in_text(text: str, mapping: dict[str, str]) -> str:
    out = text
    # longest keys first
    for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
        out = out.replace(old, new)
    return out


def main() -> int:
    pairs = collect_renames()
    if not pairs:
        print("No files to rename.")
        return 0

    mapping: dict[str, str] = {}
    for old, new in pairs:
        mapping[old.name] = new.name
        mapping[f"docs/{old.name}"] = f"docs/{new.name}"
        mapping[str(old).replace("\\", "/")] = str(new).replace("\\", "/")
        if str(old).startswith(str(ROOT)):
            rel = old.relative_to(ROOT).as_posix()
            mapping[rel] = new.relative_to(ROOT).as_posix()

    print("Renames:")
    for old, new in pairs:
        print(f"  {old.name} -> {new.name}")

    # 1. Rename files
    for old, new in pairs:
        if new.exists():
            print(f"SKIP exists: {new.name}")
            continue
        old.rename(new)

    # 2. Append footer if missing
    for _, new in pairs:
        text = new.read_text(encoding="utf-8")
        if "系列标注：** front-end" not in text:
            new.write_text(text.rstrip() + FOOTER, encoding="utf-8")

    # 3. Update references in repo
    exts = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".toml"}
    updated_files = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in exts:
            continue
        if path.name == Path(__file__).name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text = replace_in_text(text, mapping)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            updated_files += 1

    # 4. Update interview generator regex
    gen = ROOT / "scripts" / "generate_interview_questions.py"
    if gen.exists():
        t = gen.read_text(encoding="utf-8")
        old_re = 'TUTORIAL_RE = re.compile(r"^(\\d+)\\.(.+)-tutorial\\.md$")'
        new_re = 'TUTORIAL_RE = re.compile(r"^(\\d+)\\.(.+?)-tutorial(?:（front-end）)?\\.md$")'
        if old_re in t:
            gen.write_text(t.replace(old_re, new_re), encoding="utf-8")
            updated_files += 1

    print(f"\nDone: {len(pairs)} renamed, {updated_files} files updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
