# Wxw-Blog

企业级 **RAG 全栈与 AI Agent 工程师** 学习仓库：中文 Markdown 教程 + 配图，覆盖 **上传文档 → 解析分块 → 向量化索引 → 检索问答 → Agent 工具执行 → 可观测可迭代** 完整链路。

| 内容 | 数量 | 说明 |
|------|------|------|
| 编号教程 | **254 篇** | `1`～`213` 对应 [企业 RAG 路线图](docs/ENTERPRISE_RAG_ROADMAP.md)，`214`～`254` 对应 [AI Agent 工程路线](docs/AI_AGENT_ENGINEERING_ROADMAP.md) |
| Next.js 系列 | **12 篇** | RAG 全栈**主栈**前端（App Router） |
| React 系列 | **13 篇** | Vite 对照路线（含 ES6 前置与工程化延伸） |
| 配图 | `image/` | 每篇教程配套信息图，维护见 [scripts/README.md](scripts/README.md) |

> **从哪里开始？** 先按 [企业 RAG 路线图](docs/ENTERPRISE_RAG_ROADMAP.md) 完成模块 A→H，再进入 [AI Agent 工程路线](docs/AI_AGENT_ENGINEERING_ROADMAP.md)；前端实战优先走 [nextjs/README.md](nextjs/README.md)。

---

## 快速导航

| 目标 | 推荐阅读 |
|------|----------|
| 总路线与 230 条知识点清单 | [docs/ENTERPRISE_RAG_ROADMAP.md](docs/ENTERPRISE_RAG_ROADMAP.md) |
| 零基础补 Python / API / DevOps | 下方 **A. 基础前置**（1～16） |
| 理解 RAG 原理与链路 | **B～C6**（17～124） |
| 用框架重构 + 评测迭代 | **D～E**（125～155） |
| 交付可演示的全栈产品 | **F1 + F2**（156～184）+ [Next.js 系列](nextjs/README.md) |
| 上线、成本与安全 | **G**（185～198） |
| Senior / 面试加分 | **H**（199～213） |
| 构建可控、可恢复的 AI Agent | [AI Agent 工程路线](docs/AI_AGENT_ENGINEERING_ROADMAP.md)（214～254） |

---

## 分阶段学习路线

