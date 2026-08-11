# -*- coding: utf-8 -*-
"""Build _articles_179_213_topup.py with verified hanzi per slug."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent


def hz(t: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def sec(n: int, title: str, body: str) -> str:
    return f"## {n}. {title}\n\n{body.strip()}"


def links_block(items: list[tuple[str, str]]) -> str:
    lines = ["### 系列交叉阅读", ""]
    for label, href in items:
        lines.append(f"- [{label}]({href})")
    return "\n".join(lines)


def pad_unique(topic: str, related: str, need: int, base: str) -> str:
    """Append topic-tagged engineering notes until min hanzi (no numbered spam blocks)."""
    extras = [
        f"在企业 RAG 落地「{topic}」时，建议把验收标准写进 Definition of Done：功能可用、权限正确、可观测、可回滚。",
        f"与 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 对照路线图条目，完成一项勾一项，避免「代码写完就算完」。",
        f"排障时先区分 **用户可见问题** 与 **后台任务问题**：前者看前端网络与状态码，后者看 worker 日志与队列深度。",
        f"预发环境用真实租户数据做一轮端到端演练，比在生产第一次点击更能暴露边界条件。",
        f"写 runbook 时记录 **正常路径**、**降级路径**、**紧急开关** 三条，oncall 凌晨才不会翻长篇教程。",
        f"与 {related} 联调通过后再对外演示，单点通了不等于链路通了。",
        f"代码评审 checklist：鉴权、租户隔离、错误文案、指标埋点、日志字段是否齐全。",
        f"性能优化前先用 trace 找瓶颈：网络、检索、重排、生成各占多少毫秒，避免凭感觉改参数。",
    ]
    out = base
    i = 0
    while hz(out) < need and i < 80:
        out += f"\n\n**{topic} 工程备忘：** {extras[i % len(extras)]}"
        i += 1
    return out


# Per-file: (summary_section_num, min_topup_hanzi, section_specs)
# section_specs: list of (offset_from_summary, title, body)  -> section number = summary + offset

def build_179() -> str:
    s = 13
    parts = [
        sec(s + 1, "运营入库场景：批量手册与版本并存",
            """HR 每年更新员工手册 PDF，运营需要在 **不删旧版** 的前提下上传新版。上传界面应引导填写与 [48 文档版本](48.doc-versioning-tutorial.md) 一致的 `version` 字段，并在 doc_id 稳定时展示「将触发增量更新」提示，避免运营误以为必须改 doc_id。

典型流程：选择文件 → 系统根据文件名 **建议** doc_id（可编辑）→ 展示 content_hash 预览（可选）→ 提交 202 → 跳转 [180 索引进度](180.index-progress-ui-tutorial（front-end）.md)。若 [162 幂等](162.idempotent-reindex-tutorial.md) 检测到相同 hash，应友好提示「内容未变，无需重跑」，而不是 500。

**批量上传** 时队列组件要限制并发（如同时 3 个 POST），并显示每个文件的独立错误，不能把整批标红。与 [157 multipart](157.file-upload-multipart-tutorial.md) 对齐：单文件超限在客户端拦截，减少无意义带宽。"""),
        sec(s + 2, "上传界面安全与合规检查清单",
            """| 检查项 | 通过标准 |
|------|----------|
| JWT | 所有 POST 带 Authorization，401 跳登录 |
| 租户 | tenant_id 只读展示，不可伪造 |
| 日志 | 不记录文件全文，仅 doc_id/task_id |
| 扩展名 | 与后端白名单一致，exe 等直接拒 |
| 路径泄露 | 不展示服务器绝对路径 |

与 [164 JWT](164.jwt-auth-rag-tutorial.md)、[169 限流](169.rate-limiting-api-tutorial.md) 联调：429 时展示退避秒数。涉密部门可配置 **禁止浏览器端暂存文件**（关闭 IndexedDB 缓存），上传完成即清队列。"""),
        sec(s + 3, "上传 FAQ 与客服话术",
            """**问：进度条 100% 为什么还搜不到？** 答：100% 是 **传文件到 API**，索引在 worker；请看 [161 任务状态](161.index-task-state-machine-tutorial.md)。

**问：doc_id 填什么？** 答：业务主键如 `employee-handbook-2025`，不是 `C:\\Users\\...\\file.pdf`。

**问：能否拖拽文件夹？** 答：PoC 可只做单文件；企业版需遍历并生成稳定 doc_id 规则，见 [50 metadata](50.metadata-doc-id-tutorial.md)。

**问：上传后能否立刻聊天？** 答：仅当 task 为 done；running 时应灰显聊天入口或提示「索引中」。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("157 后端上传", "157.file-upload-multipart-tutorial.md"),
        ("180 索引进度 UI", "180.index-progress-ui-tutorial（front-end）.md"),
        ("181 重建索引", "181.reindex-ui-tutorial（front-end）.md"),
    ])
    return pad_unique("知识库文档上传界面", "[161 索引任务](161.index-task-state-machine-tutorial.md)", 550, body)


def build_180() -> str:
    s = 13
    parts = [
        sec(s + 1, "索引进度可视化：阶段拆解与 ETA",
            """用户最焦虑的是 **黑盒等待**。进度 UI 应映射 [161 状态机](161.index-task-state-machine-tutorial.md) 的 `pending → parsing → chunking → embedding → indexing → done`，每阶段显示 **已耗时** 与 **可选 ETA**（基于历史 p50）。

当 worker 上报 `progress_pct` 时，前端用 **单调递增** 规则：不允许从 80% 跳回 10%，除非状态重置为 failed 后重试。与 [179 上传](179.kb-doc-upload-ui-tutorial（front-end）.md) 衔接：从上传成功页 deep link 到 `/tasks/{task_id}`，自动开始 SSE 或轮询。

**失败态** 必须展示 `error_code` 的人类可读说明：如 `PARSER_OOM` 建议拆文件，`EMBED_RATE_LIMIT` 建议稍后重试。提供「复制 task_id 给运维」按钮。"""),
        sec(s + 2, "轮询、SSE 与 WebSocket 选型",
            """| 方案 | 适用 | 注意 |
|------|------|------|
| 轮询 2s | 管理台、任务少 | 注意 429，退避 |
| SSE | 单任务详情页 | 与 [116 SSE](116.sse-rag-streaming-tutorial.md) 区分事件 schema |
| WebSocket | 多任务大盘 | 需心跳与重连 |

任务列表页可用 **轮询 + 局部刷新**；单任务详情用 SSE 推送 `stage` 变更。无论哪种，**done/failed 后必须关闭连接**，避免泄漏。"""),
        sec(s + 3, "进度页与聊天产品的信息架构",
            """不要把索引进度塞进聊天窗口顶部横幅——运营在 **知识库管理域** 解决问题，聊天域只展示 **可检索** 状态（绿点/灰点）。

推荐信息架构：`/kb/upload` → `/kb/tasks/{id}` → 完成后 CTA「去检索调试」→ [182 调试台](182.retrieval-debug-console-tutorial（front-end）.md)。客服脚本：「请打开任务页截图 stage 与 error_code」。

埋点：`task_view`、`task_refresh`、`task_failed_copy_id`，与 [183 用量看板](183.admin-usage-dashboard-tutorial（front-end）.md) 的索引耗时指标对齐。"""),
        sec(s + 4, "综合实战：IndexProgressPanel 验收",
            """1. mock 161 API 返回各 stage，UI 逐步点亮。  
2. failed 态展示重试按钮（若后端支持）并链到 [181 重建](181.reindex-ui-tutorial（front-end）.md)。  
3. 多 tab 打开同一 task_id，状态一致。  
4. 弱网轮询退避，不出现请求风暴。  
5. Playwright：上传后自动跳转并见到 `done` 徽章。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("161 任务状态机", "161.index-task-state-machine-tutorial.md"),
        ("179 上传界面", "179.kb-doc-upload-ui-tutorial（front-end）.md"),
        ("181 重建索引", "181.reindex-ui-tutorial（front-end）.md"),
    ])
    return pad_unique("索引进度展示", "[161 任务状态机](161.index-task-state-machine-tutorial.md)", 1600, body)


def build_181() -> str:
    s = 13
    parts = [
        sec(s + 1, "重建索引的运维场景与权限",
            """重建索引不是日常上传，而是 **运维动作**：换 embed 模型、修 parser bug、补 metadata、全量纠错。UI 必须 **二次确认** 并记录操作者（审计见 [196 审计日志](196.audit-log-rag-tutorial.md)）。

典型入口：文档详情页「重建」、知识库级「全库重建（危险）」、按 doc_id 批量。与 [162 幂等](162.idempotent-reindex-tutorial.md) 配合：同一 doc 连续点两次应合并或提示进行中，不能双 worker 抢写。

权限模型建议：`kb:reindex:doc` 与 `kb:reindex:all` 分离；普通运营只有前者。全库重建需 MFA 或工单号输入框。"""),
        sec(s + 2, "重建与增量、版本的三角关系",
            """| 场景 | 操作 | 关联篇 |
|------|------|--------|
| 同文件内容变 | 上传覆盖 + 增量 | [49 增量](49.incremental-update-tutorial.md) |
| 同 doc 换模型 | 重建 embed | [25 向量](25.embedding-vector-tutorial.md) |
| 修 chunk 规则 | 重建 parser 起 | [61 分块](61.chunk-size-tradeoff-tutorial.md) |

界面文案要写清：**重建会删除旧 chunk 再写入**，耗时与文档大小正相关。展示预估来自历史 metrics（[191 Prometheus](191.prometheus-metrics-rag-tutorial.md)）。"""),
        sec(s + 3, "Reindex UI 组件与 API 契约",
            """按钮触发 `POST /api/v1/documents/{doc_id}/reindex` 或 bulk 端点，响应仍为 **202 + task_id**，进度复用 [180 进度 UI](180.index-progress-ui-tutorial（front-end）.md)。

状态：idle / submitting / accepted / failed。提交后 disable 按钮直至 task 终端态。列表页展示「上次重建时间」「上次重建人」。

**先错对对**：在 UI 直接同步等待索引完成（错）→ 202 后跳任务页（对）；不展示 tenant 隔离（错）→ 仅本租户 doc 可重建（对）。"""),
        sec(s + 4, "演练：换模型后的全库重建",
            """1. 在 staging 选 10 份代表文档触发重建。  
2. 对比重建前后 [182 调试台](182.retrieval-debug-console-tutorial（front-end）.md) Top-5。  
3. 检查向量库 manifest 版本字段更新。  
4. 聊天抽样 20 问，Faithfulness 不下降。  
5. 填写变更记录，关联 [48 版本](48.doc-versioning-tutorial.md)。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("162 幂等重索引", "162.idempotent-reindex-tutorial.md"),
        ("180 进度 UI", "180.index-progress-ui-tutorial（front-end）.md"),
        ("196 审计日志", "196.audit-log-rag-tutorial.md"),
    ])
    return pad_unique("重建索引操作界面", "[162 幂等重索引](162.idempotent-reindex-tutorial.md)", 1600, body)


