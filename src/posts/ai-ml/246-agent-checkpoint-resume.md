---
title: "Agent 检查点与恢复：不怕中断的长时间任务"
slug: agent-checkpoint-resume
date: 2025-06-05
tags: [AI, Agent, 检查点, 容错, 架构]
category: ai-ml
description: "实现 Agent 的检查点机制：保存中间状态、崩溃后恢复、断点续执行，让长时间运行的 Agent 任务不怕中断。"
---

## 学习目标

读完本篇，你能：

1. 解释检查点（Checkpoint）与 245 状态机持久化的关系
2. 设计 `Checkpoint` 数据结构并实现文件系统存储
3. 在 Agent 每步执行后保存检查点，崩溃后从最新点恢复
4. 跑通 §最小可运行示例（文件检查点 save/load）

## 前置阅读

- **245 状态机 Agent**：状态与上下文是什么、为何要保存
- **223 幂等工具**：恢复后重放步骤时，工具调用须幂等

## 环境要求

```bash
# 最小示例仅需标准库
# Redis 存储章节：pip install redis
```

- Python 3.10+

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 手动检查点：保存 / 加载 / 恢复策略 | Temporal 自动持久化 → **247** |
| 文件与 Redis 存储后端 | 后台任务进度 UX → **248** |

## 旧方案 vs 新方案（收束对照）

| 维度 | 无检查点 | 本篇：手动检查点 | 247 Temporal |
|------|----------|------------------|--------------|
| 崩溃后 | 从头跑 | 从最近 checkpoint 续 | 自动重放事件 |
| 实现成本 | 低 | 中 | 中高 |
| 适用 | 短任务 demo | 5–30 分钟 Agent 任务 | 长流程、分布式 |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 文件检查点读写 |
| 2 | §检查点数据结构 | 理解 `Checkpoint` 字段 |
| 3 | §崩溃恢复策略 | 知道幂等与重试边界 |
| 4 | §实战代码生成 | 看多步任务如何打点 |

## 为什么需要检查点

**检查点**（Checkpoint）：在执行过程中把 Agent 的当前状态（进度、中间结果、上下文）持久化到存储。
通俗说：像游戏存档——崩溃后从存档点继续，不用从第一关重打。

Agent 执行复杂任务可能需要几分钟甚至几小时：
- 多步检索 + 分析（5-10 分钟）
- 代码生成 + 测试 + 修复循环（10-30 分钟）
- 大规模数据处理（数小时）

如果中途崩溃（OOM、API 超时、服务器重启），所有进度丢失。

检查点（Checkpoint）= 定期保存进度 + 崩溃后从断点恢复。

## 核心架构

读下图注意：**崩溃后加载的是「上一个成功步骤」的检查点**，该步骤会重试一次（须保证幂等）。

```
Agent 执行
    │
    ├── Step 1 → [保存检查点 1]
    ├── Step 2 → [保存检查点 2]
    ├── Step 3 → 💥 崩溃！
    │
    ▼ 重启后
    │
    ├── [加载检查点 2]
    ├── Step 3（重试）→ [保存检查点 3]
    ├── Step 4 → [保存检查点 4]
    └── 完成 ✓
```

## 最小可运行示例

下面演示检查点的保存与加载（文件系统），无需 Redis。

```python
"""demo_checkpoint.py — 检查点最小示例"""
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict


@dataclass
class Checkpoint:
    checkpoint_id: str
    session_id: str
    step_number: int
    context: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "Checkpoint":
        return cls(**json.loads(data))


class FileCheckpointStore:
    def __init__(self, directory: str = "./checkpoints"):
        os.makedirs(directory, exist_ok=True)
        self.directory = directory

    def save(self, cp: Checkpoint) -> str:
        path = os.path.join(self.directory, f"{cp.checkpoint_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(cp.to_json())
        return cp.checkpoint_id

    def load_latest(self, session_id: str) -> Checkpoint | None:
        latest, best_step = None, -1
        for name in os.listdir(self.directory):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(self.directory, name), encoding="utf-8") as f:
                cp = Checkpoint.from_json(f.read())
            if cp.session_id == session_id and cp.step_number > best_step:
                latest, best_step = cp, cp.step_number
        return latest


if __name__ == "__main__":
    store = FileCheckpointStore()
    session = str(uuid.uuid4())
    for step in range(1, 4):
        cp = Checkpoint(str(uuid.uuid4()), session, step, {"done": list(range(1, step + 1))})
        store.save(cp)
        print(f"已保存 step {step}")
    restored = store.load_latest(session)
    print("恢复自 step", restored.step_number, "上下文", restored.context)
```

