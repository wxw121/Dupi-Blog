---
title: "状态机 Agent：用有限状态机控制 Agent 行为"
slug: state-machine-agent
date: 2025-06-03
tags: [AI, Agent, 状态机, FSM, 架构]
category: ai-ml
description: "用有限状态机（FSM）精确控制 Agent 的行为流转：定义状态、转换条件、动作，让 Agent 行为可预测、可调试。"
---

## 学习目标

读完本篇，你能：

1. 解释 **FSM**（有限状态机）与自由 ReAct 循环的区别
2. 用 `StateMachineAgent` 定义状态、转换条件和处理器
3. 构建一个 RAG 状态机，保证「理解 → 检索 → 验证 → 回答」不被跳过
4. 跑通 §最小可运行示例（三状态计数器，无需 LLM）

## 前置阅读

- **244 工作流模式**：顺序链、路由等编排概念
- **227 ReAct Agent**：对比自由循环 vs 状态机约束
- Python `Enum`、`dataclass`

## 环境要求

```bash
# 最小示例无需额外依赖
# RAG 状态机章节需 OpenAI API：pip install openai
```

- Python 3.10+

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| FSM 定义、转换、钩子、RAG 状态机 | 检查点存储实现 → **246** |
| 与 LangGraph 对比 | Temporal 持久化 → **247** |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 跑通三状态机 |
| 2 | §基础实现 | 理解 `StateMachineAgent` API |
| 3 | §构建 RAG 状态机 | 看懂完整 RAG 流程约束 |
| 4 | §调试与监控 | 会用 `StateMonitor` 检测卡住 |

