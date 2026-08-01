"""demo_query_planning.py — 查询规划最小示例（mock 检索）"""
import json
import re
from openai import OpenAI

client = OpenAI()

MOCK_DOCS = [
    {"id": "1", "content": "2024年公司获得专利12项，其中AI相关5项。", "source": "年报2024"},
    {"id": "2", "content": "2024年上线智能客服、知识库问答等3个产品。", "source": "产品月报"},
    {"id": "3", "content": "2023年技术成果以基础设施优化为主。", "source": "年报2023"},
]


def decompose_query(question: str) -> list[dict]:
    prompt = f"""把用户问题分解为 2-4 个独立检索子查询。把相对时间转为绝对时间（假设今年是2025年）。
用户问题：{question}
输出 JSON：{{"sub_queries": [{{"query": "...", "intent": "..."}}]}}"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)["sub_queries"]


def mock_search(query: str, top_k: int = 2) -> list[dict]:
    """教学用：按关键词重叠模拟检索（非生产实现）。"""
    words = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
    scored = []
    for doc in MOCK_DOCS:
        doc_words = set(re.findall(r"[\w\u4e00-\u9fff]+", doc["content"].lower()))
        overlap = len(words & doc_words)
        if overlap:
            scored.append((overlap, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]


def answer(question: str) -> None:
    sub_queries = decompose_query(question)
    print("子查询：", json.dumps(sub_queries, ensure_ascii=False, indent=2))

    all_docs = []
    for sq in sub_queries:
        all_docs.extend(mock_search(sq["query"]))

    context = "\n".join(
        f"[{i+1}] {d['source']}: {d['content']}" for i, d in enumerate(all_docs)
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "仅根据参考资料回答，每句事实后标注 [n]。"},
            {"role": "user", "content": f"问题：{question}\n\n参考资料：\n{context}"},
        ],
        temperature=0,
    )
    print("\n回答：\n", resp.choices[0].message.content)


if __name__ == "__main__":
    answer("公司去年的技术成果有哪些？")
