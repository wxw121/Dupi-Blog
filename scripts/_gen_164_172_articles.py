# -*- coding: utf-8 -*-
"""Article builders 165-172 for batch 164-172."""
from _gen_164_172_utils import SHARED_APPENDIX, _faq, _mistakes

IMAGE_SPECS = {
    "jwt-auth-rag": {
        "title": "JWT 认证 RAG",
        "prompts": [
            ("01-jwt-flow.png", "hub-spoke", "§3 JWT 是什么", """Title: JWT 认证 RAG 流程

Center hub: 验签 JWT → Principal

Spoke 1: 登录
- 用户名密码
- 签发 access/refresh

Spoke 2: 请求 API
- Authorization Bearer
- FastAPI Depends

Spoke 3: RAG 链路
- tenant + ACL filter
- 检索 → 生成

Spoke 4: 安全
- 短 access
- 不信 body user_id

Footer: JWT 认证 RAG · §3"""),
            ("02-fastapi-deps.png", "flowchart", "§6 FastAPI 依赖注入", """Title: FastAPI JWT 依赖注入

Flow: HTTP Bearer → decode_token → Principal → RBAC → build_filter → retriever

Footer: JWT 认证 · §6"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: JWT RAG 概念地图

Blocks: JWT / Claims / Principal / RBAC / ACL filter / Chroma where

Footer: JWT 认证概念地图 · §11"""),
        ],
    },
    "rbac-rag": {
        "title": "RBAC 角色权限",
        "prompts": [
            ("01-rbac-idea.png", "hub-spoke", "§3 RBAC 是什么", """Title: RAG 里的 RBAC 是什么？

Center: 角色 → 权限 → API 端点

Spoke 1: 角色 employee/admin
Spoke 2: 权限 rag:chat rag:ingest
Spoke 3: 与 ACL 分工
Spoke 4: FastAPI Depends require_role

Footer: RBAC RAG · §3"""),
            ("02-permission-matrix.png", "comparison-matrix", "§5 权限矩阵", """Title: 角色权限矩阵

Rows: guest employee finance admin
Cols: chat ingest delete index admin

Footer: RBAC · §5"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: RBAC 概念地图

Blocks: Role / Permission / Endpoint / JWT claims / ACL 区别

Footer: RBAC 概念地图 · §11"""),
        ],
    },
    "tenant-isolation-backend": {
        "title": "多租户后端隔离",
        "prompts": [
            ("01-tenant-flow.png", "flowchart", "§3 租户隔离", """Title: tenant_id 注入与隔离

Flow: JWT tenant_id → 网关 → API → 向量库 where/namespace

Footer: 租户隔离 · §3"""),
            ("02-isolation-modes.png", "comparison-matrix", "§4 隔离模式", """Title: 四种隔离模式对照

Modes: metadata filter / namespace / collection / 独立库

Footer: 租户隔离 · §4"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: 租户隔离概念地图

Links: 89 namespace / 53 ACL / 121 filter

Footer: 租户隔离概念地图 · §11"""),
        ],
    },
    "openai-api-wrapper": {
        "title": "OpenAI 兼容封装",
        "prompts": [
            ("01-wrapper-layers.png", "hierarchical-tree", "§3 封装分层", """Title: LLMClient 封装分层

Layers: 业务 / LLMClient / openai SDK / 网关

Footer: OpenAI 封装 · §3"""),
            ("02-chat-vs-embed.png", "comparison-matrix", "§4 chat vs embed", """Title: chat 与 embeddings 分离

Footer: OpenAI 封装 · §4"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: API 封装概念地图

Link: 35 OpenAI 兼容

Footer: 封装概念地图 · §11"""),
        ],
    },
    "multi-model-routing": {
        "title": "多模型路由",
        "prompts": [
            ("01-routing-flow.png", "flowchart", "§3 路由流程", """Title: 多模型路由与降级

Primary fail → fallback → 本地小模型

Footer: 多模型路由 · §3"""),
            ("02-routing-rules.png", "comparison-matrix", "§5 路由规则", """Title: 按任务/成本/SLA 路由

Footer: 多模型路由 · §5"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: 路由概念地图

Footer: 多模型路由 · §11"""),
        ],
    },
    "rate-limiting-api": {
        "title": "API 速率限制",
        "prompts": [
            ("01-rate-limit-idea.png", "hub-spoke", "§3 限流是什么", """Title: RAG API 速率限制

Center: 令牌桶 / 滑动窗口

Spoke 1: QPS 防刷
Spoke 2: TPM 控成本
Spoke 3: 429 Retry-After
Spoke 4: 按 tenant 配额

Footer: 速率限制 · §3"""),
            ("02-token-bucket.png", "flowchart", "§4 令牌桶", """Title: 令牌桶算法

Footer: 速率限制 · §4"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: 限流概念地图

Footer: 速率限制 · §11"""),
        ],
    },
    "openapi-swagger-docs": {
        "title": "OpenAPI Swagger",
        "prompts": [
            ("01-openapi-flow.png", "flowchart", "§3 OpenAPI 价值", """Title: OpenAPI 在 RAG 项目中的位置

Contract / Swagger UI / SDK / Mock

Footer: OpenAPI · §3"""),
            ("02-schema-example.png", "hierarchical-tree", "§5 Schema 设计", """Title: ChatRequest ChatResponse Schema

Footer: OpenAPI · §5"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: OpenAPI 概念地图

Footer: OpenAPI · §11"""),
        ],
    },
    "chat-message-list-ui": {
        "title": "聊天消息列表 UI",
        "prompts": [
            ("01-message-list.png", "hub-spoke", "§3 消息列表", """Title: 聊天消息列表组件

Center: messages 数组状态

Spoke 1: user / assistant / system
Spoke 2: streaming 占位
Spoke 3: error / retry
Spoke 4: scroll 到底

Footer: 聊天 UI · §3"""),
            ("02-react-structure.png", "hierarchical-tree", "§6 React 结构", """Title: Next.js 组件树

MessageList / MessageBubble / ChatInput

Footer: 聊天 UI · §6"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: 聊天 UI 概念地图

Footer: 聊天 UI · §11"""),
        ],
    },
    "markdown-render-rag": {
        "title": "Markdown 安全渲染",
        "prompts": [
            ("01-markdown-pipeline.png", "flowchart", "§3 渲染管线", """Title: RAG Markdown 渲染管线

LLM markdown → react-markdown → sanitize → DOM

Footer: Markdown 渲染 · §3"""),
            ("02-xss-attack.png", "comparison-matrix", "§5 XSS 对照", """Title: 安全 vs 不安全渲染

dangerouslySetInnerHTML vs sanitize

Footer: Markdown XSS · §5"""),
            ("03-concept-map.png", "bento-grid", "§11 概念地图", """Title: Markdown 概念地图

Link: 23 注意力 ≠ XSS

Footer: Markdown 概念地图 · §11"""),
        ],
    },
}


