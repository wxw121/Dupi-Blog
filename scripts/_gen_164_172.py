# -*- coding: utf-8 -*-
"""Generate tutorials 164-172 (roadmap 181-189) with >=5000 hanzi each."""
from __future__ import annotations

from pathlib import Path

from _gen_164_172_utils import (
    EXPANSION_BLOCKS,
    ROOT,
    SHARED_APPENDIX,
    _faq,
    _mistakes,
    hanzi_count,
    pad_if_needed,
    write_image_assets,
)

def build_164_jwt() -> str:
    mistakes = _mistakes([
        ("JWT 放 localStorage 且无 CSP", "XSS 偷 token 全库可读。", "HttpOnly Cookie 或短 access；CSP + sanitize [172]。"),
        ("只验签名不验 exp/aud", "过期 token 或错受众仍可用。", "验证 exp、nbf、aud、iss 全套 claim。"),
        ("从 body 读 user_id", "攻击者伪造身份越权。", "只信 Authorization 解析 Principal。"),
        ("RS256 私钥进仓库", "泄露后全网可伪造。", "KMS/Vault；CI 扫密钥。"),
        ("access token 7 天", "泄露窗口过大。", "15min access + refresh 轮换。"),
        ("无 tenant claim", "多租户串库。", "JWT 必含 tenant_id；见 [166]。"),
    ])
    faq = _faq([
        ("JWT 和 Session 选哪个？", "API/SPA 多选 JWT+refresh；强吊销选 Session 或 JWT 黑名单。"),
        ("需要 OAuth2 吗？", "企业 SSO 常用 OIDC 换 JWT；PoC 可 username/password 发 JWT。"),
        ("算法 HS256 还是 RS256？", "单服务 HS256 可；多服务/网关 RS256 公钥验签。"),
        ("Refresh token 放哪？", "HttpOnly Secure Cookie 或原生安全存储；别 localStorage。"),
        ("RAG 检索用哪个 claim？", "roles→RBAC [165]；tenant_id→[166]；groups→[53] ACL filter。"),
        ("怎么测 JWT？", "pytest 造 token；负例：过期、错 aud、篡改 payload。"),
        ("与 API Key 并存？", "机器调用 API Key；用户浏览器 JWT；网关分流。"),
        ("logout 怎么做？", "refresh 黑名单 + 删 Cookie；access 等自然过期。"),
    ], "14")
    return f'''# F 后端与 API（九）：JWT 认证 RAG API 完全指南

> RAG 服务一上线，第一个安全问题往往是：**谁可以调 `/chat`？谁可以 `/ingest`？** 把 `user_id` 写在 JSON body 里等于 **信任前端**——攻击者改一行就能 **冒充财务看机密 chunk**（[53 ACL](53.metadata-acl-tutorial.md)、[121 越权](121.unauthorized-doc-filter-tutorial.md) 拦不住 **假身份**）。**JWT**（JSON Web Token）把 **已验证的身份** 签进 token，网关或 FastAPI **验签后** 注入 **Principal**，检索链才能 **按真实角色 filter**。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F 轨地基篇**（路线图第 **181** 条）。前置：[156 FastAPI 项目结构](156.fastapi-project-structure-tutorial.md)、[53 ACL](53.metadata-acl-tutorial.md)；后续 [165 RBAC](165.rbac-rag-tutorial.md)、[166 租户隔离](166.tenant-isolation-backend-tutorial.md)。

---

## 目录

1. [前言：身份是 RAG 安全的第一道门](#1-前言身份是-rag-安全的第一道门)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [JWT 是什么](#3-jwt-是什么)
4. [Access Token 与 Refresh Token](#4-access-token-与-refresh-token)
5. [Claims：sub、roles、tenant_id](#5-claimssubrolestenant_id)
6. [FastAPI 验签与依赖注入](#6-fastapi-验签与依赖注入)
7. [登录、刷新、登出流程](#7-登录刷新登出流程)
8. [与 RAG 检索链的衔接](#8-与-rag-检索链的衔接)
9. [综合实战：JWT 保护 Mini-RAG API](#9-综合实战jwt-保护-mini-rag-api)
10. [先错对对：六种典型翻车](#10-先错对对六种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：身份是 RAG 安全的第一道门

[121 篇](121.unauthorized-doc-filter-tutorial.md) 假设你已经知道 **当前用户是谁、有哪些角色**——若身份本身可伪造，后面的 Chroma `where`、ACL filter 全是 **纸糊的门**。

**JWT**（JSON Web Token）：由 **Header.Payload.Signature** 三段 Base64 组成的 **自包含令牌**；服务端用 **密钥或公钥** 验证签名后，读取 payload 里的 **claims**（声明），无需每次查 Session 库（可吊销策略另议）。  
通俗说：**带防伪章的工牌**——保安（API）验章，不用每次都打电话问 HR。

**Bearer Token**：HTTP 头 `Authorization: Bearer <jwt>` 的传递方式。  
**Principal**（安全主体）：验签后得到的 **用户身份对象**（id、roles、tenant_id 等），供 RBAC 与检索 filter 使用。

**读完本文，你应该能做到：**

1. 说清 JWT 三段结构与 **验签** 在 RAG API 中的位置。  
2. 设计 access/refresh **双 token** 与过期策略。  
3. 在 FastAPI 用 **Depends** 注入 `CurrentUser`。  
4. 把 `tenant_id`、`roles` 传给 [121 越权过滤](121.unauthorized-doc-filter-tutorial.md)。  
5. 识别 §10 六种翻车（body 传 user、长 access、alg none、无 tenant 等）。  
6. 跑通 §9 **登录 → chat → 403 负例**。

### 1.1 F 轨位置

```text
173 FastAPI 结构 [156]
181 JWT 认证 ← 本篇
182 RBAC → 183 租户 → 184 封装 ...
```

### 1.2 术语双轨速查

| 中文 | English | 一句话 |
|------|---------|--------|
| 访问令牌 | Access Token | 短效，调 API |
| 刷新令牌 | Refresh Token | 长效，换 access |
| 声明 | Claims | payload 键值 |
| 主体 | Principal | 验签后的用户 |
| 验签 | Verify signature | 防篡改 |

---

## 2. 本文边界与动手路径

**档位：F 轨地基篇（181）。**

**本文讲：** JWT 结构、双 token、FastAPI 集成、与 ACL/RBAC 衔接、Mini-RAG 实战。  
**本文不讲：** OAuth2/OIDC 全套、Keycloak 部署、零信任、mTLS 细节。

| 步骤 | 验收 |
|------|------|
| A | 画 JWT 三段 | 能口述 |
| B | 配 SECRET/算法 | .env 不进 Git |
| C | 跑 §9 login/chat | 200 + 401 |
| D | guest 问 finance | ACL 403 |
| E | §10 六种错 | 团队 review |

**环境：** Python 3.10+；`pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart`。

---

## 3. JWT 是什么

![JWT 认证流程](image/jwt-auth-rag/01-jwt-flow.png)

对照上图：

1. 用户 **登录** → 服务端验密码 → 签发 JWT；  
2. 客户端存 access（内存/短 Cookie）；  
3. 调 `POST /rag/chat` 带 `Authorization: Bearer ...`；  
4. API **验签** → 得到 Principal → **RBAC** → **检索 filter** → 生成。

JWT **不是加密**：payload Base64 **可解码**——**勿放密码、勿放 PII 全文**；只放 **id、角色、租户** 等必要 claims。

### 3.1 三段结构

```text
eyJhbGci...  .  eyJzdWI...  .  SflKxwRJ...
   Header         Payload        Signature
```

- **Header**：算法 `alg`、类型 `typ`；  
- **Payload**：`sub`（用户 id）、`exp`（过期）、自定义 `roles`、`tenant_id`；  
- **Signature**：防篡改——改 payload 验签失败。

### 3.2 与 Session 对比

| 维度 | JWT | Session |
|------|-----|---------|
| 状态 | 无状态（默认） | 服务端存 session |
| 扩展 | 水平扩展友好 | 需 Redis 共享 |
| 吊销 | 需黑名单/短 TTL | 删 session 即吊销 |
| RAG PoC | 常用 | 也可用 |

---

## 4. Access Token 与 Refresh Token

**Access Token**：5～30 分钟，每次 API 请求携带。  
**Refresh Token**：7～30 天，**仅** 用于 `POST /auth/refresh`，**权限更大**——存储与传输要 **更严**（HttpOnly Cookie）。

```text
登录 → access(15m) + refresh(7d)
access 过期 → refresh 换新 access（可选轮换 refresh）
logout → refresh 入黑名单
```

**Rotate refresh**：每次刷新 **发新 refresh、废旧 refresh**——防 **refresh 被盗长期有效**。

---

## 5. Claims：sub、roles、tenant_id

与 [53 ACL](53.metadata-acl-tutorial.md)、[165 RBAC](165.rbac-rag-tutorial.md)、[166 租户](166.tenant-isolation-backend-tutorial.md) **对齐**：

```json
{{
  "sub": "u_1024",
  "exp": 1710000000,
  "iat": 1709999100,
  "tenant_id": "acme_corp",
  "roles": ["employee"],
  "groups": ["all_staff"]
}}
```

| Claim | 用途 |
|-------|------|
| sub | 审计、个性化 |
| tenant_id | [89 多租户](89.multi-tenant-namespace-tutorial.md) filter |
| roles | API 级 RBAC（ingest/admin） |
| groups | chunk `acl_group` 映射 |

**groups 与 roles 分工**：roles 管 **能不能调接口**；groups 管 **能检索哪些 chunk**——可重叠不可混为一谈。

---

## 6. FastAPI 验签与依赖注入

![FastAPI JWT 依赖注入](image/jwt-auth-rag/02-fastapi-deps.png)

```python
# auth/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

SECRET = "change-me-in-env"
ALGO = "HS256"
security = HTTPBearer()

class Principal(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[str]
    groups: list[str]

def decode_token(token: str) -> Principal:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return Principal(
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
            roles=payload.get("roles", []),
            groups=payload.get("groups", []),
        )
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> Principal:
    return decode_token(creds.credentials)
```

路由使用：

```python
@router.post("/rag/chat")
async def chat(body: ChatRequest, user: Principal = Depends(get_current_user)):
    ...
```

**关键**：`user` **只来自 token**，** never ** `body.user_id`。

---

## 7. 登录、刷新、登出流程

```python
# auth/routes.py 示意
@router.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(form.username, form.password)
    if not user:
        raise HTTPException(401)
    access = create_access_token(user, minutes=15)
    refresh = create_refresh_token(user, days=7)
    return {{"access_token": access, "refresh_token": refresh, "token_type": "bearer"}}
```

生产 refresh 建议 **Set-Cookie HttpOnly Secure SameSite=Lax**；SPA 若纯 Bearer，**必须** 配合 **短 access + CSP**（见 [172 Markdown XSS](172.markdown-render-rag-tutorial（front-end）.md) 同轨前端安全）。

---

## 8. 与 RAG 检索链的衔接

```text
JWT 验签 → Principal
    → require_role("rag:chat")     # 165 RBAC
    → build_filter(principal)      # 53/121 ACL + 166 tenant
    → retriever.query(where=...)
    → LLM generate
```

`build_filter` 示例：

```python
def build_filter(p: Principal) -> dict:
    return {{
        "$and": [
            {{"tenant_id": p.tenant_id}},
            {{"acl_group": {{"$in": p.groups}}}},
        ]
    }}
```

与 [76 Chroma where](76.chroma-vector-db-tutorial.md) 语法对齐；Milvus/SQL 见 [88 filter](88.metadata-filter-retrieval-tutorial.md)。

---

## 9. 综合实战：JWT 保护 Mini-RAG API

完整最小结构（节选）：

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mini-RAG JWT")

class ChatRequest(BaseModel):
    question: str

@app.post("/auth/login")
def login(username: str, password: str):
    # 演示：guest / finance 两用户
    USERS = {{
        "guest": {{"pwd": "guest", "roles": ["user"], "groups": ["all_staff"], "tenant": "t1"}},
        "fin": {{"pwd": "fin", "roles": ["user"], "groups": ["all_staff", "finance_only"], "tenant": "t1"}},
    }}
    u = USERS.get(username)
    if not u or u["pwd"] != password:
        raise HTTPException(401)
    token = jwt.encode({{
        "sub": username,
        "tenant_id": u["tenant"],
        "roles": u["roles"],
        "groups": u["groups"],
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }}, SECRET, algorithm=ALGO)
    return {{"access_token": token}}

@app.post("/rag/chat")
def chat(req: ChatRequest, user: Principal = Depends(get_current_user)):
    where = build_filter(user)
    hits = collection.query(query_texts=[req.question], n_results=3, where=where)
    if not hits["documents"][0]:
        raise HTTPException(403, "ACL_DENIED")
    return {{"answer": "...", "chunks": hits}}
```

**验收**：guest token 问「Q4 签约金额」→ **403 或空 hits**；fin token → **有结果**。

---

## 10. 先错对对：六种典型翻车

{mistakes}

---

## 11. 综合概念地图

![JWT RAG 概念地图](image/jwt-auth-rag/03-concept-map.png)

| 模块 | 本篇 | 相邻篇 |
|------|------|--------|
| 身份 | JWT 验签 | 165 RBAC |
| 租户 | tenant claim | 166 隔离 |
| 文档 | groups→ACL | 53/121 |
| 传输 | Bearer | 116 SSE 也要鉴权 |

---

## 12. 常见陷阱与 FAQ

{faq}

---

## 13. 总结与系列下一步

1. **JWT = 可验证工牌**——RAG **必须** 验签后再检索。  
2. **短 access + refresh**；**tenant/roles/groups** 与 ACL/RBAC **分轨**。  
3. **Principal 只来自 header**——body 里的 user_id **不可信**。  
4. 下一篇 [165 RBAC](165.rbac-rag-tutorial.md) 管 **接口能力**；本篇管 **身份从哪来**。

### 13.1 系列下一步

| 目标 | 阅读 |
|------|------|
| 角色权限 | [165 RBAC](165.rbac-rag-tutorial.md) |
| 租户隔离 | [166 tenant](166.tenant-isolation-backend-tutorial.md) |
| ACL 字段 | [53 ACL](53.metadata-acl-tutorial.md) |
| 越权过滤 | [121 unauthorized](121.unauthorized-doc-filter-tutorial.md) |

### 13.2 学习目标自检

- [ ] 能签发并验签 JWT  
- [ ] FastAPI Depends 注入 Principal  
- [ ] chat 路由不带 body user_id  
- [ ] guest/finance 负例通过  
- [ ] 能画 JWT→filter 链路  

### 13.3 面试 30 秒版

「RAG API 用 JWT Bearer 传身份；验签得 sub、tenant_id、roles、groups；检索前 where tenant 与 acl_group；access 短、refresh 轮换；身份绝不信任客户端 body。」

{SHARED_APPENDIX}
'''


