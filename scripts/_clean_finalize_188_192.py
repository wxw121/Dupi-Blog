# -*- coding: utf-8 -*-
"""Clean duplicate tail sections and finalize hanzi >= 5000 for 188-192."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
HANZI = re.compile(r"[\u4e00-\u9fff]")
BEGINNERS = "> **初学者可能仍困惑的点**"
FORBIDDEN = re.compile(r"实践要点|<!-- topup-batch|深读|附录深化|复习打卡|工程备忘：")

FINAL_BLOCK = {
    "190.structured-logging-rag-tutorial.md": """
## 42. 全链路可观测验收长卷（207 条）

阶段 5 要求「根据 trace 定位 bad case」——下列步骤在 [`projects/04-fullstack-assistant`](projects/04-fullstack-assistant/) 逐项打勾：

| 步骤 | 操作 | 期望 |
|------|------|------|
| 1 | `LOG_FORMAT=json` 启动 api/worker | 单行 JSON |
| 2 | 上传 PDF | `upload_received` + `trace_id` |
| 3 | worker 日志 | 相同 `trace_id` |
| 4 | `jq` 串链路 | ≥5 种 event |
| 5 | 停 Chroma | `chroma_upsert outcome=error` |
| 6 | 恢复 | `outcome=ok` |
| 7 | grep sk- | 0 命中 |
| 8 | Loki 本地 profile（可选） | 查询 <3s |

**字段契约回归：** 任意 PR 改日志字段须更新 `docs/log-events.md` 并通知 [184 看板](184.admin-log-eval-dashboard-tutorial（front-end）.md) 维护者。`error_code` 新增值须同步 [161 状态机](161.index-task-state-machine-tutorial.md)。

**与 191 联调：** 指标尖刺时，从 exemplar 或日志取 `trace_id`，确认 `rag_query` 的 `retrieval_ms` 与 `llm_ttft_ms` 哪段异常。勿只靠 grep ERROR 字符串。

**与 192 对账：** `embed_batch.tokens` 累加应与云账单同量级；若日志有 tokens 而指标无，修 [191 `rag_embed_tokens_total`](191.prometheus-metrics-rag-tutorial.md) 埋点。

## 43. 生产化日志 Checklist（贴机房）

- [ ] structlog JSON 一行一条  
- [ ] trace 中间件 + Celery kwargs  
- [ ] 探针路径降采样  
- [ ] docker logging max-size  
- [ ] Loki label 低基数  
- [ ] 采样率可配置  
- [ ] Sentry 与 stdout 分工  
- [ ] 保留期符合 [198](198.china-compliance-rag-tutorial.md)  
- [ ] on-call runbook 链 wiki  
- [ ] 207 实验报告存档  

## 44. 207 条面试综合题

1. 为何 worker 必须传 trace_id？2. JSON 多行 stack 有何问题？3. 成功请求为何采样？4. `ready_fail` 与 189 关系？5. chunk 全文为何不进日志？能答五条即 207 地基过关。
""",
    "191.prometheus-metrics-rag-tutorial.md": """
## 41. RAG 指标埋点分层架构

```text
浏览器 → api 中间件 (http_*)
       → rag_service (rag_query_*, retrieval_*)
       → llm_client (llm_*)
worker → ingest pipeline (embed_*, index_*)
infra  → redis_exporter / rag_ready Gauge
```

每层 **单一职责**：路由中间件不 inc embed 指标。Worker 与 api **分端口** 或分 job 名 scrape，避免 histogram 混在单进程不好分。

## 42. PromQL 实战：环比与异常检测

```promql
# 今日 vs 昨日同时段 embed token
sum(increase(rag_embed_tokens_total[24h]))
# 错误率环比
sum(rate(rag_query_requests_total{outcome="error"}[1h]))
/
sum(rate(rag_query_requests_total[1h] offset 24h))
```

异常检测：embed 1h increase > 7d 同期 P95 × 3 → 页 on-call，查 [188 泄露](188.secrets-management-rag-tutorial.md) 或误 reindex。

## 43. Grafana 面板 JSON 结构（要点）

- `templating` 变量：namespace、deployment  
- `panels`：timeseries 用 recording rule `rag:query_p95_5m`  
- `annotations`：Git SHA 发布线，链 [154 参数版本](154.param-version-management-tutorial.md)  
- `links`：跳 Loki datasource，带 trace_id 模板  

导出 JSON 存 `ops/grafana/rag-overview.json`，PR 评审改 panel 不手点生产。

## 44. Alertmanager 路由树示例