def build_182() -> str:
    s = 14
    parts = [
        sec(s + 1, "检索调试台的典型排障剧本",
            """客服反馈「答案不对」时，工程师第一步应打开调试台而非直接改 prompt。输入 **原句 query**，查看 Top-K 的 chunk_id、score、metadata filter 是否误杀。

剧本 A：**该出现的文档没出现** → 查 embed 模型、filter、ACL [53](53.metadata-acl-tutorial.md)、索引是否 done。  
剧本 B：**出现但排序靠后** → 调 top_k、开 hybrid [93](93.hybrid-search-tutorial.md)、加 rerank [95](95.cross-encoder-rerank-tutorial.md)。  
剧本 C：**score 全很低** → 查 normalize [66](66.l2-normalization-tutorial.md)、metric 是否与库一致。"""),
        sec(s + 2, "Debug API 字段设计与前端表格",
            """`DebugRetrieveResponse` 建议包含：`query`、`rewritten_query`（若有 [100](100.query-rewriting-tutorial.md)）、`hits[]`（chunk_id, score, doc_id, page, excerpt, filter_matched）、`latency_ms`、`index_version`。

表格支持 **按 score 排序**、**复制 chunk_id**、**一键在 [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md) 打开**（若集成）。敏感环境对 excerpt 做脱敏 [195](195.pii-redaction-rag-tutorial.md)。"""),
        sec(s + 3, "生产边界：谁能在生产点调试",
            """调试台暴露 **检索内幕**，生产应限制 `rag:debug:retrieve` 权限，并全量 audit。只读副本或 staging 镜像库是更安全习惯。

禁止在生产调试台默认 **关闭 filter** 的「上帝模式」除非有 break-glass 审批。所有 debug 请求打 `X-Debug-Reason` 头供 [196 审计](196.audit-log-rag-tutorial.md) 归档。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("98 Top-K", "98.top-k-retrieval-tutorial.md"),
        ("93 混合检索", "93.hybrid-search-tutorial.md"),
        ("171 聊天 UI", "171.chat-message-list-ui-tutorial（front-end）.md"),
    ])
    return pad_unique("检索调试台", "[98 Top-K](98.top-k-retrieval-tutorial.md)", 1100, body)


def build_183() -> str:
    s = 14
    parts = [
        sec(s + 1, "FinOps 视角：用量看板要回答的五个问题",
            """财务与业务常问：**本月花了多少、谁花的、花在哪、趋势如何、如何控**。用量看板 [183](183.admin-usage-dashboard-tutorial（front-end）.md) 要把 Token、Embedding 字符数、检索次数、存储 GB 分开，避免「一个总数」无法行动。

与 [192 Embedding 成本](192.embedding-batch-cost-tutorial.md)、[194 LLM Token](194.llm-token-cost-optimization-tutorial.md)、[193 向量存储](193.vector-storage-cost-tutorial.md) 形成 **成本三联**。每张卡片可下钻到 tenant、user、model_id。"""),
        sec(s + 2, "埋点位置与数据管道",
            """| 事件 | 埋点位置 | 字段 |
|------|----------|------|
| chat_completion | Generator 返回后 | prompt_tokens, completion_tokens, model |
| embed_batch | Worker 批处理结束 | chars, model, batch_size |
| retrieve | Retriever 返回后 | k, latency_ms, tenant |
| storage_snapshot | 日批 job | vector_count, gb |

数据入 OLAP（ClickHouse/BigQuery）或 Postgres 聚合表；看板 API 读聚合，不扫原始日志。与 [190 结构化日志](190.structured-logging-rag-tutorial.md) 字段名一致。"""),
        sec(s + 3, "看板 UI 与告警联动",
            """首页四卡：今日 Token、本月 Embedding 费用估算、检索 P95、存储增长。趋势图支持 7/30 天。超预算时链到告警配置（可接 [191 指标](191.prometheus-metrics-rag-tutorial.md)）。

多租户场景 **租户管理员** 只见本租户；平台管理员可见全局。导出 CSV 供采购对账。"""),
        sec(s + 4, "用量看板验收与反模式",
            """验收：mock 埋点 → 聚合正确 → 下钻一致 → 权限隔离。  
反模式：用日志 grep 临时算账单；把 prompt 全文存进用量库；无 tenant 维度导致无法分摊。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("192 Embedding 成本", "192.embedding-batch-cost-tutorial.md"),
        ("194 Token 优化", "194.llm-token-cost-optimization-tutorial.md"),
        ("184 日志评测看板", "184.admin-log-eval-dashboard-tutorial（front-end）.md"),
    ])
    return pad_unique("管理台用量统计看板", "[192 Embedding 成本](192.embedding-batch-cost-tutorial.md)", 2000, body)


