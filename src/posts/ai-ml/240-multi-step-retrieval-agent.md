---
title: "多步检索 Agent：逐步深入的知识获取"
slug: multi-step-retrieval-agent
date: 2025-05-20
tags: [AI, RAG, Agent, 多步检索, LLM]
category: ai-ml
description: "实现多步检索 Agent：根据前一步结果动态决定下一步检索什么，逐步深入直到获取完整信息。"
---

## 学习目标

读完本篇，你能：

1. 说清楚「多步检索」与「查询规划」（239 篇）各自解决什么问题
2. 实现一个带步数上限、防重复查询的多步检索主循环
3. 用 LLM 在每步决定「继续查还是可以回答」
4. 跑通 §最小可运行示例，在 mock 检索器上完成 2–3 步检索

## 前置阅读

- **239 查询规划 RAG Agent**：理解检索前分解子查询；本篇改为**边查边决定**下一步
- **Agent 循环**（系列 226 篇）：Observe → Think → Act 的基本模式
- OpenAI API 基础

## 环境要求

```bash
pip install openai
# LangGraph 集成章节可选：pip install langgraph
```

- Python 3.10+
- `OPENAI_API_KEY`

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 根据上一步结果动态生成下一步查询 | 检索前一次性拆好子查询 → **239** |
| 防循环（步数上限、查询去重） | 工具调用算数/查库 → **241** |
| 链式追踪、分治、假设验证等策略 | 引用验证 → **242** |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §单步检索的局限 | 能举例说明何时需要多步 |
| 2 | §最小可运行示例 | 跑通 mock 多步循环 |
| 3 | §Agent 主循环 | 理解 `AgentState` 与 `_decide_next_step` |
| 4 | §防止无限循环 | 配置 `StepGuard` |
| 5 | §实战案例 | 理解技术调研场景的步骤设计 |

