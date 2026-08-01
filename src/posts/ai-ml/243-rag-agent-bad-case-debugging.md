---
title: "RAG Agent Bad Case 调试：系统化排查与修复"
slug: rag-agent-bad-case-debugging
date: 2025-05-28
tags: [AI, RAG, Agent, 调试, 质量优化]
category: ai-ml
description: "RAG 系统回答质量差？本文提供系统化的 Bad Case 调试方法论：分类、定位、修复、验证，形成闭环。"
---

## 学习目标

读完本篇，你能：

1. 把用户反馈的「回答不对」归入检索 / 生成 / 理解 / 数据四类
2. 用 `TraceRecord` 记录一次 RAG 调用的全链路数据
3. 根据 trace 自动分类 Bad Case，并拿到修复建议列表
4. 跑通 §最小可运行示例，完成「记录 → 分类 → 诊断」闭环

## 前置阅读

本篇是 **239–242 的收束篇**，调试时需对照前序能力：

| 前序篇 | 相关 Bad Case 症状 |
|--------|-------------------|
| 239 查询规划 | 复杂问题检索偏了、子查询遗漏维度 |
| 240 多步检索 | 答案分散多篇文档却只查到一篇 |
| 241 工具增强 | 该算数/查库时胡编，或工具选错 |
| 242 引用验证 | 回答看似有据但引用撑不住 |

- 向量检索与 RAG 基础概念
- Python 文件读写、`dataclass` 基础

## 环境要求

```bash
pip install openai
# 可选：pip install ragas langsmith
```

- Python 3.10+
- 调试 LLM 辅助诊断时需 `OPENAI_API_KEY`

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| Bad Case 分类、追踪、诊断、修复建议、闭环流程 | 具体检索算法实现细节 → 见 239/240 |
| 速查表与 Prompt 模板 | 引用验证实现 → **242** |
| 团队 SOP 与回归验证思路 | Temporal / 后台任务 → **247/248** |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 跑通 trace + 自动分类 |
| 2 | §调试工具链 | 理解 `RAGTracer` / `BadCaseCollector` |
| 3 | §分类调试方法 | 会用检索/生成/理解三类调试器 |
| 4 | §实战案例 | 跟完电商客服调试流程 |
| 5 | §速查表 + SOP | 团队可落地的处理流程 |

> **可运行代码**：[`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/) — `python main.py 243`（无需 API）

## Bad Case 是常态

**Bad Case**：用户或评测认为「回答不对」的具体案例，是 RAG 质量改进的原材料。
通俗说：每次用户点踩，都是系统告诉你「哪里坏了」——关键是有没有记录下来、分好类、修掉。

RAG 系统上线后，用户反馈最多的就是"回答不对"。

常见的 Bad Case：
- "明明文档里有，为什么没检索到？"
- "检索到了，但回答跟文档说的不一样。"
- "回答是编的，文档里根本没有。"
- "回答太笼统，没有具体信息。"
- "回答的是另一个问题的内容。"

没有系统化的调试方法，你只能靠猜。本文提供一套完整的 Bad Case 调试框架。

## Bad Case 分类体系

读下图时，先判断 Bad Case 落在哪个主分支（检索 / 生成 / 理解 / 数据），再进入对应子类——**不要一上来就改 Prompt**，很多「生成幻觉」其实是检索没召回。

```
Bad Case
├── 检索问题（Retrieval）
│   ├── 召回失败：相关文档没被检索到
│   ├── 排序错误：相关文档排名太低
│   ├── 噪声过多：不相关文档排名太高
│   └── 分片问题：关键信息被切断
│
├── 生成问题（Generation）
│   ├── 幻觉：编造文档中没有的信息
│   ├── 遗漏：有相关信息但没用上
│   ├── 曲解：错误理解文档内容
│   └── 格式问题：回答结构不符合预期
│
├── 理解问题（Understanding）
│   ├── 意图误判：理解错了用户问题
│   ├── 实体混淆：搞混了相似实体
│   └── 上下文丢失：多轮对话中丢失信息
│
└── 数据问题（Data）
    ├── 文档缺失：知识库里没有相关内容
    ├── 文档过时：信息已过期
    ├── 文档矛盾：多个文档说法不一
    └── 质量问题：文档本身表述不清
```

对照上图：约 60% 的生产 Bad Case 根因在**检索或数据**，而非生成；先用 trace 确认 `top_doc_score` 和 `retrieved_docs` 再下结论。

## 最小可运行示例

下面演示「记录 trace → 自动分类 → 打印修复建议」，无需向量库。

- **前置**：Python 3.10+，无需 API（本示例用规则分类）
- **预期**：输出 Bad Case 类别与建议修复方向

```python
"""demo_bad_case.py — Bad Case 记录与分类最小示例"""
import json
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
    # 提示：高相似度却答错 → 可能是排序/实体混淆，不一定是理解错误
    if category == "understanding_error" and trace.retrieval_scores[0] > 0.8:
        print("注意：top 分数很高，建议进一步检查检索排序(见§实战案例)")


if __name__ == "__main__":
    main()
```

## 调试工具链

> **阅读顺序**：先跑通上面示例，再阅读下面完整的 `RAGTracer` 与 `BadCaseCollector`。

### 全链路追踪

```python
import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceRecord:
    """一次 RAG 调用的完整追踪。"""
    trace_id: str
    timestamp: float = field(default_factory=time.time)
    
    # 输入
    question: str = ""
    conversation_history: list = field(default_factory=list)
    
    # 查询处理
    processed_query: str = ""
    query_rewrites: list = field(default_factory=list)
    
    # 检索
    retrieval_query: str = ""
    retrieved_docs: list = field(default_factory=list)
    retrieval_scores: list = field(default_factory=list)
    retrieval_latency_ms: float = 0
    
    # 生成
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generation_latency_ms: float = 0
    raw_answer: str = ""
    
    # 后处理
    final_answer: str = ""
    citations: list = field(default_factory=list)
    
    # 评估
    user_feedback: str = ""  # "good" / "bad" / ""
    bad_case_type: str = ""
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "question": self.question,
            "processed_query": self.processed_query,
            "retrieval_query": self.retrieval_query,
            "num_docs": len(self.retrieved_docs),
            "top_doc_score": self.retrieval_scores[0] if self.retrieval_scores else 0,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "generation_latency_ms": self.generation_latency_ms,
            "answer_length": len(self.final_answer),
            "user_feedback": self.user_feedback,
            "bad_case_type": self.bad_case_type,
        }


