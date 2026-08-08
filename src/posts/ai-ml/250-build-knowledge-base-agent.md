---
title: "构建知识库 Agent：Part 7 累积工程起点"
slug: build-knowledge-base-agent
date: 2025-06-14
tags: [AI, Agent, 知识库, RAG, 综合实战]
category: ai-ml
description: "在 examples/agent-platform 上实现知识库 Agent：上传、分块、索引、检索——251–254 共用 shared/ 包。"
---

> **系列导读**：[agent-rag-series-238-254](agent-rag-series-238-254) | **体系化正文**：[`250.build-knowledge-base-agent-tutorial.md`](../../../docs/250.build-knowledge-base-agent-tutorial.md)

## 学习目标

读完本篇，你能：

1. 在本地跑通 `python -m demos.demo_250`
2. 说明 **KnowledgeBaseAgent** 的工具链：`upload` → `index` → `search`
3. 理解 `shared/types.py` 与 `shared/base.py` 在 251–254 中的复用方式
4. 画出文档生命周期状态：`uploaded` → `indexed`（失败则 `failed`）

## 前置阅读

- **214–249** 系列约束（工具、循环、Agentic RAG、可靠性）——本篇是 **Part 7 综合实战起点**
- **249 事件驱动**（可选）：生产环境中文档变更可发 `DocumentUploaded` 等事件

## 环境要求

```bash
cd examples/agent-platform
pip install -r requirements.txt
python -m demos.demo_250
```

- Python **3.10+**
- 依赖：`pydantic`（requirements.txt 已列出）
- **无需** OpenAI API / 向量数据库（教学用内存「向量库」）

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| `agent-platform` 目录、`BaseAgent`、`ToolResult` | 真实 embedding / Milvus 调优 |
| 文档上传、分块、内存索引、检索 | 251–254 业务 Agent 细节 |
| `KnowledgeBaseAgent` 最小闭环 | 重复讲解 Part 2 工具注册表 |

## 动手路径

| 步骤 | 操作 | 验收 |
|------|------|------|
| 1 | `pip install -r requirements.txt` | 无报错 |
| 2 | `python -m demos.demo_250` | 见下方「预期输出」 |
| 3 | 阅读 `shared/base.py` | 能说出 `register_tool` / `run_tool` |
| 4 | 打开 `demos/demo_251.py` | 看到继承 `KnowledgeBaseAgent` |

## 工程目录

```text
examples/agent-platform/
├── shared/
│   ├── types.py      # ToolResult, AgentTrace, PermissionLevel
│   └── base.py       # BaseAgent.register_tool / run_tool
├── demos/
│   ├── demo_250.py   # 本篇：知识库生命周期
│   ├── demo_251.py   # 研究 Agent（继承 250）
│   └── demo_252–254.py
└── requirements.txt
```

**KnowledgeBaseAgent**（知识库 Agent）：封装「上传 → 索引 → 检索」工具链的 Agent。
通俗说：管文档从进库到能搜到的全流程，不是只会问答一次的聊天框。

## 核心类型

### ToolResult

统一工具返回，模型与日志都能读：

```python
# shared/types.py（节选）
@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
```

### BaseAgent

```python
# shared/base.py（节选）
class BaseAgent(ABC):
    def register_tool(self, name, fn, permission=PermissionLevel.AUTO): ...
    def run_tool(self, name, **kwargs) -> ToolResult: ...
    @abstractmethod
    def run(self, goal: str) -> AgentTrace: ...
```

251–254 的 Agent 都从这里扩展，避免每篇重写工具调度。

## 最小可运行：demo_250

**演示什么：** 上传 FAQ 文档 → 分块索引 → 搜索「Agent」。
**预期输出：**

```text
upload: ToolResult(success=True, data={'doc_id': 'DOC-XXXXXXXX'}, ...)
search: ToolResult(success=True, data=['Agent 是能自主决策的系统。'], ...)
OK — KnowledgeBaseAgent (250)
```

完整源码（与仓库一致，便于对照）：

