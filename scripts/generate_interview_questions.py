#!/usr/bin/env python3
"""Generate docs/interview/*-interview.md — developer interview Q&A from tutorial content.

Questions target **backend / AI application engineering** interviews:
concept, design, trade-off, implementation, troubleshooting — not "did you read the article".

Usage:
  python scripts/generate_interview_questions.py
  python scripts/generate_interview_questions.py --only 93 218
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "interview"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from interview_question_config import target_question_count  # noqa: E402

TUTORIAL_RE = re.compile(r"^(\d+)\.(.+?)-tutorial(?:（front-end）)?\.md$")
GLOSSARY_RE = re.compile(
    r"\*\*([^*]+)\*\*（([^）]+)）[:：]([^\n]+)(?:\n通俗说[:：]([^\n]+))?",
    re.M,
)
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.M)
INTERVIEW_BLOCK_RE = re.compile(
    r"##\s*面试怎么讲\s*\n+([\s\S]*?)(?=\n##\s|\Z)",
    re.M,
)
BOUNDARY_RE = re.compile(
    r"(?:本文边界|本文不讲|本文讲[:：]|2\.\s*本文边界)[^\n]*\n+([\s\S]*?)(?=\n##\s|\n---|\Z)",
    re.M,
)
FAIL_RE = re.compile(
    r"##\s*[^\n]*(?:失败|翻车|陷阱|误用|FAQ|先错对对)[^\n]*\n+([\s\S]*?)(?=\n##\s|\Z)",
    re.M,
)
LEARN_RE = re.compile(
    r"(?:你会学到什么|读完本文[^：\n]*[:：]|读完本篇[^：\n]*[:：])\s*\n+([\s\S]*?)(?=\n##\s|\Z)",
    re.M,
)
TABLE_ROW_RE = re.compile(r"^\|([^|]+)\|([^|]+)\|", re.M)
BULLET_RE = re.compile(r"^[-*]\s+(.+)$", re.M)
CODE_FENCE = re.compile(r"```[\s\S]*?```", re.M)
INLINE_CODE = re.compile(r"`[^`]+`")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

SKIP_HEADINGS = {
    "目录",
    "下一步",
    "系列下一步",
    "总结与系列下一步",
    "博客版补充",
    "学习目标自检",
    "读路径自检",
    "动手作业",
    "前言",
    "本文边界与动手路径",
}

DESIGN_HEADING_KW = (
    "工程",
    "生产",
    "最小",
    "架构",
    "流程",
    "评测",
    "融合",
    "实现",
    "模式",
    "伪代码",
    "部署",
    "观测",
    "权限",
    "队列",
    "索引",
    "检索",
    "分块",
    "提取",
)


@dataclass
class Term:
    name: str
    en: str
    definition: str
    tongsu: str = ""


@dataclass
class Question:
    title: str
    category: str
    difficulty: str
    answer: str
    followups: list[str] = field(default_factory=list)
    source_hint: str = ""


@dataclass
class ParsedTutorial:
    num: int
    slug: str
    filename: str
    title: str
    terms: list[Term]
    headings: list[str]
    learn_points: list[str]
    out_of_scope: list[str]  # 本篇不讲 / 不展开
    failure_lines: list[str]
    interview_raw: str
    prose_snippets: list[str]
    table_scenarios: list[str]


def article_num(path: Path) -> int | None:
    m = TUTORIAL_RE.match(path.name)
    return int(m.group(1)) if m else None


def short_topic(title: str) -> str:
    t = title.strip()
    if "：" in t:
        t = t.split("：", 1)[1]
    elif ":" in t and "http" not in t.lower():
        t = t.split(":", 1)[1]
    t = re.sub(r"完全指南$|教程$|入门$", "", t).strip()
    return t[:32] if len(t) > 32 else t


def clean_heading(text: str) -> str:
    h = strip_md_noise(text)
    h = re.sub(r"^\d+(\.\d+)*\s*", "", h)
    h = re.sub(r"^\.\s*", "", h)
    return h.strip()


def strip_md_noise(text: str) -> str:
    text = CODE_FENCE.sub("", text)
    text = INLINE_CODE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"。{2,}", "。", text)
    return text


def extract_title(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return strip_md_noise(m.group(1)) if m else "未命名主题"


def extract_terms(text: str) -> list[Term]:
    terms: list[Term] = []
    seen: set[str] = set()
    for m in GLOSSARY_RE.finditer(text):
        name = m.group(1).strip()
        if name in seen or len(name) > 40:
            continue
        seen.add(name)
        terms.append(
            Term(
                name=name,
                en=m.group(2).strip(),
                definition=strip_md_noise(m.group(3)),
                tongsu=strip_md_noise(m.group(4) or ""),
            )
        )
    return terms


def extract_headings(text: str) -> list[str]:
    out: list[str] = []
    for m in HEADING_RE.finditer(text):
        h = clean_heading(m.group(2))
        if h in SKIP_HEADINGS or len(h) < 4:
            continue
        if any(h.startswith(x) for x in ("核心术语", "你会学到", "读下图")):
            continue
        if h not in out:
            out.append(h)
    return out


def section_bullets(block: str, limit: int = 8) -> list[str]:
    items: list[str] = []
    for m in BULLET_RE.finditer(block):
        line = strip_md_noise(m.group(1))
        if 12 <= len(line) <= 200 and line not in items:
            items.append(line)
        if len(items) >= limit:
            break
    if not items:
        for para in re.split(r"\n\s*\n", block):
            p = strip_md_noise(para)
            if 30 <= len(p) <= 300:
                items.append(p)
            if len(items) >= limit:
                break
    return items


def extract_table_scenarios(text: str, limit: int = 6) -> list[str]:
    rows: list[str] = []
    for m in TABLE_ROW_RE.finditer(text):
        c1, c2 = strip_md_noise(m.group(1)), strip_md_noise(m.group(2))
        if c1 in {"信号", "步骤", "场景", "问题", "用户问题", "维度", "---", "------", "本篇讲", "本篇不讲"}:
            continue
        if "---" in c1 or len(c1) < 2:
            continue
        row = f"{c1} → {c2}" if c2 else c1
        if row not in rows:
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def extract_out_of_scope(text: str) -> list[str]:
    items: list[str] = []
    for m in re.finditer(r"\*\*本篇不讲[:：]\*\*\s*([^\n]+)", text):
        items.append(strip_md_noise(m.group(1)))
    for m in re.finditer(r"本文不讲[:：]\s*([^\n]+)", text):
        items.append(strip_md_noise(m.group(1)))
    m = BOUNDARY_RE.search(text)
    if m:
        for row in TABLE_ROW_RE.finditer(m.group(1)):
            c1, c2 = strip_md_noise(row.group(1)), strip_md_noise(row.group(2))
            if c1 == "本篇不讲" and c2:
                items.append(c2)
    for b in section_bullets(text, limit=20):
        if b.startswith("本文不展开") or "不讲" in b[:12]:
            items.append(b)
    return items[:6]


def is_faq_style(line: str) -> bool:
    return bool(re.search(r"[？?]|吗\s*$|能不能|是否应该|要不要", line))


def is_incident_line(line: str) -> bool:
    if is_faq_style(line):
        return False
    if re.match(r"^(原因|解决|症状|步骤|追问)[:：]", strip_md_noise(line)):
        return False
    if len(line) < 25:
        return False
    return True


def terms_comparable(a: Term, b: Term) -> bool:
    if a.name == b.name:
        return False
    if a.name in b.name or b.name in a.name:
        return False
    return True


def parse_faq_line(line: str) -> tuple[str, str] | None:
    """Parse FAQ like '**问题？** 答案' or '问：…'"""
    line = strip_md_noise(line)
    m = re.match(r"^\*\*(.+?[？?])\*\*\s*(.+)$", line)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"^(.+?[？?])\s+(.+)$", line)
    if m and len(m.group(1)) < 80:
        return m.group(1), m.group(2)
    return None


def parse_interview_block(raw: str) -> list[Question]:
    if not raw.strip():
        return []
    qs: list[Question] = []
    current_q = ""
    current_a: list[str] = []
    followups: list[str] = []

    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("问：") or s.startswith("问:"):
            if current_q and current_a:
                qs.append(_pack_interview_q(current_q, current_a, followups))
            current_q = strip_md_noise(s[2:])
            current_a = []
            followups = []
        elif s.startswith("答") and ("：" in s or ":" in s):
            part = re.split(r"[：:]", s, maxsplit=1)[-1].strip()
            if part:
                current_a.append(part)
            elif not current_a:
                current_a.append("")
        elif s.startswith("追问"):
            followups.append(strip_md_noise(re.sub(r"^追问\s*\d*\s*[：:→]\s*", "", s)))
        elif s.startswith("→") or s.startswith("->"):
            extra = strip_md_noise(s.lstrip("→-> ").strip())
            if followups:
                followups[-1] += " " + extra
            elif current_a:
                current_a[-1] = (current_a[-1] + " " + extra).strip()
        elif s and current_q and not s.startswith("```"):
            if current_a:
                current_a[-1] = (current_a[-1] + " " + strip_md_noise(s)).strip()
            else:
                current_a.append(strip_md_noise(s))

    if current_q and current_a:
        qs.append(_pack_interview_q(current_q, current_a, followups))
    return qs


def _pack_interview_q(q: str, a: list[str], followups: list[str]) -> Question:
    return Question(
        title=q,
        category="综合题",
        difficulty="高频",
        answer="\n".join(a).strip(),
        followups=followups[:3],
        source_hint="系统设计 / 表述",
    )


def unwrap_interview_raw(raw: str) -> str:
    m = re.search(r"```(?:text)?\s*\n([\s\S]*?)```", raw)
    return m.group(1) if m else raw


def parse_tutorial(path: Path) -> ParsedTutorial:
    text = path.read_text(encoding="utf-8")
    num = article_num(path) or 0
    slug = TUTORIAL_RE.match(path.name).group(2)  # type: ignore[union-attr]

    learn_block = ""
    m = LEARN_RE.search(text)
    if m:
        learn_block = m.group(1)

    failure_parts = [m.group(1) for m in FAIL_RE.finditer(text)]
    failure_block = "\n".join(failure_parts)

    interview_raw = ""
    m = INTERVIEW_BLOCK_RE.search(text)
    if m:
        interview_raw = unwrap_interview_raw(m.group(1))

    prose_snippets: list[str] = []
    headings = extract_headings(text)
    for h in headings[:14]:
        hm = re.search(rf"^##\s+.*{re.escape(h)}.*\n+([\s\S]*?)(?=\n##\s|\Z)", text, re.M)
        if hm:
            prose_snippets.extend(section_bullets(hm.group(1), limit=2))

    return ParsedTutorial(
        num=num,
        slug=slug,
        filename=path.name,
        title=extract_title(text),
        terms=extract_terms(text),
        headings=headings,
        learn_points=section_bullets(learn_block, limit=8),
        out_of_scope=extract_out_of_scope(text),
        failure_lines=[
            strip_md_noise(x)
            for x in section_bullets(failure_block, limit=10)
            if "```" not in x and len(strip_md_noise(x)) > 10
        ][:8],
        interview_raw=interview_raw,
        prose_snippets=prose_snippets[:12],
        table_scenarios=extract_table_scenarios(text, limit=6),
    )


# ── Question builders (developer interview style) ──────────────────────────


def q_from_term(term: Term, topic: str) -> Question:
    answer = (
        f"**{term.name}**（{term.en}）：{term.definition}"
        + (f"\n\n直觉：{term.tongsu}" if term.tongsu else "")
        + f"\n\n**工程语境（{topic}）**：\n"
        f"- 解决什么：把「{term.name}」讲清楚时，要落到 **输入/输出、放在链路哪一层、失败时怎么办**；\n"
        f"- 常见误用：只会背定义，说不出和相邻组件的分工；\n"
        f"- 加分项：举一个线上或 demo 中的真实调用点（接口、配置项、监控指标）。"
    )
    return Question(
        title=f"什么是 {term.name}？在 {topic} 相关系统里它承担什么职责？",
        category="概念题",
        difficulty="基础",
        answer=answer,
        followups=[
            f"{term.name} 和容易混淆的替代方案怎么选？",
            f"如果去掉 {term.name} 这一层，最先坏掉的是哪一环？",
        ],
        source_hint=f"核心概念 · {term.name}",
    )


def learn_to_implementation_q(point: str, topic: str) -> Question:
    p = strip_md_noise(point).rstrip("。")
    p = re.sub(r"^[•\-\d\.]+\s*", "", p)
    if re.match(r"^(设计|实现|理解|掌握|说出|列出|跑通|区分)", p):
        title = f"请说明在 {topic} 场景下如何{p}。"
    else:
        title = f"在 {topic} 相关开发中，{p}——你会如何实现或验证？"
    return Question(
        title=title[:120],
        category="实现题",
        difficulty="中等",
        answer=(
            f"**考察点**：{p}\n\n"
            "**建议回答结构**：\n"
            "1. **接口/数据**：关键入参、出参、状态字段；\n"
            "2. **流程**：主路径 + 异常路径（超时、空结果、权限拒绝）；\n"
            "3. **代码层落点**：放在哪一层（API / Service / Worker / SDK）；\n"
            "4. **验证**：单测 + 集成测 + 一条可观测指标（日志字段或 metric）。\n\n"
            "尽量用「我们服务里 X 模块负责 Y」的方式讲，避免空泛形容词。"
        ),
        followups=["如果 QPS 翻倍，你会先改哪一段？", "有哪些必须写进 Code Review checklist 的点？"],
        source_hint="工程能力",
    )


def q_tech_boundary(topic: str, out_of_scope: list[str]) -> Question:
    scope = "\n".join(f"- {x}" for x in out_of_scope[:5])
    return Question(
        title=f"做 {topic} 时，哪些能力应在当前服务内实现，哪些应下沉到专用组件或另开服务？",
        category="架构边界",
        difficulty="中等",
        answer=(
            f"考察 **分层与职责单一**，避免一个服务包揽 {topic} 全链路。\n\n"
            f"**通常不在同一层硬做的**（示例）：\n{scope or '- 鉴权/计费/长事务编排应外置\\n- 重型模型训练与在线推理分离'}\n\n"
            "**答题要点**：\n"
            "- 当前层只保留 **决策 + 编排 + 领域状态**；\n"
            "- IO 密集（向量库、对象存储、消息队列）通过稳定接口调用；\n"
            "- 说清楚 **同步调用 vs 异步任务** 的切分依据（延迟预算、失败重试）。"
        ),
        followups=["团队很小、没有平台组时，边界会不会变？怎么避免过度拆分？"],
        source_hint="架构分层",
    )


def q_from_faq(line: str, topic: str) -> Question:
    parsed = parse_faq_line(line)
    if parsed:
        q_text, a_text = parsed
        return Question(
            title=q_text,
            category="概念题",
            difficulty="中等",
            answer=a_text,
            followups=[f"在 {topic} 项目里你实际遇到过吗？最后怎么定的？"],
            source_hint="常见误区",
        )
    return Question(
        title=f"{line[:80]}{'…' if len(line) > 80 else ''}",
        category="概念题",
        difficulty="中等",
        answer=(
            f"**问题本质**：{line}\n\n"
            "**工程视角**：\n"
            "- 先区分是 **配置/数据/代码逻辑** 哪类问题；\n"
            "- 给出可落地的判断标准（阈值、日志、评测指标），不要只给「看情况」。"
        ),
        followups=["有没有对应的监控或告警规则？"],
        source_hint="FAQ",
    )


def q_from_incident(line: str, topic: str) -> Question:
    return Question(
        title=f"生产环境 {topic} 出现：{line[:60]}… —— 排查思路是什么？",
        category="排障题",
        difficulty="中等",
        answer=(
            f"**现象摘要**：{line}\n\n"
            "**排查顺序**：\n"
            "1. **范围**：影响面、开始时间、是否可回滚；\n"
            "2. **证据链**：请求 ID → 各 hop 日志（网关 / 应用 / 向量库 / 模型 / 工具）；\n"
            "3. **分层假设**：数据污染、配置变更、依赖超时、逻辑 bug——每次只验证一个；\n"
            "4. **止血**：降级（缓存答案、缩小 top_k、关闭非关键工具）、限流；\n"
            "5. **根因与回归**：补集成测试 + 告警阈值。"
        ),
        followups=["如何写一份给 on-call 的 runbook？", "哪些信息必须打进结构化日志？"],
        source_hint="线上排障",
    )


def q_from_design(heading: str, snippets: list[str], topic: str) -> Question:
    ctx = snippets[0] if snippets else ""
    h = clean_heading(heading)
    if len(h) < 4:
        h = heading
    return Question(
        title=f"如何设计/实现「{h}」？（{topic}）",
        category="设计题",
        difficulty="中等",
        answer=(
            (f"**背景要点**：{ctx}\n\n" if ctx else "")
            + "**设计回答框架**：\n"
            "1. **目标与约束**：延迟、准确率、成本、团队规模；\n"
            "2. **组件图**：列出 3～5 个模块及数据流（可手绘）；\n"
            "3. **关键接口**：同步 API / 消息 / 批处理任务各负责什么；\n"
            "4. **失败与降级**：超时、空检索、工具失败时的默认策略；\n"
            "5. **评测**：离线指标 + 线上 shadow / 金丝雀。"
        ),
        followups=["MVP 版本可以砍掉哪些部分？", "10x 流量时最先改什么？"],
        source_hint=f"工程设计 · {h[:20]}",
    )


def q_compare_terms(a: Term, b: Term, topic: str) -> Question:
    return Question(
        title=f"{a.name} 和 {b.name} 有什么区别？在 {topic} 里如何选型？",
        category="对比题",
        difficulty="中等",
        answer=(
            f"| 维度 | {a.name} | {b.name} |\n"
            f"|------|----------|----------|\n"
            f"| 定义 | {a.definition[:80]} | {b.definition[:80]} |\n"
            f"| 适用 | 见具体场景约束 | 见具体场景约束 |\n\n"
            "**选型建议**：\n"
            "- 用 **输入形态**（精确词 vs 语义改写）、**延迟预算**、**运维成本** 三张表说话；\n"
            "- 给出「默认选谁 + 何时叠加谁」，必要时 Hybrid；\n"
            "- 用评测集证明，而不是团队偏好。"
        ),
        followups=["能否画一张两路召回合并的时序图？", "线上如何做 A/B？"],
        source_hint=f"对比 · {a.name} vs {b.name}",
    )


def q_from_scenario(scenario: str, topic: str) -> Question:
    return Question(
        title=f"场景题：{scenario[:70]}… —— 在 {topic} 架构下你怎么处理？",
        category="场景题",
        difficulty="中等",
        answer=(
            f"**场景**：{scenario}\n\n"
            "**答题要点**：\n"
            "- 先复述用户目标与约束（权限、延迟、是否允许拒答）；\n"
            "- 给出 **数据流**：从请求进入到返回证据/答案；\n"
            "- 点出 1～2 个容易翻车的配置（top_k、filter、超时）；\n"
            "- 说明如何 **验收**（命中率、引用正确率、P95）。"
        ),
        followups=["如果证据不足，拒答还是让模型自由发挥？依据是什么？"],
        source_hint="业务场景",
    )


def q_production(topic: str, snippets: list[str]) -> Question:
    hint = snippets[0] if snippets else "稳定性与可观测"
    return Question(
        title=f"{topic} 能力要上生产，你会优先保证哪三件事？",
        category="生产化",
        difficulty="高频",
        answer=(
            f"结合 {topic} 常见风险点：{hint}\n\n"
            "**推荐三件事**：\n"
            "1. **SLO 与降级**：定义 P95/P99、错误预算；检索失败/模型超时时的兜底路径；\n"
            "2. **可观测**：trace_id 贯穿；记录检索命中、token、工具调用、人工介入；\n"
            "3. **变更安全**：配置与 Prompt 版本化；灰度 + 自动回滚条件；回归评测门禁。\n\n"
            "面试时用 **一个真实指标** 收尾（如 citation 准确率、empty retrieval 率）。"
        ),
        followups=["如何做成本归因到租户/业务线？", "on-call 值班最需要哪三张大盘？"],
        source_hint="生产落地",
    )


def q_system_overview(topic: str, headings: list[str]) -> Question:
    parts = [h for h in headings if len(h) > 3 and "前言" not in h][:4]
    chain = " → ".join(parts) if parts else f"{topic} 主链路"
    return Question(
        title=f"用 2 分钟讲清楚 {topic} 的技术方案（面向面试官）。",
        category="综合题",
        difficulty="高频",
        answer=(
            "**30 秒版**：问题背景 → 核心组件 → 一条量化结果。\n\n"
            f"**2 分钟版**（可按链路讲）：{chain}\n\n"
            "每层补一句：**输入输出 + 失败怎么办**。\n"
            "避免背章节标题；用「请求进来以后……」的叙事更自然。"
        ),
        followups=["如果面试官只给白板，你会先画哪张图？", "你最自豪的一次优化是什么？"],
        source_hint="技术表述",
    )


def build_questions(parsed: ParsedTutorial) -> list[Question]:
    topic = short_topic(parsed.title)
    target = target_question_count(parsed.num)
    questions: list[Question] = []
    used: set[str] = set()

    def add(q: Question) -> None:
        key = q.title[:90]
        if key in used:
            return
        used.add(key)
        questions.append(q)

    # 1. 教程内嵌的高频面试话术（质量最高）
    for q in parse_interview_block(parsed.interview_raw):
        add(q)

    # 2. 核心概念
    for term in parsed.terms[:4]:
        add(q_from_term(term, topic))

    # 3. 实现/工程能力（由学习目标转化，不问「你是否读完」）
    for point in parsed.learn_points[:4]:
        add(learn_to_implementation_q(point, topic))

    # 4. 设计题（工程向章节）
    design_heads = [
        h for h in parsed.headings
        if len(h) >= 5 and any(k in h for k in DESIGN_HEADING_KW)
    ]
    for i, h in enumerate(design_heads[:4]):
        add(q_from_design(h, parsed.prose_snippets[i : i + 1], topic))

    # 5. FAQ → 概念；其余 → 排障
    for line in parsed.failure_lines[:4]:
        if is_faq_style(line):
            add(q_from_faq(line, topic))
        elif is_incident_line(line):
            add(q_from_incident(line, topic))

    # 6. 架构边界（技术分层，非「教程边界」）
    if parsed.out_of_scope:
        add(q_tech_boundary(topic, parsed.out_of_scope))

    # 7. 术语对比 / 场景题
    if len(parsed.terms) >= 2 and terms_comparable(parsed.terms[0], parsed.terms[1]):
        add(q_compare_terms(parsed.terms[0], parsed.terms[1], topic))
    for sc in parsed.table_scenarios[:2]:
        add(q_from_scenario(sc, topic))

    # 8. 生产化 + 串讲
    add(q_production(topic, parsed.prose_snippets))
    add(q_system_overview(topic, parsed.headings))

    # 补足题量
    idx = 0
    pools: list[tuple[str, object]] = (
        [("term", t) for t in parsed.terms]
        + [("learn", p) for p in parsed.learn_points]
        + [("design", h) for h in design_heads]
        + [("fail", l) for l in parsed.failure_lines]
        + [("scenario", s) for s in parsed.table_scenarios]
    )
    while len(questions) < target and idx < len(pools) * 3:
        kind, item = pools[idx % len(pools)] if pools else ("overview", None)
        if kind == "term":
            add(q_from_term(item, topic))  # type: ignore[arg-type]
        elif kind == "learn":
            add(learn_to_implementation_q(item, topic))  # type: ignore[arg-type]
        elif kind == "design":
            add(q_from_design(item, parsed.prose_snippets, topic))  # type: ignore[arg-type]
        elif kind == "fail":
            line = item  # type: ignore[assignment]
            if is_faq_style(line):
                add(q_from_faq(line, topic))
            elif is_incident_line(line):
                add(q_from_incident(line, topic))
        elif kind == "scenario":
            add(q_from_scenario(item, topic))  # type: ignore[arg-type]
        else:
            add(q_system_overview(topic, parsed.headings))
        idx += 1
        if idx > target + 30:
            break

    return questions[: max(target, len(questions))]


def render_markdown(parsed: ParsedTutorial, questions: list[Question]) -> str:
    rel_tutorial = f"../{parsed.filename}"
    from interview_question_config import HOT_EXTRA_QUESTIONS, ULTRA_HOT

    hot_tag = ""
    if parsed.num in ULTRA_HOT:
        hot_tag = " · **超高频**"
    elif parsed.num in HOT_EXTRA_QUESTIONS:
        hot_tag = " · **热点**"

    lines = [
        f"# {parsed.num} {parsed.title} · 开发面试题{hot_tag}",
        "",
        f"> **知识来源**：[{parsed.filename}]({rel_tutorial})（复习用，面试不考「是否读过」）  ",
        f"> **题量**：{len(questions)} 道  ",
        "> **岗位**：后端 / AI 应用 / RAG·Agent 工程开发  ",
        "> **建议**：先口头作答，再对照「参考答法」；重点练 **设计、排障、trade-off**，不是背文档目录。",
        "",
        "---",
        "",
        "## 题目目录",
        "",
    ]
    for i, q in enumerate(questions, 1):
        t = q.title[:68] + ("…" if len(q.title) > 68 else "")
        lines.append(f"{i}. [{t}](#q{i})（{q.category}）")
    lines.extend(["", "---", ""])

    for i, q in enumerate(questions, 1):
        lines.extend(
            [
                f"### Q{i}. {q.title} {{#q{i}}}",
                "",
                "| 维度 | 说明 |",
                "|------|------|",
                f"| 类型 | {q.category} |",
                f"| 难度 | {q.difficulty} |",
                f"| 考点 | {q.source_hint} |",
                "",
                "**参考答法（开发向）：**",
                "",
                q.answer,
                "",
            ]
        )
        if q.followups:
            lines.append("**常见追问：**")
            lines.append("")
            for f in q.followups:
                lines.append(f"- {f}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "## 自测清单",
            "",
            "- [ ] 能画主链路数据流（请求 → 核心服务 → 依赖 → 返回）",
            "- [ ] 能举 1 个线上/d demo 中的真实案例",
            "- [ ] 能说出 2 个失败模式 + 排查命令/日志字段",
            "- [ ] 能讲清与相邻技术栈的分工（不要大包大揽）",
            "",
            f"**复习正文**：[{parsed.filename}]({rel_tutorial})",
            "",
        ]
    )
    return "\n".join(lines)


def interview_filename(tutorial_path: Path) -> str:
    m = TUTORIAL_RE.match(tutorial_path.name)
    assert m
    return f"{m.group(1)}.{m.group(2)}-interview.md"


def list_tutorials(only: list[int] | None = None) -> list[Path]:
    files = sorted(
        [p for p in DOCS.glob("*.md") if TUTORIAL_RE.match(p.name)],
        key=lambda p: article_num(p) or 0,
    )
    if only:
        files = [p for p in files if (article_num(p) or 0) in set(only)]
    return files


def write_index(paths: list[Path]) -> None:
    lines = [
        "# 开发面试题索引（254 篇）",
        "",
        "> 面向 **后端 / AI 应用开发** 岗位：概念、设计、实现、排障、生产化。",
        "> 由 `scripts/generate_interview_questions.py` 从教程 **技术内容** 提炼，可重复生成。",
        "",
        "---",
        "",
        "## 模块导航",
        "",
        "| 模块 | 编号 |",
        "|------|------|",
        "| 基础前置 | 1–16 |",
        "| RAG 数据采集 | 17–62 |",
        "| Embedding 与索引 | 63–92 |",
        "| 检索与生成 | 93–124 |",
        "| 框架与评测 | 125–155 |",
        "| 全栈交付 | 156–184 |",
        "| 生产与安全 | 185–198 |",
        "| 进阶 | 199–213 |",
        "| AI Agent | 214–254 |",
        "",
        "---",
        "",
        "## 全量列表",
        "",
        "| # | 面试题 | 复习教程 |",
        "|---|--------|----------|",
    ]
    for p in paths:
        n = article_num(p) or 0
        iv = interview_filename(p)
        title = short_topic(extract_title(p.read_text(encoding="utf-8")))
        lines.append(f"| {n} | [{title}]({iv}) | [{p.name}](../{p.name}) |")
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", type=int, nargs="*", help="regenerate specific article numbers")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    tutorials = list_tutorials(args.only)
    if not tutorials:
        print("No tutorials matched.")
        return 1

    stats: list[tuple[int, int]] = []
    for path in tutorials:
        parsed = parse_tutorial(path)
        questions = build_questions(parsed)
        out_path = OUT / interview_filename(path)
        md = render_markdown(parsed, questions)
        stats.append((parsed.num, len(questions)))
        if not args.dry_run:
            out_path.write_text(md, encoding="utf-8")
        print(f"[{parsed.num:>3}] {len(questions):>2} Q -> {out_path.name}")

    if not args.dry_run:
        write_index(list_tutorials())

    print(f"\nDone: {len(stats)} files, min={min(c for _, c in stats)}, max={max(c for _, c in stats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