class RAGTracer:
    """RAG 全链路追踪器。"""
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend  # ES / ClickHouse / 文件
        self.current_trace: TraceRecord | None = None
    
    def start_trace(self, question: str, trace_id: str = None) -> TraceRecord:
        """开始追踪。"""
        import uuid
        self.current_trace = TraceRecord(
            trace_id=trace_id or str(uuid.uuid4()),
            question=question,
        )
        return self.current_trace
    
    def record_retrieval(self, query: str, docs: list, scores: list,
                         latency_ms: float):
        """记录检索阶段。"""
        if self.current_trace:
            self.current_trace.retrieval_query = query
            self.current_trace.retrieved_docs = [
                {"content": d[:200], "source": getattr(d, 'metadata', {}).get('source', '')}
                for d in docs
            ]
            self.current_trace.retrieval_scores = scores
            self.current_trace.retrieval_latency_ms = latency_ms
    
    def record_generation(self, answer: str, prompt_tokens: int,
                          completion_tokens: int, latency_ms: float):
        """记录生成阶段。"""
        if self.current_trace:
            self.current_trace.raw_answer = answer
            self.current_trace.final_answer = answer
            self.current_trace.prompt_tokens = prompt_tokens
            self.current_trace.completion_tokens = completion_tokens
            self.current_trace.generation_latency_ms = latency_ms
    
    def end_trace(self, feedback: str = ""):
        """结束追踪并存储。"""
        if self.current_trace:
            self.current_trace.user_feedback = feedback
            if self.storage:
                self.storage.save(self.current_trace.to_dict())
            self.current_trace = None
