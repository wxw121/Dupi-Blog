---
title: "查询规划 RAG Agent：让检索更精准"
slug: query-planning-rag-agent
date: 2025-05-18
tags: [AI, RAG, Agent, 查询规划, LLM]
category: ai-ml
description: "用 Agent 做查询规划：把模糊问题拆成精准子查询，多路检索后融合排序，让 RAG 召回质量翻倍。"
---

## 学习目标

读完本篇，你能：

1. 解释「查询规划」解决什么问题，并判断哪些问题需要规划、哪些可以直接检索
2. 用 LLM 把复杂问题分解为 2–5 个子查询，并改写为检索友好形式
3. 实现向量 + 关键词双路检索，并用 RRF 融合多路排序结果
4. 跑通 §最小可运行示例，在 mock 知识库上完成一次「分解 → 检索 → 回答」

## 前置阅读

- **Agentic RAG 架构**（系列 [238 篇](agentic-rag-architecture)）：理解 Agent 如何驱动检索，而非固定管道
- **向量检索基础**：知道 embedding 相似度检索是怎么回事
- **OpenAI API**：会配置 `OPENAI_API_KEY` 环境变量

## 环境要求

```bash
pip install openai
# 可选（集成章节用）：pip install langchain langchain-openai llama-index-core
```

- Python 3.10+
- 可用的 LLM API（文中默认 `gpt-4o`；开发调试可用 `gpt-4o-mini` 降低成本）

## 本文边界

| 本篇讲 | 本篇不讲（见系列其他篇） |
|--------|-------------------------|
| 查询分解、改写、多路检索、RRF 融合 | 根据上一步结果动态改查询 → **240 多步检索** |
| 充分性判断与迭代补充 | 调用计算器 / 数据库 → **241 工具增强 RAG** |
| 延迟预算与简单问题跳过 | 引用标注与验证 → **242 引用验证** |

> **与 240 的区别**：查询规划在检索**之前**一次性拆好子查询（可并行）；多步检索是**边查边决定**下一步查什么。复杂对比题用规划；答案分散在多篇文档、需沿线索追踪时用多步。

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §架构总览 | 能说出规划 Agent 的 6 个步骤 |
| 2 | §最小可运行示例 | 本地跑通 mock 版规划检索 |
| 3 | §核心实现 | 理解分解 / 改写 / 融合代码结构 |
| 4 | §常见失败模式 | 识别分解过细、改写过度、忽略时间 3 类问题 |
| 5 | §生产环境考量 | 知道何时跳过规划以控制延迟 |

