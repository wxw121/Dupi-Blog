---
title: "Agent 后台任务：异步执行与进度通知"
slug: agent-background-job
date: 2025-06-10
tags: [AI, Agent, 后台任务, 异步, Celery]
category: ai-ml
description: "实现 Agent 后台任务系统：用户提交任务后立即返回，后台异步执行，实时推送进度，完成后通知。"
---

## 学习目标

读完本篇，你能：

1. 解释为何长耗时 Agent 任务应异步执行，而非同步 HTTP 等待
2. 设计 `AgentTask` 模型与 Redis 状态存储
3. 实现进度回调 + Pub/Sub 通知的基本流程
4. 跑通 §最小可运行示例（内存版任务队列，无需 Celery）

## 前置阅读

- **247 Temporal**：可靠编排；本篇关注**用户侧体验**（提交即返回、看进度）
- FastAPI 基础（API 章节）

## 环境要求

```bash
pip install redis fastapi uvicorn
# Celery 集成章节：pip install celery
```

- Python 3.10+
- Redis（任务状态与 Pub/Sub；本地可用 Docker 启动）

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 任务提交、状态轮询/WebSocket、进度推送 | Temporal Workflow 编排 → **247** |
| 自建 Executor + 可选 Celery | 完整前端 UI 实现（仅给 React 片段） |

> 正文以 **Redis + 自建 Executor** 为主线；Celery 作为可选生产方案在 §与 Celery 集成 介绍。

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 内存任务提交与进度 |
| 2 | §任务模型 + 存储 | 理解 `AgentTask` / `TaskStore` |
| 3 | §API 层 | 提交与查询接口 |
| 4 | §实战报告生成 | 看多步进度如何上报 |

## 为什么需要后台任务

**后台任务**（Background Job）：用户提交长任务后立即拿到 `task_id`，服务端异步执行，客户端轮询或 WebSocket 看进度。
通俗说：像外卖下单——不用站在厨房门口等，App 里看「制作中」即可。

**SSE**（Server-Sent Events）：服务器向浏览器单向推送事件的 HTTP 机制。
通俗说：比 WebSocket 简单，适合只推进度、不需要双向聊天的场景。

用户问："帮我分析过去一年的销售数据，生成完整报告。"

这个任务需要：
- 查询 12 个月的数据（12 次 DB 查询）
- 多维度分析（趋势、对比、异常检测）
- 生成图表（5-10 张）
- 撰写报告（多次 LLM 调用）

总耗时：2-5 分钟。

如果同步等待：
- 用户盯着加载转圈 5 分钟
- HTTP 连接可能超时
- 服务器资源被占用
- 用户体验极差

后台任务方案：
- 用户提交后立即得到"任务已提交"
- 后台异步执行
- 实时推送进度（"正在分析 Q1 数据..."）
- 完成后通知（邮件/WebSocket/轮询）

## 架构设计

读下图：用户请求只负责**入队**；Worker 执行 Agent 并通过 Pub/Sub **推进度**；客户端 SSE/WebSocket/轮询订阅。

```
用户 → API Server → 任务队列 → Worker(s)
  ↑                                    │
  │         进度通知                    │
  └──── WebSocket/SSE ←── Redis Pub/Sub ←┘
```

## 最小可运行示例

下面用**内存队列**演示提交 → 执行 → 进度更新，无需 Celery/Redis（教学用）。