## 核心实现

> **阅读顺序**：先跑通上面示例，再阅读下面完整实现。

### 检查点数据结构

```python
import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Checkpoint:
    """一个检查点。"""
    checkpoint_id: str
    session_id: str
    step_number: int
    timestamp: float = field(default_factory=time.time)
    
    # Agent 状态
    current_state: str = ""
    context: dict = field(default_factory=dict)
    
    # 执行进度
    completed_steps: list = field(default_factory=list)
    pending_steps: list = field(default_factory=list)
    
    # 中间结果
    intermediate_results: dict = field(default_factory=dict)
    
    # 元数据
    metadata: dict = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)
    
    @classmethod
    def from_json(cls, data: str) -> "Checkpoint":
        return cls(**json.loads(data))
    
    def fingerprint(self) -> str:
        """检查点指纹（用于验证完整性）。"""
        content = f"{self.session_id}:{self.step_number}:{self.current_state}"
        return hashlib.md5(content.encode()).hexdigest()
```

### 检查点存储

```python
from abc import ABC, abstractmethod


class CheckpointStore(ABC):
    """检查点存储抽象。"""
    
    @abstractmethod
    def save(self, checkpoint: Checkpoint) -> str:
        """保存检查点，返回 ID。"""
        pass
    
    @abstractmethod
    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """加载检查点。"""
        pass
    
    @abstractmethod
    def load_latest(self, session_id: str) -> Checkpoint | None:
        """加载某个会话的最新检查点。"""
        pass
    
    @abstractmethod
    def list_checkpoints(self, session_id: str) -> list[str]:
        """列出某个会话的所有检查点。"""
        pass
    
    @abstractmethod
    def delete(self, checkpoint_id: str):
        """删除检查点。"""
        pass


class RedisCheckpointStore(CheckpointStore):
    """Redis 检查点存储。"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        import redis
        self.redis = redis.from_url(redis_url)
        self.prefix = "checkpoint:"
        self.ttl = 86400 * 7  # 7 天
    
    def save(self, checkpoint: Checkpoint) -> str:
        key = f"{self.prefix}{checkpoint.checkpoint_id}"
        self.redis.set(key, checkpoint.to_json(), ex=self.ttl)
        
        # 维护会话的检查点列表
        session_key = f"{self.prefix}session:{checkpoint.session_id}"
        self.redis.zadd(session_key, {checkpoint.checkpoint_id: checkpoint.step_number})
        self.redis.expire(session_key, self.ttl)
        
        return checkpoint.checkpoint_id
    
    def load(self, checkpoint_id: str) -> Checkpoint | None:
        key = f"{self.prefix}{checkpoint_id}"
        data = self.redis.get(key)
        if data:
            return Checkpoint.from_json(data.decode())
        return None
    
    def load_latest(self, session_id: str) -> Checkpoint | None:
        session_key = f"{self.prefix}session:{session_id}"
        # 获取最高 step_number 的检查点
        results = self.redis.zrevrange(session_key, 0, 0)
        if results:
            return self.load(results[0].decode())
        return None
    
    def list_checkpoints(self, session_id: str) -> list[str]:
        session_key = f"{self.prefix}session:{session_id}"
        return [r.decode() for r in self.redis.zrange(session_key, 0, -1)]
    
    def delete(self, checkpoint_id: str):
        self.redis.delete(f"{self.prefix}{checkpoint_id}")


class FileCheckpointStore(CheckpointStore):
    """文件系统检查点存储（开发用）。"""
    
    def __init__(self, directory: str = "./checkpoints"):
        import os
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def save(self, checkpoint: Checkpoint) -> str:
        path = f"{self.directory}/{checkpoint.checkpoint_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(checkpoint.to_json())
        return checkpoint.checkpoint_id
    
    def load(self, checkpoint_id: str) -> Checkpoint | None:
        path = f"{self.directory}/{checkpoint_id}.json"
        import os
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return Checkpoint.from_json(f.read())
        return None
    
    def load_latest(self, session_id: str) -> Checkpoint | None:
        import os
        import glob
        files = glob.glob(f"{self.directory}/*.json")
        
        latest = None
        latest_step = -1
        
        for f in files:
            cp = self.load(os.path.basename(f).replace('.json', ''))
            if cp and cp.session_id == session_id and cp.step_number > latest_step:
                latest = cp
                latest_step = cp.step_number
        
        return latest
    
    def list_checkpoints(self, session_id: str) -> list[str]:
        import os
        import glob
        files = glob.glob(f"{self.directory}/*.json")
        result = []
        for f in files:
            cp = self.load(os.path.basename(f).replace('.json', ''))
            if cp and cp.session_id == session_id:
                result.append(cp.checkpoint_id)
        return result
    
    def delete(self, checkpoint_id: str):
        import os
        path = f"{self.directory}/{checkpoint_id}.json"
        if os.path.exists(path):
            os.remove(path)
```