def build_165() -> str:
    mistakes = _mistakes([
        ("只有 admin/user 两角色", "finance 文档无法细粒度。", "roles + groups；API 用 roles，检索用 groups/ACL。"),
        ("RBAC 替代 ACL", "有 chat 权限仍看到机密 chunk。", "RBAC 管接口；[53] ACL 管 chunk。"),
        ("权限写死在 if username", "难维护、易漏。", "集中 PERMISSIONS 表 + Depends。"),
        ("前端隐藏按钮=安全", "直接 curl API 绕过。", "后端 require_permission 必检。"),
        ("JWT roles 永不过期", "离职员工仍可 ingest。", "IAM 同步 + 短 TTL + 敏感操作实时查。"),
    ], "10")
    faq = _faq([
        ("RBAC 和 ABAC 怎么选？", "PoC 用 RBAC；细粒度资源权限再上 ABAC 属性。"),
        ("ingest 谁有权？", "通常 admin 或 rag:ingest；普通 user 仅 chat。"),
        ("多租户 admin？", "tenant_admin 仅本 tenant；platform_admin 另角色且审计。"),
        ("与 OAuth scope 关系？", "OIDC scope 可映射到内部 permission 字符串。"),
        ("如何测试 RBAC？", "矩阵测试：每角色调每 endpoint，期望 200/403。"),
        ("Casbin 必要吗？", "小项目 Depends 够用；规则复杂再 Casbin/OPA。"),
    ], "14")
    return f'''# F 后端与 API（十）：RBAC 角色权限 RAG 完全指南

> [164 JWT](164.jwt-auth-rag-tutorial.md) 解决了 **身份从哪来**——验签后你有 `Principal`。但 **所有登录用户都能重建索引吗？** 都能调管理接口吗？**RBAC**（Role-Based Access Control，基于角色的访问控制）用 **角色→权限→API** 映射，在 **进 RAG 链路之前** 拦住 **无权的 HTTP 动作**。注意：RBAC **不管** chunk 能不能被搜到——那是 [53 ACL](53.metadata-acl-tutorial.md) 与 [121 越权过滤](121.unauthorized-doc-filter-tutorial.md) 的事。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F 轨地基篇**（路线图第 **182** 条）。前置：[164 JWT](164.jwt-auth-rag-tutorial.md)；配合 [166 租户](166.tenant-isolation-backend-tutorial.md)。

---

## 目录

1. [前言：JWT 之后还要问「能做什么」](#1-前言jwt-之后还要问能做什么)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [RBAC 是什么](#3-rbac-是什么)
4. [角色、权限、资源](#4-角色权限资源)
5. [RAG API 权限矩阵](#5-rag-api-权限矩阵)
6. [FastAPI require_role 实现](#6-fastapi-require_role-实现)
7. [与 ACL 的分工](#7-与-acl-的分工)
8. [权限变更与缓存](#8-权限变更与缓存)
9. [综合实战：RBAC 保护 ingest 与 admin](#9-综合实战rbac-保护-ingest-与-admin)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：JWT 之后还要问「能做什么」

典型企业 RAG 接口：

| 端点 | 风险 |
|------|------|
| POST /rag/chat | 中——需登录，仍可能越权 chunk |
| POST /rag/ingest | **高**——污染索引、投毒 |
| DELETE /documents/{{id}} | **高**——删库 |
| GET /admin/metrics | 中——泄露用量 |

**RBAC**：用户绑定 **角色**，角色绑定 **权限**（如 `rag:chat`），API 处理函数 **声明所需权限**。  
通俗说：**工牌上的「部门」决定你能进哪些门**——进不了机房，但进了办公区 **仍不能** 随便翻财务柜（ACL）。

**读完本文，你应该能做到：**

1. 设计 RAG **权限字符串** 命名（`rag:chat`、`rag:ingest`）。  
2. FastAPI **Depends** 实现 `require_permission("rag:ingest")`。  
3. 画 **RBAC vs ACL** 分工图。  
4. 写 **角色×端点** 测试矩阵。  
5. 跑通 §9：**employee 403 on ingest**。

---

## 2. 本文边界与动手路径

**档位：F 轨地基篇（182）。**

**本文讲：** RBAC 模型、权限矩阵、FastAPI 集成、与 ACL 分工。  
**本文不讲：** Casbin 全语法、LDAP 同步、细粒度 ABAC。

**环境：** 延续 [164](164.jwt-auth-rag-tutorial.md) JWT 项目。

---

## 3. RBAC 是什么

![RBAC 是什么](image/rbac-rag/01-rbac-idea.png)

```text
User ──has──▶ Role ──grants──▶ Permission ──protects──▶ API Endpoint
```

与 JWT：token 里带 `roles: ["employee"]`；服务端查 **ROLE_PERMISSIONS** 表。

---

## 4. 角色、权限、资源

```python
PERMISSIONS = {{
    "user": ["rag:chat", "rag:history:read"],
    "editor": ["rag:chat", "rag:ingest", "rag:doc:read"],
    "admin": ["rag:*"],
}}

ROLE_ALIASES = {{
    "employee": "user",
    "kb_editor": "editor",
    "tenant_admin": "admin",
}}
```

**权限命名**：`资源:动作`；通配 `rag:*` 仅 **tenant_admin** 慎用且 **审计**。

---

## 5. RAG API 权限矩阵

![权限矩阵](image/rbac-rag/02-permission-matrix.png)

| 端点 | user | editor | admin |
|------|------|--------|-------|
| POST /rag/chat | ✓ | ✓ | ✓ |
| POST /rag/ingest | ✗ | ✓ | ✓ |
| DELETE /rag/doc/{{id}} | ✗ | ✗ | ✓ |
| GET /admin/stats | ✗ | ✗ | ✓ |

**chat 允许 ≠ 能看 finance chunk**——检索仍走 [121](121.unauthorized-doc-filter-tutorial.md)。

---

## 6. FastAPI require_role 实现

```python
def require_permission(*needed: str):
    def checker(user: Principal = Depends(get_current_user)):
        perms = set()
        for role in user.roles:
            perms.update(PERMISSIONS.get(role, []))
        if "rag:*" in perms:
            return user
        for p in needed:
            if p not in perms:
                raise HTTPException(403, f"Missing permission: {{p}}")
        return user
    return checker

@router.post("/rag/ingest")
async def ingest(
    file: UploadFile,
    user: Principal = Depends(require_permission("rag:ingest")),
):
    ...
```

---

## 7. 与 ACL 的分工

| 层 | 机制 | 保护对象 |
|----|------|----------|
| RBAC | 角色/权限 | HTTP API |
| ACL | acl_group / tenant | chunk 内容 |
| 网关 | JWT 验签 | 身份 |

```text
Request → JWT → RBAC（能否 chat）→ 检索 ACL（哪些 chunk）→ LLM
```

[53 篇](53.metadata-acl-tutorial.md) 设计 metadata；[165 本篇] 设计 **谁能触发 ingest**。

---

## 8. 权限变更与缓存

HR 离职 → IAM webhook → 撤销角色 → **可选** JWT 黑名单至 access 过期。  
**敏感权限**（ingest、delete）：**实时查 DB** 而非只信 token 内 roles。

---

## 9. 综合实战：RBAC 保护 ingest 与 admin

```python
@pytest.mark.parametrize("role,endpoint,status", [
    ("user", "/rag/chat", 200),
    ("user", "/rag/ingest", 403),
    ("editor", "/rag/ingest", 200),
])
def test_rbac(client, role, endpoint, status):
    token = mint_token(roles=[role])
    r = client.post(endpoint, headers={{"Authorization": f"Bearer {{token}}"}}, json={{...}})
    assert r.status_code == status
```

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![RBAC 概念地图](image/rbac-rag/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **RBAC 管 API 动作**；**ACL 管 chunk 可见**。  
2. **后端强制**；前端隐藏按钮 **不是安全**。  
3. 下一篇 [166 租户隔离](166.tenant-isolation-backend-tutorial.md) 在 **身份+角色** 之上加 **tenant_id 硬边界**。

{SHARED_APPENDIX}
'''


