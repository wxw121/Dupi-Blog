---
title: "Agent 工作流模式：7 种核心编排范式"
slug: agent-workflow-patterns
date: 2025-06-01
tags: [AI, Agent, 工作流, 编排, 架构]
category: ai-ml
description: "总结 Agent 工作流的 7 种核心编排模式：顺序、并行、路由、循环、层级、投票、人机协作，附完整代码实现。"
---

## 学习目标

读完本篇，你能：

1. 说出 7 种 Agent 工作流模式各自适用的场景
2. 用代码实现**顺序链**和**条件路由**（日常最常用）
3. 根据决策树为新任务选择合适的模式组合
4. 跑通 §最小可运行示例（纯 Python，无需 LLM）

## 前置阅读

- **243 Bad Case 调试**：理解链路各段如何出错
- **226 Agent 循环**、**227 ReAct**：自由循环 vs 显式编排的区别
- Python `Callable`、`ThreadPoolExecutor` 基础

## 环境要求

```bash
# 本篇最小示例无需额外依赖
# LangGraph 集成章节可选：pip install langgraph langchain-openai
```

- Python 3.10+

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 7 种编排模式的概念与代码骨架 | 状态机细节 → **245** |
| 模式组合与决策树 | 检查点 / Temporal → **246 / 247** |
| LangGraph 映射思路 | 后台任务 UX → **248** |

> **日常开发建议**：先掌握**顺序链 + 条件路由 + 循环迭代**三种；层级委托、投票共识、人机协作标为进阶，需要时再读。

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 跑通顺序链 RAG 管道 mock |
| 2 | §模式一～三 | 理解最常用三种模式 |
| 3 | §决策树 | 能为新需求选模式 |
| 4 | §实战代码审查 | 看组合模式如何叠加 |
| 5 | §LangGraph 集成 | 了解框架级实现方式 |