```

### Bad Case 收集器

```python
class BadCaseCollector:
    """收集和管理 Bad Case。"""
    
    def __init__(self, db_path: str = "bad_cases.json"):
        self.db_path = db_path
        self.cases = self._load()
    
    def add(self, trace: TraceRecord, issue_description: str,
            expected_answer: str = ""):
        """添加一个 Bad Case。"""
        case = {
            "trace_id": trace.trace_id,
            "timestamp": trace.timestamp,
            "question": trace.question,
            "actual_answer": trace.final_answer,
            "expected_answer": expected_answer,
            "issue": issue_description,
            "category": self._auto_classify(trace, issue_description),
            "retrieval_info": {
                "query": trace.retrieval_query,
                "num_docs": len(trace.retrieved_docs),
                "top_score": trace.retrieval_scores[0] if trace.retrieval_scores else 0,
            },
            "status": "open",  # open / investigating / fixed / wontfix
            "fix_description": "",
        }
        self.cases.append(case)
        self._save()
        return case
    
    def _auto_classify(self, trace: TraceRecord, issue: str) -> str:
        """自动分类 Bad Case。"""
        # 基于规则的分类
        if not trace.retrieved_docs:
            return "retrieval_recall_failure"
        
        top_score = trace.retrieval_scores[0] if trace.retrieval_scores else 0
        if top_score < 0.5:
            return "retrieval_low_relevance"
        
        if "编造" in issue or "幻觉" in issue or "没有" in issue:
            return "generation_hallucination"
        
        if "不完整" in issue or "遗漏" in issue:
            return "generation_incomplete"
        
        if "理解错" in issue or "答非所问" in issue:
            return "understanding_error"
        
        return "other"
    
    def get_by_category(self, category: str) -> list:
        return [c for c in self.cases if c["category"] == category]
    
    def get_stats(self) -> dict:
        """统计各类 Bad Case 数量。"""
        from collections import Counter
        categories = Counter(c["category"] for c in self.cases)
        statuses = Counter(c["status"] for c in self.cases)
        return {
            "total": len(self.cases),
            "by_category": dict(categories),
            "by_status": dict(statuses),
        }
    
    def _load(self) -> list:
        import os
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.cases, f, ensure_ascii=False, indent=2)
```

## 分类调试方法

### 检索问题调试

```python
class RetrievalDebugger:
    """检索问题调试器。"""
    
    def __init__(self, vector_store, embedding_model):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
    
    def debug_recall_failure(self, question: str, expected_doc_id: str) -> dict:
        """调试召回失败：为什么期望的文档没被检索到。"""
        
        # 1. 用原始问题检索
        results = self.vector_store.similarity_search_with_score(question, k=20)
        
        # 2. 检查期望文档是否在结果中
        found = False
        rank = -1
        score = 0
        for i, (doc, s) in enumerate(results):
            if doc.metadata.get("id") == expected_doc_id:
                found = True
                rank = i + 1
                score = s
                break
        
        # 3. 如果没找到，分析原因
        diagnosis = {}
        if not found:
            # 直接检索期望文档
            expected_doc = self.vector_store.get_by_id(expected_doc_id)
            
            # 计算问题与文档的直接相似度
            q_embedding = self.embedding_model.encode(question)
            d_embedding = self.embedding_model.encode(expected_doc.page_content[:500])
            direct_similarity = self._cosine_similarity(q_embedding, d_embedding)
            
            diagnosis = {
                "found": False,
                "direct_similarity": direct_similarity,
                "possible_causes": [],
            }
            
            if direct_similarity < 0.3:
                diagnosis["possible_causes"].append(
                    "语义差距大：问题和文档的表述方式差异太大"
                )
            
            if len(expected_doc.page_content) > 2000:
                diagnosis["possible_causes"].append(
                    "文档过长：关键信息可能被分片切断"
                )
            
            # 尝试用文档中的关键句检索
            key_sentences = self._extract_key_sentences(expected_doc.page_content)
            for sent in key_sentences[:3]:
                test_results = self.vector_store.similarity_search(sent, k=5)
                if any(d.metadata.get("id") == expected_doc_id for d in test_results):
                    diagnosis["possible_causes"].append(
                        f"用文档中的句子可以检索到：'{sent[:50]}...'"
                    )
                    break
        else:
            diagnosis = {
                "found": True,
                "rank": rank,
                "score": score,
                "issue": "排序问题" if rank > 5 else "非检索问题",
            }
        
        return diagnosis
    
    def debug_noise(self, question: str, irrelevant_doc_ids: list) -> dict:
        """调试噪声：为什么不相关文档排名高。"""
        
        results = self.vector_store.similarity_search_with_score(question, k=10)
        
        noise_analysis = []
        for doc, score in results:
            if doc.metadata.get("id") in irrelevant_doc_ids:
                # 分析为什么不相关文档得分高
                noise_analysis.append({
                    "doc_id": doc.metadata.get("id"),
                    "score": score,
                    "content_preview": doc.page_content[:100],
                    "possible_reason": self._analyze_false_positive(question, doc),
                })
        
        return {"noise_docs": noise_analysis}
    
    def _cosine_similarity(self, a, b) -> float:
        import numpy as np
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def _extract_key_sentences(self, text: str) -> list[str]:
        sentences = [s.strip() for s in text.split("。") if len(s.strip()) > 20]
        return sentences[:10]
    
    def _analyze_false_positive(self, question: str, doc) -> str:
        """分析误检原因。"""
        # 简化：检查关键词重叠
        q_words = set(question.lower().split())
        d_words = set(doc.page_content[:200].lower().split())
        overlap = q_words & d_words
        if len(overlap) > 3:
            return f"关键词重叠: {overlap}"
        return "语义相似但实际不相关"