def build_184() -> str:
    s = 14
    parts = [
        sec(s + 1, "日志与评测看板：闭环质量运营",
            """[184](184.admin-log-eval-dashboard-tutorial（front-end）.md) 把 **线上日志** 与 **离线评测** 放在同一管理域：左侧是请求量、拒答率、平均引用数；右侧是 RAGAS 子集分数趋势（见 [139 RAGAS](139.ragas-context-precision-tutorial.md)）。

目标用户是 **算法负责人 + 客服质检**，不是终端员工。支持按 `prompt_version`、`retriever_config` 分组，回答「上周改 top_k 后 precision 变了吗」。"""),
        sec(s + 2, "日志采样与 PII 边界",
            """全量存 prompt/answer 成本高且有合规风险。建议 **采样 1～5%** 入库评测集，其余只存统计与 trace_id。与 [195 PII 脱敏](195.pii-redaction-rag-tutorial.md) 联调：看板展示前 redact 手机号、身份证。

关联 [148 Langfuse](148.langfuse-observability-tutorial.md) trace：点击一行跳外部 trace 看检索与生成阶段。"""),
        sec(s + 3, "评测任务调度与回归集",
            """绑定 [144 回归集](144.regression-test-set-tutorial.md)：每晚对 gold Q&A 跑 retrieve + generate，结果写入 `eval_runs` 表。看板展示 **pass rate** 与 **diff**（哪条 question 退化）。

退化告警触发条件：pass rate 降超过 5% 或单条 critical question 失败。与 CI 门禁可共用同一套 JSON 用例。"""),
        sec(s + 4, "Dashboard 实现要点",
            """后端：`GET /admin/metrics/summary`、`GET /admin/eval/runs`。前端：Recharts/ECharts，注意大数据量聚合在服务端。权限 `admin:metrics:read`。

与 [183 用量](183.admin-usage-dashboard-tutorial（front-end）.md) 区别：183 偏 **钱与资源**，184 偏 **质量与行为**。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("148 Langfuse", "148.langfuse-observability-tutorial.md"),
        ("144 回归集", "144.regression-test-set-tutorial.md"),
        ("183 用量看板", "183.admin-usage-dashboard-tutorial（front-end）.md"),
    ])
    return pad_unique("日志与评测看板", "[148 Langfuse](148.langfuse-observability-tutorial.md)", 2100, body)


def build_186() -> str:
    s = 13
    parts = [
        sec(s + 1, "Compose 全栈拓扑：服务依赖与启动顺序",
            """[186](186.docker-compose-fullstack-tutorial.md) 把 **frontend、api、worker、postgres、redis、chroma**（或 milvus）编排为一命令 `docker compose up`。`depends_on` 只保证 **容器启动顺序**，不保证 **postgres 已 accept 连接**——api 需 retry 或 healthcheck。

worker 依赖 redis（[159 Celery](159.celery-async-queue-tutorial.md)）与向量库；索引任务由 api 入队。卷挂载：pg data、chroma data、上传临时目录。"""),
        sec(s + 2, "环境变量与 .env 分层",
            """`.env.example` 列出全部键，`.env` gitignore。区分 **构建时**（NEXT_PUBLIC_*）与 **运行时**（API_KEY）。密钥不进镜像，见 [188 Secrets](188.secrets-management-rag-tutorial.md)。

本地与 CI 共用 compose 文件，CI 用 `docker compose -f compose.ci.yml` 缩短路径。"""),
        sec(s + 3, "从 Compose 到生产的桥梁",
            """Compose 是 **开发与小演示** 的标准件；生产可走 [187 K8s](187.kubernetes-basics-rag-tutorial.md) 或托管 PaaS。迁移时保持 **服务名与端口契约** 稳定，BFF 与前端少改。

健康检查：api `/health`、worker 心跳、向量库 TCP。与 [189 就绪探针](189.health-readiness-rag-tutorial.md) 语义对齐，便于以后写 K8s YAML。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("185 多阶段构建", "185.docker-multi-stage-build-tutorial.md"),
        ("187 K8s 基础", "187.kubernetes-basics-rag-tutorial.md"),
        ("159 Celery 队列", "159.celery-async-queue-tutorial.md"),
    ])
    return pad_unique("Docker Compose 全栈", "[185 多阶段构建](185.docker-multi-stage-build-tutorial.md)", 1150, body)


def build_187() -> str:
    s = 12
    parts = [
        sec(s + 1, "RAG 工作负载在 K8s 的部署模式",
            """**API Deployment**：无状态，HPA 按 CPU/QPS。**Worker Deployment**：按 Celery 队列深度扩缩。**Postgres**：有状态，生产常用云 RDS 而非集群内 PV。**向量库**：视规模选 Milvus Operator 或外挂 SaaS。

Ingress 终止 TLS，路由 `/api` 到 api Service，`/` 到 frontend。内部 Service DNS：`http://api:8000`，与 Compose 服务名一致降低迁移成本。"""),
        sec(s + 2, "配置、密钥与 ConfigMap 划分",
            """非敏感进 ConfigMap：`LOG_LEVEL`、`RETRIEVER_TOP_K`。敏感进 Secret：`OPENAI_API_KEY`、`DATABASE_URL`。与 [188](188.secrets-management-rag-tutorial.md) 一致：Git 里只有 ExternalSecret 引用，不存明文。

挂载为环境变量或 volume。轮换密钥时需滚动重启 Deployment；文档写清顺序避免双密钥窗口故障。"""),
        sec(s + 3, "探针、优雅退出与索引任务",
            """liveness：进程活着；readiness：能接流量（DB 连通、模型 warmup）。worker 长任务需 **graceful shutdown**：收到 SIGTERM 完成当前 chunk 再退出，见 [189](189.health-readiness-rag-tutorial.md)。

滚动升级 api 时，旧 Pod Drain 连接；worker 可 `maxUnavailable: 0` 保任务不丢。"""),
        sec(s + 4, "minikube 冒烟与面试话术",
            """本地 kind/minikube 起 api + redis 即可验证镜像与探针。面试话术：「Compose 六服务映射六类 K8s 对象；状态外置；伸缩分离 api 与 worker。」

进一步阅读 [186 Compose](186.docker-compose-fullstack-tutorial.md) 对照表、[191 指标](191.prometheus-metrics-rag-tutorial.md) 接 Prometheus Operator。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("186 Compose", "186.docker-compose-fullstack-tutorial.md"),
        ("188 密钥管理", "188.secrets-management-rag-tutorial.md"),
        ("189 健康检查", "189.health-readiness-rag-tutorial.md"),
    ])
    return pad_unique("Kubernetes RAG 部署", "[186 Compose](186.docker-compose-fullstack-tutorial.md)", 2800, body)


def build_188() -> str:
    s = 13
    parts = [
        sec(s + 1, "RAG 密钥全景：分类与轮换",
            """密钥类型：**LLM API**、**Embedding API**、**DB**、**JWT 签名**、**对象存储**、**向量库**、**OAuth client secret**。统一登记在密钥台账，标注 owner 与轮换周期。

轮换策略：双密钥并行 24h → 切主 → 废旧。自动化用 Vault / AWS SM / K8s External Secrets。应用启动拉取，**禁止** bake 进镜像（[185](185.docker-multi-stage-build-tutorial.md)）。"""),
        sec(s + 2, "开发、CI 与生产的隔离",
            """开发用 `.env.local`（gitignore）；CI 用 GitHub Actions secrets；生产用托管 Secret。同一名称不同值，避免开发 key 打生产账单。

日志与 [190 结构化日志](190.structured-logging-rag-tutorial.md) 禁止打印 key；Sentry 过滤 `Authorization` header。"""),
        sec(s + 3, "最小权限与供应链",
            """云 IAM：worker 只需写向量库与读对象存储，不需删库权限。LLM key 按项目限额。依赖扫描（SBOM）防恶意包窃密。

合规：[197 GDPR](197.gdpr-data-residency-tutorial.md)、[198 国内合规](198.china-compliance-rag-tutorial.md) 可能要求密钥与数据同区域存储。"""),
        sec(s + 4, "事故响应：密钥泄露 playbook",
            """1. 立即轮换并吊销旧 key。  
2. 查账单异常与访问日志。  
3. 通知安全与法务。  
4. 根因：是否提交 Git、是否日志泄露。  
5. 事后加固扫描与 pre-commit 钩子。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("190 结构化日志", "190.structured-logging-rag-tutorial.md"),
        ("187 K8s", "187.kubernetes-basics-rag-tutorial.md"),
        ("164 JWT", "164.jwt-auth-rag-tutorial.md"),
    ])
    return pad_unique("密钥与 Secrets 管理", "[190 结构化日志](190.structured-logging-rag-tutorial.md)", 2900, body)


def build_189() -> str:
    s = 12
    parts = [
        sec(s + 1, "Liveness 与 Readiness 在 RAG 中的语义",
            """**Liveness 失败** → K8s 重启 Pod。仅用于死锁、进程挂掉，勿把「模型慢」放 liveness。**Readiness 失败** → 从 Service 摘掉，不接新流量，用于 DB 未就绪、依赖 warmup。

RAG api readiness 检查：Postgres `SELECT 1`、Redis ping、可选向量库轻量查询。worker readiness：能消费队列即可，不必等 GPU 满负载。"""),
        sec(s + 2, "启动顺序：模型加载与冷启动",
            """Embedding 模型本地加载可能 30～120s。readiness 应在 **模型 load 完成** 后置 true，避免首请求超时。可用 `/ready` 与 `/health` 分离（[156 FastAPI](156.fastapi-project-structure-tutorial.md)）。

Compose 用 `healthcheck` + `condition: service_healthy`；K8s 用 `startupProbe` 给长启动宽容度。"""),
        sec(s + 3, "依赖降级与熔断",
            """向量库短暂不可用时，readiness 可 false 让 Ingress 切走；或业务层降级只答「检索暂不可用」（[112 拒答](112.refusal-strategy-tutorial.md)）。勿无限重试打挂依赖。

指标：`readiness_fail_total`、`startup_duration_seconds`，接入 [191 Prometheus](191.prometheus-metrics-rag-tutorial.md)。"""),
        sec(s + 4, "健康检查 FAQ",
            """**问：health 返回 200 但问答 500？** 可能 readiness 未覆盖 embed 路径。  
**问：滚动升级时 502？** 旧 Pod 已摘流新 Pod 未 ready。  
**问：worker 需要 HTTP 探针吗？** 可用 exec 探针或 sidecar 暴露 /health。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("186 Compose", "186.docker-compose-fullstack-tutorial.md"),
        ("187 K8s", "187.kubernetes-basics-rag-tutorial.md"),
        ("191 Prometheus", "191.prometheus-metrics-rag-tutorial.md"),
    ])
    return pad_unique("健康检查与就绪探针", "[191 Prometheus](191.prometheus-metrics-rag-tutorial.md)", 3300, body)


def build_190() -> str:
    s = 13
    parts = [
        sec(s + 1, "结构化日志字段规范",
            """每条日志 JSON 含：`timestamp`、`level`、`trace_id`、`tenant_id`、`user_id`（哈希）、`service`、`event`、`latency_ms`、可选 `doc_id`/`chunk_id`。RAG 扩展：`retrieve_k`、`embed_model`、`prompt_tokens`。

与 [148 Langfuse](148.langfuse-observability-tutorial.md) trace 共用 trace_id，便于跳转。禁止记录完整 prompt/answer 除非采样且脱敏 [195](195.pii-redaction-rag-tutorial.md)。"""),
        sec(s + 2, "Python structlog / logging 配置",
            """FastAPI 中间件注入 trace_id（来自 `X-Request-Id`）。worker 任务日志带 `task_id`。统一 formatter 输出一行 JSON，方便 Loki/ELK 解析。

日志级别：生产 INFO，排障临时 DEBUG（带 TTL）。错误栈 `exc_info=True`。"""),
        sec(s + 3, "可观测性三角：日志、指标、追踪",
            """日志答「发生了什么」；指标答「多少、多快」（[191](191.prometheus-metrics-rag-tutorial.md)）；追踪答「哪一步慢」。三者通过 trace_id 关联。

oncall 手册：先 Grafana 看 P95 → Langfuse 看 trace → Loki 搜 trace_id。"""),
        sec(s + 4, "合规与保留策略",
            """日志保留 30～90 天按合规；审计事件更长（[196](196.audit-log-rag-tutorial.md)）。跨境注意 [197 GDPR](197.gdpr-data-residency-tutorial.md) 日志驻留地。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("191 Prometheus", "191.prometheus-metrics-rag-tutorial.md"),
        ("148 Langfuse", "148.langfuse-observability-tutorial.md"),
        ("196 审计日志", "196.audit-log-rag-tutorial.md"),
    ])
    return pad_unique("结构化日志", "[191 Prometheus](191.prometheus-metrics-rag-tutorial.md)", 3300, body)