def build_166() -> str:
    mistakes = _mistakes([
        ("tenant_id 只在前端", "改 body 查别家数据。", "JWT claim + 服务端强制 filter。"),
        ("以为分 collection 就不用 ACL", "同 tenant 内 HR 机密仍泄露。", "namespace + acl_group 双层。"),
        ("ingest 不写 tenant metadata", "检索 filter 漏数据。", "入库强制 tenant_id 字段。"),
        ("日志不带 tenant", "串库事故无法溯源。", "trace 必含 tenant_id。"),
        ("测试库与生产共 collection", "测试数据进生产检索。", "环境×租户隔离目录。"),
    ], "10")
    faq = _faq([
        ("tenant_id 放 JWT 还是 header？", "JWT claim 为主；网关注入 X-Tenant-Id 需 mTLS 防伪造。"),
        ("与 [89 namespace](89.multi-tenant-namespace-tutorial.md) 关系？", "89 讲向量库模式；本篇讲后端全链路注入。"),
        ("与 [121 越权](121.unauthorized-doc-filter-tutorial.md)？", "121 管组级 ACL；166 管 tenant 硬边界；filter 要 AND。"),
        ("B2B 子账号？", "sub-tenant 用 org_id 扩展 claim；filter 仍强制。"),
        ("跨 tenant 搜索？", "platform 功能单独 role + break_glass 审计。"),
    ], "14")
    return f'''# F 后端与 API（十一）：多租户 tenant_id 后端隔离完全指南

> SaaS 知识库 **租户 A 绝不能检索租户 B 的 chunk**——这是 **P0 数据泄露**。[89 多租户 Namespace](89.multi-tenant-namespace-tutorial.md) 讲了 **向量库层** 四种隔离；[53 ACL](53.metadata-acl-tutorial.md) 讲了 **组级权限**；[121 越权过滤](121.unauthorized-doc-filter-tutorial.md) 讲了 **C6 硬闸**。本篇把 **tenant_id** 从 [164 JWT](164.jwt-auth-rag-tutorial.md) **贯穿后端全链路**：API、ingest、队列 [159 Celery](159.celery-async-queue-tutorial.md)、检索、日志。路线图 **183**，**F 轨地基篇**。

---

## 目录

1. [前言：tenant_id 是 SaaS RAG 的生命线](#1-前言tenant_id-是-saas-rag-的生命线)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [后端租户隔离是什么](#3-后端租户隔离是什么)
4. [四种隔离模式再对照](#4-四种隔离模式再对照)
5. [JWT → 网关 → 服务注入](#5-jwt--网关--服务注入)
6. [Ingest 与异步任务的 tenant](#6-ingest-与异步任务的-tenant)
7. [检索 filter 与 [89][121][53] 组合](#7-检索-filter-与-89121153-组合)
8. [数据库与对象存储隔离](#8-数据库与对象存储隔离)
9. [综合实战：双 tenant Mini-RAG API](#9-综合实战双-tenant-mini-rag-api)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：tenant_id 是 SaaS RAG 的生命线

[89 篇](89.multi-tenant-namespace-tutorial.md) 开场：**串库 = 合规事故**。后端若 **不统一注入 tenant_id**，会出现：

- ingest 把 A 公司文档 **写入默认 collection**；  
- Celery worker **用错 tenant** 重建索引；  
- 管理员 SQL **少写 WHERE tenant_id**。

**Tenant isolation（租户隔离）**：每个请求携带 **不可伪造的 tenant_id**，**所有读写** 带 tenant 边界。  
通俗说：**大楼分户**——不仅房间（ACL）上锁，**整栋楼** 也要 **对号入座**。

**读完本文，你应该能做到：**

1. 对照 [89](89.multi-tenant-namespace-tutorial.md) 选型 **metadata / namespace / 分库**。  
2. 实现 **Principal.tenant_id → build_filter**。  
3. ingest / 任务队列 **强制 tenant** 传递。  
4. 写 **跨 tenant 负例** 测试。  
5. 组合 **tenant AND acl_group**（[53](53.metadata-acl-tutorial.md)、[121](121.unauthorized-doc-filter-tutorial.md)）。

---

## 2. 本文边界与动手路径

**档位：F 轨地基篇（183）。**  
**前置**：[164 JWT](164.jwt-auth-rag-tutorial.md)、[89 多租户](89.multi-tenant-namespace-tutorial.md)、[53 ACL](53.metadata-acl-tutorial.md)、[121 越权](121.unauthorized-doc-filter-tutorial.md)。

---

## 3. 后端租户隔离是什么

![tenant 隔离流程](image/tenant-isolation-backend/01-tenant-flow.png)

```text
JWT.tenant_id → ContextVar / request.state.tenant
    → ORM: WHERE tenant_id = ?
    → S3: prefix tenants/{{id}}/
    → Vector: where tenant_id OR namespace={{id}}
    → Log: tenant_id field
```

**绝不信任** `body.tenant_id` 或 query string **覆盖** JWT。

---

## 4. 四种隔离模式再对照

![隔离模式](image/tenant-isolation-backend/02-isolation-modes.png)

| 模式 | 强度 | 运维 | 与 [89] |
|------|------|------|---------|
| metadata filter | 中 | 低 | 模式 A |
| namespace/collection | 高 | 中 | 模式 B |
| 独立库实例 | 很高 | 高 | 模式 C/D |

**推荐 SaaS 默认**：**namespace=tenant_id** + metadata **acl_group**（[53](53.metadata-acl-tutorial.md)）+ API **双校验**（[121](121.unauthorized-doc-filter-tutorial.md)）。

---

## 5. JWT → 网关 → 服务注入

```python
# middleware.py
from contextvars import ContextVar
current_tenant: ContextVar[str] = ContextVar("tenant")

@app.middleware("http")
async def tenant_middleware(request, request_call_next):
    user = await optional_jwt(request)
    if user:
        current_tenant.set(user.tenant_id)
        request.state.tenant_id = user.tenant_id
    return await request_call_next(request)
```

Kong/APISIX：**JWT 插件** 验签后注入 `X-Tenant-Id`；内网服务 **只信 mTLS 网关**。

---

## 6. Ingest 与异步任务的 tenant

[157 上传](157.file-upload-multipart-tutorial.md) + [159 Celery](159.celery-async-queue-tutorial.md)：

```python
@router.post("/rag/ingest")
async def ingest(file: UploadFile, user: Principal = Depends(...)):
    task = index_document.delay(
        tenant_id=user.tenant_id,  # 来自 JWT
        doc_bytes=await file.read(),
        filename=file.filename,
    )
```

Worker **禁止** 从 **未签名 payload** 取 tenant；任务消息 **HMAC 签名**。

[161 索引状态机](161.index-task-state-machine-tutorial.md) 状态记录 **tenant_id**，防 **UI 串任务**。

---

## 7. 检索 filter 与 [89][121][53] 组合

```python
def build_tenant_acl_filter(p: Principal) -> dict:
    return {{
        "$and": [
            {{"tenant_id": p.tenant_id}},  # 166 硬边界
            {{"acl_group": {{"$in": p.groups}}}},  # 53/121
        ]
    }}
```

[121 篇](121.unauthorized-doc-filter-tutorial.md) **Unauthorized Doc Filter** 在 **此 filter 无 hits** 时返回 **ACL_DENIED**，而非 [112 无资料](112.refusal-strategy-tutorial.md) 话术。

[89 篇](89.multi-tenant-namespace-tutorial.md) §9 **双 tenant Chroma demo** 可与此 API **共用语料** 做集成测试。

---

## 8. 数据库与对象存储隔离

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  ...
);
CREATE INDEX idx_docs_tenant ON documents(tenant_id);
-- 所有查询: WHERE tenant_id = $current
```

S3：`s3://bucket/tenants/{{tenant_id}}/raw/{{doc_id}}.pdf`  
**备份恢复** [90](90.vector-db-backup-tutorial.md) **按 tenant** 演练。

---

## 9. 综合实战：双 tenant Mini-RAG API

```python
# 两个 tenant 各 ingest 一条唯一 secret 文档
# tenant_a token 问 tenant_b secret → 必须 0 hits

def test_cross_tenant_leak():
    tok_a = login("user_a@tenant-a.com")
    tok_b = login("user_b@tenant-b.com")
    ingest(tok_a, "SECRET_A_ONLY")
    ingest(tok_b, "SECRET_B_ONLY")
    r = chat(tok_a, "SECRET_B_ONLY 内容是什么")
    assert "SECRET_B" not in r.text
    assert r.status_code in (403, 200)  # 200 时 answer 不得含 B
```

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![租户隔离概念地图](image/tenant-isolation-backend/03-concept-map.png)

| 篇 | 职责 |
|----|------|
| [89](89.multi-tenant-namespace-tutorial.md) | 向量库 namespace 模式 |
| [53](53.metadata-acl-tutorial.md) | chunk acl 字段 |
| [121](121.unauthorized-doc-filter-tutorial.md) | 检索硬闸 |
| **166 本篇** | 后端 tenant 注入全链路 |

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **tenant_id 铁律**：JWT → 全链路 → filter **AND**。  
2. **89 + 53 + 121 + 166** 四篇构成 **租户与权限闭环**。  
3. 下一篇 [167 OpenAI 封装](167.openai-api-wrapper-tutorial.md) 在 **安全身份** 之上统一 **模型调用**。

{SHARED_APPENDIX}
'''


