#!/usr/bin/env python3
"""Apply beginner-tech-blog fixes to Agent tutorials 214-254."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from agent_tutorial_config import (
    BLOG_POST,
    BOUNDARY,
    CONCEPT_MAP_TABLE,
    GLOSSARY,
    HANDS_ON,
    IMAGE_AFTER,
    LAB_FOOTER,
    MINIMAL_MERMAID,
    NARRATIVE_DOCS,
    OPTIONAL_READ,
    PART,
    SERIES_DOCS,
    TIER,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def doc_path(num: int) -> Path:
    matches = list(DOCS.glob(f"{num}.*-tutorial.md"))
    if not matches:
        raise FileNotFoundError(f"No tutorial for {num}")
    return matches[0]


def has_marker(text: str, marker: str) -> bool:
    return marker in text


def insert_after_env_block(text: str, block: str) -> str:
    if has_marker(text, "**档位：**"):
        return text
    # After environment requirements block, before first ---
    m = re.search(
        r"(\*\*环境要求：\*\*[\s\S]*?)(---\s*\n)",
        text,
    )
    if not m:
        return text
    return text[: m.end(1)] + "\n" + block + "\n" + text[m.start(2) :]


def build_meta_block(num: int) -> str:
    tier = TIER.get(num, "主线篇")
    part = PART.get(num, "")
    lines = [f"**档位：** {tier}（{part}）"]
    if num in BOUNDARY:
        lines.append(f"**本文边界：** {BOUNDARY[num]}")
    if num in HANDS_ON:
        lines.append(f"**动手路径：** {HANDS_ON[num]}")
    if num in OPTIONAL_READ:
        o = OPTIONAL_READ[num]
        lines.extend(
            [
                "",
                "### 要不要读",
                f"- **建议读：** {o['suggest']}",
                f"- **可先跳过：** {o['skip']}",
                f"- **何时回来读：** {o['return']}",
            ]
        )
    if num in GLOSSARY:
        lines.append("")
        lines.append("### 核心术语（本篇首次出现）")
        for term, en, plain in GLOSSARY[num]:
            lines.append(f"**{term}**（{en}）：{plain}")
    if num in CONCEPT_MAP_TABLE:
        lines.append(CONCEPT_MAP_TABLE[num])
    return "\n".join(lines)


def add_post_image_conclusions(text: str) -> str:
    if has_marker(text, "对照上图："):
        # still process images missing it
        pass

    def repl(m: re.Match[str]) -> str:
        full = m.group(1)
        if "对照上图" in full:
            return m.group(0)
        inner = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", full)
        alt = inner.group(1) if inner else ""
        path = inner.group(2) if inner else ""
        key = "03-" if "/03-" in path or "-03-" in path else "02-" if "/02-" in path or "-02-" in path else "01-"
        default = IMAGE_AFTER.get(key, "对照上图：把图中的步骤与下文代码/表格逐项对齐。")
        topic = alt.replace("核心思想", "").replace("流程", "流程要点").strip()
        conclusion = default
        if topic and len(topic) < 40:
            conclusion = f"对照上图：{topic}——{default.split('：', 1)[-1]}"
        return f"{full}\n{conclusion}\n"

    pattern = r"(!\[[^\]]*\]\([^)]+\))\n(?!\s*对照上图)"
    return re.sub(pattern, repl, text)


def move_02_flow_to_problem_section(text: str, num: int) -> str:
    """Move 02-flow image from 最小示例 to 它解决什么问题; add mermaid in 最小示例."""
    flow_pat = re.compile(
        r"\n\n读下图时，先看「[^」]*流程[^」]*」建立直觉。\n\n"
        r"(!\[[^\]]*\]\(\.\./image/[^)]*02-[^)]+\))\n",
        re.MULTILINE,
    )
    m = flow_pat.search(text)
    if not m:
        return text

    flow_block = m.group(0)
    text = text[: m.start()] + "\n" + text[m.end() :]

    mermaid = MINIMAL_MERMAID.get(num)
    if mermaid:
        # Insert mermaid at start of 最小示例 section
        sec = re.search(r"(## 最小示例\n\n)", text)
        if sec:
            insert = (
                f"{sec.group(1)}"
                f"下面用流程图概括本节代码演示的主线（与 §它解决什么问题 中的能力边界图互补）。\n\n"
                f"{mermaid}\n\n"
                f"**运行环境：** Python 3.10+，见文首环境要求。"
                f"**预期：** 打印各 Level 或 demo 的步骤轨迹。\n\n"
            )
            text = text[: sec.start()] + insert + text[sec.end() :]
    else:
        sec = re.search(r"(## 最小示例\n\n)", text)
        if sec:
            insert = (
                f"{sec.group(1)}"
                f"**演示什么：** 本节最小可运行切片。"
                f"**环境：** 见文首。"
                f"**预期：** 控制台打印 demo 输出。\n\n"
            )
            text = text[: sec.start()] + insert + text[sec.end() :]

    # Insert flow into 它解决什么问题 after 01 image block
    prob = re.search(r"(## 它解决什么问题\n\n)", text)
    if not prob:
        return text
    # After first 01 image + optional conclusion
    sub = text[prob.end() :]
    img01 = re.search(
        r"(!\[[^\]]*\]\(\.\./image/[^)]*01-[^)]+\)\n(?:对照上图：[^\n]+\n)?)",
        sub,
    )
    if img01:
        pos = prob.end() + img01.end()
        flow_insert = (
            "\n读下图时，看 RAG 能力边界与 Agent 要补上的多步/分支/工具能力。\n\n"
            + flow_block.strip()
            + "\n对照上图：RAG 擅长单次检索回答；Agent 补的是规划、分支与外部系统调用。\n"
        )
        text = text[:pos] + flow_insert + text[pos:]
    return text


def add_code_preamble_before_first_python_in_minimal(text: str) -> str:
    """Ensure 最小示例 first code block has preamble if missing."""
    m = re.search(r"(## 最小示例\n\n)([\s\S]*?)(```python)", text)
    if not m:
        return text
    between = m.group(2)
    if "演示什么" in between or "运行环境" in between or "预期" in between:
        return text
    if "```mermaid" in between:
        return text
    preamble = (
        "**演示什么：** 下文代码可直接运行（文末有入口）。"
        "**环境：** 见文首。"
        "**预期：** 见 `demo_*` 函数中的 `print` 输出。\n\n"
    )
    return text[: m.start(2)] + between + preamble + text[m.start(3) :]


def add_demo_main_entries(text: str) -> str:
    """Add if __name__ block before closing ``` of python blocks with demo_ functions."""

    def fix_block(block: str) -> str:
        if "if __name__" in block:
            return block
        demos = re.findall(r"^async def (demo_\w+)|^def (demo_\w+)", block, re.MULTILINE)
        names = [a or b for a, b in demos]
        if not names:
            return block
        main_name = names[-1]
        is_async = f"async def {main_name}" in block
        if is_async:
            runner = (
                f"\n\nif __name__ == \"__main__\":\n"
                f"    import asyncio\n"
                f"    asyncio.run({main_name}())\n"
            )
        else:
            runner = f"\n\nif __name__ == \"__main__\":\n    {main_name}()\n"
        # Insert before final newline of block content
        return block.rstrip() + runner

    parts = []
    last = 0
    for m in re.finditer(r"```python\n([\s\S]*?)```", text):
        parts.append(text[last : m.start()])
        inner = m.group(1)
        if "def demo_" in inner or "async def demo_" in inner:
            inner = fix_block(inner)
        parts.append("```python\n" + inner + "```")
        last = m.end()
    parts.append(text[last:])
    return "".join(parts)


def add_blog_footer(text: str, num: int) -> str:
    if num not in BLOG_POST:
        return text
    post = BLOG_POST[num]
    footer = (
        f"\n## 博客版补充\n\n"
        f"动手实践版 [`{post}`](../src/posts/ai-ml/{post})"
        f"含系列链接、动手路径与可运行代码。"
    )
    if num in LAB_FOOTER:
        footer += LAB_FOOTER[num]
    if has_marker(text, "## 博客版补充"):
        return text
    # Before ## 下一步
    m = re.search(r"\n## 下一步\n", text)
    if m:
        return text[: m.start()] + footer + text[m.start() :]
    return text + footer


def add_narrative_standard_sections(text: str, num: int) -> str:
    """Add 你会学到什么 / 最小示例 anchors for 237-240 narrative docs."""
    if num not in NARRATIVE_DOCS:
        return text
    if has_marker(text, "## 你会学到什么"):
        return text
    learning = {
        237: (
            "## 你会学到什么\n\n"
            "- 说清楚 Memory 删除要清理哪些系统（库、向量、缓存、备份）。\n"
            "- 设计可审计、可重试的删除管道。\n"
            "- 实现用户可发起、可追踪的删除请求。\n"
            "- 满足隐私合规（可删、可追溯）。\n\n"
            "## 最小示例\n\n"
            "> 本篇叙事结构为「是什么→为什么→怎么做」。"
            "可运行删除 demo 见 §怎么做 末尾 `demo_memory_deletion()`。\n\n"
            "## 工程化版本\n\n"
            "> 完整五阶段删除管道、Outbox 与审计见 §怎么做 工程实现小节。\n\n"
        ),
        238: (
            "## 你会学到什么\n\n"
            "- 区分 Agentic RAG 与普通 RAG 的决策循环。\n"
            "- 说出四个核心组件与两项基础设施。\n"
            "- 为 239–242 各专题建立全局地图。\n"
            "- 判断何时不必上 Agentic RAG。\n\n"
            "> **动手：** 组件实现与可运行代码见 "
            "[239 Query Planning](239.query-planning-rag-agent-tutorial.md) 起，"
            "及 [`examples/rag-agent-lab`](../examples/rag-agent-lab/)。\n\n"
            "## 最小示例\n\n"
            "> 本篇为概念总览；最小可运行切片见文末 `demo_agentic_rag()` 与 239+ lab。\n\n"
            "## 工程化版本\n\n"
            "> 四组件工程化展开见 §怎么做 与 239–242。\n\n"
        ),
    }
    if num not in learning:
        if num in (239, 240):
            block = (
                "## 你会学到什么\n\n"
                "- 理解本篇「是什么/为什么/怎么做」主线。\n"
                "- 能对照 `examples/rag-agent-lab` 跑通对应 `main.py`。\n\n"
                "## 最小示例\n\n"
                "> 可运行代码见文首「博客实践版」与 lab；下文「怎么做」讲设计。\n\n"
                "## 工程化版本\n\n"
                "> 见 §怎么做 与博客版综合实战。\n\n"
            )
        else:
            return text
    else:
        block = learning[num]

    # Insert after 目录 block (after first --- following 目录)
    m = re.search(r"(## 目录\n[\s\S]*?---\n\n)", text)
    if m:
        return text[: m.end()] + block + text[m.end() :]
    return text


def apply_specific_fixes(text: str, num: int) -> str:
    fixes: list[tuple[str, str]] = []
    if num == 216:
        fixes.append(
            (
                "   Agent 成功率 ~70-80%",
                "   Agent 成功率常见约 70–80%（视任务与工具质量而定，非固定统计）",
            )
        )
        fixes.append(
            (
                "   1000 次/天 × 30 天 = 节省 $3000-15000/月",
                "   1000 次/天 × 30 天 ≈ 节省 $3000–15000/月（**估算示例**，假设单次 Agent $0.1–0.5、API 近零边际）",
            )
        )
    if num == 217:
        fixes.append(
            (
                """    def _rate_limit_check(self, user_id: str) -> bool:
        count = self._request_counts.get(user_id, 0)
        if count >= self.rate_limit:
            return False
        self._request_counts[user_id] = count + 1
        return True""",
                """    def _rate_limit_check(self, user_id: str) -> bool:
        # 教程简化：生产环境应使用滑动窗口或令牌桶，并定期重置计数
        count = self._request_counts.get(user_id, 0)
        if count >= self.rate_limit:
            return False
        self._request_counts[user_id] = count + 1
        return True""",
            )
        )
    if num == 238:
        fixes.append(("间自己三个问题", "问自己三个问题"))
        # Fix infographic narrative in prose - add note about sufficiency
        old = (
            "如果足够，它生成答案并验证每个引用是否真的被证据支持。"
            "如果不够，它会继续检索，直到证据充分或者达到预算上限。"
        )
        new = (
            "如果足够，它生成答案并验证每个引用是否真的被证据支持。"
            "如果不够（例如只查到高级套餐、还没查到基础套餐），它会继续检索，"
            "直到证据充分或者达到预算上限——**不能**在对比类任务只查到一侧就判「充分」。"
        )
        if old in text:
            fixes.append((old, new))
    if num == 218:
        # Align test section with sync ToolDefinition API
        text = text.replace("AsyncToolExecutor", "ToolExecutor")
        text = text.replace("class TestToolExecutor(unittest.IsolatedAsyncioTestCase):", "class TestToolExecutor(unittest.TestCase):")
        text = text.replace("    async def test_successful_execution(self):", "    def test_successful_execution(self):")
        text = text.replace("        async def mock_search(query: str) -> str:", "        def mock_search(query: str = \"\") -> str:")
        text = text.replace("        result = await self.executor.execute(", "        result = self.executor.execute(")
        text = text.replace("    async def test_missing_tool_returns_error(self):", "    def test_missing_tool_returns_error(self):")
        text = text.replace("    async def test_timeout_returns_error(self):", "    def test_timeout_returns_error(self):")
        text = text.replace(
            """        async def slow_tool() -> str:
            await asyncio.sleep(10)
            return "done"

        self.registry.register(ToolDefinition(
            name="slow",
            description="Slow tool",
            parameters={},
            handler=slow_tool,
            timeout=0.1,
        ))""",
            """        def slow_tool() -> str:
            import time
            time.sleep(10)
            return "done"

        self.registry.register(ToolDefinition(
            name="slow",
            description="Slow tool",
            fn=slow_tool,
            parameters=[],
            timeout_ms=100,
        ))""",
        )
        text = text.replace("    async def test_exception_is_caught(self):", "    def test_exception_is_caught(self):")
        text = text.replace("        async def broken_tool() -> str:", "        def broken_tool() -> str:")
        text = re.sub(
            r'self\.registry\.register\(ToolDefinition\(\s*name="search",\s*description="Search the web",\s*parameters=\{"query": \{"type": "string"\}\},\s*handler=mock_search,\s*\)\)',
            'self.registry.register(ToolDefinition(\n            name="search",\n            description="Search the web",\n            fn=mock_search,\n            parameters=[ToolParameter("query", "string", required=True)],\n        ))',
            text,
        )
        text = re.sub(
            r'self\.registry\.register\(ToolDefinition\(\s*name="broken",\s*description="Broken tool",\s*parameters=\{\},\s*handler=broken_tool,\s*\)\)',
            'self.registry.register(ToolDefinition(\n            name="broken",\n            description="Broken tool",\n            fn=broken_tool,\n            parameters=[],\n        ))',
            text,
        )
        if "from unittest.mock import AsyncMock" in text:
            text = text.replace("from unittest.mock import AsyncMock, patch", "from unittest.mock import patch")
    if num == 231:
        # Remove duplicate 调优 section - keep first, remove second header block
        dup = "\n## 停止条件调优指南\n"
        if text.count(dup) > 1:
            first = text.find(dup)
            second = text.find(dup, first + 1)
            # find end of second section (next ## or EOF)
            nxt = re.search(r"\n## ", text[second + len(dup) :])
            end = second + len(dup) + (nxt.start() if nxt else len(text))
            text = text[:second] + text[end:]
    if num == 250:
        platform = (
            "\n> **累积工程：** 本篇为 `examples/agent-platform/` 的起点。"
            "251–254 在同一 `shared/` 包上扩展，见各篇「沿用组件」表。\n"
        )
        if "examples/agent-platform" not in text:
            text = text.replace("**环境要求：**", platform + "\n**环境要求：**", 1)
    for old, new in fixes:
        text = text.replace(old, new)
    return text


def add_platform_links_251_254(text: str, num: int) -> str:
    if num < 251 or num > 254:
        return text
    if "examples/agent-platform" in text:
        return text
    block = (
        f"\n> **累积工程：** 基于 [250](250.build-knowledge-base-agent-tutorial.md) 的 "
        f"`examples/agent-platform/shared/`，本篇新增 `demos/demo_{num}.py`。\n"
    )
    return text.replace("**环境要求：**", block + "\n**环境要求：**", 1)


def add_238_series_header(text: str, num: int) -> str:
    if num != 238:
        return text
    if "agent-rag-series" in text:
        return text
    link = (
        "\n> **系列导读：** [Agent/RAG 工程系列 238–254]"
        "(../src/posts/ai-ml/agent-rag-series-238-254.md) · "
        "[`examples/rag-agent-lab`](../examples/rag-agent-lab/)\n"
    )
    return text.replace("**环境要求：**", link + "\n**环境要求：**", 1)


def process_doc(num: int, dry_run: bool = False) -> str:
    path = doc_path(num)
    text = path.read_text(encoding="utf-8")
    text = insert_after_env_block(text, build_meta_block(num))
    text = add_narrative_standard_sections(text, num)
    text = add_238_series_header(text, num)
    text = add_platform_links_251_254(text, num)
    text = move_02_flow_to_problem_section(text, num)
    text = add_post_image_conclusions(text)
    text = add_code_preamble_before_first_python_in_minimal(text)
    text = add_demo_main_entries(text)
    text = add_blog_footer(text, num)
    text = apply_specific_fixes(text, num)
    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return path.name


def main() -> int:
    dry = "--dry-run" in sys.argv
    nums = SERIES_DOCS
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        nums = [int(sys.argv[1])]
    for n in nums:
        name = process_doc(n, dry_run=dry)
        print(f"{'[dry] ' if dry else ''}OK {n} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