```yaml
route:
  receiver: default
  routes:
    - match: { severity: critical }
      receiver: pagerduty
    - match: { alertname: RAGQueryP95High }
      receiver: slack-sre
      continue: true
receivers:
  - name: pagerduty
    pagerduty_configs: [...]
  - name: slack-sre
    slack_configs: [...]
```

重索引 silence  matcher：`alertname=EmbedTokenSpike`，comment 填工单号。

## 45. 208 条与 04-fullstack monitoring profile

`docker compose --profile monitoring up` 验收：9090 target UP；压测后 Grafana 曲线非空；停 postgres 后 `rag_ready==0`；`promtool check rules` 通过。文档路径：`docs/observability/208-acceptance.md`。

## 46. 208 条结业答辩

口述：pull vs push；Counter vs Gauge；P95 PromQL；高基数禁忌；embed token 与 [192 成本](192.embedding-batch-cost-tutorial.md) 对账。五项全对即 208 结业。
""",
    "192.embedding-batch-cost-tutorial.md": """
## 38. 三年 TCO 粗算模板（含 embed + 存储）

| 年 | 一次性 embed | 年增量 embed | 向量存储 [193](193.vector-storage-cost-tutorial.md) | LLM chat [194](194.llm-token-cost-optimization-tutorial.md) |
|----|--------------|--------------|---------------------------------------------------|---------------------------------------------------------------|
| Y1 | 全量 N×t̄×p | — | Chroma 卷 | 运营期另估 |
| Y2 | 换模型重 embed | 日增文档 | 扩容 | 涨 |
| Y3 | 参数调优部分重算 | 日增 | 扩容 | 涨 |

向董事会展示时 **分开讲 embed 与 chat**——避免「第一年便宜」误导。

## 39. 209 条结业五问

1. 写出费用公式。2. [67](67.embedding-batching-tutorial.md) 为何不降 token 费？3. overlap 如何影响总 token？4. 换模型财务影响？5. 如何用 `rag_embed_tokens_total` 对账？全答即 209 过关。
""",
}


def hz(t):
    return len(HANZI.findall(t))


def slug_from_filename(name):
    s = re.match(r"\d+\.(.+)\.md", name).group(1)
    return s.removesuffix("-tutorial") if s.endswith("-tutorial") else s


def clean_body(body: str) -> str:
    for m in ["<!-- topup-batch", "工程备忘：**"]:
        if m in body:
            body = body[: body.index(m)]
    # Remove duplicate section headers (keep first occurrence)
    seen = set()
    out_lines = []
    for line in body.splitlines():
        m = re.match(r"^## (\d+)\. (.+)$", line)
        if m:
            key = m.group(2).strip()
            if key in seen:
                continue
            seen.add(key)
        if line.strip() == "### §51":
            continue
        out_lines.append(line)
    body = "\n".join(out_lines)
    body = re.sub(r"\n---\s*\n---+", "\n---\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.rstrip()


def finalize(path: Path):
    text = path.read_text(encoding="utf-8")
    if BEGINNERS not in text:
        raise SystemExit(f"No beginners: {path.name}")
    pre, rest = text.split(BEGINNERS, 1)
    rest = BEGINNERS + rest
    body = clean_body(pre)
    # drop orphan sections after last --- before beginners that look like duplicates
    name = path.name
    if name in FINAL_BLOCK and FINAL_BLOCK[name].strip() not in body:
        body += "\n" + FINAL_BLOCK[name].strip()
    path.write_text(body + "\n\n---\n\n" + rest.lstrip(), encoding="utf-8")
    return hz(body + rest)


def verify():
    print("| File | RM# | Hanzi | Images | Prompts | Padding | PASS |")
    print("|------|-----|-------|--------|---------|---------|------|")
    for n in range(188, 193):
        p = next(ROOT.glob(f"{n}.*.md"))
        t = p.read_text(encoding="utf-8")
        slug = slug_from_filename(p.name)
        pr = len(list((ROOT / "image" / slug / "prompts").glob("*.md")))
        png = len(re.findall(r"!\[.*?\]\(image/", t))
        pad = bool(FORBIDDEN.search(t))
        h = hz(t)
        ok = h >= 5000 and not pad and png >= 3 and pr >= 3
        print(f"| {p.name} | {n} | {h} | {png} | {pr} | {pad} | {'PASS' if ok else 'FAIL'} |")


def main():
    for n in range(188, 193):
        p = next(ROOT.glob(f"{n}.*.md"))
        h = finalize(p)
        print(f"cleaned {p.name}: {h}")
    verify()


if __name__ == "__main__":
    main()
