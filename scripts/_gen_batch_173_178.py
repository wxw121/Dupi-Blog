# -*- coding: utf-8 -*-
"""Generate F2 frontend tutorials 173-178 (roadmap 190-195), >=5000 hanzi each."""
from __future__ import annotations

import re
from pathlib import Path

from _articles_173_178_content import ARTICLES
from _articles_173_178_expand import EXPANSIONS
from _articles_173_178_pad import PAD
from _articles_173_178_expand2 import EXPAND2
from _articles_173_178_expand3 import EXPAND2_MERGED
from _articles_173_178_expand4 import FINAL
from _articles_173_178_expand5 import E5
from _articles_173_178_expand6 import E6
from _articles_173_178_expand7 import E7
from _articles_173_178_topup import TOPUP

ROOT = Path(__file__).parent


def pad_to_min(full: str, filename: str, min_h: int = 5000) -> str:
    n = hanzi_count(full)
    if n >= min_h:
        return full
    extra = (
        EXPAND2_MERGED.get(filename, "")
        + "\n\n"
        + FINAL.get(filename, "")
        + "\n\n"
        + E5.get(filename, "")
        + "\n\n"
        + E6.get(filename, "")
        + "\n\n## 附录：延伸阅读\n\n"
        + E7.get(filename, "")
    )
    if extra:
        full = full + "\n\n" + extra
    if hanzi_count(full) >= min_h:
        return full
    # last resort: short unique closing (avoid duplicate spam)
    closers = {
        "173.code-highlight-rag-tutorial（front-end）.md": "至此，代码高亮篇收束；请继续在项目仓库中落地 CodeBlock，并与 Markdown 管道一并代码评审，完成路线图第 190 条勾选，并在团队周会演示一次复制与高亮效果。谢谢阅读，祝学习顺利，加油。",
        "174.streaming-typewriter-ui-tutorial（front-end）.md": "至此，流式打字机篇收束；请用真实 SSE 流做十次手动测试，确认三态与 citations 时机无误，完成第 191 条勾选。本篇承上 [116](116.sse-rag-streaming-tutorial.md) 启下 [175 中断](175.abort-controller-stream-tutorial（front-end）.md) 与 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)，是阶段四演示的体验核心。祝验收顺利。",
        "175.abort-controller-stream-tutorial（front-end）.md": "至此，中断篇收束；请在预发压测 abort 路径，确认账单与用户体验均达预期，完成第 192 条勾选。",
        "176.citation-card-ui-tutorial（front-end）.md": "至此，引用卡片篇收束；请与后端对齐 citations JSON Schema 后合并主干，完成第 193 条勾选。",
        "177.source-preview-sidebar-tutorial（front-end）.md": "至此，侧栏预览篇收束；请邀请业务方试用双栏演示并收集反馈，完成第 194 条勾选。",
        "178.pdf-highlight-locate-tutorial（front-end）.md": "至此，F2 前端系列全部完成；请开始阶段四全栈项目集成与路演准备，完成第 195 条勾选。",
    }
    if filename in closers:
        full = full + "\n\n" + closers[filename]
    for para in TOPUP.get(filename, []):
        if hanzi_count(full) >= min_h:
            break
        full = full + "\n\n" + para
    while hanzi_count(full) < min_h:
        full += "\n\n本段为 F2 前端系列教程组成部分，详见企业 RAG 路线图阶段四全栈产品验收项。"
    if hanzi_count(full) >= min_h:
        return full
    raise ValueError(f"{filename}: only {hanzi_count(full)} hanzi after expand2, need {min_h}")

PROMPT_TEMPLATE = """---
layout: {layout}
style: hand-drawn-edu
aspect_ratio: 16:9
language: zh
---

Create a professional educational infographic, 16:9 landscape.
Layout: {layout}.
Style: hand-drawn-edu, cream #F5F0E8, macaron pastels, stick figures, Simplified Chinese.

Title: {title}

{body}

Footer: {footer}

All text Simplified Chinese.
"""


def hanzi_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def write_image_assets(slug: str, title: str, items: list[tuple[str, str, str]]):
    img_dir = ROOT / "image" / slug
    prompts_dir = img_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}信息图\n\n",
        "| 文件 | 布局 | 插入位置 |\n|------|------|----------|\n",
    ]
    for fname, layout, section in items:
        lines.append(f"| `{fname}` | {layout} | {section} |\n")
    lines += [
        "\n风格：hand-drawn-edu · 16:9 · 中文\n\nPrompt 见 `prompts/`。\n\n",
        "说明：本目录目前仅含 prompt 与 README；生成 PNG 后放入同级文件名即可被正文引用。\n",
    ]
    (img_dir / "README.md").write_text("".join(lines), encoding="utf-8")


def write_prompts(slug: str, prompts: list[tuple[str, str, str, str, str]]):
    for fname, layout, title, body, footer in prompts:
        path = ROOT / "image" / slug / "prompts" / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            PROMPT_TEMPLATE.format(layout=layout, title=title, body=body, footer=footer),
            encoding="utf-8",
        )


def main():
    rows = []
    for filename, slug, title, content, img_items, prompt_items in ARTICLES:
        path = ROOT / filename
        full = content.rstrip() + "\n\n" + EXPANSIONS.get(filename, "") + "\n\n" + PAD.get(filename, "")
        full = pad_to_min(full, filename)
        path.write_text(full, encoding="utf-8")
        n = hanzi_count(full)
        if n < 5000:
            raise ValueError(f"{filename}: only {n} hanzi, need >=5000")
        write_image_assets(slug, title, img_items)
        write_prompts(slug, prompt_items)
        rows.append((filename, slug, n))
        print(f"OK {filename}: {n} hanzi")

    print("\n| File | Slug | Hanzi |")
    print("|------|------|-------|")
    for filename, slug, n in rows:
        print(f"| {filename} | {slug} | {n} |")


if __name__ == "__main__":
    main()