> **可运行代码**：[`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/) — `python main.py 240`

## 单步检索的局限

**多步检索**（Multi-Step Retrieval）：不一次性查完，而是「查一批 → 分析缺口 → 再查下一批」，直到信息足够或达到步数上限。
通俗说：像侦探办案，先找线索 A，再根据 A 发现去搜 B，而不是只搜一次就下结论。

用户问："我们项目的数据库为什么选了 PostgreSQL 而不是 MySQL？"

单步检索只能找到直接提到"PostgreSQL MySQL 对比"的文档。但真正的答案可能分散在：
- 架构评审会议纪要（提到了选型讨论）
- 技术调研报告（对比了多种数据库）
- 性能测试报告（PostgreSQL 的 JSON 性能优势）
- CTO 的决策邮件（最终拍板原因）

**多步检索 Agent** 的思路：先检索到架构评审纪要 → 发现提到了"JSON 性能" → 再检索性能测试报告 → 发现引用了 CTO 邮件 → 再检索邮件。

## 核心架构

读下图时，注意**反馈回路**：每一步的「发现」会决定下一步查什么；这是与 239「事先规划好所有子查询」的本质区别。

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────────┐
│            Multi-Step Retrieval Agent            │
│                                                 │
│  Step 1: 初始检索 → 获取第一批文档               │
│      │                                          │
│      ▼                                          │
│  Step 2: 分析文档 → 发现信息缺口/线索           │
│      │                                          │
│      ▼                                          │
│  Step 3: 根据线索生成新查询 → 再次检索          │
│      │                                          │
│      ▼                                          │
│  Step N: 重复直到信息充分或达到步数上限          │
│                                                 │
│  Final: 综合所有步骤的文档 → 生成回答           │
└─────────────────────────────────────────────────┘
```

对照上图：Step 1 用原问题检索；Step 2 起由 LLM 根据「还缺什么」生成新查询；Final 综合**所有步骤**的文档生成回答（不能只用最后一步）。

## 最小可运行示例

下面用 mock 检索器演示 2 步检索，无需向量数据库。

- **前置**：`pip install openai`，设置 `OPENAI_API_KEY`
- **预期**：打印每步查询、发现摘要、最终回答

```python
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

    # Step 1：原问题
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
```

## 核心实现

> **阅读顺序**：先跑通上面示例，再阅读下面完整 `MultiStepRetrievalAgent` 类。

### Agent 主循环

`MultiStepRetrievalAgent` 依赖一个实现 `search(query, top_k)` 的检索器。下面代码展示状态如何在多步之间**累积**（`accumulated_knowledge`）。

```python
import json
from dataclasses import dataclass, field
from openai import OpenAI

client = OpenAI()


@dataclass
class RetrievalStep:
    """一步检索的记录。"""
    step_number: int
    query: str
    reasoning: str  # 为什么做这次检索
    documents: list = field(default_factory=list)
    findings: str = ""  # 从这一步发现了什么


@dataclass
class AgentState:
    """Agent 的完整状态。"""
    question: str
    steps: list[RetrievalStep] = field(default_factory=list)
    accumulated_knowledge: str = ""
    is_complete: bool = False
    final_answer: str = ""


class MultiStepRetrievalAgent:
    """多步检索 Agent。"""
    
    def __init__(self, retriever, max_steps: int = 5):
        self.retriever = retriever
        self.max_steps = max_steps
    
    def run(self, question: str) -> AgentState:
        """执行多步检索。"""
        state = AgentState(question=question)
        
        # 第一步：基于原始问题检索
        first_query = question
        first_step = self._execute_step(state, first_query, "初始检索：直接用用户问题")
        state.steps.append(first_step)
        
        # 后续步骤：根据前一步的发现决定下一步
        for i in range(1, self.max_steps):
            # 分析当前状态，决定下一步
            decision = self._decide_next_step(state)
            
            if decision["is_complete"]:
                state.is_complete = True
                break
            
            # 执行下一步检索
            step = self._execute_step(
                state,
                decision["next_query"],
                decision["reasoning"]
            )
            state.steps.append(step)
        
        # 生成最终回答
        state.final_answer = self._generate_final_answer(state)
        return state
    
    def _execute_step(self, state: AgentState, query: str,
                      reasoning: str) -> RetrievalStep:
        """执行一步检索。"""
        step = RetrievalStep(
            step_number=len(state.steps) + 1,
            query=query,
            reasoning=reasoning,
        )
        
        # 检索
        results = self.retriever.search(query, top_k=5)
        step.documents = results
        
        # 提取发现
        step.findings = self._extract_findings(state.question, results)
        
        # 更新累积知识
        state.accumulated_knowledge += f"\n[Step {step.step_number}] {step.findings}"
        
        return step
    
    def _decide_next_step(self, state: AgentState) -> dict:
        """LLM 决定下一步做什么。"""
        
        steps_summary = "\n".join(
            f"Step {s.step_number}: 查询=\"{s.query}\" → 发现: {s.findings[:200]}"
            for s in state.steps
        )
        
        prompt = f"""你是多步检索 Agent。根据已有检索结果，决定下一步行动。

用户问题：{state.question}

已完成的检索步骤：
{steps_summary}

累积知识：
{state.accumulated_knowledge[:2000]}

判断：
1. 信息是否已经充分回答问题？
2. 如果不充分，缺少什么信息？下一步应该检索什么？

输出 JSON：
{{
  "is_complete": true/false,
  "confidence": 0.0-1.0,
  "missing_info": "缺少的信息（如果未完成）",
  "next_query": "下一步检索查询（如果未完成）",
  "reasoning": "为什么做这个决定"
}}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _extract_findings(self, question: str, documents: list) -> str:
        """从检索结果中提取与问题相关的发现。"""
        
        docs_text = "\n---\n".join(
            doc.get("content", "")[:300] for doc in documents[:5]
        )
        
        prompt = f"""从以下文档中提取与问题相关的关键信息。

问题：{question}
文档：
{docs_text}

输出：
1. 直接相关的信息点（bullet points）
2. 新发现的线索（可以进一步检索的方向）
3. 仍然缺少的信息"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500,
        )
        
        return response.choices[0].message.content
    
    def _generate_final_answer(self, state: AgentState) -> str:
        """综合所有步骤的结果生成最终回答。"""
        
        all_docs = []
        for step in state.steps:
            all_docs.extend(step.documents)
        
        context = "\n---\n".join(
            f"[来源: {doc.get('source', '未知')}]\n{doc.get('content', '')[:400]}"
            for doc in all_docs[:15]
        )
        
        prompt = f"""基于多步检索获取的所有信息，回答用户问题。

问题：{state.question}

检索过程（{len(state.steps)} 步）：
{state.accumulated_knowledge}

所有参考文档：
{context}

要求：
1. 综合所有步骤的信息给出完整回答
2. 标注信息来源
3. 如果某些方面信息不足，明确说明"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        
        return response.choices[0].message.content
```

### 检索器接口

```python
from abc import ABC, abstractmethod


class BaseRetriever(ABC):
    """检索器抽象接口。"""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """检索文档。返回 [{content, source, metadata}]"""
        pass


class VectorRetriever(BaseRetriever):
    """向量检索器。"""
    
    def __init__(self, collection, embedding_model):
        self.collection = collection
        self.embedding_model = embedding_model
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = self.embedding_model.encode(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "content": doc,
                "source": meta.get("source", ""),
                "metadata": meta,
                "score": 1 - dist,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]


class HybridRetriever(BaseRetriever):
    """混合检索器（向量 + BM25）。"""
    
    def __init__(self, vector_retriever, bm25_retriever, alpha: float = 0.7):
        self.vector = vector_retriever
        self.bm25 = bm25_retriever
        self.alpha = alpha
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        vec_results = self.vector.search(query, top_k * 2)
        bm25_results = self.bm25.search(query, top_k * 2)
        
        # 加权融合
        scores = {}
        docs = {}
        
        for i, r in enumerate(vec_results):
            doc_id = r["content"][:50]
            scores[doc_id] = self.alpha * (1 - i / len(vec_results))
            docs[doc_id] = r
        
        for i, r in enumerate(bm25_results):
            doc_id = r["content"][:50]
            scores[doc_id] = scores.get(doc_id, 0) + (1 - self.alpha) * (1 - i / len(bm25_results))
            if doc_id not in docs:
                docs[doc_id] = r
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [docs[d] for d in sorted_ids[:top_k]]
```

## 多步检索策略

### 策略一：链式追踪

根据文档中的引用/链接追踪到下一个文档。

```python
class ChainRetrieval:
    """链式追踪检索：沿着文档引用链深入。"""
    
    def retrieve_chain(self, start_query: str, max_hops: int = 3) -> list:
        """从起始查询开始，沿引用链追踪。"""
        
        all_docs = []
        current_query = start_query
        
        for hop in range(max_hops):
            # 检索当前查询
            results = self.retriever.search(current_query, top_k=3)
            all_docs.extend(results)
            
            # 从结果中提取引用/链接
            references = self._extract_references(results)
            
            if not references:
                break  # 没有更多引用，停止
            
            # 选择最相关的引用作为下一步查询
            current_query = references[0]
        
        return all_docs
    
    def _extract_references(self, documents: list) -> list[str]:
        """从文档中提取引用和链接。"""
        references = []
        for doc in documents:
            content = doc.get("content", "")
            # 提取 "参见XXX"、"详见XXX"、"引用[1]" 等模式
            import re
            refs = re.findall(r'(?:参见|详见|参考|引用)\s*[：:]?\s*(.+?)(?:[。\n]|$)', content)
            references.extend(refs)
        return references
```

### 策略二：分治聚合

把复杂问题拆成子问题，分别检索后聚合。

```python
class DivideAndConquer:
    """分治聚合：拆分→分别检索→聚合。"""
    
    def retrieve(self, question: str) -> list:
        # 分解子问题
        sub_questions = self._decompose(question)
        
        # 分别检索
        all_results = {}
        for sq in sub_questions:
            results = self.retriever.search(sq, top_k=3)
            all_results[sq] = results
        
        # 聚合：找出跨子问题的共同文档（高价值）
        doc_count = {}
        for sq_results in all_results.values():
            for doc in sq_results:
                doc_id = doc["content"][:50]
                doc_count[doc_id] = doc_count.get(doc_id, 0) + 1
        
        # 按被命中次数排序
        sorted_docs = sorted(doc_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_docs
    
    def _decompose(self, question: str) -> list[str]:
        """LLM 分解子问题。"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"把问题拆成 2-4 个子问题：\n{question}\n输出 JSON 数组。"
            }],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content).get("sub_questions", [])
```

### 策略三：假设验证

先提出假设，再检索验证/推翻。

```python
class HypothesisDriven:
    """假设驱动检索：提出假设→检索验证→修正。"""
    
    def retrieve(self, question: str, max_rounds: int = 3) -> dict:
        # 生成初始假设
        hypotheses = self._generate_hypotheses(question)
        
        evidence = {h: [] for h in hypotheses}
        
        for round_num in range(max_rounds):
            for hypothesis in hypotheses:
                # 检索支持/反对证据
                query = f"{hypothesis} 证据 数据"
                results = self.retriever.search(query, top_k=3)
                evidence[hypothesis].extend(results)
            
            # 评估假设
            evaluation = self._evaluate_hypotheses(question, hypotheses, evidence)
            
            if evaluation["converged"]:
                break
            
            # 修正假设
            hypotheses = evaluation["revised_hypotheses"]
        
        return {
            "best_hypothesis": evaluation["best"],
            "evidence": evidence,
            "confidence": evaluation["confidence"],
        }
    
    def _generate_hypotheses(self, question: str) -> list[str]:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"对以下问题提出 2-3 个可能的假设答案：\n{question}"
            }],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content).get("hypotheses", [])
    
    def _evaluate_hypotheses(self, question, hypotheses, evidence) -> dict:
        evidence_text = json.dumps(
            {h: [e.get("content", "")[:100] for e in evs[:3]] for h, evs in evidence.items()},
            ensure_ascii=False
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"问题：{question}\n假设和证据：{evidence_text}\n\n哪个假设最被支持？是否收敛？"
            }],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
```

## 防止无限循环

```python
class StepGuard:
    """防止多步检索陷入循环。"""
    
    def __init__(self, max_steps: int = 5, similarity_threshold: float = 0.85):
        self.max_steps = max_steps
        self.similarity_threshold = similarity_threshold
        self.query_history: list[str] = []
    
    def should_stop(self, new_query: str, step_num: int) -> tuple[bool, str]:
        """判断是否应该停止。"""
        
        # 检查步数上限
        if step_num >= self.max_steps:
            return True, f"达到最大步数 {self.max_steps}"
        
        # 检查查询重复
        for prev_query in self.query_history:
            similarity = self._query_similarity(new_query, prev_query)
            if similarity > self.similarity_threshold:
                return True, f"查询与 Step 的 \"{prev_query[:30]}\" 过于相似"
        
        self.query_history.append(new_query)
        return False, ""
    
    def _query_similarity(self, q1: str, q2: str) -> float:
        """查询相似度（Jaccard）：两词集合交集 / 并集，越接近 1 越像。"""
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        if not words1 or not words2:
            return 0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)
```

### 信息增量检测

当新检索几乎没有带来新句子时，应停止多步循环，避免「换了问法、内容照旧」的空转。

```python
import hashlib


class IncrementDetector:
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.knowledge_hashes: set = set()

    def has_increment(self, new_findings: str) -> bool:
        sentences = [s.strip() for s in new_findings.split("。") if s.strip()]
        new_count = 0
        for sentence in sentences:
            h = hashlib.md5(sentence.encode()).hexdigest()
            if h not in self.knowledge_hashes:
                self.knowledge_hashes.add(h)
                new_count += 1
        if not sentences:
            return False
        return new_count / len(sentences) > self.threshold
```

### 监控与告警

```python
import logging


class RetrievalMonitor:
    def __init__(self, alert_steps=4, alert_latency_ms=10000):
        self.alert_steps = alert_steps
        self.alert_latency = alert_latency_ms
        self.history = []

    def record(self, steps, latency_ms, loop_detected=False):
        self.history.append({"steps": steps, "latency": latency_ms, "loop": loop_detected})
        if steps >= self.alert_steps:
            logging.warning(f"检索步数过多: {steps}")
        if latency_ms > self.alert_latency:
            logging.warning(f"检索延迟过高: {latency_ms}ms")
        if loop_detected:
            logging.warning("检测到检索循环")

    def get_stats(self):
        if not self.history:
            return {}
        return {
            "avg_steps": sum(h["steps"] for h in self.history) / len(self.history),
            "avg_latency": sum(h["latency"] for h in self.history) / len(self.history),
            "loop_rate": sum(1 for h in self.history if h["loop"]) / len(self.history),
        }
```

## 与 LangGraph 集成

**TypedDict**：用字典类型标注状态字段名与类型；**Annotated[list, operator.add]**：LangGraph 合并状态时把新列表**追加**到旧列表，而不是覆盖。

以下 `extract_findings` / `decide_next_step` / `generate_final_answer` 实现见 §核心实现与 §最小可运行示例，此处为图编排骨架。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator


def extract_findings(question: str, docs: list) -> str:
    """占位：生产环境替换为 §核心实现 中的 LLM 提取逻辑。"""
    return "\n".join(str(d) for d in docs[:3])


def decide_next_step(question: str, knowledge: str, steps: list) -> dict:
    """占位：生产环境替换为 §Agent 主循环 的 _decide_next_step。"""
    return {"is_complete": len(steps) >= 2, "next_query": question}


def generate_final_answer(question: str, knowledge: str, steps: list) -> str:
    """占位：生产环境替换为真实生成调用。"""
    return f"基于 {len(steps)} 步检索的回答（mock）"


class RetrievalState(TypedDict):
    question: str
    steps: Annotated[list, operator.add]
    knowledge: str
    is_complete: bool
    answer: str


def create_retrieval_graph(retriever, max_steps: int = 5):
    """用 LangGraph 构建多步检索图。"""
    
    def initial_retrieval(state: RetrievalState) -> dict:
        """初始检索节点。"""
        results = retriever.search(state["question"], top_k=5)
        findings = extract_findings(state["question"], results)
        return {
            "steps": [{"query": state["question"], "findings": findings, "docs": results}],
            "knowledge": findings,
        }
    
    def decide_next(state: RetrievalState) -> dict:
        """决策节点：继续还是停止。"""
        decision = decide_next_step(state["question"], state["knowledge"], state["steps"])
        return {"is_complete": decision["is_complete"]}
    
    def follow_up_retrieval(state: RetrievalState) -> dict:
        """跟进检索节点。"""
        decision = decide_next_step(state["question"], state["knowledge"], state["steps"])
        results = retriever.search(decision["next_query"], top_k=5)
        findings = extract_findings(state["question"], results)
        return {
            "steps": [{"query": decision["next_query"], "findings": findings, "docs": results}],
            "knowledge": state["knowledge"] + "\n" + findings,
        }
    
    def generate_answer(state: RetrievalState) -> dict:
        """生成最终回答。"""
        answer = generate_final_answer(state["question"], state["knowledge"], state["steps"])
        return {"answer": answer}
    
    def should_continue(state: RetrievalState) -> str:
        """路由：继续检索还是生成回答。"""
        if state["is_complete"] or len(state["steps"]) >= max_steps:
            return "answer"
        return "retrieve"
    
    # 构建图
    graph = StateGraph(RetrievalState)
    
    graph.add_node("initial", initial_retrieval)
    graph.add_node("decide", decide_next)
    graph.add_node("retrieve", follow_up_retrieval)
    graph.add_node("answer", generate_answer)
    
    graph.set_entry_point("initial")
    graph.add_edge("initial", "decide")
    graph.add_conditional_edges("decide", should_continue, {
        "retrieve": "retrieve",
        "answer": "answer",
    })
    graph.add_edge("retrieve", "decide")
    graph.add_edge("answer", END)
    
    return graph.compile()
```

## 性能优化

### 并行预取

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ParallelPrefetch:
    """在分析当前结果时，预取可能需要的下一步文档。"""
    
    def __init__(self, retriever):
        self.retriever = retriever
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def prefetch(self, current_results: list, question: str) -> dict:
        """基于当前结果预测下一步查询并预取。"""
        
        # 快速提取可能的后续查询（不用 LLM，用规则）
        possible_queries = self._extract_lead_queries(current_results, question)
        
        # 并行预取
        futures = {
            q: self.executor.submit(self.retriever.search, q, 3)
            for q in possible_queries[:3]
        }
        
        prefetched = {}
        for q, future in futures.items():
            try:
                prefetched[q] = future.result(timeout=5)
            except Exception:
                pass
        
        return prefetched
    
    def _extract_lead_queries(self, results: list, question: str) -> list[str]:
        """从结果中提取线索查询（规则方式，快速）。"""
        import re
        queries = []
        for doc in results:
            content = doc.get("content", "")
            # 提取专有名词作为可能的后续查询
            entities = re.findall(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)*', content)
            for entity in entities[:2]:
                queries.append(f"{entity} {question.split()[0]}")
        return queries[:5]
```

### 结果缓存

```python
from functools import lru_cache
import hashlib
import time


class RetrievalCache:
    """检索结果缓存，避免重复检索。"""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, query: str) -> list | None:
        key = hashlib.md5(query.encode()).hexdigest()
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["time"] < self.ttl:
                return entry["results"]
            del self.cache[key]
        return None
    
    def set(self, query: str, results: list):
        key = hashlib.md5(query.encode()).hexdigest()
        self.cache[key] = {"results": results, "time": time.time()}
```

## 评估与调试

### 检索链路可视化

```python
def visualize_retrieval_chain(state: AgentState) -> str:
    """可视化多步检索链路。"""
    
    output = [f"问题: {state.question}\n"]
    
    for step in state.steps:
        output.append(f"{'='*50}")
        output.append(f"Step {step.step_number}: {step.query}")
        output.append(f"原因: {step.reasoning}")
        output.append(f"发现: {step.findings[:200]}")
        output.append(f"文档数: {len(step.documents)}")
        output.append("")
    
    output.append(f"{'='*50}")
    output.append(f"最终回答:\n{state.final_answer[:500]}")
    
    return "\n".join(output)
```

### 质量评估

```python
def evaluate_multi_step(question: str, gold_answer: str,
                        agent: MultiStepRetrievalAgent) -> dict:
    """评估多步检索质量。"""
    
    state = agent.run(question)
    
    # 1. 步数效率
    step_efficiency = len(state.steps)
    
    # 2. 信息覆盖率
    coverage = assess_coverage(question, gold_answer, state.accumulated_knowledge)
    
    # 3. 回答质量
    answer_quality = assess_answer(question, state.final_answer, gold_answer)
    
    # 4. 检索精确率
    all_docs = [doc for step in state.steps for doc in step.documents]
    precision = assess_precision(question, all_docs)
    
    return {
        "steps": step_efficiency,
        "coverage": coverage,
        "answer_quality": answer_quality,
        "precision": precision,
        "overall": (coverage + answer_quality + precision) / 3,
    }
```

## 实战案例：技术调研 Agent

### 场景

用户问：“调研一下 2024 年主流的向量数据库，给出选型建议。”

这需要多步检索：
1. 先检索“向量数据库 2024 主流产品”→ 发现 Milvus, Pinecone, Weaviate, Qdrant
2. 再检索每个产品的性能对比 → 发现 benchmark 数据
3. 再检索“向量数据库 选型 经验”→ 发现社区评价
4. 再检索“向量数据库 生产环境 坑”→ 发现实际问题

### 实现

```python
class TechResearchAgent(MultiStepRetrievalAgent):
    """技术调研专用 Agent。"""
    
    def run_research(self, topic: str) -> dict:
        """执行技术调研。注意：全程复用同一个 AgentState，累积每步发现。"""
        
        state = AgentState(question=topic)
        
        # 第一步：概览检索
        overview_step = self._execute_step(
            state,
            f"{topic} 2024 主流产品 概览",
            "获取市场概览",
        )
        state.steps.append(overview_step)
        
        # 提取产品列表
        products = self._extract_products(overview_step.findings)
        
        # 第二步：每个产品深入检索（复用 state，知识会累积）
        product_details = {}
        for product in products[:5]:
            detail_step = self._execute_step(
                state,
                f"{product} 性能 特点 优势 劣势",
                f"深入了解 {product}",
            )
            state.steps.append(detail_step)
            product_details[product] = detail_step.findings
        
        # 第三步：社区评价
        community_step = self._execute_step(
            state,
            f"{topic} 选型经验 社区评价 对比",
            "获取社区反馈",
        )
        state.steps.append(community_step)
        
        # 第四步：生产环境问题
        issues_step = self._execute_step(
            state,
            f"{topic} 生产环境 问题 坑 注意事项",
            "了解实际使用中的问题",
        )
        state.steps.append(issues_step)
        
        # 综合生成报告
        report = self._generate_report(topic, overview_step, product_details,
                                       community_step, issues_step)
        return {"report": report, "steps": len(state.steps)}
    
    def _extract_products(self, findings: str) -> list[str]:
        """从概览中提取产品列表。"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"从以下文本中提取提到的产品/工具名称：\n{findings}\n输出 JSON 数组。"
            }],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content).get("products", [])
    
    def _generate_report(self, topic, overview, details, community, issues) -> str:
        """生成调研报告。"""
        prompt = f"""基于以下调研结果，生成一份技术选型报告。

主题：{topic}

市场概览：{overview.findings}

产品详情：{json.dumps(details, ensure_ascii=False)[:2000]}

社区评价：{community.findings}

生产问题：{issues.findings}

报告结构：
1. 执行摘要
2. 产品对比表
3. 各产品优劣势
4. 选型建议
5. 风险提示"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content
```

## 多步检索 vs 其他方案

| 方案 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| 单步检索 | 简单事实查询 | 快、简单 | 无法处理复杂问题 |
| 查询规划 | 多维度问题 | 并行、全面 | 不能根据结果调整 |
| 多步检索 | 信息分散/隐含关联 | 动态调整、深入 | 慢、成本高 |
| 混合方案 | 生产环境 | 兼顾效率和质量 | 复杂度高 |

生产环境建议：先用查询分类路由，简单问题单步，复杂问题多步。

## 常见问题

**Q: 多步检索的延迟如何控制？**

A: 每步约 1-2s（LLM 决策 + 检索）。3 步约 4-6s。可以用并行预取减少等待，或设置严格超时。

**Q: 如何避免“检索死循环”？**

A: 三重保护：① 步数上限；② 查询相似度检测；③ 信息增量检测（如果新检索没有带来新信息，停止）。

**Q: 多步检索的成本如何？**

A: 每步约 1 次 LLM 调用（决策）+ 1 次检索。3 步约 3-4 次 LLM 调用。用 gpt-4o-mini 做决策可以大幅降低成本。

**Q: 多步检索和 Self-RAG 有什么区别？**

A: **Self-RAG** 在生成过程中按 token 决定要不要检索；多步检索在检索阶段做多轮迭代。两者可结合使用。

**Q: 如何处理多步检索中的矛盾信息？**

A: 标注矛盾点；按来源可信度排序；在最终回答中说明存在争议，而非强行统一。

**Q: 多步检索适合实时对话吗？**

A: 纯多步延迟较高（4–8s）。可先流式输出第一步，后台继续检索，再以「更新」形式追加。

**Q: 如何测试多步检索 Agent？**

A: 构建多跳问答测试集（如 **HotpotQA**——公开的多跳问答基准，问题需跨多篇 Wikipedia 文档才能回答），对比单步与多步的召回率、回答准确率。

**Q: 多步检索的步数如何确定？**

A: 简单多跳 2 步，复杂调研 3–5 步；建议上限 5 步。

## 参考资源

- Iter-RetGen: Enhancing Retrieval-Augmented LLMs with Iterative Retrieval-Generation Synergy (2023)
- Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection (2023)
- FLARE: Active Retrieval Augmented Generation (2023)
- LangGraph Multi-Step Retrieval Tutorial
- LlamaIndex Sub-Question Query Engine

## 多步检索的 Prompt 工程要点

### 决策 Prompt 的关键要素

好的决策 Prompt 需要包含：

1. **当前状态摘要**：已完成几步、每步查了什么、发现了什么
2. **累积知识**：目前掌握的所有信息
3. **明确的判断标准**：什么算"信息充分"
4. **输出约束**：JSON 格式、字段定义
5. **防循环提示**：明确告知不要重复已有查询

### 发现提取的关键要素

1. **聚焦问题**：只提取与原始问题相关的信息
2. **标注来源**：每条发现标注来自哪个文档
3. **线索识别**：识别"参见"、"引用"、"详见"等后续线索
4. **缺口识别**：明确指出还缺什么信息
5. **置信度**：对每条发现标注确信程度

### 最终回答的关键要素

1. **综合多步**：不要只用最后一步的结果
2. **标注来源**：每个论点标注来自哪一步的哪个文档
3. **承认不足**：信息不够的地方明确说明
4. **结构化**：用清晰的层次结构组织回答
5. **可追溯**：读者能沿着引用链验证每个论点

## 附录：完整配置示例

```python
# config.py - 多步检索 Agent 配置

MULTI_STEP_CONFIG = {
    # 步数控制
    "max_steps": 5,
    "min_steps": 1,
    
    # 检索配置
    "retrieval": {
        "top_k": 5,
        "score_threshold": 0.5,
        "hybrid_alpha": 0.7,  # 向量权重
    },
    
    # 防循环配置
    "guard": {
        "query_similarity_threshold": 0.85,
        "increment_threshold": 0.1,
        "max_same_topic_retries": 2,
    },
    
    # LLM 配置
    "llm": {
        "decision_model": "gpt-4o-mini",  # 决策用轻量模型
        "extraction_model": "gpt-4o-mini",  # 提取用轻量模型
        "generation_model": "gpt-4o",  # 最终回答用强模型
        "temperature": 0,
    },
    
    # 延迟控制
    "latency": {
        "total_budget_ms": 10000,
        "per_step_budget_ms": 3000,
        "retrieval_timeout_ms": 2000,
    },
    
    # 缓存配置
    "cache": {
        "enabled": True,
        "ttl_seconds": 3600,
        "max_size": 1000,
    },
    
    # 监控配置
    "monitoring": {
        "alert_steps": 4,
        "alert_latency_ms": 8000,
        "log_every_step": True,
    },
}
```

这个配置覆盖了多步检索 Agent 的所有关键参数。
根据实际场景调整 max_steps 和延迟预算即可。

## 总结

多步检索 Agent 让 RAG 从「一次搜索定生死」变成「逐步深入、动态调整」。

| 能力 | 单步检索 | 多步检索 |
|------|---------|---------|
| 信息分散 | 只能找到直接匹配的 | 沿线索追踪到所有相关文档 |
| 隐含关联 | 无法发现 | 通过中间文档桥接 |
| 深度信息 | 停在表面 | 逐步深入到细节 |
| 完整性 | 片面 | 多角度覆盖 |

核心要点：

1. **动态决策**：每步根据上一步结果决定下一步
2. **防循环**：步数上限 + 查询去重 + 增量检测
3. **策略选择**：链式追踪、分治聚合、假设验证各有适用场景
4. **成本控制**：简单问题走单步；决策用轻量模型；缓存热门查询
5. **可观测性**：记录每步查询、发现、延迟

**工程顺序**：先保证单步检索质量 → 再加多步 → 最后做自适应路由。单步做不好，多步只会放大问题。

**系列下一步**：[241 工具增强 RAG](tool-augmented-rag) —— 当问题需要精确计算、查库、调 API 时。

---

*本文代码已在 Python 3.11 + OpenAI API 环境验证。*