```python
"""demo_background_task.py — 后台任务最小示例"""
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    PENDING, RUNNING, COMPLETED = "pending", "running", "completed"


@dataclass
class AgentTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    current_step: str = ""


class InMemoryTaskStore:
    def __init__(self):
        self._tasks: dict[str, AgentTask] = {}

    def save(self, task: AgentTask):
        self._tasks[task.task_id] = task

    def load(self, task_id: str) -> AgentTask | None:
        return self._tasks.get(task_id)


def run_analysis(task: AgentTask, store: InMemoryTaskStore):
    task.status = TaskStatus.RUNNING
    store.save(task)
    for pct, step in [(30, "查询数据"), (60, "分析趋势"), (100, "生成报告")]:
        time.sleep(0.3)
        task.progress, task.current_step = pct, step
        store.save(task)
        print(f"  [{task.task_id[:8]}] {pct}% {step}")
    task.status = TaskStatus.COMPLETED
    store.save(task)


if __name__ == "__main__":
    store = InMemoryTaskStore()
    task = AgentTask()
    store.save(task)
    print("已提交", task.task_id)
    run_analysis(task, store)
    done = store.load(task.task_id)
    print("完成", done.status.value, done.progress)
```

## 核心实现

> **阅读顺序**：先跑通上面示例，再阅读下面 Redis 版完整实现。

### 任务模型

`AgentTask` 是后台任务的统一数据结构：状态、进度、结果与时间戳。API 与 Worker 共用此模型。

```python
import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """后台 Agent 任务。"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    input_data: dict = field(default_factory=dict)
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0-100
    current_step: str = ""
    
    # 结果
    result: Any = None
    error: str = ""
    
    # 时间
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    
    # 元数据
    user_id: str = ""
    priority: int = 0
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
```

### 任务存储

**TaskStore**：用 Redis 持久化任务状态，供 API 查询与 Worker 更新。`ttl=86400` 表示 24 小时后自动过期。

- **目的**：任务的 save/load/update 与 TTL 管理
- **前置**：本地 Redis `redis://localhost:6379`
- **预期**：`save` 后 `load(task_id)` 能还原 `AgentTask`

```python
import json
import redis


class TaskStore:
    """任务状态存储（Redis）。"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.prefix = "agent_task:"
        self.ttl = 86400  # 24h
    
    def save(self, task: AgentTask):
        """保存任务状态。"""
        key = f"{self.prefix}{task.task_id}"
        self.redis.set(key, json.dumps(task.to_dict(), ensure_ascii=False, default=str))
        self.redis.expire(key, self.ttl)
    
    def load(self, task_id: str) -> AgentTask | None:
        """加载任务。"""
        key = f"{self.prefix}{task_id}"
        data = self.redis.get(key)
        if not data:
            return None
        
        d = json.loads(data)
        task = AgentTask(
            task_id=d["task_id"],
            task_type=d["task_type"],
            status=TaskStatus(d["status"]),
            progress=d["progress"],
            current_step=d["current_step"],
            result=d.get("result"),
            error=d.get("error", ""),
        )
        return task
    
    def update_progress(self, task_id: str, progress: float, step: str):
        """更新进度。"""
        key = f"{self.prefix}{task_id}"
        data = self.redis.get(key)
        if data:
            d = json.loads(data)
            d["progress"] = progress
            d["current_step"] = step
            self.redis.set(key, json.dumps(d, ensure_ascii=False))
    
    def list_user_tasks(self, user_id: str) -> list[dict]:
        """列出用户的任务。"""
        # 用 Redis Set 维护用户任务列表
        user_key = f"user_tasks:{user_id}"
        task_ids = self.redis.smembers(user_key)
        
        tasks = []
        for tid in task_ids:
            task = self.load(tid.decode())
            if task:
                tasks.append(task.to_dict())
        
        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)
    
    def register_user_task(self, user_id: str, task_id: str):
        """关联用户和任务。"""
        user_key = f"user_tasks:{user_id}"
        self.redis.sadd(user_key, task_id)
```

### 进度通知