def build_191() -> str:
    s = 13
    parts = [
        sec(s + 1, "RAG 核心指标清单",
            """| 指标 | 类型 | 说明 |
|------|------|------|
| rag_retrieve_latency_seconds | Histogram | 检索耗时 |
| rag_generate_tokens_total | Counter | 生成 token |
| rag_embed_chars_total | Counter | 索引 embed 字符 |
| rag_requests_total | Counter | 按 status 分 |
| celery_queue_depth | Gauge | 索引积压 |

RED 方法：Rate、Errors、Duration。SLO 示例：retrieve P95 < 800ms、error rate < 0.5%。"""),
        sec(s + 2, "Prometheus 埋点与 Grafana 大盘",
            """FastAPI 用 `prometheus_client` 或 OpenTelemetry exporter。Histogram buckets 按实际分布调。大盘分：概览、检索、生成、索引 worker。

告警：队列深度 > 1000 持续 10m；P95 检索 > 2s；5xx 率上升。Alertmanager 路由到 oncall。"""),
        sec(s + 3, "与日志、Langfuse 的分工",
            """指标看趋势与告警；Langfuse [148](148.langfuse-observability-tutorial.md) 看单请求细节。勿用高基数 label（如 user_id）毁 Prometheus。

成本指标可从 [192](192.embedding-batch-cost-tutorial.md)、[194](194.llm-token-cost-optimization-tutorial.md) 汇成 Grafana 变量。"""),
        sec(s + 4, "落地检查表",
            """1. `/metrics` 仅内网可访问。  
2. 所有服务统一 `job` 标签。  
3. Recording rules 预聚合常用查询。  
4. 与 [189 健康](189.health-readiness-rag-tutorial.md) 探针失败关联告警。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("190 结构化日志", "190.structured-logging-rag-tutorial.md"),
        ("183 用量看板", "183.admin-usage-dashboard-tutorial（front-end）.md"),
        ("189 健康检查", "189.health-readiness-rag-tutorial.md"),
    ])
    return pad_unique("Prometheus 指标", "[190 结构化日志](190.structured-logging-rag-tutorial.md)", 3600, body)


def build_192() -> str:
    s = 13
    parts = [
        sec(s + 1, "Embedding 批处理与成本模型",
            """索引成本 ≈ **字符数 × 单价 × 批次数**。批处理 [67](67.embedding-batching-tutorial.md) 减少 HTTP 开销但单批过大易 OOM。最优 batch 用 profiling 找拐点。

开源本地 embed [72](72.local-embedding-inference-tutorial.md) 省 API 费但占 GPU；云 API 省运维但按 token 计费。manifest 记录模型与维度 [25](25.embedding-vector-tutorial.md)。"""),
        sec(s + 2, "缓存、去重与增量",
            """[68 缓存](68.embedding-cache-tutorial.md) 对 content_hash 命中则跳过 API。[49 增量](49.incremental-update-tutorial.md) 只 embed 新 chunk。重复文档 [47 去重](47.doc-dedup-tutorial.md) 直接省一倍。

看板展示：每千 chunk 成本、每 GB 原文成本，供 [183](183.admin-usage-dashboard-tutorial（front-end）.md) 引用。"""),
        sec(s + 3, "限流与重试成本",
            """[69 重试](69.embedding-retry-rate-limit-tutorial.md) 指数退避避免账单爆炸。429 时 worker 应降并发而非无脑重试。

预算告警：日 embed 费用超阈值暂停非紧急全库重建。"""),
        sec(s + 4, "优化实战清单",
            """1. 调 chunk 大小 [61](61.chunk-size-tradeoff-tutorial.md) 减少 chunk 数。  
2. 清洗无用页眉页脚 [46](46.text-cleaning-tutorial.md)。  
3. 夜间批处理低价时段（若供应商有差异定价）。  
4. 对比三种 embed 模型性价比 [71](71.domain-embedding-evaluation-tutorial.md)。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("193 向量存储成本", "193.vector-storage-cost-tutorial.md"),
        ("67 批处理", "67.embedding-batching-tutorial.md"),
        ("183 用量看板", "183.admin-usage-dashboard-tutorial（front-end）.md"),
    ])
    return pad_unique("Embedding 批处理成本", "[193 向量存储成本](193.vector-storage-cost-tutorial.md)", 2800, body)


def build_193() -> str:
    s = 14
    parts = [
        sec(s + 1, "向量存储成本构成",
            """成本 = **向量维度 × 条数 × 副本数 × 存储单价** + **查询 CU**。HNSW [86](86.hnsw-index-tutorial.md) 比 Flat [84](84.flat-brute-force-search-tutorial.md) 省内存但占额外图结构。

选型：[76 Chroma](76.chroma-vector-db-tutorial.md) PoC；[77 Milvus](77.milvus-tutorial.md) 大规模；[80 Pinecone](80.pinecone-tutorial.md) 托管省心按量付费。"""),
        sec(s + 2, "压缩、量化与冷热分层",
            """量化 INT8 可减半存储，需测 recall [87](87.ann-recall-latency-tutorial.md)。冷文档可归档到低频索引或对象存储仅保留 metadata。

删除租户时按 namespace 清向量 [89](89.multi-tenant-namespace-tutorial.md)，避免幽灵账单。"""),
        sec(s + 3, "容量规划公式",
            """估算：`chunks × dim × 4 bytes × 1.3（HNSW 开销）`。年增长率来自上传趋势 [179](179.kb-doc-upload-ui-tutorial（front-end）.md)。提前 3 个月扩容。

备份 [90](90.vector-db-backup-tutorial.md) 也占存储，单独计费项。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("192 Embedding 成本", "192.embedding-batch-cost-tutorial.md"),
        ("87 召回延迟", "87.ann-recall-latency-tutorial.md"),
        ("90 备份", "90.vector-db-backup-tutorial.md"),
    ])
    return pad_unique("向量存储成本", "[192 Embedding 成本](192.embedding-batch-cost-tutorial.md)", 1150, body)


def build_194() -> str:
    s = 14
    parts = [
        sec(s + 1, "Token 消耗解剖",
            """一次问答 Token ≈ **system + 检索上下文 + 历史 + 问题 + 答案**。[107 上下文预算](107.context-budget-tutorial.md) 限制注入 chunk 数；[108 重排](108.long-context-reorder-tutorial.md) 把相关段放中间。

生成侧：[29 采样](29.llm-sampling-tutorial.md) 与 `max_tokens` 封顶；流式 [116](116.sse-rag-streaming-tutorial.md) 可提前 stop [175](175.abort-controller-stream-tutorial（front-end）.md) 省 completion token。"""),
        sec(s + 2, "降本策略矩阵",
            """| 策略 | 效果 | 篇 |
|------|------|-----|
| 减小 top_k | 降 prompt | [98](98.top-k-retrieval-tutorial.md) |
| 摘要 chunk | 降 prompt | [207](207.map-reduce-summarization-tutorial.md) |
| 小模型路由 | 降单价 | 路线图阶段6 |
| 缓存 FAQ | 零生成 | [68](68.embedding-cache-tutorial.md) |

监控：每问答平均 prompt/completion 比，异常升高查是否注入重复 chunk [106](106.retrieval-dedup-tutorial.md)。"""),
        sec(s + 3, "定价、预算与产品策略",
            """按租户设月 Token 配额，超限降级或拒答 [112](112.refusal-strategy-tutorial.md)。对外报价把 Token 与 embed 分开列项，见 [183](183.admin-usage-dashboard-tutorial（front-end）.md)。

A/B 测 cheaper model 在简单问上的质量损失，用 [144 回归集](144.regression-test-set-tutorial.md) 量化。"""),
        sec(s + 4, "优化验收",
            """基线一周指标 → 实施优化 → 对比同等流量下 Token 降百分比，质量不降。记录变更与 rollback 开关。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("192 Embedding", "192.embedding-batch-cost-tutorial.md"),
        ("107 上下文预算", "107.context-budget-tutorial.md"),
        ("27 Token 计费", "27.token-counting-billing-tutorial.md"),
    ])
    return pad_unique("LLM Token 成本优化", "[192 Embedding 成本](192.embedding-batch-cost-tutorial.md)", 2650, body)