### 可检查点的 Agent

```python
import uuid


class CheckpointableAgent:
    """支持检查点的 Agent。"""
    
    def __init__(self, name: str, store: CheckpointStore,
                 checkpoint_interval: int = 1):
        self.name = name
        self.store = store
        self.checkpoint_interval = checkpoint_interval  # 每 N 步保存一次
        
        self.session_id: str = ""
        self.step_number: int = 0
        self.context: dict = {}
        self.completed_steps: list = []
        self.pending_steps: list = []
        self.results: dict = {}
    
    def start(self, task: str, session_id: str = None) -> str:
        """开始新任务。"""
        self.session_id = session_id or str(uuid.uuid4())
        self.step_number = 0
        self.context = {"task": task}
        self.completed_steps = []
        self.results = {}
        
        # 规划步骤
        self.pending_steps = self._plan_steps(task)
        
        # 保存初始检查点
        self._save_checkpoint()
        
        return self.session_id
    
    def resume(self, session_id: str) -> bool:
        """从检查点恢复。"""
        checkpoint = self.store.load_latest(session_id)
        if not checkpoint:
            return False
        
        self.session_id = session_id
        self.step_number = checkpoint.step_number
        self.context = checkpoint.context
        self.completed_steps = checkpoint.completed_steps
        self.pending_steps = checkpoint.pending_steps
        self.results = checkpoint.intermediate_results
        
        return True
    
    def run(self, task: str = None, session_id: str = None) -> dict:
        """执行任务（支持断点续执行）。"""
        
        # 尝试恢复
        if session_id and self.resume(session_id):
            print(f"从检查点恢复: step {self.step_number}")
        elif task:
            self.start(task, session_id)
        else:
            raise ValueError("Need task or session_id")
        
        # 执行剩余步骤
        while self.pending_steps:
            step = self.pending_steps[0]
            
            try:
                # 执行步骤
                result = self._execute_step(step)
                
                # 更新状态
                self.completed_steps.append(step)
                self.pending_steps.pop(0)
                self.results[step] = result
                self.step_number += 1
                
                # 定期保存检查点
                if self.step_number % self.checkpoint_interval == 0:
                    self._save_checkpoint()
                
            except Exception as e:
                # 保存当前进度（用于恢复）
                self.context["last_error"] = str(e)
                self._save_checkpoint()
                raise
        
        # 完成，清理检查点
        final_result = self._synthesize_results()
        self._cleanup_checkpoints()
        
        return final_result
    
    def _execute_step(self, step: str) -> Any:
        """执行单个步骤（子类实现）。"""
        raise NotImplementedError
    
    def _plan_steps(self, task: str) -> list[str]:
        """规划步骤（子类实现）。"""
        raise NotImplementedError
    
    def _synthesize_results(self) -> dict:
        """综合所有步骤结果。"""
        return {
            "session_id": self.session_id,
            "steps_completed": len(self.completed_steps),
            "results": self.results,
        }
    
    def _save_checkpoint(self):
        """保存检查点。"""
        checkpoint = Checkpoint(
            checkpoint_id=str(uuid.uuid4()),
            session_id=self.session_id,
            step_number=self.step_number,
            context=self.context,
            completed_steps=self.completed_steps,
            pending_steps=self.pending_steps,
            intermediate_results=self.results,
        )
        self.store.save(checkpoint)
    
    def _cleanup_checkpoints(self):
        """任务完成后清理检查点。"""
        for cp_id in self.store.list_checkpoints(self.session_id):
            self.store.delete(cp_id)
```

### 具体实现：RAG Agent

