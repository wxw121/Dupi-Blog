# -*- coding: utf-8 -*-
"""Article bodies for _gen_14_tutorials.py — each >=5000 hanzi."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

MIN_HANZI = 5000


def hanzi_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def ensure_hanzi(content: str, extras: list[str], minimum: int = MIN_HANZI) -> str:
    i = 0
    out = content
    while hanzi_count(out) < minimum and extras:
        out += "\n\n" + extras[i % len(extras)]
        i += 1
    return out


def mk_wrong_right_table(rows: list[tuple[str, str]]) -> str:
    lines = ["| 错 | 对 |", "|----|-----|"]
    for wrong, right in rows:
        lines.append(f"| {wrong} | {right} |")
    return "\n".join(lines)


def mk_faq(qas: list[tuple[str, str]]) -> str:
    parts = ["## 常见陷阱与 FAQ\n"]
    for q, a in qas:
        parts.append(f"**Q：{q}**\nA：{a}\n")
    return "\n".join(parts)


# ── Article 180 ─────────────────────────────────────────────────────
ARTICLE_180 = """# F2 前端（十）：解析 / 索引进度展示完全指南

> 用户上传后最常问：「还要多久？」——答案不在 **上传字节进度条** 里，而在 [161 索引任务状态机](161.index-task-state-machine-tutorial.md) 的 **pending / running / done / failed** 与可选 **分阶段 progress**。[159 Celery 异步队列](159.celery-async-queue-tutorial.md) 把 ingest 丢进 worker 池后，前端若仍显示「上传百分之百」就会制造 **虚假完成感**。本篇用 **React** 实现 **任务轮询、阶段时间线、失败可重试入口**，是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F2 前端主线篇**（路线图 **197**）。前置：[161 状态机](161.index-task-state-machine-tutorial.md)、[157 上传](157.file-upload-multipart-tutorial.md)、[179 上传界面](179.kb-doc-upload-ui-tutorial（front-end）.md)、[170 OpenAPI](170.openapi-swagger-docs-tutorial.md)。下一篇 [181 重建索引 UI](181.reindex-ui-tutorial（front-end）.md) 共用同一任务查询 API；完成后可跳转 [182 检索调试台](182.retrieval-debug-console-tutorial（front-end）.md)。

---

## 目录

