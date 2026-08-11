# -*- coding: utf-8 -*-
"""Final padding for tutorials 128-136 — topic-specific appendices to reach >=5000 hanzi."""

PAD_EXTRA = {
    "langchain-vectorstore": r"""

## 18. 附录：VectorStore 排障决策树与团队 Wiki 模板

### 18.1 排障决策树（打印贴显示器旁）

当 `similarity_search` 结果「看起来不对」时，按顺序执行，**禁止跳步直接调 temperature**：

1. **确认 Embedding 实例**：ingest 脚本与 query 脚本是否 `import` 同一 `Embeddings` 单例？模型名、维度、`normalize_embeddings` 是否一致？对照 [25 Embedding](25.embedding-vector-tutorial.md) 与 [66 L2 归一化](66.l2-normalization-tutorial.md)。  
2. **确认 collection / 索引版本**：`collection_name` 是否含 embed 模型版本？是否误连到同事昨天实验用的空库？Chroma 用 `collection.count()`；FAISS 用 `index.ntotal`。  
3. **确认 ids 与 chunk_id**：评测对齐 [51 chunk_id](51.metadata-chunk-id-tutorial.md) 时，ids 是否等于业务主键而非 UUID？  
4. **确认 filter**：`acl_group`、`tenant_id` 类型是否与 metadata 入库一致？静默滤空是最常见「召回为 0」原因。  
5. **下沉原生 API**：用 chromadb Client 直接 `query`，绕过 LangChain，判断问题在 **封装层还是数据层**。  
6. **看分数分布**：`similarity_search_with_score` 打印 top5，对照 [99 阈值](99.score-threshold-tutorial.md) 与金标 [143](143.golden-dataset-tutorial.md)。  
7. **归因模块**：仍不对则进入 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 检查清单，而非怪模型胡编。

### 18.2 团队 Wiki：VectorStore 规范（可直接粘贴）

| 条目 | 规定 |
|------|------|
| collection 命名 | `{kb}_{embed}_{schema_v}` |
| 换模型 | 新 collection + 全量重建 + 回归 [144](144.regression-test-set-tutorial.md) |
| ids | 必须等于 chunk_id |
| 持久化 | prod 禁止相对路径 `./chroma_db` 无备份 |
| ACL | filter 在 VectorStore/Retriever，禁止仅靠 Prompt |
| 日志 | 每次 query 记录 collection、embed_model、top_k、hit_ids |
| 观测 | ingest/query span 进 [147 LangSmith](147.langsmith-tracing-tutorial.md) 或 [148 Langfuse](148.langfuse-observability-tutorial.md) |

### 18.3 与 [125][126][127] 的复习闭环

- [125 核心](125.langchain-core-tutorial.md)：`Document` 是 VectorStore 的货币；  
- [126 LCEL](126.langchain-lcel-tutorial.md)：`retriever | format_docs` 消费 VectorStore 输出；  
- [127 Retriever](127.langchain-retriever-tutorial.md)：`as_retriever` 是工厂，混合检索在 Retriever 层组合。  

**30 秒面试版**：「我们用 LangChain VectorStore 统一 Chroma/FAISS 入库与相似度搜索，ids 对齐 chunk_id，ACL 在 filter，换 embed 必新 collection，排障先查 embedding 单例与 count。」

### 18.4 阶段 3 验收对照

对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 阶段 3：**能换 VectorStore 实现而不改 LCEL 链**——本篇就是该能力的 LangChain 路径。验收时演示 Chroma→FAISS 切换仅改构造类，回归集分数波动在容忍范围内。

### 18.5 延伸阅读（仍属 D 轨）

- [129 Loader](129.langchain-document-loader-tutorial.md)：谁产出 Document；  
- [130 Splitter](130.langchain-text-splitter-tutorial.md)：谁切 chunk；  
- [135 架构取舍](135.pipeline-vs-framework-tutorial.md)：何时坚持原生 [76 Chroma](76.chroma-vector-db-tutorial.md)；  
- [137 下游三件套](137.pluggable-store-retriever-generator-tutorial.md)：Store 接口与 LC 适配器并存。
""",

    "langchain-document-loader": r"""

## 18. 附录：Loader 数据治理检查单与 JSONL 中间态

### 18.1 数据治理二十项（Loader 阶段）

| # | 检查项 | 失败后果 |
|---|--------|----------|
| 1 | 每 Document 有 doc_id [50] | 无法增量与溯源 |
| 2 | source 可解析为路径/URL [52] | 导航 [115] 失效 |
| 3 | PDF 有 page 元数据 | 页码引用错误 |
| 4 | encoding 显式或 autodetect [41] | 中文乱码 |
| 5 | mime 字段 | 审计无法分类 |
| 6 | content_hash [49] | 重复 embed 烧钱 |
| 7 | acl_group [53] | 越权检索 |
| 8 | version [48] | 新旧制度混杂 |
| 9 | loader 类名入 metadata | 排障不可复现 |
| 10 | 禁止路径遍历 | 安全漏洞 |
| 11 | 扫描件走 OCR [55] 后再 Loader | 空文本入库 |
| 12 | 大目录用 lazy_load | OOM |
| 13 | DirectoryLoader 排除 .git | 垃圾 chunk |
| 14 | 去重 [47] 在 Splitter 前 | 重复 Top-K |
| 15 | JSONL 中间态可抽检 | 数据组无法审计 |
| 16 | Web 源遵守 robots | 合规风险 |
| 17 | 与 [136 Parser](136.pluggable-parser-splitter-embedder-tutorial.md) 边界清晰 | 逻辑散落 |
| 18 | 对接 [122 内容安全](122.content-safety-filter-tutorial.md) | 恶意文本进库 |
| 19 | 失败文件进死信表 [163] | 静默丢文档 |
| 20 | manifest 与 [161 索引状态机](161.index-task-state-machine-tutorial.md) 联动 | 任务不可追踪 |

### 18.2 JSONL 中间态示例

```json
{"page_content": "年假制度…", "metadata": {"doc_id": "hr-001", "source": "data/hr.md", "mime": "text/markdown", "acl_group": "all", "content_hash": "a1b2…"}}
```

数据组每周抽 50 行，核对 metadata 完整率。完整率低于 99% 时 **阻断进入 Splitter**，比索引后删库便宜。

### 18.3 与 [125][128][130] 的衔接复述

[125](125.langchain-core-tutorial.md) 定义 Document；本篇 Loader 产出它；[130 Splitter](130.langchain-text-splitter-tutorial.md) 消费它；[128 VectorStore](128.langchain-vectorstore-tutorial.md) 向量化入库。任何一环 metadata 断裂，[113 引用](113.inline-citation-tutorial.md) 与 [115 导航](115.source-document-navigation-tutorial.md) 都会断。

### 18.4 面试与作业

**面试 30 秒**：「Loader 只负责文件到 Document，复杂 PDF 在 Parser；metadata 在 Loader 第一次落盘就要齐；增量靠 content_hash；编码错误是国内库头号坑。」

**作业**：实现 `load_incremental()` 包装 DirectoryLoader，输出本轮跳过文件数、新增文件数、失败文件列表；与 [49 增量](49.incremental-update-tutorial.md) 文档对照写 wiki 一页。
""",

    "langchain-text-splitter": r"""

## 18. 附录：切块参数网格搜索与回归集联动

### 18.1 网格搜索模板（对接 [143 金标](143.golden-dataset-tutorial.md)）

```text
for chunk_size in [400, 600, 800, 1000]:
  for overlap in [0, 50, 80, 120]:
    rebuild_index(splitter_config)
    run_regression(golden_20)
    log Recall@3, avg_chunks, embed_cost
```

结果写入 [154 参数版本](154.param-version-management-tutorial.md) 表。**禁止** 无金标只凭直觉定 overlap——overlap 过大时 [106 去重](106.retrieval-dedup-tutorial.md) 与 [105 MMR](105.mmr-diversity-tutorial.md) 压力上升，成本可能翻倍。

### 18.2 中文/英文/混合库分隔符表

| 语言 | 推荐 separators 片段 |
|------|---------------------|
| 中文制度 | `\n\n`, `\n`, `。`, `！`, `？`, `；`, ` ` |
| 英文技术 | `\n\n`, `\n`, `. `, `; `, ` ` |
| 中英混合 | 按 metadata.lang 选 Splitter 实例 [136 注册表](136.pluggable-parser-splitter-embedder-tutorial.md) |

### 18.3 chunk_id 生成规范

每个 chunk 的 `chunk_id` 建议 `{doc_id}:c{seq:04d}` 或内容 hash 短码。Splitter 追加 `start_index` 时 **不要覆盖** Loader 的 doc_id。唯一性校验：`len(ids)==len(set(ids))`，否则 [128 upsert](128.langchain-vectorstore-tutorial.md) 行为未定义。

### 18.4 与 [125][129][128] 闭环

Loader [129] → Splitter 本篇 → Embed [25] → VectorStore [128]。Splitter 改参数 = **索引语义版本变更**，必须走 [48 文档版本](48.doc-versioning-tutorial.md) 流程。

### 18.5 Bad Case 入口

切块错误占 bad case 显著比例——[150 切块归因](150.bad-case-chunking-tutorial.md)。团队应维护「断裂句界样例库」，每次改 separators 必跑回归。

### 18.6 巩固作业扩展

1. 同一 PDF：按页 Loader [129] 与按全文再切，对比 Recall；  
2. Markdown 二级标题 + 递归细切流水线画图；  
3. TokenTextSplitter 与 RecursiveCharacter 对同一文件 chunk 数对比；  
4. 写 wiki：**本公司 splitter 默认参数及上次金标验证日期**。
""",

    "llamaindex-index-types": r"""

## 18. 附录：LlamaIndex Index 了解即可 — 面试速记与对照表

### 18.1 为何路线图标「了解」

团队主栈是 LangChain [125-130](125.langchain-core-tutorial.md) 时，LlamaIndex Index 类型 **不必背全 API**。价值在于：**面试能对照**、**读论文/竞品方案时不懵**、**设计自研索引层时有备选名词**。

### 18.2 Index 类型一句话表

| Index | 一句话 | 生产出现率 |
|-------|--------|------------|
| VectorStoreIndex | 向量检索主路径 | 高 |
| SummaryIndex | 全文摘要问答 | 低（小库 demo） |
| TreeIndex | 层次化检索 | 低（研究） |
| KeywordTableIndex | 关键词表 | 低（可对照 BM25） |
| ComposableGraph | 多子索引路由 | 中（复杂产品） |

### 18.3 与 LangChain 映射（必背）

| LlamaIndex | LangChain |
|------------|-----------|
| Document → Node | Document |
| VectorStoreIndex | VectorStore + ingest |
| StorageContext | Chroma persist + docstore |
| Query Engine [132] | LCEL chain |
| Agent [133] | Agent + tools [124] |

### 18.4 动手边界

安装 `llama-index`，跑通 `VectorStoreIndex.from_documents` + `as_query_engine().query()` **一次即可**，总时长建议 **≤2 小时**。其余时间留给 [128 VectorStore](128.langchain-vectorstore-tutorial.md) 与 [135 取舍](135.pipeline-vs-framework-tutorial.md)。

### 18.5 面试追问五则

**问 1**：Node 与 Document 区别？  
**答**：Node 可带关系与索引结构；Document 更轻。了解即可。

**问 2**：为何企业多 VectorStoreIndex？  
**答**：与 dense retrieval [91](91.dense-retrieval-tutorial.md) 一致，工程成熟。

**问 3**：你会在生产选 TreeIndex 吗？  
**答**：默认不会；除非明确层次化手册场景且金标证明优于向量。

**问 4**：LI 与 LC 能混用吗？  
**答**：可以但不推荐 PoC 混用；统一主栈降低运维成本。

**问 5**：读完本篇下一步？  
**答**：[132 Query Engine](132.llamaindex-query-engine-tutorial.md) 对照 LCEL，然后回 [127 Retriever](127.langchain-retriever-tutorial.md)。

### 18.6 阅读清单

官方文档 Understanding + Indexing 两章；对照本篇 §10 映射表做 **一页笔记**；不超过 2 小时。笔记模板：概念 | LI 名词 | LC 对应 | 是否主线。
""",

    "llamaindex-query-engine": r"""

## 18. 附录：Query Engine 与 LCEL 对照实验

### 18.1 对照实验设计（了解即可）

同一批 Document、同一 embed、同一 LLM，分别实现：

- **路径 A**：`VectorStoreIndex.as_query_engine().query("…")`  
- **路径 B**：[127 Retriever](127.langchain-retriever-tutorial.md) + [126 LCEL](126.langchain-lcel-tutorial.md) + Prompt [110](110.rag-prompt-template-tutorial.md)

对比：延迟、token 消耗、`source_nodes` 与手写 citations [113](113.inline-citation-tutorial.md) 的可控性。多数团队会发现 **路径 B 更透明**——适合审计与 [147 追踪](147.langsmith-tracing-tutorial.md)。

### 18.2 response_mode 速查

| 模式 | 适用 | 风险 |
|------|------|------|
| compact | 上下文适中 | 超长贵 |
| tree_summarize | 极长文档 | 延迟高 |
| refine | 迭代精炼 | 多次 LLM 调用 |
| simple_summarize | demo | 丢细节 |

生产 RAG 更常用手写 LCEL 控制 [107 预算](107.context-budget-tutorial.md)，而非黑盒 response_mode。

### 18.3 source_nodes 与 Grounding

`response.source_nodes` 含 `node_id、score、metadata`——对应 [34 Grounding](34.grounding-citation-tutorial.md)。了解即可：结构类似你在 LCEL 里维护的 `hit_docs` 列表。前端 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) 需要 **稳定 id**，无论数据来自 LI 还是 LC。

### 18.4 何时仍看 Query Engine

- 竞品方案用 LlamaIndex，你要 **读他们的代码**；  
- 研究型 PoC 快速 `query()`；  
- 与 [133 Agent](133.llamaindex-agent-tutorial.md) 工具链联读。

### 18.5 与 [125-127] 的回归

主栈 LangChain 时，Query Engine 是 **参照系**，不是第二套生产管道。wiki 应写清：**「本公司 RAG 编排标准 = LCEL」**，避免新人 copy LI 示例上线。

### 18.6 作业

1. 跑通一次 `query_engine.query`，打印 `source_nodes` 前 3 条 metadata；  
2. 用同题跑 LCEL 链，对比答案与引用条数；  
3. 写 200 字：**为何团队选 LCEL 不选 Query Engine**（模板：透明度、观测、ACL 注入点）。
""",

    "llamaindex-agent": r"""

## 18. 附录：Agent 风险边界与固定管道对比

### 18.1 生产 RAG 默认：固定管道

```text
query → [可选改写 100] → retrieve → [rerank 95] → prompt → generate
```

**Agent**（ReAct / tool loop）适合：多跳探索、工具不确定、开放研究。**企业制度问答** 多数不需要 Agent——延迟、成本、不可预测性更高。路线图 [133](133.llamaindex-agent-tutorial.md) 标「了解」即此意。

### 18.2 与 [124 Function Calling](124.function-calling-tool-use-tutorial.md) 同源

规划 → 选工具 → 执行 → 观察 → 再规划。LlamaIndex `QueryEngineTool` 把 [132 Query Engine](132.llamaindex-query-engine-tutorial.md) 包装成工具，实现 **多知识库路由**。了解即可：思想与 OpenAI tools 一致。

### 18.3 风险清单

| 风险 | 缓解 |
|------|------|
| 无限 tool loop | max_iterations |
| 越权工具 | 工具层校验 Principal [164] |
| 成本爆炸 | 每用户每日配额 [169] |
| 幻觉工具参数 | schema 校验 [123] |
| 不可观测 | trace 每步 tool I/O [147] |

### 18.4 固定管道 vs Agent 决策表

| 场景 | 建议 |
|------|------|
| 员工手册 QA | 固定管道 |
| 跨库比价分析 | Agent + 多 QueryEngineTool |
| 客服工单填槽 | Function Calling [124] |
| 合规问答 | 固定管道 + 拒答 [112] |

### 18.5 与 [125-127][135] 关系

LangChain 侧 Agent 在 [124](124.function-calling-tool-use-tutorial.md)；架构取舍见 [135](135.pipeline-vs-framework-tutorial.md)——**Agent 层是否自研 tool registry** 是常见讨论点。

### 18.6 作业

1. 读 LlamaIndex Agent 示例，标出 tool loop 每一步；  
2. 列一张表：本公司 5 个用户场景，各选固定管道或 Agent 并写理由；  
3. 面试 30 秒：「生产默认固定 RAG 管道，Agent 用于多跳；要限 iterations 与 ACL。」
""",

    "haystack-pipeline": r"""

## 18. 附录：Haystack Pipeline 思想迁移到自研 DSL

### 18.1 Component + Connection 核心

Haystack 2.x 把 RAG 拆成 **有类型的组件**（Embedder、Retriever、PromptBuilder、Generator）与 **显式连线**。价值不在必须用 Haystack，而在 **图可序列化、可审计**——对金融合规团队友好。了解即可；主栈 LangChain [126 LCEL](126.langchain-lcel-tutorial.md) 时，把此思想用于 **自研管道设计**（[135](135.pipeline-vs-framework-tutorial.md)、[138 配置驱动](138.config-driven-pipeline-tutorial.md)）。

### 18.2 典型 ingest / query 双支图

```text
ingest: File → Converter → Preprocessor → Embedder → DocumentStore
query:  Query → Embedder → Retriever → Prompt → Generator
```

与 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 数据层 + 检索层 + 生成层 **同构**。画这张图即可通过 Haystack 篇验收。

### 18.3 与 LCEL 对照

| 维度 | Haystack Pipeline | LangChain LCEL |
|------|-------------------|----------------|
| 拓扑 | 显式 YAML/图 | 代码 `\|` 组合 |
| 类型 | 组件 IO 类型 | Runnable 协议 [125] |
| 学习曲线 | 图配置 | Python 链 |
| 审计 | 图即文档 | 需额外导出 |

### 18.4 何时读 Haystack 源码

设计 [138 配置驱动](138.config-driven-pipeline-tutorial.md) 管道、或 [135 混合架构](135.pipeline-vs-framework-tutorial.md) 需要 **DSL 参考** 时。不必全员培训 Haystack API。

### 18.5 序列化与 CI

Pipeline 图可 export JSON——适合 **PR 审查**「是否偷偷改了 retriever top_k」。LCEL 团队可用 **快照测试** 或 LangSmith 达成类似效果 [147](147.langsmith-tracing-tutorial.md)。

### 18.6 作业

1. 在白板画 ingest + query 两支 Haystack 风格图，标注 [129][128][110] 对应模块；  
2. 写 10 行「若自研 DSL，组件接口应包含哪些字段」；  
3. 对比 [126 LCEL](126.langchain-lcel-tutorial.md) 链的优缺点各 3 条。
""",

    "pipeline-vs-framework": r"""

## 18. 附录：分层取舍工作坊（半日议程）

### 18.1 工作坊议程

| 时段 | 活动 | 产出 |
|------|------|------|
| 0:00-0:30 | 讲清光谱：纯自研 / 混合 / 框架梭哈 | 共识图 |
| 0:30-1:30 | 模块填表：Parser、Splitter、Embed、Store、Retriever、Prompt、ACL、观测 | 取舍表 v1 |
| 1:30-2:30 | 金标 [143] 与回滚 [154] 约束下修订 | 取舍表 v2 |
| 2:30-3:00 | 与 [136][137] 可插拔契约对齐 | 接口草案 |

### 18.2 分层推荐（起点，非银弹）

| 层 | 常见选择 | 理由 |
|----|----------|------|
| Parser/Splitter | 混合：自研协议 + LC 适配 | 格式多样 [136] |
| Embed | 框架 API + 自研缓存 [68] | 模型迭代快 |
| Store | 自研契约 + Chroma/Milvus | 数据主权 |
| Retriever | 自研 ACL 包装 + LC | 安全 [121] |
| Prompt | 框架模板 [110] | 迭代快 |
| 观测 | Langfuse 等 [148] | 省运维 |

### 18.3 三条硬原则

1. **有金标再梭哈框架**——否则换框架只是换坑。  
2. **ACL/租户永不过度外包**——[53][166] 必须自控。  
3. **任何层都要能回滚**——[154 参数版本](154.param-version-management-tutorial.md)。

### 18.4 与 [125-127][128-130] 关系

框架层选 LangChain 时，[125-130] 是 **落地细节**；本篇是 **战略层**。先战略后战术，避免「全会 API 不知为何用」。

### 18.5 案例讨论

**案例 A 创业公司**：框架梭哈 LC + Chroma，3 个月上线；ACL 简单。  
**案例 B 金融**：Store/Retriever/ACL 自研，Prompt 用 LC；审计通过。  
**案例 C 大厂**：自研 DSL [138]，框架仅 PoC。  

小组讨论：你们公司像哪一类？缺什么能力？

### 18.6 作业

完成取舍表 v2 并 wiki 发布；每条选择附 **一条可验证假设**（对接 [153 A/B](153.ab-experiment-rag-tutorial.md)）。
""",

    "pluggable-parser-splitter-embedder": r"""

## 18. 附录：三接口 Protocol 草案与注册表实现要点

### 18.1 Parser / Splitter / Embedder Protocol（概念）

```python
from typing import Protocol

class Parser(Protocol):
    def parse(self, path: str) -> list["RawDocument"]: ...

class Splitter(Protocol):
    def split(self, docs: list["RawDocument"]) -> list["Chunk"]: ...

class Embedder(Protocol):
    def embed(self, chunks: list["Chunk"]) -> list["EmbeddedChunk"]: ...
```

每类输出带 `schema_version`；Breaking 变更升 major。与 [137 Store/Retriever/Generator](137.pluggable-store-retriever-generator-tutorial.md) 对称，组成 **六接口可插拔** 全景。

### 18.2 注册表模式

```python
PARSERS = {"pymupdf": PyMuPDFParser, "markdown": MarkdownParser}
def get_parser(name: str) -> Parser:
    return PARSERS[name]()
```

[138 配置驱动](138.config-driven-pipeline-tutorial.md) 从 YAML 读 `parser: pymupdf`，工厂实例化。**禁止** if-else 散落十个 ingest 脚本。

### 18.3 LangChain 适配器层

| 自研接口 | LC 适配 |
|----------|---------|
| Parser | [129 Loader](129.langchain-document-loader-tutorial.md) 薄包装 |
| Splitter | [130 TextSplitter](130.langchain-text-splitter-tutorial.md) 子类 |
| Embedder | `Embeddings` 实现 [125] |
| 下游 | [128 VectorStore](128.langchain-vectorstore-tutorial.md) |

### 18.4 版本与索引任务

索引任务 manifest 记录：`parser_v, splitter_v, embedder_v, store_v`。回归 [144](144.regression-test-set-tutorial.md) 时 **四元组必须一致**。换 embedder 未重建索引 = [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 温床。

### 18.5 测试策略

- Parser：黄金 PDF/Markdown 快照测试；  
- Splitter：chunk 边界与 chunk_id 唯一性；  
- Embedder：维度、归一化、批处理 [67]；  
- 集成：端到端 ingest 10 文档进 [76 Chroma](76.chroma-vector-db-tutorial.md)。

### 18.6 与 [125-127][135] 闭环

[135 取舍](135.pipeline-vs-framework-tutorial.md) 决定哪层自研；本篇定义 **数据入口三接口**；[137](137.pluggable-store-retriever-generator-tutorial.md) 定义 **检索生成三接口**。六接口齐全才可 **配置化组装** [138](138.config-driven-pipeline-tutorial.md)。

### 18.7 作业

1. 实现 `MarkdownParser` + `RecursiveSplitter` + `FakeEmbedder` 最小注册表；  
2. manifest JSON 示例写入 wiki；  
3. 画六接口数据流图（Parser→…→Generator）。

### 18.8 接口方法清单（Parser）

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| parse(path) | 文件路径 | list[RawDocument] | 主入口 |
| sniff(path) | 文件路径 | mime | 可选，路由用 |
| validate(raw) | RawDocument | bool | Schema 校验 |

### 18.9 接口方法清单（Splitter）

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| split(raws) | list[RawDocument] | list[Chunk] | 主入口 |
| config() | — | dict | 返回 size/overlap 供 manifest |

### 18.10 接口方法清单（Embedder）

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| embed_documents(texts) | list[str] | list[vector] | 批量 |
| embed_query(text) | str | vector | 查询对称 |
| dimension() | — | int | 维数契约 |

### 18.11 错误处理约定

Parser 抛 `ParseError` 带 `source`；Splitter 抛 `SplitError` 带 `doc_id`；Embedder 抛 `EmbedError` 带 `batch_idx`。索引任务 [161] 捕获后写死信 [163]，**禁止** 静默吞掉半库脏数据。

### 18.12 与 LangChain [125-130] 适配清单

| 自研 | 适配步骤 |
|------|----------|
| Parser | 写 `BaseLoader` 包装 parse() |
| Splitter | 继承 `TextSplitter` 或组合 |
| Embedder | 实现 `Embeddings` 协议 |
| 输出 | 接 [128 VectorStore](128.langchain-vectorstore-tutorial.md) |

### 18.13 灰度与双跑

新版本 Parser 对 5% 文档 **双跑 diff** `content_hash` 与 chunk 数；差异超阈值 **阻断全量**。与 [162 幂等重索引](162.idempotent-reindex-tutorial.md) 共用 job_id，便于回滚。

### 18.14 面试十问

**Q1**：为何三接口先于 [137] 三件套？  
**A**：数据入口错误会污染全库，越早抽象越便宜。

**Q2**：registry 放哪？  
**A**：单模块 `registry.py` 或 [138] YAML 工厂，禁止散落 if/else。

**Q3**：schema_version 谁升？  
**A**：Breaking 变更升 major；索引任务按版本路由。

**Q4**：如何测 Parser？  
**A**：黄金文件快照 + 乱码/扫描件负例。

**Q5**：与 [129 Loader](129.langchain-document-loader-tutorial.md) 关系？  
**A**：Loader 是 LC 脸；Parser 是脊椎。

**Q6**：Embedder 批大小？  
**A**：见 [67](67.embedding-batching-tutorial.md)，外层循环，勿逐条。

**Q7**：换 BGE 要做什么？  
**A**：新 embedder 版本 + 新 collection [128] + 全量重建。

**Q8**：谁审批接口变更？  
**A**：架构 + 数据组；回归 [144] 过才合并。

**Q9**：六接口图挂哪？  
**A**：Wiki 首页 + onboarding 第一天讲解。

**Q10**：30 秒电梯演讲？  
**A**：「入口三接口可插拔，契约+注册表+manifest，LC 是适配器，换实现不改管道。」
""",
}

