---
title: "事件驱动 Agent 架构：事件总线与 Event Sourcing"
slug: agent-event-driven-architecture
date: 2025-06-12
tags: [AI, Agent, 事件驱动, Event Sourcing, 架构]
category: ai-ml
description: "用事件总线解耦 Agent 组件：发布/订阅、事件溯源重建状态、幂等与死信——替代轮询式单体循环。"
---

> **系列导读**：[agent-rag-series-238-254](agent-rag-series-238-254) | **体系化正文**：[`249.agent-event-driven-architecture-tutorial.md`](../../../docs/249.agent-event-driven-architecture-tutorial.md)

## 学习目标

读完本篇，你能：

1. 解释**事件驱动**与 **248 后台任务**、轮询 `while sleep` 的分工差异
2. 实现内存版 `EventBus`：订阅、发布、历史记录
3. 用 **Event Sourcing**（事件溯源）从事件流重建任务状态
4. 跑通 §最小可运行示例（纯 Python + asyncio，无需 Kafka）

## 前置阅读

- **248 后台任务**：`task_id`、Worker、进度推送——本篇关注**组件之间如何通信**
- **246 检查点**：手动快照 vs 本篇「事件流即历史」

## 环境要求

```bash
pip install pydantic   # 可选，工程版事件模型用
```

- Python **3.10+**
- 标准库 `asyncio` 即可跑通示例

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 内存事件总线、领域事件、溯源重建 | Kafka/Pulsar 集群运维 |
| 幂等消费、死信、Outbox 思路 | Temporal 编排细节 → **247** |
| Agent 生命周期事件清单 | Part 7 业务 Agent → **250** |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | `demo_basic_event_bus()` 控制台输出 |
| 2 | §事件溯源 | `TaskAggregate.rebuild()` 打印 `completed` |
| 3 | §与 248 对照 | 能画「API → 事件 → 多订阅者」图 |
| 4 | 教程正文 | 生产级总线、Outbox、完整 Agent 编排 |

## 为什么不用轮询

**事件驱动**（Event-Driven）：状态变化以**不可变事件**发布，订阅者异步处理。
通俗说：像公司群发通知——发一次，各部门自己响应，不用每隔 1 秒问「有没有新任务」。

```text
轮询：
  while True:
      tasks = db.query("pending")
      process(tasks)
      sleep(1)    # 延迟 + 空转查询

事件驱动：
  TaskSubmitted → [分配 Worker] [写审计] [通知用户]
  ToolCompleted → [更新状态] [触发下一步]
```

| 维度 | 轮询 | 事件驱动（本篇） |
|------|------|------------------|
| 发现新任务延迟 | 取决于 sleep 间隔 | 发布即触发（毫秒级） |
| 扩展新逻辑 | 改主循环 | 加订阅者，不改发布方 |
| 审计追溯 | 需额外打日志 | 事件流即历史 |
| 起步复杂度 | 低 | 中（需总线 + Schema） |

## 最小可运行示例

**演示什么：** 内存 `EventBus` 发布 `task_created` / `task_completed`，两个订阅者分别打日志和更新状态。
**环境：** Python 3.10+，无第三方依赖。
**预期：** 与下方「运行结果」一致。

将下列代码保存为 `demo_event_bus.py` 后执行 `python demo_event_bus.py`。

```python
"""demo_event_bus.py — 249 事件总线最小示例"""
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable
from collections import defaultdict


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    timestamp: str
    payload: dict = field(default_factory=dict)

    @staticmethod
    def create(event_type: str, payload: dict) -> "Event":
        return Event(
            event_id=uuid.uuid4().hex[:12],
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._history: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        for handler in self._handlers.get(event.event_type, []):
            try:
                await handler(event)
            except Exception as exc:
                print(f"  [ERROR] {event.event_type}: {exc}")

    @property
    def history(self) -> list[Event]:
        return list(self._history)


async def main() -> None:
    bus = EventBus()

    async def log_handler(event: Event) -> None:
        print(f"  [LOG] {event.event_type}: {event.payload}")

    async def state_handler(event: Event) -> None:
        if event.event_type == "task_completed":
            print(f"  [STATE] 任务 {event.payload['task_id']} 完成")

    bus.subscribe("task_created", log_handler)
    bus.subscribe("task_completed", log_handler)
    bus.subscribe("task_completed", state_handler)

    await bus.publish(Event.create("task_created", {"task_id": "T-001", "query": "分析数据"}))
    await bus.publish(Event.create("task_completed", {"task_id": "T-001", "result": "摘要..."}))
    print(f"\n  事件历史: {len(bus.history)} 条")


if __name__ == "__main__":
    asyncio.run(main())
```

### 运行结果

```text
  [LOG] task_created: {'task_id': 'T-001', 'query': '分析数据'}
  [LOG] task_completed: {'task_id': 'T-001', 'result': '摘要...'}
  [STATE] 任务 T-001 完成

  事件历史: 2 条
```