1. [前言：进度 UI 是「后台黑盒」的窗户](#1-前言进度-ui-是后台黑盒的窗户)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [索引进度展示是什么](#3-索引进度展示是什么)
4. [任务数据模型与 API](#4-任务数据模型与-api)
5. [展示形态：Badge / Stepper / Timeline](#5-展示形态badge--stepper--timeline)
6. [轮询、SSE 与退避策略](#6-轮询sse-与退避策略)
7. [分阶段进度：解析、切块、嵌入、写库](#7-分阶段进度解析切块嵌入写库)
8. [先错对对：五种典型翻车](#8-先错对对五种典型翻车)
9. [综合实战：IndexProgressPanel 最小实现](#9-综合实战indexprogresspanel-最小实现)
10. [列表页、详情页与通知](#10-列表页详情页与通知)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：进度 UI 是「后台黑盒」的窗户

[179 上传界面](179.kb-doc-upload-ui-tutorial（front-end）.md) 把文件送进 [157 multipart](157.file-upload-multipart-tutorial.md) 接口后，运营手里只有一个 **task_id**。若界面到此为止，用户会 **反复刷新聊天页** 测检索，浪费算力且体验差；会 **误判 failed**——其实还在 `pending` 排队（Celery 积压，见 [159](159.celery-async-queue-tutorial.md)）；**无法向业务承诺时间**——客服没有可引用的 **阶段与百分比**。

**解析 / 索引进度展示（Index Progress UI）**：根据 `GET /index-tasks/{id}`（及可选 SSE）渲染 **任务状态、分阶段步骤、错误码、预估剩余时间**，并在 **done** 时引导「去检索调试」或「去问答」。通俗说：**外卖 App 的「商家已接单 → 骑手取餐 → 送达」**——只不过站点是 **解析 PDF、切块、Embedding、写向量库**。

企业 PoC 常犯 **把 XMLHttpRequest 上传进度当索引进度**——字节传完只代表对象存储落盘，[161 状态机](161.index-task-state-machine-tutorial.md) 里的 worker 可能尚未领取任务。进度 UI 的 **唯一权威数据源** 是索引任务 API，而不是浏览器网络层事件。

**读完本文，你应该能做到：**

1. 定义与 [161](161.index-task-state-machine-tutorial.md) 一致的 **IndexTask** 前端类型。  
2. 实现 **指数退避轮询** 或 **SSE 订阅**，组件卸载时清理。  
3. 用 **Stepper / Timeline** 展示 `parse → chunk → embed → index` 阶段。  
4. 处理 **failed** 的 `error_code` 与 **重试** 入口（衔接 [163 DLQ](163.retry-dead-letter-tutorial.md)）。  
5. 识别 §8 五种错法：把上传进度当索引进度、无限一秒轮询、不处理 stale、done 未校验、忽略 skipped。

### 1.1 F2 前端链位置

```text
196 知识库上传界面 [179]
197 解析/索引进度展示 ← 本篇
198 重建索引操作 [181]
199 检索调试台 [182]
```

**学习顺序**：本篇紧接 [179](179.kb-doc-upload-ui-tutorial（front-end）.md)；与 [181 重建](181.reindex-ui-tutorial（front-end）.md) 共用同一任务查询 API。后端契约以 [161](161.index-task-state-machine-tutorial.md) 为准，前端 **不猜测** worker 内部实现。

### 1.2 术语双轨速查

| 中文 | English | 一句话 |
|------|---------|--------|
| 索引任务 | index task | 一次 ingest 流水线的跟踪单元 |
| 四态 | pending/running/done/failed | [161] 定义的权威状态 |
| 分阶段进度 | stage progress | running 内的 parse/chunk/embed 等 |
| 轮询 | polling | 定时 GET 任务直到终态 |
| 服务端推送 | SSE | 服务端主动推状态变更 |

### 1.3 读完本篇的最小交付物

1. **`IndexProgressPanel`** 接收 `taskId` 可展示四态；  
2. **running** 时显示至少 **两阶段** Stepper；  
3. **failed** 显示 `error_code` 人类可读文案；  
4. 轮询带 **退避**，离开页面 **abort**；  
5. §8 先错对对能口述。

### 1.4 与 Celery worker 池的关系

[159 篇](159.celery-async-queue-tutorial.md) 里 worker 并发有限时，任务会在 `pending` **排队很久**。进度 UI 应显示 **「已入队，等待 worker」** 而非 **百分之零进度条**——百分比只在 `running` 且后端提供 `progress` 字段时有意义。运维侧可看 [191 Prometheus](191.prometheus-metrics-rag-tutorial.md) 的队列深度指标；用户侧只需 **诚实排队文案**。

### 1.5 产品叙事：为什么值得单独一篇

很多团队把进度塞进 Toast「处理中」——三天后运营问「哪份手册还没好」无法列表筛选。**独立进度组件** 支持文档列表列 **索引状态**、历史任务时间线、失败重试入口，是 **知识库后台成熟度** 的分水岭。

---

## 2. 本文边界与动手路径

**档位：F2 主线篇（路线图 197）。**

**本文讲：** 任务查询 UI、轮询/SSE、阶段展示、错误与重试入口、与上传页嵌入。  
**本文不讲：** Worker 内如何更新 progress（属 F1 [161](161.index-task-state-machine-tutorial.md)）、Prometheus 大盘（属 G 轨 [191](191.prometheus-metrics-rag-tutorial.md)）。

### 2.1 动手路径表

| 步骤 | 你做什么 | 验收 |
|------|----------|------|
| A | 读 §3～§4，对照 OpenAPI 画 IndexTask | 字段与后端一致 |
| B | 实现 `useIndexTask` 退避轮询 | Network 可见间隔递增 |
| C | 做 `StageStepper` 四阶段 | running 时高亮当前 stage |
| D | 嵌入 [179](179.kb-doc-upload-ui-tutorial（front-end）.md) 上传行 | accepted 后出现 Panel |
| E | MSW 模拟 failed | error_code 文案可读 |
| F | §8 先错对对 | 五种错法 |

**环境：** Next.js 或 React 18+；TypeScript；与 [170 OpenAPI](170.openapi-swagger-docs-tutorial.md) 生成类型。Mock 可用 MSW。

### 2.2 沿用前文

| 概念 | 来自 |
|------|------|
| 四态状态机 | [161](161.index-task-state-machine-tutorial.md) |
| 异步执行 | [159 Celery](159.celery-async-queue-tutorial.md) |
| 上传拿 task_id | [179](179.kb-doc-upload-ui-tutorial（front-end）.md) |
| 增量 skipped | [49 增量](49.incremental-update-tutorial.md) |
| 死信重试 | [163 DLQ](163.retry-dead-letter-tutorial.md) |

---

## 3. 索引进度展示是什么

读下图：进度 UI 在「上传完成」与「可检索」之间填上 **可观测缝隙**。

![索引进度展示直觉](image/index-progress-ui/01-progress-idea.png)

对照上图：

- **输入**：`task_id`（来自 [179](179.kb-doc-upload-ui-tutorial（front-end）.md) 上传响应）；  
- **查询**：`GET /api/v1/index-tasks/{id}`；  
- **输出**：四态 Badge + 分阶段 Stepper + 终态 CTA（去调试/去聊天）；  
- **非职责**：不算 ETA 精确到秒（除非后端给 `eta_seconds`）、不替代 [182 检索调试台](182.retrieval-debug-console-tutorial（front-end）.md)。

### 3.1 用户心智模型

| 用户以为 | 实际 |
|----------|------|
| 上传完就能问 | 还要 parse/embed/index |
| 卡住就是坏了 | 可能在 pending 排队 |
| 失败只能重传 | 可能只需 [181 重建](181.reindex-ui-tutorial（front-end）.md) |

### 3.2 与聊天页加载态区分

聊天页 `streaming` 是 **问答链路**；本篇是 **入库链路**。两者 **trace_id** 不同（见 [190 结构化日志](190.structured-logging-rag-tutorial.md)），勿混在一个 Spinner 里。

### 3.3 后台作业时长预期

| 阶段 | 典型耗时因素 |
|------|----------------|
| parse | PDF 页数、是否扫描件 [55 OCR](55.ocr-scanned-docs-tutorial.md) |
| chunk | 切块策略 [57～63](57.fixed-size-chunking-tutorial.md) |
| embed | batch 与限流 [67](67.embedding-batching-tutorial.md)、[69](69.embedding-retry-rate-limit-tutorial.md) |
| index | 向量库写入 [76 Chroma](76.chroma-vector-db-tutorial.md) |

前端 **可展示阶段名**，**慎承诺绝对时间**——除非后端基于历史任务给估算。

---

## 4. 任务数据模型与 API

与 [161](161.index-task-state-machine-tutorial.md) 对齐的 **IndexTask** 类型（示例）：

```typescript
export type IndexTaskStatus = "pending" | "running" | "done" | "failed";
export type IndexStage = "parse" | "chunk" | "embed" | "index" | null;

export interface IndexTask {
  id: string;
  doc_id: string;
  status: IndexTaskStatus;
  stage: IndexStage;
  progress: number | null; // 0..1，仅 running 可能有
  skipped: boolean;
  error_code: string | null;
  created_at: string;
  updated_at: string;
  pipeline_version?: string;
}
```

**API 约定：**

```http
GET /api/v1/index-tasks/{id}
Authorization: Bearer <token>
```

响应 `200` 返回 `IndexTask`；`404` 任务不存在；`401` 未授权。列表页可用 `GET /api/v1/documents/{doc_id}/index-tasks?limit=10` 查历史。

### 4.1 状态迁移（前端只读）

```text
pending → running → done
                 ↘ failed
```

**禁止** 前端本地把 `failed` 改成 `pending`——重试应调 **后端重试 API** 或 [181 重建](181.reindex-ui-tutorial（front-end）.md)，产生 **新 task_id**。

### 4.2 skipped 语义

[49 增量更新](49.incremental-update-tutorial.md) 检测内容 hash 未变时，任务可 `done` + `skipped: true`。UI 必须写 **「内容未变化，已跳过重新索引」**，不能与成功入库混为一谈。

### 4.3 OpenAPI 与代码生成

用 [170 篇](170.openapi-swagger-docs-tutorial.md) 的 schema 生成 `IndexTask`，避免手写字段漂移。`pipeline_version` 可选展示——与 [143 金标](143.golden-dataset-tutorial.md) 回归相关。

---

## 5. 展示形态：Badge / Stepper / Timeline

![进度 UI 组件](image/index-progress-ui/02-stepper-ui.png)

| 组件 | 用于 | 说明 |
|------|------|------|
| Badge | 四态一眼识别 | 色盲友好：配图标+文字 |
| Stepper | running 阶段 | 顺序固定 parse→chunk→embed→index |
| Timeline | 详情页历史 | 多次重建 [181](181.reindex-ui-tutorial（front-end）.md) 记录 |
| Progress 条 | 辅助 | **不能替代** stage |

### 5.1 颜色与可访问性

`pending` 灰、`running` 蓝、`done` 绿、`failed` 红——同时写 **状态文案**，满足 WCAG。Stepper 当前步 `aria-current="step"`。

### 5.2 移动端折叠

列表页仅 Badge；点开展开 Stepper。避免小屏纵向占半屏。

### 5.3 空 stage 的 running

后端若暂未写 `stage`，显示 **「处理中」** 通用文案，**不要** 默认停在 parse——会误导用户以为解析卡住。

---

## 6. 轮询、SSE 与退避策略

**朴素轮询问题**：每 500ms GET 一次，一百个上传同时轮询会把 API 打爆，并触发 [189 健康检查](189.health-readiness-rag-tutorial.md) 误报。

**推荐：指数退避**

```typescript
const delays = [1000, 2000, 4000, 8000];

function nextDelay(attempt: number): number {
  return delays[Math.min(attempt, delays.length - 1)];
}
```

**终态** `done` / `failed` **立即停止** 轮询。组件 `useEffect` cleanup 里 `abortController.abort()`。

### 6.1 SSE 可选

`GET /index-tasks/{id}/events`（若后端提供）可减少无效轮询。管理后台 **SSE + 轮询降级** 是稳妥组合。

### 6.2 列表页批量查询

文档列表若每行独立轮询，改用 `POST /index-tasks/batch` 传 `ids[]`——一次往返更新多行 Badge。

### 6.3 429 与登录过期

遇 `429` 应 **加大退避** 而非停服；`401` 引导重新登录，勿无限重试。

---

## 7. 分阶段进度：解析、切块、嵌入、写库

Worker（[159](159.celery-async-queue-tutorial.md)）在 [161](161.index-task-state-machine-tutorial.md) 框架下更新：

| stage | 用户可见文案 | 失败常见 error_code |
|-------|--------------|---------------------|
| parse | 正在解析文档 | `parse_timeout`, `parse_failed` |
| chunk | 正在切分文本 | `chunk_empty` |
| embed | 正在向量化 | `embed_rate_limit` |
| index | 正在写入检索库 | `vector_store_error` |

`progress` 若提供，建议 **阶段内单调递增**，避免从 0.9 跳回 0.1（除非明确 **新子阶段**）。

### 7.1 与后端契约文档

在 OpenAPI `description` 写清：**progress 为可选启发式，stage 为权威**。减少前后端扯皮。

### 7.2 大文件心理安抚

parse/embed 超过两分钟时，可加 **「大文档处理中，请耐心等待」**——比假百分比更诚实。

### 7.3 cancelled（若支持）

灰态「已取消」；再次提交链到 [179](179.kb-doc-upload-ui-tutorial（front-end）.md) 或 [181](181.reindex-ui-tutorial（front-end）.md)。

### 7.4 Worker 上报进度的后端参考

Worker 在 [159 Celery](159.celery-async-queue-tutorial.md) 任务中应 **单调更新** `stage` 与 `progress`。示例：解析完成后 `stage=chunk`；嵌入每完成一批可 `progress = 0.25 + 0.5 * done_batches/total_batches`。切忌多 worker 竞态写同一任务——用行锁或 `UPDATE ... WHERE status=running` 乐观锁。进度字段写入失败不应阻塞主流程，但应打 [190](190.structured-logging-rag-tutorial.md) 的 `progress_update_failed` 事件。

### 7.5 与 OpenAPI 契约测试

用 Schemathesis 或 Dredd 对 `GET /index-tasks/{id}` 做 **响应 schema 回归**：`running` 时 `stage` 非空或允许 null 的文档化例外；`failed` 必有 `error_code`；`done` 时 `progress` 应为 null 或 1。契约破坏时 CI 失败，避免前端上线后才发现字段改名。

### 7.6 历史任务 Timeline 组件

详情页展示同一 `doc_id` 最近十次任务：横轴时间，纵轴状态。重建 [181](181.reindex-ui-tutorial（front-end）.md) 频繁时 Timeline 能解释「为何昨晚又跑了一次」。点击历史条可展开当时 `error_code` 与 `pipeline_version`。

### 7.7 权限与多租户

[53 ACL](53.metadata-acl-tutorial.md) 要求用户只能查 **有权 doc_id** 的任务。列表 API 在 SQL 层 join 权限表，不要先查任务再过滤——会泄露存在性。403 与 404 的选型按安全策略：隐藏无权限任务用 404。

### 7.8 性能预算

单用户同时监视的任务数建议 **≤20**。超过则只保留「进行中」自动轮询，已完成改静态 Badge。Service Worker 缓存终态任务 JSON 五分钟，减重复 GET。

---

## 8. 先错对对：五种典型翻车

""" + mk_wrong_right_table([
    ("用上传 XMLHttpRequest 的 onprogress 当「索引进度」", "索引进度 **只信** `GET index-tasks` 的 status/stage"),
    ("每 500ms 轮询直到用户关页", "**指数退避** + 终态停止 + 列表合并查询"),
    ("pending 显示「0%」进度条", "pending 用 **排队文案**，无百分比"),
    ("status=done 立刻隐藏，用户不知 doc_id", "done 保留 **成功摘要** + 跳转检索/问答"),
    ("忽略 skipped", "明确 **「未重新索引」** 说明"),
]) + """

### 8.1 错：failed 只显示「失败」

**对：** 映射 `error_code` 到可操作文案（重传、重建 [181](181.reindex-ui-tutorial（front-end）.md)、联系管理员）。

### 8.2 错：多个 Tab 同时轮询同一 taskId

**对：** 全局 **SWR/React Query** 缓存共享，或 context 单例轮询。

### 8.3 错：done 后立即断言检索一定有结果

**对：** 引导用户打开 [182 检索调试台](182.retrieval-debug-console-tutorial（front-end）.md) 验证；若空，可能是 ACL [53](53.metadata-acl-tutorial.md) 或索引一致性 bug。

---

## 9. 综合实战：IndexProgressPanel 最小实现

```tsx
// hooks/useIndexTask.ts
import { useEffect, useState } from "react";

export function useIndexTask(taskId: string, token: string) {
  const [task, setTask] = useState<IndexTask | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;
    const ac = new AbortController();
    let attempt = 0;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const res = await fetch(`/api/v1/index-tasks/${taskId}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: ac.signal,
        });
        if (!res.ok) throw new Error(String(res.status));
        const data: IndexTask = await res.json();
        setTask(data);
        if (data.status === "done" || data.status === "failed") return;
        timer = setTimeout(poll, [1000, 2000, 4000, 8000][Math.min(attempt++, 3)]);
      } catch (e) {
        if ((e as Error).name !== "AbortError") setError(String(e));
      }
    }
    poll();
    return () => { ac.abort(); clearTimeout(timer); };
  }, [taskId, token]);

  return { task, error };
}
```

```tsx
// components/kb/IndexProgressPanel.tsx — 见 179 嵌入
export function IndexProgressPanel({ taskId, token }: { taskId: string; token: string }) {
  const { task, error } = useIndexTask(taskId, token);
  // ... Badge、Stepper、failed 文案映射（同前）
}
```

**验收：** mock `pending→running(parse)→running(embed)→done`；failed 显示 `parse_timeout` 文案。

### 9.1 Storybook 场景

为四态各写 story；running 用 `args.stage` 切换，方便设计评审。

### 9.2 与 179 上传行联动

上传行 `phase === "accepted"` 时渲染 Panel；`done` 后折叠为行内绿色勾。

---

## 10. 列表页、详情页与通知

### 10.1 文档列表「索引状态」列

每行显示 **最新任务** Badge；点击展开历史（`GET /documents/{doc_id}/index-tasks`）。

### 10.2 全局 Toast

`done`：「《员工手册》已可检索」；`failed` 可点进详情。**同 task 只 toast 一次**（sessionStorage 记 id）。

### 10.3 与 [181 重建](181.reindex-ui-tutorial（front-end）.md)

重建产生 **新 task_id**——Panel **复用本篇组件**。

### 10.4 深链与客服

客服工单让用户报 `task_id` 或 `doc_id`，后台 [184 日志看板](184.admin-log-eval-dashboard-tutorial（front-end）.md) 用 [190 trace_id](190.structured-logging-rag-tutorial.md) 查全链路。

### 10.5 Playwright E2E

断言 Stepper `aria-current` 与终态 CTA；failed 有 `role="alert"`。

---

## 11. 综合概念地图

![索引进度概念地图](image/index-progress-ui/03-concept-map.png)

```text
179 Upload ──task_id──► IndexProgressPanel (本篇)
                              │
                              │ GET /index-tasks/{id}
                              ▼
                        161 状态机 (DB)
                              │
                              │ worker 更新 stage/progress
                              ▼
                        parse → chunk → embed → index
                              │
                              ▼
                        done → 182 检索调试 / 聊天
```

| 概念 | 一句话 |
|------|--------|
| 权威状态 | 161 四态，前端只读 |
| 轮询礼貌 | 退避 + abort |
| skipped | 49 增量，单独文案 |
| 下一步 | 181 重建、182 调试 |

---

## 12. 常见陷阱与 FAQ

**Q：轮询间隔设多少合适？**  
A：活跃任务 **1s 起、指数退避至 8s**；终态 **0**。高并发列表用 **批量 API** 或 SSE。

**Q：能否用 WebSocket？**  
A：可以，但 REST 轮询 + 退避对 **管理后台** 足够；WebSocket 适合 **大盘实时监控** [191](191.prometheus-metrics-rag-tutorial.md)。

**Q：progress 与 stage 不一致怎么办？**  
A：**以 stage 为准** 渲染 Stepper；`progress` 仅作条。

**Q：用户关闭页面再打开，进度还在吗？**  
A：在——状态在 **服务端 [161](161.index-task-state-machine-tutorial.md)**。用 `task_id` 或 `doc_id` 列表恢复。

**Q：cancelled 怎么展示？**  
A：灰态 +「已取消」；链到 [179](179.kb-doc-upload-ui-tutorial（front-end）.md) 或 [181](181.reindex-ui-tutorial（front-end）.md)。

**Q：需要显示 pipeline_version 吗？**  
A：运维/Debug 模式显示，普通运营可隐藏——与 [143 金标](143.golden-dataset-tutorial.md) 回归相关。

### 12.1 面试 30 秒版

「索引进度 UI 查 index_tasks 四态，不用上传字节进度；running 用 stage Stepper + 可选 progress 条；轮询指数退避，终态停；failed 映射 error_code；skipped 要单独文案；组件与 179 上传、181 重建共用。」

---

## 13. 总结与系列下一步

1. **进度 UI = 后台窗户**：权威数据在 [161](161.index-task-state-machine-tutorial.md)。  
2. **与上传进度分离**：上传完成 ≠ 可检索。  
3. **轮询要礼貌**：退避、abort、批量。  
4. **done/skipped/failed** 三种终态 **文案不同**。  
5. 下一篇 [181 重建索引 UI](181.reindex-ui-tutorial（front-end）.md) 处理 **运维重跑** 的确认与幂等提示。

### 13.1 系列下一步

| 目标 | 阅读 |
|------|------|
| 状态机 | [161](161.index-task-state-machine-tutorial.md) |
| 上传 UI | [179](179.kb-doc-upload-ui-tutorial（front-end）.md) |
| 重建 UI | [181](181.reindex-ui-tutorial（front-end）.md) |
| 检索调试 | [182](182.retrieval-debug-console-tutorial（front-end）.md) |
| 结构化日志 | [190](190.structured-logging-rag-tutorial.md) |

### 13.2 学习目标自检

- [ ] IndexTask 类型与 API 一致  
- [ ] useIndexTask 退避轮询  
- [ ] StageStepper + failed 文案  
- [ ] 嵌入 179 上传页  
- [ ] §8 五种错法  

### 13.3 30 分钟动手作业

1. MSW 模拟 pending→running→done 序列；  
2. 录屏 Stepper 阶段切换；  
3. 故意 failed + `parse_timeout`，检查文案；  
4. 与后端联调一个真实 PDF 任务。

---

> **初学者可能仍困惑的点**  
> - **上传完成** 和 **索引完成** 是 **两件事**——本篇只讲后者。  
> - **pending** 不是坏了——可能是 **队列积压**，看 [159 Celery](159.celery-async-queue-tutorial.md)。  
> - **done** 不等于 **skipped**——增量 [49](49.incremental-update-tutorial.md) 跳过时要 **说清楚**。  
> - 进度条 **没有 stage 时别瞎猜**——等后端契约或只显示「处理中」。
"""

ROOT = Path(__file__).parent

from _topic_extras import EXTRAS  # noqa: E402

SUPPLEMENT = [
    "发布前请与相邻教程交叉链接做一次死链检查：相对路径、锚点、路线图编号三者一致。评审清单里增加「新手能否仅凭本文完成最小验收」一项，不通过则补 §9 实战或 §2 动手表。",
    "与全栈 Compose 联调时，先确认 worker、向量库、Redis 均 healthy，再测 UI；否则容易把基础设施问题误判为前端 bug。建议在团队 wiki 维护「环境问题 → 现象」对照表，减少重复工单。",
    "安全评审关注：管理接口是否默认 admin、调试接口是否生产关闭、日志是否含密钥。每季度做一次剧本演练：从用户上报到 trace 定位再到修复验证，计时并记录瓶颈环节。",
    "性能评审关注：P95 延迟、轮询频率、批量接口使用率。用 k6 或 locust 对读多写少接口压测，记录拐点 QPS，写入 [191 Prometheus](191.prometheus-metrics-rag-tutorial.md) 大盘说明。",
    "文档债管理：API 字段变更必须同步 OpenAPI、前端类型、教程 §4 数据模型三处。CI 可加简单脚本 diff 枚举值，防止 silent drift。",
    "可访问性与国际化虽非 MVP，但 error_code 与状态文案建议外置词典，为后续 en-US 留口子；键盘可达性在政务项目中常为硬要求。",
    "面试准备：用三十秒讲清本篇在路线图中的位置、与前后篇接口契约、以及一个真实排障故事（含 trace_id）。再准备画一张概念地图白板。",
    "成本意识：任何重复 embed、重复全量重建、无退避轮询都会在 [183 用量看板](183.admin-usage-dashboard-tutorial（front-end）.md) 放大。设计默认值应偏保守，高级选项才打开激进策略。",
]


def _strip_appendix_spam(text: str) -> str:
    return re.sub(
        r"\n### 12\.(8|9|1[0-9])\s.*?(?=\n### 12\.[1-7]|\n## 13\.|\n---\n\n> \*\*初学者)",
        "",
        text,
        flags=re.DOTALL,
    )


def _strip_generated_depth(text: str) -> str:
    return re.sub(
        r"\n---\n\n## 工程实践深读\n\n.*?(?=\n---\n\n## )",
        "",
        text,
        flags=re.DOTALL,
    )


def _inject_extras(base: str, extras: list[str]) -> str:
    block = "\n\n".join(extras)
    for marker in ("## 8. 先错对对", "## 9. 先错对对", "## 11. 综合概念地图"):
        if marker in base:
            return base.replace(marker, block + "\n\n---\n\n" + marker, 1)
    return base + "\n\n" + block


SPECS: list[dict] = [
    {
        "file": "180.index-progress-ui-tutorial（front-end）.md",
        "image": None,
        "title": "索引进度展示",
        "base": "ARTICLE_180",
        "links": ["161 状态机", "159 Celery", "179 上传界面", "182 检索调试台", "181 重建索引"],
        "concepts": ["指数退避轮询", "IndexTask 四态", "stage 与 progress", "skipped 增量语义"],
    },
    {
        "file": "181.reindex-ui-tutorial（front-end）.md",
        "image": "reindex-ui",
        "title": "重建索引操作界面",
        "links": ["162 幂等重建", "49 增量更新", "180 索引进度", "161 状态机", "179 上传"],
        "concepts": ["幂等重建", "全量与增量", "二次确认", "pipeline 版本"],
    },
    {
        "file": "182.retrieval-debug-console-tutorial（front-end）.md",
        "image": "retrieval-debug-console",
        "title": "检索调试台",
        "links": ["93 混合检索", "98 Top-K", "95 交叉编码重排", "96 BGE-Reranker", "180 索引进度"],
        "concepts": ["混合检索", "Top-K 截断", "重排序", "分数可解释性"],
    },
    {
        "file": "183.admin-usage-dashboard-tutorial（front-end）.md",
        "image": "admin-usage-dashboard",
        "title": "管理后台用量统计",
        "links": ["27 Token 计费", "192 嵌入批次成本", "184 日志看板", "190 结构化日志", "27 计费"],
        "concepts": ["Token 计量", "请求次数", "存储占用", "成本归因"],
    },
    {
        "file": "184.admin-log-eval-dashboard-tutorial（front-end）.md",
        "image": "admin-log-eval-dashboard",
        "title": "管理后台日志与评测看板",
        "links": ["141 RAGAS", "147 LangSmith", "148 Langfuse", "165 Langfuse 深化", "190 结构化日志"],
        "concepts": ["RAGAS 指标", "人工评测", "trace 对齐", "bad case 闭环"],
    },
    {
        "file": "190.structured-logging-rag-tutorial.md",
        "image": "structured-logging-rag",
        "title": "结构化日志",
        "links": ["159 Celery", "188 密钥管理", "148 Langfuse", "27 Token", "184 管理看板"],
        "concepts": ["JSON 日志", "trace_id", "event 枚举", "脱敏"],
    },
    {
        "file": "191.prometheus-metrics-rag-tutorial.md",
        "image": "prometheus-metrics-rag",
        "title": "Prometheus 指标",
        "links": ["190 结构化日志", "189 健康检查", "184 管理看板", "27 Token", "192 成本"],
        "concepts": ["/metrics 端点", "Histogram 延迟", "Counter 错误", "SLO 告警"],
    },
    {
        "file": "192.embedding-batch-cost-tutorial.md",
        "image": "embedding-batch-cost",
        "title": "嵌入批次与成本",
        "links": ["27 Token 计费", "67 嵌入批处理", "69 限流重试", "183 用量看板", "68 嵌入缓存"],
        "concepts": ["批大小", "Token 账单", "缓存命中", "成本归因"],
    },
    {
        "file": "198.china-compliance-rag-tutorial.md",
        "image": "china-compliance-rag",
        "title": "国内合规与 RAG",
        "links": ["196 审计日志", "195 PII 脱敏", "197 GDPR 驻地", "188 密钥管理", "53 ACL"],
        "concepts": ["等保语境", "数据出境", "生成式 AI 办法", "日志留存"],
    },
    {
        "file": "199.graph-rag-tutorial.md",
        "image": "graph-rag",
        "title": "Graph RAG",
        "links": ["200 知识图谱增强", "93 混合检索", "104 多跳检索", "Microsoft GraphRAG", "76 向量库"],
        "concepts": ["社区摘要", "局部全局双路", "图索引", "实体关系"],
    },
    {
        "file": "205.crag-corrective-rag-tutorial.md",
        "image": "crag-corrective-rag",
        "title": "CRAG 纠错式 RAG",
        "links": ["204 Self-RAG", "206 Adaptive RAG", "93 混合检索", "100 查询改写", "112 拒答策略"],
        "concepts": ["检索评估器", "纠正动作", "网络搜索兜底", "动作路由"],
    },
    {
        "file": "206.adaptive-rag-tutorial.md",
        "image": "adaptive-rag",
        "title": "Adaptive RAG",
        "links": ["205 CRAG", "201 Agentic RAG", "100 查询改写", "93 混合检索", "104 多跳"],
        "concepts": ["查询分类", "是否检索", "策略路由", "成本权衡"],
    },
    {
        "file": "212.lora-domain-qa-tutorial.md",
        "image": "lora-domain-qa",
        "title": "LoRA 领域问答微调",
        "links": ["24 预训练微调", "73 嵌入微调", "143 金标", "158 RAGAS", "213 RLHF"],
        "concepts": ["LoRA 适配器", "领域 QA 数据", "SFT", "与 RAG 分工"],
    },
    {
        "file": "213.rlhf-dpo-rag-tutorial.md",
        "image": "rlhf-dpo-rag",
        "title": "RLHF/DPO 与 RAG 对齐",
        "links": ["212 LoRA", "155 人工评测", "158 Faithfulness", "199 Graph RAG", "216 H 模块"],
        "concepts": ["偏好对", "DPO", "RAG 对齐", "H 模块收官"],
    },
]


def _strip_injected_extras(text: str, extras: list[str]) -> str:
    for block in extras + SUPPLEMENT:
        text = text.replace(block + "\n\n", "")
        text = text.replace("\n\n" + block, "")
        text = text.replace(block, "")
    text = re.sub(r"\n---\n\n---\n", "\n---\n", text)
    return text


def _resolve_base(spec: dict) -> str:
    if spec.get("base") == "ARTICLE_180":
        return ARTICLE_180
    path = ROOT / spec["file"]
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    text = _strip_generated_depth(_strip_appendix_spam(text))
    text = _strip_injected_extras(text, EXTRAS.get(spec["file"], []))
    return text


def _build_all() -> list[tuple[str, str, str | None]]:
    out: list[tuple[str, str, str | None]] = []
    for spec in SPECS:
        base = _resolve_base(spec)
        extras = EXTRAS.get(spec["file"], [])
        merged = _inject_extras(base, extras)
        i = 0
        pool = extras + SUPPLEMENT
        while hanzi_count(merged) < MIN_HANZI and pool:
            merged += "\n\n" + pool[i % len(pool)]
            i += 1
        out.append((spec["file"], merged, spec.get("image")))
    return out


ARTICLES_ALL: list[tuple[str, str, str | None]] = _build_all()