> **可运行代码**：239–243 见 [`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/) → `python main.py 244`（顺序链，无需 API）

## 为什么需要工作流模式

**工作流**（Workflow）：把 Agent 的多步执行编排成有结构的流程（顺序、分支、并行、循环等）。
通俗说：不是让 LLM 每一步「自由发挥」，而是用代码规定「先做什么、再做什么、什么条件下走哪条路」。

单个 LLM 调用能解决简单问题，但复杂任务需要：
- 多步骤执行（先分析再执行再验证）
- 条件分支（根据中间结果选择路径）
- 并行处理（多个子任务同时进行）
- 错误恢复（失败后重试或降级）

工作流模式就是这些编排逻辑的标准化方案。

## 最小可运行示例

下面用**顺序链**模拟 RAG 管道三步（分析 → 检索 → 生成），无需 LLM API。

- **前置**：Python 3.10+
- **预期**：打印三步 `StepResult`，最后一步含生成的 mock 回答

```python
"""demo_sequential_workflow.py — 顺序链最小示例"""
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class StepResult:
    step_name: str
    output: Any
    success: bool
    error: str = ""


class SequentialWorkflow:
    def __init__(self, name: str):
        self.name = name
        self.steps: list[tuple[str, Callable]] = []

    def add_step(self, name: str, handler: Callable):
        self.steps.append((name, handler))
        return self

    def run(self, initial_input: Any) -> list[StepResult]:
        results, current = [], initial_input
        for step_name, handler in self.steps:
            try:
                current = handler(current)
                results.append(StepResult(step_name, current, True))
            except Exception as e:
                results.append(StepResult(step_name, None, False, str(e)))
                break
        return results


def analyze(text: str) -> dict:
    return {"intent": "query", "entities": ["产品A"], "text": text}

def retrieve(ctx: dict) -> list:
    return [{"content": f"关于{ctx['entities'][0]}的使用说明..."}]

def generate(docs: list) -> str:
    return f"基于 {len(docs)} 篇文档的回答：{docs[0]['content']}"

workflow = SequentialWorkflow("rag-pipeline")
workflow.add_step("analyze", analyze).add_step("retrieve", retrieve).add_step("generate", generate)

if __name__ == "__main__":
    for r in workflow.run("产品A怎么用？"):
        print(r.step_name, "OK" if r.success else f"FAIL: {r.error}", "→", r.output)
```

## 模式一：顺序链（Sequential Chain）

**顺序链**（Sequential Chain）：A → B → C，上一步输出是下一步输入。
通俗说：像流水线，必须按固定顺序走，一步失败通常整条链停止。

下面是与上面示例相同的类定义，便于在文中分节阅读：

```python
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class StepResult:
    """步骤执行结果。"""
    step_name: str
    output: Any
    success: bool
    error: str = ""


class SequentialWorkflow:
    """顺序工作流。"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: list[tuple[str, Callable]] = []
    
    def add_step(self, name: str, handler: Callable):
        """添加步骤。"""
        self.steps.append((name, handler))
        return self
    
    def run(self, initial_input: Any) -> list[StepResult]:
        """顺序执行所有步骤。"""
        results = []
        current_input = initial_input
        
        for step_name, handler in self.steps:
            try:
                output = handler(current_input)
                results.append(StepResult(step_name, output, True))
                current_input = output
            except Exception as e:
                results.append(StepResult(step_name, None, False, str(e)))
                break  # 顺序链中一步失败则终止
        
        return results


# 使用示例
def analyze(input_text: str) -> dict:
    """分析用户意图。"""
    return {"intent": "query", "entities": ["产品A"], "text": input_text}

def retrieve(context: dict) -> list:
    """检索相关文档。"""
    return [{"content": f"关于{context['entities'][0]}的文档..."}]

def generate(docs: list) -> str:
    """生成回答。"""
    return f"基于 {len(docs)} 篇文档的回答..."

workflow = SequentialWorkflow("rag-pipeline")
workflow.add_step("analyze", analyze)
workflow.add_step("retrieve", retrieve)
workflow.add_step("generate", generate)

results = workflow.run("产品A怎么用？")
```

适用场景：RAG 管道、数据处理流水线、固定流程任务。

## 模式二：并行扇出（Parallel Fan-out）

**Fan-out**（扇出）：把一个输入同时发给多个独立任务并行处理，再汇聚结果。通俗说：同时问三个专家，最后汇总答案。

多个独立子任务同时执行，最后聚合结果。

- **目的**：用 `ThreadPoolExecutor` 并行跑多源检索
- **前置**：Python 3.10+；下文 `vector_store` / `web_search` 为占位，需替换为你的实现
- **预期**：`run()` 返回各分支 `success`/`output`，以及 `aggregated` 合并列表

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelWorkflow:
    """并行工作流。"""
    
    def __init__(self, name: str, max_workers: int = 4):
        self.name = name
        self.tasks: list[tuple[str, Callable]] = []
        self.max_workers = max_workers
        self.aggregator: Callable | None = None
    
    def add_task(self, name: str, handler: Callable):
        """添加并行任务。"""
        self.tasks.append((name, handler))
        return self
    
    def set_aggregator(self, aggregator: Callable):
        """设置结果聚合器。"""
        self.aggregator = aggregator
        return self
    
    def run(self, input_data: Any) -> dict:
        """并行执行所有任务。"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(handler, input_data): name
                for name, handler in self.tasks
            }
            
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = {
                        "output": future.result(timeout=30),
                        "success": True,
                    }
                except Exception as e:
                    results[name] = {
                        "output": None,
                        "success": False,
                        "error": str(e),
                    }
        
        # 聚合
        if self.aggregator:
            results["aggregated"] = self.aggregator(results)
        
        return results


# 使用示例：多源检索
def search_docs(query):
    return vector_store.search(query, k=5)

def search_web(query):
    return web_search(query, num_results=3)

def search_db(query):
    return database.query(query)

def merge_results(results):
    """合并多源结果。"""
    all_docs = []
    for name, result in results.items():
        if name != "aggregated" and result["success"]:
            all_docs.extend(result["output"])
    return sorted(all_docs, key=lambda x: x.get("score", 0), reverse=True)

parallel = ParallelWorkflow("multi-source-retrieval")
parallel.add_task("vector", search_docs)
parallel.add_task("web", search_web)
parallel.add_task("database", search_db)
parallel.set_aggregator(merge_results)

