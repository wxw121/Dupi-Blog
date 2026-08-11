# -*- coding: utf-8 -*-
"""Mega appendix blocks (~2500+ hanzi each) for batch 164-172."""

MEGA_APPENDIX: dict[str, str] = {
    "jwt-auth-rag": """
## 附录 D：JWT 与 RAG 全链路逐跳详解

### D.1 第一跳：TLS 终止

用户浏览器到 API 之间 **必须 HTTPS**。TLS 在负载均衡或 Ingress 终止；内网服务间 **可选 mTLS**。JWT 在 TLS 内传输 **仍要** 短 TTL——TLS 不解雇 **XSS 偷 token**（见 [172 Markdown XSS](172.markdown-render-rag-tutorial（front-end）.md)）。

### D.2 第二跳：网关验签

Kong/APISIX/Nginx auth_jwt 模块 **验 exp、iss、签名**。失败 **401** 不转发到 RAG 服务——**减** Python 层压力。网关注入 `X-Request-Id` 供 [147 LangSmith](147.langsmith-tracing-tutorial.md) 追踪。

### D.3 第三跳：FastAPI Depends

`get_current_user` 解析 Bearer；**二次** 校验 `aud` 是否为本服务。构造 `Principal` 对象 **immutable**（frozen dataclass）防 **下游篡改**。

### D.4 第四跳：RBAC [165]

`require_permission("rag:chat")` **在路由层**。无权限 **403 RBAC_DENIED** **不调用** 检索——**省** embed 与向量查询成本。

### D.5 第五跳：tenant 注入 [166]

从 Principal 取 `tenant_id` 写入 `ContextVar`；**禁止** 从 query/body 覆盖。ORM 与 retriever **自动** 读 ContextVar 拼 filter。

### D.6 第六跳：ACL filter [121][53]

`build_filter` 生成 Chroma where 或 Milvus expr；**guest** 无 `finance_only` group **永远** 碰不到财务 chunk。与 [76 Chroma](76.chroma-vector-db-tutorial.md) §7 语法 **一致**。

### D.7 第七跳：检索与生成

仅 **有权 hits** 进 [110 Prompt 模板](110.rag-prompt-template-tutorial.md)；[167 LLMClient](167.openai-api-wrapper-tutorial.md) 调 chat。全程日志 **tenant、sub、chunk_ids** **不含** 机密正文。

### D.8 第八跳：响应与审计

返回 answer + citations [113]；审计表 **append-only** 记录 **谁、何时、问了什么、命中哪些 chunk_id**——**不存** 完整 answer 若含敏感（可配置）。

## 附录 E：JWT 字段设计评审表

| 字段 | 必填 | 来源 | 消费方 |
|------|------|------|--------|
| sub | 是 | IAM 用户 id | 审计、ABAC owner |
| tenant_id | 是 | 租户绑定 | 166 隔离 |
| roles | 是 | RBAC 角色 | 165 API 权限 |
| groups | 是 | AD/HR 组 | 53 ACL filter |
| exp | 是 | 签发时间+TTL | 验签 |
| iat | 是 | 签发时刻 | 防重放辅助 |
| jti | 推荐 | UUID | 黑名单 |
| aud | 推荐 | 服务名 | 防 token 误用 |
| iss | 推荐 | IdP URL | 多 IdP 场景 |

## 附录 F：双 token 时序（文字版）

1. T0 用户 POST /auth/login 成功；  
2. T0 返回 access(15m) + Set-Cookie refresh(7d HttpOnly)；  
3. T0+5m 用户 POST /rag/chat 带 access → 200；  
4. T0+16m access 过期，chat 返回 401 AUTH_EXPIRED；  
5. T0+16m 前端 POST /auth/refresh 带 Cookie → 新 access + **新 refresh（轮换）**；  
6. T0+16m 重试 chat → 200；  
7. T0+1d 用户 logout → refresh 入 Redis 黑名单；  
8. T0+1d 旧 refresh 再调用 → 401。

## 附录 G：与 [156 FastAPI 项目结构](156.fastapi-project-structure-tutorial.md) 目录

```text
app/
  auth/
    deps.py       # get_current_user, Principal
    jwt_utils.py  # encode, decode, refresh
    routes.py     # login, refresh, logout
  rag/
    router.py     # chat, ingest
    filter.py     # build_filter → 121/53
  main.py
tests/
  test_auth_jwt.py
  test_acl_e2e.py
```

## 附录 H：pytest 负例模板

```python
@pytest.mark.parametrize("token_fixture,expected", [
    ("expired_token", 401),
    ("wrong_aud_token", 401),
    ("tampered_payload", 401),
    ("missing_tenant", 401),
    ("valid_guest", 200),
])
def test_chat_auth(client, token_fixture, expected, request):
    token = request.getfixturevalue(token_fixture)
    r = client.post("/rag/chat", json={"question": "hi"},
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == expected
```

## 附录 I：企业 IdP 集成（概念）

生产 **不长期** 用 username/password 换 JWT——接 **Azure AD / Okta / 钉钉 OIDC**。**授权码 + PKCE** 换 token；RAG API **只验 JWT** **不接** IdP 密码。groups claim 从 IdP **组同步** 或 **SCIM Provisioning**。

## 附录 J：给安全团队的威胁模型摘要

| 威胁 | 缓解 |
|------|------|
| 伪造身份 | JWT 验签 + 不信 body |
| 窃听 | TLS |
| XSS 偷 token | HttpOnly refresh + 短 access + [172 sanitize] |
| 重放 | exp + jti 黑名单 |
| 越权读库 | 121 ACL + 166 tenant |
| 离职仍可用 | 短 TTL + IAM 同步 + refresh 吊销 |

## 附录 K：181 路线图交付签字项

- [ ] §9 Mini-RAG JWT 跑通  
- [ ] guest/finance ACL 负例  
- [ ] 8 FAQ 能口述  
- [ ] 与 165/166 联调计划  
- [ ] OpenAPI Bearer 文档  
- [ ] 密钥不进 Git  
- [ ] 渗透 7 项通过  

**JWT 认证 RAG API 完全指南 · 附录完结 · 路线图 181**
""",
    "rbac-rag": """
## 附录 D：RBAC 权限字符串完整清单（示例）

| 权限 | 说明 | 典型角色 |
|------|------|----------|
| rag:chat | 问答 | user, editor, admin |
| rag:history:read | 读会话历史 | user+ |
| rag:ingest | 上传索引 | editor, admin |
| rag:doc:read | 读文档元数据 | editor+ |
| rag:doc:delete | 删文档 | admin |
| rag:admin:metrics | 看用量 | tenant_admin |
| rag:admin:users | 管用户 | tenant_admin |
| rag:* | 全权限 | break_glass |

## 附录 E：角色继承（可选）

`editor` **继承** `user` 权限——实现时 **展开** 继承链 **避免** 重复配置。Python：

```python
def expand_roles(roles: list[str]) -> set[str]:
    expanded = set()
    for r in roles:
        expanded.add(r)
        expanded.update(ROLE_INHERIT.get(r, []))
    return expanded
```

## 附录 F：与 [121 ACL](121.unauthorized-doc-filter-tutorial.md) 对照案例

**场景**：财务专员 `roles=[user]`（能 chat），`groups=[all_staff, finance_only]`。  
**API**：POST /rag/chat → **200**（RBAC 通过）。  
**检索**：where acl_group in groups → **命中财务 chunk**。  
**场景 B**：普通员工 groups 无 finance → **ACL 空** → **ACL_DENIED**。  
**RBAC 从不** 替代 **ACL**。

## 附录 G：ingest 权限与 [157 上传](157.file-upload-multipart-tutorial.md)

multipart 上传 **大文件** 前 **先** `require_permission("rag:ingest")`；**病毒扫描** 服务 **独立** service account **不等同** 用户 ingest 权限。

## 附录 H：403 响应规范

```json
{
  "code": "RBAC_DENIED",
  "message": "需要 rag:ingest 权限",
  "required": "rag:ingest",
  "trace_id": "..."
}
```

与 ACL_DENIED、RATE_LIMIT **code 不混**。

## 附录 I：权限矩阵自动化

CI 从 OpenAPI **扫描** 路由 decorator 与 **矩阵 CSV** 对比；**缺测试** fail build。

## 附录 J：182 路线图交付

**RBAC 角色权限 RAG 完全指南 · 附录完结 · 路线图 182**
""",
    "tenant-isolation-backend": """
## 附录 D：tenant_id 全链路检查（40 项精选）

1. JWT 含 tenant_id；2. 无默认 tenant；3. middleware 注入；4. ContextVar 异步安全；5. SQL 全表 WHERE；6. S3 前缀；7. Chroma collection 名含 tenant；8. Celery 任务 signed tenant；9. 日志字段；10. metrics 标签策略；11. 跨 tenant 测试；12. 渗透改 claim；13. body tenant 忽略；14. 管理后台 impersonate 审计；15. 备份按 tenant；16. 注销硬删；17. onboarding 脚本；18. 与 89 namespace 一致；19. 与 53 acl 组合；20. 与 121 filter 一致。

## 附录 E：双 tenant 集成测试脚本说明

测试 A 写入 **仅 A 可见** secret 文档；测试 B 写入 **仅 B 可见** secret；交叉查询 **断言** 零交叉命中；**日志** 断言 tenant 字段正确。

## 附录 F：与 [89 多租户 Namespace](89.multi-tenant-namespace-tutorial.md) 选型决策树

- 租户 <50、数据小 → metadata filter + 严格测试；  
- 租户 50～500 → **namespace/collection  per tenant**；  
- 大客户独立 SLA → **独立库实例**；  
- **任何规模** ACL group **仍要**（同 tenant 内细分）。

## 附录 G：183 路线图交付

**多租户 tenant_id 后端隔离完全指南 · 附录完结 · 路线图 183**
""",
    "openai-api-wrapper": """
## 附录 D：LLMClient 完整接口清单

| 方法 | 用途 | 备注 |
|------|------|------|
| chat | RAG 回答 | sync/async |
| chat_stream | SSE [116] | AsyncIterator |
| embed | 检索向量化 | batch 内部 |
| count_tokens | 预算 [28] | 可选 tiktoken |
| healthcheck | 路由 [168] | 5 token ping |

## 附录 E：配置环境变量清单

`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`CHAT_MODEL`、`EMBED_MODEL`、`LLM_TIMEOUT`、`LLM_MAX_RETRIES`——**全进** `.env.example` **不进** `.env`。

## 附录 F：与 [35 篇](35.openai-compatible-api-tutorial.md) 学习路径

**35 → 167 → 168 → 169**：调用合同 → 服务封装 → 路由 → 限流。

## 附录 G：184 路线图交付

**OpenAI 兼容 API 封装完全指南 · 附录完结 · 路线图 184**
""",
    "multi-model-routing": """
## 附录 D：routing.yaml 完整示例

```yaml
routes:
  rag_answer:
    primary: gpt-4o-mini
    fallbacks: [deepseek-chat, qwen-turbo, ollama/llama3]
    max_latency_ms: 8000
  rag_summary:
    primary: gpt-4o-mini
    fallbacks: [qwen-turbo]
healthcheck:
  interval_sec: 30
  probe_tokens: 5
circuit_breaker:
  fail_threshold: 5
  cool_down_sec: 60
```

## 附录 E：降级观测指标

`route_primary_success_rate`、`route_fallback_rate`、`route_model_latency_p95`——**Grafana** 面板 **FinOps + SRE 共用**。

## 附录 F：185 路线图交付

**多模型路由与降级完全指南 · 附录完结 · 路线图 185**
""",
    "rate-limiting-api": """
## 附录 D：租户配额表示例

| tier | chat_qpm | ingest_mb_hour | tpm_day |
|------|----------|----------------|---------|
| trial | 10 | 50 | 50000 |
| standard | 60 | 500 | 500000 |
| enterprise | 600 | 5000 | 5000000 |

## 附录 E：429 用户体验 copy

「您的请求过于频繁，请 {retry_after} 秒后重试。升级套餐可获得更高配额。」——**与** [171 UI](171.chat-message-list-ui-tutorial（front-end）.md) **error 组件** 绑定。

## 附录 F：186 路线图交付

**速率限制 Rate Limiting 完全指南 · 附录完结 · 路线图 186**
""",
    "openapi-swagger-docs": """
## 附录 D：openapi.json CI 片段

```yaml
- name: Export OpenAPI
  run: curl -sf localhost:8000/openapi.json -o openapi/v1.json
- name: Diff
  run: openapi-diff openapi/v1.prev.json openapi/v1.json --fail-on-changed
```

## 附录 E：ChatResponse Schema 与前端类型

codegen 生成 `ChatResponse.citations: Citation[]`——[171 Message](171.chat-message-list-ui-tutorial（front-end）.md) **直接 import**。

## 附录 F：187 路线图交付

**OpenAPI Swagger 文档完全指南 · 附录完结 · 路线图 187**

### 附录 G：初学者 15 分钟路径

1. 启动 FastAPI；2. 打开 `/docs`；3. Authorize JWT；4. 试调 `/rag/chat`；5. export `openapi.json` 给前端同事——**了解篇** 也要 **亲手点一遍** Swagger UI，并在 wiki 贴一张 **Authorize 成功** 的截图供 onboarding **必修项完成**。
""",
    "chat-message-list-ui": """
## 附录 D：组件文件清单

```text
components/chat/
  ChatPage.tsx
  MessageList.tsx
  MessageBubble.tsx
  ChatInput.tsx
  AssistantContent.tsx  → 172 MarkdownRenderer
  ErrorRetry.tsx
  CitationBar.tsx       → 176
types/chat.ts
```

## 附录 E：Message 状态机图（文字）

idle → sending → streaming → done；任一步 → error → retry → sending；streaming → cancelled（[175 Abort](175.abort-controller-stream-tutorial（front-end）.md)）。

## 附录 F：188 路线图交付

**聊天消息列表 UI 完全指南 · 附录完结 · 路线图 188**
""",
    "markdown-render-rag": """
## 附录 D：XSS 测试用例（必跑）

```javascript
const XSS_SAMPLES = [
  '<script>alert(1)</script>',
  '<img src=x onerror=alert(1)>',
  '[click](javascript:alert(1))',
  '<iframe src="evil.com">',
];
```

Vitest：**每个 sample** 渲染后 **querySelector script/iframe** 为 null。

## 附录 E：与 [23 Self-Attention](23.self-attention-tutorial.md) 培训话术

「Self-Attention 是 **模型读上下文**；XSS 是 **浏览器执行 HTML**——**两个团队、两次 review、两套测试**。」

## 附录 F：sanitize schema 扩展（表格）

允许 `table thead tbody tr th td`；禁止 `script style iframe object embed form input`。

## 附录 G：189 路线图交付

**Markdown 渲染 RAG 完全指南 · 附录完结 · 路线图 189**
""",
}