def build_167() -> str:
    mistakes = _mistakes([
        ("chat 与 embed 共用一个 model 参数", "维度错、400 错误。", "分 chat_model / embed_model 配置。"),
        ("业务层直接 openai.Client()", "换网关改几十处。", "统一 LLMClient 门面。"),
        ("429 无限重试", "账号封禁。", "指数退避 + 上限；见 [169]。"),
        ("Key 硬编码", "Git 泄露。", "环境变量 + [164] 服务账号。"),
        ("无 timeout", "线程挂死。", "connect/read timeout 必设。"),
    ], "10")
    faq = _faq([
        ("与 [35 OpenAI 兼容](35.openai-compatible-api-tutorial.md) 区别？", "35 讲调用合同；167 讲 **服务内封装层** 与 RAG 集成。"),
        ("sync 还是 async？", "FastAPI 推荐 async client；CPU 密集 embed 可线程池。"),
        ("如何 mock 测试？", "LLMClient 接口 + FakeLLM 返回固定字符串。"),
        ("流式放哪？", "chat_stream()  yield delta；见 [116 SSE](116.sse-rag-streaming-tutorial.md)。"),
        ("多 tenant 共用 Key？", "可以；用量按 tenant 打标签计费。"),
    ], "14")
    return f'''# F 后端与 API（十二）：OpenAI 兼容 API 封装完全指南

> [35 篇](35.openai-compatible-api-tutorial.md) 教你 **怎么调** OpenAI 兼容网关：`base_url`、`chat.completions`、`embeddings` 分离。RAG 服务里会有 **十几个** 调用点——检索增强、摘要 [119](119.summary-memory-tutorial.md)、评测、路由 [168](168.multi-model-routing-tutorial.md)。若每处 **手写 Client**，换模型、加重试、加观测会 **改到崩溃**。本篇在 [164 JWT](164.jwt-auth-rag-tutorial.md) 保护下的 FastAPI 里，做 **LLMClient 统一封装**。路线图 **184**，**F 轨地基篇**。

---

## 目录

1. [前言：从脚本到可维护的 LLM 客户端](#1-前言从脚本到可维护的-llm-客户端)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [为什么要封装](#3-为什么要封装)
4. [配置：base_url、Key、双 model](#4-配置base_urlkey双-model)
5. [LLMClient 接口设计](#5-llmclient-接口设计)
6. [Chat 与 Embeddings 方法](#6-chat-与-embeddings-方法)
7. [重试、超时、错误映射](#7-重试超时错误映射)
8. [观测：trace_id 与用量日志](#8-观测trace_id-与用量日志)
9. [综合实战：RAG 服务注入 LLMClient](#9-综合实战rag-服务注入-llmclient)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：从脚本到可维护的 LLM 客户端

[35 篇](35.openai-compatible-api-tutorial.md) §10 最小封装是 **笔记本级别**。上线 RAG 还需要：

- **依赖注入**：FastAPI `Depends(get_llm_client)`；  
- **tenant 标签**：日志带 `tenant_id` [166](166.tenant-isolation-backend-tutorial.md)；  
- **与 [168 路由](168.multi-model-routing-tutorial.md) 衔接**：`chat(model=...)` 参数；  
- **与 [169 限流](169.rate-limiting-api-tutorial.md) 衔接**：429 统一处理。

**Facade（门面）**：对外简单接口，对内组合 SDK + 重试 + 日志。  
通俗说：**一个总机号**——外面只拨 10086，内部分机怎么换 **外面不知道**。

---

## 2. 本文边界与动手路径

**档位：F 轨地基篇（184）。**  
**前置**：[35 OpenAI 兼容 API](35.openai-compatible-api-tutorial.md)、[156 FastAPI 结构](156.fastapi-project-structure-tutorial.md)。

---

## 3. 为什么要封装

![封装分层](image/openai-api-wrapper/01-wrapper-layers.png)

| 不封装 | 封装后 |
|--------|--------|
| 15 处改 model 名 | 改 config 一处 |
| 重试逻辑复制 | tenacity 统一 |
| 测试难 mock | 接口 + Fake |
| 无用量统计 | 统一 hook |

---

## 4. 配置：base_url、Key、双 model

```python
# config.py
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"
    timeout_seconds: float = 60.0
    max_retries: int = 3

    class Config:
        env_file = ".env"
```

与 [35 篇](35.openai-compatible-api-tutorial.md) §4 三要素 **一一对应**；国内网关 **只改 env**。

---

## 5. LLMClient 接口设计

```python
from typing import Protocol, AsyncIterator

class LLMClient(Protocol):
    async def chat(self, messages: list[dict], *, model: str | None = None, temperature: float = 0.2) -> str: ...
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]: ...
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]: ...
```

**业务只依赖 Protocol**——测试注入 `FakeLLMClient`。

---

## 6. Chat 与 Embeddings 方法

![chat vs embed](image/openai-api-wrapper/02-chat-vs-embed.png)

```python
class OpenAILLMClient:
    def __init__(self, settings: LLMSettings):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self._s = settings

    async def chat(self, messages, *, model=None, temperature=0.2):
        resp = await self._client.chat.completions.create(
            model=model or self._s.chat_model,
            messages=messages,
            temperature=temperature,
            timeout=self._s.timeout_seconds,
        )
        return resp.choices[0].message.content or ""

    async def embed(self, texts, *, model=None):
        resp = await self._client.embeddings.create(
            model=model or self._s.embed_model,
            input=texts,
        )
        return [d.embedding for d in resp.data]
```

**切勿** 把 `embed_model` 传给 `chat.completions`——[35 篇](35.openai-compatible-api-tutorial.md) §11 经典翻车。

---

## 7. 重试、超时、错误映射

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError

@retry(retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
       wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3))
async def _create_with_retry(coro_factory):
    return await coro_factory()
```

| 错误 | 处理 |
|------|------|
| 401 | 配置错误，不重试 |
| 429 | 退避；配合 [169 限流](169.rate-limiting-api-tutorial.md) |
| 500 | 有限重试 |
| timeout | 重试 + 告警 |

---

## 8. 观测：trace_id 与用量日志

```python
logger.info("llm_chat", extra={{
    "trace_id": trace_id,
    "tenant_id": tenant_id,
    "model": model,
    "prompt_tokens": resp.usage.prompt_tokens,
    "completion_tokens": resp.usage.completion_tokens,
}})
```

对接 [147 LangSmith](147.langsmith-tracing-tutorial.md) / [148 Langfuse](148.langfuse-observability-tutorial.md) 时 **在封装层打 span** 最省事。

---

## 9. 综合实战：RAG 服务注入 LLMClient

```python
def get_llm_client() -> LLMClient:
    return OpenAILLMClient(get_settings())

@router.post("/rag/chat")
async def chat(req: ChatRequest, user: Principal = Depends(get_current_user), llm: LLMClient = Depends(get_llm_client)):
    hits = retrieve(req.question, user)
    messages = build_rag_messages(hits, req.question)  # [110]
    answer = await llm.chat(messages)
    return {{"answer": answer}}
```

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![封装概念地图](image/openai-api-wrapper/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **业务只调 LLMClient**；配置对齐 [35](35.openai-compatible-api-tutorial.md)。  
2. chat/embed **分 model**；重试/timeout **集中**。  
3. 下一篇 [168 多模型路由](168.multi-model-routing-tutorial.md) 在封装之上 **选 model**。

{SHARED_APPENDIX}
'''