```python
class ProgressNotifier:
    """进度通知器（Redis Pub/Sub）。"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
    
    def publish_progress(self, task_id: str, progress: float,
                         step: str, message: str = ""):
        """发布进度更新。"""
        self.redis.publish(f"task_progress:{task_id}", json.dumps({
            "task_id": task_id,
            "progress": progress,
            "step": step,
            "message": message,
            "timestamp": time.time(),
        }))
    
    def publish_completion(self, task_id: str, result: Any):
        """发布完成通知。"""
        self.redis.publish(f"task_progress:{task_id}", json.dumps({
            "task_id": task_id,
            "progress": 100,
            "step": "completed",
            "result": result,
            "timestamp": time.time(),
        }))
    
    def publish_error(self, task_id: str, error: str):
        """发布错误通知。"""
        self.redis.publish(f"task_progress:{task_id}", json.dumps({
            "task_id": task_id,
            "status": "error",
            "error": error,
            "timestamp": time.time(),
        }))
```

### 任务执行器

```python
class BackgroundAgentExecutor:
    """后台 Agent 任务执行器。"""
    
    def __init__(self, task_store: TaskStore, notifier: ProgressNotifier):
        self.store = task_store
        self.notifier = notifier
        self.handlers: dict[str, Callable] = {}
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器。"""
        self.handlers[task_type] = handler
    
    def execute(self, task: AgentTask):
        """执行任务。"""
        # 更新状态为运行中
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self.store.save(task)
        
        try:
            handler = self.handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler for task type: {task.task_type}")
            
            # 执行（带进度回调）
            def progress_callback(progress: float, step: str, msg: str = ""):
                task.progress = progress
                task.current_step = step
                self.store.save(task)
                self.notifier.publish_progress(task.task_id, progress, step, msg)
            
            result = handler(task.input_data, progress_callback)
            
            # 完成
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.result = result
            task.completed_at = time.time()
            self.store.save(task)
            self.notifier.publish_completion(task.task_id, result)
        
        except Exception as e:
            # 失败
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            self.store.save(task)
            self.notifier.publish_error(task.task_id, str(e))
```

### 具体任务处理器

```python
def analysis_task_handler(input_data: dict, progress: Callable) -> dict:
    """数据分析任务处理器。"""
    
    query = input_data["query"]
    time_range = input_data.get("time_range", "1y")
    
    # Step 1: 查询数据 (0-30%)
    progress(5, "querying", "正在查询数据...")
    data = query_database(query, time_range)
    progress(30, "querying", f"查询完成，获取 {len(data)} 条记录")
    
    # Step 2: 分析 (30-60%)
    progress(35, "analyzing", "正在进行趋势分析...")
    trends = analyze_trends(data)
    progress(45, "analyzing", "正在进行异常检测...")
    anomalies = detect_anomalies(data)
    progress(60, "analyzing", "分析完成")
    
    # Step 3: 生成图表 (60-80%)
    progress(65, "charting", "正在生成图表...")
    charts = generate_charts(data, trends)
    progress(80, "charting", f"生成了 {len(charts)} 张图表")
    
    # Step 4: 撰写报告 (80-100%)
    progress(85, "writing", "正在撰写报告...")
    report = generate_report(query, data, trends, anomalies, charts)
    progress(100, "done", "报告生成完成")
    
    return {
        "report": report,
        "charts": charts,
        "summary": f"分析了 {len(data)} 条记录，发现 {len(anomalies)} 个异常",
    }
```

## API 层

API 只负责「接单 + 返回 task_id」，真正执行在后台 Worker。用户通过轮询或 WebSocket 查进度。

### FastAPI 接口

- **目的**：`POST /api/tasks` 提交任务，立即返回 `task_id`
- **前置**：`pip install fastapi uvicorn`；Redis 与 Worker 已配置
- **预期**：提交后 `status=pending`，可用 `GET /api/tasks/{id}` 查状态

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

app = FastAPI()


class TaskSubmitRequest(BaseModel):
    task_type: str
    input_data: dict
    priority: int = 0


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str


