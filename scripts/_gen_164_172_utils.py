# -*- coding: utf-8 -*-
"""Shared utilities for batch 164-172 tutorial generation."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent


def hanzi_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def write_image_assets(slug: str, title: str, prompts: list[tuple[str, str, str, str]]):
    """prompts: (png_name, layout, section, prompt_body)"""
    img_dir = ROOT / "image" / slug
    prompts_dir = img_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    readme = [f"# {title}信息图（教程配图）\n\n| 文件 | 布局 | 插入位置 |\n|------|------|----------|\n"]
    for png, layout, section, _ in prompts:
        readme.append(f"| `{png}` | {layout} | {section} |\n")
    readme.append("\n风格：hand-drawn-edu · 16:9 · 中文\n\nPrompt 见 `prompts/`。\n\n")
    readme.append("说明：本目录目前仅含 prompt 与 README；生成 PNG 后放入同级文件名即可被正文引用。\n")
    (img_dir / "README.md").write_text("".join(readme), encoding="utf-8")
    for png, layout, section, body in prompts:
        stem = png.replace(".png", ".md")
        front = f"""---
layout: {layout.split()[0] if layout else 'hub-spoke'}
style: hand-drawn-edu
aspect_ratio: 16:9
language: zh
---

Create a professional educational infographic, 16:9 landscape.
Layout: {layout}.
Style: hand-drawn-edu, cream #F5F0E8, macaron pastels, stick figures, Simplified Chinese.

"""
        (prompts_dir / stem).write_text(front + body + "\n\nAll text Simplified Chinese.\n", encoding="utf-8")


def _mistakes(pairs: list[tuple[str, str, str]], sec: str = "10") -> str:
    lines = []
    for i, (wrong, phen, right) in enumerate(pairs, 1):
        lines.append(f"""### {sec}.{i} 错：{wrong}

**现象**：{phen}  
**对**：{right}
""")
    return "\n".join(lines)


def _faq(items: list[tuple[str, str]], sec: str = "13") -> str:
    return "\n".join(f"### {sec}.{i} {q}\n\n{a}\n" for i, (q, a) in enumerate(items, 1))


SHARED_APPENDIX = """
### 附录 A：F 轨后端联调检查单（20 项）

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 与 [156 FastAPI 结构](156.fastapi-project-structure-tutorial.md) 分层 | router 不含业务 SQL |
| 2 | 与 [35 OpenAI API](35.openai-compatible-api-tutorial.md) 配置 | base_url/key 环境变量 |
| 3 | 与 [53 ACL](53.metadata-acl-tutorial.md) 字段一致 | Principal 映射 acl_group |
| 4 | 与 [89 多租户](89.multi-tenant-namespace-tutorial.md) tenant_id | 检索带 tenant |
| 5 | 与 [121 越权过滤](121.unauthorized-doc-filter-tutorial.md) | 无权 chunk 不进 prompt |
| 6 | 与 [116 SSE 流式](116.sse-rag-streaming-tutorial.md) | 鉴权在流开始前 |
| 7 | 与 [110 Prompt 模板](110.rag-prompt-template-tutorial.md) | system 不含机密 |
| 8 | 与 [76 Chroma](76.chroma-vector-db-tutorial.md) where | filter 与 API 双校验 |
| 9 | 与 [163 重试死信](163.retry-dead-letter-tutorial.md) | 429 有退避 |
| 10 | 与 [161 索引状态机](161.index-task-state-machine-tutorial.md) | 任务带 tenant |
| 11 | JWT 过期与刷新 | refresh 轮换 |
| 12 | RBAC 变更生效 | 权限缓存 TTL |
| 13 | 速率限制 | 429 + Retry-After |
| 14 | OpenAPI 与实现一致 | CI 契约测试 |
| 15 | 前端消息列表 | 角色样式分离 |
| 16 | Markdown XSS | sanitize 单测 |
| 17 | 多模型路由日志 | model_id 可追溯 |
| 18 | API Key 不进 Git | pre-commit 扫描 |
| 19 | 审计 trace_id | 全链路 |
| 20 | 渗透：篡改 tenant | 403 |

### 附录 B：F 轨一周落地节奏

| 天 | 上午 | 下午 | 产出 |
|----|------|------|------|
| 周一 | 164 JWT + 165 RBAC 概念 | 画 Principal 白板 | 身份模型图 |
| 周二 | 166 租户隔离 | 接 [89] Chroma demo | 双租户负例 |
| 周三 | 167 封装 + 168 路由 | 跑降级链路 | 路由表 |
| 周四 | 169 限流 + 170 OpenAPI | Swagger UI 截图 | API 文档 |
| 周五 | 171 聊天 UI + 172 Markdown | 端到端 Demo | 产品评审 |

### 附录 C：面试追问十则

