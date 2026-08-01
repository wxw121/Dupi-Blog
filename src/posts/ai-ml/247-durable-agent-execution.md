---
title: "持久化 Agent 执行：用 Temporal 构建不宕机的 Agent"
slug: durable-agent-execution
date: 2025-06-08
tags: [AI, Agent, Temporal, 持久化执行, 架构]
category: ai-ml
description: "用 Temporal 实现持久化 Agent 执行：自动重试、超时控制、工作流编排，让 Agent 任务像数据库事务一样可靠。"
---

## 学习目标

读完本篇，你能：

1. 解释 **Durable Execution**（持久化执行）与 246 手动检查点的区别
2. 用 Temporal 定义 Workflow、Activity、Worker 的基本结构
3. 配置声明式重试与超时，理解 Workflow **确定性**约束
4. 知道何时从手动检查点升级到 Temporal

## 前置阅读

- **246 检查点与恢复**：手动 save/load 的思路与局限
- **244 工作流模式**：Temporal 是工作流的工业级运行时
- Python `asyncio` 基础

## 环境要求

```bash
pip install temporalio httpx
# 需本地 Temporal Server（见 §Docker Compose 快速部署）
```

- Python 3.10+
- Docker（推荐，用于启动 Temporal Server）

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| Temporal Workflow / Activity / Worker | 用户侧进度条 UX → **248** |
| 重试、超时、Signal、Schedule | 手写 Redis 检查点细节 → **246** |

## 旧方案 vs 新方案

| 特性 | 246 手动检查点 | 本篇 Temporal |
|------|----------------|---------------|
| 状态持久化 | 你写 save/load | 平台自动 |
| 崩溃恢复 | 你写恢复逻辑 | 事件重放 |
| 重试/超时 | 你实现 | 声明式配置 |
| 学习成本 | 低 | 中 |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 0 | §最小可运行示例 | Docker 起 Server + 跑通一条 Workflow |
| 1 | §Docker Compose | 本地起 Temporal Server |
| 2 | §基础实现 | 读懂 RAG Workflow 骨架 |
| 3 | §确定性约束 | 知道 Workflow 里不能写什么 |
| 4 | §对比表 | 判断项目是否值得上 Temporal |

## 最小可运行示例

本篇依赖 Temporal Server，无法像前几篇那样纯 Python 跑通。最小验证路径：

**1. 启动 Temporal（需 Docker）**

```bash
docker compose up -d
# Server: localhost:7233  |  UI: http://localhost:8233
```

完整 `docker-compose.yml` 见下文 §Docker Compose 快速部署。

**2. 启动 Worker（终端 1）**

```bash
python worker.py   # 内含 run_worker()，注册 RAGWorkflow 与 Activity
```

**3. 触发工作流（终端 2）**

```bash
python -c "import asyncio; from client import start_rag_workflow; print(asyncio.run(start_rag_workflow('什么是 RAG？')))"
```

**预期**：终端 2 打印 Workflow 返回的最终回答；Temporal UI 中能看到 `RAGWorkflow` 执行历史与各 Activity 耗时。

> 若暂无 OpenAI Key，可把 `generate_answer` Activity 改为返回 mock 字符串，先验证「Worker 注册 → 工作流启动 → 事件重放」链路。

## 为什么需要持久化执行

上一篇（246）讲了**手动检查点**——自己 `save()` / `load()`。生产环境还需要：

- **自动重试**：API 超时自动重试，不需要手动处理
- **超时控制**：步骤超时自动取消，不会永远卡住
- **可观测性**：每个步骤的执行历史自动记录
- **版本管理**：代码更新后，正在运行的任务不受影响
- **分布式**：任务可以跨机器执行，不怕单机故障

这就是 **Durable Execution**（持久化执行，耐久执行）的价值：把「状态存哪、崩了怎么续、重试几次」交给运行时，你只写业务逻辑。Temporal 是这个领域的标杆。

## Temporal 核心概念

读下图时建立映射：**Workflow = 流程图代码**，**Activity = 真正干活的步骤**（可调 API、写库）。

