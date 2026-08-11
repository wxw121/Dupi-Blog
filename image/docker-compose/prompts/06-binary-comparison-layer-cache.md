---
layout: binary-comparison
style: hand-drawn-edu
aspect: 16:9
language: zh
---

Educational binary comparison infographic, hand-drawn-edu style, cream paper background, soft macaron pastels, hand-drawn wobble lines, Chinese text, landscape 16:9.

Title at top center: Docker 分层缓存：为什么 COPY 要放在后面？

Left column header with red X badge: ❌ 低效写法（先 COPY 全部）
Show vertical layer stack (top to bottom):
Layer 1: FROM python:3.11-slim — green checkmark label: 缓存命中
Layer 2: WORKDIR /app — green checkmark: 缓存命中
Layer 3: COPY . . — orange warning: 代码一改，本层失效
Layer 4: RUN pip install -r requirements.txt — red X: 必须重跑（几分钟）
Small note: 改 main.py 也会触发重装依赖

Right column header with green check badge: ✅ 推荐写法（先 COPY 依赖）
Show vertical layer stack:
Layer 1: FROM python:3.11-slim — green checkmark: 缓存命中
Layer 2: WORKDIR /app — green checkmark: 缓存命中
Layer 3: COPY requirements.txt — green checkmark: 依赖不变则命中
Layer 4: RUN pip install — green checkmark: 跳过安装
Layer 5: COPY . . — orange: 只重拷代码（很快）
Small note: 改 main.py 不用重新 pip install

Center bottom rule box with arrow pointing down:
核心规则：从「变了的层」往下，下面所有层缓存全部作废

Bottom caption: 把 requirements.txt 单独 COPY 并先 pip install，依赖层才能稳定命中缓存

Clean layout, readable Chinese labels, no clutter, educational diagram style.