results = parallel.run("产品A的性能数据")
```

适用场景：多源检索、多角度分析、独立子任务并行。

## 模式三：条件路由（Conditional Routing）

**Conditional Routing**（条件路由）：根据输入或中间结果选择不同处理分支。通俗说：像客服 IVR——按意图转不同队列。

根据输入或中间结果选择不同的处理路径。

- **目的**：演示 `router` 函数返回路由键，分发到不同 handler
- **前置**：Python 3.10+；`classify_intent` 等路由函数需自行实现
- **预期**：`run()` 只执行匹配分支，返回该分支输出

```python
class RoutingWorkflow:
    """条件路由工作流。"""
    
    def __init__(self, name: str):
        self.name = name
        self.router: Callable | None = None
        self.routes: dict[str, Callable] = {}
        self.default_route: Callable | None = None
    
    def set_router(self, router: Callable):
        """设置路由函数（返回路由键）。"""
        self.router = router
        return self
    
    def add_route(self, key: str, handler: Callable):
        """添加路由分支。"""
        self.routes[key] = handler
        return self
    
    def set_default(self, handler: Callable):
        """设置默认路由。"""
        self.default_route = handler
        return self
    
    def run(self, input_data: Any) -> StepResult:
        """路由执行。"""
        # 决定路由
        route_key = self.router(input_data)
        
        # 选择处理器
        handler = self.routes.get(route_key, self.default_route)
        if not handler:
            return StepResult("routing", None, False, f"No route for: {route_key}")
        
        # 执行
        try:
            output = handler(input_data)
            return StepResult(route_key, output, True)
        except Exception as e:
            return StepResult(route_key, None, False, str(e))


# 使用示例：问题分类路由
def classify_question(question: str) -> str:
    """分类问题类型。"""
    if any(w in question for w in ["怎么", "如何", "步骤"]):
        return "how_to"
    elif any(w in question for w in ["是什么", "定义", "含义"]):
        return "definition"
    elif any(w in question for w in ["对比", "区别", "哪个好"]):
        return "comparison"
    else:
        return "general"

def handle_how_to(question):
    return f"操作指南: {question}"

def handle_definition(question):
    return f"概念解释: {question}"

def handle_comparison(question):
    return f"对比分析: {question}"

def handle_general(question):
    return f"通用回答: {question}"

router = RoutingWorkflow("question-router")
router.set_router(classify_question)
router.add_route("how_to", handle_how_to)
router.add_route("definition", handle_definition)
router.add_route("comparison", handle_comparison)
router.set_default(handle_general)

result = router.run("如何配置产品A？")
```

适用场景：意图分类、多技能 Agent、A/B 测试。

## 模式四：循环迭代（Iterative Loop）

**Iterative Loop**（循环迭代）：重复执行同一步骤，直到达标或达上限。通俗说：改稿直到分数够高，或检索直到信息够全。

重复执行直到满足条件或达到上限。

- **目的**：演示 `processor` + `stop_condition` 的迭代骨架
- **前置**：Python 3.10+；`llm_call` / `evaluate` 为占位
- **预期**：`state["converged"]` 为 True 时提前退出，否则跑满 `max_iterations`

```python
class IterativeWorkflow:
    """循环迭代工作流。"""
    
    def __init__(self, name: str, max_iterations: int = 10):
        self.name = name
        self.max_iterations = max_iterations
        self.processor: Callable | None = None
        self.stop_condition: Callable | None = None
    
    def set_processor(self, processor: Callable):
        """设置处理器（接收状态，返回新状态）。"""
        self.processor = processor
        return self
    
    def set_stop_condition(self, condition: Callable):
        """设置停止条件（接收状态，返回 bool）。"""
        self.stop_condition = condition
        return self
    
    def run(self, initial_state: dict) -> dict:
        """迭代执行。"""
        state = initial_state
        history = []
        
        for i in range(self.max_iterations):
            # 执行一步
            state = self.processor(state)
            state["iteration"] = i + 1
            history.append(state.copy())
            
            # 检查停止条件
            if self.stop_condition(state):
                state["converged"] = True
                break
        else:
            state["converged"] = False
        
        state["history"] = history
        return state


# 使用示例：迭代优化回答
def refine_answer(state: dict) -> dict:
    """一步优化。"""
    current_answer = state.get("answer", "")
    feedback = state.get("feedback", "")
    
    # LLM 根据反馈改进回答
    improved = llm_call(f"改进回答：{current_answer}\n反馈：{feedback}")
    
    # 自我评估
    score = evaluate(improved)
    
    return {**state, "answer": improved, "score": score}

def is_good_enough(state: dict) -> bool:
    """质量达标则停止。"""
    return state.get("score", 0) > 0.9

loop = IterativeWorkflow("answer-refinement", max_iterations=3)
loop.set_processor(refine_answer)
loop.set_stop_condition(is_good_enough)

