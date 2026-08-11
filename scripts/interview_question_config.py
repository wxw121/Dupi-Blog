"""Configuration for docs/interview/ question generation."""

from __future__ import annotations

# 每篇默认最少题数
DEFAULT_MIN_QUESTIONS = 5

# 热点篇：在默认基础上额外增加的题数（不设上限，由生成器按素材继续补充）
HOT_EXTRA_QUESTIONS: dict[int, int] = {
    # 基础 / 工程化
    3: 3,   # asyncio
    5: 2,   # REST API
    8: 2,   # PostgreSQL
    11: 2,  # Docker Compose
    # RAG 核心链路
    17: 4,
    36: 3,
    57: 2,
    61: 2,
    75: 4,  # FAISS
    81: 3,  # pgvector
    93: 5,  # hybrid search
    94: 3,  # RRF
    95: 4,  # cross-encoder rerank
    96: 3,
    104: 3,
    112: 3,
    125: 4,  # LangChain
    139: 4,  # RAGAS
    156: 3,
    185: 3,
    199: 4,  # Graph RAG
    213: 4,  # Agentic RAG intro
    # Agent 全系列偏高频
    **{n: 4 for n in range(214, 255)},
}

# 热点篇中的「超高频」：再额外 +2
ULTRA_HOT: set[int] = {
    93, 95, 125, 139, 199, 213,
    217, 218, 226, 227, 238, 239, 240, 241, 243, 247, 250,
}


def target_question_count(article_num: int) -> int:
    base = DEFAULT_MIN_QUESTIONS
    extra = HOT_EXTRA_QUESTIONS.get(article_num, 0)
    if article_num in ULTRA_HOT:
        extra += 2
    return base + extra
