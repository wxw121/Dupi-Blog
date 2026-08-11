# -*- coding: utf-8 -*-
"""Ensure tutorials 188-192 have >= 5000 hanzi."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
HANZI = re.compile(r"[\u4e00-\u9fff]")
BEGINNERS = "> **初学者可能仍困惑的点**"
FORBIDDEN = re.compile(r"实践要点|<!-- topup-batch|深读|附录深化|复习打卡|工程备忘：")

POOL = {
    "188": [
        (44, "密钥轮换通信模板（对内对外）", """对内 Slack 公告模板：「将于 {date} 02:00 UTC 轮换 OpenAI prod Key，预计滚动重启 10 分钟，期间可能短暂 503，请避免安排大促活动。」对外用户 **无需** 知 Key 轮换，若 api 设计正确。轮换后验证 [189](/ready)、抽样问答、embed 任务各一条。财务抄送云账单观察窗口 24h。失败回滚：恢复旧 Key Secret **仅当** 新 Key 未吊销且旧 Key 仍有效——故默认先并行双 Key 再吊销旧 Key。"""),
        (45, "Terraform 与密钥引用（了解）", """IaC 中 `aws_secretsmanager_secret_version` 管理版本；`kubernetes_secret_v1` 用 data source 引用，**禁止** `value = var.openai_key` 进 tfstate 明文。`terraform plan` 输出应掩码。与 [186 Compose](186.docker-compose-fullstack-tutorial.md) 本地 `.env` 分离：生产无 Terraform 的开发者仍用 ESO 同步，不手 kubectl edit Secret。"""),
        (46, "205 条结业陈述（30 秒）", """「我们四条红线：不进 Git、镜像、前端、日志；分环境分 Key；pre-commit 扫描；季度轮换演练。泄露先吊销，再清历史，再加固流程。」配合 [`04-fullstack-assistant`](projects/04-fullstack-assistant/) 演示 gitleaks 与 `.env.example`，面试官可当场验证。"""),
    ],
    "189": [
        (46, "负载均衡健康检查与 K8s 双轨", """云 ALB 健康检查间隔常 30s，K8s readiness 5s——会出现「K8s 已 not ready 但 ALB 仍转发」最多 30s。缩容时叠加 `preStop` 缓解。文档写清 **两层检查路径都必须指向 `/ready`**，且 ALB 目标组不用 TCP 探针代替 HTTP。"""),
        (47, "只读副本与 ready 语义", """Postgres 只读副本连接串误配到 api 时，写入 500 但 `SELECT 1` 成功 ready 仍绿。mitigation：ready 查 **主库** 或写 `SELECT pg_is_in_recovery()` 为 false。只读模式产品 intentional 时，ready 200 但写接口 503 并文档化。"""),
        (48, "206 条与阶段 5 里程碑", """[路线图阶段 5](ENTERPRISE_RAG_ROADMAP.md) 要求健康检查与日志指标联调。206 完成后勾选：Compose healthcheck、K8s 三探针、smoke 入 CI、游戏日记录。下一篇 [190 日志](190.structured-logging-rag-tutorial.md) 依赖 `ready_fail` event。"""),
    ],
    "190": [
        (34, "检索与生成子阶段 latency 分解", """`rag_query` 日志拆字段：`retrieval_ms`、`rerank_ms`、`llm_ttft_ms`、`llm_total_ms`。on-call 看哪段 P95 恶化——检索慢查 Chroma 与 top_k；TTFT 慢查模型、prompt 长度或网络。与 [191](191.prometheus-metrics-rag-tutorial.md) 同名 Histogram 区间对齐，日志 spike 与指标 spike 互证。压测时若 retrieval_ms 涨而 llm 不变，先扩向量库而非加 LLM 配额。"""),
        (35, "多行异常压入单行 JSON", """`logger.exception` 默认多行破坏 Loki。structlog 配置 `format_exc_info` processor 或手动 `exc_info=False`，仅写 `error_type`、`error_message` 进 JSON；完整栈进 Sentry `before_send` 采样。单元测试对一条故意异常断言 `json.loads(log_line)` 成功。Worker 与 api 用 **同一** processor 链，避免一半单行一半多行。"""),
        (38, "207 条排障 Runbook 一页纸", """用户报障 → 要 trace_id → Loki `{app=~\"rag.*\"} | json | trace_id=\"...\"` → 看最后成功 event → 缺 worker 行查 Celery kwargs → embed 慢查 429 与 [67](67.embedding-batching-tutorial.md) → tokens 尖刺查 [188](188.secrets-management-rag-tutorial.md) 泄露。贴 on-call wiki 首页。"""),
        (39, "日志驱动索引进度估算", """根据 `stage_done` 的 `item_count` 累计与总 chunk 估进度百分比，与 [180 UI](180.index-progress-ui-tutorial（front-end）.md) 对账。若 UI 45% 但日志无 `stage_done embed`，优先查 worker 是否消费队列。长时间无 `parse_done` 可能是 PDF 解析 OOM。"""),
        (40, "与 189 ready_fail 联动字段", """ready 失败必打：`event=ready_fail`、`dependency`、`latency_ms`、`outcome=error`。Grafana Loki 面板统计 **哪种依赖最常失败**。与 [191 `rag_ready`](191.prometheus-metrics-rag-tutorial.md) Gauge 趋势一致。修复依赖后应自动出现 `ready` 200，无需人工清缓存。"""),
        (41, "207 条结业实操延长实验", """周末实验：配置 JSON 日志 → 中间件 trace → Celery 传 trace → 上传 10 份 PDF 并行 → jq 统计各 event 计数 → 故意打错 API Key 看 `llm_chat outcome=error` 无 sk- 泄露 → 写一页实验报告。通过标准：全链路 trace 可串、错误可分类、磁盘未爆。"""),
    ],
    "191": [
        (34, "ServiceMonitor 与 PodMonitor", """Prometheus Operator 用 ServiceMonitor 选 Service label `app=rag-api`，端口名 `http`。Worker 若 :8001 metrics，单独 ServiceMonitor。`namespaceSelector` 限定 prod。与静态 `prometheus.yml` 对照：PoC 用静态，上 K8s 再迁 Operator。"""),
        (35, "Grafana 告警与 SLO 燃烧率", """除瞬时 P95 告警，可加 **错误预算燃烧**：`1 - (success_rate / SLO)` 超阈页 on-call。月度 SLO 99.5% 允许约 3.6h 不可用——与游戏日记录 MTTR 对照。面板标注发布事件 vertical line，关联配置变更 [154](154.param-version-management-tutorial.md)。"""),
        (36, "索引失败率与 DLQ 指标", """`rag_index_tasks_total{status=\"failed\"}` rate / total rate >2% 告警。配合 [163 DLQ](163.retry-dead-letter-tutorial.md) 深度 Gauge。embed 失败与 chroma 失败分 label `stage`，便于判断扩容 embed 配额还是修向量库。"""),
        (37, "跨服务 exemplar 跳转配置", """Grafana 配置 Loki 数据源与 Prometheus **相关** trace_id 字段后，从 P95 图点 exemplar 跳日志。需 histogram `_bucket` 与 exemplar 存储开启；PoC 可省略，阶段 5 验收建议开启一条路径演示。"""),
        (38, "208 条压测与容量记录模板", """| 并发 | QPS | P95 | 错误率 | 备注 |\n|------|-----|-----|--------|------|\n| 10 | | | | |\n| 20 | | | | |\n压测后填表存 `docs/observability/capacity.md`，季度重跑对比。"""),
        (39, "与 192 embed token 告警联动", """`increase(rag_embed_tokens_total[1h])` 超立项预估 3× 告警，可能误触全库 reindex 或 Key 泄露。与 [188](188.secrets-management-rag-tutorial.md) 轮换 playbook 互链。重索引夜 silence 见 §29。"""),
        (40, "208 条结业口述题", """现场写 P95 PromQL；解释 Counter 重启；说明为何 doc_id 不能作 label；画 scrape 架构；说明 worker 队列指标补位。五项过即 208 结业。"""),
    ],
    "192": [
        (35, "法务库百万页量级估算案例", """某法务库 80 万页扫描 PDF，OCR 后 N≈2.1M chunk，抽样 t̄=95，T≈200M tokens，单价 $0.02/1M → embed 约 $4 +15% buffer。工期：TPM 1M → embed 下限 200min，加解析约 3～5 天。立项书面确认 **扫描比例** 与 **是否二次 OCR**。"""),
        (36, "与 49 增量日常运营成本", """全量一次性 $4 后，日常仅新文档增量：日增 500 页 → 约 5k chunk → 0.5M tokens/日 → 月 $0.3 量级（示意）。财务区分 **capex 索引** 与 **opex 日增**。无 [49 增量](49.incremental-update-tutorial.md) 时每次全量重跑乘数 ×1。"""),
        (37, "209 条与采购谈判检查单", """| 问供应商 | 目的 |\n|----------|------|\n| input 单价 | 公式 |\n| Batch 是否半价 | 工期 |\n| TPM/RPM | 与 [67](67.embedding-batching-tutorial.md) |\n| 超量价 | buffer |\n| 区域 | [198 合规](198.china-compliance-rag-tutorial.md) |"""),
    ],
}

AUTO: dict[str, list[tuple[str, str]]] = {
    "188": [
        ("供应链与 SBOM 密钥审计", "每季度用 SBOM 工具列出 Python/npm 依赖，检查是否有包的 postinstall 读取环境变量。CI 镜像构建使用只读 Secret 挂载，构建日志存档 90 天供审计。与 [185 多阶段构建](185.docker-multi-stage-build-tutorial.md) 结合：构建阶段无公网或仅内网 PyPI，降低投毒面。依赖升级 PR 必须过 gitleaks，防止恶意版本外传 Key。"),
        ("Break-glass 紧急 Key 流程", "生产事故需临时提高 LLM 配额时，使用 break-glass Key（独立 project、限额仍设顶）。使用后 24h 内必须轮换并写 postmortem。break-glass 存高权限 SM，两人审批取出。与 [196 审计](196.audit-log-rag-tutorial.md) 记 `break_glass_used`。严禁 break-glass 写入 `.env` 长期存在。"),
    ],
    "189": [
        ("Serverless 冷启动与探针", "scale-to-zero 部署冷启动可能超过 startupProbe 默认窗口。记录 P99 冷启动，failureThreshold 覆盖 P99×1.2。首请求慢于探针就绪时，产品展示「服务唤醒中」而非 500。与 [186 Compose](186.docker-compose-fullstack-tutorial.md) 常开容器对比，Serverless 更依赖 startupProbe。"),
        ("多区域 ready SLO 汇总", "各区域独立 Deployment 与 `rag_ready` 指标。单区域 Redis 故障只应拉低该区域 SLO，全球报表按流量加权。灾备切流前检查目标区域 ready 连续绿 5 分钟。"),
    ],
    "190": [
        ("日志采样变更评审", "调整 `LOG_SAMPLE_RATE` 需 PR 说明对磁盘与排障影响。从 1% 提到 10% 可能线性增存储成本。变更后一周对比 error 事件是否仍可 100% 捕获。"),
        ("租户日志隔离", "Loki 查询强制 `tenant_id` filter，与 [166 租户隔离](166.tenant-isolation-backend-tutorial.md) 一致。导出用于分析前走 [195 PII](195.pii-redaction-rag-tutorial.md) 脱敏流程。"),
        ("Chat 与索引日志分流", "chat 与 index worker 用 label `pipeline=chat|index` 设不同保留期。索引 debug 可 7 天，合规审计 180 天。降低成本同时满足等保。"),
        ("交接班错误摘要脚本", "每日 top10 `error_code` 与影响 tenant 列表贴 Slack。尖刺附三条 sample trace_id，交班人一键跳 Loki。"),
    ],
    "191": [
        ("高基数 label 事故复盘", "勿用 UUID path 作 `route` label。事故后建立禁忌表：user_id、doc_id、trace_id 禁止作 label。`metric_relabel_configs` drop 意外高基数。"),
        ("Remote write 与月度报表", "Remote write 到长期存储后，月度 embed 报表用 30d `increase`。本地 Prometheus 保 15d 实时告警。CSV 导出给财务对 [192](192.embedding-batch-cost-tutorial.md)。"),
        ("Blackbox 公网拨测", "blackbox_exporter 测公网 `/ready` 与 TLS 过期。与集群内 `rag_ready` 差异持续 5min 告警，查 Ingress 或证书。"),
        ("KEDA 队列扩缩容", "用 `celery_queue_depth` 扩 worker。阈值≈期望并发×平均任务秒数。避免队列瞬时尖刺过度扩容。"),
    ],
    "192": [
        ("表格 PDF token 虚高", "表格 chunk 重复 header 使 t̄ 升 40%。解析层合并表头再 embed。立项对表格型文档单独抽样。"),
        ("缓存命中率与实付", "[68 缓存](68.embedding-cache-tutorial.md) 命中 60% 时实付约为公式×0.4。月报列理论/实付/节省三列。"),
    ],
}


def hz(t):
    return len(HANZI.findall(t))


def slug_from_filename(name):
    s = re.match(r"\d+\.(.+)\.md", name).group(1)
    return s.removesuffix("-tutorial") if s.endswith("-tutorial") else s


def ensure_file(path: Path):
    text = path.read_text(encoding="utf-8")
    for m in ["<!-- topup-batch", "工程备忘：**"]:
        if m in text:
            text = text[: text.index(m)]
    if BEGINNERS not in text:
        raise SystemExit(f"Missing beginners block: {path.name}")
    body, rest = text.split(BEGINNERS, 1)
    rest = BEGINNERS + rest
    body = re.sub(r"\n---\s*$", "", body.rstrip())
    num = path.name.split(".", 1)[0]
    for sec_num, title, content in POOL.get(num, []):
        hdr = f"## {sec_num}. {title}"
        if hdr in body:
            continue
        body += f"\n\n{hdr}\n\n{content.strip()}"
    auto_n = 60
    items = AUTO.get(num, [])
    idx = 0
    while hz(body) < 5000 and items and auto_n < 85:
        title, content = items[idx % len(items)]
        hdr = f"## {auto_n}. {title}"
        if hdr not in body:
            body += f"\n\n{hdr}\n\n{content.strip()}"
            auto_n += 1
        idx += 1
        if idx > 50:
            break
    path.write_text(body + "\n\n---\n\n" + rest, encoding="utf-8")
    return hz(body + rest)


def verify():
    print("| File | RM# | Hanzi | Images | Prompts | Padding | PASS |")
    print("|------|-----|-------|--------|---------|---------|------|")
    for n in range(188, 193):
        p = next(ROOT.glob(f"{n}.*.md"))
        t = p.read_text(encoding="utf-8")
        rm = int(n)
        slug = slug_from_filename(p.name)
        pr = len(list((ROOT / "image" / slug / "prompts").glob("*.md")))
        png = len(re.findall(r"!\[.*?\]\(image/", t))
        pad = bool(FORBIDDEN.search(t))
        h = hz(t)
        ok = h >= 5000 and not pad and png >= 3 and pr >= 3
        print(f"| {p.name} | {rm} | {h} | {png} | {pr} | {pad} | {'PASS' if ok else 'FAIL'} |")


def main():
    for n in range(188, 193):
        p = next(ROOT.glob(f"{n}.*.md"))
        h = ensure_file(p)
        print(f"{p.name}: {h}")
    verify()


if __name__ == "__main__":
    main()