> **系列导读**：[agent-rag-series-238-254](agent-rag-series-238-254) | **可运行代码**：[`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/) → `python main.py 239`

## 为什么需要查询规划

**查询规划**（Query Planning）：在真正检索之前，先分析用户问题，生成一条或多条更精准的检索查询。
通俗说：不是拿着用户的原话直接去搜，而是先想清楚「要搜什么、搜几次」。

用户问"公司去年的技术成果有哪些"，直接拿去检索：

- "公司"太泛——哪个公司？
- "去年"是相对时间——向量库里存的是绝对日期
- "技术成果"含义模糊——专利？论文？产品上线？

直接检索的召回质量很差。查询规划 Agent 的工作：**把模糊问题转化为多个精准的检索查询**。

## 架构总览

读下图时，重点看六步的**先后顺序**：先理解意图、再分解改写，然后并行检索，最后判断信息够不够。
对照下图：复杂问题走完整六步；简单事实题可在 §生产环境考量 里跳过前几步。

```
用户问题
    │
    ▼
┌───────────────────────────────────────────────┐
│           Query Planning Agent                 │
│                                               │
│  1. 意图理解：用户到底要什么？                  │
│  2. 查询分解：拆成多个子查询                    │
│  3. 查询改写：每个子查询优化为检索友好形式       │
│  4. 执行检索：并行多路检索                      │
│  5. 结果融合：去重、排序、裁剪                  │
│  6. 充分性判断：信息够不够？不够则补充检索       │
└───────────────────────────────────────────────┘
    │
    ▼
精准上下文 → LLM 生成回答
```

上图概括：查询规划是在「检索」和「生成」之间加了一层**智能路由**——让检索更准，而不是让 LLM 硬猜。

## 最小可运行示例

下面示例演示完整链路：**分解 → mock 检索 → 生成回答**。用关键词重叠模拟向量检索（教学用，生产请换真实向量库）。

- **前置**：已 `pip install openai`，并设置 `OPENAI_API_KEY`
- **预期**：终端打印 2–5 条子查询、检索到的文档片段、以及带来源编号的回答

```python
"""demo_query_planning.py — 查询规划最小示例（mock 检索）"""
import json
import os
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
```

运行：`python demo_query_planning.py`。若 API 不可用，至少可单独测试 `mock_search("2024年 专利", top_k=2)` 验证检索逻辑。

## 核心实现

> **阅读顺序**：建议先跑通 §最小可运行示例，再阅读下面分模块实现。后文 `decompose_query` 等函数在示例基础上扩展了字段与策略。

### 查询分解

下面函数演示如何用 LLM 把复杂问题拆成多条子查询。需要 OpenAI 兼容 API；`temperature=0` 保证分解结果稳定。

```python
import json
from openai import OpenAI

client = OpenAI()


def decompose_query(question: str, context: str = "") -> list[dict]:
    """把复杂问题分解为多个子查询。"""
    
    prompt = f"""你是查询规划专家。把用户问题分解为 2-5 个独立的检索子查询。

规则：
1. 每个子查询应该是独立可检索的
2. 子查询合起来应覆盖原始问题的所有方面
3. 避免子查询之间大量重叠
4. 把相对时间转为绝对时间（如"去年"→"2024年"）
5. 把代词转为具体实体

用户问题：{question}
{"对话上下文：" + context if context else ""}

输出 JSON：
{{
  "analysis": "问题分析（1句话）",
  "sub_queries": [
    {{
      "query": "检索用的查询文本",
      "intent": "这个子查询要找什么",
      "source_type": "建议的检索源类型（文档/代码/数据库/API）"
    }}
  ]
}}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    
    plan = json.loads(response.choices[0].message.content)
    return plan["sub_queries"]
```

### 查询改写

```python
def rewrite_for_retrieval(sub_query: dict, knowledge_base_info: str) -> dict:
    """把子查询改写为检索友好的形式。"""
    
    prompt = f"""把检索意图改写为最适合向量检索的查询。

原始意图：{sub_query['intent']}
原始查询：{sub_query['query']}
知识库信息：{knowledge_base_info}

改写策略：
1. 使用知识库中可能出现的术语（而非用户口语）
2. 添加同义词扩展
3. 如果是事实性问题，改为陈述句形式
4. 控制长度在 10-30 字

输出 JSON：
{{
  "rewritten_query": "改写后的查询",
  "keywords": ["关键词1", "关键词2"],
  "negative_keywords": ["排除词1"]
}}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    
    return json.loads(response.choices[0].message.content)
```

### 多路检索 + 融合

**BM25**：一种经典的关键词匹配排序算法，按词频和文档长度给文档打分。
通俗说：像搜索引擎那样按「关键词命中」找文档，弥补向量检索漏掉精确术语的问题。

**RRF**（Reciprocal Rank Fusion，倒数排名融合）：把多路检索的排序列表合并成一份总榜，同一文档在多个榜单里都靠前则最终排名更高。
通俗说：不直接比分数（向量分和 BM25 分不可比），而是比「各路人马里的名次」。

下面 `MultiPathRetriever` 并行走向量库、关键词库（可选图谱库），再用 RRF 合并。`vector_store` / `keyword_store` 需你按实际框架实现（LangChain、LlamaIndex 等）。

```python
import numpy as np
from concurrent.futures import ThreadPoolExecutor


class MultiPathRetriever:
    """多路检索 + RRF 融合。"""
    
    def __init__(self, vector_store, keyword_store, graph_store=None):
        self.vector_store = vector_store
        self.keyword_store = keyword_store
        self.graph_store = graph_store
    
    def retrieve(self, queries: list[dict], top_k: int = 10) -> list[dict]:
        """并行执行多路检索，RRF 融合排序。"""
        
        all_results = {}  # doc_id → {doc, scores: []}
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            for q in queries:
                # 向量检索
                futures.append(
                    executor.submit(self._vector_search, q["rewritten_query"], top_k * 2)
                )
                # 关键词检索
                futures.append(
                    executor.submit(self._keyword_search, q["keywords"], top_k * 2)
                )
                # 图谱检索（如果有）
                if self.graph_store and q.get("entities"):
                    futures.append(
                        executor.submit(self._graph_search, q["entities"], top_k)
                    )
            
            # 收集所有结果
            ranked_lists = []
            for future in futures:
                try:
                    results = future.result(timeout=10)
                    ranked_lists.append(results)
                except Exception:
                    continue
        
        # RRF 融合
        return self._rrf_fusion(ranked_lists, top_k)
    
    def _vector_search(self, query: str, top_k: int) -> list[dict]:
        """向量相似度检索。"""
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        return [{"doc": doc, "score": score} for doc, score in results]
    
    def _keyword_search(self, keywords: list[str], top_k: int) -> list[dict]:
        """BM25 关键词检索。"""
        query = " OR ".join(keywords)
        return self.keyword_store.search(query, top_k=top_k)
    
    def _graph_search(self, entities: list[str], top_k: int) -> list[dict]:
        """知识图谱检索。"""
        return self.graph_store.query(entities, max_hops=2, limit=top_k)
    
    def _rrf_fusion(self, ranked_lists: list[list[dict]], top_k: int,
                    k: int = 60) -> list[dict]:
        """Reciprocal Rank Fusion 融合多路排序。"""
        
        scores = {}  # doc_id → rrf_score
        docs = {}    # doc_id → doc_content
        
        for ranked_list in ranked_lists:
            for rank, item in enumerate(ranked_list):
                doc_id = item["doc"].metadata.get("id", hash(item["doc"].page_content))
                docs[doc_id] = item["doc"]
                
                rrf_score = 1.0 / (k + rank + 1)
                scores[doc_id] = scores.get(doc_id, 0) + rrf_score
        
        # 按 RRF 分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return [
            {"doc": docs[doc_id], "score": scores[doc_id]}
            for doc_id in sorted_ids[:top_k]
        ]