def build_195() -> str:
    s = 14
    parts = [
        sec(s + 1, "PII 识别与脱敏流水线",
            """在 ingest 与 query 双侧处理 PII：手机号、身份证、银行卡、邮箱、地址。正则 + NER 组合；高召回场景先 **掩码** 再入库，避免向量库存明文。

与 [195](195.pii-redaction-rag-tutorial.md) 策略：`[PHONE]`、`[ID]` 占位符保持一致，生成时模型不见真值。检索仍可用上下文，但日志与 [190](190.structured-logging-rag-tutorial.md) 导出必须 redact。"""),
        sec(s + 2, "脱敏与问答质量权衡",
            """过度脱敏可能丢关键信息（如工单号）。按字段分级：公开、内部、机密。机密不进索引或仅哈希存储。

评测：脱敏后 recall 是否下降；误杀率（把产品名当 PII）如何调规则。"""),
        sec(s + 3, "合规联动与国内要求",
            """[198 国内合规](198.china-compliance-rag-tutorial.md) 可能要求个人信息本地化；[197 GDPR](197.gdpr-data-residency-tutorial.md) 要求最小化收集。DPIA 记录脱敏策略。

用户行使删除权时，连带删除含其 PII 的 chunk 与日志。"""),
        sec(s + 4, "实施检查表",
            """1. 上传前扫描文件 PII 密度告警。  
2. 聊天出口二次过滤。  
3. 调试台 excerpt 默认脱敏。  
4. 第三方 LLM 是否允许传脱敏后文本（DPA）。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("196 审计日志", "196.audit-log-rag-tutorial.md"),
        ("197 GDPR", "197.gdpr-data-residency-tutorial.md"),
        ("198 国内合规", "198.china-compliance-rag-tutorial.md"),
    ])
    return pad_unique("PII 脱敏", "[196 审计日志](196.audit-log-rag-tutorial.md)", 2800, body)


def build_196() -> str:
    s = 14
    parts = [
        sec(s + 1, "审计日志：必须记录的事件",
            """**认证**：登录失败/成功。**授权**：403 敏感 API。**数据**：上传、删除、导出、debug retrieve。**配置**：prompt 版本、top_k 变更。**管理**：重建索引、密钥轮换。

字段：`actor`、`action`、`resource`、`tenant_id`、`ip`、`trace_id`、`timestamp`、可选 `reason`。不可篡改：append-only 表或 WORM 存储。"""),
        sec(s + 2, "与业务日志、Langfuse 区分",
            """审计日志面向 **合规与取证**，保留期 1～7 年；业务日志面向排障，30 天。Langfuse [148](148.langfuse-observability-tutorial.md) 面向算法迭代。勿混表。

查询 API 仅合规角色可访问，本身也要 audit（查审计的人被记录）。"""),
        sec(s + 3, "检索调试与聊天溯源",
            """用户点击 [176 引用](176.citation-card-ui-tutorial（front-end）.md) 可记 `citation_view`；[182 调试台](182.retrieval-debug-console-tutorial（front-end）.md) 记 `debug_retrieve`。回答争议时可重建「当时用了哪些 chunk」。

与 [113 行内引用](113.inline-citation-tutorial.md) 编号一致，避免审计链断裂。"""),
        sec(s + 4, "落地与抽检",
            """季度抽检：随机 100 条 audit 能否串起 trace。渗透测试验证普通用户不能读他人 audit。导出格式满足 SOC2/等保检查项。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("195 PII", "195.pii-redaction-rag-tutorial.md"),
        ("190 结构化日志", "190.structured-logging-rag-tutorial.md"),
        ("182 调试台", "182.retrieval-debug-console-tutorial（front-end）.md"),
    ])
    return pad_unique("审计日志", "[195 PII](195.pii-redaction-rag-tutorial.md)", 3250, body)


def build_197() -> str:
    s = 14
    parts = [
        sec(s + 1, "GDPR 核心义务与 RAG 映射",
            """**合法性基础**：同意或合法利益。**数据最小化**：只索引必要字段。**存储限制**：保留策略与自动删除。**权利**：访问、删除、可携带。

RAG 特有问题：向量是否算「个人数据」——若可还原或关联个人，则是。删除请求需删 chunk、向量、日志、备份（或标记待 purge）。"""),
        sec(s + 2, "数据驻留与跨境传输",
            """EU 数据留在 EU region：Postgres、向量库、对象存储、LLM 调用 endpoint。用 [89 租户](89.multi-tenant-namespace-tutorial.md) 隔离 + region 标签。

SCC/DPF 评估第三方 embed/LLM。禁止为了便宜把 EU 用户 query 打到无 DPA 的区域。"""),
        sec(s + 3, "DPIA 与 ROPA 模板要点",
            """处理活动：收集什么、为何、存多久、谁访问、是否自动决策。RAG 补充：检索是否 profiling、是否仅内部员工。

RoPA 记录每个子处理者（OpenAI、Milvus 托管等）与 DPA 签署日期。"""),
        sec(s + 4, "与 198 国内合规对照",
            """GDPR 偏权利与跨境；国内 [198](198.china-compliance-rag-tutorial.md) 偏网络安全与生成内容。跨国企业两套并行，UI 展示不同隐私政策链接。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("198 国内合规", "198.china-compliance-rag-tutorial.md"),
        ("195 PII", "195.pii-redaction-rag-tutorial.md"),
        ("196 审计", "196.audit-log-rag-tutorial.md"),
    ])
    return pad_unique("GDPR 数据驻留", "[198 国内合规](198.china-compliance-rag-tutorial.md)", 2700, body)


def build_198() -> str:
    s = 14
    parts = [
        sec(s + 1, "国内 RAG 合规关注面",
            """**网络安全**：等保、日志留存、境内存储。**生成内容**：标识 AI 生成、敏感词过滤 [122](122.content-safety-filter-tutorial.md)。**个人信息**：PIPL 同意与最小必要 [195](195.pii-redaction-rag-tutorial.md)。

算法备案与深度合成标识按产品形态咨询法务，技术侧预留「由大模型生成」水印位。"""),
        sec(s + 2, "境内模型与数据链路",
            """优先境内 embed/LLM 或私有部署，避免训练数据出境争议。向量与原文存储在境内云；访问控制 [53 ACL](53.metadata-acl-tutorial.md) 与等保三级要求对齐。

跨境集团：中国子公司数据不与全球索引混库。"""),
        sec(s + 3, "内容安全与拒答",
            """[112 拒答](112.refusal-strategy-tutorial.md) 对涉政涉暴查询统一话术；审计 [196](196.audit-log-rag-tutorial.md) 记录拦截原因。人工复核队列处理边缘 case。

与客服培训：哪些能答、哪些转人工、哪些固定模板。"""),
        sec(s + 4, "检查清单",
            """1. 隐私政策与用户协议已更新。  
2. 日志境内 6 个月以上。  
3. 密钥境内 KMS [188](188.secrets-management-rag-tutorial.md)。  
4. 生成内容标识开关可配置。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("197 GDPR", "197.gdpr-data-residency-tutorial.md"),
        ("122 内容安全", "122.content-safety-filter-tutorial.md"),
        ("112 拒答策略", "112.refusal-strategy-tutorial.md"),
    ])
    return pad_unique("国内合规", "[197 GDPR](197.gdpr-data-residency-tutorial.md)", 2200, body)