对照输出：`task_completed` 触发**两个**订阅者——发布方不必知道谁在监听。

## 事件溯源：用历史重建状态

**Event Sourcing**（事件溯源）：不直接覆盖状态字段，而是追加事件，需要时**重放**事件得到当前状态。
通俗说：账本只记流水，余额靠加总流水算出来。

下面演示 `TaskAggregate`：收到 `task.progress` / `task.completed` 后更新 `state` 与 `current_step`。

```python
from dataclasses import dataclass, field


@dataclass
class TaskAggregate:
    task_id: str
    state: str = "pending"
    current_step: int = 0
    total_steps: int = 0
    result: str = ""

    def apply(self, event: Event) -> None:
        t, p = event.event_type, event.payload
        if t == "task.submitted":
            self.total_steps = p.get("total_steps", 0)
            self.state = "pending"
        elif t == "task.started":
            self.state = "running"
        elif t == "task.progress":
            self.current_step = p.get("step", self.current_step)
        elif t == "task.completed":
            self.state = "completed"
            self.result = p.get("result", "")
            self.current_step = self.total_steps

    @classmethod
    def rebuild(cls, task_id: str, events: list[Event]) -> "TaskAggregate":
        agg = cls(task_id=task_id)
        for ev in events:
            if ev.payload.get("task_id", task_id) == task_id or "task_id" not in ev.payload:
                agg.apply(ev)
        return agg


async def demo_event_sourcing() -> None:
    bus = EventBus()
    task_id = "TASK-ES-001"
    for et, payload in [
        ("task.submitted", {"task_id": task_id, "total_steps": 4}),
        ("task.started", {"task_id": task_id}),
        ("task.progress", {"task_id": task_id, "step": 2}),
        ("task.completed", {"task_id": task_id, "result": "Q3 增长 15%"}),
    ]:
        await bus.publish(Event.create(et, payload))
    agg = TaskAggregate.rebuild(task_id, bus.history)
    print(f"  重建结果: state={agg.state}, step={agg.current_step}/{agg.total_steps}")


# asyncio.run(demo_event_sourcing())
# → 重建结果: state=completed, step=4/4
```

## Agent 典型领域事件

```text
生命周期：TaskSubmitted → TaskAssigned → TaskStarted → TaskProgressed → TaskCompleted
工具链：  ToolCallRequested → ToolCallSucceeded / ToolCallFailed
审批：    ApprovalRequested → ApprovalGranted / ApprovalDenied
```

发布方只关心「发生了什么」；索引、通知、计费、审计各自订阅，互不改代码。

## 与 248 后台任务如何配合

```text
248：用户 POST /tasks → 立即返回 task_id → Worker 执行 → WebSocket 推进度
249：Worker 内每一步 publish 事件 → 审计/指标/下游系统订阅

组合：
  API 层（248）负责「接单 + 查询状态」
  事件层（249）负责「系统内解耦 + 可追溯」
```

## 生产注意事项（摘要）

1. **幂等**：用 `event_id` 或业务键去重，防止重投重复消费。
2. **顺序**：同一 `aggregate_id`（如 `task_id`）的事件须有序；可用分区键。
3. **Outbox**：业务写库与写事件在同一事务，再异步投递到总线，避免「库写了、事件丢了」。
4. **死信队列**：处理失败 N 次后转入 DLQ，人工或脚本修复。

完整 `ProductionEventBus`、中间件与 Outbox 代码见教程正文 §工程化版本。

## 常见陷阱

| 陷阱 | 后果 | 对策 |
|------|------|------|
| 事件无 Schema 版本 | 消费者解析失败 | `event_type` + `schema_version` 字段 |
| 在事件里塞巨大 payload | 总线膨胀 | 存对象存储，事件只带 URL/id |
| 订阅者抛错拖垮发布 | 级联失败 | 隔离 try/except + 死信 |
| 与 248 进度混为一谈 | 职责混乱 | 进度给用户看，事件给系统用 |

## 常见问题

**Q: 小项目也要上 Kafka 吗？**

A: 不必。教学与 MVP 用内存总线或 Redis Stream；流量上来再迁 Kafka/Pulsar。

**Q: Event Sourcing 和 246 Checkpoint 冲突吗？**

A: 不冲突。Checkpoint 可以是「快照」；事件流是完整历史。常见做法：平时重放事件，定期快照加速恢复。

**Q: 和 Temporal 的关系？**

A: Temporal 内部也是事件溯源思想；本篇教你**自己设计领域事件**；247 教你用平台托管长流程。

## 系列下一步

- **250 知识库 Agent**：Part 7 起点，[`examples/agent-platform/`](../../../examples/agent-platform/) + [`250-build-knowledge-base-agent`](250-build-knowledge-base-agent)
- **体系化 + 面试**：[`249.agent-event-driven-architecture-tutorial.md`](../../../docs/249.agent-event-driven-architecture-tutorial.md)

---

*示例已在 Python 3.11 验证。生产落地请阅读教程 §生产环境注意事项。*
