# Agent / RAG 工程系列（239–248）导读

本系列覆盖「检索增强 → 可信 → 排障 → 编排 → 可靠性」完整链路。

## 读哪套文档？

| 目标 | 推荐路径 |
|------|----------|
| **动手跑代码** | `src/posts/ai-ml/239–248` 博客 + [`examples/rag-agent-lab/`](../../examples/rag-agent-lab/) |
| **体系化 + 面试** | `docs/239–248.*-tutorial.md`（含面试怎么讲、生产注意事项） |
| **快速验证** | `cd examples/rag-agent-lab && python main.py 243`（无需 API） |

两套正文互补，不重复维护全文；tutorial 文首/文末有「博客版补充」链接。

## 能力地图

| 篇 | 主题 | 交付物 | 可运行示例 |
|----|------|--------|------------|
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

## 建议阅读顺序

```
238 Agentic RAG（前驱）
  ↓
239 查询规划 → 240 多步检索 → 241 工具增强 → 242 引用验证
  ↓
243 Bad Case 调试（收束 RAG 质量）
  ↓
244 工作流模式 → 245 状态机 → 246 检查点 → 247 Temporal → 248 后台任务
```

## 刻意留白（本系列不讲）

- 向量库选型与索引调优（见 RAG 基础系列）
- 前端完整 UI 工程（248 给 Hook 骨架）
- Kubernetes / 多租户部署细节
- 微调 embedding 模型

## 环境速查

```bash
cd examples/rag-agent-lab
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # 239–242 需要

python main.py 243              # 无需 API
python main.py all --skip-api # 243 + 244
pip install temporalio && python temporal_minimal.py  # 247，需 Docker Temporal
```