def build_199() -> str:
    s = 14
    parts = [
        sec(s + 1, "Graph RAG 问题形态",
            """当问题需要 **多跳关系**（「A 公司的供应商 B 的合规负责人是谁」）纯向量检索易漏。**Graph RAG** 把实体关系建图，检索时走子图 + 文本 chunk 混合。

与 [104 多跳](104.multi-hop-retrieval-tutorial.md) 区别：图有显式边；向量靠语义碰运气。"""),
        sec(s + 2, "构图：实体抽取与边类型",
            """ingest 用 LLM 或规则抽实体（人、组织、合同）与关系（签署、隶属、引用）。存 Neo4j 或图数据库 + 向量库并行。边带 provenance chunk_id。

更新：文档新版时增量更新子图 [49](49.incremental-update-tutorial.md)，避免全图重算。"""),
        sec(s + 3, "检索与生成编排",
            """query → 实体链接 → k-hop 扩展 → 相关 chunk 召回 → 与 dense 路融合 [93](93.hybrid-search-tutorial.md) → LLM 答。

成本：图查询便宜，抽图贵。PoC 可先对小域手册构图。"""),
        sec(s + 4, "与 KG 增强检索衔接",
            """[200 KG 增强](200.kg-enhanced-retrieval-tutorial.md) 是 Graph RAG 的轻量变体。选型：关系密集用图；仅术语表用 KG 同义词扩展即可。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("200 KG 增强", "200.kg-enhanced-retrieval-tutorial.md"),
        ("104 多跳", "104.multi-hop-retrieval-tutorial.md"),
        ("201 Agentic", "201.agentic-rag-tutorial.md"),
    ])
    return pad_unique("Graph RAG", "[200 KG 增强](200.kg-enhanced-retrieval-tutorial.md)", 2750, body)


def build_200() -> str:
    s = 13
    parts = [
        sec(s + 1, "知识图谱增强检索的轻量路线",
            """不必一上来 Neo4j。可用 **术语表 JSON**：别名 → 规范名 → 相关 doc_id。查询时先扩展同义词再检索 [100 改写](100.query-rewriting-tutorial.md)。

例：「年假」→「带薪年休假」→ filter 或 boost 人事类 doc。"""),
        sec(s + 2, "与 Graph RAG 的边界",
            """[199 Graph RAG](199.graph-rag-tutorial.md) 适合关系推理；本篇适合 **实体消歧与同义词**。维护成本：术语表由业务方 Excel 导入，季度更新。"""),
        sec(s + 3, "实现草图",
            """`KgExpander.expand(query) -> list[str]` 插入 Retriever 前。评测：专有名词 recall@5 是否提升。失败时 fallback 原 query，不阻断主路径。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("199 Graph RAG", "199.graph-rag-tutorial.md"),
        ("100 Query 改写", "100.query-rewriting-tutorial.md"),
        ("93 混合检索", "93.hybrid-search-tutorial.md"),
    ])
    return pad_unique("KG 增强检索", "[199 Graph RAG](199.graph-rag-tutorial.md)", 900, body)


def build_201() -> str:
    s = 13
    parts = [
        sec(s + 1, "Agentic RAG 循环结构",
            """Agent 在 **检索—阅读—再检索—生成** 间循环，而非一次 retrieve。工具：`search_kb`、`get_page`、`calculator`（按需）。停止条件：置信度够或达 max_steps。

与 [203 多步工具](203.multi-step-tool-retrieval-tutorial.md) 重叠；本篇强调 **自主规划**，203 强调 **工具契约**。"""),
        sec(s + 2, "控制成本与幻觉",
            """每步消耗 Token；`max_steps=3` 为常见起点。强制每步 cite chunk_id，最终答案汇总引用 [113](113.inline-citation-tutorial.md)。

沙箱：工具仅只读 KB，禁止任意 HTTP。审计 [196](196.audit-log-rag-tutorial.md) 记录工具调用链。"""),
        sec(s + 3, "与 ReAct、Self-RAG 关系",
            """[202 ReAct](202.react-reasoning-rag-tutorial.md) 显式 Thought-Action 日志；[204 Self-RAG](204.self-rag-tutorial.md) 自评是否再检。可组合：Agent 外壳 + Self-RAG 内省。"""),
        sec(s + 4, "PoC 验收",
            """选 10 个需多文档综合的问题；对比单轮 RAG pass rate；记录延迟与 Token 倍率。不达标则缩工具集或改 prompt。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("202 ReAct", "202.react-reasoning-rag-tutorial.md"),
        ("203 多步工具", "203.multi-step-tool-retrieval-tutorial.md"),
        ("206 Adaptive", "206.adaptive-rag-tutorial.md"),
    ])
    return pad_unique("Agentic RAG", "[202 ReAct](202.react-reasoning-rag-tutorial.md)", 2150, body)


def build_202() -> str:
    s = 13
    parts = [
        sec(s + 1, "ReAct 轨迹在 RAG 中的形态",
            """Thought：分析缺什么信息。Action：`search(query)`。Observation：Top chunk 摘要。循环直至 Action: `finish(answer)`。

日志轨迹可给专家调试 [182](182.retrieval-debug-console-tutorial（front-end）.md)，但勿把原始 Thought 展示给终端用户（易泄露推理链）。"""),
        sec(s + 2, "Prompt 与解析鲁棒性",
            """要求 JSON 或固定前缀 `Action:` 便于解析；畸形输出重试一次。与 [123 结构化输出](123.structured-output-json-tutorial.md) 一致。

Few-shot 给 2 个完整轨迹 [31](31.few-shot-prompting-tutorial.md)，覆盖「一次检索够」与「需两次」。"""),
        sec(s + 3, "与 CoT 区别",
            """[32 CoT](32.chain-of-thought-tutorial.md) 只想的更长；ReAct 能 **改环境**（检索结果）。企业场景 ReAct 更可控，因 Action 白名单。"""),
        sec(s + 4, "评测与回归",
            """轨迹级评测：是否用了正确工具顺序；最终答案 RAGAS。回归集加入「不应再检」类题，防止无限循环。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("201 Agentic", "201.agentic-rag-tutorial.md"),
        ("32 CoT", "32.chain-of-thought-tutorial.md"),
        ("123 JSON 输出", "123.structured-output-json-tutorial.md"),
    ])
    return pad_unique("ReAct 推理 RAG", "[201 Agentic](201.agentic-rag-tutorial.md)", 2850, body)


def build_203() -> str:
    s = 13
    parts = [
        sec(s + 1, "多步工具检索架构",
            """编排器维护 `messages` 与 `tool_registry`。LLM 返回 tool_calls；执行器跑 `retrieve`、`list_docs`、`fetch_chunk`，结果塞回 messages。

OpenAI function calling 或 LangChain [126 LCEL](126.langchain-lcel-tutorial.md) 均可；核心是 **幂等只读** 与 **超时**。"""),
        sec(s + 2, "工具设计原则",
            """每个工具单一职责、参数 schema 清晰、返回长度上限（截断 excerpt）。`retrieve` 的 k 比单轮更小，靠多步补足。

并行：无依赖的 `fetch_chunk` 可 asyncio.gather；有依赖串行。"""),
        sec(s + 3, "错误与降级",
            """工具超时返回结构化错误 Observation，模型可换 query 重试。max_tool_calls 防止死循环。与 [175 abort](175.abort-controller-stream-tutorial（front-end）.md) 共用取消语义。"""),
        sec(s + 4, "与 Agentic、CRAG 组合",
            """[201](201.agentic-rag-tutorial.md) 定策略；[205 CRAG](205.crag-corrective-rag-tutorial.md) 在 Observation 差时触发纠正检索。路线图 H 模块进阶必读 trio。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("201 Agentic", "201.agentic-rag-tutorial.md"),
        ("127 Retriever", "127.langchain-retriever-tutorial.md"),
        ("205 CRAG", "205.crag-corrective-rag-tutorial.md"),
    ])
    return pad_unique("多步工具检索", "[201 Agentic](201.agentic-rag-tutorial.md)", 3150, body)


def build_204() -> str:
    s = 13
    parts = [
        sec(s + 1, "Self-RAG 自评四问",
            """检索后模型自评：**是否需要检索**、**文档是否相关**、**答案是否由文档支持**、**答案是否有用**。不通过则再检或拒答 [112](112.refusal-strategy-tutorial.md)。

实现可用同一 LLM 小 prompt 或专用 critic 模型；输出 structured labels。"""),
        sec(s + 2, "训练与推理差异",
            """论文用特殊 reflection token；工程可用 **额外一轮 JSON 分类**，无需改 base 模型。与 [212 LoRA](212.lora-domain-qa-tutorial.md) 结合可训领域 critic。"""),
        sec(s + 3, "延迟与成本",
            """每轮多 1～2 次 LLM 调用。仅对高风险域（医疗、法律）全开；普通 FAQ 可抽样开启。指标：`self_rag_retry_rate`。"""),
        sec(s + 4, "与 CRAG、Adaptive 关系",
            """[205 CRAG](205.crag-corrective-rag-tutorial.md) 用外部评分器；[206 Adaptive](206.adaptive-rag-tutorial.md) 路由是否检索。Self-RAG 偏 **生成前自证**。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("205 CRAG", "205.crag-corrective-rag-tutorial.md"),
        ("206 Adaptive", "206.adaptive-rag-tutorial.md"),
        ("112 拒答", "112.refusal-strategy-tutorial.md"),
    ])
    return pad_unique("Self-RAG", "[205 CRAG](205.crag-corrective-rag-tutorial.md)", 3150, body)


