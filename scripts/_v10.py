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

V10 = {
"188.secrets-management-rag-tutorial.md": ("V10-188", """
## 36. 密钥轮换日历模板

| 密钥 | 周期 | 负责人 | 上次轮换 |
|------|------|--------|----------|
| OPENAI prod | 90d | SRE | |
| JWT signing | 180d | 后端 | |
| DB password | 90d | DBA | |

季度审计对照表打勾。紧急轮换 15 分钟剧本贴 on-call。

## 37. 与 04-fullstack SECURITY.md

README 链 SECURITY.md：申请 .env 流程、禁止 commit 列表、轮换联系人、gitleaks 本地安装。面试官 clone 即见工程规范。
"""),
"189.health-readiness-rag-tutorial.md": ("V10-189", """
## 49. 探针术语双轨终表

| 中文 | English | RAG 要点 |
|------|---------|----------|
| 存活探针 | liveness | 进程活着 |
| 就绪探针 | readiness | 依赖就绪 |
| 启动探针 | startupProbe | 冷启动宽限 |
| 合成拨测 | synthetic probe | 集群外证书 |

## 50. 与 180 索引任务区分

用户问「为何搜不到」——先看 [180 索引进度](180.index-progress-ui-tutorial（front-end）.md) task 是否 done，再看 api ready。ready 绿只表示 **问答依赖通**，不表示 **索引完成**。

## 51. 189 篇结业签字

五能力签字：双端点实现、Compose/K8s 探针、worker 补位、SSE 超时、五种翻车口述。

## 52. 迁移 Job 与 init 容器模式

推荐：**Helm hook Job** 或 K8s `Job` 跑 alembic，完成后再 `Deployment` 起 api。反模式：api 进程内迁移 + readiness 查同一 PG 锁。

## 53. 多副本 ready 风暴

十副本同时 ready 查 Chroma——考虑 **共享缓存** 或 **抖动 periodSeconds**，避免 thundering herd。Chroma 小集群尤其敏感。

## 54. 与 [134] WebSocket

WebSocket 升级探针与 HTTP readiness **同端口**；注意 nginx `proxy_http_version 1.1` 与 Upgrade 头。断连排障先查 ingress 超时再查 ready。

## 55. 阶段 5 与 Langfuse

Langfuse 挂不影响 ready（软依赖）。trace 失败单独告警，不与 `rag_ready` 混淆。
"""),
"208.refine-summarization-tutorial.md": ("V10-208", "## 33. 补充\n\nRefine checkpoint 文件名建议含 `doc_id` 与 `content_hash`（[49 增量](49.incremental-update-tutorial.md)），避免续跑错文档。"),
"209.raptor-hierarchical-retrieval-tutorial.md": ("V10-209", """
## 35. RAPTOR ADR 模板

**背景**：库规模、问法分布。**决策**：k、L_max、是否 Adaptive。**后果**：构建 token、存储 GB、Recall 变化。**复审日**：季度。

## 36. 叶层永不删除

即使上层摘要再全，**叶 chunk 检索** 仍保留数字题能力——RAPTOR 是增强不是替代。
"""),
"210.multimodal-rag-tutorial.md": ("V10-210", """
## 46. 多模态术语双轨

| 中文 | English | 场景 |
|------|---------|------|
| 光栅化 | rasterize | PDF→PNG |
| 双通道 | dual channel | 文本+图 |
| 版式路由 | layout router | L2/L3 |

## 47. 210 篇结业

四能力：决策树、α 打分、安全清单、金标 A/B——签字进入 [211 ColPali](211.colpali-rag-tutorial.md) 了解篇。
"""),
"211.colpali-rag-tutorial.md": ("V10-211", """
## 46. ColPali 术语双轨

| 中文 | English | 说明 |
|------|---------|------|
| 晚交互 | late interaction | MaxSim |
| 粗筛 | coarse retrieve | BM25/bi-encoder |
| 精排 | rerank pages | GPU ColPali |

## 47. 228 条了解篇签字

五口述：MaxSim、对比 CLIP、粗精两阶段、索引倍数、拒绝全库 ColPali——签字回 [210 多模态总线](210.multimodal-rag-tutorial.md)。
"""),
}

if __name__ == "__main__":
    for f, (tag, blk) in V10.items():
        p = ROOT / f
        print(f"{f}: {ins(p, tag, blk)} need={max(0,5000-ch(p.read_text(encoding='utf-8')))}")
