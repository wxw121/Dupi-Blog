# -*- coding: utf-8 -*-
"""Substantive expansions for tutorials 128-136 — unique per topic, not generic spam."""

EXPANSIONS = {
    "langchain-vectorstore": """

## 14. 工程深化：VectorStore 入库流水线

### 14.1 与 C 模块 ingest 脚本对齐

你在 [76 Chroma](76.chroma-vector-db-tutorial.md) 写过 `collection.upsert(ids=..., documents=..., metadatas=..., embeddings=...)`。迁到 LangChain 时，最容易丢的是 **业务主键 ids**。`from_documents` 默认用 UUID，导致与 [51 chunk_id](51.metadata-chunk-id-tutorial.md) 对不上，增量 [49](49.incremental-update-tutorial.md) 无法幂等。

**推荐做法**：始终显式传入 ids：

```python
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FakeEmbeddings

chunks = [...]  # 来自 130 Splitter
ids = [c.metadata["chunk_id"] for c in chunks]
Chroma.from_documents(
    documents=chunks,
    embedding=FakeEmbeddings(size=128),
    ids=ids,
    persist_directory="./chroma_db",
    collection_name="handbook_bge_v2",
)
```

验收：`collection.get(ids=["hb:v3:c001"])` 能 O(1) 回查；评测 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 时能按 chunk_id 对齐。

### 14.2 Embedding 批处理与速率限制

生产 ingest 不要 `for doc in docs: embed_one`。按 [67 批处理](67.embedding-batching-tutorial.md) 切 batch（32～128），并接 [69 重试与限速](69.embedding-retry-rate-limit-tutorial.md)。LangChain `Embeddings` 的 `embed_documents` 已按列表设计——你只需在 **外层** 控制 batch，不要在 VectorStore 内部逐条 add。

日志建议字段：`batch_idx, batch_size, embed_ms, upsert_ms, collection, model_version`。与 [147 LangSmith](147.langsmith-tracing-tutorial.md) 或 [148 Langfuse](148.langfuse-observability-tutorial.md) 的 ingest span 同名，方便一条 request_id 从 API 追到向量行。

### 14.3 多租户 collection 策略

[89 多租户](89.multi-tenant-namespace-tutorial.md) 有两种常见拆法：

| 策略 | 做法 | 适用 |
|------|------|------|
| 每租户一 collection | `tenant_{id}_v2` | 租户少、强隔离 |
| 单 collection + where | `metadata.tenant_id` | 租户多、运维简单 |

LangChain Chroma 的 `search_kwargs["filter"]` 传 `{"tenant_id": "t001"}`。注意 metadata 值类型与入库一致（§8.3）。**绝不在 prompt 里藏 tenant_id**——必须在 VectorStore 层过滤，与 [121 无权过滤](121.unauthorized-doc-filter-tutorial.md) 同构。

### 14.4 混合检索时 VectorStore 的角色

[93 混合检索](93.hybrid-search-tutorial.md) 里，VectorStore 通常只承担 **稠密路**。稀疏 BM25 可走 `BM25Retriever` + `EnsembleRetriever`（[127 篇](127.langchain-retriever-tutorial.md)）。VectorStore **不应** 内置 BM25——职责清晰才好测 Recall 归因（[151](151.bad-case-retrieval-miss-tutorial.md)）。

### 14.5 与 Parent-Document 模式

[65 Parent Document](65.parent-document-retriever-tutorial.md)：child 小块入 VectorStore；parent 全文在 SQL 或另一 store。metadata 写 `parent_id`，命中 child 后 **再取 parent** 拼进 [107 上下文预算](107.context-budget-tutorial.md)。LangChain 有 `ParentDocumentRetriever` 包装——底层仍是你理解的 VectorStore + docstore。

### 14.6 30 分钟巩固作业

1. 用 FakeEmbeddings 建 Chroma 与 FAISS，打印 `similarity_search_with_score` 前三条；  
2. 故意混用 embedding 维度，复现 §8.1 并修复；  
3. 写 `filter` 演示 ACL，对照 [53](53.metadata-acl-tutorial.md)；  
4. 画白板：ingest 与 query 两侧 Embedding 必须同一实例；  
5. wiki 记录：**本公司 collection 命名规范 + 换模型重建 SOP**。
""",

    "langchain-document-loader": """

## 14. 工程深化：Loader 与数据治理

### 14.1 metadata 契约与 [50-54] 系列对齐

Loader 是 **metadata 的第一次落点**。建议团队 JSON Schema 规定必填字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| doc_id | string | [50](50.metadata-doc-id-tutorial.md) 业务主键 |
| source | string | 路径或 URL [52](52.metadata-source-page-tutorial.md) |
| mime | string | 便于审计 |
| version | int | [48 版本](48.doc-versioning-tutorial.md) |
| acl_group | string | [53 ACL](53.metadata-acl-tutorial.md) |
| content_hash | string | [49 增量](49.incremental-update-tutorial.md) |

Loader 完成后 **立即校验**，缺字段拒绝进入 Splitter——比索引后才发现 cheap 得多。

### 14.2 与 [47 去重](47.doc-dedup-tutorial.md) 的衔接

DirectoryLoader 扫 NAS 常遇到 **同一制度多路径**（邮件附件 + 正式目录）。load 后按 `content_hash` 或 simhash 去重，只保留 `doc_id` 权威版本。去重在 Splitter **之前**，避免重复 chunk 浪费 [67 embed 批次](67.embedding-batching-tutorial.md)。

### 14.3 扫描件与 OCR 前置

[55 OCR](55.ocr-scanned-docs-tutorial.md) 不是 Loader 内置能力。流水线应是：`OCR 服务 → 写 searchable PDF/txt → TextLoader`。面试能说清：**Loader 读已 OCR 产物**，别把 OCR 塞进 VectorStore。

### 14.4 安全：路径遍历与宏病毒

- 用户上传文件名禁止 `../`；  
- docx/pdf 走沙箱转换（[40 docx](40.docx-office-parsing-tutorial.md)）；  
- 加载后文本过 [122 内容安全](122.content-safety-filter-tutorial.md) 再展示给运营预览。

### 14.5 Web Loader 合规

`WebBaseLoader` 抓外部站要注意 robots、版权、TLS。企业内部 wiki 用 **官方 API 导出 JSON** 优于裸爬 HTML——结构更稳，对接 [38 Markdown](38.markdown-parsing-tutorial.md) 或 [39 HTML](39.html-content-extraction-tutorial.md)。

### 14.6 与 [136 Parser 协议](136.pluggable-parser-splitter-embedder-tutorial.md)

Loader 可看作 Parser 的 **LangChain 适配器**。自研 `Parser.parse(path) -> RawDocument` 后，写薄包装 `class ParserLoader(BaseLoader)` 即可接入 LC 生态，同时保留 [135 混合架构](135.pipeline-vs-framework-tutorial.md) 的替换能力。

### 14.7 作业

1. 对 `data/` 下 md+pdf 跑 DirectoryLoader，统计每类 mime 数量；  
2. 实现 `content_hash` 跳过未变文件；  
3. 故意用错 encoding 复现 §8.1；  
4. 输出 JSONL 中间态（每行一个 Document 序列化）供数据组审计。
""",

    "langchain-text-splitter": """

## 14. 工程深化：切块策略与评测

### 14.1 与 [61 权衡](61.chunk-size-tradeoff-tutorial.md) 的量化调参

不要拍脑袋 `chunk_size=500`。准备二十条金标 QA（[143 Golden](143.golden-dataset-tutorial.md)），网格搜索 `size ∈ {300,500,800,1200}`、`overlap ∈ {0,50,100,150}`，记录 Recall@3 与平均 chunk 数（成本）。LangChain Splitter 改参数 **一行代码**，但 **索引必须重建**——在 [48 版本](48.doc-versioning-tutorial.md) 里记 `splitter_config_v3`。

### 14.2 中文与英文分隔符差异

递归分隔符 `["\\n\\n", "\\n", "。", "！", "？", " ", ""]` 对中文制度文档友好。英文技术 doc 加 `". "`、`"; "`。混合库可按 `metadata.lang` 选不同 Splitter 实例——注册表见 [136](136.pluggable-parser-splitter-embedder-tutorial.md)。

### 14.3 代码与技术文档

[62 结构感知](62.structure-aware-chunking-tutorial.md)：[63 Markdown AST](63.markdown-ast-chunking-tutorial.md) 先按标题切，再 RecursiveCharacter 细切，避免代码块从中间断开。`MarkdownHeaderTextSplitter` 输出的 metadata 带 `h1/h2`，利于 [88 元数据过滤](88.metadata-filter-retrieval-tutorial.md)（只搜某产品章节）。

### 14.4 Token 级切分与计费

对接 OpenAI embed 时，用 `TokenTextSplitter` + `tiktoken`，与 [27 Token 计费](27.token-counting-billing-tutorial.md)、[28 窗口](28.context-window-tutorial.md) 一致。字符切分可能导致 **单 chunk 超 token 上限**——embed API 报错或静默截断。

### 14.5 overlap 与 [106 检索去重](106.retrieval-dedup-tutorial.md)

overlap 过大，Top-K 常出现 **近邻重复 chunk**。检索侧用 MMR [105](105.mmr-diversity-tutorial.md) 或按 `doc_id+section` 去重。调参时同时看 **Recall 与冗余度**。

### 14.6 Splitter 输出审计

随机抽 50 chunk，人工看 **句界是否断裂、标题是否丢失**。Bad case 归因入口 [150 切块错误](150.bad-case-chunking-tutorial.md)。把断裂样例存入回归集 [144](144.regression-test-set-tutorial.md)。

### 14.7 作业

1. 同一文件：固定长度 [57] vs 递归 [58] diff 边界；  
2. Markdown 二级标题切块 + 细切流水线；  
3. 为每个 chunk 写 `chunk_id` 并验证唯一；  
4. 用金标一条问句，对比 overlap=0 与 overlap=80 的 Recall。
""",

    "llamaindex-index-types": """

## 14. 了解即可：延伸阅读与面试要点

### 14.1 StorageContext 与向量后端

LlamaIndex 通过 **StorageContext** 绑定 vector_store、docstore、index_store。概念上类似「[76 Chroma](76.chroma-vector-db-tutorial.md) 的 Collection + 可选 KV」——**了解即可**，知道 Index 不等于磁盘路径。

### 14.2 SummaryIndex / TreeIndex 何时出现

- **SummaryIndex**：文档总页数少、需要「通读摘要」_demo；  
- **TreeIndex**：层次化手册实验、研究型项目；  
- 生产制度问答 **90% 用 VectorStoreIndex** 即可，别为面试背全 API。

### 14.3 ComposableGraph

多知识库合并：子 Index 各管一库，上层 Graph 路由。**复杂度高**，与 [89 多租户](89.multi-tenant-namespace-tutorial.md) 结合时要评估延迟。了解即可：知道名词，主线仍看 LangChain [127](127.langchain-retriever-tutorial.md)。

### 14.4 与 LangChain 映射复习

| 面试题 | 简答 |
|--------|------|
| LI Node 是什么 | 带关系的文本单元，类似增强版 Document |
| VectorStoreIndex | 构建时 embed 并写入向量后端 |
| 你会迁移吗 | 主栈 LC；LI 作对照阅读 |

### 14.5 动手边界（了解即可）

安装 `llama-index` 跑通 §5 即可，不必部署 LlamaCloud。时间留给 [128-130 LC](128.langchain-vectorstore-tutorial.md) 与 [135 架构取舍](135.pipeline-vs-framework-tutorial.md)。

### 14.6 推荐阅读

官方文档「Understanding」「Indexing」两章；对照本篇 §10 映射表做笔记，**不超过 2 小时**。
""",

    "llamaindex-query-engine": """

## 14. 了解即可：Query Engine 深入对照

### 14.1 Response 对象里有什么

`response.response` 是答案文本；`source_nodes` 含 `node_id、score、metadata`——对应 [34 Grounding](34.grounding-citation-tutorial.md)。**了解即可**：对比 LC 链里你手写的 `format_docs` + citations 列表，结构类似。

### 14.2 response_mode 选型

| 模式 | 行为 | 风险 |
|------|------|------|
| compact | 压缩进单次 LLM | 长上下文贵 |
| tree_summarize | 分层摘要 | 延迟高 |
| refine | 多轮 refine | 成本叠加 |

企业固定 RAG 更常用 **固定模板** [110](110.rag-prompt-template-tutorial.md) + LCEL，而不是 LI 黑盒 synthesizer——了解差异即可。

### 14.3 ChatEngine 与 [118 多轮](118.multi-turn-history-tutorial.md)

多轮场景 LI 提供 ChatEngine；LC 用 history + [109 查询增强](109.conversation-query-enhancement-tutorial.md)。**每轮是否重检索** 是产品决策，与框架无关。

### 14.4 流式

`streaming=True` 时逐 token；对接前端见 [116 SSE](116.sse-rag-streaming-tutorial.md)、[174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)。了解即可。

### 14.5 面试话术

「我熟 LangChain LCEL 组装检索与生成；了解 LlamaIndex Query Engine 的一站式 API 与 source_nodes，能在读开源项目时快速定位检索段。」
""",

    "llamaindex-agent": """

## 14. 了解即可：Agent 风险与治理

### 14.1 迭代预算

生产 Agent 必设：`max_iterations=3～5`、单次 tool `timeout=30s`、总 `deadline=120s`。与 [124 Function Calling](124.function-calling-tool-use-tutorial.md) 相同纪律。

### 14.2 工具 ACL

`QueryEngineTool` 内部 Retriever 必须带 [121](121.unauthorized-doc-filter-tutorial.md) 过滤。Agent 选错工具或参数时，**最后一道闸** 仍在工具实现里。

### 14.3 观测

记录每轮：`thought` 摘要（勿存 PII）、`tool_name`、`latency_ms`、`chunk_ids`。对接 [147-148 追踪](147.langsmith-tracing-tutorial.md)。

### 14.4 与固定管道对比

| 维度 | 固定 RAG | Agent |
|------|----------|-------|
| 延迟 | 低 | 高 |
| 可预测性 | 高 | 低 |
| 多跳 | 需 [104 设计](104.multi-hop-retrieval-tutorial.md) | 模型自规划 |
| 合规审计 | 易 | 难 |

**了解即可**：默认固定管道；Agent 用于探索型 PoC。

### 14.5 面试话术

「知道 LlamaIndex Agent 与 QueryEngineTool；生产优先可控检索链，Agent 需严格迭代上限与工具 ACL。」
""",

    "haystack-pipeline": """

## 14. 了解即可：从 Haystack 借鉴什么

### 14.1 显式图的价值

Haystack `connect(output, input)` 强制 **端口类型匹配**，接错线在编译期失败。自研 DAG（[135](135.pipeline-vs-framework-tutorial.md)）可借鉴：**边带 schema 名**，如 `documents: list[Chunk]`。

### 14.2 序列化与 [138 配置驱动](138.config-driven-pipeline-tutorial.md)

Pipeline YAML 导出后，运维可改 `top_k` 而不发版。LangChain 可用配置生成 LCEL，思想同源——**了解 Haystack 的动机** 即可设计自家 `pipeline.yaml`。

### 14.3 组件单测

每个 Component 单独 `run()` 测输入输出，比整条链黑盒测易定位 [149-152 Bad Case](149.bad-case-parsing-tutorial.md)。

### 14.4 与混合检索

Haystack 教程常见 **双 Retriever + Joiner**（[94 RRF](94.rrf-fusion-tutorial.md)）。图上一眼可见稠密/稀疏两路——适合画给架构评审。

### 14.5 不必全盘迁移

团队主栈 LC 时，把 Haystack 当 **设计模式参考**：[134 本篇] + [135 取舍] 足够。

### 14.6 作业（了解即可）

手绘 ingest 与 query 两张 Haystack 风格图，并各画一张等价 LCEL 链，标注差异。
""",

    "pipeline-vs-framework": """

## 14. 工程深化：组织落地与案例

### 14.1 案例 A：创业公司 PoC

- **0-3 月**：LangChain [126 LCEL](126.langchain-lcel-tutorial.md) + [76 Chroma](76.chroma-vector-db-tutorial.md) 验证业务；  
- **3-6 月**：抽出 [136 Parser/Splitter](136.pluggable-parser-splitter-embedder-tutorial.md)，因 PDF 格式多；  
- **6-12 月**：检索换自研 Hybrid（[93](93.hybrid-search-tutorial.md)），编排仍 LC；  
- **原则**：金标 [143](143.golden-dataset-tutorial.md) 守门，每次替换跑 [139-142 RAGAS](141.ragas-faithfulness-tutorial.md)。

### 14.2 案例 B：金融合规

- ACL [121](121.unauthorized-doc-filter-tutorial.md)、审计日志 **自研**；  
- LLM 调用走统一网关 [167](167.openai-api-wrapper-tutorial.md)；  
- 框架仅用于 **开发环境原型**，生产链路与框架解耦。

### 14.3 技术债信号

| 信号 | 动作 |
|------|------|
| 升级 LC 断链 | pin 版本 + 抽接口 |
| on-call 不懂 Chroma 原生 | 培训 [76][128] |
| 同一请求双框架 | 立规：单路径 |
| 无金标 | 停功能上线 |

### 14.4 PR Review 问题清单

1. 本 PR 引入的框架边界在哪？  
2. 能否两周内剔框架？  
3. 是否新增 metadata 字段并更新 Schema？  
4. 是否跑回归集 [144](144.regression-test-set-tutorial.md)？  
5. 观测 span 是否完整 [147](147.langsmith-tracing-tutorial.md)？

### 14.5 与 E 模块评测衔接

架构取舍不是空谈——用 [153 A/B](153.ab-experiment-rag-tutorial.md) 对比「纯 LC」与「自研检索 + LC 编排」，用数据写 wiki。

### 14.6 60 分钟工作坊模板

见 §9。产出物：`ARCHITECTURE.md` 一页、分层表、回滚预案、负责人签名。
""",

    "pluggable-parser-splitter-embedder": """

## 14. 工程深化：协议治理与测试

### 14.1 工厂与配置

```python
def build_pipeline(cfg: dict):
    parser = REGISTRY["parser"][cfg["parser"]]
    splitter = REGISTRY["splitter"][cfg["splitter"]]
    embedder = REGISTRY["embedder"][cfg["embedder"]]
    assert embedder.dimension == cfg["vector_dim"]
    return parser, splitter, embedder
```

配置来自 [138 YAML](138.config-driven-pipeline-tutorial.md)；`vector_dim` 与 [76 Chroma](76.chroma-vector-db-tutorial.md) collection 一致。

### 14.2 契约测试（Contract Test）

每个 Parser 实现：对 `tests/fixtures/sample.pdf` 断言 `doc_id` 存在、文本非空。每个 Splitter：对固定输入断言 chunk 数范围、chunk_id 唯一。每个 Embedder：断言 `len(vec)==dimension`、同一文本两次 embed 一致（确定性 fake）或余弦=1（真实模型批处理）。

### 14.3 版本 manifest

索引任务结束写 `manifest.json`：

```json
{
  "parser": "pymupdf_v2",
  "splitter": "recursive_500_80",
  "embedder": "bge-m3_v1",
  "chunk_count": 12034,
  "created_at": "2026-07-11T00:00:00Z"
}
```

与 [48 文档版本](48.doc-versioning-tutorial.md)、[154 参数版本](154.param-version-management-tutorial.md) 衔接。

### 14.4 错误处理

Parser 失败：**单文件跳过 + 死信队列**（路线图 163）；不要拖垮整批 NAS 扫描。Splitter 产出空列表：打 warn 并记 [149 解析归因](149.bad-case-parsing-tutorial.md)。

### 14.5 与 [137 下游三件套](137.pluggable-store-retriever-generator-tutorial.md)

数据入口三件套（本篇）产出 `Chunk + vector`；下游 Store 写入 [75 FAISS](75.faiss-ann-tutorial.md)/[76 Chroma](76.chroma-vector-db-tutorial.md)，Retriever 读，Generator 生成——**全链路可替换**。

### 14.6 LangChain 适配器清单

| 协议 | LC 类 |
|------|-------|
| Parser | 自定义 BaseLoader |
| Splitter | TextSplitter 子类或包装 |
| Embedder | Embeddings 子类 |

适配器 **薄**，逻辑仍在协议实现，方便单元测试不依赖 LC。

### 14.7 作业

1. 实现 `REGISTRY` 与 `build_pipeline`；  
2. 加第二个 `PlainTextParser` 与 `MarkdownParser` 占位；  
3. 写一条契约测试；  
4. 画全链：Parser→Splitter→Embedder→[128 VectorStore](128.langchain-vectorstore-tutorial.md)。
""",
}
