"""demo_bad_case.py — Bad Case 记录与分类最小示例"""
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class TraceRecord:
    trace_id: str
    question: str = ""
    final_answer: str = ""
    retrieval_query: str = ""
    retrieved_docs: list = field(default_factory=list)
    retrieval_scores: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


def classify_bad_case(trace: TraceRecord, issue: str) -> str:
    if not trace.retrieved_docs:
        return "retrieval_recall_failure"
    top = trace.retrieval_scores[0] if trace.retrieval_scores else 0
    if top < 0.5:
        return "retrieval_low_relevance"
    if any(w in issue for w in ["编造", "幻觉", "没有"]):
        return "generation_hallucination"
    if any(w in issue for w in ["不完整", "遗漏"]):
        return "generation_incomplete"
    if any(w in issue for w in ["理解错", "答非所问", "换货", "退货"]):
        return "understanding_error"
    return "other"


FIX_HINTS = {
    "retrieval_recall_failure": ["添加查询改写", "调整分片策略", "检查 embedding 模型"],
    "retrieval_low_relevance": ["添加 Reranker", "多路检索", "元数据过滤"],
    "generation_hallucination": ["强化 Prompt 约束", "启用引用验证(242篇)", "降低 temperature"],
    "generation_incomplete": ["减少 top_k 避免 lost-in-middle", "要求逐条分析检索结果"],
    "understanding_error": ["意图分类前置", "查询改写", "检查多轮上下文传递"],
}


def main():
    trace = TraceRecord(
        trace_id=str(uuid.uuid4()),
        question="退货政策是什么？",
        final_answer="换货需要在收到商品后7天内申请...",
        retrieval_query="退货政策",
        retrieved_docs=[{"source": "换货政策.md", "content": "换货流程..."}],
        retrieval_scores=[0.88],
    )
    issue = "问退货政策，回答了换货政策"
    category = classify_bad_case(trace, issue)
    print(f"问题：{trace.question}")
    print(f"分类：{category}")
    print(f"建议：{FIX_HINTS.get(category, ['人工排查'])}")
    if category == "understanding_error" and trace.retrieval_scores[0] > 0.8:
        print("注意：top 分数很高，建议进一步检查检索排序(见§实战案例)")


if __name__ == "__main__":
    main()
