#!/usr/bin/env python3
"""Pass 4: de-template image conclusions, hands-on paths, comparison tables, 238 02-flow."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_tutorial_pass4_data import (  # noqa: E402
    COMPARISON_TABLE,
    COMPREHENSIVE_251_254,
    FLOW_AFTER,
    FLOW_PREAMBLE,
    FLOW_PREAMBLE_DEFAULT,
    HANDS_ON_ALL,
    IDEA_AFTER,
    MAP_AFTER,
    TEMPLATE_FLOW_OLD,
    TEMPLATE_FLOW_PREAMBLE_OLD,
    TEMPLATE_IDEA,
    TEMPLATE_MAP,
    WRONG_RIGHT,
)

SERIES = list(range(214, 255))

FLOW_238_BLOCK = """
读下图时，看「规划→检索→充分性→生成」的生产流水线；重点看对比任务两侧证据齐了才判 True。

![Agentic RAG 生产架构流程](../image/agentic-rag-architecture/02-agentic-rag-architecture-flow.png)

对照上图：第一轮检索生成 2 个子查询、两侧证据齐全后充分性为 True——与 §是什么 的充分性闸门一致；证据未齐时必须继续检索而非直接生成。
"""


def doc_path(n: int) -> Path:
    return list(DOCS.glob(f"{n}.*-tutorial.md"))[0]


def upsert_hands_on(text: str, n: int) -> str:
    path = HANDS_ON_ALL[n]
    if "**动手路径：**" in text:
        text = re.sub(r"\*\*动手路径：\*\*[^\n]+", f"**动手路径：** {path}", text, count=1)
    else:
        text = re.sub(
            r"(\*\*本文边界：\*\*[^\n]+\n)",
            rf"\1**动手路径：** {path}\n",
            text,
            count=1,
        )
    return text


def fix_image_conclusions(text: str, n: int) -> str:
    if n in IDEA_AFTER:
        text = TEMPLATE_IDEA.sub(IDEA_AFTER[n], text)
        # also fix partial custom 214-style that still has template
        old_generic = "——建立本专题直觉，留意图中标注的输入/输出或对比关系，再读下文。"
        if old_generic in text and n in IDEA_AFTER:
            text = re.sub(
                rf"对照上图：[^。\n]+{re.escape(old_generic)}",
                IDEA_AFTER[n],
                text,
                count=1,
            )
    if n in MAP_AFTER:
        text = TEMPLATE_MAP.sub(MAP_AFTER[n], text)
    if TEMPLATE_FLOW_OLD in text:
        text = text.replace(TEMPLATE_FLOW_OLD, FLOW_AFTER.get(n, FLOW_AFTER.get(250, "对照上图：流程强调能力边界与痛点——下文 §最小示例 用代码落地。")))
    if TEMPLATE_FLOW_PREAMBLE_OLD in text:
        preamble = FLOW_PREAMBLE.get(n, FLOW_PREAMBLE_DEFAULT)
        text = text.replace(TEMPLATE_FLOW_PREAMBLE_OLD, preamble)
    return text


def insert_comparison_table(text: str, n: int) -> str:
    if n not in COMPARISON_TABLE:
        return text
    block = COMPARISON_TABLE[n].strip() + "\n\n"
    marker = "## 常见失败模式"
    if block.strip() in text:
        return text
    if marker in text:
        return text.replace(marker, block + marker, 1)
    return text


def insert_wrong_right(text: str, n: int) -> str:
    if n not in WRONG_RIGHT:
        return text
    block = WRONG_RIGHT[n].strip() + "\n\n"
    if "### 先错对错" in text or "### 先错后对" in text:
        return text
    m = re.search(r"(## 最小示例\n\n)", text)
    if not m:
        return text
    return text[: m.end()] + block + text[m.end() :]


def insert_238_flow(text: str) -> str:
    if "02-agentic-rag-architecture-flow" in text:
        return text
    anchor = "## 怎么做：四个核心组件的工程实现\n\n"
    if anchor not in text:
        return text
    return text.replace(anchor, anchor + FLOW_238_BLOCK.strip() + "\n\n", 1)


def replace_comprehensive(text: str, n: int) -> str:
    if n not in COMPREHENSIVE_251_254:
        return text
    new_block = COMPREHENSIVE_251_254[n].strip() + "\n\n"
    m = re.search(r"## 综合实战\n\n[\s\S]*?(?=\n## 常见失败模式)", text)
    if m:
        return text[: m.start()] + new_block + text[m.end() :]
    return text


def fix_episodic_typo(text: str) -> str:
    return text.replace("|  episodic |", "| 情景记忆（Episodic） |")


def process_one(n: int) -> bool:
    p = doc_path(n)
    original = p.read_text(encoding="utf-8")
    text = original
    text = upsert_hands_on(text, n)
    text = fix_image_conclusions(text, n)
    text = insert_comparison_table(text, n)
    text = insert_wrong_right(text, n)
    if n == 238:
        text = insert_238_flow(text)
    if n in COMPREHENSIVE_251_254:
        text = replace_comprehensive(text, n)
    if n == 232:
        text = fix_episodic_typo(text)
    if text != original:
        p.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = [n for n in SERIES if process_one(n)]
    print(f"Pass 4: updated {len(changed)} docs")
    if changed:
        print(changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