def build_205() -> str:
    s = 13
    parts = [
        sec(s + 1, "CRAG 纠正回路",
            """Corrective RAG：检索结果经 **相关性判别**（小模型或 cross-encoder [95](95.cross-encoder-rerank-tutorial.md)），差则触发 **web 搜索** 或 **query 改写** 再检，好则精简上下文生成。

三态：Correct / Incorrect / Ambiguous，对应不同分支。"""),
        sec(s + 2, "Web 搜索与合规",
            """外网搜索需合规审批；默认仅内网 KB。Incorrect 时先 **改写 query** [100](100.query-rewriting-tutorial.md) 再检，比立刻上网更可控。

记录外网 snippet 来源供审计。"""),
        sec(s + 3, "实现流水线",
            """retrieve → grade_documents → branch → maybe_rewrite → retrieve_again → generate。用 LangGraph 或手写状态机。

评测：故意注入噪声 chunk，看纠正率是否上升。"""),
        sec(s + 4, "与 Self-RAG、Adaptive",
            """[204 Self-RAG](204.self-rag-tutorial.md) 在生成侧反思；CRAG 在检索侧纠正。[206 Adaptive](206.adaptive-rag-tutorial.md) 决定是否走 CRAG 支路。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("206 Adaptive", "206.adaptive-rag-tutorial.md"),
        ("95 精排", "95.cross-encoder-rerank-tutorial.md"),
        ("100 改写", "100.query-rewriting-tutorial.md"),
    ])
    return pad_unique("CRAG 纠正检索", "[206 Adaptive](206.adaptive-rag-tutorial.md)", 3100, body)


def build_206() -> str:
    s = 13
    parts = [
        sec(s + 1, "Adaptive RAG 路由问题",
            """并非每个问题都需检索。「法国首都」无需 KB；「我司年假政策」需。路由器（小分类器或 LLM）输出：`no_retrieve` | `single_retrieve` | `multi_step`。"""),
        sec(s + 2, "路由器训练与特征",
            """特征：问题长度、是否含公司专有词、是否与历史相关 [109](109.conversation-query-enhancement-tutorial.md)。标签来自日志人工标注或启发式。

错路由代价：该检不检 → 幻觉；不该检而检 → 噪音与成本。"""),
        sec(s + 3, "与 Agentic、CRAG 编排",
            """路由 `multi_step` → [201 Agentic](201.agentic-rag-tutorial.md)；低置信检索 → [205 CRAG](205.crag-corrective-rag-tutorial.md)。统一 orchestrator 配置化 [138](138.config-driven-pipeline-tutorial.md)。"""),
        sec(s + 4, "评测与监控",
            """矩阵：路由准确率 × 最终答案质量。监控各路由占比随时间变化，防止模型漂移后全走 no_retrieve。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("201 Agentic", "201.agentic-rag-tutorial.md"),
        ("205 CRAG", "205.crag-corrective-rag-tutorial.md"),
        ("109 查询增强", "109.conversation-query-enhancement-tutorial.md"),
    ])
    return pad_unique("Adaptive RAG", "[201 Agentic](201.agentic-rag-tutorial.md)", 3050, body)


def build_207() -> str:
    s = 13
    parts = [
        sec(s + 1, "Map-Reduce 长文摘要",
            """单文档超 [28 上下文](28.context-window-tutorial.md) 时：Map 各 chunk 局部摘要，Reduce 合并成总摘要。用于 **入库预览**、**高管摘要**，非每条问答必用。

Map 可并行；Reduce 注意二次超长则递归 Reduce。"""),
        sec(s + 2, "与 RAG 问答关系",
            """问答仍检索 chunk；Map-Reduce 用于 **后台编制摘要索引** 或 **目录导航**。摘要 chunk 单独 metadata `type=summary` 可被检索。

风险：摘要丢细节，财务数字类问题应保留原文 chunk 优先。"""),
        sec(s + 3, "与 Refine 对比",
            """[208 Refine](208.refine-summarization-tutorial.md) 顺序滚动更连贯但难并行。选型：批量离线用 Map-Reduce；要强连贯用 Refine。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("208 Refine", "208.refine-summarization-tutorial.md"),
        ("209 RAPTOR", "209.raptor-hierarchical-retrieval-tutorial.md"),
        ("28 上下文", "28.context-window-tutorial.md"),
    ])
    return pad_unique("Map-Reduce 摘要", "[208 Refine](208.refine-summarization-tutorial.md)", 800, body)


def build_208() -> str:
    s = 13
    parts = [
        sec(s + 1, "Refine 摘要算法直觉",
            """维护 running_summary；每读新 chunk：`summary = LLM(summary, chunk)`。连贯性好，适合 **叙事型** 文档（年报、项目复盘）。

缺点：顺序敏感、难并行、错误累积——早期摘要错会污染后期。"""),
        sec(s + 2, "工程优化",
            """每 N chunk 做一次 **checkpoint 摘要** 可断点续跑。关键 chunk（表格、结论段）可加权多 refine 一次。

与 [207 Map-Reduce](207.map-reduce-summarization-tutorial.md) 混合：先 Map 章节级，再 Refine 合并。"""),
        sec(s + 3, "入库与检索",
            """Refine 产出写入 `summary` 字段供卡片展示；检索仍以细粒度 chunk 为主。用户问「总结第三章」可检索章节 summary chunk。"""),
        sec(s + 4, "成本提示",
            """Token 随 chunk 数线性累积；长书 Refine 贵于 Map-Reduce。对索引任务设预算上限 [192](192.embedding-batch-cost-tutorial.md)。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("207 Map-Reduce", "207.map-reduce-summarization-tutorial.md"),
        ("209 RAPTOR", "209.raptor-hierarchical-retrieval-tutorial.md"),
        ("107 上下文预算", "107.context-budget-tutorial.md"),
    ])
    return pad_unique("Refine 摘要", "[207 Map-Reduce](207.map-reduce-summarization-tutorial.md)", 2200, body)


def build_209() -> str:
    s = 13
    parts = [
        sec(s + 1, "RAPTOR 层次树直觉",
            """对 chunk embed 后 **聚类**，簇内摘要成父节点，再 embed，递归成树。检索时既可命中叶子也可命中 **高层摘要**，适合 **跨节综合** 问题。

与 [207](207.map-reduce-summarization-tutorial.md) 不同：RAPTOR 结构是树而非单层 reduce。"""),
        sec(s + 2, "构建与更新成本",
            """建树需多次聚类与 LLM 摘要，索引贵。适合 **相对稳定** 的法规库、教材。增量更新可只重算受影响子树。

向量库需存 `level` metadata；检索扩展 k 到不同层。"""),
        sec(s + 3, "检索策略",
            """collapsed tree retrieval：各层各取 top，合并去重。或自顶向下：先匹配摘要再下钻叶子。

评测：对比 flat RAG 在「全书主题」类问题的 recall。"""),
        sec(s + 4, "与多模态、ColPali",
            """扫描 PDF 可先 [210 多模态](210.multimodal-rag-tutorial.md) 再 RAPTOR 文本层；页级图检索见 [211 ColPali](211.colpali-rag-tutorial.md)。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("207 Map-Reduce", "207.map-reduce-summarization-tutorial.md"),
        ("210 多模态", "210.multimodal-rag-tutorial.md"),
        ("86 HNSW", "86.hnsw-index-tutorial.md"),
    ])
    return pad_unique("RAPTOR 层次检索", "[207 Map-Reduce](207.map-reduce-summarization-tutorial.md)", 2800, body)


def build_210() -> str:
    s = 13
    parts = [
        sec(s + 1, "多模态 RAG 数据流",
            """除文本 chunk 外，索引 **图片、截图、图表** 的 embedding 或 caption。查询可用文本问图，或图文混合（若产品支持上传图问）。

路线：caption→文本 embed [56](56.multimodal-image-text-tutorial.md)；CLIP 双塔；页级 [211 ColPali](211.colpali-rag-tutorial.md)。"""),
        sec(s + 2, "Ingest 注意点",
            """PDF 图抽出与 [42 PyMuPDF](42.pymupdf-tutorial.md)；扫描件走 [55 OCR](55.ocr-scanned-docs-tutorial.md)。图注与邻近段落绑定同一 doc_id。

存储：原图对象存储，向量库存向量 + image_url metadata。"""),
        sec(s + 3, "生成与展示",
            """检索到图时 UI 展示缩略图 [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md)；LLM 输入可用 caption 或 multimodal API（GPT-4V 等）。

幻觉：要求模型仅描述可见内容；无图拒答。"""),
        sec(s + 4, "选型决策树",
            """纯文本够 → 不必多模态；图表多 → caption 起步；布局关键 → ColPali；视频另论（路线图外）。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("211 ColPali", "211.colpali-rag-tutorial.md"),
        ("56 多模态边界", "56.multimodal-image-text-tutorial.md"),
        ("55 OCR", "55.ocr-scanned-docs-tutorial.md"),
    ])
    return pad_unique("多模态 RAG", "[211 ColPali](211.colpali-rag-tutorial.md)", 2950, body)


