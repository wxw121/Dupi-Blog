# -*- coding: utf-8 -*-
"""Third-pass expansions 128-136."""

EXPANSIONS3 = {
    "langchain-vectorstore": """## 18. 版本锁定与 LangChain 升级策略

### 18.1 VectorStore 是升级断链高发区

LangChain 生态迭代快：`langchain_community.vectorstores.Chroma` 的 import 路径、`persist()` 是否必要、`filter` 语法在 minor 版本间都可能变化。企业应 **锁定** `langchain-core`、`langchain-community`、`chromadb` 版本，经 [144 回归集](144.regression-test-set-tutorial.md) 验证后再 bump。升级时对比同一 query 的 `chunk_id` Top-K 是否与旧版一致；若集合变化，优先查 Embedding 默认实现是否被换。

### 18.2 双轨排障表

| 现象 | LC 层 | 原生层 |
|------|-------|--------|
| 结果为空 | search_kwargs、filter | collection.count() |
| ACL 泄露 | as_retriever filter | metadata 类型 |
| 重启空库 | persist_directory | 磁盘权限 |

on-call 必须会 [76 Chroma](76.chroma-vector-db-tutorial.md) 原生 API，不能只会 `similarity_search`。见 [135 框架取舍](135.pipeline-vs-framework-tutorial.md)。

### 18.3 Milvus/Qdrant 迁移预留

若在 [137 Store](137.pluggable-store-retriever-generator-tutorial.md) 已定义存储协议，LangChain 类放 `adapters/`，核心域只依赖协议。换后端时改适配器 + 重建索引，LCEL 链改动最小。

## 19. 观测、成本与 SLO

### 19.1 检索 span 最小字段

记录 `collection_name`、`embed_model`、`k`、`hit_ids`、`top1_score`、`latency_ms`、`index_version`（[147 LangSmith](147.langsmith-tracing-tutorial.md)、[148 Langfuse](148.langfuse-observability-tutorial.md)）。支撑 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 归因。

### 19.2 成本与批处理

ingest 成本在 embed（[67 批处理](67.embedding-batching-tutorial.md)、[27 Token](27.token-counting-billing-tutorial.md)）与磁盘。评审时给出「每十万 chunk」的 embed 美元数与目录体积，避免 PoC 账单击穿。

### 19.3 SLO 与降级

检索 P99 超时可降 k、关 MMR、换小模型（独立 collection），或 [112 拒答](112.refusal-strategy-tutorial.md)。降级写入 [154 参数版本](154.param-version-management-tutorial.md)。

## 20. 交付清单与面试闭环

### 20.1 上线勾选

Chroma+FAISS 冒烟；ids=chunk_id；ACL 自动化；LCEL 最小链；manifest 规范；§8 先错对对四条。

### 20.2 阅读顺序

125 Document → 129 Loader → 130 Splitter → 本篇 → 127 Retriever → 126 LCEL，对照 76/75 原生。

### 20.3 面试 60 秒

统一 Chroma/FAISS 入库与搜索，chunk_id 幂等，ACL 在检索层，观测记 hit_ids，换 embed 新建 collection，排障下沉原生 API。

## 21. 多副本发布与深度 FAQ

蓝绿：新索引写 `chroma_vNEXT`，校验后切指针（[162 幂等](162.idempotent-reindex-tutorial.md)）。监控 collection 行数与磁盘，异常激增查重复 ingest。与 [89 多租户](89.multi-tenant-namespace-tutorial.md) 压测 where 性能。

**FAQ 补充**：多进程写 Chroma 建议单 writer（[159 队列](159.celery-async-queue-tutorial.md)）。Chroma 与原生 client 混用需同源 embed。MMR 与 rerank 看延迟二选一或串联前 20 条。OpenAI 换维必新 collection（[25](25.embedding-vector-tutorial.md)）。""",
    "langchain-document-loader": """## 18. 企业数据源与同步模式

SharePoint 用 Graph API 拉文件再 Parser；Confluence 用 REST 导出 Markdown；Git 用 CI tarball + DirectoryLoader。metadata 必含 `source_system`、`external_id`、`synced_at`，对接 [49 增量](49.incremental-update-tutorial.md)。Loader 不解析业务字段，只保证 `page_content` 与稳定 `doc_id`。[89 多租户](89.multi-tenant-namespace-tutorial.md) 下 `root` 按 tenant 隔离，禁止用户输入拼 glob。大规模任务用 [159 Celery](159.celery-async-queue-tutorial.md)，单文件失败进 [163 死信](163.retry-dead-letter-tutorial.md)。

## 19. 格式边界与安全

复杂 PDF 表格走 [37 版式](37.pdf-layout-tables-tutorial.md) Parser sidecar，Loader 只载正文流。[40 docx](40.docx-office-parsing-tutorial.md) 沙箱解析，拒绝宏。[39 HTML](39.html-content-extraction-tutorial.md) 用选择器去导航噪声。用户上传防 `../`；加载后过 [122 安全](122.content-safety-filter-tutorial.md)。WebLoader 遵守 robots，内部 wiki 优先 API 导出。

## 20. 交付与面试

勾选：三格式 load、Schema 校验、content_hash 增量、JSONL 审计、与 [130 Splitter](130.langchain-text-splitter-tutorial.md) 联调。面试：Loader 统一 Document 与 metadata，增量 hash，复杂 PDF 交 Parser，编码 UTF-8 规范化，Celery 幂等 ingest。
## 21. 运营 KPI 与排障

跟踪空文本率、乱码率、metadata 缺字段率，联动 [149 解析](149.bad-case-parsing-tutorial.md)。空文本→[55 OCR](55.ocr-scanned-docs-tutorial.md)；乱码→[41 编码](41.text-encoding-detection-tutorial.md)。Loader 后运营 preview 再进 Splitter（[46 清洗](46.text-cleaning-tutorial.md)）。

**FAQ**：DirectoryLoader 务必 exclude `node_modules`。Git 只索引默认分支。CMS 用 API 优于 WebLoader。Loader vs Parser：IO 与 Document 列表 vs 版式解析（[136](136.pluggable-parser-splitter-embedder-tutorial.md)）。""",
    "langchain-text-splitter": """## 18. 切块决策树

有 Markdown 标题 → Header Splitter + Recursive；纯条文 → Recursive 中文分隔符；API 文档 → 按 `##` 且代码块不拆。法条含「第一条」「（一）」——分隔符加 `"。」"`。Parent 模式 child 256-400，metadata 写 `parent_id`（[65](65.parent-document-retriever-tutorial.md)）。

## 19. 金标调参与 bad case

网格记录 size/overlap 与 Recall@5、chunk 数、embed 成本（[143 金标](143.golden-dataset-tutorial.md)）。改参数写入 [154 版本](154.param-version-management-tutorial.md)，**重建索引**。与 [150 切块 bad case](150.bad-case-chunking-tutorial.md)、[144 回归](144.regression-test-set-tutorial.md) 联动。overlap 与 [106 去重](106.retrieval-dedup-tutorial.md)、[105 MMR](105.mmr-diversity-tutorial.md) 联合评估。

## 20. 交付与面试

diff 固定 vs 递归；Markdown 标题 demo；chunk_id 唯一；overlap 对比实验。面试：金标调 size/overlap，中文分隔符，改参必重建，与 MMR 去重一起评。
## 21. Token 切分与代码文档

OpenAI embed 用 `TokenTextSplitter`+tiktoken（[27](27.token-counting-billing-tutorial.md)）。技术 doc 用 [63 Markdown AST](63.markdown-ast-chunking-tutorial.md) 保代码块完整。随机抽 50 chunk 人工审句界（[150](150.bad-case-chunking-tutorial.md)）。

**FAQ**：`chunk_size` 是字符不是 token。`MarkdownHeaderTextSplitter` 保留 h1/h2 metadata 供 [88 过滤](88.metadata-filter-retrieval-tutorial.md)。改 overlap 要重建索引。与 [128](128.langchain-vectorstore-tutorial.md) 联调验证 chunk_id 入库。""",
    "llamaindex-index-types": """## 18. VectorStoreIndex 构建（了解）

`from_documents` 同步 embed 写入，大库应分批 insert（[67 批处理](67.embedding-batching-tutorial.md)）。Node 可带 relationships，对比 [125 Document](125.langchain-core-tutorial.md)。`storage_context` 可绑 Chroma/Qdrant（[76](76.chroma-vector-db-tutorial.md)），主栈 LC 时不必双部署。

## 19. 非向量索引边界

SummaryIndex 仅适合短文 demo；TreeIndex 实验性层次检索；KeywordTableIndex 类似 [92 稀疏](92.sparse-retrieval-rag-tutorial.md)。生产 **90% VectorStoreIndex**。ComposableGraph 多库合并复杂，了解名词即可。

## 20. 学习包与面试

两小时：官方 Indexing 章 + 本篇 §5 demo + §10 映射表。迁移：Node→Document，`as_query_engine`→LCEL。面试：主线 LC；了解 LI 索引类型，能读 LI 代码不对生产双栈。
## 21. 面试对照表扩展

| LI | LC |
|----|-----|
| VectorStoreIndex | VectorStore + from_documents |
| Node | Document |
| storage_context | persist_directory |
| as_query_engine | as_retriever + LCEL |

**FAQ**：不必部署 LlamaCloud 学本篇。LI 与 LC 不要双路径生产。Graph 索引了解即可。时间留给 [128-130](128.langchain-vectorstore-tutorial.md)。""",
    "llamaindex-query-engine": """## 18. RetrieverQueryEngine（了解）

`RetrieverQueryEngine.from_args` = retriever + synthesizer，对照 LC `retriever | prompt | llm`。`node_postprocessors` 类似 [99 阈值](99.score-threshold-tutorial.md)、[106 去重](106.retrieval-dedup-tutorial.md)。`SubQuestionQueryEngine` 类似 [103 分解](103.query-decomposition-tutorial.md)。

## 19. 流式与引用

`streaming=True` 对接 [116 SSE](116.sse-rag-streaming-tutorial.md)、[174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)。`source_nodes` 映射 [113-115 引用](113.inline-citation-tutorial.md)、[176 卡片](176.citation-card-ui-tutorial（front-end）.md)。LC 从 retriever 手写 citations，产品行为一致。

## 20. 选型与面试

固定链用 LCEL + [147 追踪](147.langsmith-tracing-tutorial.md)；需细粒度 rerank/预算用 LC。了解 LI 一站式 API 与 postprocessor。面试：熟 LCEL 分步；了解 Query Engine 与 source_nodes 对应关系。
## 21. response_mode 与成本

compact/tree_summarize/refine 成本高，企业常用固定 [110 prompt](110.rag-prompt-template-tutorial.md)+LCEL。ChatEngine 多轮见 [118 历史](118.multi-turn-history-tutorial.md)；每轮是否重检索是产品决策。

**FAQ**：`aquery` 对接 FastAPI async（[156](156.fastapi-project-structure-tutorial.md)）。source_nodes 分数不可跨模型比。了解档也要能画检索+合成两框图。""",
    "llamaindex-agent": """## 18. ReAct 与工具（了解）

ReActAgent 同构 [124 Function Calling](124.function-calling-tool-use-tutorial.md)。QueryEngineTool 的 description 要写适用/禁止场景；工具内 Retriever 强制 [121 ACL](121.unauthorized-doc-filter-tutorial.md)。多工具路由类似多库，默认单库固定 RAG。

## 19. 生产风险

每轮迭代 = LLM + 可能检索，设 `max_iterations` 与 deadline（[148 Langfuse](148.langfuse-observability-tutorial.md) 看成本）。合规场景要固定可回放管道（[135](135.pipeline-vs-framework-tutorial.md)）。工具参数 schema 校验，防编造 doc_id。

## 20. 学习与面试

动手 ≤1h 跑 ReActAgent，然后回 [127 固定链](127.langchain-retriever-tutorial.md)。对比 [104 多跳](104.multi-hop-retrieval-tutorial.md)：固定管道可控，Agent 灵活难审计。面试：了解 Agent；生产固定 RAG + ACL + 迭代预算。
## 21. 观测与工具 ACL

每轮记 tool_name、latency、chunk_ids（[147](147.langsmith-tracing-tutorial.md)）。QueryEngineTool 内 filter 强制 tenant/ACL。幻觉工具参数用 schema 拒绝并返回错误 observation。

**FAQ**：Agent 默认不对外 SLA。与固定 [104 多跳](104.multi-hop-retrieval-tutorial.md) 比可控性。max_iterations 3-5 常见。生产探索用，客服用固定链。""",
    "haystack-pipeline": """## 18. Haystack 2 组件（了解）

Component 显式端口，`Pipeline.connect` 编译期检查。Document Store 双写类似 [82 ES](82.elasticsearch-vector-tutorial.md)+向量。`pipeline.yaml` 序列化动机同 [138 配置](138.config-driven-pipeline-tutorial.md)。

## 19. 可借鉴设计

组件单测 `run(**inputs)`；架构图给评审；DocumentJoiner 对照 [94 RRF](94.rrf-fusion-tutorial.md)。LC 用 EnsembleRetriever 或自研 fusion。

## 20. 结论与面试

主栈 LC 时学 DAG+单测+配置化，不迁 Haystack。手绘 Haystack 图与 LCEL 等价图。面试：熟 LCEL；了解 Component/connect，用于自研 DSL 与评审。
## 21. 与自研 DSL

借鉴 connect 端口名与 schema，设计 `pipeline.yaml` 边：`documents: list[Chunk]`（[135](135.pipeline-vs-framework-tutorial.md)）。Haystack 测试目录值得浏览，不必引依赖。

**FAQ**：Haystack 2 与 1.x API 不同，读文档看版本。混合检索图画法可复用到 LC 架构评审。了解档不等于生产引入。""",
    "pipeline-vs-framework": """## 18. 分层矩阵扩展

Parser：PoC 用 LC Loader，成长期自研+适配。Retriever：后期常自研 Hybrid（[93](93.hybrid-search-tutorial.md)）。编排：LCEL 或 [138 配置](138.config-driven-pipeline-tutorial.md)。变更频繁处配置化；ACL/审计自研。供应商锁定评估：数据可导出，[136-137 协议](137.pluggable-store-retriever-generator-tutorial.md) 两周剔框架。

## 19. 组织治理

PR 门禁：框架边界、回归、trace、Schema。培训 on-call 原生 [76][128]。法务/产品共识：ARCHITECTURE 表译风险/速度/成本。

## 20. 三阶段演进

Phase1 LC+Chroma；Phase2 自研 Parser/Retriever；Phase3 配置驱动。每阶段 [143 金标](143.golden-dataset-tutorial.md)+[141 Faithfulness](141.ragas-faithfulness-tutorial.md)+[153 A/B](153.ab-experiment-rag-tutorial.md)。面试：模块决策表，ACL 自研，可插拔防锁定，单栈纪律。
## 21. 技术债与 A/B

双框架并行、无金标上线、on-call 不懂存储——冻结功能还债。用 [153 A/B](153.ab-experiment-rag-tutorial.md) 对比纯 LC vs 自研检索+LC 编排，数据写 wiki。

**FAQ**：全自研/全框架都少见。Prompt 层适合配置。索引层常坚持原生 API 可排障。Haystack/LI 作设计参考不并行请求。""",
    "pluggable-parser-splitter-embedder": """## 18. 协议细化

Parser→RawDocument；Splitter→Chunk（保留 doc_id/acl）；Embedder→dimension 与 [76 Chroma](76.chroma-vector-db-tutorial.md) 一致。`schema_version` bump 触发重建（[48 版本](48.doc-versioning-tutorial.md)）。

## 19. Registry 与契约

REGISTRY + build_pipeline（[138 YAML](138.config-driven-pipeline-tutorial.md)）。契约测试 fixtures：Parser 非空、chunk_id 唯一、embed 维度。FakeEmbedder 供 CI。失败进 [163 死信](163.retry-dead-letter-tutorial.md)。

## 20. 全链与面试

ingest: parse→split→embed→[137 Store](137.pluggable-store-retriever-generator-tutorial.md)。LC 适配器 ≤80 行。manifest 样例 + ADR。面试：三 Protocol + Registry + manifest；LC 薄适配；换 embed 新 collection。
## 21. HTTP 边界与 C 轨映射

独立 Parser 团队可 HTTP 返回 RawDocument；消费方 Adapter 进 Registry。57-65 切块系列对应 REGISTRY 各 key（[58 递归](58.recursive-character-chunking-tutorial.md) 等）。

**FAQ**：换 Parser 不改 Splitter 单测。换 Embedder 必新 collection。契约测试进 CI 比线上 [150](150.bad-case-chunking-tutorial.md) 便宜。下游见 [137](137.pluggable-store-retriever-generator-tutorial.md)。""",
}