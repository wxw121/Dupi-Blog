---
layout: linear-progression
style: hand-drawn-edu
aspect: 16:9
language: zh
---

Educational linear progression infographic, hand-drawn-edu style, cream paper background, soft macaron pastels, hand-drawn wobble lines, Chinese text, landscape 16:9.

Title at top: 从零启动 my-shop：Compose 推荐流程

Horizontal flow with 6 numbered steps connected by arrows:

Step 1: 检查文件
Icon: folder
Text: 确认有 compose.yaml 和 init.sql

Step 2: 构建镜像
Command: docker compose build
Text: 只 build 不启动，先验证 Dockerfile

Step 3: 后台启动
Command: docker compose up -d
Text: 拉起 db + redis + web

Step 4: 等数据库就绪
Command: docker compose logs -f db
Text: 看到 ready to accept connections

Step 5: 验证接口
Command: curl localhost:8000/health
Text: 再测 /products/count（第一次 db，第二次 cache）

Step 6: 收工清理
Command: docker compose down
Warning badge: 想清空数据库才用 down -v

Bottom note: 失败时先 logs 排错，别急着 down -v

Clean educational diagram, readable Chinese labels, numbered steps left to right.
