# -*- coding: utf-8 -*-
"""Large final sections for tutorials 128-136 — merged in assemble phase."""

FINAL_SECTIONS = {
    "langchain-vectorstore": r"""

## 20. 系列复习：D 轨 LangChain 存储链与 C 轨对照

### 20.1 从 [125] 到 [128] 的数据流复述

[125 LangChain 核心](125.langchain-core-tutorial.md) 定义 `Document` 与 `Embeddings` 协议；[126 LCEL](126.langchain-lcel-tutorial.md) 定义 Runnable 组合；[127 Retriever](127.langchain-retriever-tutorial.md) 定义 `invoke(query)→docs`；**本篇 VectorStore** 定义 `add_documents` 与 `similarity_search`。四篇连成 **「存→搜→策略→编排」** 闭环。初学者常跳过 128 直接写 LCEL，结果链能跑但 **不懂数据落在哪**——一出问题只能重跑 ingest。

对照 C 轨：[75 FAISS](75.faiss-ann-tutorial.md) 教你 ANN；[76 Chroma](76.chroma-vector-db-tutorial.md) 教你向量库三件套；128 教你 **少写胶水接 LangChain**。面试时按 C→D 顺序讲，体现 **「先懂原理再借框架」**。

### 20.2 生产检查表（第十遍强调）

入库脚本与查询 API **必须 import 同一 Embeddings 工厂**；collection 名含模型版本；ids 等于 chunk_id；ACL 用 filter 不用 prompt；持久化目录按环境隔离；每次发布跑回归集 [144](144.regression-test-set-tutorial.md)；观测记录 hit_ids [147](147.langsmith-tracing-tutorial.md)。十条做到，VectorStore 层事故率下降一个数量级。
""",

    "langchain-document-loader": r"""

## 20. 系列复习：数据入口与 [125][129] 契约

### 20.1 Loader 是 metadata 的出生地

[125](125.langchain-core-tutorial.md) 的 Document 若无 `doc_id、source、acl_group`，后面 [128 VectorStore](128.langchain-vectorstore-tutorial.md) 无法 filter，[113 引用](113.inline-citation-tutorial.md) 无法导航 [115](115.source-document-navigation-tutorial.md)。Loader 阶段就要 **Schema 校验**，不合格拒绝进入 [130 Splitter](130.langchain-text-splitter-tutorial.md)。

### 20.2 国内工程三大坑

编码 [41]、扫描件空文本 [55]、NAS 全量扫 [49]。本篇 §8 先错对对针对前两项；增量与 manifest 针对第三项。Wiki 写清 **「Loader 失败处理 SOP」**：重试三次→死信 [163]→人工→修复源文件→重跑任务 [161]。

### 20.3 与框架边界

Loader 薄、Parser 厚 [136]。复杂表格在 [42 PyMuPDF](42.pymupdf-tutorial.md) 单测，Loader 只选 backend。团队新人常把 PDF 解析逻辑写进 Loader 子类——三个月后无法换 Parser，违背 [135 取舍](135.pipeline-vs-framework-tutorial.md)。
""",

    "langchain-text-splitter": r"""

## 20. 系列复习：切块是 Recall 的隐形开关

### 20.1 为何 [130] 是地基篇

同样 embed 与 VectorStore，**只改 chunk_size** 可使 Recall@3 从 0.4 变 0.7 或反之。Splitter 不是「工具一行」——它是 [61 权衡](61.chunk-size-tradeoff-tutorial.md) 的落地。金标 [143](143.golden-dataset-tutorial.md) 不调切块就调 top_k，是 **本末倒置**。

### 20.2 与 [129][128] 的握手

Loader 产出 Document；Splitter 产出带 chunk_id 的 chunk；VectorStore 用 chunk_id 作 ids。metadata 父级字段 **只增不删**。改 splitter 配置 = 新索引版本 [48][154]。

### 20.3 结构感知是趋势

纯递归适合纯文本；制度+代码+表格混排用 [62 结构感知](62.structure-aware-chunking-tutorial.md) + [63 Markdown AST](63.markdown-ast-chunking-tutorial.md)。Splitter 注册表 [136] 允许按 `mime` 路由不同实现——与 [135 混合架构](135.pipeline-vs-framework-tutorial.md) 一致。
""",

    "llamaindex-index-types": r"""

## 20. 系列复习：了解即可 ≠ 可跳过

### 20.1 为何要读 LI Index

招聘市场、竞品方案、论文 baseline 常出现 LlamaIndex 名词。本篇让你 **30 分钟建立对照表**，避免沟通时 **把 Node 当 Document 反复确认**。主栈仍是 [125-128](125.langchain-core-tutorial.md) LangChain。

### 20.2 VectorStoreIndex 与 [128] 的差异记忆点

LI 常在构建 Index 时 embed；LC 常在 VectorStore.add 时 embed。**构建时机不同**导致性能剖析图不同——不是谁对谁错。生产选型看团队主栈与观测习惯 [147][148]。

### 20.3 学习预算

本篇 + [132](132.llamaindex-query-engine-tutorial.md) + [133](133.llamaindex-agent-tutorial.md) 合计 **≤1 工作日**；其余投入 [127 Retriever](127.langchain-retriever-tutorial.md) 与 [135 架构](135.pipeline-vs-framework-tutorial.md)。路线图已标档位，**尊重档位** 才能按时交付 PoC。
""",

    "llamaindex-query-engine": r"""

## 20. 系列复习：一站式 query() vs 透明 LCEL

### 20.1 透明度是工程团队首选 LCEL 的原因

Query Engine 黑盒在 `query()` 内完成 retrieve + synthesize；LCEL 每步可插日志、ACL、rerank [95]。金融、医疗合规团队要 **逐步审计**——[126](126.langchain-lcel-tutorial.md) 胜出。了解 Query Engine 是为了 **读懂 LI 生态**，不是为了替换主链。

### 20.2 source_nodes 与 [113] 引用

无论 LI 还是 LC，前端 [171 聊天 UI](171.chat-message-list-ui-tutorial（front-end）.md) 需要 **稳定 citation id**。Query Engine 的 `source_nodes` 映射到 [113 行内引用](113.inline-citation-tutorial.md) 与 [176 卡片](176.citation-card-ui-tutorial（front-end）.md)。协议设计时 **统一 JSON 字段**：`chunk_id, score, source, page`。

### 20.3 流式 [116] 与 Query Engine

生产 SSE [116](116.sse-rag-streaming-tutorial.md) 多在 FastAPI + LCEL `astream` 实现。LI 流式了解即可；**前后端契约** 以 OpenAPI [170] 与 SSE 事件为准。
""",

    "llamaindex-agent": r"""

## 20. 系列复习：Agent 不是 RAG 默认解

### 20.1 固定管道优先

[91 稠密检索](91.dense-retrieval-tutorial.md) + [110 Prompt](110.rag-prompt-template-tutorial.md) + [112 拒答](112.refusal-strategy-tutorial.md) 覆盖多数企业 QA。Agent 引入 **非确定性** 与 **多倍 token**。路线图 [133] 标了解：会名词、会风险、会 **何时不用**。

### 20.2 与 [124] Function Calling 分工

单步工具调用（查库、算数）用 Function Calling [124]；多步规划用 Agent。LlamaIndex Agent 是 LI 侧实现；LangChain 有 `AgentExecutor`。主栈选一个，**不要双 Agent 并存**。

### 20.3 安全

每个工具带 ACL [121]；`max_iterations`；用户配额 [169]；trace 每步 [147]。Agent 越权事故比固定管道 **更难复盘**——上线前红队测试。
""",

    "haystack-pipeline": r"""

## 20. 系列复习：Pipeline 思想超越 Haystack 品牌

### 20.1 显式图的价值

Haystack 2.x 的 Component-Connection 图可序列化、可 PR 审查——这与 [138 配置驱动](138.config-driven-pipeline-tutorial.md) 目标一致。即使不用 Haystack，**ingest 支与 query 支分图绘制** 应是团队 onboarding 第一课。

### 20.2 与 [126 LCEL](126.langchain-lcel-tutorial.md) 共存

LCEL 适合 Python 团队快速迭代；显式图适合 **合规审计** 与 **非 Python 同事读拓扑**。混合做法：LCEL 运行，CI 导出拓扑 JSON 存档。

### 20.3 与 [135 取舍](135.pipeline-vs-framework-tutorial.md) 衔接

读 Haystack 是为了 **设计自研 DSL**，不是为了多装一个框架。PoC 阶段框架梭哈可接受；规模上来后 **六接口 [136][137]** 比品牌更重要。
""",

    "pipeline-vs-framework": r"""

## 20. 系列复习：架构决策如何落地到 [128-136]

### 20.1 本篇是 D 轨战略总纲

[128 VectorStore](128.langchain-vectorstore-tutorial.md)、[129 Loader](129.langchain-document-loader-tutorial.md)、[130 Splitter](130.langchain-text-splitter-tutorial.md) 是战术；[136 可插拔](136.pluggable-parser-splitter-embedder-tutorial.md) 是契约；**本篇** 回答 **哪层用框架、哪层自研**。没有本篇，团队会争论「要不要 LangChain」而 **没有评判标准**。

### 20.2 金标是裁判

[143 Golden Dataset](143.golden-dataset-tutorial.md) 存在时，架构争论变为 **可测假设**；不存在时，争论是 **职位战争**。先金标，后架构；先回归 [144]，后重构。

### 20.3 回滚是信任基础

[154 参数版本](154.param-version-management-tutorial.md) 与 [153 A/B](153.ab-experiment-rag-tutorial.md) 让「试框架」可逆。不能回滚的框架迁移 **不是优化，是赌博**。
""",

    "pluggable-parser-splitter-embedder": r"""

## 20. 系列复习：六接口与全栈 RAG 骨干

### 20.1 本篇 + [137] = 可替换骨干

数据入口三接口（Parser/Splitter/Embedder）+ 检索生成三接口（Store/Retriever/Generator）[137] = **企业 RAG 脊椎**。LangChain [125-130] 是 **适配器集合**，不是脊椎本身——[135](135.pipeline-vs-framework-tutorial.md) 的混合架构常如此落地。

### 20.2 版本 manifest 示例

```json
{
  "job_id": "ingest-2026-07-11",
  "parser": "pymupdf@2.1",
  "splitter": "recursive_zh@3",
  "embedder": "bge-m3@1",
  "store": "chroma_handbook_bge_v3",
  "chunk_count": 12840
}
```

与 [161 状态机](161.index-task-state-machine-tutorial.md)、[162 幂等](162.idempotent-reindex-tutorial.md) 同表存储。排障时 **先对 manifest**，再对代码。

### 20.3 测试金字塔

Parser 快照 > Splitter 边界 > Embedder 维度 > 集成 ingest 10 文档 > 金标端到端 [143]。契约测试失败 **阻断发布**；比线上 [150 切块 bad case](150.bad-case-chunking-tutorial.md) 便宜两个数量级。
""",
}