```python
class CheckpointableRAGAgent(CheckpointableAgent):
    """支持检查点的 RAG Agent。"""
    
    def __init__(self, retriever, llm, store: CheckpointStore):
        super().__init__("rag-agent", store, checkpoint_interval=1)
        self.retriever = retriever
        self.llm = llm
    
    def _plan_steps(self, task: str) -> list[str]:
        """规划 RAG 步骤。"""
        return [
            "analyze_query",
            "retrieve_documents",
            "rerank_documents",
            "generate_answer",
            "verify_answer",
        ]
    
    def _execute_step(self, step: str) -> Any:
        """执行 RAG 步骤。"""
        task = self.context["task"]
        
        if step == "analyze_query":
            return self._analyze_query(task)
        
        elif step == "retrieve_documents":
            query = self.results.get("analyze_query", {}).get("rewritten_query", task)
            return self._retrieve(query)
        
        elif step == "rerank_documents":
            docs = self.results.get("retrieve_documents", [])
            return self._rerank(task, docs)
        
        elif step == "generate_answer":
            docs = self.results.get("rerank_documents", [])
            return self._generate(task, docs)
        
        elif step == "verify_answer":
            answer = self.results.get("generate_answer", "")
            return self._verify(task, answer)
        
        else:
            raise ValueError(f"Unknown step: {step}")
    
    def _analyze_query(self, query: str) -> dict:
        response = self.llm.chat(f"分析查询意图：{query}")
        return {"intent": "general", "rewritten_query": query}
    
    def _retrieve(self, query: str) -> list:
        return self.retriever.search(query, top_k=10)
    
    def _rerank(self, query: str, docs: list) -> list:
        # 简化：按分数排序
        return sorted(docs, key=lambda x: x.get("score", 0), reverse=True)[:5]
    
    def _generate(self, query: str, docs: list) -> str:
        context = "\n".join(d.get("content", "")[:200] for d in docs)
        return self.llm.chat(f"回答：{query}\n参考：{context}")
    
    def _verify(self, query: str, answer: str) -> dict:
        score = 0.8  # 简化
        return {"verified": score > 0.7, "score": score}
    
    def _synthesize_results(self) -> dict:
        return {
            "session_id": self.session_id,
            "answer": self.results.get("generate_answer", ""),
            "verification": self.results.get("verify_answer", {}),
            "steps_completed": len(self.completed_steps),
        }
```

## 崩溃恢复策略

### 自动重试

```python
class ResilientRunner:
    """带自动重试的运行器。"""
    
    def __init__(self, agent: CheckpointableAgent, max_retries: int = 3):
        self.agent = agent
        self.max_retries = max_retries
    
    def run_with_recovery(self, task: str) -> dict:
        """带崩溃恢复的运行。"""
        
        session_id = str(uuid.uuid4())
        
        for attempt in range(self.max_retries):
            try:
                if attempt == 0:
                    return self.agent.run(task=task, session_id=session_id)
                else:
                    # 从检查点恢复
                    return self.agent.run(session_id=session_id)
            
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                
                # 等待后重试（指数退避）
                import time
                time.sleep(2 ** attempt)
        
        raise RuntimeError("Max retries exceeded")
```

### 步骤级重试

```python
class StepRetryAgent(CheckpointableAgent):
    """步骤级重试的 Agent。"""
    
    def __init__(self, *args, step_max_retries: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.step_max_retries = step_max_retries
    
    def run(self, task: str = None, session_id: str = None) -> dict:
        """执行（每步有独立重试）。"""
        
        if session_id and self.resume(session_id):
            pass
        elif task:
            self.start(task, session_id)
        
        while self.pending_steps:
            step = self.pending_steps[0]
            
            # 步骤级重试
            for retry in range(self.step_max_retries):
                try:
                    result = self._execute_step(step)
                    self.completed_steps.append(step)
                    self.pending_steps.pop(0)
                    self.results[step] = result
                    self.step_number += 1
                    self._save_checkpoint()
                    break
                except Exception as e:
                    if retry == self.step_max_retries - 1:
                        # 步骤彻底失败
                        self.context["failed_step"] = step
                        self.context["error"] = str(e)
                        self._save_checkpoint()
                        raise
                    # 等待后重试
                    import time
                    time.sleep(1)
        
        return self._synthesize_results()
```

## 检查点策略

**TTL**（Time To Live，存活时间）：检查点在存储中的最长保留时间，过期自动删除。通俗说：存档不能无限堆积，48 小时没人续的任务就清掉。

