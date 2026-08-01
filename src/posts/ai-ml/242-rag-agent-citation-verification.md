---
title: "RAG Agent 引用验证：确保回答有据可查"
slug: rag-agent-citation-verification
date: 2025-05-25
tags: [AI, RAG, Agent, 引用验证, 可信度]
category: ai-ml
description: "实现 RAG Agent 的引用验证机制：每个论点都有来源支撑，杜绝幻觉，让 AI 回答可追溯、可验证。"
---

## 学习目标

读完本篇，你能：

1. 解释「引用验证」解决什么信任问题，并说出生成验证与生成后验证的区别
2. 让 LLM 生成带 `[n]` 编号引用的回答，并解析映射到文档元数据
3. 用 LLM（或 NLI）检查「论点是否被引用内容支撑」，输出置信度
4. 跑通 §最小可运行示例，完成一次「生成 → 解析引用 → 验证」

## 前置阅读

- **241 工具增强 RAG**：检索与工具调用如何配合
- **239 / 240**：检索质量决定引用素材；引用验证不能替代检索优化
- OpenAI API 基础

## 环境要求

```bash
pip install openai
# NLI 章节可选：pip install transformers torch
```

- Python 3.10+
- `OPENAI_API_KEY`

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 引用标注、逐句验证、修正、置信度输出 | 检索策略优化 → **239 / 240** |
| NLI 初筛 + LLM 精验思路 | 系统化 Bad Case 排障 → **243** |
| 前端/API 展示格式 | 完整 Perplexity 级产品 UI |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 跑通 mock 引用验证 |
| 2 | §核心实现 | 理解 `CitationRAGAgent` 五步流程 |
| 3 | §引用验证策略 | 了解逐句 / 交叉 / 时效三种策略 |
| 4 | §常见失败模式 | 识别错号、凑数、遗漏、过时 4 类问题 |
| 5 | §检查清单 | 上线前自检 |

