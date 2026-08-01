"""demo_citation_verify.py — 引用验证最小示例"""
import re
from openai import OpenAI

client = OpenAI()

DOCS = [
    {"source": "员工手册v3.2", "page": 12, "content": "带薪年假为15天。"},
    {"source": "考勤制度", "page": 5, "content": "年假需提前一周在系统申请。"},
]


def generate_cited_answer(question: str, docs: list[dict]) -> str:
    context = "\n".join(
        f"[{i+1}] 来源:{d['source']} p.{d['page']}\n{d['content']}"
        for i, d in enumerate(docs)
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"仅根据参考资料回答，每句事实后标注 [n]。\n\n{context}\n\n问题：{question}",
        }],
        temperature=0,
    )
    return resp.choices[0].message.content


def verify_support(claim: str, evidence: str) -> float:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"引用是否支持论点？只输出 0-1 数字。\n论点：{claim}\n引用：{evidence}",
        }],
        temperature=0,
        max_tokens=5,
    )
    try:
        return float(resp.choices[0].message.content.strip())
    except ValueError:
        return 0.5


def main():
    question = "年假有几天？如何申请？"
    answer = generate_cited_answer(question, DOCS)
    print("回答：", answer, "\n")

    for sent in re.split(r"[。！？]", answer):
        sent = sent.strip()
        if len(sent) < 6:
            continue
        refs = [int(x) for x in re.findall(r"\[(\d+)\]", sent)]
        evidence = " ".join(DOCS[r - 1]["content"] for r in refs if 0 < r <= len(DOCS))
        score = verify_support(sent, evidence) if refs else 0.0
        status = "✓" if score >= 0.7 else ("?" if refs else "✗ 无引用")
        print(f"  [{score:.2f}] {status} {sent}")


if __name__ == "__main__":
    main()
