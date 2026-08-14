# 企业 RAG 全栈工程师 — 面试自检 50 题

> 配合 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) 使用：每题可勾选「能讲清 / 能画图 / 能写代码」三档自评。  
> 详细追问与参考答案见 [`docs/interview/`](interview/README.md)（254 篇，与编号教程一一对应）。

---

## 使用方式

- **阶段 0～2**：优先完成 A～C 模块（1～124）相关题目  
- **阶段 3～5**：补 D～G（125～198）  
- **阶段 6～7**：补 H 与 Agent（199～254）  
- 每题链接到对应 **面试题文档**；无单独面试篇的，链到 **编号教程**

---

## A. 基础前置（1～16）

| # | 自检题 | 复习 |
|---|--------|------|
| 1 | 为什么项目要用虚拟环境？`venv` 与全局 `pip install` 的风险？ | [1](interview/1.python-virtual-env-interview.md) |
| 2 | Pydantic 与 `typing` 在 API 边界各解决什么？ | [2](interview/2.python-type-annotation-interview.md) |
| 3 | `async/await` 适用场景？FastAPI 里哪些操作用异步、哪些不必？ | [3](interview/3.python-asyncio-interview.md) |
| 4 | `requirements.txt` 与 lock 文件如何保证可复现构建？ | [4](interview/4.python-package-management-interview.md) |
| 5 | REST 里幂等、分页、错误码如何设计？ | [5](interview/5.rest-api-design-interview.md) |
| 6 | WebSocket 与 SSE 选型：双向 vs 单向推送？ | [6](interview/6.websocket-interview.md) / [7](interview/7.sse-interview.md) |
| 7 | PostgreSQL 索引、JSONB、事务在 RAG 元数据表怎么用？ | [8](interview/8.postgresql-interview.md) |
| 8 | Redis Cache-Aside 与 TTL 在 Embedding 缓存中的模式？ | [10](interview/10.nosql-cache-interview.md) |

---

## B. NLP / IR / LLM（17～35）

| # | 自检题 | 复习 |
|---|--------|------|
| 9 | BM25 与 Dense Retrieval 各自擅长什么语料？ | [19](interview/19.bm25-sparse-retrieval-interview.md) / [91](interview/91.dense-retrieval-interview.md) |
| 10 | Embedding 维度、归一化、Cosine 与内积检索的关系？ | [25](interview/25.embedding-vector-interview.md) / [66](interview/66.l2-normalization-interview.md) |
| 11 | Context Window、Token 计费如何影响 RAG 成本？ | [27](interview/27.token-counting-billing-interview.md) / [28](interview/28.context-window-interview.md) |
| 12 | 幻觉成因与 Grounding / 引用归因的基本策略？ | [33](interview/33.llm-hallucination-interview.md) / [34](interview/34.grounding-citation-interview.md) |
| 13 | OpenAI 兼容 API 的 streaming、重试、密钥管理要点？ | [35](interview/35.openai-compatible-api-interview.md) |

---

## C. RAG 核心链路（36～124）