```
Workflow（工作流）：Agent 的完整执行流程
Activity（活动）：工作流中的每个步骤
Worker（工作者）：执行工作流和活动的进程
Task Queue（任务队列）：分发任务的队列
```

关键特性：
- Workflow 代码必须是确定性的（可重放）
- Activity 可以有副作用（API 调用、数据库写入）
- 状态自动持久化（不需要手动保存检查点）
- 崩溃后自动恢复（重放事件历史）

**Signal**（信号）：外部异步发给 Workflow 的消息，用于取消、补充参数、人工审批结果等。通俗说：运行中的流程可以「收到一封邮件」改变行为，而不必轮询数据库。

**Replay**（重放）：Worker 崩溃后，Temporal 按事件历史从头「演」一遍 Workflow 代码以恢复状态。通俗说：像看录像带快进——代码再跑一遍，但副作用步骤（Activity）不会重复执行，只回放决策路径。

## 基础实现

### 安装与配置

```python
# pip install temporalio

from temporalio.client import Client
from temporalio.worker import Worker


async def connect_temporal() -> Client:
    """连接 Temporal Server。"""
    return await Client.connect("localhost:7233")
```

### 定义 Activity（Agent 步骤）

```python
from temporalio import activity
from dataclasses import dataclass
import httpx


@dataclass
class RetrievalInput:
    query: str
    top_k: int = 5


@dataclass
class RetrievalOutput:
    documents: list
    scores: list


@activity.defn
async def retrieve_documents(input: RetrievalInput) -> RetrievalOutput:
    """检索文档（Activity）。"""
    # 调用向量数据库
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://vector-db:8080/search",
            json={"query": input.query, "top_k": input.top_k},
            timeout=10,
        )
        data = response.json()
    
    return RetrievalOutput(
        documents=data["documents"],
        scores=data["scores"],
    )


@activity.defn
async def generate_answer(query: str, documents: list) -> str:
    """生成回答（Activity）。"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://llm-service:8080/generate",
            json={
                "prompt": f"基于以下文档回答：{query}",
                "context": documents[:5],
            },
            timeout=30,
        )
        return response.json()["answer"]


@activity.defn
async def verify_answer(query: str, answer: str, documents: list) -> dict:
    """验证回答（Activity）。"""
    # 调用验证服务
    return {"verified": True, "confidence": 0.85}
```

### 定义 Workflow（Agent 流程）

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta


@workflow.defn
class RAGWorkflow:
    """RAG Agent 工作流。"""
    
    @workflow.run
    async def run(self, query: str) -> dict:
        """执行 RAG 流程。"""
        
        # Step 1: 检索（带重试和超时）
        retrieval_result = await workflow.execute_activity(
            retrieve_documents,
            RetrievalInput(query=query, top_k=10),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
                backoff_coefficient=2.0,
            ),
        )
        
        # Step 2: 生成回答
        answer = await workflow.execute_activity(
            generate_answer,
            args=[query, retrieval_result.documents],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        # Step 3: 验证
        verification = await workflow.execute_activity(
            verify_answer,
            args=[query, answer, retrieval_result.documents],
            start_to_close_timeout=timedelta(seconds=15),
        )
        
        # Step 4: 如果验证不通过，重试检索
        if not verification.get("verified"):
            # 用不同的查询重试
            retrieval_result = await workflow.execute_activity(
                retrieve_documents,
                RetrievalInput(query=f"{query} 详细", top_k=10),
                start_to_close_timeout=timedelta(seconds=10),
            )
            answer = await workflow.execute_activity(
                generate_answer,
                args=[query, retrieval_result.documents],
                start_to_close_timeout=timedelta(seconds=30),
            )
        
        return {
            "query": query,
            "answer": answer,
            "verified": verification.get("verified", False),
            "confidence": verification.get("confidence", 0),
        }
```

### 启动 Worker

```python
import asyncio


async def run_worker():
    """启动 Temporal Worker。"""
    client = await connect_temporal()
    
    worker = Worker(
        client,
        task_queue="rag-agent-queue",
        workflows=[RAGWorkflow],
        activities=[retrieve_documents, generate_answer, verify_answer],
    )
    
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
```

### 启动工作流

```python
import uuid


async def start_rag_workflow(query: str) -> str:
    """启动 RAG 工作流。"""
    client = await connect_temporal()
    
    # 启动工作流
    handle = await client.start_workflow(
        RAGWorkflow.run,
        args=[query],
        id=f"rag-{uuid.uuid4()}",
        task_queue="rag-agent-queue",
    )
    
    # 等待结果
    result = await handle.result()
    return result


# 或者异步（不等待完成）
async def start_async(query: str) -> str:
    client = await connect_temporal()
    
    handle = await client.start_workflow(
        RAGWorkflow.run,
        args=[query],
        id=f"rag-{uuid.uuid4()}",
        task_queue="rag-agent-queue",
    )
    
    return handle.id  # 返回工作流 ID，稍后查询结果
```

## 高级模式

以下模式展示 Temporal 如何表达「多轮检索」与「子工作流」。Activity 须为幂等（重放时不重复副作用）。

### 多步迭代检索

- **目的**：检索 → 生成 → 评估充分性 → 不足则改写 query 再检索
- **前置**：Temporal Server 已启动；Activity 已实现
- **预期**：`sufficient` 为 True 时提前退出循环

```python
@workflow.defn
class IterativeRAGWorkflow:
    """迭代 RAG 工作流。"""
    
    @workflow.run
    async def run(self, query: str, max_iterations: int = 3) -> dict:
        
        all_documents = []
        answer = ""
        
        for iteration in range(max_iterations):
            # 检索
            retrieval = await workflow.execute_activity(
                retrieve_documents,
                RetrievalInput(query=query, top_k=5),
                start_to_close_timeout=timedelta(seconds=10),
            )
            all_documents.extend(retrieval.documents)
            
            # 生成
            answer = await workflow.execute_activity(
                generate_answer,
                args=[query, all_documents],
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # 评估充分性
            sufficiency = await workflow.execute_activity(
                check_sufficiency,
                args=[query, answer, all_documents],
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            if sufficiency["sufficient"]:
                break
            
            # 更新查询（基于缺失信息）
            query = sufficiency["follow_up_query"]
        
        return {"answer": answer, "iterations": iteration + 1}
```

### 并行执行

```python
@workflow.defn
class ParallelRAGWorkflow:
    """并行多源检索工作流。"""
    
    @workflow.run
    async def run(self, query: str) -> dict:
        
        # 并行检索多个来源
        vector_future = workflow.execute_activity(
            retrieve_from_vector_db,
            args=[query],
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        keyword_future = workflow.execute_activity(
            retrieve_from_elasticsearch,
            args=[query],
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        web_future = workflow.execute_activity(
            retrieve_from_web,
            args=[query],
            start_to_close_timeout=timedelta(seconds=15),
        )
        
        # 等待所有完成
        vector_docs = await vector_future
        keyword_docs = await keyword_future
        web_docs = await web_future
        
        # 合并 + 排序
        all_docs = vector_docs + keyword_docs + web_docs
        
        # 生成
        answer = await workflow.execute_activity(
            generate_answer,
            args=[query, all_docs],
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        return {"answer": answer, "sources": len(all_docs)}
```

### 人工审批（Signal）

```python
@workflow.defn
class ApprovalWorkflow:
    """带人工审批的工作流。"""
    
    def __init__(self):
        self.approved = False
        self.rejected = False
    
    @workflow.signal
    async def approve(self):
        """接收审批信号。"""
        self.approved = True
    
    @workflow.signal
    async def reject(self):
        """接收拒绝信号。"""
        self.rejected = True
    
    @workflow.run
    async def run(self, action: str) -> dict:
        
        # 执行前置步骤
        result = await workflow.execute_activity(
            prepare_action,
            args=[action],
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        # 等待人工审批（最多等 24 小时）
        try:
            await workflow.wait_condition(
                lambda: self.approved or self.rejected,
                timeout=timedelta(hours=24),
            )
        except asyncio.TimeoutError:
            return {"status": "timeout", "message": "审批超时"}
        
        if self.rejected:
            return {"status": "rejected"}
        
        # 审批通过，执行操作
        final = await workflow.execute_activity(
            execute_action,
            args=[action],
            start_to_close_timeout=timedelta(seconds=60),
        )
        
        return {"status": "completed", "result": final}
```

### 子工作流

```python
@workflow.defn
class OrchestratorWorkflow:
    """编排多个子工作流。"""
    
    @workflow.run
    async def run(self, tasks: list[str]) -> list[dict]:
        
        results = []
        
        for task in tasks:
            # 启动子工作流
            result = await workflow.execute_child_workflow(
                RAGWorkflow.run,
                args=[task],
                id=f"sub-{uuid.uuid4()}",
            )
            results.append(result)
        
        return results
```

## 错误处理

### 重试策略

```python
from temporalio.common import RetryPolicy


# 不同场景的重试策略
RETRY_POLICIES = {
    # API 调用：快速重试
    "api_call": RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=10),
        maximum_attempts=5,
        backoff_coefficient=2.0,
        non_retryable_error_types=["ValidationError"],
    ),
    
    # LLM 调用：慢速重试（可能是限流）
    "llm_call": RetryPolicy(
        initial_interval=timedelta(seconds=5),
        maximum_interval=timedelta(seconds=60),
        maximum_attempts=3,
        backoff_coefficient=3.0,
    ),
    
    # 数据库：中等重试
    "database": RetryPolicy(
        initial_interval=timedelta(seconds=2),
        maximum_attempts=3,
    ),
    
    # 不重试（幂等操作）
    "no_retry": RetryPolicy(maximum_attempts=1),
}
```

### 补偿（Saga 模式）

```python
@workflow.defn
class SagaWorkflow:
    """Saga 模式：失败时回滚已完成的步骤。"""
    
    @workflow.run
    async def run(self, order: dict) -> dict:
        
        completed = []
        
        try:
            # Step 1: 扣库存
            await workflow.execute_activity(
                reserve_inventory,
                args=[order["items"]],
                start_to_close_timeout=timedelta(seconds=10),
            )
            completed.append("inventory")
            
            # Step 2: 扣款
            await workflow.execute_activity(
                charge_payment,
                args=[order["amount"]],
                start_to_close_timeout=timedelta(seconds=15),
            )
            completed.append("payment")
            
            # Step 3: 发货
            await workflow.execute_activity(
                ship_order,
                args=[order],
                start_to_close_timeout=timedelta(seconds=30),
            )
            completed.append("shipping")
            
            return {"status": "completed"}
        
        except Exception as e:
            # 补偿：回滚已完成的步骤
            for step in reversed(completed):
                await self._compensate(step, order)
            
            return {"status": "rolled_back", "error": str(e)}
    
    async def _compensate(self, step: str, order: dict):
        """执行补偿操作。"""
        if step == "inventory":
            await workflow.execute_activity(
                release_inventory, args=[order["items"]],
                start_to_close_timeout=timedelta(seconds=10),
            )
        elif step == "payment":
            await workflow.execute_activity(
                refund_payment, args=[order["amount"]],
                start_to_close_timeout=timedelta(seconds=15),
            )
```

## 监控与运维

### Temporal Web UI

Temporal 自带 Web UI（默认 http://localhost:8233），可以看到：
- 所有工作流的执行历史
- 每个 Activity 的输入/输出/耗时
- 失败的工作流和错误信息
- 重试次数和状态

### 自定义指标

```python
from temporalio import activity
from prometheus_client import Counter, Histogram

activity_counter = Counter("agent_activities_total", "Total activities", ["type"])
activity_duration = Histogram("agent_activity_duration_seconds", "Activity duration", ["type"])


@activity.defn
async def monitored_retrieve(input: RetrievalInput) -> RetrievalOutput:
    """带监控的检索 Activity。"""
    activity_counter.labels(type="retrieve").inc()
    
    with activity_duration.labels(type="retrieve").time():
        # 实际检索逻辑
        result = await do_retrieve(input)
    
    return result
```

## 实战：完整的 Agent 工作流

```python
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from datetime import timedelta
import uuid


@dataclass
class AgentTask:
    """Agent 任务输入。"""
    task_id: str
    query: str
    user_id: str
    priority: str = "normal"
    max_iterations: int = 3


@dataclass
class AgentResult:
    """Agent 任务输出。"""
    task_id: str
    answer: str
    sources: list
    confidence: float
    iterations: int
    total_latency_ms: float


@workflow.defn
class ProductionAgentWorkflow:
    """生产级 Agent 工作流。"""
    
    @workflow.run
    async def run(self, task: AgentTask) -> AgentResult:
        start_time = workflow.now()
        
        # 1. 查询分析
        analysis = await workflow.execute_activity(
            analyze_query,
            args=[task.query],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )
        
        # 2. 路由：根据复杂度选择策略
        if analysis["complexity"] == "simple":
            answer = await self._simple_path(task.query)
        elif analysis["complexity"] == "moderate":
            answer = await self._moderate_path(task.query, analysis)
        else:
            answer = await self._complex_path(task, analysis)
        
        # 3. 后处理
        final = await workflow.execute_activity(
            post_process,
            args=[task.query, answer],
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        elapsed = (workflow.now() - start_time).total_seconds() * 1000
        
        return AgentResult(
            task_id=task.task_id,
            answer=final["answer"],
            sources=final.get("sources", []),
            confidence=final.get("confidence", 0),
            iterations=final.get("iterations", 1),
            total_latency_ms=elapsed,
        )
    
    async def _simple_path(self, query: str) -> dict:
        """简单路径：直接检索+生成。"""
        docs = await workflow.execute_activity(
            retrieve_documents,
            RetrievalInput(query=query, top_k=3),
            start_to_close_timeout=timedelta(seconds=5),
        )
        answer = await workflow.execute_activity(
            generate_answer,
            args=[query, docs.documents],
            start_to_close_timeout=timedelta(seconds=15),
        )
        return {"answer": answer, "iterations": 1}
    
    async def _moderate_path(self, query: str, analysis: dict) -> dict:
        """中等路径：多路检索+生成。"""
        # 并行检索
        vec_future = workflow.execute_activity(
            vector_search, args=[query],
            start_to_close_timeout=timedelta(seconds=5),
        )
        kw_future = workflow.execute_activity(
            keyword_search, args=[analysis["keywords"]],
            start_to_close_timeout=timedelta(seconds=5),
        )
        
        vec_docs = await vec_future
        kw_docs = await kw_future
        
        # 合并 + 生成
        all_docs = vec_docs + kw_docs
        answer = await workflow.execute_activity(
            generate_answer, args=[query, all_docs],
            start_to_close_timeout=timedelta(seconds=20),
        )
        return {"answer": answer, "iterations": 1, "sources": len(all_docs)}
    
    async def _complex_path(self, task: AgentTask, analysis: dict) -> dict:
        """复杂路径：迭代检索+验证。"""
        all_docs = []
        answer = ""
        
        for i in range(task.max_iterations):
            docs = await workflow.execute_activity(
                retrieve_documents,
                RetrievalInput(query=task.query, top_k=5),
                start_to_close_timeout=timedelta(seconds=10),
            )
            all_docs.extend(docs.documents)
            
            answer = await workflow.execute_activity(
                generate_answer, args=[task.query, all_docs],
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            check = await workflow.execute_activity(
                check_sufficiency, args=[task.query, answer],
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            if check["sufficient"]:
                break
        
        return {"answer": answer, "iterations": i + 1, "sources": len(all_docs)}
```

## 部署架构

```
┌─────────────────────────────────────────────────┐
│                  API Gateway                     │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Application Server                  │
│  (启动工作流、查询状态、接收 Signal)             │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Temporal Server                     │
│  (状态持久化、任务分发、定时器)                  │
└─────────────────────┬───────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Worker 1    │ │  Worker 2    │ │  Worker 3    │
│  (RAG 任务)  │ │  (RAG 任务)  │ │  (审批任务)  │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 常见问题

**Q: Temporal 的学习曲线陡吗？**

A: 基本概念 1-2 天能掌握。但"确定性约束"需要适应——
Workflow 代码不能有随机数、不能直接 IO、不能用非确定性库。
所有副作用必须放在 Activity 中。

**Q: 自建检查点 vs Temporal，怎么选？**

A: 如果你的 Agent 只有 3-5 步、单机运行、不需要分布式——自建检查点够了。
如果需要：自动重试、超时、分布式、版本管理、审计——用 Temporal。

**Q: Temporal Cloud 还是自建？**

A: 起步用 Temporal Cloud（免费额度够开发）。
生产环境如果数据敏感，自建（Docker Compose 一键部署）。

**Q: LLM 调用放在 Activity 中有什么注意？**

A: ① 设置合理超时（LLM 可能很慢）；② 重试时注意幂等性；
③ 非重试错误（如 prompt 太长）不要重试；④ 记录 token 消耗。

**Q: 工作流可以运行多久？**

A: 理论上无限（Temporal 支持长期运行的工作流）。
但建议设置整体超时（如 1 小时），避免僵尸工作流。

## Temporal 确定性约束详解

这是 Temporal 最重要的概念，也是新手最容易踩的坑。

### 什么是确定性

Workflow 代码在崩溃恢复时会被**重放**（replay）。
Temporal 通过重放事件历史来恢复状态。
所以 Workflow 代码必须是确定性的——同样的输入，必须产生同样的执行路径。

### 不能做的事

```python
@workflow.defn
class BadWorkflow:
    @workflow.run
    async def run(self):
        # ✗ 不能用随机数
        x = random.random()
        
        # ✗ 不能直接 IO
        response = requests.get("http://api.com")
        
        # ✗ 不能用 time.time()
        now = time.time()
        
        # ✗ 不能用非确定性库
        result = some_nondeterministic_lib.call()
        
        # ✗ 不能直接 sleep
        await asyncio.sleep(10)
```

### 正确的做法

```python
@workflow.defn
class GoodWorkflow:
    @workflow.run
    async def run(self):
        # ✓ 随机数用 workflow.random()
        x = workflow.random().random()
        
        # ✓ IO 放在 Activity 中
        response = await workflow.execute_activity(
            http_get, args=["http://api.com"],
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        # ✓ 时间用 workflow.now()
        now = workflow.now()
        
        # ✓ 等待用 workflow.sleep()
        await workflow.sleep(timedelta(seconds=10))
```

### 为什么有这个约束

因为 Temporal 需要重放 Workflow 代码来恢复状态。
如果代码不确定（比如用了随机数），重放时走的路径可能不同，
导致状态不一致。

把所有"不确定"的操作（IO、随机、时间）封装到 Activity 中，
Activity 的结果会被记录到事件历史中，重放时直接使用记录的结果。

## 测试 Temporal 工作流

```python
import pytest
from temporalio.testing import WorkflowEnvironment, ActivityEnvironment


@pytest.mark.asyncio
async def test_rag_workflow():
    """测试 RAG 工作流。"""
    
    # 使用测试环境（内存中的 Temporal）
    async with await WorkflowEnvironment.start_time_skipping() as env:
        
        # Mock Activity
        async def mock_retrieve(input):
            return RetrievalOutput(
                documents=["doc1", "doc2"],
                scores=[0.9, 0.8],
            )
        
        async def mock_generate(query, docs):
            return "mock answer"
        
        async def mock_verify(query, answer, docs):
            return {"verified": True, "confidence": 0.9}
        
        # 启动 Worker
        worker = Worker(
            env.client,
            task_queue="test-queue",
            workflows=[RAGWorkflow],
            activities=[mock_retrieve, mock_generate, mock_verify],
        )
        
        async with worker:
            # 启动工作流
            result = await env.client.execute_workflow(
                RAGWorkflow.run,
                args=["测试问题"],
                id="test-workflow",
                task_queue="test-queue",
            )
            
            assert result["answer"] == "mock answer"
            assert result["verified"] == True


@pytest.mark.asyncio
async def test_activity_retry():
    """测试 Activity 重试。"""
    
    call_count = 0
    
    @activity.defn
    async def flaky_activity(input: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("Temporary failure")
        return "success"
    
    async with ActivityEnvironment() as env:
        result = await env.run(
            flaky_activity,
            "test",
            retry_policy=RetryPolicy(maximum_attempts=5),
        )
        assert result == "success"
        assert call_count == 3
```

## 参考资源

- Temporal Python SDK Documentation
- Temporal.io - Build Invincible Apps
- Durable Execution Pattern (Temporal Blog)
- LangGraph + Temporal Integration Guide
- Netflix: Durable Execution at Scale

## Docker Compose 快速部署

```yaml
# docker-compose.yml - Temporal 开发环境
version: '3.8'

services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
    environment:
      - DB=sqlite
    volumes:
      - temporal-data:/var/lib/temporal

  temporal-ui:
    image: temporalio/ui:latest
    ports:
      - "8233:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233

  temporal-admin:
    image: temporalio/admin-tools:latest
    environment:
      - TEMPORAL_ADDRESS=temporal:7233

volumes:
  temporal-data:
```

启动：
```bash
docker compose up -d
# Temporal Server: localhost:7233
# Web UI: http://localhost:8233
```

## 与其他方案的对比

| 方案 | 适用场景 | 可靠性 | 复杂度 | 成本 |
|------|---------|--------|--------|------|
| 无（直接运行） | 开发/测试 | 低 | 低 | 低 |
| 手动检查点 | 简单生产 | 中 | 中 | 低 |
| Celery + Redis | 任务队列 | 中 | 中 | 低 |
| LangGraph + Redis | Agent 工作流 | 中高 | 中 | 低 |
| Temporal | 复杂长流程 | 高 | 高 | 中 |
| AWS Step Functions | 云原生 | 高 | 中 | 按量 |

选择原则：
- 能用简单方案解决的，不要用复杂方案
- 可靠性要求越高，方案越重
- 团队熟悉度也是重要因素

## 生产环境检查清单

- [ ] Temporal Server 高可用部署（至少 3 节点）
- [ ] Worker 多实例部署（至少 2 个）
- [ ] 所有 Activity 有超时设置
- [ ] 关键 Activity 有重试策略
- [ ] 工作流有整体超时
- [ ] 监控告警配置（失败率、延迟）
- [ ] 日志结构化（方便排查）
- [ ] 版本管理策略（Worker 滚动更新）
- [ ] 任务队列隔离（不同类型任务分队列）
- [ ] 定期清理已完成的工作流历史

每一项都做到位，才能安心跑生产。

## 版本管理（Worker 滚动更新）

Temporal 支持 Worker 版本管理，让你可以安全地更新代码而不影响正在运行的工作流。

```python
from temporalio.worker import VersioningIntent

# 旧版本 Worker
@workflow.defn
class RAGWorkflowV1:
    @workflow.run
    async def run(self, query: str) -> dict:
        docs = await workflow.execute_activity(retrieve_v1, args=[query])
        return await workflow.execute_activity(generate_v1, args=[query, docs])

# 新版本 Worker（添加验证步骤）
@workflow.defn
class RAGWorkflowV2:
    @workflow.run
    async def run(self, query: str) -> dict:
        docs = await workflow.execute_activity(retrieve_v2, args=[query])
        answer = await workflow.execute_activity(generate_v2, args=[query, docs])
        # 新增：验证步骤
        verified = await workflow.execute_activity(verify, args=[answer])
        return {"answer": answer, "verified": verified}
```

滚动更新策略：
1. 部署新版本 Worker（新旧并存）
2. 新工作流走新版本
3. 旧工作流继续在旧版本完成
4. 等所有旧工作流完成后，下线旧 Worker

## 定时工作流（Schedule）

```python
from temporalio.client import Schedule, ScheduleActionStartWorkflow


async def create_daily_report_schedule(client: Client):
    """创建每日报告定时任务。"""
    
    await client.create_schedule(
        id="daily-report",
        schedule=Schedule(
            action=ScheduleActionStartWorkflow(
                workflow=DailyReportWorkflow.run,
                task_queue="report-queue",
            ),
            spec=ScheduleSpec(
                cron_expressions=["0 9 * * *"],  # 每天 9 点
            ),
        ),
    )
```

适用场景：
- 每日数据汇总
- 定期知识库更新
- 定时质量检查
- 周期性报告生成

## 附录：Temporal 术语表

| 术语 | 含义 |
|------|------|
| Workflow | 持久化函数，定义执行流程 |
| Activity | 具体操作（可以有副作用） |
| Worker | 执行 Workflow/Activity 的进程 |
| Task Queue | 任务分发队列 |
| Signal | 外部发送给 Workflow 的异步消息 |
| Query | 同步查询 Workflow 状态 |
| Schedule | 定时触发 Workflow |
| Namespace | 隔离环境（类似数据库 schema） |
| Event History | Workflow 的完整执行日志 |
| Replay | 重放事件历史恢复状态 |

掌握这些术语，你就能流畅地阅读 Temporal 文档了。

## 附录：最小 Worker + Client 单文件

下面把 Worker 与 Client 合并为一个可运行文件（需 Docker 起 Temporal + mock Activity）。完整版亦见 [`examples/rag-agent-lab/temporal_minimal.py`](../../../examples/rag-agent-lab/temporal_minimal.py)。

```python
"""temporal_minimal.py — 验证 Worker 注册 → 启动 Workflow → 获取结果"""
import asyncio
import uuid
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class RetrievalInput:
    query: str


@activity.defn
async def retrieve_documents(inp: RetrievalInput) -> list[str]:
    return [f"mock doc about {inp.query}"]


@activity.defn
async def generate_answer(query: str, docs: list[str]) -> str:
    return f"Answer for {query}: {docs[0]}"


@workflow.defn
class RAGWorkflow:
    @workflow.run
    async def run(self, query: str) -> str:
        docs = await workflow.execute_activity(
            retrieve_documents,
            RetrievalInput(query),
            start_to_close_timeout=timedelta(seconds=10),
        )
        return await workflow.execute_activity(
            generate_answer,
            args=[query, docs],
            start_to_close_timeout=timedelta(seconds=10),
        )


async def main():
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="rag-agent-queue",
        workflows=[RAGWorkflow],
        activities=[retrieve_documents, generate_answer],
    ):
        handle = await client.start_workflow(
            RAGWorkflow.run,
            "什么是 RAG？",
            id=f"rag-{uuid.uuid4()}",
            task_queue="rag-agent-queue",
        )
        print(await handle.result())


if __name__ == "__main__":
    asyncio.run(main())
```

运行：`docker compose up -d` 后 `python temporal_minimal.py`。

## 总结

| 特性 | 246 手动检查点 | Temporal |
|------|----------------|----------|
| 状态持久化 | 手动 | 自动 |
| 崩溃恢复 | 手动 | 事件重放 |
| 重试/超时 | 手写 | 声明式 |
| 分布式 | 手写 | 内置 |

**选择建议**：< 5 步单机任务用手动检查点；5–20 步用 LangGraph + Redis；长流程、高可靠、分布式用 Temporal。

**系列下一步**：[248 Agent 后台任务](agent-background-job) —— 解决「用户不必同步等待」的体验问题。

---

*本文代码基于 Temporal Python SDK 1.6+。*
*持久化执行是 Agent 工程化的终极形态。掌握它，你的系统就真正生产就绪了。*
