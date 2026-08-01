#!/usr/bin/env python3
"""RAG Agent Lab — 239-243 系列最小示例统一入口。"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEMOS: dict[str, tuple[str, bool]] = {
    "239": ("demo_query_planning.py", True),
    "240": ("demo_multi_step.py", True),
    "241": ("demo_tool_rag.py", True),
    "242": ("demo_citation_verify.py", True),
    "243": ("demo_bad_case.py", False),
    "244": ("demo_sequential_workflow.py", False),
}


def run_script(script: str) -> int:
    path = ROOT / script
    print(f"\n{'=' * 60}\n>> {script}\n{'=' * 60}")
    return subprocess.run([sys.executable, str(path)], cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG Agent Lab 示例运行器")
    parser.add_argument(
        "target",
        nargs="?",
        default="243",
        help="示例编号 239-244，或 all",
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="跳过需要 OPENAI_API_KEY 的示例",
    )
    args = parser.parse_args()

    if args.target == "all":
        codes = []
        for num, (script, needs_api) in DEMOS.items():
            if args.skip_api and needs_api:
                print(f"跳过 {num}（需要 API）")
                continue
            codes.append(run_script(script))
        return max(codes) if codes else 0

    if args.target not in DEMOS:
        print(f"未知目标: {args.target}，可选: {', '.join(DEMOS)} 或 all")
        return 1

    script, needs_api = DEMOS[args.target]
    if needs_api and args.skip_api:
        print(f"{args.target} 需要 OPENAI_API_KEY，未运行")
        return 0
    return run_script(script)


if __name__ == "__main__":
    raise SystemExit(main())