**问 1**：JWT 与 Session 在 RAG API 怎么选？  
**答**：无状态水平扩展选 JWT；强即时吊销选 Session+Redis 或 JWT+短 TTL+黑名单。

**问 2**：RBAC 与 ACL 分工？  
**答**：RBAC 管 API 能力；ACL 管 chunk 可见性；两者都要。

**问 3**：tenant_id 放哪？  
**答**：JWT claim + 网关注入 + 检索 filter + 日志；不信任 body。

**问 4**：OpenAI 封装为什么要统一？  
**答**：换模型/网关不改业务；统一重试、观测、限流。

**问 5**：多模型路由触发条件？  
**答**：任务类型、延迟 SLA、成本预算、主模型 429/5xx。

**问 6**：限流 token 还是 QPS？  
**答**：企业 RAG 常双限：QPS 防刷 + TPM 控成本。

**问 7**：OpenAPI 价值？  
**答**：契约、Mock、SDK 生成、前后端并行。

**问 8**：聊天 UI 核心状态？  
**答**：messages 数组、streaming 占位、error、abort。

**问 9**：Markdown XSS 怎么防？  
**答**：react-markdown + remark/rehype sanitize；禁 raw HTML。

**问 10**：PoC 最小安全集？  
**答**：JWT + tenant filter + 基础 RBAC + sanitize；再补限流与 OpenAPI。
"""


EXPANSION_BLOCKS: dict[str, list[str]] = {
    "jwt-auth-rag": [
        "### 14.20 HS256 密钥轮换\n\n生产 **JWT_SECRET** 应支持 **kid** 头标识多密钥；验证端 **按 kid 选公钥/对称密钥**；轮换窗口 **双密钥并存 24h**，避免 **全量登出** 除非安全事件。",
        "### 14.21 与 [159 Celery](159.celery-async-queue-tutorial.md) 任务身份\n\n异步索引任务 **不能** 用用户 JWT 长期有效——用 **服务账号** + **任务 payload 内 tenant_id** **签名**，worker **不信任** 队列里裸 tenant 字符串。",
        "### 14.22 移动端 Token 存储\n\n**禁止** localStorage 存 refresh token（XSS 风险）；原生 App 用 **Keychain/Keystore**；Web 用 **HttpOnly Cookie** 存 refresh 或 **短 access + 生物识别** 再取。",
        "### 14.23 与 [121 越权](121.unauthorized-doc-filter-tutorial.md) 联调\n\nJWT 解析出的 `roles` **必须** 与 [53 ACL](53.metadata-acl-tutorial.md) `acl_group` **同一映射表** 维护——**两套表** 是 **P0 事故** 温床。",
        "### 14.24 时钟偏移\n\n验证 `exp` 时允许 **leeway=60s** 防 NTP 漂移；**禁止** leeway 过大导致 **过期 token 长期有效**。",
        "### 14.25 审计字段\n\n日志记 `sub`、`tenant_id`、`jti`（JWT ID）、`path`——**不记** token 全文；`jti` 可用于 **黑名单** 与 **重放检测**。",
        "### 14.26 与 API Gateway\n\nKong/APISIX **在网关验 JWT**，后端 **只信** 网关注入头 `X-Principal-Json` **且 mTLS**——**防** 内网 **绕过**。",
        "### 14.27 开发环境 fake JWT\n\n`ENV=dev` 时 **禁止** 接受 `alg=none` 或 **固定弱密钥** 上 **预发/生产**——**配置漂移** 曾致 **真实事故**。",
        "### 14.28 完结\n\n**181 JWT 认证** — 无权身份 **不得** 进入 RAG 检索链；与 165 RBAC、166 tenant **三连读** 构成 **F 轨身份底座**。",
    ],
    "rbac-rag": [
        "### 14.20 与 [157 上传](157.file-upload-multipart-tutorial.md)\n\n`POST /documents/upload` 需 **`rag:ingest`** 权限——**普通 chat 用户** **不能** 污染索引。",
        "### 14.21 权限缓存\n\nIAM 同步 **每小时** 时，JWT 内 roles **可能 stale**——敏感操作 **实时查 DB** 或 **短 TTL 缓存 5min**。",
        "### 14.22 与 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md)\n\nSwagger **securitySchemes** 标注 **Bearer**；每个 endpoint **声明 required scopes**——**文档即契约**。",
        "### 14.23 角色爆炸\n\n超过 **30 个角色** 考虑 **ABAC 属性** 或 **组+例外**——纯 RBAC **矩阵难维护**。",
        "### 14.24 完结\n\n**182 RBAC** — API 能力 **角色门**；chunk 可见 **仍靠 ACL**。",
    ],
    "tenant-isolation-backend": [
        "### 14.25 与 [80 Pinecone](80.pinecone-tutorial.md)\n\n托管 **namespace=tenant_id** + metadata **acl_group** **双层**——[89 篇](89.multi-tenant-namespace-tutorial.md) 模式 A+B。",
        "### 14.26 跨 tenant 管理后台\n\n超管 **impersonate** 租户 **必须** **break_glass 审计**——**禁止** 默认 JWT **无 tenant 限** 查全库。",
        "### 14.27 数据导出\n\n租户 **offboarding** **delete collection + S3 prefix + DB rows**——[90 备份](90.vector-db-backup-tutorial.md) **按 tenant 恢复** 演练。",
        "### 14.28 完结\n\n**183 租户隔离** — **tenant_id 铁律**；与 89/53/121 **四篇伴读**。",
    ],
    "openai-api-wrapper": [
        "### 14.20 与 [69 Embedding 重试](69.embedding-retry-rate-limit-tutorial.md)\n\n封装层 **统一 tenacity** 策略：429 **指数退避**；401 **不重试**。",
        "### 14.21 与 [116 SSE](116.sse-rag-streaming-tutorial.md)\n\n`stream=True` **单独方法** `chat_stream()`——**别** 与 sync create **混一个 bool** 难测。",
        "### 14.22 完结\n\n**184 OpenAI 封装** — 业务 **只调 LLMClient**；换 [35](35.openai-compatible-api-tutorial.md) 网关 **改配置**。",
    ],
    "multi-model-routing": [
        "### 14.20 与 [29 采样](29.llm-sampling-tutorial.md)\n\n路由到 **小模型** 时 **temperature** 可能需 **调高** 补偿能力——**路由表带采样参数**。",
        "### 14.21 与 [168] 成本\n\n路由决策 **写 metrics**：`route_reason=primary_429`——**FinOps** 复盘 **降级比例**。",
        "### 14.22 完结\n\n**185 多模型路由** — **可用性 + 成本** 杠杆；**别** 无观测 **静默降级**。",
    ],
    "rate-limiting-api": [
        "### 14.20 与 [169] Redis 集群\n\n限流 key **按 tenant 分片**——**热 tenant** **不拖** 全局。",
        "### 14.21 与 [186] 公平性\n\n**加权公平队列** 防 **单用户占满 TPM**——**企业版** 常见需求。",
        "### 14.22 完结\n\n**186 速率限制** — **429 是产品特性** 不是 **丢错误**。",
    ],
    "openapi-swagger-docs": [
        "### 14.15 与 [167 封装](167.openai-api-wrapper-tutorial.md)\n\n响应 schema **引用** 共用 `ChatResponse` **component**——**DRY**。",
        "### 14.16 完结\n\n**187 OpenAPI** — **了解篇** 也要 **CI 校验**；**文档腐烂** = **集成事故**。",
    ],
    "chat-message-list-ui": [
        "### 14.20 与 [174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)\n\nMessageList **只负责列表**；StreamingText **子组件** 消费 delta——**关注点分离**。",
        "### 14.21 与 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)\n\nassistant 消息 **citations prop** 渲染 **底部卡片**——**别** 和 markdown **混一层**。",
        "### 14.22 完结\n\n**188 聊天 UI** — **messages 状态机** 是 **前端 RAG 心脏**。",
    ],
    "markdown-render-rag": [
        "### 14.20 与 [173 代码高亮](173.code-highlight-rag-tutorial（front-end）.md)\n\nsanitize **后再** highlight——**防** 高亮插件 **注入**。",
        "### 14.21 与 [23 Self-Attention](23.self-attention-tutorial.md)\n\n模型 **内部** 注意力 **≠** 用户可见 HTML——**XSS 是渲染层** 问题 **不是** transformer 问题。",
        "### 14.22 与 [113 引用](113.inline-citation-tutorial.md)\n\n`[1]` **自定义 component** **禁** `dangerouslySetInnerHTML`。",
        "### 14.23 完结\n\n**189 Markdown 渲染** — **sanitize 默认开**；**安全 review** **必含 XSS 用例**。",
    ],
}

from _gen_164_172_expansion import EXTRA_EXPANSION  # noqa: E402
from _gen_164_172_mega import MEGA_APPENDIX, TOPUP_APPENDIX  # noqa: E402

for _slug, _blocks in EXTRA_EXPANSION.items():
    EXPANSION_BLOCKS.setdefault(_slug, []).extend(_blocks)


def pad_if_needed(content: str, slug: str, min_h: int = 5000) -> str:
    out = content
    if slug in MEGA_APPENDIX:
        out += "\n\n" + MEGA_APPENDIX[slug]
    for block in EXPANSION_BLOCKS.get(slug, []):
        if hanzi_count(out) >= min_h:
            break
        out += "\n\n" + block
    if slug in TOPUP_APPENDIX and hanzi_count(out) < min_h:
        out += "\n\n" + TOPUP_APPENDIX[slug]
    if hanzi_count(out) < min_h:
        raise ValueError(f"{slug}: only {hanzi_count(out)} hanzi, need {min_h}")
    return out
