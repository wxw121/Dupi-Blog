#!/usr/bin/env python3
"""Second pass: glossary 通俗说, default boundaries, 收束篇 tables, cleanup."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

DEFAULT_GLOSSARY: dict[str, list[tuple[str, str, str, str]]] = {
    "part2": [
        ("Tool Calling", "工具调用", "模型输出结构化函数名与参数。", "像给助理一张办事清单，写明「去办哪件事、带什么材料」。"),
        ("幂等", "Idempotency", "同一请求执行多次与一次效果相同。", "重复点「提交」不会重复扣款。"),
    ],
    "part3": [
        ("OTA", "Observe-Think-Act", "观察环境→推理→执行行动的循环。", "看一眼→想一下→动手→再看结果。"),
        ("停止条件", "Stop Condition", "决定 Agent 何时退出循环的规则。", "像跑步机的紧急停止钮。"),
    ],
    "part4": [
        ("短期记忆", "Short-term Memory", "单会话内的上下文与任务状态。", "柜台上的便签，下班就扔。"),
        ("长期记忆", "Long-term Memory", "跨会话保留的用户偏好与事实。", "客户档案柜。"),
    ],
    "part5": [
        ("Agentic RAG", "自主检索增强", "检索策略由中间证据驱动，非固定管道。", "侦探根据线索决定下一步查哪里。"),
    ],
    "part6": [
        ("Checkpoint", "检查点", "持久化 Agent 中间状态以便恢复。", "游戏存档点。"),
        ("状态机", "State Machine", "用有限状态与转移约束 Agent 行为。", "红绿灯，不能随意乱跳。"),
    ],
    "part7": [
        ("综合实战", "End-to-end Project", "在同一代码库上交付可运行 Agent 切片。", "从零件到能跑的原型车。"),
    ],
}

PART_RANGE = {
    "part1": range(214, 218),
    "part2": range(218, 226),
    "part3": range(226, 232),
    "part4": range(232, 238),
    "part5": range(238, 244),
    "part6": range(244, 250),
    "part7": range(250, 255),
}

CLOSING_TABLES: dict[int, str] = {
    243: """
### 改前 / 改后对照（收束自检）

| 维度 | 改前（固定 RAG） | 改后（Agentic RAG + 调试） |
|------|------------------|----------------------------|
| 检索 | 一次 query→top-k | 规划子查询、多步检索 |
| 失败处理 | 直接生成，难定位 | trace 反查 + 根因分层 |
| 引用 | 可能有假引用 | 242 验证 + 243 回归用例 |
| 验收 | 人工抽检 | `python main.py 243` + 检查清单 |

**自检清单：** ① 能画出最近一次 bad case 的 trace ② 能归类到检索/规划/生成/引用 ③ 有对应回归样例。
""",
    246: """
### 旧方案 ↔ 检查点（收束对照）

| 旧写法 | 检查点写法 | 何时用 |
|--------|------------|--------|
| 内存里跑完即丢 | `save_checkpoint` / `load_checkpoint` | 长任务、进程可能重启 |
| 全靠重跑 | 从最近 checkpoint 恢复 | 人工中断、部署滚动 |
| 无状态 HTTP | 后台 job + 检查点 ID | 248 后台任务 |

可运行：`examples/rag-agent-lab` 文内 demo 或博客版 `demo_checkpoint`。
""",
    247: """
### 246 手动检查点 ↔ Temporal 持久执行

| 能力 | 246 手动 Checkpoint | 247 Temporal / Durable |
|------|----------------------|-------------------------|
| 状态存储 | 自建 JSON/DB | 平台托管 |
| 故障恢复 | 自行 load | 自动重放 |
| 运维成本 | 低（教学） | 中（生产） |
| 适用 | 原型、单进程 | 长流程、多 worker |

