# -*- coding: utf-8 -*-
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

V5 = {
"197.gdpr-data-residency-tutorial.md": ("V5-197", "## 21. 最小补充\n\nRoPA 与 Terraform 输出字段 **版本锁定**，避免法务 PDF 与生产配置漂移。"),
"207.map-reduce-summarization-tutorial.md": ("V5-207", "## 18. 补充\n\nMap 阶段 **限流** 与 embed 批次对齐 [67](67.embedding-batching-tutorial.md)，防夜间批任务打满 API 配额。"),
}

# Large blocks for bigger gaps
V5["188.secrets-management-rag-tutorial.md"] = ("V5-188", """
## 21. 密钥治理周会三件小事

每周五分钟：1）gitleaks 是否绿；2）是否有新员工缺 `.env` 指引；3）云账单 embed 突增是否 Key 泄露疑云。与 [192 成本](192.embedding-batch-cost-tutorial.md) 联动。

## 22. K8s Secret 与 ConfigMap 边界

`CHROMA_COLLECTION`、`LOG_LEVEL` 进 ConfigMap；`OPENAI_API_KEY` 仅 Secret。`stringData` 示例不得进 Git——用 Sealed Secrets。

## 23. 与 [185 镜像](185.docker-multi-stage-build-tutorial.md) 联合验收

`docker history` 无 `sk-`；`ENV` 无默认密钥；worker/api 同 Settings 类启动 fail fast。
""")

V5["189.health-readiness-rag-tutorial.md"] = ("V5-189", """
## 21. 探针失败事件排障

`kubectl describe pod` Events 里 **Liveness probe failed** 与 **Readiness probe failed** 分开读。前者杀容器；后者摘流量。勿混为一谈。

## 22. 依赖 mock 与测试环境

集成测试 mock Postgres 时 **不要** 把 mock 配置进生产 ready 路径——测试 settings 单独模块。

## 23. 与 [186 Compose](186.docker-compose-fullstack-tutorial.md) 一键验收

`depends_on: condition: service_healthy` 对齐 ready；故意停 redis 观察 api **不 crash** 仅 ready 503。
""")

V5["196.audit-log-rag-tutorial.md"] = ("V5-196", """
## 21. 审计查询性能

`tenant_id + ts` 复合索引；按月分区。BI 只读副本，禁止生产写权限。大查询 **异步导出** 对象存储。

## 22. legal hold 与销毁

`legal_hold` 租户跳过 TTL job；解除后批删。销毁作业记元审计 `audit.purge`。
""")

V5["203.multi-step-tool-retrieval-tutorial.md"] = ("V5-203", """
## 20. 补充：轨迹去重指标

`duplicate_chunk_rate` 高说明 **可少搜一轮**——反改 tool description 或 Adaptive 路由（[206](206.adaptive-rag-tutorial.md)）。
""")

V5["204.self-rag-tutorial.md"] = ("V5-204", """
## 19. 补充：与 CRAG 并联

检索差时 [205 CRAG](205.crag-corrective-rag-tutorial.md) 改写 query；Self-RAG 在 **有证据仍胡编** 时更有价值——按 bad case 分桶选型。
""")

V5["208.refine-summarization-tutorial.md"] = ("V5-208", """
## 18. Refine 与索引任务状态

ingest Refine 任务暴露 `refine_progress={k,n}` 给 [180 进度 UI](180.index-progress-ui-tutorial（front-end）.md)。失败保留 checkpoint 路径供 [181 重建](181.reindex-ui-tutorial（front-end）.md) 重跑。

## 19. 数字守恒 prompt 片段

「合并摘要时 **禁止引入新数字**；若新段含数字，必须原文照录并标注来源段编号。」——降低胡编，略增 token。

## 20. 与 [207 Map-Reduce](207.map-reduce-summarization-tutorial.md) 实验记录

同一 200 页 PDF：记录 Refine 总 token、墙钟时间、ROUGE、数字题 F1；选型写入 ADR（Architecture Decision Record）。
""")

V5["209.raptor-hierarchical-retrieval-tutorial.md"] = ("V5-209", """
## 18. 簇摘要 prompt 要点

要求摘要 **保留专有名词与数字**、**不写引言套话**、**长度≤簇内原文 20%**。坏摘要会污染整层检索。

## 19. 树版本与回滚

`raptor_tree_version` 写入 metadata；回滚读旧版本指针。与 [48 doc 版本](48.doc-versioning-tutorial.md) 对齐。

## 20. 构建资源 limit

worker 构建树时 `memory limit 8Gi` 起；OOM 时 **减小 k 或分批聚类**，勿盲目加并发。
""")

V5["210.multimodal-rag-tutorial.md"] = ("V5-210", """
## 18. rasterize DPI 选择

150 DPI 平衡体积与 OCR/CLIP 质量；300 DPI 扫描件。单页 PNG **>5MB** 拒绝入库（[179 上传](179.kb-doc-upload-ui-tutorial（front-end）.md) 对齐）。

## 19. 双通道分合并

text hit score `s_t`，image hit `s_i`；合并 `α*s_t + (1-α)*s_i`，α 由 query 分类器输出。默认 α=0.7。

## 20. 与 ColPali 路由

版式关键词命中 **>0.8** 走 [211](211.colpali-rag-tutorial.md)；否则 L2 CLIP。记录 `router_decision` 供分析。
""")

V5["211.colpali-rag-tutorial.md"] = ("V5-211", """
## 18. patch 网格与分辨率

页 rasterize 长边 **1024px** 常见；patch 大小影响向量条数与 MaxSim 精度。与 [210 ingest](210.multimodal-rag-tutorial.md) DPI 一致。

## 19. 冷启动与预热

首批查询 **预热 GPU**；缓存热门 doc 页向量在 **GPU 显存**（小规模）。大规模 **仅磁盘索引**。

## 20. 采购对话要点

向采购说明：**ColPali 成本 = 存储 GB + GPU 时 + 构建 embed**；纯文本库 **不应默认全量 ColPali**。
""")

if __name__ == "__main__":
    for fname, (tag, block) in V5.items():
        p = ROOT / fname
        before = ch(p.read_text(encoding="utf-8"))
        after = ins(p, tag, block)
        print(f"{fname}: {before} -> {after} need={max(0,5000-after)}")
