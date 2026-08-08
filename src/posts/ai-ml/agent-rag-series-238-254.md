# Agent / RAG 工程系列（238–254）导读

> 本文件原名 `agent-rag-series-239-248.md`，现与内容范围对齐为 **238–254**。

本系列覆盖「Agentic RAG 架构 → 检索增强 → 可信 → 排障 → 编排 → 可靠性 → 综合实战」完整链路。

## 读哪套文档？

| 目标 | 推荐路径 |
|------|----------|
| **架构总览** | `docs/238.agentic-rag-architecture-tutorial.md` |
| **动手跑代码（239–244）** | `src/posts/ai-ml/239`–`248` 博客 + [`examples/rag-agent-lab/`](../../examples/rag-agent-lab/) |
| **可靠性 + 事件（248–249）** | [248 后台任务](248-agent-background-job.md) · [249 事件驱动](249-agent-event-driven-architecture.md) |
| **综合实战（250–254）** | [250 知识库 Agent 博客](250-build-knowledge-base-agent.md) + [`examples/agent-platform/`](../../examples/agent-platform/) + `docs/250–254` |
| **体系化 + 面试** | `docs/*-tutorial.md`（含面试怎么讲、生产注意事项） |
| **快速验证** | `cd examples/rag-agent-lab && python main.py 243`（无需 API） |

两套正文互补：tutorial 偏体系与面试；博客 + lab/platform 偏可运行代码。

## 能力地图

| 篇 | 主题 | 交付物 | 可运行示例 |
|----|------|--------|------------|
| 238 | Agentic RAG 架构 | 四组件总览 | 文内 `demo_agentic_rag()` |
| 239 | 查询规划 | 分解 + 多路检索 + RRF | `main.py 239` |
| 240 | 多步检索 | 动态多轮检索 + 防循环 | `main.py 240` |
| 241 | 工具增强 | tool_calls 循环 + 安全 | `main.py 241` |
| 242 | 引用验证 | 标注 + 验证 + 修正 | `main.py 242` |
| 243 | Bad Case 调试 | trace + 分类 + 闭环 | `main.py 243`（无 API） |
| 244 | 工作流模式 | 7 种编排范式 | `main.py 244`（无 API） |
| 245 | 状态机 Agent | FSM 约束流程 | 文内 `demo_fsm` |
| 246 | 检查点 | 手动 save/load | 文内 `demo_checkpoint` |
| 247 | Temporal | 持久化执行 | `temporal_minimal.py`（需 Docker） |
| 248 | 后台任务 | 异步 + 进度推送 | 文内内存 demo |
| 249 | 事件驱动 | 事件总线 + 溯源 | 文内 async demo · [博客](249-agent-event-driven-architecture.md) |
| 250 | 知识库 Agent | `agent-platform` 起点 | [`python -m demos.demo_250`](../../examples/agent-platform/) · [博客](250-build-knowledge-base-agent.md) |
| 251–254 | 综合实战 | 累积扩展 | `demo_251` … `demo_254` |

## 建议阅读顺序

```
214–225 工具与边界（前置）
  ↓
226–237 Agent Loop 与 Memory
  ↓
238 Agentic RAG（总览）
  ↓
239 查询规划 → 240 多步检索 → 241 工具增强 → 242 引用验证
  ↓
243 Bad Case 调试（收束 RAG 质量）
  ↓
244 工作流模式 → 245 状态机 → 246 检查点 → 247 Temporal → 248 后台 → 249 事件驱动
  ↓
250 知识库 Agent → 251 研究 → 252 客服 → 253 代码审查 → 254 运营
```

## 刻意留白（本系列不讲）

- 向量库选型与索引调优（见 RAG 基础系列）
- 前端完整 UI 工程（248 给 Hook 骨架）
- Kubernetes / 多租户部署细节
- 微调 embedding 模型

## 环境速查

```bash
# Agentic RAG lab（239–244）
cd examples/rag-agent-lab
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # 239–242 需要
python main.py 243              # 无需 API
python main.py 244              # 无需 API

# Part 7 累积工程
cd examples/agent-platform
pip install -r requirements.txt
python -m demos.demo_250

# Temporal（247）
pip install temporalio && python temporal_minimal.py  # 需 Docker Temporal
```

## 博客实践版（248–250）

| 篇 | 博客 | 可运行入口 |
|----|------|------------|
| 248 | [agent-background-job](248-agent-background-job.md) | 文内内存队列 demo |
| 249 | [agent-event-driven-architecture](249-agent-event-driven-architecture.md) | `demo_event_bus.py`（文内） |
| 250 | [build-knowledge-base-agent](250-build-knowledge-base-agent.md) | `python -m demos.demo_250` |