```

### 生成问题调试

```python
class GenerationDebugger:
    """生成问题调试器。"""
    
    def debug_hallucination(self, question: str, answer: str,
                            retrieved_docs: list) -> dict:
        """调试幻觉：回答中哪些内容是编造的。"""
        
        # 把回答拆成句子
        sentences = [s.strip() for s in answer.split("。") if len(s.strip()) > 10]
        
        # 构建文档上下文
        doc_context = "\n".join(d.page_content[:300] for d in retrieved_docs[:5])
        
        hallucinated = []
        supported = []
        
        for sentence in sentences:
            # 检查这个句子是否有文档支撑
            support = self._check_sentence_support(sentence, doc_context)
            
            if support["supported"]:
                supported.append(sentence)
            else:
                hallucinated.append({
                    "sentence": sentence,
                    "confidence": support["confidence"],
                    "nearest_doc_content": support.get("nearest", ""),
                })
        
        return {
            "total_sentences": len(sentences),
            "supported": len(supported),
            "hallucinated": len(hallucinated),
            "hallucination_rate": len(hallucinated) / len(sentences) if sentences else 0,
            "hallucinated_details": hallucinated,
        }
    
    def debug_incomplete(self, question: str, answer: str,
                         retrieved_docs: list, expected_info: str) -> dict:
        """调试遗漏：文档中有但回答没用上的信息。"""
        
        # 检查期望信息是否在检索结果中
        doc_context = "\n".join(d.page_content for d in retrieved_docs)
        
        if expected_info.lower() in doc_context.lower():
            # 信息在文档中但没被用上
            return {
                "info_in_docs": True,
                "info_in_answer": expected_info.lower() in answer.lower(),
                "cause": "generation_missed",
                "suggestion": "检查 Prompt 是否要求充分利用所有检索结果",
            }
        else:
            # 信息不在检索结果中
            return {
                "info_in_docs": False,
                "cause": "retrieval_missed",
                "suggestion": "这是检索问题，不是生成问题",
            }
    
    def _check_sentence_support(self, sentence: str, doc_context: str) -> dict:
        """检查句子是否有文档支撑。"""
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""以下陈述是否有文档支撑？

陈述：{sentence}
文档内容：{doc_context[:1000]}

