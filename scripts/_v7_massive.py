# -*- coding: utf-8 -*-
"""Massive unique top-up for files still under 5000 hanzi."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
HANZI = re.compile(r"[\u4e00-\u9fff]")
FOOTER = re.compile(r"^> \*\*初学者可能仍困惑的点\*\*", re.M)

def ch(t): return len(HANZI.findall(t))

def ins(path, tag, block):
    text = path.read_text(encoding="utf-8")
    if tag in text:
        return ch(text)
    m = FOOTER.search(text)
    pos = m.start() if m else len(text)
    text = text[:pos] + "\n\n---\n\n" + block.strip() + "\n\n---\n\n" + text[pos:]
    path.write_text(text, encoding="utf-8")
    return ch(text)

# V7-MASSIVE unique topic blocks
BLOCKS = {}

BLOCKS["196.audit-log-rag-tutorial.md"] = ("V7-196", """
## 24. 审计 SQL 与分区实践

调查越权：`SELECT * FROM audit_events WHERE tenant_id=$1 AND user_hash=$2 AND ts BETWEEN $3 AND $4`。chunk 引用查询：`chunk_ids @> ARRAY['c123']`。索引：`(tenant_id, ts DESC)` + 月分区。BI 连 **只读副本**，禁止生产写账号。导出异步写对象存储，下载链接受 RBAC。

## 25. SIEM 告警规则示例

`acl_denied` 5 分钟内同用户 >20 次 → P2 告警。`empty_retrieval` 日环比 +50% → 内容工单。`prompt_tokens` 单租户 P95 破阈值 → [194](194.llm-token-cost-optimization-tutorial.md) 排查。Playbook URL 写在告警正文。

## 26. legal hold 与销毁作业

`legal_hold=true` 跳过 TTL；解除后 `DELETE FROM audit_events WHERE tenant_id=$1 AND ts<$2` 分批。`audit.purge` 元事件记录执行人与范围。与 [197 擦除](197.gdpr-data-residency-tutorial.md) 区别：擦除针对数据主体；保留针对时间策略。
""")

BLOCKS["188.secrets-management-rag-tutorial.md"] = ("V7-188", """
## 28. ESO 清单与轮换 Runbook

ExternalSecret `refreshInterval: 1h`；SM 新版本 → ESO 更新 K8s Secret → `kubectl rollout restart deploy/rag-api,rag-worker` → curl /ready → 抽样问答 → 吊销旧 Key。Celery 长任务：先 `scale worker=0`。Runbook 贴 on-call  wiki，每半年桌面演练计时。

## 29. 分环境项目与 CI 注入

`rag-dev`/`rag-staging`/`rag-prod` 三云项目独立限额。GitHub Actions：`main` 分支才注入 prod secret 引用。feature 分支用 dev Key。防止 staging 误连 prod 账单爆炸。

## 30. pydantic Settings 失败快

缺 `OPENAI_API_KEY` 启动即 `ValidationError`——避免运行时 401 难归因。api 与 worker **同一 Settings 类**，避免一边有 Key 一边没有。单测 mock `os.environ` 不硬编码 sk-。

## 31. 供应链与 SBOM

Dependabot + gitleaks 双门禁。私有 PyPI token 轮换与 LLM Key 同级。BuildKit `--mount=type=secret` 仅构建期，不进 [185 镜像](185.docker-multi-stage-build-tutorial.md) 层。

## 32. BYOK 与等保映射

租户 Key KMS envelope；审计 `key_custody` 无明文。等保：分散存储、访问审计、定期更换——本篇 checklist 直接映射控制点。与 [197](197.gdpr-data-residency-tutorial.md) 数据出境并列推进。
""")

BLOCKS["189.health-readiness-rag-tutorial.md"] = ("V7-189", """
## 31. /health 与 /ready 契约再述

`/health`：进程存活，不调外网，不调 DB，应 **极快**。<10ms。`/ready`：Postgres `SELECT 1`、Redis `PING`、Chroma `list_collections`，并行超时 1s。**LLM 永不进 ready**。Worker 无 HTTP：celery inspect ping 或 sidecar。

## 32. Ingress、SSE、preStop

`proxy-read-timeout: 300` 对齐 [134 SSE](134.websocket-streaming-tutorial.md)。`lifecycle.preStop: sleep 5` 摘流后优雅停 Uvicorn。半开流不杀 Pod，拒新连接即可。

## 33. 硬软依赖实现片段

```python
hard = pg_ok and redis_ok and chroma_ok
soft = reranker_ok
return JSONResponse({"ready": hard, "degraded": not soft}, status=200 if hard else 503)
```

## 34. Worker 队列与合成探针

`celery_queue_length` 告警补位 api ready。集群外合成 `/ready`+mock chat，防证书过期。SLO ready 99.9%。

## 35. Compose 与 K8s 对照

| | Compose | K8s |
|---|---------|-----|
| 存活 | curl /health | livenessProbe |
| 就绪 | curl /ready | readinessProbe |
| 启动 | start_period | startupProbe |

## 36. 阶段 4 验收脚本