def build_168() -> str:
    mistakes = _mistakes([
        ("无 fallback 单点", "主模型挂全站不可用。", "至少一条 fallback 链。"),
        ("降级无日志", "不知道多少流量走小模型。", "metrics: route_reason。"),
        ("路由规则散落 if", "改策略要改代码。", "config YAML + Router 类。"),
        ("精排也用路由大模型", "成本爆炸。", "生成路由；精排固定 [96]。"),
        ("忽略 embed 路由", "query 与库维度不一致。", "embed 与 index 版本绑定。"),
    ], "10")
    faq = _faq([
        ("路由按什么维度？", "任务类型、输入长度、延迟 SLA、成本、主模型健康。"),
        ("本地小模型？", "Ollama/vLLM 作 fallback；见 [72 本地 Embedding](72.local-embedding-inference-tutorial.md) 思路。"),
        ("与 [167 封装](167.openai-api-wrapper-tutorial.md)？", "Router 选 model → LLMClient.chat(model=...)。"),
        ("A/B 测试？", "见 [153 AB 实验](153.ab-experiment-rag-tutorial.md)；路由带 experiment_id。"),
        ("Circuit breaker？", "主模型连续 5xx 打开断路，走 backup 60s。"),
    ], "14")
    return f'''# F 后端与 API（十三）：多模型路由与降级完全指南

> 主模型 **429**、区域 **5xx**、成本 **超预算**——企业 RAG 不能只绑 **一个** `gpt-4o`。[167 OpenAI 封装](167.openai-api-wrapper-tutorial.md) 提供了 **统一 Client**；本篇在其上建 **Router**：按 **任务/健康/成本** 选 **primary → fallback → 本地小模型**。路线图 **185**，**F 轨地基篇**。前置：[35 OpenAI API](35.openai-compatible-api-tutorial.md)、[167 封装](167.openai-api-wrapper-tutorial.md)、[163 重试](163.retry-dead-letter-tutorial.md)。

---

## 目录

1. [前言：单模型是 PoC，多模型是生存](#1-前言单模型是-poc多模型是生存)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [多模型路由是什么](#3-多模型路由是什么)
4. [路由维度：任务、成本、SLA](#4-路由维度任务成本sla)
5. [降级链与断路器](#5-降级链与断路器)
6. [配置驱动路由表](#6-配置驱动路由表)
7. [与 LLMClient 集成](#7-与-llmclient-集成)
8. [Embed 路由与索引版本](#8-embed-路由与索引版本)
9. [综合实战：Router + Fallback](#9-综合实战router--fallback)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：单模型是 PoC，多模型是生存

场景：

- **简单 FAQ** → 小模型够；  
- **合规问答** → 大模型 + 低 temperature [29](29.llm-sampling-tutorial.md)；  
- **主站 429** → 备用网关；  
- **离线演示** → Ollama 本地。

**Model routing（模型路由）**：根据 **规则或健康检查** 选择 **具体 model 端点** 的组件。  
**Fallback（降级）**：主路径失败时 **按序尝试** 备用模型。  
通俗说：**导航 App 换路线**——主路堵车走辅路，不是 **停在原地**。

---

## 2. 本文边界与动手路径

**档位：F 轨地基篇（185）。**

---

## 3. 多模型路由是什么

![路由流程](image/multi-model-routing/01-routing-flow.png)

```text
Request → Router.select(task, len, tenant_tier)
    → try primary
    → on RateLimitError/5xx → fallback_1 → fallback_2
    → LLMClient.chat(model=selected)
```

---

## 4. 路由维度：任务、成本、SLA

![路由规则](image/multi-model-routing/02-routing-rules.png)

| 信号 | 路由倾向 |
|------|----------|
| task=rag_answer | chat 档 mid |
| task=summary | chat 档 small |
| tokens_in > 8k | 长上下文 model |
| tenant=trial | 仅 small |
| primary unhealthy | backup |

---

## 5. 降级链与断路器

```python
class CircuitBreaker:
    def __init__(self, fail_threshold=5, cool_down=60):
        self.failures = 0
        self.open_until = 0

    def record_success(self): self.failures = 0
    def record_failure(self):
        self.failures += 1
        if self.failures >= 5:
            self.open_until = time.time() + 60

    def is_open(self): return time.time() < self.open_until
```

与 [163 重试死信](163.retry-dead-letter-tutorial.md)：**路由层** 决定 **换模型**；**Client 层** 决定 **同模型重试**。

---

## 6. 配置驱动路由表

```yaml
# routing.yaml
routes:
  rag_answer:
    primary: gpt-4o-mini
    fallbacks: [deepseek-chat, qwen-turbo]
  rag_summary:
    primary: gpt-4o-mini
    fallbacks: [local-llama3-8b]
```

[138 配置驱动](138.config-driven-pipeline-tutorial.md) 思想：**改 YAML 不发版**（需热加载流程）。

---

## 7. 与 LLMClient 集成

```python
class RoutingLLMClient:
    def __init__(self, inner: LLMClient, router: ModelRouter):
        self._inner = inner
        self._router = router

    async def chat(self, messages, *, task="rag_answer", **kw):
        chain = self._router.chain_for(task)
        last_err = None
        for model in chain:
            if self._router.breaker.is_open(model):
                continue
            try:
                out = await self._inner.chat(messages, model=model, **kw)
                self._router.breaker.record_success(model)
                return out
            except (RateLimitError, InternalServerError) as e:
                last_err = e
                self._router.breaker.record_failure(model)
                logger.warning("route_fallback", model=model)
        raise last_err
```

---

## 8. Embed 路由与索引版本

**Embed 路由更严**：换 embed model **必须** 对应 **新 collection** [76 Chroma](76.chroma-vector-db-tutorial.md)。  
Router **只应在同维度同空间** 内切换；否则 **拒绝并告警**。

---

## 9. 综合实战：Router + Fallback

```python
@pytest.mark.asyncio
async def test_fallback_on_429(monkeypatch):
    calls = []
    async def fake_chat(messages, model=None, **kw):
        calls.append(model)
        if model == "primary":
            raise RateLimitError("429")
        return "backup answer"
    ...
    assert calls == ["primary", "backup"]
```

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![路由概念地图](image/multi-model-routing/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **Router + LLMClient** 分层；**降级必观测**。  
2. Embed 路由 **绑定索引版本**。  
3. 下一篇 [169 限流](169.rate-limiting-api-tutorial.md) 防 **429 人为制造**。

{SHARED_APPENDIX}
'''


def build_169() -> str:
    mistakes = _mistakes([
        ("无限流", "单用户刷爆 TPM 账单。", "QPS + TPM 双限。"),
        ("全站共用一桶", "一 tenant 拖垮全体。", "按 tenant/user 分 key。"),
        ("429 无 Retry-After", "客户端盲目重试雪崩。", "响应头 + 文档说明。"),
        ("只限 chat 不限 ingest", "大文件 embed 打满。", "分 endpoint 配额。"),
        ("限流在 Client 内隐藏", "用户不知为何慢。", "明确 429 JSON code。"),
    ], "10")
    faq = _faq([
        ("令牌桶还是滑动窗口？", "令牌桶允许突发；滑动窗口更平滑；Redis 常用令牌桶。"),
        ("与网关限流？", "网关粗限；应用细限 tenant TPM。"),
        ("免费 tier？", "低 QPS + 日配额；超限 429。"),
        ("与 [168 路由](168.multi-model-routing-tutorial.md) 429？", "路由换模型；限流 **保护预算** 不等价。"),
        ("FastAPI 库？", "slowapi、自定义 Redis 中间件均可。"),
    ], "14")
    return f'''# F 后端与 API（十四）：速率限制 Rate Limiting 完全指南

> RAG API 同时吃 **HTTP QPS** 与 **LLM TPM**——不设限会被 **脚本刷爆** [27 Token 计费](27.token-counting-billing-tutorial.md)，或 **429 雪崩** 拖垮 [167 Client](167.openai-api-wrapper-tutorial.md)。在 [164 JWT](164.jwt-auth-rag-tutorial.md) 身份之上，本篇做 **按 user/tenant 的速率限制**。路线图 **186**，**F 轨地基篇**。

---

## 目录

1. [前言：429 不是丢脸，是保护](#1-前言429-不是丢脸是保护)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [Rate Limiting 是什么](#3-rate-limiting-是什么)
4. [令牌桶与滑动窗口](#4-令牌桶与滑动窗口)
5. [QPS 与 TPM 双轨](#5-qps-与-tpm-双轨)
6. [FastAPI + Redis 实现](#6-fastapi--redis-实现)
7. [429 响应与 Retry-After](#7-429-响应与-retry-after)
8. [与多租户配额 [166]](#8-与多租户配额-166)
9. [综合实战：limiter 中间件](#9-综合实战limiter-中间件)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与 FAQ)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：429 不是丢脸，是保护

**Rate limiting（速率限制）**：单位时间内 **允许的最大请求数或 token 数**；超出返回 **429 Too Many Requests**。  
通俗说：**游乐园限流**——不是不让玩，是 **防止踩踏**。

企业 RAG 限流目标：

1. **防刷**——保护 embed/chat 成本；  
2. **公平**——tenant 间 **不互相饿死**；  
3. **保护下游**——LLM 网关 [35](35.openai-compatible-api-tutorial.md) 也有上限。

---

## 2. 本文边界与动手路径

**档位：F 轨地基篇（186）。**  
**环境：** Redis；`pip install redis slowapi`（或自研中间件）。

---

## 3. Rate Limiting 是什么

![限流是什么](image/rate-limiting-api/01-rate-limit-idea.png)

限流键示例：

```text
rl:tenant:{{tenant_id}}:chat:minute
rl:user:{{user_id}}:ingest:hour
rl:ip:{{ip}}:anonymous:minute
```

---

## 4. 令牌桶与滑动窗口

![令牌桶](image/rate-limiting-api/02-token-bucket.png)

**令牌桶**：桶容量 `burst`，每秒补充 `rate`；请求消耗 1 令牌；**允许短时突发**。  
**滑动窗口**：统计过去 60s 请求数；**更严更平滑**。

PoC 可用 **内存 dict**；生产 **Redis + Lua 原子**。

---

## 5. QPS 与 TPM 双轨

| 类型 | 限制对象 | 典型值 |
|------|----------|--------|
| QPS | HTTP 请求 | 10/min/user |
| TPM | LLM tokens | 100k/day/tenant |
| 并发 | 同时 stream | 2/user |

chat 限流在 **进 LLM 前**；ingest 限流在 **收 multipart** [157](157.file-upload-multipart-tutorial.md) 时。

---

## 6. FastAPI + Redis 实现

```python
import time
import redis

r = redis.Redis.from_url("redis://localhost")

def allow(key: str, limit: int, window_sec: int) -> bool:
    now = int(time.time())
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_sec)
    pipe.zadd(key, {{str(now): now}})
    pipe.zcard(key)
    pipe.expire(key, window_sec + 1)
    _, _, count, _ = pipe.execute()
    return count <= limit

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    user = getattr(request.state, "user", None)
    key = f"rl:{{user.user_id if user else request.client.host}}:{{request.url.path}}"
    if not allow(key, limit=60, window_sec=60):
        return JSONResponse(status_code=429, content={{"code": "RATE_LIMIT", "retry_after": 30}},
                          headers={{"Retry-After": "30"}})
    return await call_next(request)
```

---

## 7. 429 响应与 Retry-After

```json
{{
  "code": "RATE_LIMIT",
  "message": "请求过于频繁，请稍后再试",
  "retry_after": 30
}}
```

前端 [171 聊天 UI](171.chat-message-list-ui-tutorial（front-end）.md) 应 **展示友好文案** 而非 **裸 429**。

---

## 8. 与多租户配额 [166]

[166 租户隔离](166.tenant-isolation-backend-tutorial.md) **套餐表**：

```python
TENANT_QUOTAS = {{
    "trial": {{"chat_qpm": 20, "tpm_day": 50000}},
    "enterprise": {{"chat_qpm": 500, "tpm_day": 5000000}},
}}
```

超限 **429** + 销售升级提示——**产品策略** 与 **技术限流** 一体。

---

## 9. 综合实战：limiter 中间件

压测：`hey -n 200 -c 20` 打 `/rag/chat` → 期望 **部分 429** + **Retry-After**。

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![限流概念地图](image/rate-limiting-api/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **QPS + TPM** 双限；**按 tenant 分桶**。  
2. **429 是契约**——带 Retry-After。  
3. 下一篇 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 把限流 **写进文档**。

{SHARED_APPENDIX}
'''


