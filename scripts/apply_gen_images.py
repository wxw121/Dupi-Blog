#!/usr/bin/env python3
"""Copy generated agent infographic PNGs from assets/ to image/{slug}/."""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(os.environ.get("BLOG_ASSETS_DIR", ROOT / "assets"))
if not ASSETS.is_absolute():
    ASSETS = ROOT / ASSETS
MANIFEST = ROOT / "scripts" / "_agent_gen_manifest.json"
PROGRESS = ROOT / "scripts" / "_agent_gen_progress.json"


def load_manifest() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    return data


def load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"completed": [], "failed": [], "total": 123}


def save_progress(progress: dict) -> None:
    PROGRESS.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_entry(entry: dict, asset_name: str | None = None) -> bool:
    target = ROOT / str(entry.get("image", entry.get("id", ""))).replace("\\", "/")
    if not target.suffix:
        target = ROOT / "image" / entry["id"]
    src = ASSETS / (asset_name or target.name)
    if not src.exists():
        print(f"SKIP missing {src.name}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    print(f"OK {target.relative_to(ROOT)}")
    return True


def copy_all() -> int:
    manifest = load_manifest()
    progress = load_progress()
    completed = set(progress.get("completed", []))
    moved = 0
    for entry in manifest:
        eid = entry.get("id") or str(entry["image"]).replace("\\", "/")
        if copy_entry(entry):
            completed.add(eid)
            moved += 1
    progress["completed"] = sorted(completed)
    save_progress(progress)
    print(f"copied {moved}, total completed {len(completed)}")
    return moved


def copy_batch_args(args: list[str]) -> int:
    """Copy by manifest index: python apply_gen_images.py 4:filename.png 5:other.png"""
    manifest = load_manifest()
    progress = load_progress()
    completed = set(progress.get("completed", []))
    moved = 0
    for arg in args:
        idx_s, asset_name = arg.split(":", 1)
        entry = manifest[int(idx_s)]
        eid = entry.get("id") or str(entry["image"]).replace("\\", "/")
        if copy_entry(entry, asset_name):
            completed.add(eid)
            moved += 1
        else:
            progress.setdefault("failed", []).append({"id": eid, "error": "asset missing"})
    progress["completed"] = sorted(completed)
    save_progress(progress)
    print(f"copied {moved}, total completed {len(completed)}")
    return moved


def main() -> None:
    if len(sys.argv) > 1:
        copy_batch_args(sys.argv[1:])
    else:
        copy_all()


if __name__ == "__main__":
    main()