可运行：`cd examples/rag-agent-lab && python temporal_minimal.py`（需 Docker）。
""",
}

FLOW_02_CONCLUSION: dict[str, str] = {
    "agent-loop": "对照上图：OTA 四阶段（观察→思考→行动→评估）构成所有 Agent 模式的地基。",
    "react-agent": "对照上图：ReAct 在 OTA 的 THINK/ACT 之间插入显式 Thought 与 Observation 解析。",
    "tool-calling": "对照上图：工具从注册、校验到执行返回是一条完整生命周期。",
    "default_rag": "对照上图：RAG 擅长单次检索回答；Agent 补的是规划、分支与外部系统调用。",
}


def doc_path(num: int) -> Path:
    return list(DOCS.glob(f"{num}.*-tutorial.md"))[0]


def part_key(num: int) -> str:
    for k, rng in PART_RANGE.items():
        if num in rng:
            return k
    return "part2"


def format_glossary(items: list[tuple[str, str, str, str]]) -> str:
    lines = ["### 核心术语（本篇首次出现）"]
    for term, en, pro, plain in items:
        lines.append(f"**{term}**（{en}）：{pro}")
        lines.append(f"通俗说：{plain}")
    return "\n".join(lines)


def ensure_glossary(text: str, num: int) -> str:
    if "通俗说：" in text:
        return text
    if num in range(214, 218):
        return text  # Part 1 glossaries hand-tuned
    # Replace flat glossary or add default
    m = re.search(r"### 核心术语（本篇首次出现）\n([\s\S]*?)\n---", text)
    items = DEFAULT_GLOSSARY.get(part_key(num), DEFAULT_GLOSSARY["part2"])
    block = format_glossary(items) + "\n"
    if m:
        text = text[: m.start()] + block + "---" + text[m.end() :]
    elif "**档位：**" in text:
        text = text.replace("\n---\n\n## 目录", "\n" + block + "\n---\n\n## 目录", 1)
    return text


def fix_duplicate_flow_preamble(text: str) -> str:
    return re.sub(
        r"读下图时，看 RAG 能力边界与 Agent 要补上的多步/分支/工具能力。\n\n"
        r"读下图时，先看「[^」]*流程[^」]*」建立直觉。\n\n",
        lambda m: m.group(0).split("\n\n", 1)[0] + "\n\n",
        text,
    )


def fix_flow02_conclusion(text: str, num: int) -> str:
    path = doc_path(num)
    slug = path.stem.split(".", 1)[1].replace("-tutorial", "")
    for key, conclusion in FLOW_02_CONCLUSION.items():
        if key in slug:
            text = re.sub(
                r"(!\[[^\]]*02-[^\]]*\]\([^)]+\))\n对照上图：RAG 擅长[^\n]+\n",
                rf"\1\n{conclusion}\n",
                text,
                count=1,
            )
            break
    return text


def insert_closing_table(text: str, num: int) -> str:
    if num not in CLOSING_TABLES or CLOSING_TABLES[num].strip() in text:
        return text
    m = re.search(r"\n## 常见失败模式\n", text)
    if m:
        return text[: m.start()] + "\n" + CLOSING_TABLES[num] + text[m.start() :]
    return text


def uncomment_demos(text: str) -> str:
    # # demo_four_forms() -> demo_four_forms()
    text = re.sub(r"^# (demo_\w+\(\))\s*$", r"\1", text, flags=re.MULTILINE)
    return text


def fix_meta_newlines(text: str) -> str:
    text = re.sub(
        r"(### 核心术语[\s\S]*?)\n---\n",
        lambda m: m.group(1).rstrip() + "\n\n---\n",
        text,
        count=1,
    )
    return text


def process(num: int) -> None:
    p = doc_path(num)
    t = p.read_text(encoding="utf-8")
    t = fix_duplicate_flow_preamble(t)
    t = ensure_glossary(t, num)
    t = fix_flow02_conclusion(t, num)
    t = insert_closing_table(t, num)
    t = uncomment_demos(t)
    t = fix_meta_newlines(t)
    p.write_text(t, encoding="utf-8")


def main() -> int:
    nums = list(range(214, 255))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        nums = [int(sys.argv[1])]
    for n in nums:
        process(n)
        print(f"pass2 OK {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