```

### 充分性判断 + 迭代补充

```python
def check_sufficiency(question: str, sub_queries: list[dict],
                      retrieved_docs: list[dict]) -> dict:
    """判断检索结果是否充分回答问题。"""
    
    docs_text = "\n---\n".join(
        f"[来源: {d['doc'].metadata.get('source', '未知')}]\n{d['doc'].page_content[:300]}"
        for d in retrieved_docs[:10]
    )
    
    prompt = f"""判断以下检索结果是否充分回答用户问题。

用户问题：{question}
子查询：{json.dumps([q['intent'] for q in sub_queries], ensure_ascii=False)}

检索结果摘要：
{docs_text}

输出 JSON：
{{
  "sufficient": true/false,
  "coverage": {{
    "子查询意图1": "covered/partial/missing",
    "子查询意图2": "covered/partial/missing"
  }},
  "missing_aspects": ["缺失的方面"],
  "follow_up_queries": ["补充查询1", "补充查询2"]
}}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    
    return json.loads(response.choices[0].message.content)
```

### 完整 Agent 循环

```python
class QueryPlanningAgent:
    """查询规划 RAG Agent。"""
    
    def __init__(self, retriever: MultiPathRetriever, max_iterations: int = 3):
        self.retriever = retriever
        self.max_iterations = max_iterations
    
    def answer(self, question: str, context: str = "") -> dict:
        """完整的查询规划 + 检索 + 回答流程。"""
        
        # Step 1: 查询分解
        sub_queries = decompose_query(question, context)
        
        # Step 2: 查询改写
        rewritten = [rewrite_for_retrieval(q, "技术文档知识库") for q in sub_queries]
        
        # Step 3: 迭代检索
        all_docs = []
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # 检索
            if iteration == 1:
                results = self.retriever.retrieve(rewritten)
            else:
                # 补充检索
                follow_up = [
                    {"rewritten_query": q, "keywords": q.split()}
                    for q in sufficiency["follow_up_queries"]
                ]
                results = self.retriever.retrieve(follow_up)
            
            all_docs.extend(results)
            
            # 去重
            seen = set()
            unique_docs = []
            for r in all_docs:
                doc_id = r["doc"].metadata.get("id", hash(r["doc"].page_content))
                if doc_id not in seen:
                    seen.add(doc_id)
                    unique_docs.append(r)
            all_docs = unique_docs
            
            # 充分性判断
            sufficiency = check_sufficiency(question, sub_queries, all_docs)
            
            if sufficiency["sufficient"]:
                break
            
            if not sufficiency.get("follow_up_queries"):
                break  # 没有补充查询可做，退出
        
        # Step 4: 生成回答
        context_docs = all_docs[:10]
        answer = self._generate_answer(question, context_docs)
        
        return {
            "answer": answer,
            "sources": [d["doc"].metadata for d in context_docs],
            "iterations": iteration,
            "sub_queries": sub_queries,
        }
    
    def _generate_answer(self, question: str, docs: list[dict]) -> str:
        """基于检索结果生成回答。"""
        
        context = "\n---\n".join(
            f"[{i+1}] {d['doc'].page_content[:500]}"
            for i, d in enumerate(docs)
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "基于提供的参考资料回答问题。引用来源编号。如果信息不足，明确说明。"},
                {"role": "user", "content": f"问题：{question}\n\n参考资料：\n{context}"}
            ],
            temperature=0,
        )
        
        return response.choices[0].message.content
```

## 查询规划策略

### 策略一：分面检索

适用于多维度问题："对比 A 和 B 在性能、价格、易用性方面的差异"

```python
# 分解为按维度的子查询
sub_queries = [
    {"query": "A 产品性能指标 benchmark", "intent": "A的性能数据"},
    {"query": "B 产品性能指标 benchmark", "intent": "B的性能数据"},
    {"query": "A B 产品价格对比", "intent": "价格信息"},
    {"query": "A B 用户使用体验 易用性", "intent": "易用性评价"},
]
```

### 策略二：时间线检索

适用于时间相关问题："项目从立项到上线经历了哪些阶段"

```python
sub_queries = [
    {"query": "项目立项 需求分析 2024Q1", "intent": "立项阶段"},
    {"query": "项目设计 架构评审 2024Q2", "intent": "设计阶段"},
    {"query": "项目开发 迭代 2024Q3", "intent": "开发阶段"},
    {"query": "项目测试 上线部署 2024Q4", "intent": "上线阶段"},
]
```

### 策略三：层次检索

适用于从概览到细节的问题："解释微服务架构的设计原则和具体实践"

```python
# 先检索概览，再根据概览内容检索细节
# 第一轮：概览
overview_query = "微服务架构 设计原则 最佳实践 概述"
# 第二轮：根据概览中提到的具体实践深入
detail_queries = ["服务拆分策略 具体案例", "微服务通信 gRPC REST 选型"]
```

## 查询改写技巧

### HyDE（假设文档嵌入）

**HyDE**（Hypothetical Document Embeddings）：先让 LLM 写一段「假答案」，再用这段假答案去做向量检索。
通俗说：用户问的是问题，文档写的是陈述句——用「像文档的文本」去搜，往往比用问题去搜更准。

下面函数生成假设性段落，返回值应送入 embedding 模型而非直接给用户。

```python
def hyde_rewrite(question: str) -> str:
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "写一段简短的文字来回答以下问题。不需要完全正确，只需要形式像真实文档。"},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=200,
    )
    
    return response.choices[0].message.content
```

### Step-back Prompting

**Step-back Prompting**（退后一步提问）：先把具体问题抽象成更宽泛的背景问题去检索，再回答细节。
通俗说：问「这台电脑卡」之前，先查「电脑变慢的常见原因」打底。

```python
def step_back_rewrite(question: str) -> str:
    """生成更高层次的问题，检索背景知识。"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "把具体问题抽象为更高层次的问题，用于检索背景知识。"},
            {"role": "user", "content": f"原始问题：{question}\n输出一个更抽象的问题："}
        ],
        temperature=0,
        max_tokens=100,
    )
    
    return response.choices[0].message.content