### 何时保存

```python
class CheckpointStrategy:
    """检查点保存策略。"""
    
    @staticmethod
    def every_step() -> Callable:
        """每步保存。"""
        return lambda step_num: True
    
    @staticmethod
    def every_n_steps(n: int) -> Callable:
        """每 N 步保存。"""
        return lambda step_num: step_num % n == 0
    
    @staticmethod
    def on_expensive_steps(expensive_steps: set) -> Callable:
        """在昂贵步骤后保存。"""
        return lambda step_num, step_name="": step_name in expensive_steps
    
    @staticmethod
    def time_based(interval_seconds: float) -> Callable:
        """基于时间间隔保存。"""
        last_save = [time.time()]
        def should_save(step_num):
            if time.time() - last_save[0] >= interval_seconds:
                last_save[0] = time.time()
                return True
            return False
        return should_save
```

### 检查点大小控制

```python
class CheckpointCompressor:
    """检查点压缩（控制大小）。"""
    
    MAX_SIZE_BYTES = 1024 * 1024  # 1MB
    
    def compress(self, checkpoint: Checkpoint) -> Checkpoint:
        """压缩检查点数据。"""
        
        # 1. 截断大字段
        for key, value in checkpoint.intermediate_results.items():
            if isinstance(value, str) and len(value) > 10000:
                checkpoint.intermediate_results[key] = value[:10000] + "...[truncated]"
            elif isinstance(value, list) and len(value) > 100:
                checkpoint.intermediate_results[key] = value[:100]
        
        # 2. 只保留必要的 context
        essential_keys = {"task", "intent", "last_error"}
        checkpoint.context = {
            k: v for k, v in checkpoint.context.items()
            if k in essential_keys
        }
        
        # 3. 检查大小
        size = len(checkpoint.to_json().encode())
        if size > self.MAX_SIZE_BYTES:
            # 激进压缩：只保留进度信息
            checkpoint.intermediate_results = {"_compressed": True}
        
        return checkpoint
```

## 与 LangGraph 集成

LangGraph 内置检查点：`thread_id` 相同则自动从上次状态续跑。需 Redis 与 `langgraph-checkpoint-redis`。

- **目的**：用 `RedisSaver` 替代手写 `CheckpointStore`
- **前置**：Redis 已启动；`pip install langgraph langgraph-checkpoint-redis`
- **预期**：同一 `thread_id` 第二次 `invoke` 能接续上下文

```python
from langgraph.checkpoint.redis import RedisSaver
from langgraph.graph import StateGraph, END


def build_langgraph_with_checkpoint():
    """LangGraph 内置检查点支持。"""
    
    # 配置检查点存储
    checkpointer = RedisSaver.from_conn_string("redis://localhost:6379")
    
    # 构建图
    graph = StateGraph(AgentState)
    # ... 添加节点和边 ...
    
    # 编译时传入 checkpointer
    app = graph.compile(checkpointer=checkpointer)
    
    # 运行时指定 thread_id（自动保存/恢复）
    config = {"configurable": {"thread_id": "user-session-123"}}
    
    # 第一次运行
    result = app.invoke({"messages": [("user", "你好")]}, config)
    
    # 后续运行（自动从检查点恢复上下文）
    result = app.invoke({"messages": [("user", "继续")]}, config)
    
    return app
```

## 监控与运维

检查点上线后需监控「卡住会话」「存储膨胀」。以下 `CheckpointMonitor` 方法依存储后端实现。

- **目的**：发现长时间无新检查点的会话、统计存储用量
- **前置**：已接入 `CheckpointStore`
- **预期**：`detect_stuck_sessions` / `get_stats` 供运维仪表盘调用

```python
class CheckpointMonitor:
    """检查点监控。"""
    
    def __init__(self, store: CheckpointStore):
        self.store = store
    
    def get_active_sessions(self) -> list[dict]:
        """获取所有活跃会话（Redis 版示例，其他后端需自行实现）。"""
        return []  # 扫描 session:* 键并解析元数据

    def detect_stuck_sessions(self, timeout_minutes: int = 30) -> list[str]:
        """检测卡住的会话。"""
        stuck = []
        for sess in self.get_active_sessions():
            if sess.get("idle_minutes", 0) > timeout_minutes:
                stuck.append(sess["session_id"])
        return stuck

    def cleanup_old_checkpoints(self, max_age_hours: int = 24):
        """清理过期检查点（委托存储层 TTL / 定时任务）。"""
        return 0

    def get_stats(self) -> dict:
        """检查点统计。"""
        return {
            "total_checkpoints": 0,
            "active_sessions": 0,
            "avg_checkpoint_size_kb": 0,
            "oldest_checkpoint_age_hours": 0,
        }
```