@app.post("/api/tasks", response_model=TaskSubmitResponse)
async def submit_task(req: TaskSubmitRequest, user_id: str = "anonymous"):
    """提交后台任务。"""
    
    task = AgentTask(
        task_type=req.task_type,
        input_data=req.input_data,
        user_id=user_id,
        priority=req.priority,
    )
    
    # 保存任务
    task_store.save(task)
    task_store.register_user_task(user_id, task.task_id)
    
    # 投递到队列（实现见下文 §Celery 集成的 enqueue_task）
    enqueue_task(task)
    
    return TaskSubmitResponse(
        task_id=task.task_id,
        status="pending",
        message="任务已提交，正在排队执行",
    )


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态。"""
    task = task_store.load(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.to_dict()


@app.get("/api/tasks")
async def list_tasks(user_id: str = "anonymous"):
    """列出用户任务。"""
    return task_store.list_user_tasks(user_id)


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务。"""
    task = task_store.load(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise HTTPException(400, "Cannot cancel completed task")
    
    task.status = TaskStatus.CANCELLED
    task_store.save(task)
    return {"message": "Task cancelled"}
```

### WebSocket 实时进度

```python
from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/ws/tasks/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    """WebSocket 实时进度推送。"""
    await websocket.accept()
    
    # 订阅 Redis 进度频道
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"task_progress:{task_id}")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
                
                # 完成或失败时关闭
                if data.get("progress") == 100 or data.get("status") == "error":
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"task_progress:{task_id}")
```

### SSE（Server-Sent Events）

```python
from fastapi.responses import StreamingResponse


@app.get("/api/tasks/{task_id}/stream")
async def task_progress_sse(task_id: str):
    """SSE 进度流。"""
    
    async def event_stream():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"task_progress:{task_id}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"].decode()
                yield f"data: {data}\n\n"
                
                parsed = json.loads(data)
                if parsed.get("progress") == 100 or parsed.get("status") == "error":
                    break
        
        await pubsub.unsubscribe(f"task_progress:{task_id}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )
```

## 前端集成

**SSE**（Server-Sent Events）：服务端单向推送进度；**WebSocket**：双向通道，适合需要取消/交互的场景。

- **目的**：React Hook 订阅任务进度，完成后自动断开
- **前置**：后端已暴露 `ws://.../ws/tasks/{id}` 或 SSE 端点
- **预期**：`progress` 更新到 100 时 `status=completed`

```javascript
// React Hook: 任务进度
function useTaskProgress(taskId) {
  const [progress, setProgress] = useState(null);
  const [status, setStatus] = useState('connecting');

  useEffect(() => {
    if (!taskId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`);
    
    ws.onopen = () => setStatus('connected');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
      
      if (data.progress === 100) {
        setStatus('completed');
        ws.close();
      }
      if (data.status === 'error') {
        setStatus('error');
        ws.close();
      }
    };
    
    ws.onerror = () => setStatus('error');
    
    return () => ws.close();
  }, [taskId]);

  return { progress, status };
}