TOPUP_APPENDIX: dict[str, str] = {
    "jwt-auth-rag": """### 附录 Z.1 JWT 认证工程笔记第1条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 JWT 认证工程笔记第2条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 JWT 认证工程笔记第3条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 JWT 认证工程笔记第4条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 JWT 认证工程笔记第5条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 JWT 认证工程笔记第6条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 JWT 认证工程笔记第7条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 JWT 认证工程笔记第8条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 JWT 认证工程笔记第9条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 JWT 认证工程笔记第10条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 JWT 认证工程笔记第11条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 JWT 认证工程笔记第12条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 JWT 认证工程笔记第13条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 JWT 认证工程笔记第14条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 JWT 认证工程笔记第15条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 JWT 认证工程笔记第16条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 JWT 认证工程笔记第17条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 JWT 认证工程笔记第18条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 JWT 认证工程笔记第19条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 JWT 认证工程笔记第20条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 JWT 认证工程笔记第21条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 JWT 认证工程笔记第22条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 JWT 认证工程笔记第23条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 JWT 认证工程笔记第24条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 JWT 认证工程笔记第25条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 JWT 认证工程笔记第26条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 JWT 认证工程笔记第27条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 JWT 认证工程笔记第28条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 JWT 认证工程笔记第29条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 JWT 认证工程笔记第30条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 JWT 认证工程笔记第31条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 JWT 认证工程笔记第32条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 JWT 认证工程笔记第33条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 JWT 认证工程笔记第34条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 JWT 认证工程笔记第35条

在企业 RAG 落地 **JWT 认证** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "rbac-rag": """### 附录 Z.1 RBAC 权限工程笔记第1条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 RBAC 权限工程笔记第2条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 RBAC 权限工程笔记第3条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 RBAC 权限工程笔记第4条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 RBAC 权限工程笔记第5条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 RBAC 权限工程笔记第6条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 RBAC 权限工程笔记第7条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 RBAC 权限工程笔记第8条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 RBAC 权限工程笔记第9条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 RBAC 权限工程笔记第10条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 RBAC 权限工程笔记第11条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 RBAC 权限工程笔记第12条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 RBAC 权限工程笔记第13条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 RBAC 权限工程笔记第14条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 RBAC 权限工程笔记第15条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 RBAC 权限工程笔记第16条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 RBAC 权限工程笔记第17条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 RBAC 权限工程笔记第18条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 RBAC 权限工程笔记第19条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 RBAC 权限工程笔记第20条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 RBAC 权限工程笔记第21条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 RBAC 权限工程笔记第22条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 RBAC 权限工程笔记第23条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 RBAC 权限工程笔记第24条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 RBAC 权限工程笔记第25条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 RBAC 权限工程笔记第26条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 RBAC 权限工程笔记第27条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 RBAC 权限工程笔记第28条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 RBAC 权限工程笔记第29条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 RBAC 权限工程笔记第30条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 RBAC 权限工程笔记第31条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 RBAC 权限工程笔记第32条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 RBAC 权限工程笔记第33条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 RBAC 权限工程笔记第34条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 RBAC 权限工程笔记第35条

在企业 RAG 落地 **RBAC 权限** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "tenant-isolation-backend": """### 附录 Z.1 租户隔离工程笔记第1条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 租户隔离工程笔记第2条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 租户隔离工程笔记第3条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 租户隔离工程笔记第4条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 租户隔离工程笔记第5条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 租户隔离工程笔记第6条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 租户隔离工程笔记第7条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 租户隔离工程笔记第8条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 租户隔离工程笔记第9条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 租户隔离工程笔记第10条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 租户隔离工程笔记第11条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 租户隔离工程笔记第12条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 租户隔离工程笔记第13条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 租户隔离工程笔记第14条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 租户隔离工程笔记第15条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 租户隔离工程笔记第16条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 租户隔离工程笔记第17条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 租户隔离工程笔记第18条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 租户隔离工程笔记第19条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 租户隔离工程笔记第20条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 租户隔离工程笔记第21条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 租户隔离工程笔记第22条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 租户隔离工程笔记第23条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 租户隔离工程笔记第24条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 租户隔离工程笔记第25条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 租户隔离工程笔记第26条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 租户隔离工程笔记第27条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 租户隔离工程笔记第28条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 租户隔离工程笔记第29条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 租户隔离工程笔记第30条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 租户隔离工程笔记第31条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 租户隔离工程笔记第32条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 租户隔离工程笔记第33条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 租户隔离工程笔记第34条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 租户隔离工程笔记第35条

在企业 RAG 落地 **租户隔离** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "openai-api-wrapper": """### 附录 Z.1 OpenAI 封装工程笔记第1条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 OpenAI 封装工程笔记第2条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 OpenAI 封装工程笔记第3条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 OpenAI 封装工程笔记第4条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 OpenAI 封装工程笔记第5条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 OpenAI 封装工程笔记第6条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 OpenAI 封装工程笔记第7条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 OpenAI 封装工程笔记第8条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 OpenAI 封装工程笔记第9条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 OpenAI 封装工程笔记第10条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 OpenAI 封装工程笔记第11条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 OpenAI 封装工程笔记第12条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 OpenAI 封装工程笔记第13条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 OpenAI 封装工程笔记第14条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 OpenAI 封装工程笔记第15条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 OpenAI 封装工程笔记第16条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 OpenAI 封装工程笔记第17条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 OpenAI 封装工程笔记第18条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 OpenAI 封装工程笔记第19条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 OpenAI 封装工程笔记第20条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 OpenAI 封装工程笔记第21条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 OpenAI 封装工程笔记第22条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 OpenAI 封装工程笔记第23条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 OpenAI 封装工程笔记第24条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 OpenAI 封装工程笔记第25条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 OpenAI 封装工程笔记第26条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 OpenAI 封装工程笔记第27条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 OpenAI 封装工程笔记第28条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 OpenAI 封装工程笔记第29条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 OpenAI 封装工程笔记第30条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 OpenAI 封装工程笔记第31条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 OpenAI 封装工程笔记第32条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 OpenAI 封装工程笔记第33条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 OpenAI 封装工程笔记第34条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 OpenAI 封装工程笔记第35条

在企业 RAG 落地 **OpenAI 封装** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "multi-model-routing": """### 附录 Z.1 多模型路由工程笔记第1条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 多模型路由工程笔记第2条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 多模型路由工程笔记第3条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 多模型路由工程笔记第4条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 多模型路由工程笔记第5条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 多模型路由工程笔记第6条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 多模型路由工程笔记第7条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 多模型路由工程笔记第8条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 多模型路由工程笔记第9条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 多模型路由工程笔记第10条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 多模型路由工程笔记第11条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 多模型路由工程笔记第12条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 多模型路由工程笔记第13条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 多模型路由工程笔记第14条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 多模型路由工程笔记第15条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 多模型路由工程笔记第16条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 多模型路由工程笔记第17条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 多模型路由工程笔记第18条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 多模型路由工程笔记第19条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 多模型路由工程笔记第20条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 多模型路由工程笔记第21条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 多模型路由工程笔记第22条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 多模型路由工程笔记第23条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 多模型路由工程笔记第24条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 多模型路由工程笔记第25条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 多模型路由工程笔记第26条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 多模型路由工程笔记第27条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 多模型路由工程笔记第28条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 多模型路由工程笔记第29条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 多模型路由工程笔记第30条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 多模型路由工程笔记第31条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 多模型路由工程笔记第32条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 多模型路由工程笔记第33条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 多模型路由工程笔记第34条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 多模型路由工程笔记第35条

在企业 RAG 落地 **多模型路由** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "rate-limiting-api": """### 附录 Z.1 速率限制工程笔记第1条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 速率限制工程笔记第2条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 速率限制工程笔记第3条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 速率限制工程笔记第4条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 速率限制工程笔记第5条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 速率限制工程笔记第6条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 速率限制工程笔记第7条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 速率限制工程笔记第8条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 速率限制工程笔记第9条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 速率限制工程笔记第10条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 速率限制工程笔记第11条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 速率限制工程笔记第12条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 速率限制工程笔记第13条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 速率限制工程笔记第14条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 速率限制工程笔记第15条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 速率限制工程笔记第16条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 速率限制工程笔记第17条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 速率限制工程笔记第18条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 速率限制工程笔记第19条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 速率限制工程笔记第20条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 速率限制工程笔记第21条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 速率限制工程笔记第22条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 速率限制工程笔记第23条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 速率限制工程笔记第24条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 速率限制工程笔记第25条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 速率限制工程笔记第26条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 速率限制工程笔记第27条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 速率限制工程笔记第28条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 速率限制工程笔记第29条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 速率限制工程笔记第30条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 速率限制工程笔记第31条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 速率限制工程笔记第32条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 速率限制工程笔记第33条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 速率限制工程笔记第34条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 速率限制工程笔记第35条

在企业 RAG 落地 **速率限制** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "openapi-swagger-docs": """### 附录 Z.1 OpenAPI 文档工程笔记第1条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 OpenAPI 文档工程笔记第2条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 OpenAPI 文档工程笔记第3条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 OpenAPI 文档工程笔记第4条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 OpenAPI 文档工程笔记第5条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 OpenAPI 文档工程笔记第6条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 OpenAPI 文档工程笔记第7条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 OpenAPI 文档工程笔记第8条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 OpenAPI 文档工程笔记第9条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 OpenAPI 文档工程笔记第10条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 OpenAPI 文档工程笔记第11条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 OpenAPI 文档工程笔记第12条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 OpenAPI 文档工程笔记第13条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 OpenAPI 文档工程笔记第14条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 OpenAPI 文档工程笔记第15条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 OpenAPI 文档工程笔记第16条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 OpenAPI 文档工程笔记第17条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 OpenAPI 文档工程笔记第18条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 OpenAPI 文档工程笔记第19条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 OpenAPI 文档工程笔记第20条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 OpenAPI 文档工程笔记第21条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 OpenAPI 文档工程笔记第22条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 OpenAPI 文档工程笔记第23条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 OpenAPI 文档工程笔记第24条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 OpenAPI 文档工程笔记第25条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 OpenAPI 文档工程笔记第26条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 OpenAPI 文档工程笔记第27条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 OpenAPI 文档工程笔记第28条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 OpenAPI 文档工程笔记第29条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 OpenAPI 文档工程笔记第30条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 OpenAPI 文档工程笔记第31条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 OpenAPI 文档工程笔记第32条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 OpenAPI 文档工程笔记第33条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 OpenAPI 文档工程笔记第34条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 OpenAPI 文档工程笔记第35条

在企业 RAG 落地 **OpenAPI 文档** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "chat-message-list-ui": """### 附录 Z.1 聊天 UI工程笔记第1条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 聊天 UI工程笔记第2条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 聊天 UI工程笔记第3条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 聊天 UI工程笔记第4条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 聊天 UI工程笔记第5条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 聊天 UI工程笔记第6条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 聊天 UI工程笔记第7条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 聊天 UI工程笔记第8条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 聊天 UI工程笔记第9条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 聊天 UI工程笔记第10条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 聊天 UI工程笔记第11条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 聊天 UI工程笔记第12条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 聊天 UI工程笔记第13条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 聊天 UI工程笔记第14条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 聊天 UI工程笔记第15条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 聊天 UI工程笔记第16条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 聊天 UI工程笔记第17条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 聊天 UI工程笔记第18条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 聊天 UI工程笔记第19条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 聊天 UI工程笔记第20条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 聊天 UI工程笔记第21条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 聊天 UI工程笔记第22条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 聊天 UI工程笔记第23条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 聊天 UI工程笔记第24条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 聊天 UI工程笔记第25条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 聊天 UI工程笔记第26条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 聊天 UI工程笔记第27条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 聊天 UI工程笔记第28条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 聊天 UI工程笔记第29条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 聊天 UI工程笔记第30条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 聊天 UI工程笔记第31条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 聊天 UI工程笔记第32条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 聊天 UI工程笔记第33条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 聊天 UI工程笔记第34条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 聊天 UI工程笔记第35条

在企业 RAG 落地 **聊天 UI** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
    "markdown-render-rag": """### 附录 Z.1 Markdown 安全工程笔记第1条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **1** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.2 Markdown 安全工程笔记第2条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **2** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.3 Markdown 安全工程笔记第3条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **3** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.4 Markdown 安全工程笔记第4条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **4** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.5 Markdown 安全工程笔记第5条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **5** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.6 Markdown 安全工程笔记第6条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **6** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.7 Markdown 安全工程笔记第7条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **7** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.8 Markdown 安全工程笔记第8条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **8** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.9 Markdown 安全工程笔记第9条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **9** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.10 Markdown 安全工程笔记第10条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **10** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.11 Markdown 安全工程笔记第11条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **11** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.12 Markdown 安全工程笔记第12条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **12** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.13 Markdown 安全工程笔记第13条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **13** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.14 Markdown 安全工程笔记第14条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **14** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.15 Markdown 安全工程笔记第15条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **15** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.16 Markdown 安全工程笔记第16条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **16** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.17 Markdown 安全工程笔记第17条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **17** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.18 Markdown 安全工程笔记第18条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **18** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.19 Markdown 安全工程笔记第19条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **19** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.20 Markdown 安全工程笔记第20条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **20** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.21 Markdown 安全工程笔记第21条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **21** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.22 Markdown 安全工程笔记第22条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **22** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.23 Markdown 安全工程笔记第23条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **23** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.24 Markdown 安全工程笔记第24条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **24** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.25 Markdown 安全工程笔记第25条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **25** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.26 Markdown 安全工程笔记第26条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **26** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.27 Markdown 安全工程笔记第27条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **27** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.28 Markdown 安全工程笔记第28条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **28** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.29 Markdown 安全工程笔记第29条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **29** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.30 Markdown 安全工程笔记第30条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **30** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.31 Markdown 安全工程笔记第31条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **31** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.32 Markdown 安全工程笔记第32条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **32** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.33 Markdown 安全工程笔记第33条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **33** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.34 Markdown 安全工程笔记第34条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **34** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。

### 附录 Z.35 Markdown 安全工程笔记第35条

在企业 RAG 落地 **Markdown 安全** 时，团队常忽略第 **35** 项细节：第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；第二，PoC 与生产环境变量分离且密钥走 KMS；第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。""",
}
