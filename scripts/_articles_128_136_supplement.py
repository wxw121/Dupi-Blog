# -*- coding: utf-8 -*-
"""Clean substantive supplement — one block per slug, no numbered spam."""

SUPPLEMENT = {
    "langchain-text-splitter": """

## 14. 与 C 模块切块实验报告模板

完成 [58 递归切块](58.recursive-character-chunking-tutorial.md) 手写版与 `RecursiveCharacterTextSplitter` 对照后，用下表记录结果（贴团队 wiki）：

| 指标 | 手写 | LangChain | 备注 |
|------|------|-----------|------|
| chunk 数 | | | |
| 平均长度 | | | |
| 金标 Recall@5 | | | |
| 句界断裂样例数 | | | |

**判定**：Recall 差距 <5% 且断裂样例可接受 → 采用 LC Splitter 并注册到 [136 协议](136.pluggable-parser-splitter-embedder-tutorial.md)；否则保留自研或混合（标题用 LC、正文用手写）。

**参数发布**：`chunk_size / overlap / separators` 写入 [154 参数版本](154.param-version-management-tutorial.md)，与索引 manifest 绑定。改参触发 [48 文档版本](48.doc-versioning-tutorial.md) 全量重建，禁止只改在线 `k`。
""",

    "llamaindex-index-types": """

## 14. 了解即可：Index 类型一张表背完

| Index | 一句话 | 生产默认？ |
|-------|--------|------------|
| VectorStoreIndex | 向量语义检索 | 是（LI 侧） |
| SummaryIndex | 串联/摘要短文 | 否 |
| TreeIndex | 树状层次摘要 | 否 |
| KeywordTableIndex | 关键词表 | 罕用 |
| ComposableGraph | 多 Index 组合 | 慎 |

**与 [128 LC VectorStore](128.langchain-vectorstore-tutorial.md) 差异记忆**：LI 常在 **构建 Index 时** embed；LC 常在 **VectorStore.add** 时 embed。构建时机不同 → 性能剖析与失败点不同，不是「谁更先进」。

**学习预算**：本篇 1h + [132](132.llamaindex-query-engine-tutorial.md) 1h + [133](133.llamaindex-agent-tutorial.md) 1h；其余时间给 [127 Retriever](127.langchain-retriever-tutorial.md) 与 [135 取舍](135.pipeline-vs-framework-tutorial.md)。路线图 [148] 条勾选标准：**能画主路径 + 填映射表 + 声明主栈 LangChain**。
""",

    "llamaindex-query-engine": """

## 14. 了解即可：Query Engine 与 LCEL 对照实验

同一批 Document、同一 embed、同一 LLM，跑两条路径：

- **A**：`index.as_query_engine().query("年假几天？")`  
- **B**：[127 Retriever](127.langchain-retriever-tutorial.md) + [126 LCEL](126.langchain-lcel-tutorial.md) + [110 模板](110.rag-prompt-template-tutorial.md)

记录：延迟、token、`source_nodes` 与手写 citations [113](113.inline-citation-tutorial.md) 可控性。多数团队选 **B**——便于插 [96 精排](96.bge-reranker-tutorial.md)、[107 预算](107.context-budget-tutorial.md)、[121 ACL](121.unauthorized-doc-filter-tutorial.md)、[147 追踪](147.langsmith-tracing-tutorial.md)。

**response_mode 了解即可**：`compact / tree_summarize / refine` 影响成本与延迟；生产更常用手写 LCEL 控制进 prompt 的块列表，而非黑盒 synthesizer。

**source_nodes**：对应 [34 Grounding](34.grounding-citation-tutorial.md)；前端 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) 需要稳定 `chunk_id`，无论数据来自 LI 还是 LC。

**面试 30 秒**：「熟 LCEL 分步链；了解 Query Engine 一站式 API 与 source_nodes，能读 LI 项目，生产默认可审计的 LangChain 管道。」
""",

    "llamaindex-agent": """

## 14. 了解即可：Agent 决策矩阵与治理

| 场景 | 固定 RAG [126] | Agent |
|------|------------------|-------|
| 单库 FAQ | 默认 | 过度 |
| 多库路由实验 | 意图 + 多 Retriever | QueryEngineTool |
| 合规审计 | 优 | 劣 |
| 延迟/成本 | 低 | 高 |

**治理六条**（与 [124 Function Calling](124.function-calling-tool-use-tutorial.md) 同构）：`max_iterations`、总 deadline、工具内 [121 ACL](121.unauthorized-doc-filter-tutorial.md)、schema 校验、`description` 写清禁止场景、trace 记 `tool_name` 与 `chunk_ids` [147](147.langsmith-tracing-tutorial.md)。

**默认立场**：对外制度/财务 QA 走固定链；Agent 仅内部探索。路线图 [150] 完成标志：**口述三风险（延迟、成本、失控）+ ReAct 流程图 + 对比 [104 多跳](104.multi-hop-retrieval-tutorial.md) 固定管道**。
""",

    "haystack-pipeline": """

## 14. 了解即可：三张图映射本系列

**Ingest**：FileConverter → Splitter → Embedder → Writer → [129][130][25][128](128.langchain-vectorstore-tutorial.md)。

**Query**：Embedder → Retriever → (Ranker) → PromptBuilder → Generator → [127][96][110][126](126.langchain-lcel-tutorial.md)。

**Hybrid**：BM25 + Dense → Joiner([94 RRF](94.rrf-fusion-tutorial.md)) → [93 混合](93.hybrid-search-tutorial.md)。

Haystack 价值是 **显式 DAG 可评审、可序列化**（动机同 [138 配置驱动](138.config-driven-pipeline-tutorial.md)），不必引入第二框架。自研 FastAPI [156](156.fastapi-project-structure-tutorial.md) 可导出 `pipeline.json` 供合规存档。

**面试**：「熟 LCEL；了解 Haystack Component-Connection 拓扑，借鉴单测与配置化思想。」
""",

    "pipeline-vs-framework": """

## 14. 架构评审：PR 五问模板

1. 本 PR 触及哪一层（Parser / Store / Retriever / 编排 / API）？  
2. 是否引入新框架依赖？能否两周内剔回自研？  
3. metadata / chunk_id Schema 是否更新并版本化 [50-51](51.metadata-chunk-id-tutorial.md)？  
4. 是否跑 [143 金标](143.golden-dataset-tutorial.md) / [144 回归](144.regression-test-set-tutorial.md)？  
5. trace 是否覆盖检索 hit_ids [147](147.langsmith-tracing-tutorial.md)？

**回滚条件示例**：Faithfulness [141](141.ragas-faithfulness-tutorial.md) 降 ≥5% 或 p95 延迟升 ≥30% → feature flag 切 legacy pipeline [154](154.param-version-management-tutorial.md)。

**战术组合（常见）**：LC [126] 编排 + 自研 HybridRetriever [93] + Chroma 原生 [76] + [136 三协议](136.pluggable-parser-splitter-embedder-tutorial.md)。
""",

    "pluggable-parser-splitter-embedder": """

## 14. 契约测试与 manifest 样例

**契约测试**（CI，无 live API）：每个 Parser 对 `fixtures/sample.md` 断言 `doc_id`；每个 Splitter 断言 chunk 数范围与 `chunk_id` 唯一；每个 Embedder 断言 `len(vec)==dimension`。

**manifest.json 样例**：

```json
{
  "parser": "plain_text_v1",
  "splitter": "recursive_500_80",
  "embedder": "fake_128_v1",
  "chunk_count": 42,
  "schema_version": 2,
  "created_at": "2026-07-11T00:00:00Z"
}
```

与 [137 Store/Retriever/Generator](137.pluggable-store-retriever-generator-tutorial.md) 衔接后，ingest 链变为：`parse → split → embed → store.write`。换 embedder **major** → 新 collection [76](76.chroma-vector-db-tutorial.md)，旧库只读 [48](48.doc-versioning-tutorial.md)。

**LC 适配原则**：`BaseLoader / TextSplitter / Embeddings` 薄包装 ≤80 行；协议实现可单测不依赖 LangChain [135](135.pipeline-vs-framework-tutorial.md)。
""",
}
