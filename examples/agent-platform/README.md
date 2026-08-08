# Agent Platform — Part 7 累积工程（250–254）

五篇综合实战共享 `shared/` 包，各篇在 `demos/demo_NNN.py` 扩展业务能力。

## 快速开始

```bash
cd examples/agent-platform
pip install -r requirements.txt
python -m demos.demo_250   # 知识库 Agent（250）
python -m demos.demo_251   # 研究 Agent（251）
python -m demos.demo_252   # 客服 Agent（252）
python -m demos.demo_253   # 代码审查 Agent（253）
python -m demos.demo_254   # 运营 Agent（254）
```

## 目录结构

```text
agent-platform/
├── shared/           # 250 起共用：ToolResult、BaseAgent、权限钩子
├── demos/            # 各篇可运行入口
└── requirements.txt
```

## 与教程对应

| 教程 | 模块 | 沿用 shared |
|------|------|-------------|
| 250 | `demos/demo_250.py` | 定义 `ToolResult`, `BaseAgent` |
| 251 | `demos/demo_251.py` | + 多步检索状态 |
| 252 | `demos/demo_252.py` | + HITL 审批队列 |
| 253 | `demos/demo_253.py` | + diff 分块审查 |
| 254 | `demos/demo_254.py` | + 高风险操作确认 |

Part 5–6 动手代码见 [`../rag-agent-lab/`](../rag-agent-lab/)。  
Part 6–7 博客实践版：[249 事件驱动](../../src/posts/ai-ml/249-agent-event-driven-architecture.md) · [250 知识库 Agent](../../src/posts/ai-ml/250-build-knowledge-base-agent.md)