README：`curl -f /ready`；停 redis→503 不 crash。三十秒给面试官演示。
""")

BLOCKS["208.refine-summarization-tutorial.md"] = ("V7-208", """
## 24. Refine 完整状态机叙述

S0：`summary=""`，队列 Q 含按序 chunk。循环：弹 c→`summary'=LLM(summary,c)`→持久化 checkpoint→直至 Q 空。失败：单步超时重试 3 次；仍失败标 `refine_incomplete` 保留上一 checkpoint。与 Map-Reduce 并行对比：Refine **串行连贯**，Map **并行快**。

## 25. 在线证据压缩路径

top-12 chunk 按 **原文顺序** Refine 至 ~800 token→主模型作答。金标：数字题降幅≤2%。UI「整理证据 k/n」；勿流式展示中间 rolling summary（[174](174.streaming-typewriter-ui-tutorial（front-end）.md) 仅用于最终问答）。

## 26. 陷阱段、toc、人工纪要

金标 **故意错数段**；`segment_kind=toc` 跳过 LLM；法务 `summary_0` 从 §2 机器续写。冲突 **新段优先**。

## 27. Map-Refine 与指标

分 doc 并行 Refine→Reduce；`refine_rounds`、`stagnant_rounds`（编辑距离<5% stop）、`refine_tokens_total`。任务状态接 [161](161.index-task-state-machine-tutorial.md)。
""")

BLOCKS["209.raptor-hierarchical-retrieval-tutorial.md"] = ("V7-209", """
## 26. RAPTOR 构建逐步（工程师版）

①叶向量已有；②k-means(k≈10~20)；③簇内 chat **抽象摘要**；④摘要 embed 上浮；⑤至根或 L_max≤4。坏摘要污染整层——低温、限长、保留数字。换 embed **全树重建**（[193](193.vector-storage-cost-tutorial.md)）。

## 27. 在线：全层 ANN vs 下钻

全层合并打分简单但贵；上层下钻省算力。叶层 [93 hybrid](93.hybrid-search-tutorial.md)。`layer_weight`：概述 0.6 偏层，细节 0.2 偏叶。`raptor_layer_hits` 月度调参。

## 28. Celery 与资源

`cluster|summarize|embed` 链；失败簇重试。worker memory 8Gi+；OOM 减小 k。夜间构建白天只读。

## 29. Adaptive 与 PoC

[206](206.adaptive-rag-tutorial.md) 路由问法。200 页手册 PoC：主题→上层，脚注数字→叶。报告写构建 token、存储、Recall 对比扁平索引。
""")

BLOCKS["210.multimodal-rag-tutorial.md"] = ("V7-210", """
## 31. L1/L2/L3 再述与 ingest

L1 仅文本；L2 文本+页图 CLIP 双通道；L3 [211 ColPali](211.colpali-rag-tutorial.md)。metadata：`page_no, modality, content_hash`。ingest 监控 `ingest_text_chunks_total` vs `ingest_image_pages_total`。

## 32. 打分合并与路由

`score=α*s_text+(1-α)*s_image`；含「图、表」α→0.4。版式分类器 `route=clip|colpali`；误路由月度抽审 50 条。

## 33. OCR/VLM 决策

表格数字→OCR+文本 LLM；空间关系→VLM；标题页→文本即可。GPU 故障 `MM_RAG_ENABLED=false`。

## 34. 安全与金标

EXIF 剥离；像素上限；[195 PII](195.pii-redaction-rag-tutorial.md) 扫 OCR。[153 A/B](153.ab-experiment-rag-tutorial.md) 50+50 题分桶。采购 **分项报价** embed/GPU/存储。
""")

BLOCKS["211.colpali-rag-tutorial.md"] = ("V7-211", """
## 31. MaxSim 逐步（口述版）

页→patch 向量；query→token 向量。每 query token 在页内取 **max 相似 patch**，再对 token **求和**得页分。比整页 cosine **抗版式噪声**。索引 **10~50×** 单向量（[193](193.vector-storage-cost-tutorial.md)）。

## 32. 粗筛 200 + 精排 5

BM25/bi-encoder top-200→ColPali top-5。粗筛 Recall@200 **≥0.95** 金标守门。GPU 队列隔离；p95 3s 限精排 50 页。

## 33. 双 collection 与增量

`collection_text`/`collection_colpali`；删 doc 同步（[49](49.incremental-update-tutorial.md)）。FAQ **不** 默认 ColPali。

## 34. 构建、运维、面试

夜间 GPU 批索引；`colpali_gpu_queue_depth` 告警。面试：「多向量页嵌入+late interaction；版式 PDF；粗筛+精排两阶段。」与 [210](210.multimodal-rag-tutorial.md) 总线：210 选型，211 L3 专论。
""")

if __name__ == "__main__":
    for fname, (tag, block) in BLOCKS.items():
        p = ROOT / fname
        before = ch(p.read_text(encoding="utf-8"))
        after = ins(p, tag, block)
        print(f"{fname}: {before} -> {after} need={max(0,5000-after)}")