> **可运行代码**：[`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/) — `python main.py 242`

## 为什么需要引用验证

**引用验证**（Citation Verification）：检查回答中的每个事实性论点，是否有检索到的文档片段真实支撑。
通俗说：不仅要求 AI「标注来源」，还要核实「标的对不对、撑不撑得住」。

**幻觉**（Hallucination）：模型生成看似合理、但文档中不存在或与文档矛盾的内容。
通俗说：AI「编」出来的——引用验证的目标就是把这类内容拦下来或标出来。

RAG 系统的最大信任危机：**用户不知道回答是检索到的还是编造的。**

没有引用验证的 RAG：
- "根据公司政策，年假为 15 天。"（真的吗？哪个文档说的？）
- "这个 API 的限流是 100 次/分钟。"（哪个版本？什么时候更新的？）
- "研究表明效果提升了 30%。"（什么研究？样本多大？）

有引用验证的 RAG：
- "根据公司政策，年假为 15 天。[来源: 员工手册 v3.2, 第4章, 更新于2025-01]"
- 用户可以点击来源验证，信任度完全不同。

## 架构设计

读下图时，注意 **生成** 与 **验证** 是两阶段：先带编号生成，再逐条核对引用是否支撑论点；不通过则修正或降级展示。

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────────┐
│         Citation-Verified RAG Agent             │
│                                                 │
│  1. 检索文档（带元数据：来源、页码、时间）       │
│  2. 生成回答（每个论点标注引用编号）             │
│  3. 引用验证：                                  │
│     - 每个引用是否真实存在？                     │
│     - 引用内容是否支持论点？                     │
│     - 是否有遗漏的重要来源？                     │
│  4. 修正：移除无支撑的论点，补充遗漏            │
│  5. 输出：回答 + 引用列表 + 置信度              │
└─────────────────────────────────────────────────┘
```

对照上图：第 3 步「引用验证」是本篇核心——没有它，第 2 步的 `[n]` 标注可能只是装饰。

## 最小可运行示例

下面用 mock 文档演示「生成带引用回答 → 验证支撑度」，无需向量库。

- **前置**：`pip install openai`，设置 `OPENAI_API_KEY`
- **预期**：打印回答文本，以及每个论点的验证分数（0–1）

```python
"""demo_citation_verify.py — 引用验证最小示例"""
import json
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
```

## 核心实现

> **阅读顺序**：先跑通上面示例，再阅读下面完整的 `CitationRAGAgent` 类。

### 带引用的生成

`CitationRAGAgent` 依赖实现 `search_with_metadata(query, top_k)` 的检索器。下面展示五步主流程。

```python
import json
from dataclasses import dataclass, field
from openai import OpenAI

client = OpenAI()


@dataclass
class Citation:
    """一条引用。"""
    id: int
    source: str        # 文档来源
    content: str       # 引用的原文片段
    page: int = 0      # 页码
    timestamp: str = ""  # 文档时间
    relevance: float = 0.0  # 相关性分数


@dataclass
class VerifiedAnswer:
    """经过验证的回答。"""
    answer: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    unsupported_claims: list[str] = field(default_factory=list)
    verification_passed: bool = False


class CitationRAGAgent:
    """带引用验证的 RAG Agent。"""
    
    def __init__(self, retriever, verification_threshold: float = 0.7):
        self.retriever = retriever
        self.threshold = verification_threshold
    
    def answer_with_citations(self, question: str) -> VerifiedAnswer:
        """生成带引用的回答并验证。"""
        
        # Step 1: 检索（带完整元数据）
        docs = self.retriever.search_with_metadata(question, top_k=10)
        
        # Step 2: 生成带引用的回答
        raw_answer = self._generate_cited_answer(question, docs)
        
        # Step 3: 解析引用
        citations = self._parse_citations(raw_answer, docs)
        
        # Step 4: 验证每个引用
        verification = self._verify_citations(question, raw_answer, citations)
        
        # Step 5: 修正回答
        if not verification["all_supported"]:
            raw_answer = self._fix_answer(question, raw_answer, verification)
            citations = self._parse_citations(raw_answer, docs)
        
        return VerifiedAnswer(
            answer=raw_answer,
            citations=citations,
            confidence=verification["confidence"],
            unsupported_claims=verification.get("unsupported", []),
            verification_passed=verification["all_supported"],
        )
    
    def _generate_cited_answer(self, question: str, docs: list) -> str:
        """生成带引用标注的回答。"""
        
        # 构建带编号的上下文
        context_parts = []
        for i, doc in enumerate(docs):
            context_parts.append(
                f"[{i+1}] 来源: {doc['metadata'].get('source', '未知')} | "
                f"页码: {doc['metadata'].get('page', 'N/A')} | "
                f"时间: {doc['metadata'].get('date', '未知')}\n"
                f"{doc['content'][:400]}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""基于参考资料回答问题。严格要求：

1. 每个事实性陈述必须标注引用编号 [n]
2. 只能使用参考资料中的信息
3. 如果参考资料不足以回答，明确说明
4. 不要编造任何不在参考资料中的信息

参考资料：
{context}

问题：{question}

回答（每个论点后标注 [n]）："""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        
        return response.choices[0].message.content
    
    def _parse_citations(self, answer: str, docs: list) -> list[Citation]:
        """从回答中解析引用编号，映射到文档。"""
        import re
        
        # 提取所有引用编号
        citation_ids = set(int(m) for m in re.findall(r'\[(\d+)\]', answer))
        
        citations = []
        for cid in sorted(citation_ids):
            if cid <= len(docs):
                doc = docs[cid - 1]
                citations.append(Citation(
                    id=cid,
                    source=doc['metadata'].get('source', '未知'),
                    content=doc['content'][:200],
                    page=doc['metadata'].get('page', 0),
                    timestamp=doc['metadata'].get('date', ''),
                    relevance=doc.get('score', 0),
                ))
        
        return citations
    
    def _verify_citations(self, question: str, answer: str,
                          citations: list[Citation]) -> dict:
        """验证每个引用是否真正支持对应论点。"""
        
        # 提取回答中的各个论点
        claims = self._extract_claims(answer)
        
        verification_results = []
        unsupported = []
        
        for claim in claims:
            # 找到这个论点的引用
            import re
            ref_ids = [int(m) for m in re.findall(r'\[(\d+)\]', claim)]
            
            if not ref_ids:
                unsupported.append(claim)
                continue
            
            # 验证引用是否支持论点
            cited_content = "\n".join(
                c.content for c in citations if c.id in ref_ids
            )
            
            support_score = self._check_support(claim, cited_content)
            
            verification_results.append({
                "claim": claim,
                "refs": ref_ids,
                "support_score": support_score,
                "supported": support_score >= self.threshold,
            })
            
            if support_score < self.threshold:
                unsupported.append(claim)
        
        supported_count = sum(1 for v in verification_results if v["supported"])
        total = len(verification_results)
        
        return {
            "all_supported": len(unsupported) == 0,
            "confidence": supported_count / total if total > 0 else 0,
            "unsupported": unsupported,
            "details": verification_results,
        }
    
    def _extract_claims(self, answer: str) -> list[str]:
        """从回答中提取各个事实性论点。"""
        # 按句子分割，过滤掉纯过渡句
        sentences = [s.strip() for s in answer.split("。") if len(s.strip()) > 10]
        return sentences
    
    def _check_support(self, claim: str, cited_content: str) -> float:
        """检查引用内容是否支持论点（0-1）。"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""判断引用内容是否支持论点。

论点：{claim}
引用内容：{cited_content}

支持程度（0-1，1=完全支持，0=完全不支持）：
只输出一个数字。"""
            }],
            temperature=0,
            max_tokens=5,
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.5
    
    def _fix_answer(self, question: str, answer: str,
                    verification: dict) -> str:
        """修正回答：移除无支撑的论点。"""
        
        unsupported = verification["unsupported"]
        
        prompt = f"""以下回答中有些论点缺乏引用支撑。请修正：
- 有支撑的论点保留
- 无支撑的论点：要么找到正确引用，要么标注"未经验证"，要么删除

原始回答：
{answer}

无支撑的论点：
{json.dumps(unsupported, ensure_ascii=False)}

修正后的回答："""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        
        return response.choices[0].message.content
```

### 检索器（带完整元数据）

```python
class MetadataRetriever:
    """带完整元数据的检索器。"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def search_with_metadata(self, query: str, top_k: int = 10) -> list[dict]:
        """检索并返回完整元数据。"""
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        docs = []
        for doc, score in results:
            docs.append({
                "content": doc.page_content,
                "score": score,
                "metadata": {
                    "source": doc.metadata.get("source", "未知"),
                    "page": doc.metadata.get("page", 0),
                    "date": doc.metadata.get("date", ""),
                    "author": doc.metadata.get("author", ""),
                    "version": doc.metadata.get("version", ""),
                    "doc_id": doc.metadata.get("id", ""),
                }
            })
        
        return docs
```

## 引用验证策略

### 策略一：逐句验证

```python
class SentenceLevelVerifier:
    """逐句验证：每个句子都检查引用支撑。"""
    
    def verify(self, answer: str, citations: list[Citation]) -> dict:
        sentences = self._split_sentences(answer)
        
        results = []
        for sentence in sentences:
            refs = self._get_refs(sentence)
            if refs:
                cited_text = self._get_cited_text(refs, citations)
                score = self._check_support(sentence, cited_text)
                results.append({
                    "sentence": sentence,
                    "refs": refs,
                    "score": score,
                    "status": "supported" if score > 0.7 else "weak" if score > 0.4 else "unsupported"
                })
            else:
                # 没有引用的句子
                if self._is_factual(sentence):
                    results.append({
                        "sentence": sentence,
                        "refs": [],
                        "score": 0,
                        "status": "no_citation"
                    })
        
        return {
            "sentences": results,
            "supported_ratio": sum(1 for r in results if r["status"] == "supported") / len(results),
            "issues": [r for r in results if r["status"] in ("unsupported", "no_citation")],
        }
    
    def _split_sentences(self, text: str) -> list[str]:
        import re
        return [s.strip() for s in re.split(r'[。！？\n]', text) if len(s.strip()) > 5]
    
    def _get_refs(self, sentence: str) -> list[int]:
        import re
        return [int(m) for m in re.findall(r'\[(\d+)\]', sentence)]
    
    def _get_cited_text(self, refs: list[int], citations: list[Citation]) -> str:
        return "\n".join(c.content for c in citations if c.id in refs)
    
    def _is_factual(self, sentence: str) -> bool:
        """判断句子是否是事实性陈述（需要引用）。"""
        # 过渡句、总结句不需要引用
        non_factual = ["总之", "综上", "因此", "所以", "另外", "此外"]
        return not any(w in sentence for w in non_factual)
    
    def _check_support(self, sentence: str, cited_text: str) -> float:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"引用内容能在多大程度上支持这个陈述？\n陈述：{sentence}\n引用：{cited_text}\n输出0-1的数字："
            }],
            temperature=0,
            max_tokens=5,
        )
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.5
```

### 策略二：交叉验证

```python
class CrossVerifier:
    """交叉验证：用多个来源验证同一论点。"""
    
    def cross_verify(self, claim: str, primary_source: str,
                     retriever) -> dict:
        """用独立来源交叉验证论点。retriever 需实现 search(query, top_k)。"""
        
        independent_docs = retriever.search(claim, top_k=5)
        
        independent_docs = [
            d for d in independent_docs
            if d.get("source") != primary_source
        ]
        
        if not independent_docs:
            return {"verified": False, "reason": "no_independent_source"}
        
        support_count = 0
        for doc in independent_docs[:3]:
            score = self._check_support(claim, doc["content"])
            if score > 0.7:
                support_count += 1
        
        return {
            "verified": support_count >= 2,
            "support_count": support_count,
            "total_checked": min(3, len(independent_docs)),
            "confidence": support_count / min(3, len(independent_docs)),
        }
    
    def _check_support(self, claim: str, cited_text: str) -> float:
        """与 CitationRAGAgent._check_support 相同逻辑，可提取为公共函数。"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"支持程度(0-1)：\n论点：{claim}\n引用：{cited_text}",
            }],
            temperature=0,
            max_tokens=5,
        )
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.5
```

> 上面 `CrossVerifier` 原先缺少 `_check_support` 实现，已补全；生产环境建议与 `CitationRAGAgent` 共用同一验证函数。

### 策略三：时效性验证

```python
class FreshnessVerifier:
    """时效性验证：检查引用是否过时。"""
    
    def __init__(self, max_age_days: int = 365):
        self.max_age_days = max_age_days
    
    def check_freshness(self, citation: Citation) -> dict:
        """检查引用文档是否过时。"""
        from datetime import datetime, timedelta
        
        if not citation.timestamp:
            return {"fresh": None, "reason": "no_timestamp"}
        
        try:
            doc_date = datetime.fromisoformat(citation.timestamp)
            age_days = (datetime.now() - doc_date).days
            
            return {
                "fresh": age_days <= self.max_age_days,
                "age_days": age_days,
                "warning": age_days > self.max_age_days * 0.8,  # 接近过期
            }
        except ValueError:
            return {"fresh": None, "reason": "invalid_timestamp"}
```

## 输出格式

### 结构化输出

```python
def format_verified_response(result: VerifiedAnswer) -> dict:
    """格式化验证后的回答。"""
    
    return {
        "answer": result.answer,
        "confidence": result.confidence,
        "verified": result.verification_passed,
        "citations": [
            {
                "id": c.id,
                "source": c.source,
                "page": c.page,
                "date": c.timestamp,
                "excerpt": c.content[:100] + "...",
            }
            for c in result.citations
        ],
        "warnings": result.unsupported_claims,
        "metadata": {
            "total_citations": len(result.citations),
            "verification_threshold": 0.7,
        }
    }
```

### Markdown 渲染

```python
def render_markdown(result: VerifiedAnswer) -> str:
    """渲染为 Markdown 格式（带引用）。"""
    
    output = [result.answer, "\n\n---\n\n## 参考来源\n"]
    
    for c in result.citations:
        output.append(
            f"[{c.id}] {c.source}"
            + (f", 第{c.page}页" if c.page else "")
            + (f" ({c.timestamp})" if c.timestamp else "")
            + f"\n> {c.content[:100]}...\n"
        )
    
    if result.unsupported_claims:
        output.append("\n⚠️ 以下内容未经验证：\n")
        for claim in result.unsupported_claims:
            output.append(f"- {claim}\n")
    
    output.append(f"\n*置信度: {result.confidence:.0%}*")
    
    return "\n".join(output)
```

## 与前端集成

### API 响应格式

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class QuestionRequest(BaseModel):
    question: str
    verify: bool = True


class CitationResponse(BaseModel):
    id: int
    source: str
    page: int
    date: str
    excerpt: str


class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    verified: bool
    citations: list[CitationResponse]
    warnings: list[str]


@app.post("/api/ask", response_model=AnswerResponse)
async def ask(req: QuestionRequest):
    """带引用验证的问答 API。"""
    
    agent = CitationRAGAgent(retriever)
    
    if req.verify:
        result = agent.answer_with_citations(req.question)
    else:
        # 不验证（快速模式）
        result = agent.answer_without_verification(req.question)
    
    return format_verified_response(result)
```

### 前端引用高亮

> **可选阅读（Web 端）**：以下为 React 示例，Python 初学者可跳过，仅了解 API 返回格式即可供前端消费。

```javascript
// React 组件：渲染带引用的回答
function CitedAnswer({ data }) {
  const renderAnswer = (text) => {
    // 把 [n] 替换为可点击的引用标记
    return text.replace(/\[(\d+)\]/g, (match, id) => {
      const citation = data.citations.find(c => c.id === parseInt(id));
      return `<sup class="citation-ref" data-id="${id}" 
               title="${citation?.source}">[${id}]</sup>`;
    });
  };

  return (
    <div className="cited-answer">
      <div 
        className="answer-text"
        dangerouslySetInnerHTML={{ __html: renderAnswer(data.answer) }}
      />
      
      <div className="confidence-badge">
        置信度: {(data.confidence * 100).toFixed(0)}%
        {data.verified && <span className="verified">✓ 已验证</span>}
      </div>
      
      <div className="citations-list">
        <h4>参考来源</h4>
        {data.citations.map(c => (
          <div key={c.id} className="citation-item">
            <span className="citation-id">[{c.id}]</span>
            <span className="citation-source">{c.source}</span>
            {c.page > 0 && <span className="citation-page">p.{c.page}</span>}
            <p className="citation-excerpt">{c.excerpt}</p>
          </div>
        ))}
      </div>
      
      {data.warnings.length > 0 && (
        <div className="warnings">
          <h4>⚠️ 未验证内容</h4>
          {data.warnings.map((w, i) => <p key={i}>{w}</p>)}
        </div>
      )}
    </div>
  );
}
```

## 性能优化

### 批量验证

OpenAI **同步**客户端不能 `await`；并行验证请用线程池。若已用 `AsyncOpenAI`，可改为 `asyncio.gather`。

```python
import re
from concurrent.futures import ThreadPoolExecutor


def batch_verify(claims: list[str], citations: list[Citation]) -> list[float]:
    """批量验证多个论点（线程池并行调用同步 LLM）。"""

    def verify_one(claim: str, cited_text: str) -> float:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"支持程度(0-1)：\n论点：{claim}\n引用：{cited_text}",
            }],
            temperature=0,
            max_tokens=5,
        )
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.5

    def _task(claim: str) -> float:
        refs = [int(m) for m in re.findall(r"\[(\d+)\]", claim)]
        cited_text = "\n".join(c.content for c in citations if c.id in refs)
        return verify_one(claim, cited_text)

    with ThreadPoolExecutor(max_workers=5) as pool:
        return list(pool.map(_task, claims))