REVIEW_LOOP_DEFAULT = (
    "### 复习打卡\n\n"
    "对照 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 阶段验收项、本篇动手路径与 "
    "[125 LangChain 核心](125.langchain-core-tutorial.md)、[126 LCEL](126.langchain-lcel-tutorial.md)、"
    "[127 Retriever](127.langchain-retriever-tutorial.md) 系列交叉链接，逐项勾选未完成项并记入下周 sprint。"
)

REVIEW_LOOP = {
    "langchain-vectorstore": (
        "### 复习：VectorStore 五问\n\n"
        "**问**：ingest 与 query 的 Embeddings 为什么要同一实例？"
        "**答**：向量空间必须一致，否则相似度无意义，见 [25](25.embedding-vector-tutorial.md)。\n\n"
        "**问**：`as_retriever` 与 `similarity_search` 分工？"
        "**答**：前者接 [126 LCEL](126.langchain-lcel-tutorial.md) 与 [127](127.langchain-retriever-tutorial.md) 策略层，后者是存储层原语。\n\n"
        "**问**：Chroma 与 FAISS 在 LC 中如何选型？"
        "**答**：要 metadata filter 与持久化省事选 Chroma [76]；要极致 ANN 且自管 sidecar 选 FAISS [75]。\n\n"
    ),
    "langchain-document-loader": (
        "### 复习：Loader 五问\n\n"
        "Loader 产出什么类型？[125 Document](125.langchain-core-tutorial.md)。"
        "metadata 最少字段？doc_id、source、acl_group [50][53]。"
        "增量键？content_hash [49]。编码坑？[41]。"
        "与 Parser 边界？[136] 厚、Loader 薄。"
        "下游谁消费？[130 Splitter](130.langchain-text-splitter-tutorial.md) → [128 VectorStore](128.langchain-vectorstore-tutorial.md)。\n\n"
    ),
    "langchain-text-splitter": (
        "### 复习：Splitter 五问\n\n"
        "chunk_size 谁定？[143 金标](143.golden-dataset-tutorial.md) 网格搜索，非拍脑袋。"
        "overlap 副作用？[106 去重](106.retrieval-dedup-tutorial.md) 与 [105 MMR](105.mmr-diversity-tutorial.md) 压力。"
        "chunk_id 规范？[51](51.metadata-chunk-id-tutorial.md) 唯一且稳定。"
        "改参数要不要重建索引？要，[48 版本](48.doc-versioning-tutorial.md)。"
        "中文分隔符？句号、分号入 separators 列表。\n\n"
    ),
    "llamaindex-index-types": (
        "### 复习：Index 了解即可\n\n"
        "主栈 LangChain [125-128](125.langchain-core-tutorial.md)；LI Index 用于对照与面试。"
        "生产最常见？VectorStoreIndex。与 LC 映射？见本篇 §10 表。"
        "学习预算？≤2 小时 + [132][133] 各速览。\n\n"
    ),
    "llamaindex-query-engine": (
        "### 复习：Query Engine\n\n"
        "一站式 query() vs [126 LCEL](126.langchain-lcel-tutorial.md) 透明管道？团队要审计选 LCEL。"
        "source_nodes 对应？[113 引用](113.inline-citation-tutorial.md) 与 [34 Grounding](34.grounding-citation-tutorial.md)。"
        "流式生产路径？[116 SSE](116.sse-rag-streaming-tutorial.md) + LCEL astream。\n\n"
    ),
    "llamaindex-agent": (
        "### 复习：Agent 边界\n\n"
        "企业 QA 默认？固定 RAG 管道，非 Agent。"
        "与 [124 Function Calling](124.function-calling-tool-use-tutorial.md) ？单步工具 vs 多步规划。"
        "必配？max_iterations、ACL [121]、配额 [169]、trace [147]。\n\n"
    ),
    "haystack-pipeline": (
        "### 复习：Pipeline 思想\n\n"
        "核心价值？显式 Component-Connection 图，可审计，可 export。"
        "与 LCEL？[126](126.langchain-lcel-tutorial.md) 快速组合 vs 图配置；可 CI 导出拓扑 JSON。"
        "自研 DSL？[138 配置驱动](138.config-driven-pipeline-tutorial.md) 参考 Haystack。\n\n"
    ),
    "pipeline-vs-framework": (
        "### 复习：架构取舍\n\n"
        "裁判？[143 金标](143.golden-dataset-tutorial.md)。"
        "不可外包？[53 ACL](53.metadata-acl-tutorial.md)、[166 租户](166.tenant-isolation-backend-tutorial.md)。"
        "可回滚？[154 参数版本](154.param-version-management-tutorial.md)。"
        "战术落地？[128-130](128.langchain-vectorstore-tutorial.md) + [136 契约](136.pluggable-parser-splitter-embedder-tutorial.md)。\n\n"
    ),
    "pluggable-parser-splitter-embedder": (
        "### 复习：三接口\n\n"
        "Parser/Splitter/Embedder 输出？带 schema_version 的可序列化契约。"
        "注册表？[138 YAML](138.config-driven-pipeline-tutorial.md) 或 registry.py 工厂。"
        "下游？[137 Store/Retriever/Generator](137.pluggable-store-retriever-generator-tutorial.md) 组成六接口。"
        "LC 适配？[129][130][128](128.langchain-vectorstore-tutorial.md) 薄包装。"
        "测试？快照 + 集成 ingest + [144 回归](144.regression-test-set-tutorial.md)。\n\n"
    ),
}
