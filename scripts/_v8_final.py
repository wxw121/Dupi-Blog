# -*- coding: utf-8 -*-
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

B = {}
B["196.audit-log-rag-tutorial.md"] = ("V8-196", "## 27. 结业检查\n\n审计表按月分区、只读副本查越权、empty_retrieval 周报驱动补库、导出记元审计——四条全过即 196 篇工程结业。与 [197 擦除](197.gdpr-data-residency-tutorial.md)、[195 PII](195.pii-redaction-rag-tutorial.md) 组成合规三角。")

B["188.secrets-management-rag-tutorial.md"] = ("V8-188", """
## 33. 188 篇工程结业五问

1）仓库 `docker history` 与 `git log -p` 无 sk-？2）前端 bundle 搜不到 Key？3）轮换 runbook 存在且半年演练？4）分环境云项目限额独立？5）[189 ready](189.health-readiness-rag-tutorial.md) 不 ping LLM 验 Key？全 **是** 方可标路线图 205 条密钥篇结业。与 [186 Compose env_file](186.docker-compose-fullstack-tutorial.md)、[187 K8s Secret](187.kubernetes-basics-rag-tutorial.md) 联调通过。
""")

B["189.health-readiness-rag-tutorial.md"] = ("V8-189", """
## 37. 案例库：五种 ready 翻车

**案例1** 迁移锁：进程内 alembic 与 ready 抢 PG→独立 Job。**案例2** Chroma 冷 30s→startupProbe。**案例3** Redis DNS 抖→ready 偶发 503 摘流量→修 CoreDNS。**案例4** 把 OpenAI ping 放 ready→厂商抖全网重启→移出。**案例5** worker 假死队列堆→api ready 绿→加 `celery_queue_length` 告警。

## 38. 探针参数起步值（单副本 api）

liveness：period 20s，timeout 2s，failure 3。readiness：period 10s，timeout 3s，failure 3。startup：period 5s，failureThreshold 24（覆盖 2min）。按实测 P99 调，**ready 必须轻于 liveness**。

## 39. 与 [190][191][148] 观测三角

190 JSON 日志 `ready_fail` 事件；191 `rag_ready` Gauge；148 trace 与探针分离。Grafana 一页：ready 率、组件失败占比、探针延迟 P99。

## 40. 初学者实操：本地故意弄错

Compose 故意 `DATABASE_URL` 指错容器名→ready 503 但 `/health` 200。新人亲手试一次胜过读十页文档。写进 `04-fullstack-assistant/TROUBLESHOOTING.md`。
""")

B["208.refine-summarization-tutorial.md"] = ("V8-208", """
## 28. Refine vs Map-Reduce vs RAPTOR 一表

| | Refine | Map-Reduce | RAPTOR |
|---|--------|------------|--------|
| 并行 | 低 | 高 | 构建离线 |
| 叙事 | 强 | 中 | 层次 |
| 数字题 | 需金标 | 较稳 | 叶层 |
| 成本 | 递推 token | map 并行峰值 | 构建+存储 |

## 29. 180/181 任务衔接

Refine ingest 写 `refine_k/n` 到 task；checkpoint 路径供断点续跑与重建。失败 `refine_incomplete` 运维可续。

## 30. 阶段 4 不强制 Refine

PoC 可只做 Map-Reduce 离线摘要；在线问答仍用叶 chunk。Refine 是 **锦上添花** 非门槛。
""")

B["209.raptor-hierarchical-retrieval-tutorial.md"] = ("V8-209", """
## 30. 参数实验记录表（模板）

| k | L_max | 构建token | 存储GB | overview R@5 | detail R@5 |
|---|-------|-----------|--------|----------------|------------|
| 10 | 3 | ... | ... | ... | ... |

选 Pareto 最优写 ADR。勿拍脑袋默认 k=10。

## 31. 增量剪枝

单 doc 更新重建 **子树**；删除 doc **剪枝** 释放空间。全库重建仅换 embed 或改 k/L_max。

## 32. 与固定 RAG 共存

扁平叶 chunk **仍保留**；RAPTOR 上层是 **额外索引**。检索可配置 `use_raptor=true` 特征开关。
""")

B["210.multimodal-rag-tutorial.md"] = ("V8-210", """
## 35. 三档选型决策树

纯 MD/可选中文本？→ L1。有图但版式简单？→ L2 CLIP。扫描合同/幻灯片版式题？→ L3 ColPali。决策树贴 wiki，防销售承诺「全能多模态」。

## 36. ingest 失败态

rasterize 失败→记 `image_ingest_failed` 仍保留文本支路。OCR 空→标 `ocr_empty` 降权 image 通道。运营可见任务详情（[180](180.index-progress-ui-tutorial（front-end）.md)）。

## 37. 成本看板四列

文本 embed 元、图像 embed 元、GPU 时、存储 GB——周会只看超预算租户。与 [194 token](194.llm-token-cost-optimization-tutorial.md) 分开。

## 38. 安全复审清单

EXIF、像素炸弹、PII 扫 OCR、上传大小（[179](179.kb-doc-upload-ui-tutorial（front-end）.md)）。每季度复审一次。
""")

B["211.colpali-rag-tutorial.md"] = ("V8-211", """
## 35. ColPali 采购对话脚本

「我们库 80% 是 Word/Markdown，只有 20% 扫描合同——建议仅对这 20% 上 ColPali，其余 CLIP/文本。ColPali 索引约为单向量十倍存储，GPU 精排 p95 三秒，需粗筛守门。」避免全库 ColPali 被采购误批。

## 36. 精排候选数调参

50 页精排 p95 2.5s；100 页可能破 5s。用生产 trace 调 `max_refine_pages`。A/B 准确率 vs 延迟。

## 37. 与 BM25 粗筛联调

合同编号、公司名 **BM25 先缩 doc** 再页级 ColPali——百万页库必备。否则粗筛 200 页跨 doc 噪声大。

## 38. 了解篇结业

能口述 MaxSim、对比 CLIP、画粗筛→精排流程、说明索引贵一个数量级——即 228 条了解篇达标。训练 ColPali 不在本篇范围。
""")

if __name__ == "__main__":
    for f, (tag, blk) in B.items():
        p = ROOT / f
        print(f"{f}: {ins(p, tag, blk)} need={max(0,5000-ch(p.read_text(encoding='utf-8')))}")