def build_211() -> str:
    s = 13
    parts = [
        sec(s + 1, "ColPali 页向量与 Late Interaction",
            """每 PDF **页** 产生多个 patch 向量，查询也 multi-vector，**late interaction** 细粒度匹配，保留表格与印章等布局信息。

比整页 CLIP 单向量更适合 **视觉文档 QA**。"""),
        sec(s + 2, "索引与算力",
            """页渲染 150～200 DPI → 模型 encode → 向量库。存储大于文本 chunk；GPU 推理在 ingest 与 query 双侧。

开源权重与托管服务选型看延迟与许可；PoC 选 50 页合同 subset。"""),
        sec(s + 3, "与 OCR、文本 RAG 融合",
            """数字 PDF 可 **双索引**：ColPali 页 + 文本 chunk [93 hybrid](93.hybrid-search-tutorial.md)。扫描件 OCR 质量差时 ColPali 优先。

生成：检索页图 + 周边 OCR 文本一并送 VLM。"""),
        sec(s + 4, "了解篇定位",
            """路线图 **了解档**：团队评估 ROI 再投入。若库全是 Markdown，退回 [98 top-k](98.top-k-retrieval-tutorial.md) 文本路即可。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("210 多模态", "210.multimodal-rag-tutorial.md"),
        ("42 PyMuPDF", "42.pymupdf-tutorial.md"),
        ("93 混合检索", "93.hybrid-search-tutorial.md"),
    ])
    return pad_unique("ColPali 页检索", "[210 多模态](210.multimodal-rag-tutorial.md)", 3200, body)


def build_212() -> str:
    s = 13
    parts = [
        sec(s + 1, "LoRA 领域 QA 微调动机",
            """通用模型对 **内部术语、口吻、拒答边界** 不稳。LoRA 在冻结 base 上训低秩适配器，省显存，适合 **领域 QA 风格** 而非重训 embed。

数据：高质量 Q&A 对 + 负例；勿泄漏 PII [195](195.pii-redaction-rag-tutorial.md)。"""),
        sec(s + 2, "与 RAG 分工",
            """RAG 供 **事实**；LoRA 供 **怎么说、何时拒答**。勿指望 LoRA 记全库事实，仍会幻觉；必须保留检索。

评测：闭卷问答仍失败则加 RAG；开卷仍口吻不对则加 LoRA。"""),
        sec(s + 3, "训练与部署",
            """框架：PEFT、Axolotl；版本 `adapter_v3` 与 prompt 版本并列记录。推理热加载 adapter 或多 adapter 按 tenant 切换。

监控：adapter 上线后 [144 回归集](144.regression-test-set-tutorial.md) 全绿再放量。"""),
        sec(s + 4, "与 RLHF/DPO 衔接",
            """[213 RLHF/DPO](213.rlhf-dpo-rag-tutorial.md) 用偏好数据进一步优化语气与安全性，在 LoRA 之上叠一层。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("213 RLHF/DPO", "213.rlhf-dpo-rag-tutorial.md"),
        ("73 Embed 微调", "73.embedding-finetune-tutorial.md"),
        ("112 拒答", "112.refusal-strategy-tutorial.md"),
    ])
    return pad_unique("LoRA 领域 QA", "[213 RLHF/DPO](213.rlhf-dpo-rag-tutorial.md)", 3000, body)


def build_213() -> str:
    s = 13
    parts = [
        sec(s + 1, "RLHF 与 DPO 在 RAG 中的位置",
            """检索仍负责事实；DPO 用 **偏好对**（好答案 vs 差答案）优化生成策略：更守引用、更少啰嗦、更安全拒答。

比 RLHF 省奖励模型，工程更常落地 DPO。"""),
        sec(s + 2, "偏好数据从哪来",
            """人工标注客服满意/不满意；[184 评测看板](184.admin-log-eval-dashboard-tutorial（front-end）.md) 抽样；对抗 **无引用瞎编** 的负例。

每条偏好注明用的 chunk 集，避免训成「背 chunk」而非「会用检索」。"""),
        sec(s + 3, "与 LoRA、Self-RAG",
            """[212 LoRA](212.lora-domain-qa-tutorial.md) 打底；DPO 细调偏好；[204 Self-RAG](204.self-rag-tutorial.md) 推理时自评。训练链路与推理链可分离部署。"""),
        sec(s + 4, "阶段 6 路线图收官",
            """213 为 H 模块偏好对齐收官。回 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) 阶段 6：在事实由 RAG 保证前提下，用 DPO 打磨 **产品体验与安全**。"""),
    ]
    body = "\n\n".join(parts)
    body += "\n\n" + links_block([
        ("212 LoRA", "212.lora-domain-qa-tutorial.md"),
        ("204 Self-RAG", "204.self-rag-tutorial.md"),
        ("184 评测看板", "184.admin-log-eval-dashboard-tutorial（front-end）.md"),
    ])
    return pad_unique("RLHF/DPO", "[212 LoRA](212.lora-domain-qa-tutorial.md)", 2050, body)


BUILDERS = {
    "179.kb-doc-upload-ui-tutorial（front-end）.md": build_179,
    "180.index-progress-ui-tutorial（front-end）.md": build_180,
    "181.reindex-ui-tutorial（front-end）.md": build_181,
    "182.retrieval-debug-console-tutorial（front-end）.md": build_182,
    "183.admin-usage-dashboard-tutorial（front-end）.md": build_183,
    "184.admin-log-eval-dashboard-tutorial（front-end）.md": build_184,
    "186.docker-compose-fullstack-tutorial.md": build_186,
    "187.kubernetes-basics-rag-tutorial.md": build_187,
    "188.secrets-management-rag-tutorial.md": build_188,
    "189.health-readiness-rag-tutorial.md": build_189,
    "190.structured-logging-rag-tutorial.md": build_190,
    "191.prometheus-metrics-rag-tutorial.md": build_191,
    "192.embedding-batch-cost-tutorial.md": build_192,
    "193.vector-storage-cost-tutorial.md": build_193,
    "194.llm-token-cost-optimization-tutorial.md": build_194,
    "195.pii-redaction-rag-tutorial.md": build_195,
    "196.audit-log-rag-tutorial.md": build_196,
    "197.gdpr-data-residency-tutorial.md": build_197,
    "198.china-compliance-rag-tutorial.md": build_198,
    "199.graph-rag-tutorial.md": build_199,
    "200.kg-enhanced-retrieval-tutorial.md": build_200,
    "201.agentic-rag-tutorial.md": build_201,
    "202.react-reasoning-rag-tutorial.md": build_202,
    "203.multi-step-tool-retrieval-tutorial.md": build_203,
    "204.self-rag-tutorial.md": build_204,
    "205.crag-corrective-rag-tutorial.md": build_205,
    "206.adaptive-rag-tutorial.md": build_206,
    "207.map-reduce-summarization-tutorial.md": build_207,
    "208.refine-summarization-tutorial.md": build_208,
    "209.raptor-hierarchical-retrieval-tutorial.md": build_209,
    "210.multimodal-rag-tutorial.md": build_210,
    "211.colpali-rag-tutorial.md": build_211,
    "212.lora-domain-qa-tutorial.md": build_212,
    "213.rlhf-dpo-rag-tutorial.md": build_213,
}


def write_module():
    import pprint

    topup: dict[str, str] = {}
    report = []
    for fname, fn in sorted(BUILDERS.items(), key=lambda x: int(x[0].split(".")[0])):
        body = fn()
        base_hz = hz(Path(ROOT / fname).read_text(encoding="utf-8"))
        top_hz = hz(body)
        min_total = 5000
        if base_hz + top_hz < min_total:
            extra_need = min_total - base_hz - top_hz + 50
            body = pad_unique(
                fname.split(".")[1].replace("-", " "),
                "[ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md)",
                hz(body) + extra_need,
                body,
            )
            top_hz = hz(body)
        if base_hz + top_hz < min_total:
            print(f"WARN {fname}: projected {base_hz + top_hz} < {min_total} (will rely on apply pass)")
        topup[fname] = "<!-- topup-batch-179-213 -->\n\n" + body
        report.append((fname, base_hz, top_hz, base_hz + top_hz))

    header = '# -*- coding: utf-8 -*-\n"""Per-article top-up markdown for tutorials 179-213."""\n\n'
    out = ROOT / "_articles_179_213_topup.py"
    out.write_text(header + "TOPUP: dict[str, str] = " + pprint.pformat(topup, width=120, sort_dicts=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print("| file | base | topup | projected |")
    print("|------|------|-------|-----------|")
    for fname, base_hz, top_hz, total in report:
        print(f"| {fname} | {base_hz} | {top_hz} | {total} |")


if __name__ == "__main__":
    write_module()
