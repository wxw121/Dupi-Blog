#!/usr/bin/env python3
"""Pass 3: spot-check fixes — formatting, 01 conclusions, Part 7 综合实战."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

COMPREHENSIVE_251_254 = {
    251: """## 综合实战

**沿用组件：** [250](250.build-knowledge-base-agent-tutorial.md) 的 `KnowledgeBaseAgent` / `shared/`。

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_251
```

**验收：** 输出 `## 研究摘要` 与至少 2 条要点 bullet。

""",
    252: """## 综合实战

**沿用组件：** [250](250.build-knowledge-base-agent-tutorial.md) `BaseAgent` + [224](224.human-in-the-loop-agent-tutorial.md) HITL 模式。

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_252
```

**验收：** 控制台出现 `[HITL]` 提示与 `refund` 成功 `ToolResult`。

""",
    253: """## 综合实战

**沿用组件：** [250](250.build-knowledge-base-agent-tutorial.md) 平台；本篇新增 diff 解析工具。

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_253
```

**验收：** 打印 `issues: ['avoid eval()']`。

""",
    254: """## 综合实战

**沿用组件：** [250–253](250.build-knowledge-base-agent-tutorial.md) + [225](225.agent-tool-permission-boundary-tutorial.md) 高风险确认。

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_254
```

**验收：** 扩容与清缓存均经 HITL 提示后返回 `success=True`。

""",
}

EXPECTED_BY_PART = {
    "part1": "**运行环境：** Python 3.10+，见文首环境要求。\n**预期输出：** 控制台打印 Level 0 RAG 与 Level 2 Agent 的步骤与结果。\n",
    "default": "**运行环境：** Python 3.10+，见文首环境要求。\n**预期输出：** 运行文末 `demo_*()` 或 `python -m demos.demo_NNN`，控制台有明确 OK/步骤输出。\n",
}


def part(n: int) -> str:
    if n < 218:
        return "part1"
    return "default"


def fix_newlines(text: str) -> str:
    text = re.sub(
        r"(\*\*动手路径：\*\*[^\n]+)\n(### )",
        r"\1\n\n\2",
        text,
    )
    text = re.sub(
        r"(\*\*本文边界：\*\*[^\n]+)\n(### )",
        r"\1\n\n\2",
        text,
    )
    return text


def fix_expected_output(text: str, n: int) -> str:
    old = "**运行环境：** Python 3.10+，见文首环境要求。**预期：** 打印各 Level 或 demo 的步骤轨迹。"
    if old not in text:
        return text
    rep = EXPECTED_BY_PART["part1" if n == 214 else "default"]
    return text.replace(old, rep)


def fix_01_conclusions(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        alt = m.group(1)
        topic = re.sub(r"核心思想|概念地图", "", alt).strip()
        if not topic:
            topic = "本专题"
        return (
            f"![{alt}]({m.group(2)})\n"
            f"对照上图：{topic}——建立本专题直觉，留意图中标注的输入/输出或对比关系，再读下文。\n"
        )

    return re.sub(
        r"!\[([^\]]*)\]\(([^)]*01-[^)]+\.png)\)\n"
        r"对照上图：[^\n]*先抓住「要解决什么矛盾」，再读下文机制与代码。\n",
        repl,
        text,
    )


def add_comprehensive(text: str, n: int) -> str:
    if n not in COMPREHENSIVE_251_254 or "## 综合实战" in text:
        return text
    block = COMPREHENSIVE_251_254[n]
    m = re.search(r"\n## 常见失败模式\n", text)
    if m:
        return text[: m.start()] + "\n" + block + text[m.start() :]
    return text


def process(n: int) -> bool:
    p = list(DOCS.glob(f"{n}.*-tutorial.md"))[0]
    t = p.read_text(encoding="utf-8")
    orig = t
    t = fix_newlines(t)
    t = fix_expected_output(t, n)
    t = fix_01_conclusions(t)
    t = add_comprehensive(t, n)
    if t != orig:
        p.write_text(t, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = []
    for n in range(214, 255):
        if process(n):
            changed.append(n)
    print("updated:", changed)


if __name__ == "__main__":
    main()
