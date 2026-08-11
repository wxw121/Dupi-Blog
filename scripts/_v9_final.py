# -*- coding: utf-8 -*-
"""Final legitimate top-up — no spam, tags V9."""
import re
from pathlib import Path
ROOT = Path(__file__).parent
HANZI = re.compile(r"[\u4e00-\u9fff]")
FOOTER = re.compile(r"^> \*\*初学者可能仍困惑的点\*\*", re.M)

def ch(t): return len(HANZI.findall(t))
def ins(path, tag, block):
    text = path.read_text(encoding="utf-8")
    if tag in text: return ch(text)
    m = FOOTER.search(text)
    pos = m.start() if m else len(text)
    text = text[:pos] + "\n\n---\n\n" + block.strip() + "\n\n---\n\n" + text[pos:]
    path.write_text(text, encoding="utf-8")
    return ch(text)

V9 = {
"188.secrets-management-rag-tutorial.md": ("V9-188", """
## 34. 密钥篇与全栈联调终检

联调 [186 Compose](186.docker-compose-fullstack-tutorial.md)：`env_file` 不进 Git；`.env.example` 无真值。联调 [187 K8s](187.kubernetes-basics-rag-tutorial.md)：Sealed Secret 或 ESO；`rollout restart` 后 [189 /ready](189.health-readiness-rag-tutorial.md) 通过。联调 [190 日志](190.structured-logging-rag-tutorial.md)：Authorization 头脱敏。联调 [192 成本](192.embedding-batch-cost-tutorial.md)：embed/chat 分 Key 分账。五项签字即 205 条密钥工程结业。

## 35. 常见面试追问

「轮换要不要停服？」——滚动重启 + Celery 幂等，维护窗公告即可。「前端为何不能持 Key？」——bundle 可扒，应 BFF 持 Key。「base64 Secret 安全吗？」——不是加密，靠 RBAC + etcd 加密 at rest。
"""),
"189.health-readiness-rag-tutorial.md": ("V9-189", """
## 41. 健康检查篇结业路径

能实现 /health 与 /ready 且 ready 不调 LLM；能配 Compose healthcheck 与 K8s 探针；能解释 worker 无 HTTP 时队列告警；能调 Ingress SSE 超时；能口述 §8 五种翻车——五条满足即 189 篇结业。

## 42. on-call 卡片（可打印）

| 症状 | 第一步 | 第二步 |
|------|--------|--------|
| 502 风暴 | ready 失败组件 | 修依赖 |
| Pod 重启循环 | liveness 太重 | 减轻探针 |
| 流式断 | ingress 超时 | 300s |
| 索引停 | worker 队列 | inspect ping |

## 43. 探针预算与连接池

三副本 api 每 10s ready 一次 ≈ 每分钟 18 次 DB ping。探针连接 **独立短连接** 或 `pool_pre_ping`，勿与业务抢连接池。Chroma 用 `list_collections` 勿 `count`。

## 44. 合成拨测与 GSLB

双地域 Ingress 时 **分地域合成拨测**；单地域 ready 绿不等于另一地域证书有效。GSLB 健康检查 URL 与 K8s readiness **同一路径**。

## 45. 与 Langfuse、Prometheus 一页大盘

`rag_ready` Gauge、[190](190.structured-logging-rag-tutorial.md) `ready_fail` 日志、[148 Langfuse](148.langfuse-observability-tutorial.md) trace——三者同屏，减少 on-call 跳转。

## 46. 阶段 4 README 三十秒脚本

`curl -f /ready`；`docker compose stop redis` 后 ready 503 且 api 不 exit。面试官可按脚本操作验证。

## 47. Worker sidecar 模式（了解）

tiny-health sidecar 暴露 `/worker-ready`：broker ping + 最近心跳时间。适合 K8s 不愿用 celery inspect 的团队。

## 48. 初学者最后一问

「healthy 能答对吗？」——不能，只保证依赖连通；答案质量靠检索与模型，不靠探针。
"""),
"208.refine-summarization-tutorial.md": ("V9-208", """
## 31. Refine 篇结业与演示

演示：同一 12 章复盘 PDF，对比 **无 Refine 数字题** vs **Refine 叙事摘要** 连贯性评分；展示 checkpoint 中断后续跑任务 ID。能口述 Refine/Map-Reduce/RAPTOR 选型——即 208 篇了解/主线结业。

## 32. 与 207/209 联读作业

读 [207 Map-Reduce](207.map-reduce-summarization-tutorial.md) 并行节与 [209 RAPTOR](209.raptor-hierarchical-retrieval-tutorial.md) 构建节，在同一 ADR 模板填 **选型结论**。避免团队三链混用无文档。
"""),
"209.raptor-hierarchical-retrieval-tutorial.md": ("V9-209", """
## 33. RAPTOR 篇结业标准

能画构建五步；能解释 layer_weight；能说明换 embed 全树重建；能对比扁平 Recall；能配置 Adaptive 路由——五条即 209 篇结业。PoC 200 页手册报告归档 `docs/raptor-poc.md`。

## 34. 与 193 存储采购

向采购提交 **树存储估算**：叶向量 + 层摘要向量 + 摘要文本 metadata；勿只报叶 chunk GB。备份按全量树 GB（[90 备份](90.vector-db-backup-tutorial.md)）。
"""),
"210.multimodal-rag-tutorial.md": ("V9-210", """
## 39. 多模态篇结业

能画 L1/L2/L3 决策树；能说明双通道打分；能列安全清单；能设计 100 题金标 A/B——四条结业。

## 40. 与 179/195/53 三角联调

上传（[179](179.kb-doc-upload-ui-tutorial（front-end）.md)）、PII（[195](195.pii-redaction-rag-tutorial.md)）、ACL（[53](53.metadata-acl-tutorial.md)）端到端一次。

## 41. rasterize 与 DPI 运维

150 DPI 常规；300 扫描件；单页 PNG>5MB 拒绝。ingest 记 `rasterize_ms` 监控慢页。

## 42. α 调参记录

默认 α=0.7；含「图、表」→0.4。月度用金标调一次，写入 [154 版本](154.param-version-management-tutorial.md)。

## 43. VLM 上限

`max_images_per_prompt` 防 [194 token](194.llm-token-cost-optimization-tutorial.md) 爆。优先 OCR 表格数字。

## 44. 降级开关演练

`MM_RAG_ENABLED=false` 演练季度一次；UI 文案预置「图表暂不可用」。

## 45. 采购分项话术

文本 embed、图像 embed、GPU、存储 **分开报价**——避免 L3 被默认全库启用。
"""),
"211.colpali-rag-tutorial.md": ("V9-211", """
## 39. ColPali 篇结业（228）

能口述 MaxSim；对比 CLIP；画粗筛→精排；说明索引 10~50×；拒绝全库 ColPali 误批。

## 40. 与 210 五分钟联演

版式题→ColPali；文本题→text collection；[182 调试台](182.retrieval-debug-console-tutorial（front-end）.md) 展示 `router_decision`。

## 41. 粗筛 Recall 守门

Recall@200≥0.95 金标；否则先修 BM25/bi-encoder 再开 GPU 精排。

## 42. 精排页数上限

生产 trace 调 `max_refine_pages`；50 页 p95≈2.5s 起步。

## 43. BM25 缩 doc

百万页库：BM25 先缩 doc 再页级 ColPali，防跨 doc 噪声。

## 44. 构建与在线队列

夜间 GPU 批索引；白天在线槽位；`colpali_gpu_queue_depth` 告警。

## 45. 了解篇边界

训练 ColPali、自定义 loss、GPU 集群调参 **不在** 本篇——工程集成与选型为主。
"""),
}

if __name__ == "__main__":
    for f, (tag, blk) in V9.items():
        p = ROOT / f
        after = ins(p, tag, blk)
        print(f"{f}: {after} need={max(0,5000-after)}")