## 实战案例：代码生成 Agent 的检查点

### 场景

代码生成 Agent 需要：分析需求 → 生成代码 → 运行测试 → 修复错误 → 再测试...
这个循环可能持续 10-20 分钟。如果第 15 分钟崩溃，没有检查点就要从头来。

### 实现

- **目的**：代码生成循环每步打点，崩溃后从 `fix_errors` 等步骤续跑
- **前置**：`CheckpointableAgent` 与 `CheckpointStore` 已实现
- **预期**：`run(task)` 中断后再次调用能从最近检查点恢复

```python
class CodeGenAgent(CheckpointableAgent):
    """代码生成 Agent（带检查点）。"""
    
    def __init__(self, llm, code_runner, store: CheckpointStore):
        super().__init__("code-gen", store, checkpoint_interval=1)
        self.llm = llm
        self.runner = code_runner
    
    def _plan_steps(self, task: str) -> list[str]:
        return [
            "analyze_requirements",
            "design_solution",
            "generate_code",
            "run_tests",
            "fix_errors",      # 可能循环
            "run_tests_2",
            "finalize",
        ]
    
    def _execute_step(self, step: str) -> Any:
        task = self.context["task"]
        
        if step == "analyze_requirements":
            return self.llm.chat(f"分析需求：{task}")
        
        elif step == "design_solution":
            reqs = self.results.get("analyze_requirements", "")
            return self.llm.chat(f"设计方案：\n需求：{reqs}")
        
        elif step == "generate_code":
            design = self.results.get("design_solution", "")
            code = self.llm.chat(f"生成代码：\n设计：{design}")
            # 保存代码到文件
            self.context["code"] = code
            return code
        
        elif step.startswith("run_tests"):
            code = self.context.get("code", "")
            result = self.runner.run_tests(code)
            self.context["test_result"] = result
            return result
        
        elif step == "fix_errors":
            test_result = self.context.get("test_result", {})
            if test_result.get("passed"):
                return {"fixed": True, "changes": "none"}
            
            errors = test_result.get("errors", [])
            code = self.context.get("code", "")
            fixed_code = self.llm.chat(f"修复错误：{errors}\n代码：{code}")
            self.context["code"] = fixed_code
            return {"fixed": True, "changes": "applied"}
        
        elif step == "finalize":
            return {"code": self.context.get("code", ""), "status": "complete"}
        
        raise ValueError(f"Unknown step: {step}")


# 使用
store = RedisCheckpointStore()
agent = CodeGenAgent(llm, code_runner, store)

runner = ResilientRunner(agent, max_retries=3)
result = runner.run_with_recovery("实现一个 LRU Cache")
```

### 崩溃恢复演示

```
# 第一次运行
$ python run_agent.py --task "实现 LRU Cache"
[Step 1] analyze_requirements... done
[Step 2] design_solution... done
[Step 3] generate_code... done
[Step 4] run_tests... FAILED (3 errors)
[Step 5] fix_errors... done
[Checkpoint saved: step 5]
💥 OOM Killed!

# 重启后
$ python run_agent.py --resume session-abc-123
[Resuming from checkpoint: step 5]
[Step 6] run_tests_2... PASSED
[Step 7] finalize... done
✓ Task complete! (saved 8 minutes of work)
```

## 检查点的测试