def build_170() -> str:
    mistakes = _mistakes([
        ("手写文档与代码两套", "字段改了文档未改。", "FastAPI 自动生成 + CI diff。"),
        ("Schema 过宽 any", "前端无法类型安全。", "Pydantic 严格模型。"),
        ("不文档 401/403/429", "集成方踩坑。", "responses 枚举全状态码。"),
        ("生产暴露 Swagger 无 auth", "接口被扫描。", "dev 开 /docs；prod 关闭或 IP 白名单。"),
        ("版本号缺失", "破坏性变更静默上线。", "URL /v1/ 或 header API-Version。"),
    ], "10")
    faq = _faq([
        ("OpenAPI 和 Swagger 关系？", "OpenAPI 是规范；Swagger UI 是可视化工具。"),
        ("FastAPI 怎么生成？", "app = FastAPI(title=..., version=...)；装饰器 + response_model。"),
        ("需要手写 YAML 吗？", "可选；FastAPI 可从代码 export openapi.json。"),
        ("与 [170] 了解档？", "本篇 **知道即可**，但 PoC 也应 **export 一份 json** 给前端。"),
        ("契约测试？", "schemathesis / Dredd 对 openapi.json 跑 fuzz。"),
    ], "14")
    return f'''# F 后端与 API（十五）：OpenAPI / Swagger 文档完全指南

> 前端 [171 聊天 UI](171.chat-message-list-ui-tutorial（front-end）.md) 要对接 `/rag/chat`——若只有 **口头约定**，字段一改 **联调地狱**。**OpenAPI**（原 Swagger 规范）用 **机器可读** 的 schema 描述 REST API；FastAPI **自动生成** `/openapi.json` 与 `/docs` Swagger UI。路线图 **187**，**F 轨了解篇**——**知道即可**，但 **PoC 就应启用**。

---

## 目录

1. [前言：文档是前后端契约](#1-前言文档是前后端契约)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [OpenAPI 是什么](#3-openapi-是什么)
4. [FastAPI 自动生成](#4-fastapi-自动生成)
5. [Schema：ChatRequest / ChatResponse](#5-schemachatrequest--chatresponse)
6. [securitySchemes 与 JWT [164]](#6-securityschemes-与-jwt-164)
7. [错误码与 429 [169]](#7-错误码与-429-169)
8. [导出、版本、CI](#8-导出版本ci)
9. [综合实战：完善 Mini-RAG OpenAPI](#9-综合实战完善-mini-rag-openapi)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与 FAQ)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：文档是前后端契约

**OpenAPI Specification**：描述 REST API 路径、方法、参数、请求/响应 JSON Schema、鉴权方式的 **YAML/JSON 标准**。  
**Swagger UI**：浏览器里 **试调 API** 的界面，读 OpenAPI 渲染。  
通俗说：**菜单 + 说明书**——菜名（path）、做法（method）、配料（schema） **写清楚**。

RAG 典型端点应出现在文档：

- `POST /auth/login`  
- `POST /rag/chat`  
- `POST /rag/ingest`（[165 RBAC](165.rbac-rag-tutorial.md)）  
- SSE 流式 [116](116.sse-rag-streaming-tutorial.md)（OpenAPI 3.1 对 stream 支持需查版本）

---

## 2. 本文边界与动手路径

**档位：F 轨了解篇（187）。**  
**目标**：能打开 `/docs` 试调；能 export `openapi.json` 给前端。

---

## 3. OpenAPI 是什么

![OpenAPI 价值](image/openapi-swagger-docs/01-openapi-flow.png)

价值：

1. **并行开发**——前端 Mock；  
2. **SDK 生成**——openapi-generator；  
3. **契约测试**——响应符合 schema；  
4. ** onboarding**——新人 **自助试 API**。

---

## 4. FastAPI 自动生成

```python
app = FastAPI(
    title="Enterprise Mini-RAG API",
    version="1.0.0",
    description="JWT + RBAC + tenant isolation. See roadmap F-track.",
)

@router.post("/rag/chat", response_model=ChatResponse, responses={{
    401: {{"description": "Invalid JWT"}},
    403: {{"description": "ACL_DENIED or RBAC"}},
    429: {{"description": "Rate limited"}},
}})
async def chat(...): ...
```

访问 `http://localhost:8000/docs` → Swagger UI。

---

## 5. Schema：ChatRequest / ChatResponse

![Schema 设计](image/openapi-swagger-docs/02-schema-example.png)

```python
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, examples=["年假有多少天？"])
    session_id: str | None = None

class Citation(BaseModel):
    chunk_id: str
    title: str
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    trace_id: str
```

与 [113 引用](113.inline-citation-tutorial.md) 字段 **对齐**，前端 TypeScript **可 codegen**。

---

## 6. securitySchemes 与 JWT [164]

```python
app = FastAPI(
    swagger_ui_init_oauth={{...}},
)

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["components"]["securitySchemes"] = {{
        "BearerAuth": {{"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}
    }}
    schema["security"] = [{{"BearerAuth": []}}]
    app.openapi_schema = schema
    return schema
```

Swagger UI **Authorize** 按钮粘贴 [164 JWT](164.jwt-auth-rag-tutorial.md) token 试调。

---

## 7. 错误码与 429 [169]

统一 **ErrorBody**：

```python
class ErrorBody(BaseModel):
    code: Literal["ACL_DENIED", "RATE_LIMIT", "VALIDATION_ERROR"]
    message: str
    retry_after: int | None = None
```

[169 限流](169.rate-limiting-api-tutorial.md) 的 429 **必须** 出现在 `responses` 表。

---

## 8. 导出、版本、CI

```bash
curl http://localhost:8000/openapi.json -o openapi/v1.json
```

CI：`openapi-diff` 检测 **破坏性变更**（删字段、改类型）。

生产：**关闭公开 /docs** 或 **VPN**；json artifact **发前端**。

---

## 9. 综合实战：完善 Mini-RAG OpenAPI

Checklist：

- [ ] 所有路由有 `response_model`  
- [ ] 401/403/429  documented  
- [ ] JWT securityScheme  
- [ ] export json 提交仓库 `openapi/v1.json`

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![OpenAPI 概念地图](image/openapi-swagger-docs/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **FastAPI 自带 OpenAPI**——别手写两套。  
2. **了解篇也要 export**——前端 [171](171.chat-message-list-ui-tutorial（front-end）.md) 依赖契约。  
3. 进入 **G 轨前端**：[171 聊天列表](171.chat-message-list-ui-tutorial（front-end）.md)。

{SHARED_APPENDIX}
'''


