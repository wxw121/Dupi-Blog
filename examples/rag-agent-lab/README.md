# RAG Agent Lab

系列 **239–243** 的可运行最小示例，对应 `src/posts/ai-ml/` 各篇 §最小可运行示例。

## 环境

```bash
cd examples/rag-agent-lab
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # 239–242 需要；243 不需要
```

## 运行

```bash
# 单篇
python demo_query_planning.py
python demo_bad_case.py          # 无需 API
python demo_sequential_workflow.py  # 244 顺序链，无需 API

# 或统一入口
python main.py 243               # 按编号
python main.py 244               # 工作流顺序链
python main.py all --skip-api    # 243 + 244

# 247 Temporal（需 Docker + pip install temporalio）
python temporal_minimal.py
```

| 脚本 | 对应篇目 | 需要 API |
|------|----------|----------|
| `demo_query_planning.py` | 239 查询规划 | 是 |
| `demo_multi_step.py` | 240 多步检索 | 是 |
| `demo_tool_rag.py` | 241 工具增强 | 是 |
| `demo_citation_verify.py` | 242 引用验证 | 是 |
| `demo_bad_case.py` | 243 Bad Case 调试 | 否 |
| `demo_sequential_workflow.py` | 244 顺序链工作流 | 否 |
| `temporal_minimal.py` | 247 Temporal 最小验证 | 否（需 Docker Temporal） |

## 建议学习顺序

239 → 240 → 241 → 242 → 243 → 244（检索链 → 多步 → 工具 → 引用 → 调试 → 编排）

系列总览见 [`agent-rag-series-238-254.md`](../../src/posts/ai-ml/agent-rag-series-238-254.md)（已扩展至 238–254；Part 7 见 [`../agent-platform/`](../agent-platform/)）。
