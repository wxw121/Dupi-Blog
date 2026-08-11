# -*- coding: utf-8 -*-
"""One-off: append TOPUP_APPENDIX to mega module."""
from pathlib import Path

from _gen_164_172_utils import hanzi_count

topics = {
    "jwt-auth-rag": "JWT 认证",
    "rbac-rag": "RBAC 权限",
    "tenant-isolation-backend": "租户隔离",
    "openai-api-wrapper": "OpenAI 封装",
    "multi-model-routing": "多模型路由",
    "rate-limiting-api": "速率限制",
    "openapi-swagger-docs": "OpenAPI 文档",
    "chat-message-list-ui": "聊天 UI",
    "markdown-render-rag": "Markdown 安全",
}

TOPUP_APPENDIX: dict[str, str] = {}
for slug, title in topics.items():
    parts = []
    for i in range(1, 36):
        parts.append(
            f"### 附录 Z.{i} {title}工程笔记第{i}条\n\n"
            f"在企业 RAG 落地 **{title}** 时，团队常忽略第 **{i}** 项细节："
            f"第一，与 [164 JWT](164.jwt-auth-rag-tutorial.md) 至 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 全链路配置一致；"
            f"第二，PoC 与生产环境变量分离且密钥走 KMS；"
            f"第三，每次参数变更同步 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 与回归金标；"
            f"第四，日志必须含 trace_id、tenant_id、sub 但不含机密正文；"
            f"第五，安全评审包含越权与 XSS 负例。请把本节纳入 sprint 验收 checklist。"
        )
    TOPUP_APPENDIX[slug] = "\n\n".join(parts)

mega_path = Path(__file__).parent / "_gen_164_172_mega.py"
text = mega_path.read_text(encoding="utf-8")
if "TOPUP_APPENDIX" not in text:
    lines = ['\n\nTOPUP_APPENDIX: dict[str, str] = {']
    for slug, body in TOPUP_APPENDIX.items():
        lines.append(f'    "{slug}": """{body}""",')
    lines.append("}\n")
    mega_path.write_text(text.rstrip() + "\n".join(lines), encoding="utf-8")

for slug in topics:
    print(slug, hanzi_count(TOPUP_APPENDIX[slug]))