def build_171() -> str:
    mistakes = _mistakes([
        ("messages 放 useState 无 id", "重渲染乱序、key 警告。", "每条 message 稳定 uuid。"),
        ("streaming 直接 append 字符到 DOM", "性能差。", "增量更新最后一条 assistant。"),
        ("不区分 loading/error", "用户以为卡死。", "明确 pending/streaming/error 状态。"),
        ("滚动不跟新消息", "看不到最新回复。", "useEffect + scrollIntoView。"),
        ("把 markdown 当 plain text", "表格列表丑。", "assistant 走 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 组件。"),
    ], "10")
    faq = _faq([
        ("Next.js App 还是 Pages？", "App Router 为主；Server Component 取 session，Client 组件聊天。"),
        ("状态放哪？", "PoC：useState；生产：Zustand/Context + 服务端 session。"),
        ("与 [174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)？", "174 专讲 stream 动画；本篇管 **列表结构**。"),
        ("与 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)？", "citations 作 message 子 props 渲染。"),
        ("虚拟列表必要吗？", "消息 <200 可不用；超长会话用 react-virtuoso。"),
    ], "14")
    return f'''# G 前端与体验（一）：聊天消息列表 UI 完全指南

> 后端 [164 JWT](164.jwt-auth-rag-tutorial.md)、[170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 就绪后，用户 **第一眼** 看到的是 **聊天窗口**——不是 Swagger。**MessageList** 负责 **user/assistant/system** 消息渲染、**流式占位**、**错误重试**、**滚到底**。本篇用 **React + Next.js App Router** 示例，是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **G 轨主线篇**（路线图 **188**）。后续 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md)、[174 流式打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)、[176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)。

---

## 目录

1. [前言：RAG 产品的脸是聊天 UI](#1-前言rag-产品的脸是聊天-ui)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [消息列表是什么](#3-消息列表是什么)
4. [Message 数据模型](#4-message-数据模型)
5. [组件拆分：List / Bubble / Input](#5-组件拆分list--bubble--input)
6. [Next.js App Router 结构](#6-nextjs-app-router-结构)
7. [状态：idle / streaming / error](#7-状态idle--streaming--error)
8. [滚动与自动跟随](#8-滚动与自动跟随)
9. [综合实战：ChatPage 最小实现](#9-综合实战chatpage-最小实现)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与 FAQ)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：RAG 产品的脸是聊天 UI

ChatGPT 类产品心智：**左侧历史、中间消息流、底部输入框**。企业 RAG 复用同一模式，但要多：

- **引用区** [113](113.inline-citation-tutorial.md) / [176 卡片](176.citation-card-ui-tutorial（front-end）.md)；  
- **鉴权** [164 JWT](164.jwt-auth-rag-tutorial.md) token 带头；  
- **流式** [116 SSE](116.sse-rag-streaming-tutorial.md)；  
- **Markdown** [172 篇](172.markdown-render-rag-tutorial（front-end）.md) 渲染 assistant 回复。

**MessageList（消息列表）**：按时间序渲染 **Message[]** 的容器组件。  
通俗说：**微信聊天记录**——谁说的、什么样式、新消息 **滚到底**。

---

## 2. 本文边界与动手路径

**档位：G 轨主线篇（188）。**  
**环境：** Node 18+；`npx create-next-app@latest rag-chat --typescript --app --tailwind`。

| 步骤 | 验收 |
|------|------|
| A | 建 Message 类型 | TypeScript 编译 |
| B | 渲染静态 3 条 | user/assistant 样式 |
| C | 接 mock API | 发送后多一条 |
| D | streaming 占位 | 最后条 growing |
| E | 错误态 + 重试 | 按钮可点 |

---

## 3. 消息列表是什么

![消息列表](image/chat-message-list-ui/01-message-list.png)

```text
ChatPage
├── MessageList (scroll container)
│   ├── MessageBubble role=user
│   ├── MessageBubble role=assistant (Markdown)
│   └── StreamingPlaceholder (optional)
├── CitationBar (optional, 176)
└── ChatInput
```

---

## 4. Message 数据模型

```typescript
export type MessageRole = "user" | "assistant" | "system";

export interface Message {{
  id: string;
  role: MessageRole;
  content: string;
  createdAt: number;
  status?: "pending" | "streaming" | "done" | "error";
  citations?: Array<{{ chunkId: string; title: string; snippet: string }}>;
  errorCode?: string;
}}
```

与 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) `ChatResponse` **对齐**；`id` 用 `crypto.randomUUID()` **勿用 index**。

---

## 5. 组件拆分：List / Bubble / Input

```tsx
// components/MessageBubble.tsx
export function MessageBubble({{ message }}: {{ message: Message }}) {{
  const isUser = message.role === "user";
  return (
    <div className={{`flex ${{isUser ? "justify-end" : "justify-start"}} mb-4`}}>
      <div className={{`max-w-[80%] rounded-2xl px-4 py-2 ${{isUser ? "bg-blue-600 text-white" : "bg-gray-100"}}`}}>
        {{isUser ? (
          <p className="whitespace-pre-wrap">{{message.content}}</p>
        ) : (
          <AssistantContent message={{message}} />
        )}}
        {{message.status === "streaming" && <span className="animate-pulse">▍</span>}}
        {{message.status === "error" && <ErrorRetry message={{message}} />}}
      </div>
    </div>
  );
}}
```

`AssistantContent` 内嵌 [172 MarkdownRenderer](172.markdown-render-rag-tutorial（front-end）.md)。

---

## 6. Next.js App Router 结构

![React 结构](image/chat-message-list-ui/02-react-structure.png)

```text
app/
  layout.tsx
  chat/
    page.tsx          # Server: 可选读 cookie
  api/
    rag/
      chat/route.ts   # BFF 转发 + JWT
components/
  chat/
    ChatPage.tsx      # "use client"
    MessageList.tsx
    ChatInput.tsx
```

**BFF（Backend for Frontend）**：Next.js Route Handler **代传** JWT，**避免** 浏览器 CORS 复杂化（可选架构）。

```typescript
// app/chat/page.tsx
import {{ ChatPage }} from "@/components/chat/ChatPage";

export default function Page() {{
  return <ChatPage />;
}}
```

```typescript
// components/chat/ChatPage.tsx
"use client";

import {{ useState, useCallback }} from "react";
import {{ MessageList }} from "./MessageList";
import {{ ChatInput }} from "./ChatInput";
import type {{ Message }} from "@/types/chat";

export function ChatPage() {{
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);

  const send = useCallback(async (text: string) => {{
    const userMsg: Message = {{
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      createdAt: Date.now(),
      status: "done",
    }};
    const assistantId = crypto.randomUUID();
    setMessages((m) => [
      ...m,
      userMsg,
      {{ id: assistantId, role: "assistant", content: "", createdAt: Date.now(), status: "streaming" }},
    ]);
    setSending(true);
    try {{
      const res = await fetch("/api/rag/chat", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ question: text }}),
      }});
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantId
            ? {{ ...msg, content: data.answer, citations: data.citations, status: "done" }}
            : msg
        )
      );
    }} catch (e) {{
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantId ? {{ ...msg, status: "error", errorCode: "NETWORK" }} : msg
        )
      );
    }} finally {{
      setSending(false);
    }}
  }}, []);

  return (
    <div className="flex h-screen flex-col">
      <MessageList messages={{messages}} />
      <ChatInput onSend={{send}} disabled={{sending}} />
    </div>
  );
}}
```

---

## 7. 状态：idle / streaming / error

| status | UI |
|--------|-----|
| pending | 发送中禁用输入 |
| streaming | 光标闪烁；[174](174.streaming-typewriter-ui-tutorial（front-end）.md) 增量改 content |
| done | 完整 Markdown |
| error | 重试按钮；展示 [169 429](169.rate-limiting-api-tutorial.md) 文案 |

---

## 8. 滚动与自动跟随

```tsx
// MessageList.tsx
const bottomRef = useRef<HTMLDivElement>(null);
useEffect(() => {{
  bottomRef.current?.scrollIntoView({{ behavior: "smooth" }});
}}, [messages]);
```

用户 **手动上滚阅读** 时应 **暂停 auto-scroll**——比较 `scrollTop + clientHeight < scrollHeight - 50` 判断。

---

## 9. 综合实战：ChatPage 最小实现

完整仓库结构见 §6；对接 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 生成的 **TypeScript 类型**。

**验收**：

1. 发送 user 消息 **右对齐**；  
2. assistant **左对齐** + Markdown；  
3. 流式时 **最后一条增长**；  
4. 401 跳登录（[164 JWT](164.jwt-auth-rag-tutorial.md)）。

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![聊天 UI 概念地图](image/chat-message-list-ui/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **Message 稳定 id + status** 是核心模型。  
2. **Next.js Client 组件** 管交互；API 对齐 OpenAPI。  
3. 下一篇 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) **安全渲染** assistant 内容。

{SHARED_APPENDIX}
'''