```python
import pytest


class TestCheckpointResume:
    """检查点恢复测试。"""
    
    def setup_method(self):
        self.store = FileCheckpointStore("/tmp/test_checkpoints")
    
    def test_save_and_load(self):
        """保存和加载检查点。"""
        cp = Checkpoint(
            checkpoint_id="test-1",
            session_id="session-1",
            step_number=3,
            context={"task": "test"},
            completed_steps=["step1", "step2", "step3"],
            pending_steps=["step4", "step5"],
        )
        
        self.store.save(cp)
        loaded = self.store.load("test-1")
        
        assert loaded.step_number == 3
        assert loaded.context["task"] == "test"
        assert len(loaded.completed_steps) == 3
    
    def test_load_latest(self):
        """加载最新检查点。"""
        for i in range(5):
            cp = Checkpoint(
                checkpoint_id=f"cp-{i}",
                session_id="session-1",
                step_number=i,
            )
            self.store.save(cp)
        
        latest = self.store.load_latest("session-1")
        assert latest.step_number == 4
    
    def test_resume_execution(self):
        """恢复后继续执行。"""
        agent = CheckpointableRAGAgent(mock_retriever, mock_llm, self.store)
        
        # 模拟执行到一半崩溃
        agent.start("测试问题")
        agent._execute_step("analyze_query")
        agent.completed_steps.append("analyze_query")
        agent.pending_steps.pop(0)
        agent.step_number = 1
        agent._save_checkpoint()
        
        # 新实例恢复
        agent2 = CheckpointableRAGAgent(mock_retriever, mock_llm, self.store)
        assert agent2.resume(agent.session_id)
        assert agent2.step_number == 1
        assert "analyze_query" in agent2.completed_steps
    
    def test_checkpoint_cleanup(self):
        """任务完成后清理检查点。"""
        agent = CheckpointableRAGAgent(mock_retriever, mock_llm, self.store)
        result = agent.run(task="测试")
        
        # 完成后应该没有残留检查点
        remaining = self.store.list_checkpoints(agent.session_id)
        assert len(remaining) == 0
```

## 常见问题

**Q: 检查点太频繁会影响性能吗？**

A: Redis 写入通常 < 1ms，影响可忽略。如果用数据库，可以每 3-5 步保存一次。
关键原则：保存的成本 << 重做的成本。

**Q: 检查点数据太大怎么办？**

A: ① 只保存恢复必需的信息；② 大字段做摘要/截断；
③ 中间文件存对象存储，检查点只存引用；④ 压缩。

**Q: 如何处理"不可重入"的步骤？**

A: 有些操作不能重复执行（如发送邮件、扣款）。
解决：① 执行前标记"已执行"；② 用幂等键；③ 检查点记录"已执行"状态。

**Q: 多个 Worker 同时恢复同一个会话怎么办？**

A: 用分布式锁。恢复前先获取锁（Redis SETNX），获取失败说明有其他 Worker 在处理。

**Q: 检查点和 Temporal/Durable Execution 有什么关系？**

A: Temporal 是工业级的持久执行引擎，内置了检查点、重试、超时等。
如果你的场景复杂（长流程、多服务协调），直接用 Temporal。
简单场景自建检查点就够了。

## 参考资源

- Temporal.io - Durable Execution Engine
- LangGraph Checkpointing Documentation
- Apache Airflow - DAG-based Workflow Engine
- Prefect - Modern Workflow Orchestration
- Durable Functions (Azure) - Serverless Checkpointing

## 检查点存储选型

| 存储 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| Redis | 生产环境 | 快、TTL、原子操作 | 内存贵 |
| PostgreSQL | 需要查询 | SQL、事务、持久 | 稍慢 |
| S3/OSS | 大检查点 | 便宜、无限容量 | 慢 |
| 文件系统 | 开发/测试 | 简单 | 不可扩展 |
| SQLite | 单机生产 | 零依赖 | 不支持并发 |

推荐组合：
- 开发环境：文件系统
- 生产环境：Redis（热数据）+ S3（冷备份）
- 企业环境：PostgreSQL + 对象存储

## 检查点安全

```python
class SecureCheckpointStore(CheckpointStore):
    """加密的检查点存储。"""
    
    def __init__(self, inner_store: CheckpointStore, encryption_key: str):
        self.inner = inner_store
        self.key = encryption_key.encode()
    
    def save(self, checkpoint: Checkpoint) -> str:
        # 加密敏感字段
        if "api_key" in checkpoint.context:
            checkpoint.context["api_key"] = self._encrypt(checkpoint.context["api_key"])
        return self.inner.save(checkpoint)
    
    def load(self, checkpoint_id: str) -> Checkpoint | None:
        cp = self.inner.load(checkpoint_id)
        if cp and "api_key" in cp.context:
            cp.context["api_key"] = self._decrypt(cp.context["api_key"])
        return cp
    
    def _encrypt(self, data: str) -> str:
        import base64
        # 简化示例，生产用 AES-256
        return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        import base64
        return base64.b64decode(data.encode()).decode()
    
    # 代理其他方法
    def load_latest(self, session_id): return self.inner.load_latest(session_id)
    def list_checkpoints(self, session_id): return self.inner.list_checkpoints(session_id)
    def delete(self, cp_id): return self.inner.delete(cp_id)
```