| # | 自检题 | 复习 |
|---|--------|------|
| 14 | **能否在白板画出** 上传 → 解析 → 分块 → 向量化 → 检索 → 生成 全链路？ | [156](interview/156.fastapi-project-structure-interview.md) |
| 15 | chunk size 变大/变小的 trade-off？Overlap 何时必要？ | [61](interview/61.chunk-size-tradeoff-interview.md) / [60](interview/60.chunk-overlap-interview.md) |
| 16 | Parent-Document / 结构感知分块解决什么问题？ | [65](interview/65.parent-document-retriever-interview.md) / [63](interview/63.markdown-ast-chunking-interview.md) |
| 17 | 向量库选型：FAISS / Chroma / pgvector / Milvus 各适合什么规模？ | [75](interview/75.faiss-ann-interview.md) / [81](interview/81.pgvector-interview.md) |
| 18 | HNSW vs IVF：召回、延迟、内存如何权衡？ | [86](interview/86.hnsw-index-interview.md) / [85](interview/85.ivf-index-interview.md) |
| 19 | Metadata 过滤与多租户 Namespace 如何叠加？ | [88](interview/88.metadata-filter-retrieval-interview.md) / [89](interview/89.multi-tenant-namespace-interview.md) |
| 20 | **混合检索为什么比纯向量好？RRF 是什么？** | [93](interview/93.hybrid-search-interview.md) / [94](interview/94.rrf-fusion-interview.md) |
| 21 | Cross-Encoder 重排放在链路哪一段？Top-K 如何调？ | [95](interview/95.cross-encoder-rerank-interview.md) / [98](interview/98.top-k-retrieval-interview.md) |
| 22 | Query Rewriting / HyDE / Multi-hop 各自适用什么问法？ | [100](interview/100.query-rewriting-interview.md) / [102](interview/102.hyde-interview.md) |
| 23 | Context 预算、Long Context Reorder 如何减少「 lost in the middle 」？ | [107](interview/107.context-budget-interview.md) / [108](interview/108.long-context-reorder-interview.md) |
| 24 | RAG Prompt 模板应约束哪些规则（拒答、引用、格式）？ | [110](interview/110.rag-prompt-template-interview.md) |
| 25 | 行内引用 vs 脚注引用 vs 源文档跳转的产品差异？ | [113](interview/113.inline-citation-interview.md) / [115](interview/115.source-document-navigation-interview.md) |
| 26 | SSE / WebSocket 流式 RAG 前后端如何配合 Abort？ | [116](interview/116.sse-rag-streaming-interview.md) / [175](interview/175.abort-controller-stream-interview.md) |
| 27 | 多轮历史、摘要记忆、指代消解如何影响检索 query？ | [118](interview/118.multi-turn-history-interview.md) / [119](interview/119.summary-memory-interview.md) |
| 28 | ACL / 未授权文档过滤在 ingest 与 retrieve 各做什么？ | [53](interview/53.metadata-acl-interview.md) / [121](interview/121.unauthorized-doc-filter-interview.md) |
| 29 | **检索漏了怎么办？** 如何定位是解析、分块还是检索阶段？ | [151](interview/151.bad-case-retrieval-miss-interview.md) / [149](interview/149.bad-case-parsing-interview.md) |
| 30 | **生成胡编怎么查？** Faithfulness 与 citation 校验思路？ | [152](interview/152.bad-case-hallucination-interview.md) / [141](interview/141.ragas-faithfulness-interview.md) |

---

## D～E. 框架与评测（125～155）

| # | 自检题 | 复习 |
|---|--------|------|
| 31 | LangChain Retriever 与 VectorStore 的边界？ | [127](interview/127.langchain-retriever-interview.md) / [128](interview/128.langchain-vectorstore-interview.md) |
| 32 | 自研 Pipeline vs 框架：何时该抽象 Parser / Embedder / Generator？ | [135](interview/135.pipeline-vs-framework-interview.md) / [136](interview/136.pluggable-parser-splitter-embedder-interview.md) |
| 33 | **RAGAS 四个核心指标**（Context Precision/Recall、Faithfulness、Answer Relevancy）含义？ | [139](interview/139.ragas-context-precision-interview.md)～[142](interview/142.ragas-answer-relevancy-interview.md) |
| 34 | Golden Dataset 与回归测试集如何维护？ | [143](interview/143.golden-dataset-interview.md) / [144](interview/144.regression-test-set-interview.md) |
| 35 | LangSmith / Langfuse 在 RAG 链路要 trace 哪些 span？ | [147](interview/147.langsmith-tracing-interview.md) / [148](interview/148.langfuse-observability-interview.md) |
| 36 | RAG A/B 实验与参数版本管理（chunk / top-k / reranker）？ | [153](interview/153.ab-experiment-rag-interview.md) / [154](interview/154.param-version-management-interview.md) |

---

## F. 全栈产品（156～184）

