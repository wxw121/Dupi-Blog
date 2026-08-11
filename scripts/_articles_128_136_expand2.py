# -*- coding: utf-8 -*-
"""Second-pass expansions for tutorials 128-136 — sections 15-17, >=2200 hanzi each."""

EXPANSIONS2 = {
    "langchain-vectorstore": """
## 15. FAISS 与 Chroma 在 LangChain 中的集成对照

### 15.1 为什么 VectorStore 是 D 轨的「存储插头」

在 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) 的 D 轨里，[128 LangChain VectorStore](128.langchain-vectorstore-tutorial.md) 承上启下：上游 [129 Loader](129.langchain-document-loader-tutorial.md) 与 [130 Splitter](130.langchain-text-splitter-tutorial.md) 产出 `Document` 列表，中间 [25 Embedding](25.embedding-vector-tutorial.md) 把文本变成向量，下游 [127 Retriever](127.langchain-retriever-tutorial.md) 按策略取回证据。VectorStore 的职责不是「魔法检索」，而是 **统一相似度搜索 + metadata 过滤 + 批量写入** 的薄封装。你若已读过 [76 Chroma](76.chroma-vector-db-tutorial.md) 与 [75 FAISS](75.faiss-ann-tutorial.md)，应把 LangChain 类看作 **适配器**：真正排障时仍要会查底层 collection 或 `index.ntotal`。

LangChain 社区包 `langchain_community.vectorstores` 同时提供 `Chroma` 与 `FAISS` 两种后端。PoC 阶段常问「选哪个」——没有银弹，只有 **运维成本 vs 查询形态** 的权衡。Chroma 自带持久化目录与 metadata 过滤，适合 **中小规模、需要 ACL where 子句** 的企业手册库；FAISS 是内存/文件索引库，极致单机 QPS 时常用，但 **filter 能力弱**，多租户 ACL 往往要在检索后二次过滤或维护多份索引。初学者务必各跑通一次 `from_documents` 与 `similarity_search_with_score`，再读 [125 LangChain 核心](125.langchain-core-tutorial.md) 理解 `Embeddings` 接口契约。

### 15.2 Chroma 集成：持久化与 collection 契约

Chroma 在 LangChain 中的典型初始化如下。注意 **embedding 实例必须入库与查询共用**，否则向量空间不一致，Recall 会「看起来像随机」：

```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

embed = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
docs = [Document(page_content="年假制度…", metadata={"doc_id": "hr-001", "acl_group": "all"})]

vs = Chroma.from_documents(
    documents=docs,
    embedding=embed,
    ids=["hr-001:c000"],
    persist_directory="./data/chroma_handbook",
    collection_name="handbook_bge_v2",
)
vs.persist()  # 旧版需显式；新版多数自动落盘，以你锁定的版本为准
```

与 [76 篇](76.chroma-vector-db-tutorial.md) 原生 `collection.upsert` 对齐时，最容易翻车的是 **ids 默认 UUID**。企业增量 [49 增量更新](49.incremental-update-tutorial.md) 要求 ids 等于 [51 chunk_id](51.metadata-chunk-id-tutorial.md)，否则无法幂等覆盖。验收方法：`collection.get(ids=["hr-001:c000"])` 能 O(1) 回查；评测 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 时能按 chunk_id 对齐 bad case。

collection 命名建议 `{知识库}_{embed模型}_{schema版本}`，例如 `policy_bge-m3_v3`。换 [25 embedding](25.embedding-vector-tutorial.md) 模型必须 **新建 collection 全量重建**，旧库只读归档——这是路线图索引层的硬纪律，不是可选项。

### 15.3 FAISS 集成：本地文件与 save_local 流程

FAISS 适配器适合 **只读副本、离线评测、或单机高 QPS demo**。典型模式：

```python
from langchain_community.vectorstores import FAISS

vs = FAISS.from_documents(docs, embed)
vs.save_local("./data/faiss_handbook", index_name="handbook")
# 查询侧
vs2 = FAISS.load_local("./data/faiss_handbook", embed, allow_dangerous_deserialization=True)
hits = vs2.similarity_search_with_score("年假几天", k=5)
```

`allow_dangerous_deserialization=True` 不是装饰——FAISS 反序列化 pickle 有安全风险，**只加载可信路径**。生产若用 FAISS，建议：索引文件放对象存储版本化；发布时 **蓝绿切换** 索引文件而非原地覆盖；与 [75 IVF/HNSW](75.faiss-ann-tutorial.md) 参数文档对照，理解 `IndexFlatIP` 与归一化向量的关系（见 [66 L2 归一化](66.l2-normalization-tutorial.md)）。

FAISS 在 LangChain 里 **没有 Chroma 那样的一等 metadata filter**。企业 ACL [53](53.metadata-acl-tutorial.md) 若选 FAISS，常见补救：① 每租户一份 `save_local`；② 检索 top_k 放大后在应用层按 metadata 过滤；③ 主库仍用 Chroma/Milvus，FAISS 只做只读加速层。面试能说清 trade-off 比背 API 更重要。

### 15.4 与 [126 LCEL](126.langchain-lcel-tutorial.md) 的最小衔接

VectorStore 本身不生成答案。标准做法是 `retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 8})`，再接入 LCEL 链。此处 **search_kwargs** 是生产调参入口：`k` 与 [107 上下文预算](107.context-budget-tutorial.md)、[95 rerank](95.cross-encoder-rerank-tutorial.md) 联动；`filter` 在 Chroma 后端生效。务必在 wiki 记录「当前环境默认 k/filter/MMR 开关」，避免开发者笔记本与 staging 行为不一致。

## 16. 持久化、ACL 元数据过滤与 MMR 多样性检索

### 16.1 持久化与多环境隔离

持久化不仅是 `persist_directory` 字符串。工程上要回答：**谁备份、如何回滚、如何与 embed 版本绑定**。推荐索引任务结束时写 manifest（Parser/Splitter/Embedder 版本见 [136 可插拔](136.pluggable-parser-splitter-embedder-tutorial.md)），至少包含：`collection_name, embed_model, vector_dim, chunk_count, created_at`。staging 与 prod 的目录 **绝不共用**；CI 用临时目录或内存 Chroma，避免污染开发机上的 `./chroma_db`。

容器部署时，把 `persist_directory` 挂到 PVC 或对象存储同步侧车。恢复演练每季度做一次：从备份拉索引 → `load_local` 或 Chroma client 重连 → 跑 [144 回归集](144.regression-test-set-tutorial.md) 十条。没有演练的持久化等于赌磁盘。

### 16.2 ACL filter：在 VectorStore 层强制，而非 Prompt 层祈祷

[121 无权文档过滤](121.unauthorized-doc-filter-tutorial.md) 与 [53 ACL 元数据](53.metadata-acl-tutorial.md) 要求：**检索必须在向量库或 Retriever 层带 filter**。Chroma 示例：

```python
retriever = vs.as_retriever(
    search_kwargs={
        "k": 10,
        "filter": {"acl_group": {"$in": ["all", "finance_ro"]}},
    }
)
```

注意 metadata 值类型与入库一致——`acl_group` 入库是字符串，filter 就不要写整数。常见翻车：开发库 metadata 字段叫 `acl`，生产叫 `acl_group`，filter 静默失效，模型拿到越权 chunk。治理办法：Loader 层 JSON Schema 校验（[129 篇](129.langchain-document-loader-tutorial.md)），入库前拒绝缺字段。

**绝不在 system prompt 里写「不要泄露财务文档」替代 filter**。大模型不是安全边界；VectorStore/Retriever 才是。金融合规场景（[135 框架取舍](135.pipeline-vs-framework-tutorial.md) 案例 B）往往自研 Retriever 包装，在 `_get_relevant_documents` 里强制注入 principal 的 ACL 集合，LangChain 类仅作底层 store。

### 16.3 MMR：缓解 overlap 带来的近邻重复

[60 chunk overlap](60.chunk-overlap-tutorial.md) 与 [105 MMR](105.mmr-diversity-tutorial.md) 是孪生话题：overlap 提高 Recall，但 Top-K 常出现 **同一章节相邻 chunk 占满名额**。LangChain 启用 MMR：

```python
retriever = vs.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 8, "fetch_k": 24, "lambda_mult": 0.6},
)
```

`fetch_k` 先宽召回，MMR 再按相关性与多样性重排。`lambda_mult` 接近 1 偏相关，接近 0 偏多样。调参不要凭感觉：用 [143 金标](143.golden-dataset-tutorial.md) 看 Recall@8 与 **唯一 doc_id 数**。制度库章节长、overlap 高时，MMR 常能降 [106 检索去重](106.retrieval-dedup-tutorial.md) 压力。若已接 [95 cross-encoder rerank](95.cross-encoder-rerank-tutorial.md)，MMR 与 rerank 顺序要在架构图画清——一般 **先 MMR 再 rerank** 或 **只选其一**，避免延迟叠乘。

### 16.4 similarity_search_with_score 与阈值

[99 分数阈值](99.score-threshold-tutorial.md) 在 LangChain 里可用 `similarity_search_with_relevance_scores`（版本不同 API 名略有差异，以锁定版本文档为准）。生产日志应记录 **top1_score、score_gap、hit_ids**，方便 [149 bad case 解析](149.bad-case-parsing-tutorial.md)。不同 embed 模型分数分布不同，阈值必须 **按模型校准**，不可从教程抄 0.7。

## 17. 生产级 ingest 流水线与观测衔接

### 17.1 批量 embed 与限速

生产 ingest 禁止 `for doc in docs: vs.add_documents([doc])`。应按 [67 批处理](67.embedding-batching-tutorial.md) 切 batch（32～128），外层循环 `embed_documents` + `add_texts`/`upsert`，并接 [69 重试限速](69.embedding-retry-rate-limit-tutorial.md)。LangChain `Embeddings.embed_documents` 已按列表设计——VectorStore 内部若逐条 embed，要换实现或自己先算向量再 `add_embeddings`。

日志字段建议：`batch_idx, batch_size, embed_ms, upsert_ms, collection, model_version, job_id`。与 [147 LangSmith](147.langsmith-tracing-tutorial.md) 或 [148 Langfuse](148.langfuse-observability-tutorial.md) 的 ingest span 同名，保证一条 `request_id` 从 API 追到向量行。

### 17.2 增量、删除与幂等

对接 [49 增量](49.incremental-update-tutorial.md) 与 [48 文档版本](48.doc-versioning-tutorial.md)：内容 hash 未变则跳过；变更则 **同 chunk_id upsert 覆盖**；删除则按 `doc_id` metadata 删除或 tombstone。Chroma 可 `delete(ids=...)` 或 where 删除；FAISS 删除能力弱，往往 **全量重建** 或维护旁路删除表。路线图 [162 幂等重索引](162.idempotent-reindex-tutorial.md) 要求 job 可重跑——ids 稳定是前提。

### 17.3 混合检索时 VectorStore 的边界

[93 混合检索](93.hybrid-search-tutorial.md) 里，VectorStore 通常只承担 **稠密路**。稀疏 BM25 用 `BM25Retriever` + `EnsembleRetriever`（[127 篇](127.langchain-retriever-tutorial.md)）。不要让 VectorStore「顺便做 BM25」——职责清晰才好做 Recall 归因。评测时分别记录 dense hit_ids 与 sparse hit_ids，便于 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 分类。

### 17.4 Parent Document 与上下文扩展

[65 Parent Document](65.parent-document-retriever-tutorial.md) 模式：child 小块入 VectorStore，parent 全文在 docstore。metadata 写 `parent_id`，命中 child 后再取 parent 拼进 [107 预算](107.context-budget-tutorial.md)。LangChain `ParentDocumentRetriever` 是包装器，底层仍是 VectorStore + 文档存储。设计 ingest 时要保证 **child 与 parent 的 chunk_id/doc_id 可关联**，否则扩展失败只能退化为短 chunk 答案。

### 17.5 三十分钟巩固清单

1. 同一批 chunk 分别用 Chroma 与 FAISS 入库，对比 `similarity_search_with_score` 延迟与分数分布；  
2. 故意使用不同 `Embeddings` 实例做查询，复现向量空间错乱并修复；  
3. 写 `filter` 演示 ACL，对照 [53][121] 无权用例；  
4. 开启 MMR，对比 overlap=80 时 Top-8 的 doc_id 多样性；  
5. 画白板：ingest 与 query **必须同一 embedding 实例**；  
6. 把本公司 collection 命名规范与换模型重建 SOP 写入 wiki，对齐 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 索引层检查项。

### 17.6 排障决策树：检索结果异常时先查什么

当业务反馈「明明文档里有却搜不到」，不要先怪模型幻觉。第一步确认查询与入库是否同一 embedding 实例、同一 collection、同一 embed 模型版本——这三项任一不一致，表现都是随机漏召回。第二步用 similarity_search_with_score 打印 top10 分数：若 top1 分数极低且与金标 chunk 无关，优先查切块（[130 Splitter](130.langchain-text-splitter-tutorial.md)）与 query 改写（[100 查询改写](100.query-rewriting-tutorial.md)）。第三步查 filter 是否过严：ACL 字段名错误会导致合法用户也召不回。第四步查 collection 是否为空或 count 异常下降。第五步才考虑调 k、MMR、混合检索（[93](93.hybrid-search-tutorial.md)）。

### 17.7 多副本只读与蓝绿发布

生产常见模式：夜间批处理构建新索引到 chroma_db_vNEXT，白天 API 仍读 vCURRENT。校验通过后改配置指针切换，旧目录保留七天只读。FAISS 用 save_local 到版本化路径，发布脚本原子替换 symlink。切勿原地 from_documents 覆盖生产目录。与 [162 幂等重索引](162.idempotent-reindex-tutorial.md) 结合：job_id 重复执行应得到相同 ids 集合。

### 17.8 面试深度题与参考答法

问：LangChain Chroma 与原生 Chroma 客户端何时混用？答：ingest 批量任务可用原生 client 提高吞吐，在线 query 用 LC as_retriever 接 LCEL；但 embed 函数必须同源。混用时封装 ChromaStore 实现 [137 Store](137.pluggable-store-retriever-generator-tutorial.md) 接口。问：FAISS 如何做 ACL？答：分租户索引、检索后过滤、或主库 Chroma 加 FAISS 只读加速。问：MMR 与 rerank 同时开吗？答：看延迟预算；常二选一或先 MMR 再 rerank 前 20 条。

### 17.9 与路线图五层对照自检

数据层：chunk metadata 从 Loader 传到 VectorStore 不丢字段。索引层：collection 命名、embed 版本、持久化备份。服务层：Retriever filter 强制 ACL。应用层：引用靠 [113-115](113.inline-citation-tutorial.md)。工程化：ingest manifest、回归集、[147 追踪](147.langsmith-tracing-tutorial.md)。完成 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) D 轨 128 条时用此五层自检。

### 17.10 深度 FAQ

问：Chroma persist_directory 放哪？放挂载卷，三环境隔离，备份见 [90 向量库备份](90.vector-db-backup-tutorial.md)。问：add_documents 与 from_documents 区别？后者建新库；前者增量。ids 都要显式。问：能否多进程写同一 Chroma？谨慎，常见单 writer 队列加多 reader API，与 [159 Celery](159.celery-async-queue-tutorial.md) 衔接。问：换 embed 后旧库能 query 吗？不能，必须新建 collection，见 [25 Embedding](25.embedding-vector-tutorial.md)。问：何时用 MMR？Top-K 相邻 overlap chunk 过多时，见 [60 overlap](60.chunk-overlap-tutorial.md) 与 [106 去重](106.retrieval-dedup-tutorial.md)。

### 17.11 生产哨兵与配置隔离

ingest 与 query 共用配置中心的 embed_model 与 collection_name 指针。staging 误连 prod 目录是严重事故——用不同前缀与环境变量硬隔离。每周抽检十条金标查询，对比 hit_ids 与上周是否一致，作为 [144 回归](144.regression-test-set-tutorial.md) 补充哨兵。on-call 手册写明 Chroma 与 FAISS 各自的恢复步骤与联系人。


VectorStore 层还要监控 collection 行数增长率与磁盘用量，异常激增可能是重复 ingest 或 ids 不稳定导致只增不删。与 [89 多租户](89.multi-tenant-namespace-tutorial.md) 结合时，单 collection 加 where 要在压测中验证 filter 索引是否生效。

VectorStore 层还要监控 collection 行数增长率与磁盘用量，异常激增可能是重复 ingest 或 ids 不稳定导致只增不删。与 [89 多租户](89.multi-tenant-namespace-tutorial.md) 结合时，单 collection 加 where 要在压测中验证 filter 索引是否生效。
""",
    "langchain-document-loader": """
## 15. Document Loader 族谱与格式选型

### 15.1 Loader 在流水线中的位置

[129 LangChain Document Loader](129.langchain-document-loader-tutorial.md) 是数据层的 **第一站**：把磁盘、URL、数据库里的原始字节变成 `langchain_core.documents.Document`（`page_content` + `metadata`）。在 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) 里，它与 C 轨 [36 PDF 提取](36.pdf-text-extraction-tutorial.md)、[38 Markdown](38.markdown-parsing-tutorial.md)、[41 编码检测](41.text-encoding-detection-tutorial.md) 的关系是：**重解析在 Parser，Loader 是编排入口**。读完 [125 核心](125.langchain-core-tutorial.md) 后应记住：`BaseLoader.load()` 返回 `Iterator[Document]`，可懒加载大目录。

企业常见三类输入：**PDF 制度**、**Markdown/Git 文档**、**混合目录 NAS 扫描**。LangChain 对应 `PyPDFLoader`/`PyMuPDFLoader`、`UnstructuredMarkdownLoader`/`TextLoader`、`DirectoryLoader`。选型不要追新名堂——先对照 [42 PyMuPDF](42.pymupdf-tutorial.md) 与 [43 pdfplumber](43.pdfplumber-tutorial.md) 做 **对照抽取**，固定主 Parser，Loader 只负责传路径与统一 metadata。

### 15.2 PDF Loader：PyPDF 与 PyMuPDF 的工程差异

扫描件 PDF 没有文本层时，Loader 读出来是空串——OCR 是 [55 扫描件](55.ocr-scanned-docs-tutorial.md) 前置，不是 Loader 内置。可搜索 PDF 的差异在 **表格、多栏、页眉页脚**：

```python
from langchain_community.document_loaders import PyMuPDFLoader

loader = PyMuPDFLoader("data/policy.pdf")
docs = loader.load()
for d in docs[:2]:
    print(d.metadata.get("page"), d.page_content[:120])
```

`PyMuPDFLoader` 通常按页产出 Document，`metadata` 带 `page`、`source`。面试常问：为何不用一个 Loader 打天下？因为 **版式复杂** 时 [44 Unstructured](44.unstructured-io-tutorial.md) 或自研 [136 Parser 协议](136.pluggable-parser-splitter-embedder-tutorial.md) 更稳。Loader 层应允许 **配置切换** `loader_backend=pymupdf|pdfplumber`，用 [138 配置驱动](138.config-driven-pipeline-tutorial.md) 注入。

### 15.3 Markdown 与纯文本 Loader

内部 wiki 导出 Markdown 时，`TextLoader` 最简单，但要处理 **编码**（下一节详述）。带 front matter 的 md 可用 `UnstructuredMarkdownLoader` 或自研：先解析 YAML front matter 写入 `metadata.version`、`metadata.owner`，正文进 `page_content`。与 [38 Markdown 解析](38.markdown-parsing-tutorial.md)、[63 AST 切块](63.markdown-ast-chunking-tutorial.md) 衔接时，Loader 阶段就应保留 `source` 相对路径，供后续标题切块使用。

### 15.4 DirectoryLoader：glob 与多格式混合

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader

loader = DirectoryLoader(
    "data/handbook/",
    glob="**/*.{md,txt}",
    loader_cls=TextLoader,
    loader_kwargs={"autodetect_encoding": True},
    show_progress=True,
    use_multithreading=True,
)
docs = loader.load()
```

NAS 上十万文件时，`use_multithreading` 要配合 **增量**（§16），否则 nightly 全量扫会打爆 IO。`glob` 要排除 `node_modules`、`.git`、临时附件。混合 pdf+md 目录可用 `loader_map` 模式：按扩展名选 Loader 类——这正是 [136 注册表](136.pluggable-parser-splitter-embedder-tutorial.md) 思想在 Loader 层的预演。

## 16. metadata 契约、编码与增量同步

### 16.1 与 [50-54] 元数据系列对齐

Loader 是 **metadata 的第一次落点**。建议团队 JSON Schema 规定必填字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| doc_id | string | [50 doc_id](50.metadata-doc-id-tutorial.md) 业务主键 |
| source | string | 路径或 URL [52 source/page](52.metadata-source-page-tutorial.md) |
| mime | string | 审计与回放 |
| version | int | [48 版本](48.doc-versioning-tutorial.md) |
| acl_group | string | [53 ACL](53.metadata-acl-tutorial.md) |
| content_hash | string | [49 增量](49.incremental-update-tutorial.md) |
| lang | string | 供 [130 Splitter](130.langchain-text-splitter-tutorial.md) 选分隔符 |

Loader 完成后 **立即校验**，缺字段拒绝进入 Splitter——比索引后才发现便宜两个数量级。`doc_id` 应稳定：同一路径重跑不变，用 `sha256(normalized_path)` 或业务 CMS id，不要用 Loader 内部随机 id。

### 16.2 编码检测：UTF-8、GBK 与 autodetect_encoding

[41 文本编码](41.text-encoding-detection-tutorial.md) 是国内企业库的隐形杀手。Windows 遗留 txt 常是 GBK，默认 UTF-8 会 **静默乱码** 或抛错。`TextLoader(..., autodetect_encoding=True)` 可缓解，但 autodetect 不是魔法——应用 `chardet` 或 `charset-normalizer` 先检测，再 **显式 encoding 写入 metadata** 供审计。

作业：故意用 GBK 保存 `sample.txt`，对比 `encoding=utf-8` 与 autodetect 的 `page_content` 差异。wiki 规定：**入库前统一转 UTF-8 规范化**（NFKC），与 [46 文本清洗](46.text-cleaning-tutorial.md) 管道衔接。

### 16.3 增量加载与 content_hash 跳过

对接 [49 增量更新](49.incremental-update-tutorial.md)：维护 `manifest.sqlite` 记录 `source, mtime, content_hash, last_ingested_at`。DirectoryLoader 外层包装：

```python
def load_incremental(root: str) -> list:
    out = []
    for path in iter_changed_files(root):  # 自研：对比 mtime/hash
        docs = pick_loader(path).load()
        for d in docs:
            d.metadata["content_hash"] = file_hash(path)
        out.extend(docs)
    return out
```

未变文件 **不进入 Splitter/embed**，节省 [67 批处理](67.embedding-batching-tutorial.md) 成本。删除检测：CMS 下架文档要在 manifest 标 `deleted`，索引侧按 `doc_id` 删除（[128 VectorStore](128.langchain-vectorstore-tutorial.md) 联动）。增量与 [162 幂等重索引](162.idempotent-reindex-tutorial.md) 共用 ids 契约。

### 16.4 去重与多路径同一文档

[47 文档去重](47.doc-dedup-tutorial.md)：邮件附件与正式目录常出现 **同一制度多路径**。load 后按 `content_hash` 或 simhash 去重，只保留权威 `doc_id`。去重在 Splitter **之前**，避免重复 chunk 浪费 embed 配额，也污染 [76 Chroma](76.chroma-vector-db-tutorial.md) collection。

## 17. 安全合规、Web 源与可插拔 Parser 衔接

### 17.1 路径遍历与恶意文件

用户上传文件名禁止 `../`；zip 解压要防 **zip bomb**。docx/pdf 走沙箱转换（[40 docx](40.docx-office-parsing-tutorial.md)），宏文档默认拒绝。加载后文本过 [122 内容安全](122.content-safety-filter-tutorial.md) 再给运营预览——Loader 是 **恶意内容进入系统的闸门**。

### 17.2 Web Loader 与合规抓取

`WebBaseLoader` 抓外部站要注意 robots、版权、TLS 证书。企业内部 Confluence/Notion 优先 **官方 API 导出 JSON/Markdown**，优于裸爬 HTML（[39 HTML 抽取](39.html-content-extraction-tutorial.md)）。抓取频率限速，遵守 [69 重试限速](69.embedding-retry-rate-limit-tutorial.md) 纪律，避免被封 IP 连累办公出口。

### 17.3 中间态 JSONL 与数据组审计

生产建议 Loader 输出 **JSONL 中间态**（每行一个 Document 序列化），供数据组抽检 metadata 完整率，再进入 Splitter。字段与 [143 金标](143.golden-dataset-tutorial.md) 的 `gold_chunk_ids` 对齐时，能大幅缩短 [150 切块 bad case](150.bad-case-chunking-tutorial.md) 归因时间。

### 17.4 与 [136 Parser 协议](136.pluggable-parser-splitter-embedder-tutorial.md) 的薄适配

自研 `Parser.parse(path) -> RawDocument` 后，写 `class ParserLoader(BaseLoader)` 包装即可接入 [126 LCEL](126.langchain-lcel-tutorial.md) 生态，同时保留 [135 混合架构](135.pipeline-vs-framework-tutorial.md) 的替换能力。LangChain Loader 应 **薄**：复杂表格抽取留在 Parser 单测，不把 PDF 逻辑散落在三个 Loader 子类里。

### 17.5 巩固作业

1. 对 `data/` 下 md+pdf 跑 DirectoryLoader，统计 mime 分布与平均页数；  
2. 实现 `content_hash` 跳过未变文件，打印本轮 embed 节省比例；  
3. 故意错 encoding 复现乱码并修复；  
4. 为每条 Document 填齐 `doc_id/source/acl_group`，跑 Schema 校验；  
5. 输出 JSONL 中间态，抽 20 条人工审计 metadata；  
6. 对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 数据层清单勾选 Loader 相关项。

### 17.6 多源同步：Git、CMS 与对象存储

企业文档不止 NAS。Git 用 GitLoader 或 CI 导出 tarball 再 DirectoryLoader；只索引默认分支。CMS 用官方 API 导出 json 或 md，优于 WebLoader。对象存储用事件通知触发云函数拉取再 ingest，与 [161 索引状态机](161.index-task-state-machine-tutorial.md) 衔接。doc_id 必须稳定，不能随意用 S3 etag 除非业务确认 etag 变即内容变。

### 17.7 大文件、懒加载与 enrich

万页 PDF 禁止一次 load 进内存；用 lazy_load 按页迭代或 Parser 流式写临时文本。DirectoryLoader 加文件大小上限。扩展 metadata：product_line、effective_date（[54](54.metadata-timestamp-version-tutorial.md)），供 [88 过滤](88.metadata-filter-retrieval-tutorial.md)。Loader enrich 后 Splitter 只继承不删字段。

### 17.8 排障、Celery 与数据 KPI

空文本查扫描件 [55 OCR](55.ocr-scanned-docs-tutorial.md)、加密 PDF、Loader 选错。乱码查 [41 编码](41.text-encoding-detection-tutorial.md)。大规模 ingest 用 [159 Celery](159.celery-async-queue-tutorial.md) 投递单文件任务，[162 幂等](162.idempotent-reindex-tutorial.md)，失败进 [163 死信](163.retry-dead-letter-tutorial.md)。跟踪空文本率、乱码率、metadata 缺字段率，联动 [149 bad case](149.bad-case-parsing-tutorial.md)。

### 17.9 运营预览与清洗衔接

Loader 后增加 preview 接口给运营抽检前 500 字与 metadata，确认再进 Splitter。与 [46 文本清洗](46.text-cleaning-tutorial.md) 衔接：全角半角、页眉页脚在 Splitter 前完成。面试答：Loader 与 [136 Parser](136.pluggable-parser-splitter-embedder-tutorial.md) 边界——Loader 负责 IO 与 Document 列表；复杂版式在 Parser。

### 17.10 DirectoryLoader 与 Web 合规再强调

glob 决定递归，务必 exclude node_modules。WebLoader 注意 robots 与限速；内部 wiki 用 API 导出。用户上传防路径遍历；zip 防炸弹；加载后过 [122 安全](122.content-safety-filter-tutorial.md)。对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 数据层 C1 清单逐项勾选 Loader 能力。


Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。

Loader 调度层建议维护「待处理队列深度」指标，防止 Celery worker 积压导致文档更新延迟数日。与 [48 文档版本](48.doc-versioning-tutorial.md) 联动：版本回滚时 Loader 应能重新拉取历史版本文件路径。
""",
    "langchain-text-splitter": """
## 15. 递归切块与 Markdown 结构感知

### 15.1 Splitter 解决什么问题

[130 LangChain Text Splitter](130.langchain-text-splitter-tutorial.md) 把长 `Document` 切成适合 [25 Embedding](25.embedding-vector-tutorial.md) 与 [28 Context Window](28.context-window-tutorial.md) 的短块。C 轨已讲 [57 固定长度](57.fixed-size-chunking-tutorial.md)、[58 递归字符](58.recursive-character-chunking-tutorial.md)、[59 句子边界](59.sentence-boundary-chunking-tutorial.md)——LangChain 是这些策略的 **可配置实现**，接入 [126 LCEL](126.langchain-lcel-tutorial.md) 时通常位于 Loader 之后、VectorStore 之前。

核心矛盾见 [61 chunk 大小权衡](61.chunk-size-tradeoff-tutorial.md)：块太大语义杂、块太小上下文缺。企业制度库常见起点 `chunk_size=500～800` 字符、`chunk_overlap=50～100`，但必须用 [143 金标](143.golden-dataset-tutorial.md) 网格搜索验证，而非抄教程默认值。

### 15.2 RecursiveCharacterTextSplitter 参数深读

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=80,
    separators=["

", "
", "。", "！", "？", "；", " ", ""],
    length_function=len,
)
chunks = splitter.split_documents(docs)
```

中文制度文档应把 **句号、分号** 放进 separators，避免在词条中间切断。英文技术 doc 加 `". "`、`"; "`。`length_function` 可换为 tiktoken 计数，与 [27 Token 计费](27.token-counting-billing-tutorial.md) 一致——对接 OpenAI embed 时尤甚，字符切分可能导致 **单 chunk 超 token 上限**。

每次改 `chunk_size/overlap/separators`，索引必须 **全量重建**（除非你做段落级增量）。在 [48 版本](48.doc-versioning-tutorial.md) 记录 `splitter_config_v3`，与 [154 参数版本](154.param-version-management-tutorial.md) 对齐，避免「库是 v2 切块、新文档用 v3 切块」的隐形混合。

### 15.3 MarkdownHeaderTextSplitter 与二级流水线

[62 结构感知](62.structure-aware-chunking-tutorial.md)、[63 Markdown AST](63.markdown-ast-chunking-tutorial.md) 推荐 **先结构后细切**：

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
sections = md_splitter.split_text(md_text)
fine = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=60)
chunks = fine.split_documents(sections)
```

`metadata` 继承 `h1/h2/h3`，利于 [88 元数据过滤](88.metadata-filter-retrieval-tutorial.md)（只搜某产品章节）。代码块、表格应尽量 **整块保留**——若 Markdown AST 检测 fenced code，可先按块类型路由：prose 走递归切，code 走 [173 代码高亮](173.code-highlight-rag-tutorial（front-end）.md) 专用策略。

### 15.4 与 [64 HTML DOM](64.html-dom-chunking-tutorial.md)、[65 Parent](65.parent-document-retriever-tutorial.md) 的边界

HTML 手册常用 DOM 切块；LangChain 可用 `HTMLHeaderTextSplitter` 或自研 Parser 输出后再递归细切。Parent Document 模式：小块用于检索，大块用于生成——Splitter 要产出 **child**，并在 metadata 写 `parent_id`，供 [128 VectorStore](128.langchain-vectorstore-tutorial.md) 与 docstore 关联。

## 16. chunk_id 生成、metadata 继承与 overlap 调参

### 16.1 chunk_id 契约

[51 chunk_id](51.metadata-chunk-id-tutorial.md) 必须 **全局唯一且稳定**：同内容同配置重跑 id 不变，内容变则新 id。推荐格式 `{doc_id}:c{seq:04d}` 或 `{doc_id}:{section_hash}:{seq}`：

```python
def assign_chunk_ids(doc_id: str, chunks: list) -> list:
    for i, c in enumerate(chunks):
        c.metadata["doc_id"] = doc_id
        c.metadata["chunk_id"] = f"{doc_id}:c{i:04d}"
        c.metadata["chunk_index"] = i
    return chunks
```

禁止 Splitter 随机 UUID——否则 [49 增量](49.incremental-update-tutorial.md) 与 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 无法对齐。入库 ids 与 `chunk_id` 一致（[128 篇](128.langchain-vectorstore-tutorial.md)）。

### 16.2 继承 Loader metadata 与追加字段

Splitter **只追加** `start_index`、`chunk_id`、`chunk_index`，勿丢弃 `source/acl_group/version`。父级 `Document.metadata` 应在 `split_documents` 后复制到每个 chunk。审计时随机抽 50 chunk，检查 **acl_group 是否丢失**——丢失即 ACL 漏洞。

### 16.3 overlap 调参实验设计

准备二十条金标 QA，网格搜索 `size ∈ {300,500,800,1200}`、`overlap ∈ {0,50,80,150}`，记录 Recall@3、平均 chunk 数（成本）、Top-8 唯一 doc 数。overlap 过大时配合 [105 MMR](105.mmr-diversity-tutorial.md) 或 [106 检索去重](106.retrieval-dedup-tutorial.md)。调参结论写入 wiki，作为 [153 A/B](153.ab-experiment-rag-tutorial.md) 基线。

### 16.4 TokenTextSplitter 与多语言

混合中英文库可按 `metadata.lang` 选不同 Splitter 实例——注册表见 [136 可插拔](136.pluggable-parser-splitter-embedder-tutorial.md)。日文、韩文无空格语系要调整 separators，避免单字符切块。

## 17. 质量审计、bad case 与全链衔接

### 17.1 人工审计与断裂样例库

随机抽 50 chunk 人工看：**句界是否断裂、标题是否丢失、代码是否腰斩**。断裂样例存入 [144 回归集](144.regression-test-set-tutorial.md)，归因入口 [150 切块错误](150.bad-case-chunking-tutorial.md)。与运营共建 **「不可切断」规则**（如法律条文编号、API 签名）。

### 17.2 同一文件：固定长度 vs 递归 diff

用 [57 固定](57.fixed-size-chunking-tutorial.md) 与 [58 递归](58.recursive-character-chunking-tutorial.md) 对同一文件切块，diff 首尾边界。向团队演示：**递归在段落边界更自然**，固定长度实现简单但 FAQ 类文档易断句。

### 17.3 金标 Recall 对比作业

选一条金标问句，对比 `overlap=0` 与 `overlap=80` 的 Recall@5。通常 overlap 略升 Recall，但升 [76 Chroma](76.chroma-vector-db-tutorial.md) 存储与检索冗余——用数据说话，不写玄学。

### 17.4 接入 [127 Retriever](127.langchain-retriever-tutorial.md) 前的检查

切块完成后、embed 之前：统计 **平均每 doc chunk 数、空 chunk 数、超长 chunk 数**。空列表要打 warn 并记 [149 解析归因](149.bad-case-parsing-tutorial.md)。超长 chunk 要么二次切，要么换 Token 切分。

### 17.5 与路线图和可插拔协议

[ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 数据层要求掌握 [57-65] 切块系列；D 轨 [136](136.pluggable-parser-splitter-embedder-tutorial.md) 要求 Splitter 可替换。实现 `Protocol` + 注册表后，LangChain `TextSplitter` 子类只做 **薄适配**，核心逻辑单测不依赖 LangChain。

### 17.6 三十分钟清单

1. Markdown 二级标题切块 + 递归细切流水线跑通；  
2. 全 chunk 写入 `chunk_id` 并 `assert` 唯一；  
3. 网格一组 size/overlap 写进表格；  
4. 抽 10 chunk 给同事盲审断裂率；  
5. 画 Parser→Splitter→Embedder→[75 FAISS](75.faiss-ann-tutorial.md)/[76 Chroma](76.chroma-vector-db-tutorial.md) 全链白板。

### 17.7 表格、列表、FAQ 与法律条款切分

制度 PDF 常含编号列表。先用正则识别条款边界再递归细切。FAQ 按问答对切，Recall 对问答查询高。小表整表一切，大表按行切，配合 [37 PDF 表格](37.pdf-layout-tables-tutorial.md)。法律文本 separators 优先句号，英文合同加句点空格。策略对比写入 [143 金标](143.golden-dataset-tutorial.md) 再固化 REGISTRY。

### 17.8 语义切分、变更管理与版本

语义切分按 embed 断点，成本高，记录 splitter=semantic_v1 到 manifest。任何 chunk_size 或 overlap 变更等于新索引版本：PR 附金标表、[144 回归](144.regression-test-set-tutorial.md)、夜间重建、蓝绿切换，见 [48 版本](48.doc-versioning-tutorial.md) 与 [154 参数版本](154.param-version-management-tutorial.md)。

### 17.9 与 MMR、去重、批处理联动

overlap 高时用 [106 去重](106.retrieval-dedup-tutorial.md) 或 [105 MMR](105.mmr-diversity-tutorial.md)。上万 chunk 按 section 批切批 embed（[67](67.embedding-batching-tutorial.md)）批 upsert [128](128.langchain-vectorstore-tutorial.md)。混合语言用 metadata.lang 路由 Splitter，登记 [136 REGISTRY](136.pluggable-parser-splitter-embedder-tutorial.md)。

### 17.10 FAQ 与 LangChain 版本锁定

chunk_size 用字符还是 token？中文常字符，OpenAI embed 用 token，见 [27 计费](27.token-counting-billing-tutorial.md)。代码块尽量整块，见 [173 代码 RAG](173.code-highlight-rag-tutorial（front-end）.md)。overlap 不是越大越好。锁定 langchain-text-splitters 版本，升级后跑回归，防 silently 改边界。向产品展示无 overlap 时证据被切成两半的示意图。


对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。

对 [62 结构感知](62.structure-aware-chunking-tutorial.md) 手册，可先用 MarkdownHeader 产出 section 级 chunk 做目录检索，再对超长 section 递归细切，形成两级索引策略，metadata 写 section_level=1 或 2。
""",
    "llamaindex-index-types": """
## 15. 了解即可：LlamaIndex 索引类型全景

### 15.1 为何本篇标「了解即可」

[企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) D 轨主线是 LangChain [125-127](125.langchain-core-tutorial.md)。[131 LlamaIndex 索引类型](131.llamaindex-index-types-tutorial.md) 的价值在于 **面试对照、读开源项目、理解「索引」一词在不同框架中的外延**——不必双栈精通。时间优先级：先扎实 [128 VectorStore](128.langchain-vectorstore-tutorial.md)、[129 Loader](129.langchain-document-loader-tutorial.md)、[130 Splitter](130.langchain-text-splitter-tutorial.md)，再花 **不超过两小时** 阅读 LlamaIndex 官方 Understanding/Indexing 章节。

LlamaIndex 把文档组织单元叫 **Node**（类似增强版 `Document`，可带前后关系）。**Index** 是 Node 的容器 + 构建时策略。**VectorStoreIndex** 是最接近日常 RAG 的类型：构建时 embed 并写入向量后端（概念上对接 [76 Chroma](76.chroma-vector-db-tutorial.md)、[75 FAISS](75.faiss-ann-tutorial.md)）。其它索引类型多用于特定 demo 或研究——知道名词即可，生产制度问答 **九成场景 VectorStoreIndex 足够**。

### 15.2 StorageContext 三件套

LlamaIndex 用 **StorageContext** 绑定 `vector_store`、`docstore`、`index_store`。可粗略映射：vector_store ≈ LC VectorStore；docstore ≈ 原文/KV 存储（Parent 模式见 [65 篇](65.parent-document-retriever-tutorial.md)）；index_store ≈ 索引结构元数据。**了解即可**：Index 不等于磁盘路径；持久化要理解三件套各自存什么，否则迁移项目时只拷向量文件会丢关联。

### 15.3 VectorStoreIndex 构建时机

`VectorStoreIndex.from_documents` 在 **构建期** 调 embed（与 [25 Embedding](25.embedding-vector-tutorial.md) 同构），查询期主要做 retrieve。LangChain 往往 Loader→Splitter→`from_documents` 更 **流水线显式**；LlamaIndex 一行 API 把 ingest 包进 Index 构建。面试话术：「我能说清 LI 构建期 embed 与 LC 分步 ingest 的差异；生产主栈用 LC 是为可控批处理、manifest 与 [136 可插拔](136.pluggable-parser-splitter-embedder-tutorial.md) 契约。」

### 15.4 与 C 轨向量库的映射表

| LlamaIndex 概念 | LangChain / C 轨近似 |
|-----------------|----------------------|
| VectorStoreIndex | [128] Chroma/FAISS + ingest |
| Node | Document + 关系 |
| StorageContext | collection + docstore |
| embed_model | [25] Embeddings |

## 16. 了解即可：SummaryIndex、TreeIndex 与 ComposableGraph

### 16.1 SummaryIndex 适用边界

**SummaryIndex**（旧名 ListIndex）把文档串联或逐条摘要，适合 **页数少、需要通读感** 的 demo（如十页投资备忘录）。企业上千 PDF 制度库若用 SummaryIndex 通读，成本和延迟都不现实。**了解即可**：知道它存在，别在生产手册库默认启用。

### 16.2 TreeIndex 与层次化手册

**TreeIndex** 通过树状摘要组织章节，适合 **层次化实验** 或研究型「从根到叶」查询。运维复杂、构建慢、调试难。**了解即可**：与 [62 结构感知切块](62.structure-aware-chunking-tutorial.md) 不同层——TreeIndex 是索引层树，不是 Markdown 标题切块。主线 RAG 仍用扁平 chunk + [88 元数据过滤](88.metadata-filter-retrieval-tutorial.md)。

### 16.3 ComposableGraph 多库路由

**ComposableGraph** 把多个子 Index 组成图，查询时路由到子库。概念上类似多 collection（[89 多租户](89.multi-tenant-namespace-tutorial.md)），但 **图路由 + 汇总** 延迟更高。了解即可：读多知识库合并的开源方案时能认出架构；自研时用 [127 Retriever](127.langchain-retriever-tutorial.md) 多路 + [94 RRF](94.rrf-fusion-tutorial.md) 往往更透明。

### 16.4 面试三问三答

| 面试题 | 简答 |
|--------|------|
| LI 有哪些索引类型 | Vector/Summary/Tree/Keyword 等，生产主用 Vector |
| Node 与 Document | Node 可带关系与索引指针，Document 更轻 |
| 你会迁移整套 LI 吗 | 否，主栈 LC；LI 作阅读对照 |

## 17. 了解即可：动手边界、阅读顺序与框架取舍

### 17.1 推荐动手边界

安装 `llama-index`，跑通官方 **最小 VectorStoreIndex 查询** 即可：加载两三份 md、构建、打印 `source_nodes`。不必部署 LlamaCloud、不必配齐全部索引类型。**省下的时间** 用于 [135 框架 vs 自研](135.pipeline-vs-framework-tutorial.md) 工作坊与 [143 金标](143.golden-dataset-tutorial.md) 建设——那才是企业区分度。

### 17.2 阅读顺序（两小时版）

1. 官方文档 Understanding：Node、Index、StorageContext（30 分钟）；  
2. 对照本篇 §15 映射表与 [128 LC VectorStore](128.langchain-vectorstore-tutorial.md) 画一张双栏图（30 分钟）；  
3. 扫一眼 SummaryIndex/TreeIndex API 签名，不写生产代码（20 分钟）；  
4. 读 [132 Query Engine](132.llamaindex-query-engine-tutorial.md) 预告查询侧一站式 API（20 分钟）；  
5. 在笔记写三句话：**我何时选 LC 而非 LI**（20 分钟）。

### 17.3 与 [135 pipeline-vs-framework](135.pipeline-vs-framework-tutorial.md) 的关系

框架选型不是信仰。LlamaIndex 擅长 **研究型原型、快速 Index 实验**；LangChain 擅长 **与 [126 LCEL](126.langchain-lcel-tutorial.md)、[124 Function Calling](124.function-calling-tool-use-tutorial.md)、企业自研 [136 协议](136.pluggable-parser-splitter-embedder-tutorial.md) 拼接**。了解 LI 索引类型，是为了 **不被面试官带偏**——「听过 TreeIndex」不等于「应用 TreeIndex 上线」。

### 17.4 与切块、embed 路线的衔接

无论 LI 还是 LC，**切块** 仍遵守 [57-65](57.fixed-size-chunking-tutorial.md) 规律；**向量** 仍遵守 [25](25.embedding-vector-tutorial.md)、[66 归一化](66.l2-normalization-tutorial.md)、换模型重建 collection 的纪律。索引类型换不了烂切块——[150 bad case](150.bad-case-chunking-tutorial.md) 仍要从 Splitter 查起。

### 17.5 巩固自检（了解即可）

1. 能白板画出 StorageContext 三件套；  
2. 能说出 VectorStoreIndex 与 LC `from_documents` 的三点差异；  
3. 能拒绝在生产手册库上 SummaryIndex 通读的理由（成本、延迟、可观测）；  
4. 对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) D 轨，确认主线仍 LangChain 125-130。

### 17.8 KeywordTable 与稀疏路（了解即可）

KeywordTableIndex 思想接近 [92 稀疏检索](92.sparse-retrieval-rag-tutorial.md)。生产多用 BM25 加向量 [93 混合](93.hybrid-search-tutorial.md)，不必在 LI 内换索引类型。了解即可。

### 17.9 开源定位、Agent 依赖与分工

追 StorageContext 可知后端是 Chroma 还是别的。ComposableGraph 是多库路由。SummaryIndex 慎用于大库。Query Engine 与 Agent 都依赖索引质量，回到 [57-65 切块](57.fixed-size-chunking-tutorial.md) 与 [25 embed](25.embedding-vector-tutorial.md)。一人深钻 LC 128-130，一人两小时产 LI-LC 对照 wiki。

### 17.10 面试、笔记模板与 LlamaCloud

面试只画 VectorStoreIndex 主路径与 StorageContext 三件套。笔记表：LI 概念、LC 映射、是否生产采用、理由。LlamaCloud 了解即可不自托管主线。LI 与 LC 可共享 [76 Chroma](76.chroma-vector-db-tutorial.md) 后端，但 chunk_id 契约须统一。对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) D 轨，主阅读不超过两小时。


读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。

读 LI 文档时注意区分 Index 构建期 embed 与查询期 retrieve 的配置项，混淆二者会导致「建库用 A 模型、查询用 B 模型」的隐性 bug，与 LC 侧 ingest/query 共用 Embeddings 实例的纪律相同。
""",
    "llamaindex-query-engine": """
## 15. 了解即可：Query Engine 是什么

### 15.1 一站式查询 vs LCEL 分步

[132 LlamaIndex Query Engine](132.llamaindex-query-engine-tutorial.md) 把 **检索 + 拼装 + LLM 合成** 封装成 `query_engine.query(question)`，返回 `Response` 对象。LangChain [126 LCEL](126.langchain-lcel-tutorial.md) 则鼓励 **Runnable 分步**：`retriever | format_docs | prompt | llm`，每步可插观测、缓存、拒答分支（[112 拒答](112.refusal-strategy-tutorial.md)）。

**了解即可**：不是二选一生死战，而是 **封装粒度** 差异。企业固定 RAG 更常用 **显式 LCEL + [110 Prompt 模板](110.rag-prompt-template-tutorial.md)**，因为审计、引用格式（[113 行内引用](113.inline-citation-tutorial.md)、[114 脚注](114.footnote-citation-tutorial.md)）要在链上可见。LI Query Engine 适合快速验证检索质量，再拆步迁移到 LC。

### 15.2 Response 与 source_nodes

`response.response` 是答案文本；`response.source_nodes` 含 `node_id、score、metadata`——对应 [34 Grounding](34.grounding-citation-tutorial.md) 与 [115 溯源导航](115.source-document-navigation-tutorial.md)。对比 LC 里手写的 `format_docs` + citations 列表，**结构类似、字段名不同**。读 LI 开源项目时，先找 `source_nodes` 生成点，等价于在 LC 找 `retriever.invoke` 之后。

### 15.3 与 [127 Retriever](127.langchain-retriever-tutorial.md) 的概念映射

| Query Engine 侧 | LangChain 侧 |
|---------------|--------------|
| retriever | [127] BaseRetriever |
| response_synthesizer | prompt + llm |
| query_bundle | 原始 query + 改写 |

检索策略（k、filter、MMR）仍遵守 [98 top-k](98.top-k-retrieval-tutorial.md)、[105 MMR](105.mmr-diversity-tutorial.md)、[121 ACL](121.unauthorized-doc-filter-tutorial.md)——框架不换物理定律。

## 16. 了解即可：response_mode 与合成策略

### 16.1 compact、tree_summarize、refine

| 模式 | 行为 | 企业风险 |
|------|------|----------|
| compact | 压缩证据进单次 LLM | 长上下文贵，[107 预算](107.context-budget-tutorial.md) 易爆 |
| tree_summarize | 分层摘要再答 | 延迟高，难 debug |
| refine | 多轮迭代 refine | 成本叠加，引用漂移 |

**了解即可**：制度 FAQ 常用 **固定模板单次生成**，而非 LI 黑盒 synthesizer。若用 compact，要手动限制 `source_nodes` 数量，与 [107 上下文预算](107.context-budget-tutorial.md) 一致。

### 16.2 流式与 [116 SSE](116.sse-rag-streaming-tutorial.md)

`streaming=True` 时逐 token 输出，对接前端打字机。LC 侧用 `chain.astream` + 应用层 SSE 事件包装。了解 LI 流式 API 即可，生产事件契约（`delta/citations/done`）建议 **自研统一**（[117 WebSocket](117.websocket-rag-streaming-tutorial.md) 同构）。

### 16.3 ChatEngine 与多轮

**ChatEngine** 包装多轮历史，类似 [118 多轮历史](118.multi-turn-history-tutorial.md) + [109 查询增强](109.conversation-query-enhancement-tutorial.md)。关键产品决策：**每轮是否重检索**——与框架无关。了解即可：读 LI demo 时不要假设它默认每轮检索；看 `chat_mode` 配置。

### 16.4 空检索与拒答

LI 可配 `empty_query_mode` 或自定义 synthesizer；LC 用 `RunnableBranch`。无论哪边，**空检索必须拒答或澄清**（[112](112.refusal-strategy-tutorial.md)），勿让 LLM 无证据编造（[33 幻觉](33.llm-hallucination-tutorial.md)）。

## 17. 了解即可：观测、面试话术与阅读建议

### 17.1 观测字段

记录：`query, latency_retrieve, latency_synth, source_node_ids, embed_model, prompt_version`。与 [147 LangSmith](147.langsmith-tracing-tutorial.md)、[148 Langfuse](148.langfuse-observability-tutorial.md) 对齐时，把 LI 的 `query` span 映射到 LC 的 `retriever` + `llm` 两段，便于混合栈排障。

### 17.2 与混合检索、rerank 的边界

Query Engine 默认向量检索；若要 [93 混合](93.hybrid-search-tutorial.md) 或 [95 rerank](95.cross-encoder-rerank-tutorial.md)，在 LI 要换 retriever 组件或自定义。了解即可：**一站式不等于全功能**，复杂检索仍要拆步——这也是企业偏向 LC + [136/137 可插拔](137.pluggable-store-retriever-generator-tutorial.md) 的原因。

### 17.3 面试标准话术

「我熟 LangChain LCEL 组装检索与生成，能在链上实现 ACL、引用与拒答；了解 LlamaIndex Query Engine 的 `Response/source_nodes` 与 response_mode，读 LI 项目时能快速定位检索段，但生产主路径是可控的 LC + 自研 Retriever。」

### 17.4 两小时阅读路径

1. 官方 Query Engine 入门示例（30 分钟）；  
2. 打印 `source_nodes` 与 [34 Grounding](34.grounding-citation-tutorial.md) 对照（20 分钟）；  
3. 读 [133 Agent](133.llamaindex-agent-tutorial.md) 预告工具调用（20 分钟）；  
4. 画 LC 等价链：retriever→format→prompt→llm（30 分钟）；  
5. 对照 [135 框架取舍](135.pipeline-vs-framework-tutorial.md) 写何时不选 Query Engine 黑盒（20 分钟）。

### 17.5 与路线图、向量库基础

[ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 服务层要求 **来源引用、流式、权限**——这些在 LC 链上更显式。向量库底层仍建议先学 [76 Chroma](76.chroma-vector-db-tutorial.md)、[75 FAISS](75.faiss-ann-tutorial.md)，再谈 Query Engine，否则 `source_nodes` 分数异常时无法排障。

### 17.6 自检（了解即可）

1. 说出 Response 两个核心字段；  
2. 说出 compact 的成本风险；  
3. 画出 LC 等价最小 RAG 链；  
4. 明确生产为何不默认 tree_summarize。

### 17.7 SubQuestion 与多跳（了解即可）

子问题引擎接近 [103 分解](103.query-decomposition-tutorial.md) 与 [104 多跳](104.multi-hop-retrieval-tutorial.md)。企业可先固定分解加 [127 Retriever](127.langchain-retriever-tutorial.md)。对照 [101 多查询](101.multi-query-retrieval-tutorial.md)。

### 17.8 引用、Prompt 版本与缓存 ACL

强制 [113 引用](113.inline-citation-tutorial.md) 与 [115 溯源](115.source-document-navigation-tutorial.md)。Prompt 版本对齐 [110](110.rag-prompt-template-tutorial.md)，换 prompt 跑 [144 回归](144.regression-test-set-tutorial.md)。缓存 key 含 principal 与 filter，防 [121 ACL](121.unauthorized-doc-filter-tutorial.md) 越权。

### 17.9 金标对比、多轮与流式统一

同一 [143 金标](143.golden-dataset-tutorial.md) 对比 LI 与 LC 的 Recall、延迟、引用率。ChatEngine 多轮见 [118](118.multi-turn-history-tutorial.md)，每轮是否重检索要写清。流式与 [116 SSE](116.sse-rag-streaming-tutorial.md) 事件契约在应用层统一。了解 LI 为接口设计，非永久双栈。底层仍须 [76 Chroma](76.chroma-vector-db-tutorial.md)、[75 FAISS](75.faiss-ann-tutorial.md)。


评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。

评测 LI Query Engine 时，记录 synthesizer 类型与 response_mode，否则三个月後无法复现当时原型数字。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时，LI 一站式链也要拆出 hit_ids 对齐金标。
""",
    "llamaindex-agent": """
## 15. 了解即可：LlamaIndex Agent 与工具体系

### 15.1 Agent 在 RAG 中的位置

[133 LlamaIndex Agent](133.llamaindex-agent-tutorial.md) 让 LLM **多步选择工具**（如 `QueryEngineTool`、计算器、外部 API），循环「思考→调用→观察」直到生成最终答案。思想与 [124 Function Calling](124.function-calling-tool-use-tutorial.md) 同源，与 [104 多跳检索](104.multi-hop-retrieval-tutorial.md) 有交集——但 **多跳不等于 Agent**，固定管道 + 查询分解往往更可控。

[企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) 强调可观测、合规、成本。Agent 默认 **延迟高、路径不确定、审计难**。**了解即可**：掌握名词与风险，生产 FAQ 优先固定检索链（[127 Retriever](127.langchain-retriever-tutorial.md) + [110 Prompt](110.rag-prompt-template-tutorial.md)），Agent 用于 **探索型 PoC** 或研发内工具。

### 15.2 QueryEngineTool 与检索边界

`QueryEngineTool` 把某个 Index/Query Engine 包成工具，Agent 决定是否调用。工具内部 Retriever **必须** 带 [121 ACL](121.unauthorized-doc-filter-tutorial.md) 与 [98 top-k](98.top-k-retrieval-tutorial.md)，principal 从服务端 JWT 来，**不信任模型传的租户字段**。即使 Agent 选错工具，最后一道闸仍在工具实现里——与 [124 search_kb](124.function-calling-tool-use-tutorial.md) 纪律相同。

### 15.3 迭代预算与超时

生产 Agent 必设：`max_iterations=3～5`、单次 tool `timeout=30s`、总 `deadline=120s`。否则模型可能 **循环检索** 烧光 token（[27 计费](27.token-counting-billing-tutorial.md)）。日志记录每轮：`tool_name、参数哈希、latency_ms、source_node_ids`（勿存 PII 原文到 thought 日志）。

## 16. 了解即可：与固定管道、LangChain 工具对比

### 16.1 固定 RAG vs Agent 对照表

| 维度 | 固定 RAG | Agent |
|------|----------|-------|
| 延迟 | 低 | 高 |
| 可预测性 | 高 | 低 |
| 多跳 | 需 [104] 或规则 | 模型自规划 |
| 合规审计 | 易复现 hit_ids | 难复现推理链 |
| 成本 | 一次检索+生成 | 多轮 LLM+工具 |

**了解即可**：默认固定管道；Agent 需书面迭代上限与工具白名单。金融场景见 [135 案例 B](135.pipeline-vs-framework-tutorial.md)。

### 16.2 LangChain Agent 对照

LC 侧 `create_react_agent`、`bind_tools` 与 LI Agent 类似。主栈 LC 时，读 LI Agent 源码是为了 **理解工具描述写法**（何时调用、何时不调用）——坏描述会导致该搜不搜、不该搜乱搜。工具改名要版本化。

### 16.3 流式与 UI

Agent 循环阶段通常 **非流式**，UI 应显示「正在查资料」；最终答案步可接 [116 SSE](116.sse-rag-streaming-tutorial.md)。不要试图让模型边流式边输出合法工具 JSON。

## 17. 了解即可：治理、观测与面试收尾

### 17.1 工具 ACL 与内容安全

工具返回的 chunk 也要过 [122 内容安全](122.content-safety-filter-tutorial.md)。不要开放任意代码执行工具；SQL 参数化；API 工具要鉴权。Agent 放大攻击面——**了解即可** 不等于 **默认可上线**。

### 17.2 观测与 [147-148 追踪](147.langsmith-tracing-tutorial.md)

每轮 tool 调用一个 span，属性含 `tool_name、k、filter、hit_count`。与固定链对比，Agent trace 更深，存储成本更高——PoC 可开，生产采样。

### 17.3 何时考虑 Agent（了解即可）

- 用户意图跨越 **多个子库** 且无法规则路由；  
- 需要 **计算器/结构化 API** 与检索混用；  
- 研发内 **调试助手**，非面向外部客户。  

否则 [103 查询分解](103.query-decomposition-tutorial.md) + 固定多检索往往够用。

### 17.4 阅读与动手边界

安装 `llama-index`，跑官方 **单 Agent + QueryEngineTool** 示例，观察 2～3 轮工具调用日志即可。不必调优 ReAct prompt 上线。时间留给 [128-130](128.langchain-vectorstore-tutorial.md) 与 [136 可插拔](136.pluggable-parser-splitter-embedder-tutorial.md)。

### 17.5 面试话术

「知道 LlamaIndex Agent 与 QueryEngineTool 的迭代结构；生产优先可控检索链，Agent 需 max_iterations、工具 ACL、timeout，并记录每轮 tool 与 hit_ids。多跳场景先评估 [104] 固定分解，再考虑 Agent。」

### 17.6 与向量库、切块基础

Agent 工具内部的索引仍建立在 [25 Embedding](25.embedding-vector-tutorial.md)、[76 Chroma](76.chroma-vector-db-tutorial.md)、[57-65 切块](57.fixed-size-chunking-tutorial.md) 之上。Agent 层再花哨，**烂切块仍导致工具返回垃圾**——排障顺序：证据质量 → 检索参数 → Agent 策略。

### 17.7 自检（了解即可）

1. 说出三项 Agent 生产红线（迭代、超时、ACL）；  
2. 对比固定 RAG 与 Agent 的审计难度；  
3. 说明 QueryEngineTool 内必须强制 filter 的理由；  
4. 对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 确认 Agent 非主线必修。

### 17.8 ReAct、多 Agent 与安全（了解即可）

ReAct 与 OpenAI tools 提示不同，治理相同：ACL、迭代上限、日志。见 [124 Function Calling](124.function-calling-tool-use-tutorial.md)。多 Agent 运维成本高，默认单 Agent 或固定链。

### 17.9 红队、多跳选择与观测

文档注入诱导调工具——缓解靠工具描述、[122 安全](122.content-safety-filter-tutorial.md)、禁高危工具。对比 [104 多跳](104.multi-hop-retrieval-tutorial.md)：固定链易评测，Agent 难审计；金标够好则勿上 Agent。thought 日志脱敏；[147 LangSmith](147.langsmith-tracing-tutorial.md) 单独 agent trace。

### 17.10 多轮、产出物与基础

多轮见 [118](118.multi-turn-history-tutorial.md)。一页纸：组件图、三项红线、bind_tools 对照、为何不默认 Agent。Agent 工具内索引仍靠 [25 embed](25.embedding-vector-tutorial.md) 与 [57-65 切块](60.chunk-overlap-tutorial.md)。对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 确认 Agent 非主线。


Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。

Agent 上线前必须做「工具不被调用」与「工具被滥用」两类对抗测试：前者测该搜不搜，后者测恶意文档诱导。结果写入 [152 幻觉 bad case](152.bad-case-hallucination-tutorial.md) 子集。
""",
    "haystack-pipeline": """
## 15. 了解即可：Haystack Pipeline 显式组件图

### 15.1 Haystack 在 D 轨中的定位

[134 Haystack Pipeline](134.haystack-pipeline-tutorial.md) 用 **有向图** 连接 DocumentStore、Retriever、Ranker、Generator 等组件，`connect(output_socket, input_socket)` 强制 **端口类型匹配**，接错线在编译期失败。LangChain [126 LCEL](126.langchain-lcel-tutorial.md) 用 `|` 管道符表达数据流，类型检查较弱。

[企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) 主栈若是 LangChain，Haystack 是 **设计模式参考书**，不是必须迁移的第二框架。**了解即可**：借其「显式图、可序列化、组件单测」思想改进自研 DAG（[135 框架 vs 自研](135.pipeline-vs-framework-tutorial.md)）。

### 15.2 ingest 图与 query 图分离

Haystack 教程常画两张图：**索引管道**（fetch→convert→split→embed→write）与 **查询管道**（embed query→retrieve→rank→prompt→generate）。这与 C 轨 ingest/query 分离一致。对照 LC：[129 Loader](129.langchain-document-loader-tutorial.md)→[130 Splitter](130.langchain-text-splitter-tutorial.md)→[128 VectorStore](128.langchain-vectorstore-tutorial.md) 是 ingest；[127 Retriever](127.langchain-retriever-tutorial.md)→LCEL 是 query。手绘 Haystack 风格双图，再画 LC 等价图，标注差异——**两小时收获大于通读 Haystack 全 API**。

### 15.3 与 [76 Chroma](76.chroma-vector-db-tutorial.md)、[75 FAISS](75.faiss-ann-tutorial.md) 后端

Haystack 2.x 支持多种 DocumentStore；底层仍是你学过的向量库。换 Haystack 不免去学 ANN、metadata filter、持久化——初学者勿跳过 [75][76] 直接抄 Haystack YAML。

## 16. 了解即可：序列化、配置与混合检索图

### 16.1 Pipeline YAML 与 [138 配置驱动](138.config-driven-pipeline-tutorial.md)

Haystack 可把 Pipeline 导出 YAML，运维改 `top_k`、换 Ranker 而不改 Python 入口。LangChain 可用配置生成 LCEL 或工厂函数（[136 注册表](136.pluggable-parser-splitter-embedder-tutorial.md)）。**了解动机即可**：参数版本进 [154 参数版本](154.param-version-management-tutorial.md)，与 [143 金标](143.golden-dataset-tutorial.md) 评测绑定。

### 16.2 双 Retriever + Joiner 与 [93 混合](93.hybrid-search-tutorial.md)

Haystack 常见 **BM25 + Embedding Retriever → Joiner**（[94 RRF](94.rrf-fusion-tutorial.md)）。图上一眼可见稠密/稀疏两路，适合架构评审 PPT。LC 用 `EnsembleRetriever` 实现类似效果。了解即可：混合检索的 **物理组件** 在 Haystack 更醒目，在 LC 更靠组合模式。

### 16.3 组件单测与 [149 bad case](149.bad-case-parsing-tutorial.md)

每个 Component 单独 `run()` 测输入输出，比整条链黑盒测易定位问题。自研管道应借鉴：Parser、Splitter、Embedder、Store 各有契约测试（[136 篇](136.pluggable-parser-splitter-embedder-tutorial.md)），而非只测端到端答案字符串。

### 16.4 Ranker 与 [95 rerank](95.cross-encoder-rerank-tutorial.md)

Haystack 把 Cross-Encoder 放在 Ranker 组件；LC 常在 retriever 后接 `ContextualCompressionRetriever` 或自研 rerank。了解端口命名 `documents` vs `query` 即可，不必背全 Ranker 参数。

## 17. 了解即可：不必全盘迁移、作业与面试

### 17.1 何时不值得迁 Haystack

团队已投入 [125-130](125.langchain-core-tutorial.md)、[136-138 可插拔](138.config-driven-pipeline-tutorial.md)，且 on-call 熟 LC——**为「显式图」全盘迁 Haystack 成本极高**。更优：在自研 `pipeline.yaml` 里用 **边带 schema 名**（`documents: list[Chunk]`），编译期校验连接。

### 17.2 可从 Haystack 抄的清单

1. ingest/query 双图文档模板；  
2. 组件 IO 契约表；  
3. YAML 驱动的 top_k、filter、ranker 开关；  
4. 混合检索 Joiner 在架构图的画法；  
5. 每组件 metrics：`in_count、out_count、latency_ms`。

### 17.3 与 LlamaIndex、LC 三角对照

| 能力 | Haystack | LangChain | LlamaIndex |
|------|----------|-----------|------------|
| 显式图 | 强 | 中（LCEL） | 中（QueryEngine 黑盒） |
| 生态广度 | 中 | 强 | 中 |
| 企业可插拔 | 需适配 | 需适配 | 需适配 |

结论：**框架是皮，[25 embed](25.embedding-vector-tutorial.md)、[57-65 切块](58.recursive-character-chunking-tutorial.md)、[76 存储](76.chroma-vector-db-tutorial.md) 是骨**。

### 17.4 面试话术

「主栈 LangChain LCEL + 自研 Retriever；了解 Haystack 的 Pipeline 显式连接与 YAML 序列化，用其图论思想设计自家 ingest/query DAG 与契约测试，而非引入双框架运维。」

### 17.5 了解即可作业

手绘 ingest 与 query 两张 Haystack 风格图，各画一张 LC 等价图，标注 **filter、ACL、rerank、citations** 在图中的位置。对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 服务层与工程化层检查项。

### 17.6 阅读时间盒

官方 Haystack **Pipeline 入门 + 混合检索教程** 各一篇，合计不超过 90 分钟；其余时间做 [135 工作坊](135.pipeline-vs-framework-tutorial.md) 与金标建设。不要在一个周末同时深钻 Haystack 与 LlamaIndex——D 轨深度优先 LC 128-136。

### 17.7 自检

1. 说出 `connect` 的类型检查价值；  
2. 画出 BM25+Dense 双路 Joiner；  
3. 说明为何不盲目迁 Haystack；  
4. 指向 [137 Store/Retriever/Generator](137.pluggable-store-retriever-generator-tutorial.md) 与 Haystack 组件的粗略映射。

### 17.8 版本差异与 compile 草图（了解即可）

老 add_node 与新 connect 不同，勿混用旧博客。自研 compile_pipeline 读 yaml 的 nodes 与 edges，边列表进 Git review，借鉴 Haystack 不必引入其 runtime。

### 17.9 可观测、138 配置与 137 映射

每组件 metrics：out_count、avg_chunk_len、batch_ms、upsert_ms。[148 Langfuse](148.langfuse-observability-tutorial.md) 分 ingest 与 query trace。[138 配置](138.config-driven-pipeline-tutorial.md) 加显式图。DocumentWriter 映射 [137 Store](137.pluggable-store-retriever-generator-tutorial.md)；Retriever 与 Generator 同理。

### 17.10 评审话术、时间盒与 Eval 思想

同事要换 Haystack：采纳 YAML 与图，保留 LC，两周交 pipeline.yaml 原型。阅读不超过 90 分钟。Eval 思想可借鉴 [139-142 RAGAS](139.ragas-context-precision-tutorial.md)，不必引入 Haystack Eval。主栈 LC 125-130；Haystack 与 [131 LI](131.llamaindex-index-types-tutorial.md) 对照。骨干仍是 [25 embed](25.embedding-vector-tutorial.md) 与 [58 递归切](58.recursive-character-chunking-tutorial.md)。


手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。

手绘 Haystack ingest 图时，在 Joiner 节点旁标注 RRF 参数 k（[94](94.rrf-fusion-tutorial.md)），在 Ranker 旁标注 cross-encoder 模型版本（[95](95.cross-encoder-rerank-tutorial.md)），养成「图上有参数版本」习惯。
""",
    "pipeline-vs-framework": """
## 15. 框架与自研：决策深度与分层模型

### 15.1 问题本身比答案更重要

[135 Pipeline vs Framework](135.pipeline-vs-framework-tutorial.md) 不是「LangChain 好还是坏」的站队，而是：**在 ingest、检索、生成、观测四段，哪些必须用框架胶水，哪些必须用自研核心**。 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) 要求交付 **可演示、可观测、可迭代** 的全栈产品——框架 demo 离此差 **metadata 契约、ACL、评测、幂等 ingest、引用契约** 五座山。

决策深度应达到：能画 **分层表**（数据/索引/服务/应用/工程化），每格写「LC / 自研 / 混合」及 **回滚预案**。浅层答案「小公司用 LC，大公司自研」在面试里不合格——要讲 **团队阶段、合规等级、QPS、变更频率**。

### 15.2 推荐分层表（模板）

| 层级 | 典型组件 | 建议 |
|------|----------|------|
| 数据 | Parser/Splitter | 自研协议 [136] + LC Loader 薄适配 |
| 索引 | Embed/Store | 自研批处理 + LC 或原生 [76 Chroma](76.chroma-vector-db-tutorial.md) |
| 检索 | Retriever/混合 | 自研策略 + [127] 接口 |
| 编排 | LCEL/Agent | LC [126] 优先，Agent 谨慎 |
| 生成 | Prompt/LLM | 自研模板 [110] + 网关 |
| 观测 | Trace/评测 | 自研日志 + [147-148] |

框架价值在 **编排与快速试错**；企业护城河在 **数据契约、权限、评测、成本**。

### 15.3 何时框架足够

- 单人/双人 PoC，3 个月内验证业务；  
- 文档形态单一（md+pdf），[129-130](129.langchain-document-loader-tutorial.md) 够用；  
- 无强合规 ACL，[121](121.unauthorized-doc-filter-tutorial.md) 要求弱；  
- 检索 **单向量 + top_k** 即可，尚未需要 [93 混合](93.hybrid-search-tutorial.md)。

此时 [125-128](125.langchain-core-tutorial.md) 全链 LC 是理性选择，但应 **尽早** 抽 [136 协议](136.pluggable-parser-splitter-embedder-tutorial.md)，避免业务逻辑写进 LLMChain 回不去。

### 15.4 何时必须自研核心

- 金融/政务 ACL、审计留痕；  
- 多租户 [89](89.multi-tenant-namespace-tutorial.md) 与复杂 filter；  
- 混合检索 + [95 rerank](95.cross-encoder-rerank-tutorial.md) + 自定义分数融合；  
- 索引百万级，需 [75 FAISS](75.faiss-ann-tutorial.md)/Milvus 调优；  
- [143 金标](143.golden-dataset-tutorial.md) 驱动发版，框架升级不能破坏 Recall。

自研不是重写 LangChain，而是 **厚接口 + 薄适配器**（[137 篇](137.pluggable-store-retriever-generator-tutorial.md)）：核心可单测，LC 只做 Embeddings/BaseRetriever 包装。

## 16. 案例深度：创业公司 vs 金融合规

### 16.1 案例 A：创业公司 0→12 月

- **0-3 月**：LC [126 LCEL](126.langchain-lcel-tutorial.md) + [76 Chroma](76.chroma-vector-db-tutorial.md) 验证问答；[25 embedding](25.embedding-vector-tutorial.md) 选开源中文模型；  
- **3-6 月**：PDF 版式烂，抽 [136 Parser/Splitter](136.pluggable-parser-splitter-embedder-tutorial.md)，因 [42 PyMuPDF](42.pymupdf-tutorial.md) 与 [44 Unstructured](44.unstructured-io-tutorial.md) 需切换；  
- **6-9 月**：Recall 瓶颈，检索换自研 Hybrid（[93][94]），编排仍 LC；  
- **9-12 月**：[138 配置驱动](138.config-driven-pipeline-tutorial.md) + [144 回归](144.regression-test-set-tutorial.md) 守门，[153 A/B](153.ab-experiment-rag-tutorial.md) 验证改动。

原则：**金标守门**，每次替换跑 [139-142 RAGAS](141.ragas-faithfulness-tutorial.md)。框架可换，指标不可换。

### 16.2 案例 B：金融合规

- ACL [121]、审计日志 **自研**，不信任 prompt 保密；  
- LLM 走统一网关，密钥不出业务容器；  
- 框架仅 **开发环境原型**；生产 ingest/query 与 LC 解耦，on-call 熟 [76] 原生 API 与自研 Retriever；  
- Agent [133](133.llamaindex-agent-tutorial.md) 默认关闭，除非合规签署迭代上限。

面试讲案例 B 要强调：**合规是架构约束**，不是「我们更牛不用框架」。

### 16.3 技术债信号与动作

| 信号 | 动作 |
|------|------|
| 升级 LC 断链 | pin 版本 + 抽 [136] 接口 |
| on-call 不懂 Chroma 原生 | 培训 [76][128] |
| 同一请求双框架 LC+LI | 立规：单路径 |
| 无金标发版 | 停功能上线 |
| embed 换模型未新建 collection | 紧急重建 + 回归 |

## 17. PR 评审、工作坊与路线图衔接

### 17.1 PR Review 五问

1. 本 PR 框架边界在哪？能否两周内剔框架？  
2. 是否新增 metadata 字段并更新 Schema（[50-54](50.metadata-doc-id-tutorial.md)）？  
3. 是否跑 [144 回归](144.regression-test-set-tutorial.md) 与抽样 RAGAS？  
4. 观测 span 是否含 hit_ids、embed_model、prompt_version（[147](147.langsmith-tracing-tutorial.md)）？  
5. ingest 是否幂等（[162](162.idempotent-reindex-tutorial.md)）？

### 17.2 六十分钟工作坊模板

参与：后端、算法、产品、on-call。产出：一页 ARCHITECTURE.md 分层表；框架/自研/混合决策与 **回滚预案**；负责人签名与复查季度；对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 勾选五层完成度。

### 17.3 与 Haystack、LlamaIndex 的三角

主栈选一个深钻（建议 LC 125-130），[134 Haystack](134.haystack-pipeline-tutorial.md) 与 [131 LI](131.llamaindex-index-types-tutorial.md) **了解即可**，用对照表防面试官带偏。自研 DAG 可借鉴 Haystack 显式图，不必引入 Haystack 运行时。

### 17.4 切块与 embed 不可外包给框架

无论选哪框架，[57-65 切块](60.chunk-overlap-tutorial.md) 与 [25 embedding](25.embedding-vector-tutorial.md) 质量仍是 Recall 地基。框架争论若脱离 [150 切块 bad case](150.bad-case-chunking-tutorial.md)、[151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md)，是空对空。

### 17.5 巩固交付物

1. 团队分层表 v1；  
2. 两个案例各三句话复盘；  
3. PR 五问贴到 wiki；  
4. 写下触发条件：何时从纯 LC 抽到 [136] 协议（PDF 解析失败率、Recall 阈值、合规审计）。

### 17.6 成本模型与迁移剧本

框架成本在升级断裂、培训、双栈运维；自研成本在初期慢、需要资深工程师。用表格估算 LC 升级频率、on-call 熟 [76 Chroma](76.chroma-vector-db-tutorial.md) 人数、金标回归耗时。迁移剧本：136 协议 → Retriever 混合 [93] → 138 配置 → 144 回归门禁，每阶段保留回滚路径。

### 17.7 组织政治、招聘与两人团队

用 [143 金标](143.golden-dataset-tutorial.md) 与 on-call 事故复盘做共同事实，避免「框架派」「自研派」领地战。JD 应考 [128 filter](128.langchain-vectorstore-tutorial.md)、[130 chunk_id](130.langchain-text-splitter-tutorial.md)、分层表画工。两人团队：LC 125-130 + 尽早 136，勿过早全自研；ACL 与混合检索强需求时再自研 [127 Retriever](127.langchain-retriever-tutorial.md)。

### 17.8 季度复查与管理层沟通

每季度查：单一路径、manifest 完整、回归绿、ACL 绿、无 embed 混用 collection、路线图五层有负责人。向管理层画 PoC 加速与六月后维护成本曲线；诚实说明 LC 加速验证、[136](136.pluggable-parser-splitter-embedder-tutorial.md) 防止 PoC 腐烂成生产泥球。技术选型文档写明「我们不是什么」：不是 LI 全家桶、不是 Haystack 运行时、不是无脑 LC。

### 17.9 与评测轨 E 模块衔接

每次 [153 A/B](153.ab-experiment-rag-tutorial.md) 或检索参数变更，回写 ARCHITECTURE.md 的当前默认路径。与 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 联测时记录用的是 LC 纯链还是自研 Retriever 链。新人 onboarding：第一周读 135+136 图，第二周跟 ingest 夜间任务，第三周跟 on-call 检索异常。


### 17.10 常见误区逐条拆穿

误区一：「上了 LangChain 就等于企业级。」——错。企业级来自 metadata 契约、ACL、金标回归、幂等 ingest 与引用格式，框架只提供胶水。误区二：「自研就是不用任何框架。」——错。自研指厚接口与可替换核心，LC 仍可用于 LCEL 编排。误区三：「LlamaIndex 更先进所以要换。」——错。先进不等于适合你的合规与 on-call 能力。误区四：「Haystack 有图所以更清晰。」——图可以画在 ARCHITECTURE.md，不必多一套运行时。误区五：「等用户量大了再抽接口。」——往往来不及，PoC 逻辑已焊死在链里，抽离成本指数上升。

### 17.11 与 [125-127 LangChain](125.langchain-core-tutorial.md) 的协同而非对立

125 教你 Runnable 与 Message 结构；126 教你管道组合与拒答分支；127 教你 Retriever 策略与 filter。135 不是让你抛弃这三篇，而是规定 **哪些逻辑不许写进链里**：Parser 业务规则、ACL 强制、manifest 写入、金标门禁应在外层服务或协议实现。面试时画一张图：最外层 FastAPI，中间自研 RAG Service，内层 LC 链仅负责 prompt-llm 与可选 retriever 调用，底层 [76 Chroma](76.chroma-vector-db-tutorial.md) 或 [75 FAISS](75.faiss-ann-tutorial.md) 由 Store 接口屏蔽。这样答既体现框架价值，又体现企业纪律。

### 17.12 工作坊演练题（60 分钟可完成）

题一：给三人团队（无合规要求、一千份 PDF、预算紧）写分层表与选型结论。题二：给金融团队（强 ACL、审计、混合检索）写同一模板并对比差异。题三：写一份「LC 升级断裂」回滚预案：pin 版本、哪些测试必须先绿、谁签字发布。题四：列举五条技术债信号并对应动作。题五：说明何时引入 [136 三协议](136.pluggable-parser-splitter-embedder-tutorial.md) 的三条量化触发条件。完成这五题，135 篇从「读过」变为「能落地」。

### 17.13 与路线图 H 工程化层的长期对齐

[ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 不只覆盖 C 轨链路与 D 轨框架，还要求评测观测、部署运维、成本与安全。架构取舍必须连接到 E 轨 [143 金标](143.golden-dataset-tutorial.md)、[144 回归](144.regression-test-set-tutorial.md)、[147 追踪](147.langsmith-tracing-tutorial.md)。没有评测门禁的框架选型讨论，容易沦为个人偏好辩论。建议把 ARCHITECTURE.md 与回归阈值、manifest 字段放在同一 Git 仓库，发版时三者一起审。


### 17.14 发版门禁与 on-call 的架构契约

建议把以下条款写进团队发版规范：任何改动检索或切块参数的 PR，必须附 [143 金标](143.golden-dataset-tutorial.md) 对比截图或 CSV；任何引入新框架依赖的 PR，必须附 ARCHITECTURE.md 更新与回滚步骤；任何修改 embed 模型的 PR，必须附新 collection 名称与重建 job 链接。on-call 值班手册第一节写清：当前生产路径是 LC 纯链还是混合链；manifest 字段去哪查；[76 Chroma](76.chroma-vector-db-tutorial.md) 持久化目录与备份负责人是谁。架构不是架构师私藏，而是 on-call 能执行的文档。

### 17.15 与 [128-130](128.langchain-vectorstore-tutorial.md) 的落地顺序

初学者常问先深哪篇。建议：128 VectorStore 跑通 Chroma 与 FAISS 双后端与 filter；129 Loader 把 metadata Schema 钉死；130 Splitter 把 chunk_id 与 overlap 调参流程钉死；然后回到 135 画分层表，决定 Parser 何时从 LC Loader 抽到 [136 协议](136.pluggable-parser-splitter-embedder-tutorial.md)。顺序反了——先争论框架——容易空对空。数据入口质量决定 Recall 上限，框架只决定你多快撞到上限。


### 17.16 写给技术负责人的一页纸摘要

若你只能向上汇报一页纸：第一段写当前选型（例如 LC 编排加自研 Retriever 加 Chroma 存储）；第二段写三条量化指标（金标 Recall、P95 延迟、月 embed 成本）；第三段写两个最大风险（框架升级断裂、embed 混库）与缓解；第四段写下一季度里程碑（136 协议全覆盖、144 回归强制、混合检索上线）。附链接到 ARCHITECTURE.md 与 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 勾选进度。避免使用「我们在用先进框架」这类无法验收的表述。


### 17.17 复盘模板

每次架构相关事故或发版回滚后，用五问复盘：默认路径变了吗？金标跌了多少？manifest 是否不一致？on-call 文档是否过期？两周内能否剔框架到上次稳定态？答案写入 wiki，与 [149-152 bad case](149.bad-case-parsing-tutorial.md) 系列同库检索。季度例会回顾 ARCHITECTURE.md 与路线图勾选进度，避免文档腐烂无人维护，并指定文档 owner。
""",
    "pluggable-parser-splitter-embedder": """
## 15. Protocol、数据类与窄接口设计

### 15.1 为何需要三件套协议

[136 可插拔 Parser/Splitter/Embedder](136.pluggable-parser-splitter-embedder-tutorial.md) 是 D 轨 **数据入口** 的地基：把 [129 Loader](129.langchain-document-loader-tutorial.md)、[130 Splitter](130.langchain-text-splitter-tutorial.md)、[25 Embedding](25.embedding-vector-tutorial.md) 从框架类里 **拔出来**，变成可单测、可配置、可版本化的窄接口。下游 [137 Store/Retriever/Generator](137.pluggable-store-retriever-generator-tutorial.md) 对称设计，中间 [138 配置驱动](138.config-driven-pipeline-tutorial.md) 拧紧，才能做 [139-145 评测](139.ragas-context-precision-tutorial.md) 与 [144 回归](144.regression-test-set-tutorial.md)。

[135 框架取舍](135.pipeline-vs-framework-tutorial.md) 讲何时用 LC；本篇讲 **自研芯长什么样**。初学者勿跳过 [75 FAISS](75.faiss-ann-tutorial.md)、[76 Chroma](76.chroma-vector-db-tutorial.md) 直接抄接口——不懂存储层，接口背后排障会盲。

### 15.2 推荐 Protocol 草图（Python 3.10+）

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass
class RawDocument:
    doc_id: str
    text: str
    metadata: dict

@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict

class Parser(Protocol):
    def parse(self, path: str) -> RawDocument: ...

class Splitter(Protocol):
    def split(self, doc: RawDocument) -> list[Chunk]: ...

class Embedder(Protocol):
    dimension: int
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
```

Chunk.metadata 必须继承 doc_id、source、acl_group（[50-53](50.metadata-doc-id-tutorial.md)），并含稳定 chunk_id（[51](51.metadata-chunk-id-tutorial.md)）。Embedder.dimension 与 [76 Chroma](76.chroma-vector-db-tutorial.md) collection 维度一致，换模型即新 collection。

### 15.3 与 C 轨切块、embed 的对应

| 协议 | C 轨教程 |
|------|----------|
| Splitter | [57-65](58.recursive-character-chunking-tutorial.md) |
| Embedder | [25][66][67][69] |
| Parser | [36-44][42 PyMuPDF](42.pymupdf-tutorial.md) |

协议实现内部可调 LangChain 类，但 **单元测试只依赖 Protocol**，不 import langchain 包。

## 16. Adapter 薄包装与 Registry 注册表

### 16.1 LangChain 适配器清单

| 协议 | LC 适配 |
|------|---------|
| Parser | 自定义 BaseLoader 或 ParserLoader |
| Splitter | TextSplitter 子类包装 split |
| Embedder | Embeddings 子类包装 embed_texts |

适配器 **薄**：逻辑在 PyMuPDFParser 等实现类，适配器只转 Document 与 Chunk。这样 [126 LCEL](126.langchain-lcel-tutorial.md) 与自研 ingest 脚本 **共用同一 Parser**。

### 16.2 REGISTRY 与 build_pipeline

```python
REGISTRY = {
    "parser": {"pymupdf": PyMuPDFParser, "plain": PlainTextParser},
    "splitter": {"recursive_600_80": Recursive600Splitter, "md_header": MdHeaderSplitter},
    "embedder": {"bge_small": BgeSmallEmbedder, "fake": FakeEmbedder},
}

def build_pipeline(cfg: dict):
    parser = REGISTRY["parser"][cfg["parser"]]
    splitter = REGISTRY["splitter"][cfg["splitter"]]
    embedder = REGISTRY["embedder"][cfg["embedder"]]
    assert embedder.dimension == cfg["vector_dim"]
    return parser, splitter, embedder
```

配置来自 [138 YAML](138.config-driven-pipeline-tutorial.md)；vector_dim 写入 manifest。禁止在 build_pipeline 里硬编码 Chroma——Store 是 [137](137.pluggable-store-retriever-generator-tutorial.md) 的职责。

### 16.3 契约测试（Contract Test）

每个 Parser：对 tests/fixtures/sample.pdf 断言 doc_id 存在、文本非空。每个 Splitter：固定输入断言 chunk 数范围、chunk_id 唯一、含 acl_group。每个 Embedder：len(vec)==dimension；fake 模型同一文本两次 embed 完全一致。失败即 CI 红，别等到 [150 切块](150.bad-case-chunking-tutorial.md) 才人工发现。

### 16.4 错误处理与死信

Parser 单文件失败：**跳过 + 死信队列**（[163 重试死信](163.retry-dead-letter-tutorial.md)），不要拖垮整批 NAS 扫描。Splitter 产出空列表：warn + [149 解析归因](149.bad-case-parsing-tutorial.md)。Embedder 批失败：按 [69 重试限速](69.embedding-retry-rate-limit-tutorial.md) 指数退避，批大小减半重试。

## 17. manifest 治理、全链衔接与作业

### 17.1 版本 manifest

索引任务结束写 manifest.json，字段含 parser、splitter、embedder、vector_dim、chunk_count、collection、created_at。与 [48 文档版本](48.doc-versioning-tutorial.md)、[154 参数版本](154.param-version-management-tutorial.md)、[162 幂等重索引](162.idempotent-reindex-tutorial.md) 衔接。查询侧日志带 manifest_id，排障知道答案用的是哪套切块与 embed。

### 17.2 全链：Parser → Splitter → Embedder → Store

RawDocument 变 Chunk 列表；embed_texts 批处理（[67 批处理](67.embedding-batching-tutorial.md)）；写入 [128 LC VectorStore](128.langchain-vectorstore-tutorial.md) 或 [137 Store](137.pluggable-store-retriever-generator-tutorial.md)；[127 Retriever](127.langchain-retriever-tutorial.md) 读，[110 Generator](110.rag-prompt-template-tutorial.md) 生成。全链路可替换：换 Parser 不改 Splitter 单测；换 Embedder 新建 collection 全量重建。

### 17.3 切块策略注册与依赖注入

REGISTRY 为不同 metadata.lang 或 mime 注册 recursive_zh、md_header_en、code_aware 等 Splitter。build_pipeline 测试 overrides 用 FakeEmbedder。Registry 并存 pymupdf 与 pdfplumber，[153 A/B](153.ab-experiment-rag-tutorial.md) 选主 Parser。

### 17.4 归一化、跨语言与 ADR

Embedder 对接 [66 L2 归一化](66.l2-normalization-tutorial.md)，联调 [75 FAISS IP](75.faiss-ann-tutorial.md)。lang metadata 路由 Splitter；[70 混合语言 embed](70.mixed-language-embedding-tutorial.md)。每实现写 ADR：为何选、弃用条件、manifest 字段、回滚步骤。独立团队可 HTTP parse 返回 RawDocument，Adapter 进 Registry。

### 17.5 性能 profiling 与指标面板

千页 PDF ingest 分别 profile Parser、Splitter、Embedder 耗时。通常 Embedder 是大头，Parser 单线程则先并行 Parser。Parser 输出字符数、Splitter 输出 chunk 数写入面板；chunk 数骤降常是 Parser 升级引入静默空文本。与 [161 索引状态机](161.index-task-state-machine-tutorial.md) 结合，状态转换记录三件套版本号。

### 17.6 巩固作业与路线图完成标准

实现 REGISTRY + build_pipeline + 契约测试；加 PlainTextParser 与 MarkdownParser；跑通 manifest + [76 Chroma](76.chroma-vector-db-tutorial.md) 联调；画全链白板。完成标准：≥2 实现、契约测试绿、manifest 落盘、与 128 联调、wiki 有 ADR。与 [137 下游三插头](137.pluggable-store-retriever-generator-tutorial.md) 成对。面试话术：三 Protocol + Registry；LC 薄适配；manifest 绑定版本；换 embed 必新建 collection。对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) D 轨 154-155 条验收。


### 17.7 OpenAPI 边界与团队分工

当 Parser 由独立数据团队维护时，可暴露 HTTP parse 接口返回 RawDocument JSON，ingest 服务通过 Adapter 调用而非 import 库——**协议即团队边界**。契约测试在提供方跑：保证 sample.pdf 输出稳定；消费方跑：保证 Splitter 能消费 RawDocument。Embedder 若走独立 GPU 服务，embed_texts 可变成 batch RPC，但 dimension 与 model_version 必须在 manifest 中可见，避免 [128 VectorStore](128.langchain-vectorstore-tutorial.md) 写入错误维度向量。

### 17.8 与 [57-65 切块](57.fixed-size-chunking-tutorial.md) 系列的实践映射

57 固定长度适合实现简单的 PlainTextSplitter 协议类；58 递归字符是 Recursive600Splitter 的默认实现；59 句子边界可作为 separators 配置预设；60 overlap 是 Splitter 构造参数，变更要 bump manifest；61 权衡用金标网格驱动 REGISTRY 默认项；62-64 结构感知对应 md_header、html_dom 等命名实现；65 Parent 模式在 Splitter 产出 child 时写 parent_id，供下游 docstore。初学者应能指着 REGISTRY 说明每个 key 对应 C 轨哪一篇，而不是只会抄 Protocol 定义。

### 17.9 与 [25 Embedding](25.embedding-vector-tutorial.md) 及向量库的硬约束

换 embed 模型等于换向量空间：协议层 Embedder 实现可以多个，但 **同一 collection 只能绑定一个活跃 embedder 版本**。FakeEmbedder 用于 CI 与本地 demo，dimension 设为 8 或 128 即可；生产 BGE 或 OpenAI embed 维度写入配置。归一化策略与 [66](66.l2-normalization-tutorial.md)、[75 FAISS 内积](75.faiss-ann-tutorial.md) 一致。批大小与 [67](67.embedding-batching-tutorial.md)、限速与 [69](69.embedding-retry-rate-limit-tutorial.md) 在 Embedder 实现内部封装，不让 VectorStore 或 LangChain 类散落重试逻辑。

### 17.10 契约测试样例与 CI 集成

在 tests/contract/test_parser.py 中：加载 fixtures/sample.pdf，调用 REGISTRY 中每个 Parser，断言 doc_id 非空、text 长度大于一百、metadata 含 source。tests/contract/test_splitter.py：固定 RawDocument 输入，断言 chunk 数在预期范围、chunk_id 唯一、acl_group 继承。tests/contract/test_embedder.py：两句相同中文，向量维度等于 cfg.vector_dim；fake 嵌入两次结果完全一致。CI 在 PR 阶段跑契约，夜间跑端到端 ingest 加 [144 回归](144.regression-test-set-tutorial.md) 子集。失败时禁止合并，比上线后 [150 切块](150.bad-case-chunking-tutorial.md) 救火便宜得多。

### 17.11 全栈演示脚本与面试深度表达

用一百行以内脚本演示：遍历 fixtures 目录，build_pipeline 从 prod.yaml 组装三件套，parse→split→embed_texts→写入内存 [76 Chroma](76.chroma-vector-db-tutorial.md)，打印 manifest 与一条 similarity_search 的 chunk_id。面试时这样说：「我们把数据入口收成 Parser、Splitter、Embedder 三个窄协议，Registry 与 [138 配置](138.config-driven-pipeline-tutorial.md) 驱动；LangChain 的 Loader、TextSplitter、Embeddings 只是薄适配；manifest 把版本钉死；下游 [137](137.pluggable-store-retriever-generator-tutorial.md) 的 Store 与 Retriever 可换而不动 Parser 契约。」再配合白板画数据流，区分度高于「我会调 from_documents」。

### 17.12 对照 ENTERPRISE_RAG_ROADMAP 的完成自检

打开路线图 D 轨与数据层清单：是否能在团队 wiki 找到 REGISTRY 截图与 manifest 样例？是否至少两种 Parser 实现？是否 Splitter 改参数会 bump 版本并触发重建？是否 Embedder 换模型会新建 collection？是否与 [125-127](125.langchain-core-tutorial.md) 适配器代码控制在百行以内？是否契约测试进 CI？全部为是，才算 136 篇达标；否则只是「知道 Protocol 这个单词」。


### 17.13 从 Demo 到生产的 Registry 演进

第一周：REGISTRY 只有 pymupdf、recursive_600_80、fake 三项，跑通 manifest。第一个月：加 plain、md_header、bge_small，契约测试进 CI。第三个月：加 pdfplumber 做 A/B，加 code_aware 应对技术文档，Embedder 接真实 GPU 服务。第六个月：HTTP Parser 适配外部团队，manifest 字段与 [154 参数版本](154.param-version-management-tutorial.md) 合并展示。每次只加一个实现、一条契约、一次回归，避免「大爆炸式重构」同时换 Parser 与 Embedder 导致无法归因。

### 17.14 与 LangChain [125-127](125.langchain-core-tutorial.md) 适配器代码纪律

适配器文件建议每个不超过八十行：ParserLoader 只调用 protocol.parse 并转 Document；RecursiveSplitterAdapter 只调用 protocol.split 并转 Document 列表；BgeEmbedderAdapter 只实现 embed_documents 委托 embed_texts。禁止在适配器里写 PDF 表格逻辑或重试循环——那些属于协议实现或 Embedder 内部。代码评审时问：若明天剥离 LangChain，适配器删后业务逻辑是否仍在 protocol 包？否的话打回。

### 17.15 全链路故障注入练习（建议季度一次）

故意制造：Parser 返回空文本、Splitter 返回零 chunk、Embedder 超时、manifest 缺 vector_dim、用旧 embedder 查新 collection。观察 ingest job 是否按 [163 死信](163.retry-dead-letter-tutorial.md) 隔离失败文件；query 是否返回可理解错误而非胡编答案。练习记录写进 wiki，新人按剧本操作一次。比背诵 Protocol 定义更能建立对企业数据入口的信心。


### 17.16 与 ingest 队列、[159 Celery](159.celery-async-queue-tutorial.md) 的组合方式

扫描 NAS 后不要把「解析加切块加向量化」塞在一个长任务里。推荐：任务 A 只 parse 写 RawDocument 到对象存储；任务 B 读 RawDocument split 写 Chunk 列表；任务 C batch embed 写 [76 Chroma](76.chroma-vector-db-tutorial.md)。每个任务读 manifest 片段，失败可独立重试，符合 [162 幂等](162.idempotent-reindex-tutorial.md)。Registry 在三类 worker 启动时由同一 prod.yaml 构建，保证版本一致。队列深度与死信数量进面板，比端到端黑盒任务更易定位是 Parser 崩还是 Embedder 限速。

### 17.17 新人第一周阅读与实操清单

周一读 136 本篇与 [135 取舍](135.pipeline-vs-framework-tutorial.md)；周二读 [57-58 切块](57.fixed-size-chunking-tutorial.md) 与 [25 embed](25.embedding-vector-tutorial.md)；周三实现 FakeEmbedder 与一条契约测试；周四用 PyMuPDFParser 跑 fixtures；周五联调 [128 VectorStore](128.langchain-vectorstore-tutorial.md) 写入十条 chunk 并查询。周末写半页笔记：三个协议职责、Registry 作用、manifest 字段含义。完成即达到团队要求的 136 入门线。


### 17.18 与 [137 Store](137.pluggable-store-retriever-generator-tutorial.md) 的 handoff 契约

三件套产出的是 Chunk 加向量，不是最终答案。handoff 约定：Chunk.text 已清洗；Chunk.metadata 含 chunk_id 与 acl_group；向量维度等于 manifest.vector_dim；批量写入时 ids 等于 chunk_id。Store 实现不应再修改文本，只负责 upsert 与 delete。Retriever 读 Store 时强制 filter，不回头改 Parser。Generator 只消费 Retriever 返回的 evidence 列表。这条边界画清，[135 框架争论](135.pipeline-vs-framework-tutorial.md) 会少一半。

### 17.19 术语表（面试速记）

Parser：路径到 RawDocument；Splitter：RawDocument 到 Chunk 列表；Embedder：文本列表到向量列表；Registry：名字到实现；manifest：一次索引的版本快照；Adapter：协议到 LangChain 的薄壳；契约测试：不启动完整 RAG 也能验证接口。能用自己的话解释这七个词，比背诵代码更能通过企业面试。

### 17.20 与 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 数据层检查项

逐项自检：是否 Parser 可切换且具契约测试？是否 Splitter 改参必重建索引？是否 Embedder 换模型必新建 collection？是否 manifest 可查？是否 [125-127 LangChain](125.langchain-core-tutorial.md) 适配器保持薄？是否已与 [76 Chroma](76.chroma-vector-db-tutorial.md) 或 [75 FAISS](75.faiss-ann-tutorial.md) 联调写入？全部满足方可宣称掌握企业级可插拔数据入口，而非仅会调用 from_documents。建议把本清单贴到 ingest 服务 README 首页，与 [138 配置驱动](138.config-driven-pipeline-tutorial.md) 的 prod.yaml 变更流程绑定，形成可审计的发布习惯。新人入职第三天应能根据 README 独立跑通一次 fixtures ingest 并读出 manifest 文件内容。团队负责人每月抽查一条契约测试与一份 manifest，确认字段未漂移，与 [154 参数版本](154.param-version-management-tutorial.md) 台账一致。若台账与生产 manifest 不一致，按 [162 幂等重索引](162.idempotent-reindex-tutorial.md) 流程暂停写入并通知 on-call。此纪律与 [135 架构取舍](135.pipeline-vs-framework-tutorial.md) 中「可回滚、可观测」原则一致，是数据入口团队对全公司的承诺，也应写入季度工程复盘纪要并由负责人签字确认存档备查即可。
""",
}