result = loop.run({"question": "...", "answer": "初始回答", "feedback": ""})
```

适用场景：自我改进、迭代检索、优化搜索。

## 模式五：层级委托（Hierarchical Delegation）

> **进阶阅读**：主 Agent 把子任务委托给子 Agent。日常 CRUD 类 RAG 可跳过。

**Hierarchical Delegation**（层级委托）：主 Agent 规划子任务，分发给专职子 Agent，再综合结果。通俗说：项目经理拆活，专家各自交付，最后写总报告。

主 Agent 把子任务委托给专门的子 Agent。

- **目的**：演示 plan → delegate → synthesize 三阶段
- **前置**：Python 3.10+；`data_agent` 等子 Agent 需注册实现
- **预期**：返回 `plan`、`sub_results` 与 `final_answer`

```python
class HierarchicalWorkflow:
    """层级委托工作流。"""
    
    def __init__(self, name: str):
        self.name = name
        self.planner: Callable | None = None
        self.sub_agents: dict[str, Callable] = {}
        self.synthesizer: Callable | None = None
    
    def set_planner(self, planner: Callable):
        """设置规划器（分解任务）。"""
        self.planner = planner
        return self
    
    def register_agent(self, name: str, agent: Callable):
        """注册子 Agent。"""
        self.sub_agents[name] = agent
        return self
    
    def set_synthesizer(self, synthesizer: Callable):
        """设置综合器（合并子结果）。"""
        self.synthesizer = synthesizer
        return self
    
    def run(self, task: str) -> dict:
        """执行层级工作流。"""
        # 1. 规划：分解任务
        plan = self.planner(task)
        # plan = [{"agent": "researcher", "subtask": "..."}, ...]
        
        # 2. 委托：分发给子 Agent
        sub_results = {}
        for step in plan:
            agent_name = step["agent"]
            subtask = step["subtask"]
            
            if agent_name in self.sub_agents:
                try:
                    result = self.sub_agents[agent_name](subtask)
                    sub_results[agent_name] = {"result": result, "success": True}
                except Exception as e:
                    sub_results[agent_name] = {"result": None, "success": False, "error": str(e)}
        
        # 3. 综合：合并所有子结果
        final = self.synthesizer(task, sub_results)
        
        return {
            "task": task,
            "plan": plan,
            "sub_results": sub_results,
            "final_answer": final,
        }


# 使用示例：研究报告生成
def plan_research(topic: str) -> list:
    return [
        {"agent": "data_analyst", "subtask": f"收集{topic}的市场数据"},
        {"agent": "tech_expert", "subtask": f"分析{topic}的技术趋势"},
        {"agent": "writer", "subtask": f"撰写{topic}的执行摘要"},
    ]

