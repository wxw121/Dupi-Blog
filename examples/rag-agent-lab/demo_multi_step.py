"""demo_multi_step.py — 多步检索最小示例"""
import json
from openai import OpenAI

client = OpenAI()

MOCK_INDEX = {
    "postgresql mysql 选型": [
        {"content": "架构评审倾向 PostgreSQL，提到 JSON 字段性能。", "source": "评审纪要"},
    ],
    "postgresql json 性能 测试": [
        {"content": "JSON 查询 QPS 比 MySQL 高 40%。CTO 在邮件中确认。", "source": "压测报告"},
    ],
    "cto 邮件 postgresql 决策": [
        {"content": "最终因 JSON 与扩展性选择 PostgreSQL。", "source": "CTO邮件"},
    ],
}


class MockRetriever:
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        for key, docs in MOCK_INDEX.items():
            if any(w in query.lower() for w in key.split()):
                return docs[:top_k]
        return []


def extract_findings(question: str, docs: list[dict]) -> str:
    text = "\n".join(d["content"] for d in docs)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"从文档提取与问题相关的发现与线索：\n问题：{question}\n文档：{text}"}],
        temperature=0,
        max_tokens=300,
    )
    return resp.choices[0].message.content


def decide_next(question: str, steps: list[dict]) -> dict:
    summary = "\n".join(f"Step{s['n']}: {s['query']} → {s['findings'][:120]}" for s in steps)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""问题：{question}
已完成：{summary}
信息够了吗？不够则给出 next_query。输出 JSON：{{"is_complete": bool, "next_query": "...", "reasoning": "..."}}"""}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def run(question: str, max_steps: int = 3) -> None:
    retriever = MockRetriever()
    steps = []

    docs = retriever.search(question)
    findings = extract_findings(question, docs)
    steps.append({"n": 1, "query": question, "findings": findings})
    print(f"[Step 1] {findings[:200]}...\n")

    for i in range(2, max_steps + 1):
        decision = decide_next(question, steps)
        if decision.get("is_complete"):
            print(f"[完成] {decision.get('reasoning')}")
            break
        q = decision["next_query"]
        docs = retriever.search(q)
        findings = extract_findings(question, docs)
        steps.append({"n": i, "query": q, "findings": findings})
        print(f"[Step {i}] 查询={q}\n{findings[:200]}...\n")

    print("共", len(steps), "步")


if __name__ == "__main__":
    run("为什么选 PostgreSQL 而不是 MySQL？")