```

## 性能优化

### 并行检索

```python
import asyncio


async def parallel_retrieve(queries: list[str], retriever) -> list:
    """异步并行检索多个子查询。"""
    
    async def search_one(query):
        # 在线程池中执行同步检索
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, retriever.search, query)
    
    tasks = [search_one(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 过滤失败
    return [r for r in results if not isinstance(r, Exception)]
```

### 缓存热门查询

```python
from functools import lru_cache
import hashlib


class QueryCache:
    """查询规划结果缓存。"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1小时
    
    def get_plan(self, question: str) -> list[dict] | None:
        key = f"query_plan:{hashlib.md5(question.encode()).hexdigest()}"
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def save_plan(self, question: str, plan: list[dict]):
        key = f"query_plan:{hashlib.md5(question.encode()).hexdigest()}"
        self.redis.setex(key, self.ttl, json.dumps(plan, ensure_ascii=False))
```

## 评估指标

| 指标 | 计算方式 | 目标 |
|------|---------|------|
| 子查询覆盖率 | 子查询覆盖的问题维度 / 总维度 | > 90% |
| 检索精确率 | 相关文档 / 检索返回文档 | > 60% |
| 检索召回率 | 检索到的相关文档 / 所有相关文档 | > 80% |
| 回答准确率 | 人工评估 | > 85% |
| 端到端延迟 | 从问题到回答的时间 | < 5s |

> 上表为目标参考值，实际需在你的知识库上 A/B 测试得出，勿直接当作实测结论。

## 查询规划的常见失败模式

### 失败一：分解过细

```python
# 问题："Python 和 Go 哪个好？"

# ✗ 分解过细（5个子查询，大量重叠）
bad_queries = [
    "Python 语言特点",
    "Python 优势",
    "Python 劣势",
    "Go 语言特点",
    "Go 优势",
    "Go 劣势",
    "Python Go 对比",
]

# ✓ 合理分解（3个不重叠的子查询）
good_queries = [
    "Python vs Go 性能对比 benchmark",
    "Python Go 适用场景 优势劣势",
    "Python Go 生态对比 库 工具链",
]
```

### 失败二：改写过度

```python
# 原始问题："K8s Pod 一直 CrashLoopBackOff 怎么办"

# ✗ 改写过度（丢失了关键错误信息）
bad_rewrite = "Kubernetes 容器编排 故障排查 最佳实践"

# ✓ 保留关键信息
good_rewrite = "Kubernetes Pod CrashLoopBackOff 原因 排查 解决"
```

### 失败三：忽略时间约束

```python
# 问题："上个月的服务端事故报告"

# ✗ 没有处理时间
bad_query = "服务端事故报告"

# ✓ 转化为绝对时间
good_query = "服务端事故报告 2025年4月 incident report"
```

## 与 LangChain/LlamaIndex 集成

### LangChain 集成

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import json


@tool
def plan_queries(question: str) -> str:
    """把复杂问题分解为多个检索子查询。"""
    sub_queries = decompose_query(question)
    return json.dumps(sub_queries, ensure_ascii=False)


@tool
def search_knowledge_base(query: str) -> str:
    """在知识库中检索相关文档。"""
    results = vector_store.similarity_search(query, k=5)
    return "\n---\n".join(doc.page_content[:300] for doc in results)


@tool
def check_coverage(question: str, docs: str) -> str:
    """检查检索结果是否充分回答问题。"""
    fake_doc = type("Doc", (), {"page_content": docs, "metadata": {}})()
    result = check_sufficiency(question, [], [{"doc": fake_doc}])
    return json.dumps(result, ensure_ascii=False)


def create_langchain_agent():
    """创建 LangChain 查询规划 Agent。"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    tools = [plan_queries, search_knowledge_base, check_coverage]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是查询规划专家。流程：
1. 用 plan_queries 分解问题
2. 对每个子查询用 search_knowledge_base 检索
3. 用 check_coverage 检查充分性
4. 不充分则补充检索
5. 基于所有检索结果生成回答"""),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
```

> LangChain 版本差异较大；核心是 **Prompt 用 ChatPromptTemplate**，不要用纯字符串。

### LlamaIndex 集成

```python
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode


class QueryPlanningRetriever(BaseRetriever):
    """LlamaIndex 自定义查询规划检索器。"""
    
    def __init__(self, base_retriever, llm):
        self.base_retriever = base_retriever
        self.llm = llm
    
    def _retrieve(self, query_bundle) -> list[NodeWithScore]:
        # 查询分解
        sub_queries = decompose_query(query_bundle.query_str)
        
        # 多路检索
        all_nodes = []
        for sq in sub_queries:
            nodes = self.base_retriever.retrieve(sq["query"])
            all_nodes.extend(nodes)
        
        # 去重 + 排序
        seen = set()
        unique_nodes = []
        for node in all_nodes:
            if node.node.node_id not in seen:
                seen.add(node.node.node_id)
                unique_nodes.append(node)
        
        unique_nodes.sort(key=lambda x: x.score or 0, reverse=True)
        return unique_nodes[:10]


def create_llamaindex_engine(vector_index, llm):
    """创建 LlamaIndex 查询规划引擎。"""
    base_retriever = vector_index.as_retriever(similarity_top_k=5)
    planning_retriever = QueryPlanningRetriever(base_retriever, llm)
    return RetrieverQueryEngine.from_args(planning_retriever, llm=llm)
```

## 生产环境考量

### 延迟控制

```python
import time


class LatencyBudget:
    """查询规划延迟预算。"""
    
    TOTAL_BUDGET_MS = 5000  # 总预算 5s
    
    ALLOCATION = {
        "query_decompose": 800,    # LLM 分解
        "query_rewrite": 500,      # LLM 改写（并行）
        "retrieval": 2000,         # 检索（并行）
        "sufficiency_check": 700,  # LLM 判断
        "generation": 1000,        # LLM 生成
    }
    
    @staticmethod
    def should_skip_planning(question: str) -> bool:
        """简单问题跳过规划，直接检索。"""
        # 复杂信号：含对比、时间、多实体、分析类问法 → 需要规划
        complex_signals = [
            "对比", "比较", "和", "与", "哪些", "分别",
            "去年", "上月", "最近", "为什么", "如何", "怎么",
        ]
        if any(w in question for w in complex_signals):
            return False
        # 很短且无复杂信号 → 简单事实，直接检索
        if len(question) < 20:
            return True
        return False


def answer_with_budget(question: str, agent: QueryPlanningAgent) -> dict:
    """带延迟预算的回答。"""
    start = time.time()
    
    if LatencyBudget.should_skip_planning(question):
        # 简单问题：直接检索
        results = agent.retriever.retrieve([{"rewritten_query": question, "keywords": question.split()}])
        answer = agent._generate_answer(question, results[:5])
        return {"answer": answer, "planning": "skipped"}
    
    # 复杂问题：完整规划
    result = agent.answer(question)
    elapsed = (time.time() - start) * 1000
    result["latency_ms"] = elapsed
    return result
```

### 可观测性

```python
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("query_planning")


@dataclass
class PlanningTrace:
    """查询规划全链路追踪。"""
    question: str
    sub_queries: list = field(default_factory=list)
    rewritten_queries: list = field(default_factory=list)
    retrieval_results: list = field(default_factory=list)
    sufficiency_checks: list = field(default_factory=list)
    iterations: int = 0
    total_latency_ms: float = 0
    final_answer: str = ""
    
    def log(self):
        logger.info(json.dumps({
            "question": self.question,
            "num_sub_queries": len(self.sub_queries),
            "iterations": self.iterations,
            "num_docs_retrieved": len(self.retrieval_results),
            "latency_ms": self.total_latency_ms,
            "sufficient": self.sufficiency_checks[-1].get("sufficient") if self.sufficiency_checks else None,
        }, ensure_ascii=False))
```

## 实战案例：企业知识库问答

### 场景描述

某企业内部知识库，包含：
- 技术文档（5000+ 篇）
- 产品手册（200+ 份）
- 会议纪要（10000+ 篇）
- 事故报告（500+ 份）

用户问题类型多样，从简单事实查询到复杂分析都有。

### 实现代码

```python
class EnterpriseQueryAgent:
    """企业知识库查询规划 Agent。"""
    
    def __init__(self):
        self.vector_store = load_vector_store("enterprise_kb")
        self.bm25_index = load_bm25_index("enterprise_kb")
        self.retriever = MultiPathRetriever(self.vector_store, self.bm25_index)
        self.agent = QueryPlanningAgent(self.retriever, max_iterations=2)
    
    def answer(self, question: str, user_context: dict = None) -> dict:
        """回答企业知识库问题。"""
        
        # 用户上下文补充（部门、角色、历史查询）
        context = ""
        if user_context:
            context = f"用户部门：{user_context.get('department', '')}"
        
        # 查询分类：决定是否需要规划
        query_type = self._classify_query(question)
        
        if query_type == "simple_fact":
            # 简单事实：直接检索
            results = self.retriever.retrieve(
                [{"rewritten_query": question, "keywords": question.split()}]
            )
            answer = self.agent._generate_answer(question, results[:5])
            return {"answer": answer, "type": "direct"}
        
        elif query_type == "comparison":
            # 对比类：分面检索
            return self._handle_comparison(question)
        
        elif query_type == "temporal":
            # 时间类：时间线检索
            return self._handle_temporal(question, context)
        
        else:
            # 复杂问题：完整规划
            return self.agent.answer(question, context)
    
    def _classify_query(self, question: str) -> str:
        """查询分类。"""
        if len(question) < 20 and "?" not in question:
            return "simple_fact"
        if any(w in question for w in ["对比", "比较", "区别", "哪个好"]):
            return "comparison"
        if any(w in question for w in ["上个月", "去年", "最近", "历史"]):
            return "temporal"
        return "complex"
    
    def _handle_comparison(self, question: str) -> dict:
        """处理对比类问题。"""
        sub_queries = decompose_query(question)
        # 确保每个对比对象都有独立查询
        results = self.retriever.retrieve(
            [rewrite_for_retrieval(q, "企业知识库") for q in sub_queries]
        )
        answer = self.agent._generate_answer(question, results[:10])
        return {"answer": answer, "type": "comparison"}
    
    def _handle_temporal(self, question: str, context: str) -> dict:
        """处理时间类问题。"""
        # 时间表达式解析
        sub_queries = decompose_query(question, context)
        results = self.retriever.retrieve(
            [rewrite_for_retrieval(q, "企业知识库") for q in sub_queries]
        )
        answer = self.agent._generate_answer(question, results[:10])
        return {"answer": answer, "type": "temporal"}
```

### 效果对比

> 以下为**示意数据**，用来说明各阶段收益的相对趋势；你的知识库需自行 A/B 测试。

| 方法 | 召回率 | 精确率 | 回答准确率 | 延迟 |
|------|--------|--------|-----------|------|
| 直接检索 | 45% | 32% | 51% | 1.2s |
| 查询改写 | 58% | 41% | 63% | 2.0s |
| 查询规划 | 78% | 55% | 82% | 3.5s |
| 规划 + 迭代 | 85% | 58% | 87% | 5.2s |

## 查询规划的评估体系

### 自动化评估

```python
def evaluate_planning_quality(question: str, gold_answer: str,
                              agent: QueryPlanningAgent) -> dict:
    """评估查询规划质量。"""
    
    result = agent.answer(question)
    
    # 1. 检索质量：用 LLM 判断每个检索结果的相关性
    relevance_scores = []
    for source in result["sources"]:
        score = judge_relevance(question, source.get("content", ""))
        relevance_scores.append(score)
    
    # 2. 回答质量：与金标准对比
    answer_quality = judge_answer_quality(question, result["answer"], gold_answer)
    
    # 3. 效率：迭代次数和延迟
    efficiency = {
        "iterations": result["iterations"],
        "num_queries": len(result["sub_queries"]),
    }
    
    return {
        "retrieval_precision": sum(relevance_scores) / len(relevance_scores),
        "answer_quality": answer_quality,
        "efficiency": efficiency,
    }


def judge_relevance(question: str, doc_content: str) -> float:
    """LLM 判断文档相关性（0-1）。"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"问题：{question}\n文档：{doc_content[:200]}\n\n相关性分数(0-1)："
        }],
        temperature=0,
        max_tokens=10,
    )
    try:
        return float(response.choices[0].message.content.strip())
    except ValueError:
        return 0.5
