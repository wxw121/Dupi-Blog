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

Title: 事件驱动 Agent 架构核心思想

LEFT: 事件驱动 Agent 架构要解决什么
传统轮询模式：
tasks = db.query("SELECT * FROM tasks WHERE state='pending'")
process(task)

RIGHT: 工程化关键点
sleep(1)
问题：
1. 延迟：最坏情况等 1 秒才能发现新任务
