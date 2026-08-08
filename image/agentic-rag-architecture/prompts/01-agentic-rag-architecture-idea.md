---
layout: binary-comparison
style: hand-drawn-edu
aspect_ratio: 16:9
language: zh
---

Create a professional educational infographic.
- Type: Infographic
- Layout: binary-comparison
- Style: hand-drawn-edu
- Aspect Ratio: 16:9
- Language: zh (Simplified Chinese)

## Style Guidelines

Style Guidelines (hand-drawn-edu — MUST follow strictly):
- Background: Warm cream (#F5F0E8) with subtle paper grain texture
- Macaron pastel rounded cards (Mint #B5E5CF, Blue #A8D8EA, Lavender #D5C6E0, Peach #FFD5C2)
- Hand-drawn wavy arrows, stick figures, doodle stars/sparkles
- Hand-lettered Simplified Chinese, legible, organic
- Bold footer banner at bottom with key takeaway
- NO flat corporate vector, NO pure white background

---

Create a professional educational infographic, 16:9 landscape.
Layout: binary-comparison (LEFT vs RIGHT with vertical divider).
Style: hand-drawn-edu, cream #F5F0E8, macaron pastels, stick figures, Simplified Chinese.

Title (top center): Agentic RAG 生产架构核心思想

LEFT SIDE — 普通 RAG（一次检索）:
- 用户任务：对比「高级报表套餐」与「基础套餐」功能差异
- 流程：复杂问题 → 一次向量检索 → 只召回「高级套餐」文档
- 结果：缺少基础套餐证据仍直接生成 → 易幻觉 / 只答一半
- Stick figure looks confused; red X or warning doodle

RIGHT SIDE — Agentic RAG（决策循环）:
- 查询规划：拆成 2 个子查询（高级套餐功能 / 基础套餐功能）
- 第 1 轮检索：仅命中高级套餐证据
- 充分性判断：False（不足）— 原因：「缺少基础套餐证据」
- 动作：继续第 2 轮检索基础套餐（箭头标注「继续检索」）
- 第 2 轮后：两侧证据齐全 → 充分性 True → 再生成答案
- Stick figure with checklist; green check when both sides present

BOTTOM BANNER (bold):
对比类任务：证据未齐不生成；充分性判断是 Agentic RAG 的核心闸门

IMPORTANT: Render ALL text in Simplified Chinese. The RIGHT side must show Sufficiency=False after round 1, NOT True. Fill canvas richly with illustrations.