```

### A/B 测试框架

```python
class PlanningABTest:
    """查询规划 A/B 测试。"""
    
    def __init__(self):
        self.metrics = {"control": [], "treatment": []}
    
    def run(self, test_questions: list[dict]):
        """test_questions: [{"question": ..., "gold_answer": ...}]"""
        
        for item in test_questions:
            q = item["question"]
            
            # Control: 直接检索
            control_result = direct_retrieval_answer(q)
            control_score = evaluate_answer(q, control_result, item["gold_answer"])
            self.metrics["control"].append(control_score)
            
            # Treatment: 查询规划
            treatment_result = planning_agent_answer(q)
            treatment_score = evaluate_answer(q, treatment_result, item["gold_answer"])
            self.metrics["treatment"].append(treatment_score)
    
    def report(self):
        import numpy as np
        control = np.array(self.metrics["control"])
        treatment = np.array(self.metrics["treatment"])
        
        print(f"Control:   mean={control.mean():.3f}, std={control.std():.3f}")
        print(f"Treatment: mean={treatment.mean():.3f}, std={treatment.std():.3f}")
        print(f"Lift: {(treatment.mean() - control.mean()) / control.mean() * 100:.1f}%")
```

## 高级技巧

### 动态规划深度

```python
def adaptive_planning_depth(question: str, first_results: list) -> int:
    """根据第一次检索质量决定是否需要迭代。"""
    
    if not first_results:
        return 3  # 没有结果，多次迭代
    
    top_score = first_results[0].get("score", 0)
    
    if top_score > 0.9:
        return 0  # 非常相关，不需要迭代
    elif top_score > 0.7:
        return 1  # 较相关，最多一次补充
    else:
        return 2  # 不太相关，需要多次迭代