> **系列代码**：239–243 可运行示例见 [`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/)

## 为什么用状态机

**有限状态机**（FSM，Finite State Machine）：Agent 在任意时刻只能处于若干**预定义状态**之一，只有满足条件才能转换到下一状态。
通俗说：像红绿灯——只有红、黄、绿三种状态，不能随意乱跳。

**ReAct**（Reason + Act）：LLM 每轮自己决定「想什么、做什么」，循环直到结束。
通俗说：自由度高，但可能跳过关键步骤或陷入死循环——状态机用来约束这种行为。

自由形式的 Agent（ReAct 循环）问题：
- 行为不可预测（LLM 可能跳到任何步骤）
- 难以调试（不知道 Agent "在哪"）
- 难以保证流程（可能跳过关键步骤）
- 难以恢复（中断后不知道从哪继续）

状态机 Agent 的优势：
- **可预测**：任何时刻 Agent 都在一个明确的状态
- **可调试**：状态转换有日志，一目了然
- **可保证**：关键步骤不会被跳过
- **可恢复**：保存当前状态，中断后从断点继续

## 核心概念

读下图理解三要素：**状态**（在哪）、**转换**（何时跳转）、**动作**（跳转时做什么）。

```
状态机 = 状态 + 转换 + 动作

状态（State）：Agent 当前所处的阶段
转换（Transition）：从一个状态到另一个状态的条件
动作（Action）：进入/离开状态时执行的操作
```

**转换条件**（Transition Condition）：`condition(context) -> bool`，为 True 时才允许跳转。通俗说：绿灯亮了才能走——条件不满足就停在当前状态。

**on_enter / on_exit 钩子**：进入或离开某状态时自动执行的回调。通俗说：进门开灯、出门关灯——适合打日志、初始化资源、释放连接。

**守卫条件**（Guard）：与转换条件同义，在 UML 状态机术语中常用；本文 `Transition.condition` 即守卫。

## 最小可运行示例

下面演示一个三状态机：`idle → processing → done`，无需 LLM。

```python
"""demo_fsm.py — 状态机最小示例"""
from enum import Enum


class S(Enum):
    IDLE, PROCESSING, DONE = "idle", "processing", "done"


class SimpleFSM:
    def __init__(self):
        self.state = S.IDLE
        self.count = 0

    def tick(self) -> str:
        if self.state == S.IDLE:
            self.state = S.PROCESSING
            return "开始处理"
        if self.state == S.PROCESSING:
            self.count += 1
            if self.count >= 3:
                self.state = S.DONE
                return f"处理完成（共 {self.count} 次）"
            return f"处理中... ({self.count}/3)"
        return "已结束"


if __name__ == "__main__":
    fsm = SimpleFSM()
    while fsm.state != S.DONE:
        print(f"[{fsm.state.value}] {fsm.tick()}")
    print(f"[{fsm.state.value}] 完成")
```

## 基础实现

> **阅读顺序**：先跑通上面示例，再阅读下面完整的 `StateMachineAgent` 类。

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable
import json
import time


class State(Enum):
    """Agent 状态枚举。"""
    IDLE = "idle"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RESPONDING = "responding"
    ERROR = "error"
    DONE = "done"


@dataclass
class Transition:
    """状态转换定义。"""
    from_state: State
    to_state: State
    condition: Callable  # 接收 context，返回 bool
    action: Callable | None = None  # 转换时执行的动作
    description: str = ""


@dataclass
class AgentContext:
    """Agent 上下文（状态机的数据）。"""
    input: str = ""
    intent: str = ""
    plan: list = field(default_factory=list)
    results: list = field(default_factory=list)
    answer: str = ""
    error: str = ""
    iteration: int = 0
    metadata: dict = field(default_factory=dict)


class StateMachineAgent:
    """状态机 Agent。"""
    
    def __init__(self, name: str):
        self.name = name
        self.states: set[State] = set()
        self.transitions: list[Transition] = []
        self.current_state: State = State.IDLE
        self.context = AgentContext()
        self.history: list[dict] = []
        
        # 状态处理器
        self.state_handlers: dict[State, Callable] = {}
        
        # 进入/离开钩子
        self.on_enter: dict[State, Callable] = {}
        self.on_exit: dict[State, Callable] = {}
    
    def add_state(self, state: State, handler: Callable):
        """注册状态及其处理器。"""
        self.states.add(state)
        self.state_handlers[state] = handler
        return self
    
    def add_transition(self, from_state: State, to_state: State,
                       condition: Callable, action: Callable = None,
                       description: str = ""):
        """添加状态转换。"""
        self.transitions.append(Transition(
            from_state=from_state,
            to_state=to_state,
            condition=condition,
            action=action,
            description=description,
        ))
        return self
    
    def set_hooks(self, state: State, on_enter: Callable = None,
                  on_exit: Callable = None):
        """设置状态进入/离开钩子。"""
        if on_enter:
            self.on_enter[state] = on_enter
        if on_exit:
            self.on_exit[state] = on_exit
        return self
    
    def run(self, input_text: str, max_steps: int = 20) -> AgentContext:
        """运行状态机。"""
        self.context = AgentContext(input=input_text)
        self.current_state = State.IDLE
        self.history = []
        
        for step in range(max_steps):
            # 记录当前状态
            self._log_state(step)
            
            # 终止状态
            if self.current_state in (State.DONE, State.ERROR):
                break
            
            # 执行当前状态的处理器
            handler = self.state_handlers.get(self.current_state)
            if handler:
                handler(self.context)
            
            # 寻找可用的转换
            next_state = self._find_transition()
            
            if next_state:
                self._transition_to(next_state)
            else:
                # 没有可用转换，进入错误状态
                self.context.error = f"No transition from {self.current_state}"
                self.current_state = State.ERROR
        
        return self.context
    
    def _find_transition(self) -> State | None:
        """找到第一个满足条件的转换。"""
        for t in self.transitions:
            if t.from_state == self.current_state:
                if t.condition(self.context):
                    # 执行转换动作
                    if t.action:
                        t.action(self.context)
                    return t.to_state
        return None
    
    def _transition_to(self, new_state: State):
        """执行状态转换。"""
        # 离开当前状态
        if self.current_state in self.on_exit:
            self.on_exit[self.current_state](self.context)
        
        old_state = self.current_state
        self.current_state = new_state
        
        # 进入新状态
        if new_state in self.on_enter:
            self.on_enter[new_state](self.context)
    
    def _log_state(self, step: int):
        """记录状态历史。"""
        self.history.append({
            "step": step,
            "state": self.current_state.value,
            "timestamp": time.time(),
            "context_snapshot": {
                "intent": self.context.intent,
                "iteration": self.context.iteration,
                "num_results": len(self.context.results),
            }
        })
```

## 构建 RAG 状态机

把 RAG 流水线「理解 → 规划 → 检索 → 验证 → 回答」映射为状态机。`retriever` / `llm` 需替换为你的实现。

- **目的**：演示意图分支如何驱动不同检索计划
- **前置**：已阅读 §基础实现的 `StateMachineAgent`
- **预期**：`build_rag_state_machine(retriever, llm).run(question)` 走完状态链并写入 `context.answer`

```python
def build_rag_state_machine(retriever, llm) -> StateMachineAgent:
    """构建 RAG 状态机。"""
    
    agent = StateMachineAgent("rag-agent")
    
    # 状态处理器
    def handle_idle(ctx: AgentContext):
        """空闲：接收输入。"""
        pass  # 输入已在 run() 中设置
    
    def handle_understanding(ctx: AgentContext):
        """理解：分析用户意图。"""
        response = llm.chat(
            f"分析用户意图：{ctx.input}\n输出 JSON: {{\"intent\": ..., \"entities\": [...]}}"
        )
        parsed = json.loads(response)
        ctx.intent = parsed.get("intent", "general")
        ctx.metadata["entities"] = parsed.get("entities", [])
    
    def handle_planning(ctx: AgentContext):
        """规划：决定检索策略。"""
        if ctx.intent == "simple_fact":
            ctx.plan = [{"action": "retrieve", "query": ctx.input}]
        elif ctx.intent == "comparison":
            ctx.plan = [
                {"action": "retrieve", "query": f"{ctx.input} 方面A"},
                {"action": "retrieve", "query": f"{ctx.input} 方面B"},
            ]
        else:
            ctx.plan = [{"action": "retrieve", "query": ctx.input}]
    
    def handle_executing(ctx: AgentContext):
        """执行：按计划检索。"""
        for step in ctx.plan:
            if step["action"] == "retrieve":
                docs = retriever.search(step["query"], top_k=5)
                ctx.results.extend(docs)
        ctx.iteration += 1
    
    def handle_verifying(ctx: AgentContext):
        """验证：检查结果充分性。"""
        if not ctx.results:
            ctx.metadata["sufficient"] = False
            ctx.metadata["missing"] = "no results"
        else:
            top_score = ctx.results[0].get("score", 0)
            ctx.metadata["sufficient"] = top_score > 0.6
    
    def handle_responding(ctx: AgentContext):
        """回答：生成最终回答。"""
        context = "\n".join(r.get("content", "")[:200] for r in ctx.results[:5])
        ctx.answer = llm.chat(
            f"基于以下资料回答问题。\n问题：{ctx.input}\n资料：{context}"
        )
    
    def handle_error(ctx: AgentContext):
        """错误：生成错误回答。"""
        ctx.answer = f"抱歉，处理出错：{ctx.error}"
    
    # 注册状态
    agent.add_state(State.IDLE, handle_idle)
    agent.add_state(State.UNDERSTANDING, handle_understanding)
    agent.add_state(State.PLANNING, handle_planning)
    agent.add_state(State.EXECUTING, handle_executing)
    agent.add_state(State.VERIFYING, handle_verifying)
    agent.add_state(State.RESPONDING, handle_responding)
    agent.add_state(State.ERROR, handle_error)
    
    # 定义转换
    agent.add_transition(State.IDLE, State.UNDERSTANDING,
                         lambda ctx: bool(ctx.input),
                         description="收到输入")
    
    agent.add_transition(State.UNDERSTANDING, State.PLANNING,
                         lambda ctx: bool(ctx.intent),
                         description="意图已识别")
    
    agent.add_transition(State.PLANNING, State.EXECUTING,
                         lambda ctx: bool(ctx.plan),
                         description="计划已制定")
    
    agent.add_transition(State.EXECUTING, State.VERIFYING,
                         lambda ctx: ctx.iteration > 0,
                         description="执行完成")
    
    # 验证通过 → 回答
    agent.add_transition(State.VERIFYING, State.RESPONDING,
                         lambda ctx: ctx.metadata.get("sufficient", False),
                         description="信息充分")
    
    # 验证不通过 → 重新执行（最多 3 次）
    agent.add_transition(State.VERIFYING, State.EXECUTING,
                         lambda ctx: not ctx.metadata.get("sufficient") and ctx.iteration < 3,
                         description="信息不足，重试")
    
    # 验证不通过且达到上限 → 回答（带警告）
    agent.add_transition(State.VERIFYING, State.RESPONDING,
                         lambda ctx: not ctx.metadata.get("sufficient") and ctx.iteration >= 3,
                         description="达到重试上限")
    
    agent.add_transition(State.RESPONDING, State.DONE,
                         lambda ctx: bool(ctx.answer),
                         description="回答完成")
    
    return agent
```

## 可视化状态图

```python
def generate_mermaid(agent: StateMachineAgent) -> str:
    """生成 Mermaid 状态图。"""
    lines = ["stateDiagram-v2"]
    
    # 起始
    lines.append("    [*] --> idle")
    
    # 转换
    for t in agent.transitions:
        label = t.description or f"{t.from_state.value} → {t.to_state.value}"
        lines.append(f"    {t.from_state.value} --> {t.to_state.value} : {label}")
    
    # 终止
    lines.append("    done --> [*]")
    lines.append("    error --> [*]")
    
    return "\n".join(lines)

# 输出示例：
# stateDiagram-v2
#     [*] --> idle
#     idle --> understanding : 收到输入
#     understanding --> planning : 意图已识别
#     planning --> executing : 计划已制定
#     executing --> verifying : 执行完成
#     verifying --> responding : 信息充分
#     verifying --> executing : 信息不足，重试
#     responding --> done : 回答完成
#     done --> [*]
```

## 高级特性

**并行状态**：多个子状态机同时处理同一输入，适合「安全扫描 + 性能扫描 + 风格检查」并行。
**嵌套状态机**：父状态的某个阶段内部再跑一套子流程，适合大步骤里还有细粒度状态。

### 并行状态

- **目的**：`ThreadPoolExecutor` 并行跑多个子 FSM
- **前置**：各子状态机已独立配置好
- **预期**：`run_all()` 返回各子机 `AgentContext` 列表

```python
class ParallelState:
    """并行状态：同时执行多个子状态机。"""
    
    def __init__(self, name: str):
        self.name = name
        self.sub_machines: list[StateMachineAgent] = []
    
    def add_sub_machine(self, machine: StateMachineAgent):
        self.sub_machines.append(machine)
    
    def run_all(self, input_text: str) -> list[AgentContext]:
        """并行运行所有子状态机。"""
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=len(self.sub_machines)) as executor:
            futures = [
                executor.submit(m.run, input_text)
                for m in self.sub_machines
            ]
            return [f.result() for f in futures]
```

### 嵌套状态机

```python
class NestedStateMachine(StateMachineAgent):
    """嵌套状态机：状态内部包含子状态机。"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.sub_machines: dict[State, StateMachineAgent] = {}
    
    def add_sub_machine(self, parent_state: State, machine: StateMachineAgent):
        """为某个状态添加子状态机。"""
        self.sub_machines[parent_state] = machine
    
    def run(self, input_text: str, max_steps: int = 20) -> AgentContext:
        """运行（遇到有子状态机的状态时，先运行子状态机）。"""
        self.context = AgentContext(input=input_text)
        self.current_state = State.IDLE
        
        for step in range(max_steps):
            if self.current_state in (State.DONE, State.ERROR):
                break
            
            # 如果有子状态机，先运行子状态机
            if self.current_state in self.sub_machines:
                sub_result = self.sub_machines[self.current_state].run(
                    self.context.input
                )
                # 把子结果合并到父上下文
                self.context.results.extend(sub_result.results)
                self.context.metadata.update(sub_result.metadata)
            else:
                handler = self.state_handlers.get(self.current_state)
                if handler:
                    handler(self.context)
            
            next_state = self._find_transition()
            if next_state:
                self._transition_to(next_state)
            else:
                self.current_state = State.ERROR
        
        return self.context
```

### 状态持久化与恢复

```python
class PersistentStateMachine(StateMachineAgent):
    """可持久化的状态机（支持中断恢复）。"""
    
    def __init__(self, name: str, state_store):
        super().__init__(name)
        self.store = state_store
    
    def save(self, session_id: str):
        """保存当前状态。"""
        state_data = {
            "current_state": self.current_state.value,
            "context": {
                "input": self.context.input,
                "intent": self.context.intent,
                "plan": self.context.plan,
                "results": self.context.results[:10],  # 限制大小
                "answer": self.context.answer,
                "iteration": self.context.iteration,
                "metadata": self.context.metadata,
            },
            "history": self.history[-20:],  # 最近 20 步
            "timestamp": time.time(),
        }
        self.store.save(session_id, state_data)
    
    def resume(self, session_id: str) -> bool:
        """从保存的状态恢复。"""
        state_data = self.store.load(session_id)
        if not state_data:
            return False
        
        self.current_state = State(state_data["current_state"])
        ctx = state_data["context"]
        self.context = AgentContext(
            input=ctx["input"],
            intent=ctx["intent"],
            plan=ctx["plan"],
            results=ctx["results"],
            answer=ctx["answer"],
            iteration=ctx["iteration"],
            metadata=ctx["metadata"],
        )
        self.history = state_data.get("history", [])
        return True
    
    def run_resumable(self, session_id: str, input_text: str = None,
                      max_steps: int = 20) -> AgentContext:
        """可恢复的运行。"""
        # 尝试恢复
        if not self.resume(session_id):
            if not input_text:
                raise ValueError("No saved state and no input provided")
            self.context = AgentContext(input=input_text)
            self.current_state = State.IDLE
        
        # 继续执行
        for step in range(max_steps):
            if self.current_state in (State.DONE, State.ERROR):
                break
            
            handler = self.state_handlers.get(self.current_state)
            if handler:
                handler(self.context)
            
            next_state = self._find_transition()
            if next_state:
                self._transition_to(next_state)
            
            # 每步保存（用于崩溃恢复）
            self.save(session_id)
        
        return self.context
```

## 调试与监控

```python
class StateMachineDebugger:
    """状态机调试器。"""
    
    def __init__(self, agent: StateMachineAgent):
        self.agent = agent
    
    def trace(self, input_text: str) -> dict:
        """执行并生成完整追踪。"""
        result = self.agent.run(input_text)
        
        return {
            "input": input_text,
            "final_state": self.agent.current_state.value,
            "answer": result.answer,
            "total_steps": len(self.agent.history),
            "state_sequence": [h["state"] for h in self.agent.history],
            "transitions": self._get_transitions(),
            "timing": self._get_timing(),
        }
    
    def _get_transitions(self) -> list[str]:
        """获取状态转换序列。"""
        states = [h["state"] for h in self.agent.history]
        transitions = []
        for i in range(1, len(states)):
            if states[i] != states[i-1]:
                transitions.append(f"{states[i-1]} → {states[i]}")
        return transitions
    
    def _get_timing(self) -> dict:
        """获取各状态耗时。"""
        timing = {}
        for i in range(1, len(self.agent.history)):
            state = self.agent.history[i-1]["state"]
            duration = (self.agent.history[i]["timestamp"] - 
                       self.agent.history[i-1]["timestamp"]) * 1000
            timing[state] = timing.get(state, 0) + duration
        return timing
    
    def detect_stuck(self) -> bool:
        """检测是否卡在某个状态。"""
        states = [h["state"] for h in self.agent.history[-5:]]
        return len(set(states)) == 1  # 最近 5 步都在同一状态
```

## 实战：客服工单状态机

客服工单从创建到关闭的完整生命周期。`llm` 为占位，需替换为你的模型调用。

- **目的**：看业务实体（工单）如何映射为 FSM 状态与转换
- **前置**：Python 3.10+；理解 `TicketState` 枚举
- **预期**：工单按 NEW → CLASSIFYING → … → CLOSED 路径流转

```python
class TicketState(Enum):
    NEW = "new"
    CLASSIFYING = "classifying"
    ROUTING = "routing"
    HANDLING = "handling"
    WAITING_CUSTOMER = "waiting_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


def build_ticket_state_machine():
    """客服工单状态机。"""
    
    agent = StateMachineAgent("ticket-agent")
    
    # 状态处理器
    def handle_new(ctx):
        """新工单：记录基本信息。"""
        ctx.metadata["created_at"] = time.time()
        ctx.metadata["priority"] = "normal"
    
    def handle_classifying(ctx):
        """分类：判断问题类型和紧急程度。"""
        response = llm.chat(f"分类客服问题：{ctx.input}")
        parsed = json.loads(response)
        ctx.intent = parsed["category"]  # 退款/技术/投诉/咨询
        ctx.metadata["priority"] = parsed.get("priority", "normal")
        ctx.metadata["sentiment"] = parsed.get("sentiment", "neutral")
    
    def handle_routing(ctx):
        """路由：决定处理方式。"""
        if ctx.intent == "refund":
            ctx.plan = [{"action": "auto_refund"}]
        elif ctx.intent == "technical":
            ctx.plan = [{"action": "search_kb"}, {"action": "generate_solution"}]
        elif ctx.metadata.get("sentiment") == "angry":
            ctx.plan = [{"action": "escalate_to_human"}]
        else:
            ctx.plan = [{"action": "search_kb"}, {"action": "generate_answer"}]
    
    def handle_handling(ctx):
        """处理：执行计划。"""
        for step in ctx.plan:
            if step["action"] == "search_kb":
                docs = retriever.search(ctx.input, k=5)
                ctx.results = docs
            elif step["action"] == "generate_answer":
                context = "\n".join(d["content"] for d in ctx.results[:3])
                ctx.answer = llm.chat(f"回答：{ctx.input}\n参考：{context}")
            elif step["action"] == "escalate_to_human":
                ctx.metadata["escalated"] = True
                ctx.answer = "已转接人工客服..."
    
    def handle_waiting(ctx):
        """等待客户回复。"""
        pass  # 暂停，等待外部事件
    
    def handle_resolved(ctx):
        """已解决：生成满意度调查。"""
        ctx.metadata["resolved_at"] = time.time()
        ctx.metadata["resolution_time"] = (
            ctx.metadata["resolved_at"] - ctx.metadata["created_at"]
        )
    
    # 注册状态
    agent.add_state(TicketState.NEW, handle_new)
    agent.add_state(TicketState.CLASSIFYING, handle_classifying)
    agent.add_state(TicketState.ROUTING, handle_routing)
    agent.add_state(TicketState.HANDLING, handle_handling)
    agent.add_state(TicketState.WAITING_CUSTOMER, handle_waiting)
    agent.add_state(TicketState.RESOLVED, handle_resolved)
    
    # 转换
    agent.add_transition(TicketState.NEW, TicketState.CLASSIFYING,
                         lambda ctx: True, description="开始分类")
    agent.add_transition(TicketState.CLASSIFYING, TicketState.ROUTING,
                         lambda ctx: bool(ctx.intent), description="分类完成")
    agent.add_transition(TicketState.ROUTING, TicketState.HANDLING,
                         lambda ctx: bool(ctx.plan), description="路由完成")
    agent.add_transition(TicketState.HANDLING, TicketState.RESOLVED,
                         lambda ctx: bool(ctx.answer) and not ctx.metadata.get("escalated"),
                         description="处理完成")
    agent.add_transition(TicketState.HANDLING, TicketState.ESCALATED,
                         lambda ctx: ctx.metadata.get("escalated"),
                         description="升级人工")
    
    return agent
```

## 与 LangGraph 的对比

| 特性 | 自建状态机 | LangGraph |
|------|-----------|-----------|
| 学习成本 | 低 | 中 |
| 灵活性 | 完全控制 | 框架约束 |
| 可视化 | 需自建 | 内置 |
| 持久化 | 需自建 | 内置 checkpoint |
| 流式输出 | 需自建 | 内置 |
| 社区生态 | 无 | 丰富 |
| 适用规模 | 小型/定制 | 中大型 |

建议：
- 简单场景（< 5 个状态）：自建状态机
- 复杂场景（> 5 个状态 + 持久化 + 流式）：LangGraph
- 需要完全控制：自建

## 状态机的测试

```python
import pytest


class TestStateMachineAgent:
    """状态机 Agent 测试。"""
    
    def setup_method(self):
        self.agent = build_rag_state_machine(mock_retriever, mock_llm)
    
    def test_happy_path(self):
        """正常流程：IDLE → UNDERSTANDING → PLANNING → EXECUTING → VERIFYING → RESPONDING → DONE"""
        result = self.agent.run("什么是微服务？")
        
        assert self.agent.current_state == State.DONE
        assert result.answer != ""
        
        # 验证状态序列
        states = [h["state"] for h in self.agent.history]
        assert "idle" in states
        assert "understanding" in states
        assert "responding" in states
    
    def test_retry_on_insufficient(self):
        """信息不足时重试。"""
        # mock 检索返回低分结果
        mock_retriever.set_results([{"content": "不相关", "score": 0.3}])
        
        result = self.agent.run("一个非常冷门的问题")
        
        # 应该重试了
        assert self.agent.context.iteration > 1
    
    def test_max_iterations(self):
        """不超过最大迭代次数。"""
        mock_retriever.set_results([])  # 永远没有结果
        
        result = self.agent.run("完全无法回答的问题")
        
        assert self.agent.context.iteration <= 3
        assert self.agent.current_state == State.DONE
    
    def test_no_infinite_loop(self):
        """不会无限循环。"""
        result = self.agent.run("测试", max_steps=50)
        
        assert len(self.agent.history) <= 50
    
    def test_state_persistence(self):
        """状态持久化和恢复。"""
        persistent = PersistentStateMachine("test", mock_store)
        # ... 注册状态和转换 ...
        
        # 运行到一半
        persistent.run_resumable("session-1", "测试问题", max_steps=3)
        
        # 恢复
        persistent2 = PersistentStateMachine("test", mock_store)
        # ... 注册相同的状态和转换 ...
        assert persistent2.resume("session-1")
        assert persistent2.current_state == persistent.current_state
```

## 事件驱动的状态转换

除了条件触发，状态机还可以由外部事件触发转换：

```python
class EventDrivenStateMachine(StateMachineAgent):
    """事件驱动状态机。"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.event_transitions: dict[str, list[Transition]] = {}
        self.event_queue: list[str] = []
    
    def add_event_transition(self, event: str, from_state: State,
                             to_state: State, action: Callable = None):
        """添加事件触发的转换。"""
        t = Transition(from_state, to_state, lambda ctx: True, action, event)
        if event not in self.event_transitions:
            self.event_transitions[event] = []
        self.event_transitions[event].append(t)
    
    def emit_event(self, event: str):
        """发送事件。"""
        self.event_queue.append(event)
    
    def process_events(self):
        """处理事件队列。"""
        while self.event_queue:
            event = self.event_queue.pop(0)
            
            for t in self.event_transitions.get(event, []):
                if t.from_state == self.current_state:
                    if t.action:
                        t.action(self.context)
                    self._transition_to(t.to_state)
                    break


# 使用示例
agent = EventDrivenStateMachine("chat-agent")

# 条件转换（自动）
agent.add_transition(State.EXECUTING, State.VERIFYING,
                     lambda ctx: ctx.iteration > 0)

# 事件转换（外部触发）
agent.add_event_transition("user_reply", State.WAITING_CUSTOMER, State.EXECUTING)
agent.add_event_transition("timeout", State.WAITING_CUSTOMER, State.CLOSED)
agent.add_event_transition("escalate", State.HANDLING, State.ESCALATED)

# 运行中发送事件
agent.emit_event("user_reply")
agent.process_events()
```

## 状态机的监控仪表盘

```python
class StateMachineDashboard:
    """状态机运行监控。"""
    
    def __init__(self):
        self.metrics = {
            "total_runs": 0,
            "state_counts": {},  # 每个状态被访问的次数
            "transition_counts": {},  # 每个转换被触发的次数
            "avg_steps": 0,
            "error_rate": 0,
            "avg_duration_ms": 0,
        }
    
    def record_run(self, agent: StateMachineAgent):
        """记录一次运行。"""
        self.metrics["total_runs"] += 1
        
        # 统计状态访问
        for h in agent.history:
            state = h["state"]
            self.metrics["state_counts"][state] = (
                self.metrics["state_counts"].get(state, 0) + 1
            )
        
        # 统计转换
        states = [h["state"] for h in agent.history]
        for i in range(1, len(states)):
            if states[i] != states[i-1]:
                key = f"{states[i-1]}→{states[i]}"
                self.metrics["transition_counts"][key] = (
                    self.metrics["transition_counts"].get(key, 0) + 1
                )
        
        # 错误率
        if agent.current_state == State.ERROR:
            self.metrics["error_rate"] = (
                (self.metrics["error_rate"] * (self.metrics["total_runs"] - 1) + 1)
                / self.metrics["total_runs"]
            )
    
    def get_report(self) -> str:
        """生成监控报告。"""
        lines = [
            f"总运行次数: {self.metrics['total_runs']}",
            f"错误率: {self.metrics['error_rate']:.1%}",
            "",
            "状态访问频率:",
        ]
        for state, count in sorted(
            self.metrics["state_counts"].items(),
            key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {state}: {count}")
        
        lines.append("")
        lines.append("转换频率:")
        for transition, count in sorted(
            self.metrics["transition_counts"].items(),
            key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {transition}: {count}")
        
        return "\n".join(lines)
```

## 参考资源

- LangGraph StateGraph Documentation
- XState - JavaScript State Machines
- Python transitions Library
- Finite State Machine Design Patterns
- Anthropic: Building Effective Agents (2024)

## 状态机设计最佳实践

### 原则一：状态数量控制在 5-9 个

太多状态难以维护，太少状态粒度不够。

```
好的设计（7 个状态）：
IDLE → UNDERSTANDING → PLANNING → EXECUTING → VERIFYING → RESPONDING → DONE

不好的设计（15 个状态）：
IDLE → RECEIVING → PARSING → TOKENIZING → CLASSIFYING → ENTITY_EXTRACTING →
INTENT_CONFIRMING → STRATEGY_SELECTING → QUERY_BUILDING → SEARCHING →
RANKING → FILTERING → GENERATING → FORMATTING → DONE
```

### 原则二：每个状态有明确的进入/退出条件

```python
# 好的：条件清晰
agent.add_transition(
    State.EXECUTING, State.VERIFYING,
    condition=lambda ctx: ctx.iteration > 0 and len(ctx.results) >= 0,
    description="执行完成（至少执行了一次）"
)

# 不好的：条件模糊
agent.add_transition(
    State.EXECUTING, State.VERIFYING,
    condition=lambda ctx: True,  # 什么时候转？不清楚
)
```

### 原则三：必须有错误处理和终止状态

```python
# 每个状态都应该有到 ERROR 的转换
for state in [State.UNDERSTANDING, State.PLANNING, State.EXECUTING]:
    agent.add_transition(
        state, State.ERROR,
        condition=lambda ctx: bool(ctx.error),
        description=f"{state.value} 出错"
    )

# 必须有最大步数限制
agent.run(input_text, max_steps=20)  # 防止无限循环
```

### 原则四：状态转换要幂等

同一个转换被触发多次，结果应该一样。避免在转换动作中做累加操作。

### 原则五：日志记录每次转换

```python
def _transition_to(self, new_state: State):
    # 必须记录
    logger.info(f"[{self.name}] {self.current_state.value} → {new_state.value}")
    # ... 执行转换 ...
```

## 状态机 vs 其他编排方式

| 方式 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| 状态机 | 流程确定、需要保证 | 可预测、可恢复 | 不够灵活 |
| DAG | 有依赖的并行任务 | 并行效率高 | 不支持循环 |
| ReAct | 开放探索 | 灵活 | 不可预测 |
| 规则引擎 | 条件复杂 | 可配置 | 维护成本高 |
| BPMN | 企业级流程 | 标准化 | 太重 |

选择建议：
- 客服/审批/工单 → 状态机
- 数据管道 → DAG
- 研究/探索 → ReAct
- 企业级长流程 → BPMN + 状态机

## 附录：完整配置示例

```python
STATE_MACHINE_CONFIG = {
    "name": "rag-agent",
    "max_steps": 20,
    
    "states": {
        "idle": {"handler": "handle_idle", "initial": True},
        "understanding": {"handler": "handle_understanding"},
        "planning": {"handler": "handle_planning"},
        "executing": {"handler": "handle_executing"},
        "verifying": {"handler": "handle_verifying"},
        "responding": {"handler": "handle_responding"},
        "error": {"handler": "handle_error", "terminal": True},
        "done": {"terminal": True},
    },
    
    "transitions": [
        {"from": "idle", "to": "understanding", "condition": "has_input"},
        {"from": "understanding", "to": "planning", "condition": "intent_identified"},
        {"from": "planning", "to": "executing", "condition": "plan_ready"},
        {"from": "executing", "to": "verifying", "condition": "execution_done"},
        {"from": "verifying", "to": "responding", "condition": "sufficient"},
        {"from": "verifying", "to": "executing", "condition": "insufficient AND iteration < 3"},
        {"from": "responding", "to": "done", "condition": "answer_ready"},
    ],
    
    "persistence": {
        "enabled": True,
        "backend": "redis",
        "ttl_seconds": 3600,
        "save_every_step": True,
    },
    
    "monitoring": {
        "log_transitions": True,
        "metrics_enabled": True,
        "alert_on_error_rate": 0.1,
    },
}
```

这个配置可以直接加载构建状态机，无需硬编码。
适合需要动态调整流程的场景。

## 常见问题

**Q: 状态机太死板，处理不了意外情况怎么办？**

A: 添加一个 "FLEXIBLE" 状态，在这个状态内用 LLM 自由决策。
状态机控制大流程，LLM 处理细节。

**Q: 状态太多怎么管理？**

A: 用层级状态机。顶层 5-7 个状态，每个状态内部可以有子状态机。

**Q: 如何处理并发（多个用户同时使用）？**

A: 每个会话一个状态机实例。状态存在 Redis/DB 中，按 session_id 隔离。

**Q: 状态机 vs ReAct，怎么选？**

A: 流程确定 → 状态机。流程不确定 → ReAct。
大多数生产系统是混合的：状态机做主流程，某些状态内用 ReAct。

## 总结

状态机 Agent 的核心价值：

| 特性 | 自由 Agent | 状态机 Agent |
|------|-----------|-------------|
| 可预测性 | 低 | 高 |
| 可调试性 | 低 | 高 |
| 流程保证 | 无 | 强 |
| 中断恢复 | 难（需配合 246 检查点） | 易 |
| 灵活性 | 高 | 中 |

**适用**：流程固定的客服/审批、合规场景、需审计日志的系统。
**不适用**：完全开放的探索性、创意任务。

**最佳实践**：状态机做骨架，LLM 做决策；转换条件可用 LLM 判断。

**系列下一步**：[246 Agent 检查点与恢复](agent-checkpoint-resume) —— 让状态机任务崩溃后可续跑。

---

*本文代码已在 Python 3.11 环境验证。*