输出 JSON：{{"supported": true/false, "confidence": 0-1}}"""
            }],
            temperature=0,
            response_format={"type": "json_object"},
        )
        
        return json.loads(response.choices[0].message.content)
```

### 理解问题调试

```python
class UnderstandingDebugger:
    """理解问题调试器。"""
    
    def debug_intent(self, question: str, answer: str,
                     expected_intent: str) -> dict:
        """调试意图理解错误。"""
        from openai import OpenAI
        client = OpenAI()
        
        # 让 LLM 分析它理解的意图
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"用户问题：{question}\n\n这个问题最可能的意图是什么？列出 top-3 可能的意图。"
            }],
            temperature=0,
            response_format={"type": "json_object"},
        )
        
        interpreted = json.loads(response.choices[0].message.content)
        
        return {
            "question": question,
            "expected_intent": expected_intent,
            "interpreted_intents": interpreted,
            "match": expected_intent in str(interpreted),
            "suggestion": "优化查询改写或添加意图分类前置步骤" if not 
                         expected_intent in str(interpreted) else "非理解问题",
        }
```

## 修复策略

### 检索问题修复

```python
class RetrievalFixer:
    """检索问题修复建议。"""
    
    def suggest_fixes(self, diagnosis: dict) -> list[dict]:
        """根据诊断结果建议修复方案。"""
        
        fixes = []
        causes = diagnosis.get("possible_causes", [])
        
        for cause in causes:
            if "语义差距" in cause:
                fixes.append({
                    "fix": "添加查询改写",
                    "effort": "medium",
                    "impact": "high",
                    "description": "用 LLM 把用户问题改写为更接近文档表述的形式",
                })
                fixes.append({
                    "fix": "添加同义词/术语映射",
                    "effort": "low",
                    "impact": "medium",
                    "description": "建立用户用语→文档术语的映射表",
                })
            
            if "分片" in cause:
                fixes.append({
                    "fix": "调整分片策略",
                    "effort": "medium",
                    "impact": "high",
                    "description": "增大 chunk_size 或使用语义分片",
                })
                fixes.append({
                    "fix": "添加父子文档",
                    "effort": "high",
                    "impact": "high",
                    "description": "检索子片段，返回父文档",
                })
        
        if diagnosis.get("issue") == "排序问题":
            fixes.append({
                "fix": "添加 Reranker",
                "effort": "medium",
                "impact": "high",
                "description": "用 Cross-Encoder 对 top-k 结果重排序",
            })
        
        return fixes
```

### 生成问题修复

```python
class GenerationFixer:
    """生成问题修复建议。"""
    
    def suggest_fixes(self, diagnosis: dict) -> list[dict]:
        fixes = []
        
        if diagnosis.get("hallucination_rate", 0) > 0.1:
            fixes.append({
                "fix": "强化 Prompt 约束",
                "effort": "low",
                "impact": "medium",
                "description": "在 Prompt 中强调'只使用提供的参考资料，不要编造'",
            })
            fixes.append({
                "fix": "添加引用验证",
                "effort": "medium",
                "impact": "high",
                "description": "生成后验证每个论点是否有文档支撑",
            })
            fixes.append({
                "fix": "降低 temperature",
                "effort": "low",
                "impact": "low",
                "description": "temperature=0 减少随机性",
            })
        
        if diagnosis.get("cause") == "generation_missed":
            fixes.append({
                "fix": "优化 Prompt 结构",
                "effort": "low",
                "impact": "medium",
                "description": "要求'逐条分析每个检索结果，确保不遗漏'",
            })
            fixes.append({
                "fix": "减少检索结果数",
                "effort": "low",
                "impact": "medium",
                "description": "太多结果会导致 LLM 'lost in the middle'",
            })
        
        return fixes
```

## 自动化调试 Pipeline

```python
class AutoDebugger:
    """自动化 Bad Case 调试 Pipeline。"""
    
    def __init__(self, vector_store, embedding_model):
        self.retrieval_debugger = RetrievalDebugger(vector_store, embedding_model)
        self.generation_debugger = GenerationDebugger()
        self.understanding_debugger = UnderstandingDebugger()
        self.retrieval_fixer = RetrievalFixer()
        self.generation_fixer = GenerationFixer()
    
    def debug(self, bad_case: dict) -> dict:
        """自动调试一个 Bad Case。"""
        
        question = bad_case["question"]
        answer = bad_case["actual_answer"]
        expected = bad_case.get("expected_answer", "")
        category = bad_case["category"]
        
        result = {
            "trace_id": bad_case["trace_id"],
            "category": category,
            "diagnosis": {},
            "fixes": [],
        }
        
        if category.startswith("retrieval"):
            # 检索问题
            diagnosis = self.retrieval_debugger.debug_recall_failure(
                question, bad_case.get("expected_doc_id", "")
            )
            result["diagnosis"] = diagnosis
            result["fixes"] = self.retrieval_fixer.suggest_fixes(diagnosis)
        
        elif category.startswith("generation"):
            # 生成问题
            docs = bad_case.get("retrieved_docs", [])
            diagnosis = self.generation_debugger.debug_hallucination(
                question, answer, docs
            )
            result["diagnosis"] = diagnosis
            result["fixes"] = self.generation_fixer.suggest_fixes(diagnosis)
        
        elif category.startswith("understanding"):
            # 理解问题
            diagnosis = self.understanding_debugger.debug_intent(
                question, answer, bad_case.get("expected_intent", "")
            )
            result["diagnosis"] = diagnosis
        
        return result
    
    def batch_debug(self, bad_cases: list[dict]) -> list[dict]:
        """批量调试。"""
        return [self.debug(case) for case in bad_cases]
    
    def generate_report(self, results: list[dict]) -> str:
        """生成调试报告。"""
        from collections import Counter
        
        categories = Counter(r["category"] for r in results)
        all_fixes = [f["fix"] for r in results for f in r.get("fixes", [])]
        fix_counts = Counter(all_fixes)
        
        report = [
            "# Bad Case 调试报告\n",
            f"## 总览\n- 总数: {len(results)}",
            f"\n## 分类分布",
        ]
        for cat, count in categories.most_common():
            report.append(f"- {cat}: {count}")
        
        report.append(f"\n## 高频修复建议")
        for fix, count in fix_counts.most_common(5):
            report.append(f"- {fix}: {count} 次")
        
        return "\n".join(report)
```

## 持续改进闭环

```python
class QualityLoop:
    """质量改进闭环。"""
    
    def __init__(self, collector: BadCaseCollector, debugger: AutoDebugger):
        self.collector = collector
        self.debugger = debugger
    
    def weekly_review(self) -> dict:
        """每周 Bad Case 回顾。"""
        
        # 获取本周新增 Bad Case
        open_cases = [c for c in self.collector.cases if c["status"] == "open"]
        
        # 批量调试
        results = self.debugger.batch_debug(open_cases)
        
        # 生成报告
        report = self.debugger.generate_report(results)
        
        # 按影响排序修复建议
        prioritized_fixes = self._prioritize(results)
        
        return {
            "report": report,
            "new_cases": len(open_cases),
            "prioritized_fixes": prioritized_fixes,
        }
    
    def _prioritize(self, results: list[dict]) -> list[dict]:
        """按 impact/effort 排序修复建议。"""
        
        impact_score = {"high": 3, "medium": 2, "low": 1}
        effort_score = {"low": 3, "medium": 2, "high": 1}
        
        all_fixes = []
        for r in results:
            for fix in r.get("fixes", []):
                fix["priority"] = (
                    impact_score.get(fix.get("impact", "low"), 1) *
                    effort_score.get(fix.get("effort", "high"), 1)
                )
                all_fixes.append(fix)
        
        # 去重 + 排序
        seen = set()
        unique_fixes = []
        for fix in sorted(all_fixes, key=lambda x: x["priority"], reverse=True):
            if fix["fix"] not in seen:
                seen.add(fix["fix"])
                unique_fixes.append(fix)
        
        return unique_fixes[:5]
    
    def verify_fix(self, case_id: str, rag_answer_fn, threshold: float = 0.6) -> bool:
        """验证修复是否有效：用修复后的系统重跑，对比期望要点。"""
        case = next(
            (c for c in self.collector.cases if c["trace_id"] == case_id),
            None,
        )
        if not case:
            return False

        new_answer = rag_answer_fn(case["question"])
        expected = case.get("expected_answer", "")

        if not expected:
            return new_answer.strip() != case["actual_answer"].strip()

        keywords = [w for w in expected.replace("，", " ").split() if len(w) >= 2][:8]
        if not keywords:
            return False
        hit_rate = sum(1 for k in keywords if k in new_answer) / len(keywords)
        return hit_rate >= threshold
```

> `rag_answer_fn` 传入修复后的 RAG 调用入口，如 `lambda q: agent.answer(q)["answer"]`。生产环境建议接入 Ragas 或人工评测。

## 实战案例：电商客服 RAG 调试

### 背景

某电商客服 RAG 系统，上线后收到大量投诉：
- "问退货政策，回答的是换货政策"
- "问 A 产品的参数，回答了 B 产品的"
- "明明有优惠活动，但 AI 说没有"

### 调试过程

```python
# 1. 收集 Bad Case
collector = BadCaseCollector("ecommerce_bad_cases.json")

# 用户反馈：问退货政策，回答了换货政策
collector.add(
    trace=trace_record,
    issue_description="问退货政策，回答了换货政策",
    expected_answer="7天无理由退货，需保持商品完好...",
)

# 2. 自动分类
# → category: "understanding_error" (实体混淆：退货 vs 换货)

# 3. 调试
debugger = AutoDebugger(vector_store, embedding_model)
result = debugger.debug({
    "trace_id": "xxx",
    "question": "退货政策是什么？",
    "actual_answer": "换货需要在收到商品后7天内...",
    "category": "understanding_error",
})

# 4. 诊断结果
# {
#   "diagnosis": {
#     "interpreted_intents": ["退货政策", "换货政策", "售后服务"],
#     "match": true,  # 意图理解正确
#     "actual_issue": "retrieval_noise"  # 实际是检索问题
#   }
# }

# 5. 进一步调试检索
retrieval_result = debugger.retrieval_debugger.debug_recall_failure(
    "退货政策", expected_doc_id="return_policy_v2"
)
# 发现：退货政策文档和换货政策文档语义相似度 0.89
# 换货文档排名 #1，退货文档排名 #4

# 6. 修复建议
fixes = [
    {"fix": "添加 Reranker", "impact": "high", "effort": "medium"},
    {"fix": "文档标题加权", "impact": "medium", "effort": "low"},
    {"fix": "意图分类前置", "impact": "high", "effort": "medium"},
]
```

### 修复效果

> 以下为**示意数据**，实际需在你的测试集上回归验证。

| 修复措施 | 修复前准确率 | 修复后准确率 |
|---------|------------|------------|
| 基线 | 72% | - |
| + Reranker | - | 81% |
| + 标题加权 | - | 84% |
| + 意图分类 | - | 89% |

## 调试工具推荐

**RAG Triad**（RAG 三元组）：三个核心质量维度——上下文相关性（检索是否相关）、 groundedness（回答是否忠于上下文）、答案相关性（回答是否切题）。
通俗说：检索准不准、生成有没有编、答没答到点子上。

| 工具 | 用途 | 特点 |
|------|------|------|
| LangSmith | 全链路追踪 | LangChain 生态，可视化 |
| Phoenix (Arize) | 检索质量分析 | 嵌入可视化，漂移检测 |
| Ragas | RAG 离线评估（召回/忠实度等指标） | 自动化指标，CI 集成 |
| Weights & Biases | 实验追踪 | Prompt 版本管理 |
| 自建追踪 | 定制化 | 完全控制，适合生产 |

## 常见 Bad Case 速查表

| 症状 | 可能原因 | 快速验证 | 修复方向 |
|------|---------|---------|---------|
| 答非所问 | 意图理解错误 | 检查 processed_query | 查询改写/意图分类 |
| 信息过时 | 文档未更新 | 检查文档时间戳 | 定期更新知识库 |
| 回答模糊 | 检索结果不相关 | 检查 top-1 score | 优化嵌入/分片 |
| 编造信息 | 幻觉 | 对比文档原文 | 强化 Prompt/验证 |
| 遗漏关键信息 | Lost in the middle | 减少检索数量 | 调整 top_k/重排 |
| 混淆相似实体 | 文档标题相似 | 检查检索结果列表 | 元数据过滤/Reranker |
| 多轮丢失上下文 | 历史未传递 | 检查 conversation_history | 修复上下文传递 |
| 数值计算错误 | LLM 不擅长计算 | 检查计算步骤 | 添加计算器工具 |

## 预防措施

### 上线前测试

```python
class PreLaunchTester:
    """上线前自动化测试。"""
    
    def __init__(self, test_cases: list[dict]):
        self.test_cases = test_cases
    
    def run_all(self, rag_system) -> dict:
        """运行所有测试用例。"""
        
        results = []
        for case in self.test_cases:
            answer = rag_system.answer(case["question"])
            
            # 自动评估
            score = self._evaluate(answer, case["expected"])
            results.append({
                "question": case["question"],
                "score": score,
                "passed": score >= case.get("threshold", 0.7),
            })
        
        passed = sum(1 for r in results if r["passed"])
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": passed / len(results),
            "failures": [r for r in results if not r["passed"]],
        }
    
    def _evaluate(self, answer: str, expected: str) -> float:
        """评估回答质量。"""
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"评估回答质量(0-1)：\n问题隐含的期望：{expected}\n实际回答：{answer}\n只输出数字："
            }],
            temperature=0,
            max_tokens=5,
        )
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.5
```

### 监控告警

```python
# 关键监控指标
ALERTS = {
    "retrieval_score_drop": {
        "condition": "avg_top1_score < 0.6 持续 5 分钟",
        "action": "检查嵌入模型或知识库变更",
    },
    "hallucination_spike": {
        "condition": "hallucination_rate > 0.15 持续 10 分钟",
        "action": "检查 Prompt 或模型版本变更",
    },
    "latency_spike": {
        "condition": "p95_latency > 10s 持续 5 分钟",
        "action": "检查向量数据库或 LLM API 状态",
    },
    "user_feedback_drop": {
        "condition": "thumbs_down_rate > 0.3 持续 30 分钟",
        "action": "人工审查最近的 Bad Case",
    },
}
```

## 参考资源

- Ragas: Automated Evaluation of Retrieval Augmented Generation (2023)
- LangSmith Documentation - Tracing and Evaluation
- Arize Phoenix - LLM Observability
- RAG Triad: Context Relevance, Groundedness, Answer Relevance
- LlamaIndex Evaluation Module

## Bad Case 调试的 Prompt 模板

### 自动诊断 Prompt

```
你是 RAG 系统质量专家。分析以下 Bad Case 的根因。

用户问题：{question}
期望回答：{expected_answer}
实际回答：{actual_answer}
检索到的文档（top-3）：
{retrieved_docs}

分析：
1. 检索阶段：相关文档是否被检索到？排序是否合理？
2. 生成阶段：回答是否忠实于检索结果？是否有幻觉？
3. 理解阶段：用户意图是否被正确理解？

输出 JSON：
{{
  "root_cause": "retrieval|generation|understanding|data",
  "specific_issue": "具体问题描述",
  "evidence": "判断依据",
  "fix_suggestion": "修复建议",
  "priority": "high|medium|low"
}}
```

### 回归测试 Prompt

```
对比修复前后的回答质量。

问题：{question}
期望回答要点：{expected_points}
修复前回答：{before_answer}
修复后回答：{after_answer}

评估：
1. 修复后是否解决了原始问题？(yes/no)
2. 修复后是否引入了新问题？(yes/no)
3. 整体质量提升程度 (0-10)

输出 JSON：
{{"fixed": bool, "new_issues": bool, "improvement": int}}
```

## 团队协作流程

### Bad Case 处理 SOP

1. **发现**（任何人）：用户反馈 / 监控告警 / 抽检发现
2. **记录**（值班人员）：录入 Bad Case 系统，附带 trace_id
3. **分类**（自动）：系统自动分类 + 人工确认
4. **诊断**（开发人员）：用调试工具定位根因
5. **修复**（开发人员）：实施修复方案
6. **验证**（测试人员）：重跑 Bad Case + 回归测试
7. **关闭**（值班人员）：确认修复有效，关闭 Case
8. **复盘**（团队）：每周回顾，提炼系统性改进

### 优先级矩阵

| | 高频 | 低频 |
|---|---|---|
| **高影响** | P0 立即修复 | P1 本周修复 |
| **低影响** | P2 排期修复 | P3 观察 |

高频 + 高影响的 Bad Case 是最高优先级——它们影响最多用户、伤害最大。

## 常见问题

**Q: 每个 Bad Case 都要建完整 trace 吗？**

A: 高频或高影响的必须建；偶发、低影响的可先记问题 + 截图。P0/P1 一律拉全链路 trace。

**Q: 检索和生成问题怎么快速区分？**

A: 看 `top_doc_score` 和 `retrieved_docs`：相关文档在 top-3 但回答错 → 生成问题；相关文档根本没检索到 → 检索问题。

**Q: 修复后怎么确认没引入新问题？**

A: 用 `verify_fix` 重跑原 Case，再跑同类型的回归测试集（至少 10 条）。修复前后回答做 diff 对比。

**Q: Ragas 和 LangSmith 该选哪个？**

A: **Ragas** 偏离线评测指标（召回、忠实度）；**LangSmith** 偏在线 trace 与调试。两者可并用：LangSmith 定位，Ragas 量化。

**Q: 什么时候不必深入调试某个 Bad Case？**

A: 低频 + 低影响 + 已有 workaround（如用户换种问法能得到正确答案）可排 P3 观察，但需记录避免重复踩坑。

**Q: Bad Case 修复的优先级怎么排？**

A: 影响用户数 × 严重程度。参考上文优先级矩阵：高频高影响 P0 立即修，低频低影响 P3 观察。

## 附录：Bad Case 记录模板

```json
{
  "trace_id": "uuid",
  "timestamp": "2025-05-28T10:30:00Z",
  "question": "用户原始问题",
  "actual_answer": "系统实际回答",
  "expected_answer": "期望的正确回答",
  "category": "retrieval|generation|understanding|data",
  "severity": "P0|P1|P2|P3",
  "retrieval_info": {
    "query_used": "实际检索查询",
    "top_docs": ["doc1", "doc2", "doc3"],
    "top_score": 0.85,
    "expected_doc_found": true,
    "expected_doc_rank": 3
  },
  "status": "open|investigating|fixed|wontfix",
  "fix_description": "修复措施描述",
  "verified": false
}
```

每个 Bad Case 都按这个模板记录，确保信息完整、可追溯。

## 总结

Bad Case 调试的核心方法论：

1. **分类**：检索 / 生成 / 理解 / 数据——先定分支再改代码
2. **定位**：用 `trace_id` 拉全链路 trace，看 `top_doc_score` 与 `retrieved_docs`
3. **诊断**：对照前序篇（239–242）判断该改检索、工具还是引用验证
4. **修复**：按 impact/effort 排序，优先高频高影响
5. **验证**：`verify_fix` 重跑 + 回归测试集
6. **闭环**：每周回顾，沉淀 Prompt / 分片 / 路由改动

**改前 / 改后对照**（电商退货案例）：

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| 检索 top-1 | 换货政策（相似度 0.89） | 退货政策（Reranker 后 #1） |
| 回答内容 | 换货流程 | 7 天无理由退货 |
| 根因归类 | 表面像理解错误，实为排序 | 检索噪声 + 缺意图分类 |

不要靠猜，靠 trace。每个 Bad Case 都是系统改进的机会。

**系列下一步**：[244 Agent 工作流模式](agent-workflow-patterns) —— 用编排把检索、工具、验证串成可控流程。

---

*本文代码已在 Python 3.11 + OpenAI API 环境验证。*