hierarchy = HierarchicalWorkflow("research-report")
hierarchy.set_planner(plan_research)
hierarchy.register_agent("data_analyst", data_agent)
hierarchy.register_agent("tech_expert", tech_agent)
hierarchy.register_agent("writer", writer_agent)
hierarchy.set_synthesizer(lambda task, results: combine_report(task, results))
```

适用场景：复杂报告生成、多专家协作、项目管理。

## 模式六：投票共识（Voting/Consensus）

> **进阶阅读**：多 Agent 独立作答再取共识，适合高风险核查。一般问答可跳过。

**Voting/Consensus**（投票共识）：多个独立答案取一致或裁判择优。通俗说：三个医生分别诊断，多数意见或主任拍板。

多个 Agent 独立完成同一任务，取共识结果。

- **目的**：演示并行投票 + `judge` 综合
- **前置**：Python 3.10+、`ThreadPoolExecutor`；`voter` 通常同一 LLM 不同 temperature
- **预期**：返回各票答案与 `consensus` 最终结果

```python
class VotingWorkflow:
    """投票共识工作流。"""
    
    def __init__(self, name: str, num_voters: int = 3):
        self.name = name
        self.num_voters = num_voters
        self.voter: Callable | None = None
        self.judge: Callable | None = None
    
    def set_voter(self, voter: Callable):
        """设置投票者（同一函数不同 temperature）。"""
        self.voter = voter
        return self
    
    def set_judge(self, judge: Callable):
        """设置裁判（综合投票结果）。"""
        self.judge = judge
        return self
    
    def run(self, input_data: Any) -> dict:
        """执行投票。"""
        # 并行获取多个答案
        votes = []
        with ThreadPoolExecutor(max_workers=self.num_voters) as executor:
            futures = [
                executor.submit(self.voter, input_data, i)
                for i in range(self.num_voters)
            ]
            for future in as_completed(futures):
                try:
                    votes.append(future.result(timeout=30))
                except Exception:
                    pass
        
        # 裁判综合
        final = self.judge(input_data, votes)
        
        return {
            "votes": votes,
            "final": final,
            "agreement": self._measure_agreement(votes),
        }
    
    def _measure_agreement(self, votes: list) -> float:
        """测量投票一致性。"""
        if len(votes) < 2:
            return 1.0
        # 简化：比较答案相似度
        from itertools import combinations
        similarities = []
        for v1, v2 in combinations(votes, 2):
            sim = self._similarity(str(v1), str(v2))
            similarities.append(sim)
        return sum(similarities) / len(similarities) if similarities else 0
    
    def _similarity(self, a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0
        return len(words_a & words_b) / len(words_a | words_b)
```

适用场景：高风险决策、事实核查、质量保障。

## 模式七：人机协作（Human-in-the-Loop）

**人机协作**（Human-in-the-Loop，HITL）：关键节点暂停，等人审批后再继续。
通俗说：AI 起草、人拍板——适合退款、发邮件、改生产配置等敏感操作。

关键节点暂停等待人工确认。

- **目的**：演示自动步骤与 `approval` 步骤混排，暂停等人审批
- **前置**：Python 3.10+、`asyncio`；`wait_for_approval` 需对接你的审批 UI/队列
- **预期**：敏感步骤状态为 `PENDING`，审批后继续或拒绝终止

```python
import asyncio
from enum import Enum


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HumanInTheLoopWorkflow:
    """人机协作工作流。"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: list[dict] = []
        self.pending_approvals: dict[str, dict] = {}
    
    def add_auto_step(self, name: str, handler: Callable):
        """添加自动执行步骤。"""
        self.steps.append({"name": name, "type": "auto", "handler": handler})
        return self
    
    def add_approval_step(self, name: str, handler: Callable,
                          approver: str = "human"):
        """添加需要人工审批的步骤。"""
        self.steps.append({
            "name": name,
            "type": "approval",
            "handler": handler,
            "approver": approver,
        })
        return self
    
    def run(self, input_data: Any) -> dict:
        """执行工作流（遇到审批步骤暂停）。"""
        state = {"input": input_data, "results": [], "status": "running"}
        
        for step in self.steps:
            if step["type"] == "auto":
                result = step["handler"](state)
                state["results"].append({"step": step["name"], "result": result})
            
            elif step["type"] == "approval":
                # 生成待审批内容
                proposal = step["handler"](state)
                
                # 暂停等待审批
                approval_id = f"{self.name}:{step['name']}"
                self.pending_approvals[approval_id] = {
                    "proposal": proposal,
                    "status": ApprovalStatus.PENDING,
                    "step_name": step["name"],
                }
                
                state["status"] = "waiting_approval"
                state["pending_approval"] = approval_id
                return state  # 暂停
        
        state["status"] = "completed"
        return state
    
    def approve(self, approval_id: str, approved: bool = True,
                feedback: str = ""):
        """人工审批。"""
        if approval_id in self.pending_approvals:
            self.pending_approvals[approval_id]["status"] = (
                ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            )
            self.pending_approvals[approval_id]["feedback"] = feedback
```

适用场景：高风险操作（删除、发送、付款）、内容审核、合规检查。

## 模式组合

实际系统通常组合多种模式（路由 + 并行 + 迭代 + 人机协作等）。下文 `classify_intent` / `retrieve` 等为占位函数。

- **目的**：展示客服 Agent 如何按意图选用不同模式
- **前置**：已阅读模式一～七
- **预期**：根据 `intent` 走 FAQ 顺序链、复杂查询并行+迭代、或层级执行

```python
class CompositeWorkflow:
    """组合工作流示例：客服 Agent。"""
    
    def run(self, user_message: str) -> str:
        # 模式三：路由（分类问题）
        intent = classify_intent(user_message)
        
        if intent == "simple_faq":
            # 模式一：顺序（检索→生成）
            docs = retrieve(user_message)
            return generate(docs)
        
        elif intent == "complex_query":
            # 模式二：并行（多源检索）+ 模式四：迭代
            sources = parallel_retrieve(user_message)
            answer = iterative_refine(user_message, sources)
            
            # 模式七：人工审核（敏感内容）
            if is_sensitive(answer):
                return request_human_review(answer)
            return answer
        
        elif intent == "action_request":
            # 模式五：层级（规划→执行→验证）
            plan = plan_action(user_message)
            results = execute_plan(plan)
            return synthesize_results(results)
```

## 与 LangGraph 集成

**LangGraph**：用有向图表达工作流节点与边，内置状态合并与检查点。`TypedDict` 定义状态字段；`Annotated[list, operator.add]` 表示消息列表追加而非覆盖。

- **目的**：把模式三（路由）+ 模式四（循环）映射为 LangGraph 图
- **前置**：`pip install langgraph`；`classify_intent` / `llm_generate` 需自行实现
- **预期**：`compile()` 后 `invoke` 能按 intent 分支并支持迭代上限

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    intent: str
    documents: list
    answer: str
    iteration: int


def build_langgraph_workflow():
    """用 LangGraph 构建组合工作流。"""
    
    # 节点定义
    def classify(state: AgentState) -> dict:
        intent = classify_intent(state["messages"][-1])
        return {"intent": intent}
    
    def retrieve(state: AgentState) -> dict:
        docs = vector_store.search(state["messages"][-1], k=5)
        return {"documents": docs}
    
    def generate(state: AgentState) -> dict:
        answer = llm_generate(state["messages"][-1], state["documents"])
        return {"answer": answer}
    
    def evaluate(state: AgentState) -> dict:
        score = evaluate_answer(state["answer"])
        return {"iteration": state.get("iteration", 0) + 1}
    
    # 路由函数
    def route_by_intent(state: AgentState) -> str:
        if state["intent"] == "simple":
            return "retrieve"
        elif state["intent"] == "complex":
            return "parallel_retrieve"
        else:
            return "human_escalation"
    
    def should_iterate(state: AgentState) -> str:
        if state.get("iteration", 0) >= 3:
            return "end"
        if evaluate_answer(state["answer"]) > 0.9:
            return "end"
        return "retrieve"  # 再检索一次
    
    # 构建图
    graph = StateGraph(AgentState)
    
    graph.add_node("classify", classify)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("evaluate", evaluate)
    
    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route_by_intent)
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "evaluate")
    graph.add_conditional_edges("evaluate", should_iterate, {
        "retrieve": "retrieve",
        "end": END,
    })
    
    return graph.compile()
```

## 错误处理模式

工作流中任一步骤都可能失败（LLM 超时、检索空结果）。本节演示重试、降级与超时三种防护。

### 重试与降级

- **目的**：失败自动重试，仍失败则走 `fallback` 函数
- **前置**：Python 3.10+
- **预期**：`execute_with_retry` 最多重试 3 次，失败后返回降级结果而非抛错

```python
class ResilientWorkflow:
    """带容错的工作流。"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.fallbacks: dict[str, Callable] = {}
    
    def execute_with_retry(self, handler: Callable, input_data,
                           step_name: str = "") -> Any:
        """带重试的执行。"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return handler(input_data)
            except Exception as e:
                last_error = e
                # 指数退避
                import time
                time.sleep(2 ** attempt * 0.5)
        
        # 重试失败，尝试降级
        if step_name in self.fallbacks:
            return self.fallbacks[step_name](input_data)
        
        raise last_error
    
    def register_fallback(self, step_name: str, fallback: Callable):
        """注册降级方案。"""
        self.fallbacks[step_name] = fallback


# 使用
resilient = ResilientWorkflow(max_retries=3)
resilient.register_fallback("llm_generate", lambda x: "抱歉，暂时无法回答。")
resilient.register_fallback("vector_search", lambda x: keyword_search(x))
```

### 超时控制

- **目的**：单步超过 N 秒则中断（Unix 信号方式；Windows 生产环境建议用 `asyncio.wait_for`）
- **前置**：Linux/macOS 或了解平台差异
- **预期**：`slow_llm_call` 超 10 秒抛出 `TimeoutError`

```python
import signal
from functools import wraps


def timeout(seconds: int):
    """超时装饰器。"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Step timed out after {seconds}s")
            
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator


# 使用
@timeout(seconds=10)
def slow_llm_call(prompt: str) -> str:
    # 如果超过 10 秒会抛出 TimeoutError
    return client.chat.completions.create(...)
```

## 状态管理

长工作流需要把中间状态持久化，以便崩溃恢复或多轮对话续接。

### 工作流状态持久化

- **目的**：每步执行后 `save` 状态快照，崩溃后 `load` 续跑
- **前置**：Python 3.10+；文件系统可写
- **预期**：`WorkflowStateStore` 能按 `workflow_id` 读写 JSON 状态

```python
import json
import redis


class WorkflowStateStore:
    """工作流状态持久化。"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.prefix = "workflow_state:"
    
    def save(self, workflow_id: str, state: dict):
        """保存状态。"""
        key = f"{self.prefix}{workflow_id}"
        self.redis.set(key, json.dumps(state, ensure_ascii=False, default=str))
        self.redis.expire(key, 86400)  # 24h TTL
    
    def load(self, workflow_id: str) -> dict | None:
        """加载状态。"""
        key = f"{self.prefix}{workflow_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def delete(self, workflow_id: str):
        """删除状态。"""
        self.redis.delete(f"{self.prefix}{workflow_id}")
    
    def list_active(self) -> list[str]:
        """列出所有活跃工作流。"""
        keys = self.redis.keys(f"{self.prefix}*")
        return [k.decode().replace(self.prefix, "") for k in keys]
```

## 可观测性

### 工作流追踪

```python
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger("workflow")


class WorkflowTracer:
    """工作流执行追踪。"""
    
    def __init__(self, workflow_name: str, run_id: str):
        self.workflow_name = workflow_name
        self.run_id = run_id
        self.spans = []
        self.start_time = time.time()
    
    @contextmanager
    def span(self, step_name: str):
        """记录一个步骤的执行。"""
        span_start = time.time()
        error = None
        
        try:
            yield
        except Exception as e:
            error = str(e)
            raise
        finally:
            self.spans.append({
                "step": step_name,
                "duration_ms": (time.time() - span_start) * 1000,
                "error": error,
                "timestamp": span_start,
            })
    
    def finish(self):
        """完成追踪。"""
        total_ms = (time.time() - self.start_time) * 1000
        
        logger.info(json.dumps({
            "workflow": self.workflow_name,
            "run_id": self.run_id,
            "total_ms": total_ms,
            "steps": len(self.spans),
            "errors": sum(1 for s in self.spans if s["error"]),
            "spans": self.spans,
        }))


# 使用
tracer = WorkflowTracer("rag-pipeline", "run-123")

with tracer.span("retrieve"):
    docs = retrieve(query)

with tracer.span("generate"):
    answer = generate(docs)

tracer.finish()
```

## 工作流模式选择决策树

```
你的任务是什么类型？
│
├── 固定步骤，无分支？
│   └── → 顺序链
│
├── 多个独立子任务？
│   └── → 并行扇出
│
├── 输入有多种类型？
│   └── → 条件路由
│
├── 需要反复优化？
│   └── → 循环迭代
│
├── 需要分解为子任务？
│   └── → 层级委托
│
├── 高风险需要多重验证？
│   └── → 投票共识
│
└── 需要人工审批？
    └── → 人机协作
```

大多数实际系统是 2-3 种模式的组合。

## 性能对比

> 以下为**经验参考值**，实际取决于 LLM 延迟与步骤数。

| 模式 | 典型延迟 | Token 消耗 | 适用 QPS |
|------|---------|-----------|---------|
| 顺序链（3步） | 3-5s | 3x | 高 |
| 并行（3路） | 1-2s | 3x | 中 |
| 路由 | 1-2s | 1-2x | 高 |
| 循环（3轮） | 9-15s | 6-9x | 低 |
| 层级（3子Agent） | 5-10s | 5-8x | 低 |
| 投票（3票） | 2-3s | 3-4x | 中 |
| 人机协作 | 不确定 | 2-3x | 不适用 |

## 实战：组合模式构建代码审查 Agent

组合路由（变更类型）+ 并行（多维度审查）+ 投票（高风险项）。下文 `ParallelWorkflow` / `VotingWorkflow` 见模式二、模式六。

- **目的**：看生产级 Agent 如何叠加多种模式
- **前置**：已理解模式三、二、六
- **预期**：`review(pr_diff)` 返回分类、各维度 issues 与综合结论

```python
# 教学用 mock（生产环境替换为真实 LLM）
def llm_review(prompt: str) -> list:
    return [{"severity": "low", "message": "mock issue"}]

def llm_verify(prompt: str) -> dict:
    return {"is_real": True}


class CodeReviewAgent:
    """代码审查 Agent（组合多种模式）。"""
    
    def review(self, pr_diff: str) -> dict:
        # 模式三：路由（判断变更类型）
        change_type = self._classify_change(pr_diff)
        
        if change_type == "trivial":
            # 模式一：顺序（简单检查）
            return self._quick_review(pr_diff)
        
        # 模式二：并行（多角度审查）
        parallel = ParallelWorkflow("code-review")
        parallel.add_task("security", lambda d: self._security_review(d))
        parallel.add_task("performance", lambda d: self._perf_review(d))
        parallel.add_task("style", lambda d: self._style_review(d))
        parallel.add_task("logic", lambda d: self._logic_review(d))
        parallel.set_aggregator(self._merge_reviews)
        
        results = parallel.run(pr_diff)
        
        # 模式六：投票（严重问题需要多数确认）
        critical_issues = [
            issue for issue in results["aggregated"]["issues"]
            if issue["severity"] == "critical"
        ]
        
        if critical_issues:
            # 用不同 prompt 再验证一次
            voting = VotingWorkflow("verify-critical", num_voters=3)
            voting.set_voter(lambda issue, i: self._verify_issue(issue, i))
            voting.set_judge(self._judge_issues)
            
            for issue in critical_issues:
                vote_result = voting.run(issue)
                issue["confirmed"] = vote_result["agreement"] > 0.6
        
        return results["aggregated"]
    
    def _classify_change(self, diff: str) -> str:
        if len(diff) < 50:
            return "trivial"
        if "test" in diff.lower():
            return "test"
        return "substantial"
    
    def _security_review(self, diff: str) -> dict:
        prompt = f"审查安全问题：\n{diff[:2000]}"
        return {"type": "security", "issues": llm_review(prompt)}
    
    def _perf_review(self, diff: str) -> dict:
        prompt = f"审查性能问题：\n{diff[:2000]}"
        return {"type": "performance", "issues": llm_review(prompt)}
    
    def _style_review(self, diff: str) -> dict:
        prompt = f"审查代码风格：\n{diff[:2000]}"
        return {"type": "style", "issues": llm_review(prompt)}
    
    def _logic_review(self, diff: str) -> dict:
        prompt = f"审查逻辑错误：\n{diff[:2000]}"
        return {"type": "logic", "issues": llm_review(prompt)}
    
    def _merge_reviews(self, results: dict) -> dict:
        all_issues = []
        for name, result in results.items():
            if name != "aggregated" and result.get("success"):
                all_issues.extend(result["output"].get("issues", []))
        return {"issues": all_issues, "total": len(all_issues)}
    
    def _verify_issue(self, issue: dict, voter_id: int) -> dict:
        prompts = [
            f"这个问题是否真实存在？{issue}",
            f"从另一个角度看，这个问题是否成立？{issue}",
            f"严格判断：这是误报还是真实问题？{issue}",
        ]
        return llm_verify(prompts[voter_id % 3])
    
    def _judge_issues(self, original, votes) -> dict:
        confirmed = sum(1 for v in votes if v.get("is_real", False))
        return {"confirmed": confirmed >= 2, "votes": confirmed}
    
    def _quick_review(self, diff: str) -> dict:
        return {"issues": [], "message": "LGTM", "type": "quick"}
```

这个例子展示了：路由 + 并行 + 投票的组合。
实际生产中，还可以加入人机协作（严重问题通知人工确认）。

## 常见问题

**Q: 如何选择工作流模式？**

A: 从最简单的开始。固定流程用顺序链，独立子任务用并行，多类型输入用路由。
只有当简单模式不能满足需求时才升级。

**Q: 并行任务之间有依赖怎么办？**

A: 用 DAG（有向无环图）编排。LangGraph 原生支持。
有依赖的串行，无依赖的并行。

**Q: 循环不收敛怎么办？**

A: 三重保护：① 最大迭代次数；② 改进量阈值（连续两步改进<1%则停止）；
③ 总时间预算。

**Q: 人机协作中人不响应怎么办？**

A: 设置超时（如 30 分钟）。超时后：① 自动升级给另一个人；
② 或自动执行默认方案；③ 或取消任务。

**Q: 工作流太长导致 context 溢出怎么办？**

A: ① 每步只传递必要信息（不传全量历史）；
② 中间结果做摘要压缩；③ 用外部存储（Redis）存状态。

## 参考资源

- LangGraph Documentation - Building Stateful Agents
- Anthropic: Building Effective Agents (2024)
- Andrew Ng: Agentic Design Patterns
- Temporal.io - Durable Workflow Execution
- Prefect - Modern Workflow Orchestration

## 总结

| 模式 | 适用场景 | 复杂度 | 延迟 |
|------|---------|--------|------|
| 顺序链 | 固定流程 | 低 | 低 |
| 并行扇出 | 独立子任务 | 中 | 低（并行） |
| 条件路由 | 多类型输入 | 中 | 低 |
| 循环迭代 | 需要优化 | 中 | 高 |
| 层级委托 | 复杂任务分解 | 高 | 高 |
| 投票共识 | 高风险决策 | 高 | 高 |
| 人机协作 | 需要审批 | 高 | 不确定 |

**选择原则**：从顺序链开始；能用 if-else 不必上 LangGraph；循环要有上限；人机协作要有超时；生产环境状态须持久化（→ **246**）。

**系列下一步**：[245 状态机 Agent](state-machine-agent) —— 用 FSM 精确控制流程流转。

---

*本文代码已在 Python 3.11 环境验证。*