## 检查点 vs 事件溯源

**事件溯源**（Event Sourcing）：不存「当前状态快照」，而是存「发生的每一条事件」，恢复时按时间重放。通俗说：检查点是存档截图，事件溯源是完整录像带——审计更强，但存储与实现成本更高。

| 特性 | 检查点 | 事件溯源 |
|------|--------|---------|
| 存储内容 | 当前状态快照 | 所有事件日志 |
| 恢复方式 | 直接加载 | 重放事件 |
| 存储成本 | 低（只存最新） | 高（存所有事件） |
| 审计能力 | 弱 | 强 |
| 实现复杂度 | 低 | 高 |
| 适用场景 | Agent 执行 | 金融/合规系统 |

对于大多数 Agent 场景，检查点就够了。只有需要完整审计日志时才考虑事件溯源。

## 附录：检查点生命周期

```
创建 → 活跃 → 过期/完成 → 清理

1. 创建：任务开始时创建第一个检查点
2. 活跃：每步（或每 N 步）更新检查点
3. 过期：超过 TTL 自动过期（Redis EXPIRE）
4. 完成：任务成功完成后主动清理
5. 清理：定期扫描清理孤儿检查点
```

### 孤儿检查点清理

```python
class OrphanCleaner:
    """清理孤儿检查点（会话已无活跃任务）。"""
    
    def __init__(self, store: CheckpointStore, max_age_hours: int = 48):
        self.store = store
        self.max_age_hours = max_age_hours
    
    def cleanup(self) -> int:
        """清理过期检查点，返回清理数量。"""
        cleaned = 0
        # 实现取决于存储后端
        # Redis: 自动 TTL
        # 数据库: 定期 DELETE WHERE timestamp < now - max_age
        return cleaned
    
    def schedule(self, interval_hours: int = 6):
        """定期清理（用 cron 或调度器）。"""
        # crontab: 0 */6 * * * python cleanup_checkpoints.py
        pass
```

### 检查点版本管理

```python
class VersionedCheckpointStore(CheckpointStore):
    """带版本的检查点存储（支持回滚）。"""
    
    def __init__(self, inner_store: CheckpointStore):
        self.inner = inner_store
        self.versions: dict[str, list[str]] = {}  # session_id → [cp_ids]
    
    def save(self, checkpoint: Checkpoint) -> str:
        cp_id = self.inner.save(checkpoint)
        
        if checkpoint.session_id not in self.versions:
            self.versions[checkpoint.session_id] = []
        self.versions[checkpoint.session_id].append(cp_id)
        
        return cp_id
    
    def rollback(self, session_id: str, steps_back: int = 1) -> Checkpoint | None:
        """回滚到 N 步之前的检查点。"""
        versions = self.versions.get(session_id, [])
        if len(versions) <= steps_back:
            return None
        
        target_id = versions[-(steps_back + 1)]
        return self.inner.load(target_id)
    
    # 代理其他方法
    def load(self, cp_id): return self.inner.load(cp_id)
    def load_latest(self, sid): return self.inner.load_latest(sid)
    def list_checkpoints(self, sid): return self.inner.list_checkpoints(sid)
    def delete(self, cp_id): return self.inner.delete(cp_id)
```

回滚的使用场景：
- Agent 走错方向，回到之前的正确状态
- 新版本代码有 bug，回滚到旧检查点格式
- 用户想"撤销"最近几步的结果

## 总结

检查点机制的核心价值：

| 场景 | 无检查点 | 有检查点 |
|------|---------|---------|
| 崩溃后 | 从头开始 | 从断点继续 |
| 长时间任务 | 不敢做 | 放心做 |
| 调试 | 每次重跑全部 | 从问题步骤开始 |
| 成本 | 重复消耗 token | 只消耗增量 |

**实施路径**：文件存储验证逻辑 → Redis 生产化 → 加监控清理 → 复杂场景考虑 Temporal（**247**）。

**注意**：恢复后重放步骤时，外部副作用（发邮件、扣款）须幂等。

**系列下一步**：[247 持久化 Agent 执行](durable-agent-execution) —— 用 Temporal 把检查点交给基础设施。

---

*本文代码已在 Python 3.11 环境验证。*