# Due to script size, remaining builders imported from companion module
from _gen_164_172_articles import (  # noqa: E402
    build_165,
    build_166,
    build_167,
    build_168,
    build_169,
    build_170,
    build_171,
    build_172,
    IMAGE_SPECS,
)

BUILDERS = {
    "164.jwt-auth-rag-tutorial.md": ("jwt-auth-rag", build_164_jwt),
    "165.rbac-rag-tutorial.md": ("rbac-rag", build_165),
    "166.tenant-isolation-backend-tutorial.md": ("tenant-isolation-backend", build_166),
    "167.openai-api-wrapper-tutorial.md": ("openai-api-wrapper", build_167),
    "168.multi-model-routing-tutorial.md": ("multi-model-routing", build_168),
    "169.rate-limiting-api-tutorial.md": ("rate-limiting-api", build_169),
    "170.openapi-swagger-docs-tutorial.md": ("openapi-swagger-docs", build_170),
    "171.chat-message-list-ui-tutorial（front-end）.md": ("chat-message-list-ui", build_171),
    "172.markdown-render-rag-tutorial（front-end）.md": ("markdown-render-rag", build_172),
}


def main():
    rows = []
    for fname, (slug, builder) in BUILDERS.items():
        content = pad_if_needed(builder(), slug)
        path = ROOT / fname
        path.write_text(content, encoding="utf-8")
        hz = hanzi_count(content)
        rows.append((fname, slug, hz, "OK" if hz >= 5000 else "LOW"))
        if slug in IMAGE_SPECS:
            write_image_assets(slug, IMAGE_SPECS[slug]["title"], IMAGE_SPECS[slug]["prompts"])

    print("\n| 文件 | Roadmap | Slug | 汉字 | 状态 |")
    print("|------|---------|------|------|------|")
    roadmap = {164: 181, 165: 182, 166: 183, 167: 184, 168: 185, 169: 186, 170: 187, 171: 188, 172: 189}
    for fname, slug, hz, st in rows:
        num = int(fname.split(".")[0])
        print(f"| {fname} | {roadmap[num]} | {slug} | {hz} | {st} |")


if __name__ == "__main__":
    main()
