# 开发面试题索引（254 篇）

> 面向 **后端 / AI 应用开发** 岗位：概念、设计、实现、排障、生产化。
> 由 `scripts/generate_interview_questions.py` 从教程 **技术内容** 提炼，可重复生成。

---

## 模块导航

| 模块 | 编号 |
|------|------|
| 基础前置 | 1–16 |
| RAG 数据采集 | 17–62 |
| Embedding 与索引 | 63–92 |
| 检索与生成 | 93–124 |
| 框架与评测 | 125–155 |
| 全栈交付 | 156–184 |
| 生产与安全 | 185–198 |
| 进阶 | 199–213 |
| AI Agent | 214–254 |

---

## 全量列表

| # | 面试题 | 复习教程 |
|---|--------|----------|
| 1 | [从 venv 到 .venv，一文搞懂环境隔离](1.python-virtual-env-interview.md) | [1.python-virtual-env-tutorial.md](../1.python-virtual-env-tutorial.md) |
| 2 | [从 typing 到 pydantic，告别「动态一时爽，重构火](2.python-type-annotation-interview.md) | [2.python-type-annotation-tutorial.md](../2.python-type-annotation-tutorial.md) |
| 3 | [从 asyncio 到 async/await，让代码飞起来](3.python-asyncio-interview.md) | [3.python-asyncio-tutorial.md](../3.python-asyncio-tutorial.md) |
| 4 | [从 pip 到 uv.lock，构建可复现的项目环境](4.python-package-management-interview.md) | [4.python-package-management-tutorial.md](../4.python-package-management-tutorial.md) |
| 5 | [从新手到出坑，写让人心情愉悦的接口](5.rest-api-design-interview.md) | [5.rest-api-design-tutorial.md](../5.rest-api-design-tutorial.md) |
| 6 | [从轮询到实时推送，让服务端主动「开口说话」](6.websocket-interview.md) | [6.websocket-tutorial.md](../6.websocket-tutorial.md) |
| 7 | [比 WebSocket 更简单的服务端推送方案](7.sse-interview.md) | [7.sse-tutorial.md](../7.sse-tutorial.md) |
| 8 | [从增删改查到 JSON、全文搜索、窗口函数](8.postgresql-interview.md) | [8.postgresql-tutorial.md](../8.postgresql-tutorial.md) |
| 9 | [从「直接 push master」到规范的协作开发](9.git-branch-strategy-interview.md) | [9.git-branch-strategy-tutorial.md](../9.git-branch-strategy-tutorial.md) |
| 10 | [Redis、文档库、Cache-Aside 和 TTL 一文搞懂](10.nosql-cache-interview.md) | [10.nosql-cache-tutorial.md](../10.nosql-cache-tutorial.md) |
| 11 | [从「在我电脑上能跑」到一键起全套环境](11.docker-compose-interview.md) | [11.docker-compose-tutorial.md](../11.docker-compose-tutorial.md) |
| 12 | [从「SSH 上去一脸懵」到能独立查故障](12.linux-commands-log-interview.md) | [12.linux-commands-log-tutorial.md](../12.linux-commands-log-tutorial.md) |
| 13 | [从「JavaScript 加类型」到能读懂现代前端代码](13.typescript-basics-interview.md) | [13.typescript-basics-tutorial（front-end）.md](../13.typescript-basics-tutorial（front-end）.md) |
| 14 | [从 useState 到 Zustand、Redux 与 Pin](14.frontend-state-management-interview.md) | [14.frontend-state-management-tutorial（front-end）.md](../14.frontend-state-management-tutorial（front-end）.md) |
| 15 | [逐字显示、中断与用户感知](15.streaming-ui-rendering-interview.md) | [15.streaming-ui-rendering-tutorial（front-end）.md](../15.streaming-ui-rendering-tutorial（front-end）.md) |
| 16 | [从排版到 XSS 防护](16.markdown-rendering-security-interview.md) | [16.markdown-rendering-security-tutorial（front-end）.md](../16.markdown-rendering-security-tutorial（front-end）.md) |
| 17 | [中文分词与英文 Tokenization](17.nlp-tokenization-basics-interview.md) | [17.nlp-tokenization-basics-tutorial.md](../17.nlp-tokenization-basics-tutorial.md) |
| 18 | [TF-IDF 原理](18.tfidf-principles-interview.md) | [18.tfidf-principles-tutorial.md](../18.tfidf-principles-tutorial.md) |
| 19 | [BM25 稀疏检索原理](19.bm25-sparse-retrieval-interview.md) | [19.bm25-sparse-retrieval-tutorial.md](../19.bm25-sparse-retrieval-tutorial.md) |
| 20 | [倒排索引概念](20.inverted-index-interview.md) | [20.inverted-index-tutorial.md](../20.inverted-index-tutorial.md) |
| 21 | [Word2Vec 与静态词向量](21.word2vec-static-embeddings-interview.md) | [21.word2vec-static-embeddings-tutorial.md](../21.word2vec-static-embeddings-tutorial.md) |
| 22 | [Transformer 架构](22.transformer-architecture-interview.md) | [22.transformer-architecture-tutorial.md](../22.transformer-architecture-tutorial.md) |
| 23 | [Self-Attention（自注意力）](23.self-attention-interview.md) | [23.self-attention-tutorial.md](../23.self-attention-tutorial.md) |
| 24 | [预训练与微调](24.pretrain-finetune-interview.md) | [24.pretrain-finetune-tutorial.md](../24.pretrain-finetune-tutorial.md) |
| 25 | [Embedding 向量表示](25.embedding-vector-interview.md) | [25.embedding-vector-tutorial.md](../25.embedding-vector-tutorial.md) |
| 26 | [Cosine Similarity 与内积相似度](26.similarity-metrics-interview.md) | [26.similarity-metrics-tutorial.md](../26.similarity-metrics-tutorial.md) |
| 27 | [Token 计数与计费](27.token-counting-billing-interview.md) | [27.token-counting-billing-tutorial.md](../27.token-counting-billing-tutorial.md) |
| 28 | [Context Window（上下文窗口）](28.context-window-interview.md) | [28.context-window-tutorial.md](../28.context-window-tutorial.md) |
| 29 | [Temperature / Top-p / Top-k 采样](29.llm-sampling-interview.md) | [29.llm-sampling-tutorial.md](../29.llm-sampling-tutorial.md) |
| 30 | [System / User / Assistant 提示词角色](30.prompt-roles-interview.md) | [30.prompt-roles-tutorial.md](../30.prompt-roles-tutorial.md) |
| 31 | [Few-shot Prompting（少样本提示）](31.few-shot-prompting-interview.md) | [31.few-shot-prompting-tutorial.md](../31.few-shot-prompting-tutorial.md) |
| 32 | [Chain-of-Thought（思维链）了解指南](32.chain-of-thought-interview.md) | [32.chain-of-thought-tutorial.md](../32.chain-of-thought-tutorial.md) |
| 33 | [幻觉（Hallucination）成因](33.llm-hallucination-interview.md) | [33.llm-hallucination-tutorial.md](../33.llm-hallucination-tutorial.md) |
| 34 | [Grounding 与引用归因](34.grounding-citation-interview.md) | [34.grounding-citation-tutorial.md](../34.grounding-citation-tutorial.md) |
| 35 | [闭源 LLM API 调用模式（OpenAI 兼容）](35.openai-compatible-api-interview.md) | [35.openai-compatible-api-tutorial.md](../35.openai-compatible-api-tutorial.md) |
| 36 | [PDF 文本提取](36.pdf-text-extraction-interview.md) | [36.pdf-text-extraction-tutorial.md](../36.pdf-text-extraction-tutorial.md) |
| 37 | [PDF 表格与版面（Layout）挑战](37.pdf-layout-tables-interview.md) | [37.pdf-layout-tables-tutorial.md](../37.pdf-layout-tables-tutorial.md) |
| 38 | [Markdown 解析](38.markdown-parsing-interview.md) | [38.markdown-parsing-tutorial.md](../38.markdown-parsing-tutorial.md) |
| 39 | [HTML 正文抽取](39.html-content-extraction-interview.md) | [39.html-content-extraction-tutorial.md](../39.html-content-extraction-tutorial.md) |
| 40 | [DOCX / Office 文档解析](40.docx-office-parsing-interview.md) | [40.docx-office-parsing-tutorial.md](../40.docx-office-parsing-tutorial.md) |
| 41 | [纯文本与编码检测（UTF-8 / GBK）](41.text-encoding-detection-interview.md) | [41.text-encoding-detection-tutorial.md](../41.text-encoding-detection-tutorial.md) |
| 42 | [PyMuPDF（fitz）](42.pymupdf-interview.md) | [42.pymupdf-tutorial.md](../42.pymupdf-tutorial.md) |
| 43 | [pdfplumber](43.pdfplumber-interview.md) | [43.pdfplumber-tutorial.md](../43.pdfplumber-tutorial.md) |
| 44 | [Unstructured.io 统一分区](44.unstructured-io-interview.md) | [44.unstructured-io-tutorial.md](../44.unstructured-io-tutorial.md) |
| 45 | [Apache Tika 内容检测与抽取](45.apache-tika-interview.md) | [45.apache-tika-tutorial.md](../45.apache-tika-tutorial.md) |
| 46 | [文本清洗（空白、乱码、页眉页脚）](46.text-cleaning-interview.md) | [46.text-cleaning-tutorial.md](../46.text-cleaning-tutorial.md) |
| 47 | [文档去重（Hash / SimHash）](47.doc-dedup-interview.md) | [47.doc-dedup-tutorial.md](../47.doc-dedup-tutorial.md) |
| 48 | [文档版本管理](48.doc-versioning-interview.md) | [48.doc-versioning-tutorial.md](../48.doc-versioning-tutorial.md) |
| 49 | [增量更新与变更检测](49.incremental-update-interview.md) | [49.incremental-update-tutorial.md](../49.incremental-update-tutorial.md) |
| 50 | [doc_id 元数据](50.metadata-doc-id-interview.md) | [50.metadata-doc-id-tutorial.md](../50.metadata-doc-id-tutorial.md) |
| 51 | [chunk_id 元数据](51.metadata-chunk-id-interview.md) | [51.metadata-chunk-id-tutorial.md](../51.metadata-chunk-id-tutorial.md) |
| 52 | [Source / Page / Section 溯源元数据](52.metadata-source-page-interview.md) | [52.metadata-source-page-tutorial.md](../52.metadata-source-page-tutorial.md) |
| 53 | [ACL 访问控制元数据](53.metadata-acl-interview.md) | [53.metadata-acl-tutorial.md](../53.metadata-acl-tutorial.md) |
| 54 | [Timestamp / Version 时效元数据](54.metadata-timestamp-version-interview.md) | [54.metadata-timestamp-version-tutorial.md](../54.metadata-timestamp-version-tutorial.md) |
| 55 | [OCR 与扫描件](55.ocr-scanned-docs-interview.md) | [55.ocr-scanned-docs-tutorial.md](../55.ocr-scanned-docs-tutorial.md) |
| 56 | [图片内文字与多模态边界](56.multimodal-image-text-interview.md) | [56.multimodal-image-text-tutorial.md](../56.multimodal-image-text-tutorial.md) |
| 57 | [固定长度分块](57.fixed-size-chunking-interview.md) | [57.fixed-size-chunking-tutorial.md](../57.fixed-size-chunking-tutorial.md) |
| 58 | [递归字符分块](58.recursive-character-chunking-interview.md) | [58.recursive-character-chunking-tutorial.md](../58.recursive-character-chunking-tutorial.md) |
| 59 | [句子边界分块](59.sentence-boundary-chunking-interview.md) | [59.sentence-boundary-chunking-tutorial.md](../59.sentence-boundary-chunking-tutorial.md) |
| 60 | [Overlap 重叠窗口](60.chunk-overlap-interview.md) | [60.chunk-overlap-tutorial.md](../60.chunk-overlap-tutorial.md) |
| 61 | [Chunk Size 调参 Trade-off](61.chunk-size-tradeoff-interview.md) | [61.chunk-size-tradeoff-tutorial.md](../61.chunk-size-tradeoff-tutorial.md) |
| 62 | [结构感知分块（标题层级）](62.structure-aware-chunking-interview.md) | [62.structure-aware-chunking-tutorial.md](../62.structure-aware-chunking-tutorial.md) |
| 63 | [Markdown AST 分块](63.markdown-ast-chunking-interview.md) | [63.markdown-ast-chunking-tutorial.md](../63.markdown-ast-chunking-tutorial.md) |
| 64 | [HTML DOM 分块](64.html-dom-chunking-interview.md) | [64.html-dom-chunking-tutorial.md](../64.html-dom-chunking-tutorial.md) |
| 65 | [Parent-Document Retriever](65.parent-document-retriever-interview.md) | [65.parent-document-retriever-tutorial.md](../65.parent-document-retriever-tutorial.md) |
| 66 | [L2 归一化](66.l2-normalization-interview.md) | [66.l2-normalization-tutorial.md](../66.l2-normalization-tutorial.md) |
| 67 | [批量 Embedding](67.embedding-batching-interview.md) | [67.embedding-batching-tutorial.md](../67.embedding-batching-tutorial.md) |
| 68 | [Embedding 缓存策略](68.embedding-cache-interview.md) | [68.embedding-cache-tutorial.md](../68.embedding-cache-tutorial.md) |
| 69 | [Embedding API 重试与限流](69.embedding-retry-rate-limit-interview.md) | [69.embedding-retry-rate-limit-tutorial.md](../69.embedding-retry-rate-limit-tutorial.md) |
| 70 | [中英混合语料 Embedding 选型](70.mixed-language-embedding-interview.md) | [70.mixed-language-embedding-tutorial.md](../70.mixed-language-embedding-tutorial.md) |
| 71 | [领域专用 Embedding 评估](71.domain-embedding-evaluation-interview.md) | [71.domain-embedding-evaluation-tutorial.md](../71.domain-embedding-evaluation-tutorial.md) |
| 72 | [本地 Embedding 推理](72.local-embedding-inference-interview.md) | [72.local-embedding-inference-tutorial.md](../72.local-embedding-inference-tutorial.md) |
| 73 | [Embedding 微调概念](73.embedding-finetune-interview.md) | [73.embedding-finetune-tutorial.md](../73.embedding-finetune-tutorial.md) |
| 74 | [对比学习完全指南（了解篇）](74.contrastive-learning-interview.md) | [74.contrastive-learning-tutorial.md](../74.contrastive-learning-tutorial.md) |
| 75 | [FAISS 本地 ANN](75.faiss-ann-interview.md) | [75.faiss-ann-tutorial.md](../75.faiss-ann-tutorial.md) |
| 76 | [Chroma 轻量向量库](76.chroma-vector-db-interview.md) | [76.chroma-vector-db-tutorial.md](../76.chroma-vector-db-tutorial.md) |
| 77 | [Milvus 分布式向量库](77.milvus-interview.md) | [77.milvus-tutorial.md](../77.milvus-tutorial.md) |
| 78 | [Qdrant 向量库与 Payload 过滤](78.qdrant-interview.md) | [78.qdrant-tutorial.md](../78.qdrant-tutorial.md) |
| 79 | [Weaviate 图式向量库入门指南](79.weaviate-interview.md) | [79.weaviate-tutorial.md](../79.weaviate-tutorial.md) |
| 80 | [Pinecone 托管向量库入门指南](80.pinecone-interview.md) | [80.pinecone-tutorial.md](../80.pinecone-tutorial.md) |
| 81 | [pgvector 与 Postgres 一体化 RAG 指南](81.pgvector-interview.md) | [81.pgvector-tutorial.md](../81.pgvector-tutorial.md) |
| 82 | [Elasticsearch 向量检索入门指南](82.elasticsearch-vector-interview.md) | [82.elasticsearch-vector-tutorial.md](../82.elasticsearch-vector-tutorial.md) |
| 83 | [OpenSearch 混合检索入门指南](83.opensearch-hybrid-interview.md) | [83.opensearch-hybrid-tutorial.md](../83.opensearch-hybrid-tutorial.md) |
| 84 | [Flat 暴力检索](84.flat-brute-force-search-interview.md) | [84.flat-brute-force-search-tutorial.md](../84.flat-brute-force-search-tutorial.md) |
| 85 | [IVF 倒排文件索引](85.ivf-index-interview.md) | [85.ivf-index-tutorial.md](../85.ivf-index-tutorial.md) |
| 86 | [HNSW 图索引](86.hnsw-index-interview.md) | [86.hnsw-index-tutorial.md](../86.hnsw-index-tutorial.md) |
| 87 | [ANN 召回率与延迟评测指南](87.ann-recall-latency-interview.md) | [87.ann-recall-latency-tutorial.md](../87.ann-recall-latency-tutorial.md) |
| 88 | [Metadata 过滤检索](88.metadata-filter-retrieval-interview.md) | [88.metadata-filter-retrieval-tutorial.md](../88.metadata-filter-retrieval-tutorial.md) |
| 89 | [多租户 Namespace 隔离](89.multi-tenant-namespace-interview.md) | [89.multi-tenant-namespace-tutorial.md](../89.multi-tenant-namespace-tutorial.md) |
| 90 | [向量数据库备份与恢复指南](90.vector-db-backup-interview.md) | [90.vector-db-backup-tutorial.md](../90.vector-db-backup-tutorial.md) |
| 91 | [Dense Retrieval 稠密检索](91.dense-retrieval-interview.md) | [91.dense-retrieval-tutorial.md](../91.dense-retrieval-tutorial.md) |
| 92 | [Sparse Retrieval 稀疏检索](92.sparse-retrieval-rag-interview.md) | [92.sparse-retrieval-rag-tutorial.md](../92.sparse-retrieval-rag-tutorial.md) |
| 93 | [Hybrid Search 混合检索](93.hybrid-search-interview.md) | [93.hybrid-search-tutorial.md](../93.hybrid-search-tutorial.md) |
| 94 | [RRF 融合排序](94.rrf-fusion-interview.md) | [94.rrf-fusion-tutorial.md](../94.rrf-fusion-tutorial.md) |
| 95 | [Cross-Encoder 重排](95.cross-encoder-rerank-interview.md) | [95.cross-encoder-rerank-tutorial.md](../95.cross-encoder-rerank-tutorial.md) |
| 96 | [BGE Reranker 重排模型入门指南](96.bge-reranker-interview.md) | [96.bge-reranker-tutorial.md](../96.bge-reranker-tutorial.md) |
| 97 | [Cohere Rerank 托管重排服务入门指南](97.cohere-rerank-interview.md) | [97.cohere-rerank-tutorial.md](../97.cohere-rerank-tutorial.md) |
| 98 | [Top-K 检索数量选择指南](98.top-k-retrieval-interview.md) | [98.top-k-retrieval-tutorial.md](../98.top-k-retrieval-tutorial.md) |
| 99 | [Score Threshold 分数阈值检索指南](99.score-threshold-interview.md) | [99.score-threshold-tutorial.md](../99.score-threshold-tutorial.md) |
| 100 | [Query Rewriting 查询改写](100.query-rewriting-interview.md) | [100.query-rewriting-tutorial.md](../100.query-rewriting-tutorial.md) |
| 101 | [Multi-Query Retrieval 多查询检索](101.multi-query-retrieval-interview.md) | [101.multi-query-retrieval-tutorial.md](../101.multi-query-retrieval-tutorial.md) |
| 102 | [HyDE 假想文档嵌入](102.hyde-interview.md) | [102.hyde-tutorial.md](../102.hyde-tutorial.md) |
| 103 | [Query Decomposition 查询分解](103.query-decomposition-interview.md) | [103.query-decomposition-tutorial.md](../103.query-decomposition-tutorial.md) |
| 104 | [Multi-hop 多跳检索](104.multi-hop-retrieval-interview.md) | [104.multi-hop-retrieval-tutorial.md](../104.multi-hop-retrieval-tutorial.md) |
| 105 | [MMR 多样性重排](105.mmr-diversity-interview.md) | [105.mmr-diversity-tutorial.md](../105.mmr-diversity-tutorial.md) |
| 106 | [检索结果去重](106.retrieval-dedup-interview.md) | [106.retrieval-dedup-tutorial.md](../106.retrieval-dedup-tutorial.md) |
| 107 | [Context 预算分配](107.context-budget-interview.md) | [107.context-budget-tutorial.md](../107.context-budget-tutorial.md) |
| 108 | [Long Context Reorder](108.long-context-reorder-interview.md) | [108.long-context-reorder-tutorial.md](../108.long-context-reorder-tutorial.md) |
| 109 | [会话历史查询增强](109.conversation-query-enhancement-interview.md) | [109.conversation-query-enhancement-tutorial.md](../109.conversation-query-enhancement-tutorial.md) |
| 110 | [RAG Prompt 模板入门指南](110.rag-prompt-template-interview.md) | [110.rag-prompt-template-tutorial.md](../110.rag-prompt-template-tutorial.md) |
| 111 | [Context Injection Format](111.context-injection-format-interview.md) | [111.context-injection-format-tutorial.md](../111.context-injection-format-tutorial.md) |
| 112 | [RAG 拒答策略](112.refusal-strategy-interview.md) | [112.refusal-strategy-tutorial.md](../112.refusal-strategy-tutorial.md) |
| 113 | [行内引用标注](113.inline-citation-interview.md) | [113.inline-citation-tutorial.md](../113.inline-citation-tutorial.md) |
| 114 | [脚注式引用](114.footnote-citation-interview.md) | [114.footnote-citation-tutorial.md](../114.footnote-citation-tutorial.md) |
| 115 | [源文档跳转与页码定位](115.source-document-navigation-interview.md) | [115.source-document-navigation-tutorial.md](../115.source-document-navigation-tutorial.md) |
| 116 | [SSE RAG 流式输出](116.sse-rag-streaming-interview.md) | [116.sse-rag-streaming-tutorial.md](../116.sse-rag-streaming-tutorial.md) |
| 117 | [WebSocket RAG Streaming](117.websocket-rag-streaming-interview.md) | [117.websocket-rag-streaming-tutorial.md](../117.websocket-rag-streaming-tutorial.md) |
| 118 | [多轮历史管理](118.multi-turn-history-interview.md) | [118.multi-turn-history-tutorial.md](../118.multi-turn-history-tutorial.md) |
| 119 | [摘要记忆](119.summary-memory-interview.md) | [119.summary-memory-tutorial.md](../119.summary-memory-tutorial.md) |
| 120 | [指代消解](120.coreference-resolution-interview.md) | [120.coreference-resolution-tutorial.md](../120.coreference-resolution-tutorial.md) |
| 121 | [未授权文档过滤](121.unauthorized-doc-filter-interview.md) | [121.unauthorized-doc-filter-tutorial.md](../121.unauthorized-doc-filter-tutorial.md) |
| 122 | [RAG 内容安全过滤](122.content-safety-filter-interview.md) | [122.content-safety-filter-tutorial.md](../122.content-safety-filter-tutorial.md) |
| 123 | [结构化输出（JSON Mode）入门指南](123.structured-output-json-interview.md) | [123.structured-output-json-tutorial.md](../123.structured-output-json-tutorial.md) |
| 124 | [Function Calling / Tool Use 入门指南](124.function-calling-tool-use-interview.md) | [124.function-calling-tool-use-tutorial.md](../124.function-calling-tool-use-tutorial.md) |
| 125 | [LangChain 核心概念入门指南](125.langchain-core-interview.md) | [125.langchain-core-tutorial.md](../125.langchain-core-tutorial.md) |
| 126 | [LangChain LCEL 入门指南](126.langchain-lcel-interview.md) | [126.langchain-lcel-tutorial.md](../126.langchain-lcel-tutorial.md) |
| 127 | [LangChain Retriever 入门指南](127.langchain-retriever-interview.md) | [127.langchain-retriever-tutorial.md](../127.langchain-retriever-tutorial.md) |
| 128 | [LangChain VectorStore 入门指南](128.langchain-vectorstore-interview.md) | [128.langchain-vectorstore-tutorial.md](../128.langchain-vectorstore-tutorial.md) |
| 129 | [LangChain Document Loader 入门指南](129.langchain-document-loader-interview.md) | [129.langchain-document-loader-tutorial.md](../129.langchain-document-loader-tutorial.md) |
| 130 | [LangChain Text Splitter 入门指南](130.langchain-text-splitter-interview.md) | [130.langchain-text-splitter-tutorial.md](../130.langchain-text-splitter-tutorial.md) |
| 131 | [LlamaIndex Index 类型入门指南](131.llamaindex-index-types-interview.md) | [131.llamaindex-index-types-tutorial.md](../131.llamaindex-index-types-tutorial.md) |
| 132 | [LlamaIndex Query Engine](132.llamaindex-query-engine-interview.md) | [132.llamaindex-query-engine-tutorial.md](../132.llamaindex-query-engine-tutorial.md) |
| 133 | [LlamaIndex Agent 入门指南](133.llamaindex-agent-interview.md) | [133.llamaindex-agent-tutorial.md](../133.llamaindex-agent-tutorial.md) |
| 134 | [Haystack Pipeline 思想](134.haystack-pipeline-interview.md) | [134.haystack-pipeline-tutorial.md](../134.haystack-pipeline-tutorial.md) |
| 135 | [自研 Pipeline vs 使用框架](135.pipeline-vs-framework-interview.md) | [135.pipeline-vs-framework-tutorial.md](../135.pipeline-vs-framework-tutorial.md) |
| 136 | [可插拔 Parser / Splitter / Embedder](136.pluggable-parser-splitter-embedder-interview.md) | [136.pluggable-parser-splitter-embedder-tutorial.md](../136.pluggable-parser-splitter-embedder-tutorial.md) |
| 137 | [可插拔 Store / Retriever / Generato](137.pluggable-store-retriever-generator-interview.md) | [137.pluggable-store-retriever-generator-tutorial.md](../137.pluggable-store-retriever-generator-tutorial.md) |
| 138 | [配置驱动管道组装入门指南](138.config-driven-pipeline-interview.md) | [138.config-driven-pipeline-tutorial.md](../138.config-driven-pipeline-tutorial.md) |
| 139 | [RAGAS Context Precision 入门指南](139.ragas-context-precision-interview.md) | [139.ragas-context-precision-tutorial.md](../139.ragas-context-precision-tutorial.md) |
| 140 | [RAGAS Context Recall 入门指南](140.ragas-context-recall-interview.md) | [140.ragas-context-recall-tutorial.md](../140.ragas-context-recall-tutorial.md) |
| 141 | [RAGAS Faithfulness 入门指南](141.ragas-faithfulness-interview.md) | [141.ragas-faithfulness-tutorial.md](../141.ragas-faithfulness-tutorial.md) |
| 142 | [RAGAS Answer Relevancy 入门指南](142.ragas-answer-relevancy-interview.md) | [142.ragas-answer-relevancy-tutorial.md](../142.ragas-answer-relevancy-tutorial.md) |
| 143 | [Golden Dataset 构建入门指南](143.golden-dataset-interview.md) | [143.golden-dataset-tutorial.md](../143.golden-dataset-tutorial.md) |
| 144 | [回归测试集维护入门指南](144.regression-test-set-interview.md) | [144.regression-test-set-tutorial.md](../144.regression-test-set-tutorial.md) |
| 145 | [DeepEval 入门指南](145.deepeval-interview.md) | [145.deepeval-tutorial.md](../145.deepeval-tutorial.md) |
| 146 | [TruLens 反馈驱动评估](146.trulens-interview.md) | [146.trulens-tutorial.md](../146.trulens-tutorial.md) |
| 147 | [LangSmith 链路追踪](147.langsmith-tracing-interview.md) | [147.langsmith-tracing-tutorial.md](../147.langsmith-tracing-tutorial.md) |
| 148 | [Langfuse 可观测性](148.langfuse-observability-interview.md) | [148.langfuse-observability-tutorial.md](../148.langfuse-observability-tutorial.md) |
| 149 | [Bad Case 归因之解析错误](149.bad-case-parsing-interview.md) | [149.bad-case-parsing-tutorial.md](../149.bad-case-parsing-tutorial.md) |
| 150 | [Bad Case 归因之切块错误](150.bad-case-chunking-interview.md) | [150.bad-case-chunking-tutorial.md](../150.bad-case-chunking-tutorial.md) |
| 151 | [Bad Case 归因之检索遗漏](151.bad-case-retrieval-miss-interview.md) | [151.bad-case-retrieval-miss-tutorial.md](../151.bad-case-retrieval-miss-tutorial.md) |
| 152 | [Bad Case 归因之生成胡编](152.bad-case-hallucination-interview.md) | [152.bad-case-hallucination-tutorial.md](../152.bad-case-hallucination-tutorial.md) |
| 153 | [RAG A/B 实验设计](153.ab-experiment-rag-interview.md) | [153.ab-experiment-rag-tutorial.md](../153.ab-experiment-rag-tutorial.md) |
| 154 | [RAG 参数版本管理](154.param-version-management-interview.md) | [154.param-version-management-tutorial.md](../154.param-version-management-tutorial.md) |
| 155 | [RAG 人工评测流程入门指南](155.human-evaluation-rag-interview.md) | [155.human-evaluation-rag-tutorial.md](../155.human-evaluation-rag-tutorial.md) |
| 156 | [FastAPI RAG 项目结构](156.fastapi-project-structure-interview.md) | [156.fastapi-project-structure-tutorial.md](../156.fastapi-project-structure-tutorial.md) |
| 157 | [RAG 文件上传 multipart 入门指南](157.file-upload-multipart-interview.md) | [157.file-upload-multipart-tutorial.md](../157.file-upload-multipart-tutorial.md) |
| 158 | [FastAPI BackgroundTasks 入门指南](158.fastapi-background-tasks-interview.md) | [158.fastapi-background-tasks-tutorial.md](../158.fastapi-background-tasks-tutorial.md) |
| 159 | [Celery RAG 异步任务队列入门指南](159.celery-async-queue-interview.md) | [159.celery-async-queue-tutorial.md](../159.celery-async-queue-tutorial.md) |
| 160 | [Bull / ARQ / Node 队列入门指南](160.bull-arq-node-queue-interview.md) | [160.bull-arq-node-queue-tutorial.md](../160.bull-arq-node-queue-tutorial.md) |
| 161 | [索引任务状态机入门指南](161.index-task-state-machine-interview.md) | [161.index-task-state-machine-tutorial.md](../161.index-task-state-machine-tutorial.md) |
| 162 | [幂等重建索引入门指南](162.idempotent-reindex-interview.md) | [162.idempotent-reindex-tutorial.md](../162.idempotent-reindex-tutorial.md) |
| 163 | [索引失败重试与死信入门指南](163.retry-dead-letter-interview.md) | [163.retry-dead-letter-tutorial.md](../163.retry-dead-letter-tutorial.md) |
| 164 | [JWT 认证 RAG API 入门指南](164.jwt-auth-rag-interview.md) | [164.jwt-auth-rag-tutorial.md](../164.jwt-auth-rag-tutorial.md) |
| 165 | [RBAC 角色权限 RAG](165.rbac-rag-interview.md) | [165.rbac-rag-tutorial.md](../165.rbac-rag-tutorial.md) |
| 166 | [多租户 tenant_id 后端隔离](166.tenant-isolation-backend-interview.md) | [166.tenant-isolation-backend-tutorial.md](../166.tenant-isolation-backend-tutorial.md) |
| 167 | [OpenAI 兼容 API 封装](167.openai-api-wrapper-interview.md) | [167.openai-api-wrapper-tutorial.md](../167.openai-api-wrapper-tutorial.md) |
| 168 | [多模型路由与降级](168.multi-model-routing-interview.md) | [168.multi-model-routing-tutorial.md](../168.multi-model-routing-tutorial.md) |
| 169 | [Rate Limiting 速率限制入门指南](169.rate-limiting-api-interview.md) | [169.rate-limiting-api-tutorial.md](../169.rate-limiting-api-tutorial.md) |
| 170 | [OpenAPI / Swagger 文档](170.openapi-swagger-docs-interview.md) | [170.openapi-swagger-docs-tutorial.md](../170.openapi-swagger-docs-tutorial.md) |
| 171 | [聊天消息列表 UI 入门指南](171.chat-message-list-ui-interview.md) | [171.chat-message-list-ui-tutorial（front-end）.md](../171.chat-message-list-ui-tutorial（front-end）.md) |
| 172 | [RAG 答案的 Markdown 渲染与安全](172.markdown-render-rag-interview.md) | [172.markdown-render-rag-tutorial（front-end）.md](../172.markdown-render-rag-tutorial（front-end）.md) |
| 173 | [RAG 答案代码高亮](173.code-highlight-rag-interview.md) | [173.code-highlight-rag-tutorial（front-end）.md](../173.code-highlight-rag-tutorial（front-end）.md) |
| 174 | [流式打字机效果](174.streaming-typewriter-ui-interview.md) | [174.streaming-typewriter-ui-tutorial（front-end）.md](../174.streaming-typewriter-ui-tutorial（front-end）.md) |
| 175 | [中断生成 AbortController](175.abort-controller-stream-interview.md) | [175.abort-controller-stream-tutorial（front-end）.md](../175.abort-controller-stream-tutorial（front-end）.md) |
| 176 | [引用卡片 UI](176.citation-card-ui-interview.md) | [176.citation-card-ui-tutorial（front-end）.md](../176.citation-card-ui-tutorial（front-end）.md) |
| 177 | [侧边栏原文预览](177.source-preview-sidebar-interview.md) | [177.source-preview-sidebar-tutorial（front-end）.md](../177.source-preview-sidebar-tutorial（front-end）.md) |
| 178 | [PDF 高亮定位](178.pdf-highlight-locate-interview.md) | [178.pdf-highlight-locate-tutorial（front-end）.md](../178.pdf-highlight-locate-tutorial（front-end）.md) |
| 179 | [知识库文档上传界面](179.kb-doc-upload-ui-interview.md) | [179.kb-doc-upload-ui-tutorial（front-end）.md](../179.kb-doc-upload-ui-tutorial（front-end）.md) |
| 180 | [解析 / 索引进度展示](180.index-progress-ui-interview.md) | [180.index-progress-ui-tutorial（front-end）.md](../180.index-progress-ui-tutorial（front-end）.md) |
| 181 | [重建索引操作](181.reindex-ui-interview.md) | [181.reindex-ui-tutorial（front-end）.md](../181.reindex-ui-tutorial（front-end）.md) |
| 182 | [检索调试台](182.retrieval-debug-console-interview.md) | [182.retrieval-debug-console-tutorial（front-end）.md](../182.retrieval-debug-console-tutorial（front-end）.md) |
| 183 | [管理后台用量统计](183.admin-usage-dashboard-interview.md) | [183.admin-usage-dashboard-tutorial（front-end）.md](../183.admin-usage-dashboard-tutorial（front-end）.md) |
| 184 | [管理后台日志与评测看板](184.admin-log-eval-dashboard-interview.md) | [184.admin-log-eval-dashboard-tutorial（front-end）.md](../184.admin-log-eval-dashboard-tutorial（front-end）.md) |
| 185 | [Docker 多阶段构建](185.docker-multi-stage-build-interview.md) | [185.docker-multi-stage-build-tutorial.md](../185.docker-multi-stage-build-tutorial.md) |
| 186 | [Docker Compose 全栈部署](186.docker-compose-fullstack-interview.md) | [186.docker-compose-fullstack-tutorial.md](../186.docker-compose-fullstack-tutorial.md) |
| 187 | [Kubernetes 基本概念（RAG 语境）](187.kubernetes-basics-rag-interview.md) | [187.kubernetes-basics-rag-tutorial.md](../187.kubernetes-basics-rag-tutorial.md) |
| 188 | [RAG 密钥管理](188.secrets-management-rag-interview.md) | [188.secrets-management-rag-tutorial.md](../188.secrets-management-rag-tutorial.md) |
| 189 | [健康检查 /health /ready](189.health-readiness-rag-interview.md) | [189.health-readiness-rag-tutorial.md](../189.health-readiness-rag-tutorial.md) |
| 190 | [结构化日志（JSON）](190.structured-logging-rag-interview.md) | [190.structured-logging-rag-tutorial.md](../190.structured-logging-rag-tutorial.md) |
| 191 | [Prometheus 指标](191.prometheus-metrics-rag-interview.md) | [191.prometheus-metrics-rag-tutorial.md](../191.prometheus-metrics-rag-tutorial.md) |
| 192 | [Embedding 批次成本估算](192.embedding-batch-cost-interview.md) | [192.embedding-batch-cost-tutorial.md](../192.embedding-batch-cost-tutorial.md) |
| 193 | [向量库存储成本](193.vector-storage-cost-interview.md) | [193.vector-storage-cost-tutorial.md](../193.vector-storage-cost-tutorial.md) |
| 194 | [LLM Token 成本优化](194.llm-token-cost-optimization-interview.md) | [194.llm-token-cost-optimization-tutorial.md](../194.llm-token-cost-optimization-tutorial.md) |
| 195 | [RAG 链路 PII 脱敏](195.pii-redaction-rag-interview.md) | [195.pii-redaction-rag-tutorial.md](../195.pii-redaction-rag-tutorial.md) |
| 196 | [RAG 审计日志](196.audit-log-rag-interview.md) | [196.audit-log-rag-tutorial.md](../196.audit-log-rag-tutorial.md) |
| 197 | [GDPR 与数据驻留（RAG 视角）](197.gdpr-data-residency-interview.md) | [197.gdpr-data-residency-tutorial.md](../197.gdpr-data-residency-tutorial.md) |
| 198 | [等保与 RAG 合规语境](198.china-compliance-rag-interview.md) | [198.china-compliance-rag-tutorial.md](../198.china-compliance-rag-tutorial.md) |
| 199 | [Graph RAG](199.graph-rag-interview.md) | [199.graph-rag-tutorial.md](../199.graph-rag-tutorial.md) |
| 200 | [知识图谱增强检索](200.kg-enhanced-retrieval-interview.md) | [200.kg-enhanced-retrieval-tutorial.md](../200.kg-enhanced-retrieval-tutorial.md) |
| 201 | [Agentic RAG 完全指南（了解）](201.agentic-rag-interview.md) | [201.agentic-rag-tutorial.md](../201.agentic-rag-tutorial.md) |
| 202 | [ReAct 推理式 RAG 完全指南（了解）](202.react-reasoning-rag-interview.md) | [202.react-reasoning-rag-tutorial.md](../202.react-reasoning-rag-tutorial.md) |
| 203 | [Multi-step Tool Retrieval 完全指南（了](203.multi-step-tool-retrieval-interview.md) | [203.multi-step-tool-retrieval-tutorial.md](../203.multi-step-tool-retrieval-tutorial.md) |
| 204 | [Self-RAG 自反思检索完全指南（了解）](204.self-rag-interview.md) | [204.self-rag-tutorial.md](../204.self-rag-tutorial.md) |
| 205 | [CRAG 纠错式 RAG 完全指南（了解）](205.crag-corrective-rag-interview.md) | [205.crag-corrective-rag-tutorial.md](../205.crag-corrective-rag-tutorial.md) |
| 206 | [Adaptive RAG 自适应检索完全指南（了解）](206.adaptive-rag-interview.md) | [206.adaptive-rag-tutorial.md](../206.adaptive-rag-tutorial.md) |
| 207 | [Map-Reduce 长文档摘要](207.map-reduce-summarization-interview.md) | [207.map-reduce-summarization-tutorial.md](../207.map-reduce-summarization-tutorial.md) |
| 208 | [Refine 迭代精炼摘要](208.refine-summarization-interview.md) | [208.refine-summarization-tutorial.md](../208.refine-summarization-tutorial.md) |
| 209 | [RAPTOR 层次检索完全指南（了解）](209.raptor-hierarchical-retrieval-interview.md) | [209.raptor-hierarchical-retrieval-tutorial.md](../209.raptor-hierarchical-retrieval-tutorial.md) |
| 210 | [多模态 RAG 完全指南（了解）](210.multimodal-rag-interview.md) | [210.multimodal-rag-tutorial.md](../210.multimodal-rag-tutorial.md) |
| 211 | [ColPali 类文档页检索完全指南（了解）](211.colpali-rag-interview.md) | [211.colpali-rag-tutorial.md](../211.colpali-rag-tutorial.md) |
| 212 | [LoRA 微调领域问答完全指南（了解）](212.lora-domain-qa-interview.md) | [212.lora-domain-qa-tutorial.md](../212.lora-domain-qa-tutorial.md) |
| 213 | [RLHF / DPO 与 RAG 对齐完全指南（了解）](213.rlhf-dpo-rag-interview.md) | [213.rlhf-dpo-rag-tutorial.md](../213.rlhf-dpo-rag-tutorial.md) |
| 214 | [从 RAG 走向 Agent](214.rag-to-agent-transition-interview.md) | [214.rag-to-agent-transition-tutorial.md](../214.rag-to-agent-transition-tutorial.md) |
| 215 | [Agent、RAG 与 Workflow 怎么选](215.agent-vs-rag-vs-workflow-interview.md) | [215.agent-vs-rag-vs-workflow-tutorial.md](../215.agent-vs-rag-vs-workflow-tutorial.md) |
| 216 | [什么时候不要使用 Agent](216.when-not-to-use-agent-interview.md) | [216.when-not-to-use-agent-tutorial.md](../216.when-not-to-use-agent-tutorial.md) |
| 217 | [企业级 Agent 架构总览](217.enterprise-agent-architecture-overview-interview.md) | [217.enterprise-agent-architecture-overview-tutorial.md](../217.enterprise-agent-architecture-overview-tutorial.md) |
| 218 | [工具调用基础](218.tool-calling-basics-interview.md) | [218.tool-calling-basics-tutorial.md](../218.tool-calling-basics-tutorial.md) |
| 219 | [Tool Schema 设计](219.tool-schema-design-interview.md) | [219.tool-schema-design-tutorial.md](../219.tool-schema-design-tutorial.md) |
| 220 | [工具参数校验](220.tool-parameter-validation-interview.md) | [220.tool-parameter-validation-tutorial.md](../220.tool-parameter-validation-tutorial.md) |
| 221 | [工具结果标准化](221.tool-result-normalization-interview.md) | [221.tool-result-normalization-tutorial.md](../221.tool-result-normalization-tutorial.md) |
| 222 | [工具错误、超时与重试](222.tool-error-timeout-retry-interview.md) | [222.tool-error-timeout-retry-tutorial.md](../222.tool-error-timeout-retry-tutorial.md) |
| 223 | [幂等 Agent 工具](223.idempotent-agent-tools-interview.md) | [223.idempotent-agent-tools-tutorial.md](../223.idempotent-agent-tools-tutorial.md) |
| 224 | [Human-in-the-Loop Agent](224.human-in-the-loop-agent-interview.md) | [224.human-in-the-loop-agent-tutorial.md](../224.human-in-the-loop-agent-tutorial.md) |
| 225 | [Agent 工具权限边界](225.agent-tool-permission-boundary-interview.md) | [225.agent-tool-permission-boundary-tutorial.md](../225.agent-tool-permission-boundary-tutorial.md) |
| 226 | [Agent 循环——观察-思考-行动](226.agent-loop-observe-think-act-interview.md) | [226.agent-loop-observe-think-act-tutorial.md](../226.agent-loop-observe-think-act-tutorial.md) |
| 227 | [ReAct Agent 模式](227.react-agent-pattern-interview.md) | [227.react-agent-pattern-tutorial.md](../227.react-agent-pattern-tutorial.md) |
| 228 | [Plan-and-Execute Agent](228.plan-and-execute-agent-interview.md) | [228.plan-and-execute-agent-tutorial.md](../228.plan-and-execute-agent-tutorial.md) |
| 229 | [Reflection Agent 模式](229.reflection-agent-pattern-interview.md) | [229.reflection-agent-pattern-tutorial.md](../229.reflection-agent-pattern-tutorial.md) |
| 230 | [任务分解 Agent](230.task-decomposition-agent-interview.md) | [230.task-decomposition-agent-tutorial.md](../230.task-decomposition-agent-tutorial.md) |
| 231 | [Agent 停止条件](231.agent-stop-condition-interview.md) | [231.agent-stop-condition-tutorial.md](../231.agent-stop-condition-tutorial.md) |
| 232 | [Agent Memory 类型](232.agent-memory-types-interview.md) | [232.agent-memory-types-tutorial.md](../232.agent-memory-types-tutorial.md) |
| 233 | [短期记忆与会话上下文](233.short-term-agent-memory-interview.md) | [233.short-term-agent-memory-tutorial.md](../233.short-term-agent-memory-tutorial.md) |
| 234 | [长期记忆](234.long-term-agent-memory-interview.md) | [234.long-term-agent-memory-tutorial.md](../234.long-term-agent-memory-tutorial.md) |
| 235 | [Memory 写入策略](235.memory-write-policy-interview.md) | [235.memory-write-policy-tutorial.md](../235.memory-write-policy-tutorial.md) |
| 236 | [Memory 检索策略](236.memory-retrieval-policy-interview.md) | [236.memory-retrieval-policy-tutorial.md](../236.memory-retrieval-policy-tutorial.md) |
| 237 | [Memory 隐私与删除](237.memory-privacy-deletion-interview.md) | [237.memory-privacy-deletion-tutorial.md](../237.memory-privacy-deletion-tutorial.md) |
| 238 | [Agentic RAG 生产架构](238.agentic-rag-architecture-interview.md) | [238.agentic-rag-architecture-tutorial.md](../238.agentic-rag-architecture-tutorial.md) |
| 239 | [RAG Agent 的 Query Planning](239.query-planning-rag-agent-interview.md) | [239.query-planning-rag-agent-tutorial.md](../239.query-planning-rag-agent-tutorial.md) |
| 240 | [多步检索](240.multi-step-retrieval-agent-interview.md) | [240.multi-step-retrieval-agent-tutorial.md](../240.multi-step-retrieval-agent-tutorial.md) |
| 241 | [Tool-Augmented RAG](241.tool-augmented-rag-interview.md) | [241.tool-augmented-rag-tutorial.md](../241.tool-augmented-rag-tutorial.md) |
| 242 | [RAG Agent 引用验证](242.rag-agent-citation-verification-interview.md) | [242.rag-agent-citation-verification-tutorial.md](../242.rag-agent-citation-verification-tutorial.md) |
| 243 | [RAG Agent Bad Case Debugging](243.rag-agent-bad-case-debugging-interview.md) | [243.rag-agent-bad-case-debugging-tutorial.md](../243.rag-agent-bad-case-debugging-tutorial.md) |
| 244 | [Agent Workflow 模式](244.agent-workflow-patterns-interview.md) | [244.agent-workflow-patterns-tutorial.md](../244.agent-workflow-patterns-tutorial.md) |
| 245 | [状态机 Agent](245.state-machine-agent-interview.md) | [245.state-machine-agent-tutorial.md](../245.state-machine-agent-tutorial.md) |
| 246 | [Checkpoint 与 Resume](246.agent-checkpoint-resume-interview.md) | [246.agent-checkpoint-resume-tutorial.md](../246.agent-checkpoint-resume-tutorial.md) |
| 247 | [Durable Agent Execution](247.durable-agent-execution-interview.md) | [247.durable-agent-execution-tutorial.md](../247.durable-agent-execution-tutorial.md) |
| 248 | [Agent 后台任务](248.agent-background-job-interview.md) | [248.agent-background-job-tutorial.md](../248.agent-background-job-tutorial.md) |
| 249 | [事件驱动 Agent 架构](249.agent-event-driven-architecture-interview.md) | [249.agent-event-driven-architecture-tutorial.md](../249.agent-event-driven-architecture-tutorial.md) |
| 250 | [构建知识库管理 Agent](250.build-knowledge-base-agent-interview.md) | [250.build-knowledge-base-agent-tutorial.md](../250.build-knowledge-base-agent-tutorial.md) |
| 251 | [构建研究 Agent](251.build-research-agent-interview.md) | [251.build-research-agent-tutorial.md](../251.build-research-agent-tutorial.md) |
| 252 | [构建客服 Agent](252.build-customer-support-agent-interview.md) | [252.build-customer-support-agent-tutorial.md](../252.build-customer-support-agent-tutorial.md) |
| 253 | [构建代码审查 Agent](253.build-code-review-agent-interview.md) | [253.build-code-review-agent-tutorial.md](../253.build-code-review-agent-tutorial.md) |
| 254 | [构建运维 Agent](254.build-admin-ops-agent-interview.md) | [254.build-admin-ops-agent-tutorial.md](../254.build-admin-ops-agent-tutorial.md) |