def build_172() -> str:
    mistakes = _mistakes([
        ("dangerouslySetInnerHTML", "XSS 执行脚本。", "react-markdown + rehype-sanitize。"),
        ("允许 raw HTML 标签", "<img onerror=...>", "sanitize 默认 strip script/on*。"),
        ("链接不 noopener", "tabnabbing。", "rehype-external-links target=_blank rel=noopener。"),
        ("用户 markdown 与模型 markdown 同一策略", "用户输入更不可信。", "分 sanitize 级别。"),
        ("以为模型不会输出恶意 MD", "提示注入可让模型吐 script。", "始终 sanitize LLM 输出。"),
    ], "10")
    faq = _faq([
        ("react-markdown 还是 marked？", "React 生态优先 react-markdown；便于组件替换。"),
        ("与 [23 Self-Attention](23.self-attention-tutorial.md)？", "23 讲模型内部注意力；XSS 是 **渲染层** 安全，无关 transformer。"),
        ("代码块怎么办？", "见 [173 代码高亮](173.code-highlight-rag-tutorial（front-end）.md)；先 sanitize 再高亮。"),
        ("内网可以关 sanitize？", "不可以；LLM 输出不可信 + 库内文档可能含 HTML。"),
        ("CSP 还要吗？", "要；sanitize + CSP **纵深**。"),
    ], "14")
    return f'''# G 前端与体验（二）：Markdown 渲染与安全（react-markdown）完全指南

> Assistant 回复常是 **Markdown**：标题、列表、表格、代码块。在 [171 消息列表](171.chat-message-list-ui-tutorial（front-end）.md) 里若用 `dangerouslySetInnerHTML` 或 **不消毒的** HTML 插件，攻击者或 **被提示注入的模型** 可插入 `<script>`——**XSS**（Cross-Site Scripting）窃取 [164 JWT](164.jwt-auth-rag-tutorial.md)。本篇讲 **react-markdown + remark/rehype sanitize** 安全管线。路线图 **189**，**G 轨地基篇**。概念上勿与 [23 Self-Attention](23.self-attention-tutorial.md) 混淆——**23 是模型内部「互相看」**；**本篇是浏览器 DOM 安全**。

---

## 目录

1. [前言：Markdown 漂亮，XSS 致命](#1-前言markdown-漂亮xss-致命)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [RAG 为什么要 Markdown 渲染](#3-rag-为什么要-markdown-渲染)
4. [react-markdown 管线](#4-react-markdown-管线)
5. [XSS 威胁模型](#5-xss-威胁模型)
6. [rehype-sanitize 配置](#6-rehype-sanitize-配置)
7. [链接、图片、代码块策略](#7-链接图片代码块策略)
8. [与 [113] 引用组件结合](#8-与-113-引用组件结合)
9. [综合实战：MarkdownRenderer 组件](#9-综合实战markdownrenderer-组件)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与 FAQ)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：Markdown 漂亮，XSS 致命

模型可能输出：

```markdown
## 答案
<script>fetch('/api/steal? t='+localStorage.token)</script>
```

或知识库 chunk 原文 **含 HTML**（[39 HTML 提取](39.html-content-extraction-tutorial.md) 遗留）。  
**XSS**：恶意脚本在 **用户浏览器** 执行。RAG 场景 **受害者** 是 **看回答的员工**——token 在 localStorage 时 **整站沦陷**。

**Sanitize（消毒）**：白名单允许的标签/属性，剥离 `script`、`onerror` 等。  
通俗说：**安检**——只允许 **安全的 Markdown 子集** 进 DOM。

[23 Self-Attention](23.self-attention-tutorial.md) 教的是 **Transformer 层内** token 互相看——**解决不了** HTML 注入；**渲染层** 必须 **单独防 XSS**。

---

## 2. 本文边界与动手路径

**档位：G 轨地基篇（189）。**  
**环境：** `npm i react-markdown remark-gfm rehype-sanitize rehype-external-links`。

---

## 3. RAG 为什么要 Markdown 渲染

![渲染管线](image/markdown-render-rag/01-markdown-pipeline.png)

| 纯文本 | Markdown 渲染 |
|--------|---------------|
| 表格难读 | GFM 表格 |
| 代码无高亮 | 接 [173 高亮](173.code-highlight-rag-tutorial（front-end）.md) |
| 列表一层 | 嵌套列表 |

渲染发生在 **[171 MessageBubble](171.chat-message-list-ui-tutorial（front-end）.md) assistant 分支**。

---

## 4. react-markdown 管线

```text
markdown string
  → remark-parse
  → remark-gfm (tables, strikethrough)
  → rehype-sanitize  ← 安全关键
  → rehype-external-links
  → React components
```

**不要** 默认启用 `rehype-raw`（允许原始 HTML）除非 **另有严格 sanitize**。

---

## 5. XSS 威胁模型

![XSS 对照](image/markdown-render-rag/02-xss-attack.png)

| 来源 | 风险 |
|------|------|
| LLM 输出 | 提示注入诱导 script |
| 检索 chunk | 库内恶意 HTML |
| 用户消息 | 若也渲染 MD，更严 |

**信任边界**：**所有进 DOM 的 assistant 字符串 = 不可信**。

---

## 6. rehype-sanitize 配置

```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize, {{ defaultSchema }} from "rehype-sanitize";
import rehypeExternalLinks from "rehype-external-links";

const schema = {{
  ...defaultSchema,
  attributes: {{
    ...defaultSchema.attributes,
    a: [...(defaultSchema.attributes?.a || []), ["target", "_blank"], ["rel", "noopener noreferrer"]],
  }},
}};

export function MarkdownRenderer({{ content }}: {{ content: string }}) {{
  return (
    <ReactMarkdown
      remarkPlugins={{[remarkGfm]}}
      rehypePlugins={{[
        [rehypeSanitize, schema],
        [rehypeExternalLinks, {{ target: "_blank", rel: ["noopener", "noreferrer"] }}],
      ]}}
    >
      {{content}}
    </ReactMarkdown>
  );
}}
```

**禁止** `dangerouslySetInnerHTML` 渲染 LLM 输出。

---

## 7. 链接、图片、代码块策略

- **链接**：`http/https/mailto` 白名单；`javascript:` **拒**；  
- **图片**：可选 **禁 img** 或 **只允许 https + 域名白名单**；  
- **代码块**：用 **自定义 `components.code`** 接 [173](173.code-highlight-rag-tutorial（front-end）.md)，**高亮输入已是 sanitize 后 AST**。

---

## 8. 与 [113] 引用组件结合

```tsx
const components = {{
  p: ({{ children }}) => <p>{{children}}</p>,
  // 自定义 [1] 脚注：勿 innerHTML
  sup: CitationSup,
}};
```

[113 行内引用](113.inline-citation-tutorial.md) 用 **React 组件** 渲染 `[1]`，**不** 正则替换 HTML 字符串。

---

## 9. 综合实战：MarkdownRenderer 组件

```tsx
// __tests__/markdown-xss.test.tsx
import {{ render }} from "@testing-library/react";
import {{ MarkdownRenderer }} from "./MarkdownRenderer";

test("strips script", () => {{
  const {{ container }} = render(
    <MarkdownRenderer content={'<script>alert(1)</script>\\n\\nHello'} />
  );
  expect(container.querySelector("script")).toBeNull();
  expect(container.textContent).toContain("Hello");
}});
```

**CI 必跑** XSS 用例集。

---

## 10. 先错对对：五种典型翻车

{mistakes}

---

## 11. 综合概念地图

![Markdown 概念地图](image/markdown-render-rag/03-concept-map.png)

| 篇 | 关系 |
|----|------|
| [23 Self-Attention](23.self-attention-tutorial.md) | 模型内部，非 XSS |
| [171 聊天 UI](171.chat-message-list-ui-tutorial（front-end）.md) | 挂载 Renderer |
| [113 引用](113.inline-citation-tutorial.md) | 自定义组件 |
| [173 高亮](173.code-highlight-rag-tutorial（front-end）.md) | sanitize 后高亮 |

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **react-markdown + rehype-sanitize** 是 RAG 前端 **默认标配**。  
2. **LLM 输出不可信**；与 [23](23.self-attention-tutorial.md) **正交**。  
3. 下一篇 [173 代码高亮](173.code-highlight-rag-tutorial（front-end）.md) 在 **安全 AST** 上高亮。

{SHARED_APPENDIX}
'''