| # | 自检题 | 复习 |
|---|--------|------|
| 37 | FastAPI 项目结构：ingest / retrieve / chat 如何分层？ | [156](interview/156.fastapi-project-structure-interview.md) |
| 38 | 文件上传 → 异步索引任务状态机（pending/running/done/failed）？ | [157](interview/157.file-upload-multipart-interview.md) / [161](interview/161.index-task-state-machine-interview.md) |
| 39 | **如何做增量索引而不全量重建？** 幂等 reindex 要点？ | [49](interview/49.incremental-update-interview.md) / [162](interview/162.idempotent-reindex-interview.md) |
| 40 | JWT + RBAC + tenant_id 在后端如何贯穿检索？ | [164](interview/164.jwt-auth-rag-interview.md) / [166](interview/166.tenant-isolation-backend-interview.md) |
| 41 | **流式输出前后端如何实现？** 打字机 UI 与 Markdown 安全？ | [174](interview/174.streaming-typewriter-ui-interview.md) / [172](interview/172.markdown-render-rag-interview.md) |
| 42 | 检索调试台输入 query 看 top-k：排障价值是什么？ | [182](interview/182.retrieval-debug-console-interview.md) |

---

## G. 生产与安全（185～198）

| # | 自检题 | 复习 |
|---|--------|------|
| 43 | Docker 多阶段构建与 Compose 全栈部署要点？ | [185](interview/185.docker-multi-stage-build-interview.md) / [186](interview/186.docker-compose-fullstack-interview.md) |
| 44 | `/health` 与 `/ready` 在 RAG 服务里分别检查什么？ | [189](interview/189.health-readiness-rag-interview.md) |
| 45 | Embedding / 向量存储 / LLM Token **成本如何估算与优化**？ | [192](interview/192.embedding-batch-cost-interview.md) / [194](interview/194.llm-token-cost-optimization-interview.md) |
| 46 | PII 脱敏、审计日志、GDPR 数据驻留的 RAG 语境？ | [195](interview/195.pii-redaction-rag-interview.md) / [196](interview/196.audit-log-rag-interview.md) |

---

## H. 进阶（199～213）

| # | 自检题 | 复习 |
|---|--------|------|
| 47 | Graph RAG 与 Agentic RAG 相对朴素 RAG 解决什么？ | [199](interview/199.graph-rag-interview.md) / [201](interview/201.agentic-rag-interview.md) |
| 48 | Self-RAG / CRAG / Adaptive RAG 的纠错思路差异？ | [204](interview/204.self-rag-interview.md) / [205](interview/205.crag-corrective-rag-interview.md) |
| 49 | Map-Reduce / RAPTOR 长文档摘要与层次检索？ | [207](interview/207.map-reduce-summarization-interview.md) / [209](interview/209.raptor-hierarchical-retrieval-interview.md) |
| 50 | **什么场景不适合 RAG？** 何时用微调 / Workflow / Agent？ | [215](interview/215.agent-vs-rag-vs-workflow-interview.md) / [216](interview/216.when-not-to-use-agent-interview.md) |

---

## 核心 10 题速查（路线图 §面试自检）

与 [ENTERPRISE_RAG_ROADMAP.md](ENTERPRISE_RAG_ROADMAP.md#面试自检) 对齐：

1. 题 **14** — RAG 全链路白板  
2. 题 **15** — chunk size trade-off  
3. 题 **29～30** — 检索漏 / 生成胡编  
4. 题 **20** — 混合检索与 RRF  
5. 题 **19** — 多租户隔离  
6. 题 **39** — 增量索引  
7. 题 **41** — 流式前后端  
8. 题 **33** — RAGAS 四指标  
9. 题 **31** — LangChain Retriever vs VectorStore  
10. 题 **50** — 不适合 RAG 的场景  

---

## 进度追踪

```text
[ ] 1–13   基础 + LLM
[ ] 14–30  RAG 核心
[ ] 31–36  框架与评测
[ ] 37–42  全栈
[ ] 43–46  生产安全
[ ] 47–50  进阶与选型
```

全部勾选后，建议抽 5 题做 **30 分钟口述 + 白板**，并对照 [`docs/interview/`](interview/README.md) 补薄弱点。