与 [路线图 §三](docs/ENTERPRISE_RAG_ROADMAP.md#三分阶段学习计划) 对齐：

| 阶段 | 目标 | 对应教程 / 项目 |
|------|------|-----------------|
| 0 基础补齐 | Python API + 流式 LLM | A（1～16）；SSE #7、asyncio #3 |
| 1 RAG 最小闭环 | 手写 ingest → retrieve → generate | C1～C6（36～124） |
| 2 检索质量 | 混合检索、重排、RAGAS | C4～C5、E（75～109、139～155） |
| 3 框架与工程化 | LangChain + 异步索引 | D、F1（125～138、156～170） |
| 4 全栈产品 | 聊天 + 引用 + 管理台 | F2 + [Next.js 1～12](nextjs/README.md) |
| 5 生产化 | 部署、观测、成本 | G（185～198） |
| 6 进阶与面试 | Graph RAG / Agentic RAG | H（199～213） |
| 7 AI Agent 工程 | Tool Calling、Agent Loop、Memory、Workflow、项目实战 | [AI Agent 工程路线](docs/AI_AGENT_ENGINEERING_ROADMAP.md)（214～254） |

---

## 前端实战系列

| 系列 | 定位 | 目录 |
|------|------|------|
| **Next.js（推荐）** | RAG 全栈主栈：CRUD + RAG 前端闭环 | [nextjs/README.md](nextjs/README.md) |
| **React（对照）** | Vite SPA 参考实现，含 TypeScript / TanStack Query | [react/README.md](react/README.md) |

```text
推荐路线：React（一）ES6+  →  Next 1～12（CRUD + RAG UI）
已有 React 经验：React 1～6 速览  →  Next 1～5 补 App Router  →  Next 6～12
```

---

## 企业 RAG 编号教程目录（1～213）

### A. 基础前置

Python 工程化、HTTP/REST、流式协议、数据库、DevOps 与前端基础。

| 序号 | 主题 |
|------|------|
| 1 | [Python 虚拟环境](docs/1.python-virtual-env-tutorial.md) |
| 2 | [Python 类型注解](docs/2.python-type-annotation-tutorial.md) |
| 3 | [Python 异步编程](docs/3.python-asyncio-tutorial.md) |
| 4 | [Python 包管理与依赖锁定](docs/4.python-package-management-tutorial.md) |
| 5 | [REST API 设计](docs/5.rest-api-design-tutorial.md) |
| 6 | [WebSocket 与长连接](docs/6.websocket-tutorial.md) |
| 7 | [SSE（Server-Sent Events）](docs/7.sse-tutorial.md) |
| 8 | [PostgreSQL 常用特性](docs/8.postgresql-tutorial.md) |
| 9 | [Git 分支策略与 PR 流程](docs/9.git-branch-strategy-tutorial.md) |
| 10 | [NoSQL 与缓存入门：Redis、文档库、Cache-Aside 和 TTL 一文搞懂](docs/10.nosql-cache-tutorial.md) |
| 11 | [Docker 镜像与容器 + Docker Compose 多服务编排：从「在我电脑上能跑」到一键起全套环境](docs/11.docker-compose-tutorial.md) |
| 12 | [Linux 常用命令与日志排查：从「SSH 上去一脸懵」到能独立查故障](docs/12.linux-commands-log-tutorial.md) |
| 13 | [从「JavaScript 加类型」到能读懂现代前端代码](docs/13.typescript-basics-tutorial（front-end）.md) |
| 14 | [从 useState 到 Zustand、Redux 与 Pinia](docs/14.frontend-state-management-tutorial（front-end）.md) |
| 15 | [流式 UI 渲染](docs/15.streaming-ui-rendering-tutorial（front-end）.md) |
| 16 | [Markdown 渲染与安全](docs/16.markdown-rendering-security-tutorial（front-end）.md) |

### B. NLP / IR / LLM 基础

分词、检索原理、Transformer、Embedding 与 LLM 调用。

| 序号 | 主题 |
|------|------|
| 17 | [中文分词与英文 Tokenization](docs/17.nlp-tokenization-basics-tutorial.md) |
| 18 | [TF-IDF 原理](docs/18.tfidf-principles-tutorial.md) |
| 19 | [BM25 稀疏检索原理](docs/19.bm25-sparse-retrieval-tutorial.md) |
| 20 | [倒排索引概念](docs/20.inverted-index-tutorial.md) |
| 21 | [Word2Vec 与静态词向量](docs/21.word2vec-static-embeddings-tutorial.md) |
| 22 | [Transformer 架构](docs/22.transformer-architecture-tutorial.md) |
| 23 | [Self-Attention（自注意力）](docs/23.self-attention-tutorial.md) |
| 24 | [预训练与微调](docs/24.pretrain-finetune-tutorial.md) |
| 25 | [Embedding 向量表示](docs/25.embedding-vector-tutorial.md) |
| 26 | [Cosine Similarity 与内积相似度](docs/26.similarity-metrics-tutorial.md) |
| 27 | [Token 计数与计费](docs/27.token-counting-billing-tutorial.md) |
| 28 | [Context Window（上下文窗口）](docs/28.context-window-tutorial.md) |
| 29 | [Temperature / Top-p / Top-k 采样](docs/29.llm-sampling-tutorial.md) |
| 30 | [System / User / Assistant 提示词角色](docs/30.prompt-roles-tutorial.md) |
| 31 | [Few-shot Prompting（少样本提示）](docs/31.few-shot-prompting-tutorial.md) |
| 32 | [Chain-of-Thought（思维链）](docs/32.chain-of-thought-tutorial.md) |
| 33 | [幻觉（Hallucination）成因](docs/33.llm-hallucination-tutorial.md) |
| 34 | [Grounding 与引用归因](docs/34.grounding-citation-tutorial.md) |
| 35 | [闭源 LLM API 调用模式（OpenAI 兼容）](docs/35.openai-compatible-api-tutorial.md) |

### C1. 数据采集与解析

PDF / Markdown / HTML / DOCX 解析、清洗、元数据与 OCR。

| 序号 | 主题 |
|------|------|
| 36 | [PDF 文本提取](docs/36.pdf-text-extraction-tutorial.md) |
| 37 | [PDF 表格与版面（Layout）挑战](docs/37.pdf-layout-tables-tutorial.md) |
| 38 | [Markdown 解析](docs/38.markdown-parsing-tutorial.md) |
| 39 | [HTML 正文抽取](docs/39.html-content-extraction-tutorial.md) |
| 40 | [DOCX / Office 文档解析](docs/40.docx-office-parsing-tutorial.md) |
| 41 | [纯文本与编码检测（UTF-8 / GBK）](docs/41.text-encoding-detection-tutorial.md) |
| 42 | [PyMuPDF（fitz）](docs/42.pymupdf-tutorial.md) |
| 43 | [pdfplumber](docs/43.pdfplumber-tutorial.md) |
| 44 | [Unstructured.io 统一分区](docs/44.unstructured-io-tutorial.md) |
| 45 | [Apache Tika 内容检测与抽取](docs/45.apache-tika-tutorial.md) |
| 46 | [文本清洗（空白、乱码、页眉页脚）](docs/46.text-cleaning-tutorial.md) |
| 47 | [文档去重（Hash / SimHash）](docs/47.doc-dedup-tutorial.md) |
| 48 | [文档版本管理](docs/48.doc-versioning-tutorial.md) |
| 49 | [增量更新与变更检测](docs/49.incremental-update-tutorial.md) |
| 50 | [doc_id 元数据](docs/50.metadata-doc-id-tutorial.md) |
| 51 | [chunk_id 元数据](docs/51.metadata-chunk-id-tutorial.md) |
| 52 | [Source / Page / Section 溯源元数据](docs/52.metadata-source-page-tutorial.md) |
| 53 | [ACL 访问控制元数据](docs/53.metadata-acl-tutorial.md) |
| 54 | [Timestamp / Version 时效元数据](docs/54.metadata-timestamp-version-tutorial.md) |
| 55 | [OCR 与扫描件](docs/55.ocr-scanned-docs-tutorial.md) |
| 56 | [图片内文字与多模态边界](docs/56.multimodal-image-text-tutorial.md) |

### C2. 分块（Chunking）

固定 / 递归 / 结构感知分块、Overlap 与 Parent-Document。

| 序号 | 主题 |
|------|------|
| 57 | [固定长度分块](docs/57.fixed-size-chunking-tutorial.md) |
| 58 | [递归字符分块](docs/58.recursive-character-chunking-tutorial.md) |
| 59 | [句子边界分块](docs/59.sentence-boundary-chunking-tutorial.md) |
| 60 | [Overlap 重叠窗口](docs/60.chunk-overlap-tutorial.md) |
| 61 | [Chunk Size 调参 Trade-off](docs/61.chunk-size-tradeoff-tutorial.md) |
| 62 | [结构感知分块（标题层级）](docs/62.structure-aware-chunking-tutorial.md) |
| 63 | [Markdown AST 分块](docs/63.markdown-ast-chunking-tutorial.md) |
| 64 | [HTML DOM 分块](docs/64.html-dom-chunking-tutorial.md) |
| 65 | [Parent-Document Retriever](docs/65.parent-document-retriever-tutorial.md) |

### C3. 向量化（Embedding）

归一化、批量、缓存、限流、本地推理与微调。

| 序号 | 主题 |
|------|------|
| 66 | [L2 归一化](docs/66.l2-normalization-tutorial.md) |
| 67 | [批量 Embedding](docs/67.embedding-batching-tutorial.md) |
| 68 | [Embedding 缓存策略](docs/68.embedding-cache-tutorial.md) |
| 69 | [Embedding API 重试与限流](docs/69.embedding-retry-rate-limit-tutorial.md) |
| 70 | [中英混合语料 Embedding 选型](docs/70.mixed-language-embedding-tutorial.md) |
| 71 | [领域专用 Embedding 评估](docs/71.domain-embedding-evaluation-tutorial.md) |
| 72 | [本地 Embedding 推理](docs/72.local-embedding-inference-tutorial.md) |
| 73 | [Embedding 微调概念](docs/73.embedding-finetune-tutorial.md) |
| 74 | [对比学习](docs/74.contrastive-learning-tutorial.md) |

### C4. 向量存储与检索

FAISS / Chroma / Milvus / pgvector、索引算法与多租户。

| 序号 | 主题 |
|------|------|
| 75 | [FAISS 本地 ANN](docs/75.faiss-ann-tutorial.md) |
| 76 | [Chroma 轻量向量库](docs/76.chroma-vector-db-tutorial.md) |
| 77 | [Milvus 分布式向量库](docs/77.milvus-tutorial.md) |
| 78 | [Qdrant 向量库与 Payload 过滤](docs/78.qdrant-tutorial.md) |
| 79 | [Weaviate 图式向量库](docs/79.weaviate-tutorial.md) |
| 80 | [Pinecone 托管向量库](docs/80.pinecone-tutorial.md) |
| 81 | [pgvector 与 Postgres 一体化 RAG 指南](docs/81.pgvector-tutorial.md) |
| 82 | [Elasticsearch 向量检索](docs/82.elasticsearch-vector-tutorial.md) |
| 83 | [OpenSearch 混合检索](docs/83.opensearch-hybrid-tutorial.md) |
| 84 | [Flat 暴力检索](docs/84.flat-brute-force-search-tutorial.md) |
| 85 | [IVF 倒排文件索引](docs/85.ivf-index-tutorial.md) |
| 86 | [HNSW 图索引](docs/86.hnsw-index-tutorial.md) |
| 87 | [ANN 召回率与延迟评测指南](docs/87.ann-recall-latency-tutorial.md) |
| 88 | [Metadata 过滤检索](docs/88.metadata-filter-retrieval-tutorial.md) |
| 89 | [多租户 Namespace 隔离](docs/89.multi-tenant-namespace-tutorial.md) |
| 90 | [向量数据库备份与恢复指南](docs/90.vector-db-backup-tutorial.md) |

### C5. 检索与查询优化

Dense / Sparse / Hybrid、重排、Query 增强与会话增强。

| 序号 | 主题 |
|------|------|
| 91 | [Dense Retrieval 稠密检索](docs/91.dense-retrieval-tutorial.md) |
| 92 | [Sparse Retrieval 稀疏检索](docs/92.sparse-retrieval-rag-tutorial.md) |
| 93 | [Hybrid Search 混合检索](docs/93.hybrid-search-tutorial.md) |
| 94 | [RRF 融合排序](docs/94.rrf-fusion-tutorial.md) |
| 95 | [Cross-Encoder 重排](docs/95.cross-encoder-rerank-tutorial.md) |
| 96 | [BGE Reranker 重排模型](docs/96.bge-reranker-tutorial.md) |
| 97 | [Cohere Rerank 托管重排服务](docs/97.cohere-rerank-tutorial.md) |
| 98 | [Top-K 检索数量选择指南](docs/98.top-k-retrieval-tutorial.md) |
| 99 | [Score Threshold 分数阈值检索指南](docs/99.score-threshold-tutorial.md) |
| 100 | [Query Rewriting 查询改写](docs/100.query-rewriting-tutorial.md) |
| 101 | [Multi-Query Retrieval 多查询检索](docs/101.multi-query-retrieval-tutorial.md) |
| 102 | [HyDE 假想文档嵌入](docs/102.hyde-tutorial.md) |
| 103 | [Query Decomposition 查询分解](docs/103.query-decomposition-tutorial.md) |
| 104 | [Multi-hop 多跳检索](docs/104.multi-hop-retrieval-tutorial.md) |
| 105 | [MMR 多样性重排](docs/105.mmr-diversity-tutorial.md) |
| 106 | [检索结果去重](docs/106.retrieval-dedup-tutorial.md) |
| 107 | [Context 预算分配](docs/107.context-budget-tutorial.md) |
| 108 | [Long Context Reorder](docs/108.long-context-reorder-tutorial.md) |
| 109 | [会话历史查询增强](docs/109.conversation-query-enhancement-tutorial.md) |

### C6. 生成与 Grounding

Prompt、引用、流式、多轮对话、安全与 Tool Use。

| 序号 | 主题 |
|------|------|
| 110 | [RAG Prompt 模板](docs/110.rag-prompt-template-tutorial.md) |
| 111 | [Context Injection Format](docs/111.context-injection-format-tutorial.md) |
| 112 | [RAG 拒答策略](docs/112.refusal-strategy-tutorial.md) |
| 113 | [行内引用标注](docs/113.inline-citation-tutorial.md) |
| 114 | [脚注式引用](docs/114.footnote-citation-tutorial.md) |
| 115 | [源文档跳转与页码定位](docs/115.source-document-navigation-tutorial.md) |
| 116 | [SSE RAG 流式输出](docs/116.sse-rag-streaming-tutorial.md) |
| 117 | [WebSocket RAG Streaming](docs/117.websocket-rag-streaming-tutorial.md) |
| 118 | [多轮历史管理](docs/118.multi-turn-history-tutorial.md) |
| 119 | [摘要记忆](docs/119.summary-memory-tutorial.md) |
| 120 | [指代消解](docs/120.coreference-resolution-tutorial.md) |
| 121 | [未授权文档过滤](docs/121.unauthorized-doc-filter-tutorial.md) |
| 122 | [RAG 内容安全过滤](docs/122.content-safety-filter-tutorial.md) |
| 123 | [结构化输出（JSON Mode）](docs/123.structured-output-json-tutorial.md) |
| 124 | [Function Calling / Tool Use](docs/124.function-calling-tool-use-tutorial.md) |

### D. 框架与架构

LangChain、LlamaIndex、Haystack 与可插拔 Pipeline。

| 序号 | 主题 |
|------|------|
| 125 | [LangChain 核心概念](docs/125.langchain-core-tutorial.md) |
| 126 | [LangChain LCEL](docs/126.langchain-lcel-tutorial.md) |
| 127 | [LangChain Retriever](docs/127.langchain-retriever-tutorial.md) |
| 128 | [LangChain VectorStore](docs/128.langchain-vectorstore-tutorial.md) |
| 129 | [LangChain Document Loader](docs/129.langchain-document-loader-tutorial.md) |
| 130 | [LangChain Text Splitter](docs/130.langchain-text-splitter-tutorial.md) |
| 131 | [LlamaIndex Index 类型](docs/131.llamaindex-index-types-tutorial.md) |
| 132 | [LlamaIndex Query Engine](docs/132.llamaindex-query-engine-tutorial.md) |
| 133 | [LlamaIndex Agent](docs/133.llamaindex-agent-tutorial.md) |
| 134 | [Haystack Pipeline 思想](docs/134.haystack-pipeline-tutorial.md) |
| 135 | [自研 Pipeline vs 使用框架](docs/135.pipeline-vs-framework-tutorial.md) |
| 136 | [可插拔 Parser / Splitter / Embedder](docs/136.pluggable-parser-splitter-embedder-tutorial.md) |
| 137 | [可插拔 Store / Retriever / Generator](docs/137.pluggable-store-retriever-generator-tutorial.md) |
| 138 | [配置驱动管道组装](docs/138.config-driven-pipeline-tutorial.md) |

### E. 评测、观测与迭代

RAGAS、Golden Dataset、Bad Case 归因与 A/B 实验。

| 序号 | 主题 |
|------|------|
| 139 | [RAGAS Context Precision](docs/139.ragas-context-precision-tutorial.md) |
| 140 | [RAGAS Context Recall](docs/140.ragas-context-recall-tutorial.md) |
| 141 | [RAGAS Faithfulness](docs/141.ragas-faithfulness-tutorial.md) |
| 142 | [RAGAS Answer Relevancy](docs/142.ragas-answer-relevancy-tutorial.md) |
| 143 | [Golden Dataset 构建](docs/143.golden-dataset-tutorial.md) |
| 144 | [回归测试集维护](docs/144.regression-test-set-tutorial.md) |
| 145 | [DeepEval](docs/145.deepeval-tutorial.md) |
| 146 | [TruLens 反馈驱动评估](docs/146.trulens-tutorial.md) |
| 147 | [LangSmith 链路追踪](docs/147.langsmith-tracing-tutorial.md) |
| 148 | [Langfuse 可观测性](docs/148.langfuse-observability-tutorial.md) |
| 149 | [Bad Case 归因之解析错误](docs/149.bad-case-parsing-tutorial.md) |
| 150 | [Bad Case 归因之切块错误](docs/150.bad-case-chunking-tutorial.md) |
| 151 | [Bad Case 归因之检索遗漏](docs/151.bad-case-retrieval-miss-tutorial.md) |
| 152 | [Bad Case 归因之生成胡编](docs/152.bad-case-hallucination-tutorial.md) |
| 153 | [RAG A/B 实验设计](docs/153.ab-experiment-rag-tutorial.md) |
| 154 | [RAG 参数版本管理](docs/154.param-version-management-tutorial.md) |
| 155 | [RAG 人工评测流程](docs/155.human-evaluation-rag-tutorial.md) |

### F1. 全栈 · 后端

FastAPI、任务队列、认证、多租户与 API 文档。

| 序号 | 主题 |
|------|------|
| 156 | [FastAPI RAG 项目结构](docs/156.fastapi-project-structure-tutorial.md) |
| 157 | [RAG 文件上传 multipart](docs/157.file-upload-multipart-tutorial.md) |
| 158 | [FastAPI BackgroundTasks](docs/158.fastapi-background-tasks-tutorial.md) |
| 159 | [Celery RAG 异步任务队列](docs/159.celery-async-queue-tutorial.md) |
| 160 | [Bull / ARQ / Node 队列](docs/160.bull-arq-node-queue-tutorial.md) |
| 161 | [索引任务状态机](docs/161.index-task-state-machine-tutorial.md) |
| 162 | [幂等重建索引](docs/162.idempotent-reindex-tutorial.md) |
| 163 | [索引失败重试与死信](docs/163.retry-dead-letter-tutorial.md) |
| 164 | [JWT 认证 RAG API](docs/164.jwt-auth-rag-tutorial.md) |
| 165 | [RBAC 角色权限 RAG](docs/165.rbac-rag-tutorial.md) |
| 166 | [多租户 tenant_id 后端隔离](docs/166.tenant-isolation-backend-tutorial.md) |
| 167 | [OpenAI 兼容 API 封装](docs/167.openai-api-wrapper-tutorial.md) |
| 168 | [多模型路由与降级](docs/168.multi-model-routing-tutorial.md) |
| 169 | [Rate Limiting 速率限制](docs/169.rate-limiting-api-tutorial.md) |
| 170 | [OpenAPI / Swagger 文档](docs/170.openapi-swagger-docs-tutorial.md) |

### F2. 全栈 · 前端

聊天 UI、流式、引用溯源、上传与管理台。

| 序号 | 主题 |
|------|------|
| 171 | [聊天消息列表 UI](docs/171.chat-message-list-ui-tutorial（front-end）.md) |
| 172 | [RAG 答案的 Markdown 渲染与安全](docs/172.markdown-render-rag-tutorial（front-end）.md) |
| 173 | [RAG 答案代码高亮](docs/173.code-highlight-rag-tutorial（front-end）.md) |
| 174 | [流式打字机效果](docs/174.streaming-typewriter-ui-tutorial（front-end）.md) |
| 175 | [中断生成 AbortController](docs/175.abort-controller-stream-tutorial（front-end）.md) |
| 176 | [引用卡片 UI](docs/176.citation-card-ui-tutorial（front-end）.md) |
| 177 | [侧边栏原文预览](docs/177.source-preview-sidebar-tutorial（front-end）.md) |
| 178 | [PDF 高亮定位](docs/178.pdf-highlight-locate-tutorial（front-end）.md) |
| 179 | [知识库文档上传界面](docs/179.kb-doc-upload-ui-tutorial（front-end）.md) |
| 180 | [解析 / 索引进度展示](docs/180.index-progress-ui-tutorial（front-end）.md) |
| 181 | [重建索引操作](docs/181.reindex-ui-tutorial（front-end）.md) |
| 182 | [检索调试台](docs/182.retrieval-debug-console-tutorial（front-end）.md) |
| 183 | [管理后台用量统计](docs/183.admin-usage-dashboard-tutorial（front-end）.md) |
| 184 | [管理后台日志与评测看板](docs/184.admin-log-eval-dashboard-tutorial（front-end）.md) |

### G. 生产与云原生

Docker / K8s、密钥、监控、成本与安全合规。

| 序号 | 主题 |
|------|------|
| 185 | [Docker 多阶段构建](docs/185.docker-multi-stage-build-tutorial.md) |
| 186 | [Docker Compose 全栈部署](docs/186.docker-compose-fullstack-tutorial.md) |
| 187 | [Kubernetes 基本概念](docs/187.kubernetes-basics-rag-tutorial.md) |
| 188 | [RAG 密钥管理](docs/188.secrets-management-rag-tutorial.md) |
| 189 | [健康检查 /health /ready](docs/189.health-readiness-rag-tutorial.md) |
| 190 | [结构化日志（JSON）](docs/190.structured-logging-rag-tutorial.md) |
| 191 | [Prometheus 指标](docs/191.prometheus-metrics-rag-tutorial.md) |
| 192 | [Embedding 批次成本估算](docs/192.embedding-batch-cost-tutorial.md) |
| 193 | [向量库存储成本](docs/193.vector-storage-cost-tutorial.md) |
| 194 | [LLM Token 成本优化](docs/194.llm-token-cost-optimization-tutorial.md) |
| 195 | [RAG 链路 PII 脱敏](docs/195.pii-redaction-rag-tutorial.md) |
| 196 | [RAG 审计日志](docs/196.audit-log-rag-tutorial.md) |
| 197 | [GDPR 与数据驻留](docs/197.gdpr-data-residency-tutorial.md) |
| 198 | [等保与 RAG 合规语境](docs/198.china-compliance-rag-tutorial.md) |

### H. 进阶方向

Graph RAG、Agentic RAG、多模态与微调。

| 序号 | 主题 |
|------|------|
| 199 | [Graph RAG](docs/199.graph-rag-tutorial.md) |
| 200 | [知识图谱增强检索](docs/200.kg-enhanced-retrieval-tutorial.md) |
| 201 | [Agentic RAG](docs/201.agentic-rag-tutorial.md) |
| 202 | [ReAct 推理式 RAG](docs/202.react-reasoning-rag-tutorial.md) |
| 203 | [Multi-step Tool Retrieval](docs/203.multi-step-tool-retrieval-tutorial.md) |
| 204 | [Self-RAG 自反思检索](docs/204.self-rag-tutorial.md) |
| 205 | [CRAG 纠错式 RAG](docs/205.crag-corrective-rag-tutorial.md) |
| 206 | [Adaptive RAG 自适应检索](docs/206.adaptive-rag-tutorial.md) |
| 207 | [Map-Reduce 长文档摘要](docs/207.map-reduce-summarization-tutorial.md) |
| 208 | [Refine 迭代精炼摘要](docs/208.refine-summarization-tutorial.md) |
| 209 | [RAPTOR 层次检索](docs/209.raptor-hierarchical-retrieval-tutorial.md) |
| 210 | [多模态 RAG](docs/210.multimodal-rag-tutorial.md) |
| 211 | [ColPali 类文档页检索](docs/211.colpali-rag-tutorial.md) |
| 212 | [LoRA 微调领域问答](docs/212.lora-domain-qa-tutorial.md) |
| 213 | [RLHF / DPO 与 RAG 对齐](docs/213.rlhf-dpo-rag-tutorial.md) |

---

## AI Agent 工程学习路线（214～254）

见 [docs/AI_AGENT_ENGINEERING_ROADMAP.md](docs/AI_AGENT_ENGINEERING_ROADMAP.md)。这条路线衔接现有 RAG 全栈内容，覆盖 Tool Calling、Agent Loop、Planning、Memory、Agentic RAG、Workflow、人类确认、观测评测与安全边界，并以 5 个项目实战收尾。


---

## 扩展阅读

| 主题 | 链接 |
|------|------|
| Superpowers + frontend-design 实战 | [skill/superpowers-frontend-design-web-dev-tutorial.md](skill/superpowers-frontend-design-web-dev-tutorial.md) |
| 博客配图维护脚本 | [scripts/README.md](scripts/README.md) |
| 面试自检 50 题 | [docs/interview-checklist.md](docs/interview-checklist.md)（路线图引用，待补充） |

---

## 仓库结构

```text
.
├── 1～213.*.md               # 企业 RAG 编号教程
├── 214～254.*.md             # AI Agent 工程编号教程
├── docs/ENTERPRISE_RAG_ROADMAP.md # 总路线图与知识点清单
├── docs/AI_AGENT_ENGINEERING_ROADMAP.md # AI Agent 分阶段路线图
├── nextjs/                   # Next.js RAG 前端系列（12 篇）
├── react/                    # React/Vite 对照系列（13 篇）
├── skill/                    # 扩展技能教程
├── scripts/                  # 配图 manifest / 同步脚本
├── image/                    # 教程配图（按 slug 分子目录）
└── diagram/                  # 单张流程图生成（Pillow）
```

---

## 进度追踪

学习时可在此勾选阶段（也可复制到个人笔记）：

- [ ] 阶段 0：基础补齐（A，1～16）
- [ ] 阶段 1：RAG 最小闭环（C1～C6，36～124）
- [ ] 阶段 2：检索质量（C4～C5 + E）
- [ ] 阶段 3：框架与工程化（D + F1）
- [ ] 阶段 4：全栈产品（F2 + Next.js 系列）
- [ ] 阶段 5：生产化（G）
- [ ] 阶段 6：进阶与面试（H）
- [ ] 阶段 7：AI Agent 工程（214～254）

---

## 贡献与维护

- 新增教程后运行 [scripts/](scripts/README.md) 中的 manifest 流程更新配图引用。
- RAG 教程编号与 [docs/ENTERPRISE_RAG_ROADMAP.md](docs/ENTERPRISE_RAG_ROADMAP.md) 模块保持一致；Agent 教程编号与 [docs/AI_AGENT_ENGINEERING_ROADMAP.md](docs/AI_AGENT_ENGINEERING_ROADMAP.md) 保持一致。