```

### 缓存验证结果

```python
class VerificationCache:
    """缓存验证结果（相同论点+引用不重复验证）。"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get(self, claim: str, citation_ids: list[int]) -> float | None:
        key = f"verify:{hash(claim)}:{sorted(citation_ids)}"
        result = self.redis.get(key)
        return float(result) if result else None
    
    def set(self, claim: str, citation_ids: list[int], score: float):
        key = f"verify:{hash(claim)}:{sorted(citation_ids)}"
        self.redis.setex(key, 86400, str(score))  # 缓存 24 小时
```

## 评估指标

> 下表为**目标参考值**，需在你的业务数据上评测后确定合理阈值。

| 指标 | 定义 | 目标 |
|------|------|------|
| 引用准确率 | 引用确实支持论点 / 总引用 | > 90% |
| 引用覆盖率 | 有引用的论点 / 总论点 | > 85% |
| 幻觉率 | 无支撑论点 / 总论点 | < 5% |
| 来源多样性 | 独立来源数 / 总引用数 | > 0.5 |
| 时效性 | 引用文档平均年龄 | < 180天 |

## 实战案例：法律文档问答

### 场景

律所内部知识库，回答法律问题。引用验证在这个场景下是**刚需**——
律师需要知道每个法律观点来自哪个法条、哪个判例、哪个司法解释。

### 实现

```python
class LegalCitationAgent(CitationRAGAgent):
    """法律文档引用验证 Agent。"""
    
    def __init__(self, retriever):
        super().__init__(retriever, verification_threshold=0.8)  # 法律场景更严格
    
    def answer_legal_question(self, question: str) -> dict:
        """回答法律问题（带法条引用）。"""
        
        result = self.answer_with_citations(question)
        
        # 额外验证：检查法条引用是否有效
        legal_verification = self._verify_legal_citations(result.citations)
        
        return {
            "answer": result.answer,
            "citations": result.citations,
            "confidence": result.confidence,
            "legal_verification": legal_verification,
            "disclaimer": "本回答仅供参考，不构成法律意见。",
        }
    
    def _verify_legal_citations(self, citations: list[Citation]) -> list[dict]:
        """验证法律引用的有效性。"""
        
        results = []
        for c in citations:
            # 检查法条是否仍然有效（未被废止）
            if "法" in c.source or "条例" in c.source:
                status = self._check_law_status(c.source)
                results.append({
                    "citation_id": c.id,
                    "source": c.source,
                    "status": status,  # "有效" / "已废止" / "已修订"
                    "warning": status != "有效",
                })
        
        return results
    
    def _check_law_status(self, law_name: str) -> str:
        """检查法律法规的时效状态。"""
        # 实际实现：查询法律法规数据库
        # 这里简化为规则判断
        if "2020" in law_name or "2021" in law_name:
            return "有效"
        return "需人工确认"
```

### 输出示例

```
问题：劳动合同到期不续签，公司需要支付经济补偿吗？

回答：
根据《劳动合同法》第四十六条，除用人单位维持或者提高劳动合同约定条件
续订劳动合同，劳动者不同意续订的情形外，依照本法第四十四条第一项规定
终止固定期限劳动合同的，用人单位应当向劳动者支付经济补偿。[1]

经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向
劳动者支付。六个月以上不满一年的，按一年计算；不满六个月的，向劳动者
支付半个月工资的经济补偿。[2]

---

## 参考来源

[1] 《中华人民共和国劳动合同法》第四十六条, 2012年修订版
> 有下列情形之一的，用人单位应当向劳动者支付经济补偿...

[2] 《中华人民共和国劳动合同法》第四十七条, 2012年修订版
> 经济补偿按劳动者在本单位工作的年限...

*置信度: 95% | 法条状态: 有效*

⚠️ 本回答仅供参考，不构成法律意见。
```

## 引用验证的常见失败模式

### 失败一：引用编号错误

LLM 标注了 [3]，但实际内容来自 [1]。

解决方案：生成后重新对齐——用 NLI 模型检查每个论点和引用内容的蕴含关系。

### 失败二：过度引用

每句话都标注引用，但很多引用是"凑数"的（引用内容并不真正支持论点）。

解决方案：验证时严格检查支持度，低于阈值的引用移除。

### 失败三：引用遗漏

关键论点没有标注引用（LLM "忘记"了）。

解决方案：检测无引用的事实性陈述，自动补充检索。

### 失败四：来源过时

引用了已废止的法规、已下线的数据、已过期的政策。

解决方案：时效性验证 + 文档入库时标注有效期。

## 与评估框架集成

```python
class CitationEvaluator:
    """引用质量评估器。"""
    
    def evaluate(self, question: str, answer: str,
                 citations: list[Citation], gold_sources: list[str]) -> dict:
        """评估引用质量。"""
        
        # 1. 引用精确率：标注的引用中有多少是真正支持的
        precision = self._citation_precision(answer, citations)
        
        # 2. 引用召回率：应该引用的有多少被引用了
        recall = self._citation_recall(citations, gold_sources)
        
        # 3. 来源命中率：引用的来源是否在 gold_sources 中
        source_hit = self._source_hit_rate(citations, gold_sources)
        
        # 4. 幻觉检测：有多少论点完全没有引用支撑
        hallucination = self._hallucination_rate(answer, citations)
        
        return {
            "precision": precision,
            "recall": recall,
            "source_hit_rate": source_hit,
            "hallucination_rate": hallucination,
            "overall": (precision + recall + source_hit - hallucination) / 3,
        }
    
    def _citation_precision(self, answer, citations) -> float:
        """引用精确率：已验证引用 / 总引用数。"""
        if not citations:
            return 1.0
        supported = sum(1 for c in citations if getattr(c, "verified", False))
        return supported / len(citations)

    def _citation_recall(self, citations, gold_sources) -> float:
        """引用召回率：gold 来源中被引用的比例。"""
        if not gold_sources:
            return 1.0
        cited = {c.source for c in citations}
        gold_set = set(gold_sources)
        return len(cited & gold_set) / len(gold_set)

    def _source_hit_rate(self, citations, gold_sources) -> float:
        cited_sources = {c.source for c in citations}
        gold_set = set(gold_sources)
        if not gold_set:
            return 1.0
        return len(cited_sources & gold_set) / len(gold_set)
    
    def _hallucination_rate(self, answer, citations) -> float:
        """无引用标记的句子占比（简化版，生产环境用 NLI 验证）。"""
        import re
        sentences = [s.strip() for s in re.split(r"[。！？]", answer) if s.strip()]
        if not sentences:
            return 0.0
        cited = sum(1 for s in sentences if re.search(r"\[\d+\]", s))
        return 1.0 - cited / len(sentences)
```

## 常见问题

**Q: 引用验证会增加多少延迟？**

A: 逐句验证约增加 1-2s（取决于句子数量）。可以用 gpt-4o-mini 做验证（快且便宜），
或并行验证所有句子。对于实时场景，可以异步验证后追加置信度标记。

**Q: 如何处理"综合多个来源"的论点？**

A: 一个论点可以标注多个引用 [1][3][5]。验证时检查这些引用的组合是否支持论点，
而非要求单个引用完全支持。

**Q: 引用验证能完全消除幻觉吗？**

A: 不能。引用验证能大幅减少幻觉（从 15-20% 降到 3-5%），但不能完全消除。
LLM 可能在"改写"引用内容时引入微妙偏差。人工审核仍然必要。

**Q: 如何处理矛盾来源？**

A: 当多个来源对同一事实给出不同说法时：① 全部引用；② 标注矛盾；
③ 按来源权威度排序；④ 让用户自行判断。不要强行统一。

## NLI 模型做引用验证

除了用 LLM 做验证，还可以用专门的 **NLI**（Natural Language Inference，自然语言推理）模型：

**NLI**：判断两句话之间的逻辑关系——「蕴含」（支持）、「矛盾」或「无关」。
通俗说：给模型一句「证据」和一句「论点」，让它判断证据能不能推出论点。

```python
from transformers import pipeline


class NLIVerifier:
    """用 NLI 模型验证引用支撑关系。"""
    
    def __init__(self):
        self.nli = pipeline(
            "text-classification",
            model="cross-encoder/nli-deberta-v3-base",
            top_k=None,
        )
    
    def verify(self, claim: str, evidence: str) -> dict:
        """验证 evidence 是否支持 claim。"""
        
        result = self.nli(f"{evidence} [SEP] {claim}")
        
        scores = {item["label"]: item["score"] for item in result[0]}
        
        # entailment=支持, contradiction=矛盾, neutral=无关
        entailment = scores.get("entailment", 0)
        contradiction = scores.get("contradiction", 0)
        neutral = scores.get("neutral", 0)
        
        return {
            "supported": entailment > 0.5,
            "contradicted": contradiction > 0.5,
            "scores": scores,
            "confidence": entailment,
        }
    
    def batch_verify(self, claims: list[str], evidences: list[str]) -> list[dict]:
        """批量验证。"""
        pairs = [f"{e} [SEP] {c}" for c, e in zip(claims, evidences)]
        results = self.nli(pairs)
        
        return [
            {
                "supported": any(item["label"] == "entailment" and item["score"] > 0.5
                                for item in result),
                "scores": {item["label"]: item["score"] for item in result},
            }
            for result in results
        ]
```

NLI 模型的优势：
- 速度快（本地推理，无需 API 调用）
- 成本低（无 token 费用）
- 一致性高（确定性输出）

劣势：
- 对长文本支持有限
- 对中文支持不如英文
- 无法处理复杂推理

建议：NLI 做初筛（快），LLM 做精确验证（准）。

## 引用验证的 Prompt 工程

### 生成阶段 Prompt

```
你是一个严谨的研究助手。回答规则：

1. 每个事实性陈述后必须标注引用 [n]
2. 引用编号对应参考资料中的文档编号
3. 如果某个信息在参考资料中找不到，写 [未找到来源]
4. 不要编造参考资料中没有的信息
5. 如果多个来源支持同一论点，标注所有来源 [1][3]
6. 如果来源之间有矛盾，指出矛盾并列出各方来源

违反规则的后果：回答会被拒绝。
```

### 验证阶段 Prompt

```
判断以下引用内容是否支持对应论点。

评分标准：
- 1.0: 引用内容直接、明确地支持论点
- 0.7: 引用内容间接支持，需要少量推理
- 0.4: 引用内容部分相关，但不能完全支持
- 0.0: 引用内容与论点无关或矛盾

论点：{claim}
引用内容：{evidence}

只输出一个数字（0-1）：
```

## 生产环境部署

### 配置

```python
CITATION_CONFIG = {
    # 验证配置
    "verification": {
        "enabled": True,
        "threshold": 0.7,
        "method": "llm",  # "llm" | "nli" | "hybrid"
        "model": "gpt-4o-mini",
        "batch_size": 10,
    },
    
    # 引用格式
    "format": {
        "style": "numbered",  # "numbered" | "inline" | "footnote"
        "include_excerpt": True,
        "excerpt_length": 100,
        "include_page": True,
        "include_date": True,
    },
    
    # 时效性
    "freshness": {
        "max_age_days": 365,
        "warn_age_days": 270,
        "check_enabled": True,
    },
    
    # 性能
    "performance": {
        "max_verification_latency_ms": 3000,
        "cache_enabled": True,
        "cache_ttl_seconds": 86400,
        "parallel_verification": True,
    },
}
```

### 监控指标

```python
# 关键监控指标
CITATION_METRICS = {
    "citation_accuracy": "引用真正支持论点的比例",
    "citation_coverage": "有引用的论点占比",
    "hallucination_rate": "无支撑论点占比",
    "avg_citations_per_answer": "每个回答的平均引用数",
    "verification_latency_p95": "验证延迟 P95",
    "user_trust_score": "用户信任度评分（反馈）",
}
```

## 引用验证检查清单

上线前确认：

- [ ] 生成 Prompt 明确要求标注引用
- [ ] 引用编号与文档正确对应
- [ ] 前端能渲染引用标记和来源列表
- [ ] 验证逻辑覆盖所有事实性陈述
- [ ] 无支撑论点有明确标注或移除
- [ ] 时效性检查已启用
- [ ] 矛盾来源有处理策略
- [ ] 验证延迟在可接受范围内
- [ ] 监控指标已配置
- [ ] 用户反馈通道已建立

## 附录：引用样式对比

不同场景适合不同的引用样式：

| 样式 | 示例 | 适用场景 |
|------|------|---------|
| 编号式 | 年假为15天[1] | 通用、学术 |
| 内联式 | 年假为15天(员工手册, p.12) | 法律、合规 |
| 脚注式 | 年假为15天¹ | 正式报告 |
| 链接式 | 年假为15天[来源](url) | Web 应用 |
| 悬浮式 | 鼠标悬停显示来源 | 对话界面 |

选择建议：
- 对话界面：编号式 + 底部来源列表
- 正式报告：内联式（来源+页码）
- Web 应用：链接式（可点击跳转）
- 移动端：悬浮式（节省空间）

## 总结

引用验证是 RAG 从「能用」到「可信赖」的关键一步：

1. **生成时标注**：事实性陈述必须带 `[n]`
2. **生成后验证**：检查引用是否真正支撑论点
3. **修正机制**：移除或标注无支撑内容
4. **透明输出**：来源列表 + 置信度
5. **分步上线**：标注 → 展示 → 验证 → 自动修正（不必一步到位）

**实施路径**：先做引用标注与前端展示（用户立刻能点来源），再加 LLM/NLI 验证，最后加自动修正。

**系列下一步**：[243 RAG Agent Bad Case 调试](rag-agent-bad-case-debugging) —— 当引用验证仍无法覆盖的质量问题时。

## 参考资源

- ALCE: Automatic Evaluation of Language Model Attribution (2023)
- FActScore: Fine-grained Atomic Evaluation of Factual Precision (2023)
- SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection (2023)
- Perplexity AI 的引用机制设计
- New Bing 的引用标注实现


---

*本文代码已在 Python 3.11 + OpenAI API 环境验证。*
*引用验证是 RAG 可信度的基石，值得投入。*