```python
"""demos/demo_250.py — 知识库 Agent"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from shared.base import BaseAgent
from shared.types import AgentTrace, ToolResult


class DocState(str, Enum):
    UPLOADED = "uploaded"
    INDEXED = "indexed"
    FAILED = "failed"


@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    state: DocState = DocState.UPLOADED
    chunks: list[str] = field(default_factory=list)


class KnowledgeBaseAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self.documents: dict[str, Document] = {}
        self.vector_store: dict[str, list[str]] = {}
        self.register_tool("upload", self.upload)
        self.register_tool("index", self.index_doc)
        self.register_tool("search", self.search)

    def upload(self, title: str, content: str) -> ToolResult:
        doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        self.documents[doc_id] = Document(doc_id=doc_id, title=title, content=content)
        return ToolResult(success=True, data={"doc_id": doc_id})

    def index_doc(self, doc_id: str) -> ToolResult:
        doc = self.documents.get(doc_id)
        if not doc:
            return ToolResult(success=False, error="not found")
        doc.chunks = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
        doc.state = DocState.INDEXED
        self.vector_store[doc_id] = doc.chunks
        return ToolResult(success=True, data={"chunks": len(doc.chunks)})

    def search(self, query: str) -> ToolResult:
        hits: list[str] = []
        for chunks in self.vector_store.values():
            hits.extend(c for c in chunks if query.lower() in c.lower())
        return ToolResult(success=True, data=hits[:3])

    def run(self, goal: str) -> AgentTrace:
        self.trace = AgentTrace(goal=goal)
        up = self.run_tool(
            "upload",
            title="FAQ",
            content="Agent 是能自主决策的系统。\n\nRAG 是检索增强生成。",
        )
        doc_id = up.data["doc_id"]
        self.run_tool("index", doc_id=doc_id)
        sr = self.run_tool("search", query="Agent")
        print("upload:", up)
        print("search:", sr)
        return self.trace


if __name__ == "__main__":
    KnowledgeBaseAgent().run("索引并搜索知识库")
    print("OK — KnowledgeBaseAgent (250)")
```

### 代码后解读

1. `upload` 只登记文档，状态为 `UPLOADED`，尚未可搜。
2. `index` 按空行分块并写入 `vector_store`，状态变为 `INDEXED`。
3. `search` 在内存块上做子串匹配——生产环境替换为向量检索即可，**工具接口不变**。

## 文档状态机（概念）

```text
upload → UPLOADED → index 成功 → INDEXED → search 命中
                  → index 失败 → FAILED（可重试 index）
delete → 删 documents + vector_store 对应项
```

教程正文含 `cleanup_orphans`、健康检查等工程化工具。

## 与 239–248 lab 的关系

| 工程 | 路径 | 适用篇 |
|------|------|--------|
| rag-agent-lab | `examples/rag-agent-lab/` | 239–244 Agentic RAG |
| agent-platform | `examples/agent-platform/` | **250–254** 业务 Agent |

250 起默认在 **agent-platform** 上叠代；不要与 lab 混为两个「半套」工程。

## Part 7 路线图

| 篇 | demo | 在 250 基础上增加 |
|----|------|-------------------|
| 250 | `demo_250` | 知识库生命周期 |
| 251 | `demo_251` | 研究摘要 `synthesize` |
| 252 | `demo_252` | 客服 + HITL 退款 |
| 253 | `demo_253` | diff 分块审查 |
| 254 | `demo_254` | 运维高风险确认 |

## 常见陷阱

1. **只 upload 不 index**：搜索永远空——Agent 或工作流须保证索引步骤。
2. **更新文档不删旧向量**：检索到过期 chunk——更新策略：先删后写或 versioned id。
3. **把 Part 2 工具层跳过**：250 仍依赖 `ToolResult` 约定——与 218–221 一致。

## 常见问题

**Q: 为什么没有真向量库？**

A: 本篇聚焦 **Agent 工具编排与生命周期**；向量库替换 `vector_store` 字典即可，接口保持 `ToolResult`。

**Q: 251 怎么接？**

A: `class ResearchAgent(KnowledgeBaseAgent)`，见 `demos/demo_251.py`。

**Q: 教程太长从哪里读？**

A: 面试与失败模式读 [`250.build-knowledge-base-agent-tutorial.md`](../../../docs/250.build-knowledge-base-agent-tutorial.md)；跑通代码读本篇即可。

## 系列下一步

- 博客 + 代码：**251** [`docs/251.build-research-agent-tutorial.md`](../../../docs/251.build-research-agent-tutorial.md) · `python -m demos.demo_251`
- 系列总览：[agent-rag-series-238-254](agent-rag-series-238-254)

---

*运行 `python -m demos.demo_250` 即可验证环境。*
