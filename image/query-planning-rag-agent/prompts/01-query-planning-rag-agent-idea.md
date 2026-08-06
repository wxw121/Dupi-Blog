---
layout: binary-comparison
style: hand-drawn-edu
aspect_ratio: 16:9
language: zh
---

Create a professional educational infographic, 16:9 landscape.
Layout: binary-comparison.
Style: hand-drawn-edu, cream #F5F0E8, macaron pastels, stick figures, Simplified Chinese.

All text Simplified Chinese. Legible, generous whitespace.

Title: RAG Agent 的 Query Planning核心思想

LEFT: RAG Agent 的 Query Planning要解决什么
你是一个查询规划器。你的任务是把用户的复杂问题拆解成可执行的检索查询。
可用数据源：
- product_docs: 产品文档库，包含功能说明、定价、使用指南。

RIGHT: 工程化关键点
过滤: version (current/legacy), category (pricing/feature/guide)
- audit_logs: 审计日志，包含角色变更、套餐变更、登录记录。
过滤: event_type (role_change/subscription/login), time_range