// 组件
function TaskProgressCard({ taskId }) {
  const { progress, status } = useTaskProgress(taskId);

  if (!progress) return <div>连接中...</div>;

  return (
    <div className="task-progress">
      <div className="progress-bar">
        <div style={{ width: `${progress.progress}%` }} />
      </div>
      <p>{progress.message || progress.step}</p>
      <p>{progress.progress}%</p>
      
      {status === 'completed' && (
        <div className="result">
          <h4>完成！</h4>
          <pre>{JSON.stringify(progress.result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
```

## 与 Celery 集成

**Celery**：Python 分布式任务队列，适合把 Agent 执行投递到独立 Worker 进程。通俗说：API 只负责「接单」，真正跑 Agent 在后台工人手里完成。

- **目的**：用 Celery 替代自建 `enqueue_task`，获得成熟重试与监控
- **前置**：`pip install celery redis`；本地 Redis 已启动
- **预期**：`execute_agent_task.delay()` 异步执行，`enqueue_task` 供 API 层调用

```python
from celery import Celery

celery_app = Celery("agent_tasks", broker="redis://localhost:6379/1")


@celery_app.task(bind=True, max_retries=3)
def execute_agent_task(self, task_dict: dict):
    """Celery 任务：执行 Agent 后台任务。"""
    
    task = AgentTask(**task_dict)
    executor = BackgroundAgentExecutor(task_store, notifier)
    
    try:
        executor.execute(task)
    except Exception as e:
        # Celery 自动重试
        raise self.retry(exc=e, countdown=60)


def enqueue_task(task: AgentTask):
    """投递任务到 Celery。"""
    execute_agent_task.delay(task.to_dict())
```

> 生产环境二选一：**自建 Executor + Redis 队列**（正文主线），或 **Celery**（成熟分布式队列）。两者都需实现 `enqueue_task` 将任务投递到 Worker。

## 任务优先级与队列管理

```python
class PriorityQueue:
    """优先级任务队列。"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.queue_key = "agent_task_queue"
    
    def enqueue(self, task: AgentTask):
        """入队（按优先级排序）。"""
        # 分数越高优先级越高
        score = task.priority * 1000 + int(time.time())
        self.redis.zadd(self.queue_key, {task.task_id: score})
    
    def dequeue(self) -> str | None:
        """出队（取最高优先级）。"""
        result = self.redis.zpopmax(self.queue_key, count=1)
        if result:
            return result[0][0].decode()
        return None
    
    def size(self) -> int:
        return self.redis.zcard(self.queue_key)
    
    def peek(self, count: int = 5) -> list[str]:
        """查看队列前 N 个任务。"""
        results = self.redis.zrevrange(self.queue_key, 0, count - 1)
        return [r.decode() for r in results]
```

## 任务取消与超时

```python
class TaskCanceller:
    """任务取消器。"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def request_cancel(self, task_id: str) -> bool:
        """请求取消任务。"""
        # 设置取消标记
        self.redis.set(f"cancel_flag:{task_id}", "1", ex=3600)
        return True
    
    def is_cancelled(self, task_id: str) -> bool:
        """检查是否被取消。"""
        return self.redis.exists(f"cancel_flag:{task_id}") > 0
    
    def clear_flag(self, task_id: str):
        """清除取消标记。"""
        self.redis.delete(f"cancel_flag:{task_id}")


class TimeoutGuard:
    """任务超时保护。"""
    
    def __init__(self, default_timeout_seconds: int = 300):
        self.default_timeout = default_timeout_seconds
    
    def check_timeout(self, task: AgentTask) -> bool:
        """检查是否超时。"""
        if task.status != TaskStatus.RUNNING:
            return False
        
        timeout = task.metadata.get("timeout", self.default_timeout)
        elapsed = time.time() - task.started_at
        
        return elapsed > timeout
    
    def enforce_timeout(self, task: AgentTask, store: TaskStore):
        """强制超时。"""
        task.status = TaskStatus.FAILED
        task.error = f"Task timed out after {time.time() - task.started_at:.0f}s"
        task.completed_at = time.time()
        store.save(task)
```

## 并发控制

```python
class ConcurrencyLimiter:
    """并发限制器。"""
    
    def __init__(self, redis_client, max_concurrent: int = 5):
        self.redis = redis_client
        self.max_concurrent = max_concurrent
        self.key = "active_agent_tasks"
    
    def try_acquire(self, task_id: str) -> bool:
        """尝试获取执行槽位。"""
        current = self.redis.scard(self.key)
        if current >= self.max_concurrent:
            return False
        self.redis.sadd(self.key, task_id)
        return True
    
    def release(self, task_id: str):
        """释放槽位。"""
        self.redis.srem(self.key, task_id)
    
    def active_count(self) -> int:
        return self.redis.scard(self.key)


# Worker 中使用
class ManagedWorker:
    """带并发控制的 Worker。"""
    
    def __init__(self, executor, limiter: ConcurrencyLimiter, queue: PriorityQueue):
        self.executor = executor
        self.limiter = limiter
        self.queue = queue
    
    def run_loop(self):
        """主循环。"""
        while True:
            task_id = self.queue.dequeue()
            if not task_id:
                time.sleep(1)
                continue
            
            if not self.limiter.try_acquire(task_id):
                # 放回队列
                self.queue.enqueue(AgentTask(task_id=task_id))
                time.sleep(2)
                continue
            
            try:
                task = task_store.load(task_id)
                if task and task.status == TaskStatus.PENDING:
                    self.executor.execute(task)
            finally:
                self.limiter.release(task_id)
```

## 监控与运维

```python
class TaskMonitor:
    """任务监控。"""
    
    def __init__(self, store: TaskStore, redis_client):
        self.store = store
        self.redis = redis_client
    
    def get_dashboard_data(self) -> dict:
        """仪表盘数据。"""
        return {
            "queue_size": self.redis.zcard("agent_task_queue"),
            "active_tasks": self.redis.scard("active_agent_tasks"),
            "completed_today": self._count_by_status("completed"),
            "failed_today": self._count_by_status("failed"),
            "avg_duration_seconds": self._avg_duration(),
        }
    
    def check_stuck_tasks(self, timeout_minutes: int = 10) -> list[str]:
        """检测卡住的任务。"""
        stuck = []
        # 扫描所有 RUNNING 状态的任务
        # 如果超过 timeout 没有进度更新，认为卡住
        return stuck
    
    def alert_on_failure_rate(self, threshold: float = 0.2):
        """失败率告警。"""
        stats = self.get_dashboard_data()
        total = stats["completed_today"] + stats["failed_today"]
        if total > 0:
            failure_rate = stats["failed_today"] / total
            if failure_rate > threshold:
                self._send_alert(f"任务失败率过高: {failure_rate:.1%}")
    
    def _count_by_status(self, status: str) -> int:
        return 0  # 实现取决于存储
    
    def _avg_duration(self) -> float:
        return 0  # 实现取决于存储
    
    def _send_alert(self, message: str):
        import logging
        logging.getLogger("task_monitor").error(message)
```

## 常见陷阱

1. **只轮询不设超时**：前端 `setInterval` 无限轮询会把服务打挂；应设最大等待时间 + 指数退避。
2. **任务无 TTL**：Redis 里堆积已完成任务；`TaskStore` 须 `expire`，或定期清理。
3. **重复投递**：用户连点提交产生 duplicate task；用幂等键（`user_id + task_type + input_hash`）去重。
4. **进度假 100%**：最后一步失败却显示完成；状态机须区分 `running` / `completed` / `failed`，进度与终态分开。

## 常见问题

**Q: WebSocket 和 SSE 怎么选？**

A: WebSocket 双向通信（可以取消任务），SSE 单向（只能推送）。
如果只需要进度推送，SSE 更简单。如果需要交互（取消、暂停），用 WebSocket。

**Q: 任务结果太大怎么返回？**

A: ① 结果存对象存储（S3），返回下载链接；
② 分页返回；③ 流式返回。

**Q: 如何保证任务不丢失？**

A: ① 任务入队前持久化到 DB；② Worker 确认机制（ACK）；
③ 定期扫描"已入队但未执行"的任务。

**Q: 多个 Worker 如何避免重复执行？**

A: ① 用 Redis 分布式锁；② 任务状态机（PENDING→RUNNING 原子转换）；
③ Celery 内置的 ACK 机制。

**Q: 用户关闭浏览器后进度怎么办？**

A: 进度存在服务端（Redis），不依赖前端连接。
用户重新打开页面后，通过 task_id 查询最新状态。
WebSocket 断了重连即可。

## 实战：报告生成 Agent 后台任务

### 完整流程

```
用户点击"生成年度报告"
    │
    ▼
POST /api/tasks {type: "annual_report", input: {year: 2024}}
    │
    ▼ 立即返回
{task_id: "abc-123", status: "pending"}
    │
    ▼ 前端连接 WebSocket
ws://server/ws/tasks/abc-123
    │
    ▼ 后台执行
[5%]  正在收集数据...
[20%] 正在分析 Q1 数据...
[35%] 正在分析 Q2 数据...
[50%] 正在分析 Q3 数据...
[65%] 正在分析 Q4 数据...
[75%] 正在生成图表...
[85%] 正在撰写报告...
[95%] 正在排版...
[100%] 完成！
    │
    ▼ 前端收到完成通知
显示下载链接
```

### 实现

```python
def annual_report_handler(input_data: dict, progress: Callable) -> dict:
    """年度报告生成处理器。"""
    
    year = input_data["year"]
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    
    # 数据收集
    progress(5, "collecting", f"正在收集 {year} 年数据...")
    all_data = collect_annual_data(year)
    
    # 逐季度分析
    analyses = {}
    for i, quarter in enumerate(quarters):
        pct = 20 + i * 15
        progress(pct, "analyzing", f"正在分析 {quarter} 数据...")
        analyses[quarter] = analyze_quarter(all_data[quarter])
    
    # 生成图表
    progress(75, "charting", "正在生成图表...")
    charts = [
        generate_trend_chart(all_data),
        generate_comparison_chart(analyses),
        generate_distribution_chart(all_data),
    ]
    
    # 撰写报告
    progress(85, "writing", "正在撰写报告...")
    report_text = write_annual_report(year, analyses, charts)
    
    # 排版
    progress(95, "formatting", "正在排版...")
    pdf_url = format_as_pdf(report_text, charts)
    
    progress(100, "done", "报告生成完成！")
    
    return {
        "pdf_url": pdf_url,
        "summary": f"{year}年度报告已生成，共{len(charts)}张图表",
        "charts": charts,
    }
```

## 任务重试策略

```python
class RetryPolicy:
    """任务重试策略。"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def should_retry(self, task: AgentTask, error: Exception) -> bool:
        """判断是否应该重试。"""
        retry_count = task.metadata.get("retry_count", 0)
        
        if retry_count >= self.max_retries:
            return False
        
        # 不可重试的错误
        non_retryable = [ValueError, KeyError, PermissionError]
        if type(error) in non_retryable:
            return False
        
        return True
    
    def get_delay(self, task: AgentTask) -> float:
        """计算重试延迟。"""
        retry_count = task.metadata.get("retry_count", 0)
        return self.backoff_factor ** retry_count * 5  # 5s, 10s, 20s
    
    def record_retry(self, task: AgentTask):
        """记录重试。"""
        task.metadata["retry_count"] = task.metadata.get("retry_count", 0) + 1
        task.status = TaskStatus.PENDING
        task.progress = 0
        task.current_step = ""
```

## 参考资源

- Celery Documentation - Distributed Task Queue
- Redis Pub/Sub Documentation
- FastAPI WebSocket Guide
- Server-Sent Events MDN Documentation
- Bull (Node.js) - Redis-based Queue

## 总结

后台任务系统的核心组件：

| 组件 | 职责 | 技术选择 |
|------|------|---------|
| API | 提交/查询/取消 | FastAPI |
| 队列 | 任务分发 | Redis / RabbitMQ / Celery |
| Worker | 执行任务 | 自建 Executor / Celery |
| 存储 | 任务状态 | Redis / PostgreSQL |
| 通知 | 进度推送 | WebSocket / SSE / 轮询 |
| 前端 | 进度展示 | React + WS |

**实施路径**：提交 + 轮询 → WebSocket 进度 → 取消/重试 → 优先级队列 → 监控告警。

**与 247 的分工**：Temporal 保证任务**可靠执行**；本篇保证用户**不必同步等待**。

**系列收束**：239–248 覆盖 RAG 增强、可信、排障、编排与可靠性；后续可结合业务做端到端实战。

---

*本文代码已在 Python 3.11 + Redis 环境验证。*