```

### 查询规划记忆

```python
class PlanningMemory:
    """记住成功的查询规划模式。"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def save_successful_plan(self, question_type: str, plan: list[dict],
                             score: float):
        """保存高分规划模式。"""
        if score > 0.8:
            key = f"plan_pattern:{question_type}"
            self.redis.lpush(key, json.dumps(plan, ensure_ascii=False))
            self.redis.ltrim(key, 0, 9)  # 保留最近 10 个
    
    def get_similar_plans(self, question_type: str) -> list:
        """获取类似问题的历史成功规划。"""
        key = f"plan_pattern:{question_type}"
        plans = self.redis.lrange(key, 0, 4)
        return [json.loads(p) for p in plans]
```

## 常见问题

**Q: 查询规划会增加多少延迟？**

A: 一次 LLM 调用约 500-800ms。如果分解为 3 个子查询并行检索，总延迟增加约 1-2s。对于简单问题可以跳过规划。

**Q: 子查询之间有重叠怎么办？**

A: RRF 融合会自动处理——同一文档被多路检索命中时，分数会叠加，排名自然靠前。重叠不是问题，遗漏才是。

**Q: 如何判断是否需要迭代补充？**

A: 两个信号：① top-1 检索分数低于阈值（如 0.7）；② LLM 判断信息不充分。两者结合使用效果最好。

**Q: 查询规划适用于所有 RAG 场景吗？**

A: 不是。简单事实查询直接检索即可。查询规划适用于多跳推理、对比分析、时间线梳理等复杂场景。

## 总结

查询规划 Agent 的核心能力：

| 能力 | 效果 |
|------|------|
| 查询分解 | 复杂问题 → 多个简单检索 |
| 查询改写 | 用户语言 → 检索语言 |
| 多路检索 | 向量 + 关键词 + 图谱互补 |
| RRF 融合 | 多路结果统一排序 |
| 迭代补充 | 不够就再查，直到充分 |
| 延迟控制 | 简单问题跳过规划 |

**实施建议**（由易到难，每步可独立上线）：

1. 先做查询改写（收益大、成本低）
2. 再加多路检索（向量 + BM25）
3. 然后加查询分解（复杂问题）
4. 最后加迭代补充（高精度场景）

**何时不必用查询规划**：

- 简单事实性问题（"年假有几天"）→ 直接检索
- 知识库很小（< 1000 篇）→ 收益有限
- 延迟预算极紧（< 2s）→ 规划 LLM 调用吃不消

**系列下一步**：[240 多步检索 Agent](multi-step-retrieval-agent) —— 当答案分散在多篇文档、需沿线索追踪时。

## 参考资源

- Query2Doc: Query Expansion with Large Language Models (2023)
- Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods (2009)
- LangChain Query Construction Guide
- LlamaIndex Query Planning Documentation
- Hypothetical Document Embeddings (HyDE) - Gao et al. (2022)
- Step-Back Prompting for Complex Reasoning (2023)

---

*本文代码已在 Python 3.11 + OpenAI API 环境验证。*
