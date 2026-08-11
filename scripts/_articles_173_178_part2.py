# -*- coding: utf-8 -*-
"""Part 2: articles 174-178 content (roadmap 191-195)."""

FOOTER_F2 = """
### 13.4 30 分钟动手作业

1. 把 §9 组件接到你 [171 聊天列表](171.chat-message-list-ui-tutorial（front-end）.md) 的消息气泡里；  
2. 与 [172 Markdown 渲染](172.markdown-render-rag-tutorial（front-end）.md) 联调，确认 XSS 策略仍生效；  
3. 用浏览器 DevTools 录一段 **3 分钟演示视频** 给产品；  
4. 写 wiki 一段：**本文 UI 在 F2 前端链路中的位置**。

### 13.5 给未来自己的排障便签

贴显示器旁：流式先接 delta 再接 citations；AbortController 每次请求新建；引用卡片 chunk_id 与 [113](113.inline-citation-tutorial.md) 编号对齐；PDF 预览权限与 [121 ACL](121.unauthorized-doc-filter-tutorial.md) 一致。

---

> **初学者可能仍困惑的点**  
> - F2 前端不是「好看就行」——要和 [116 SSE](116.sse-rag-streaming-tutorial.md) 事件契约、 [115 导航](115.source-document-navigation-tutorial.md) 字段对齐。  
> - 组件库可以换，但 **数据形状**（`citations[]`、`navigate_url`）不要自造。  
> - 阶段 4 全栈产品的验收是 **上传→问答→点引用看原文**——见 [路线图阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品)。
"""

FOOTER_178 = """
### 14.4 F2 前端系列收官：与阶段 4 全栈产品对齐

[企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **阶段 4：全栈产品** 要求交付 **企业知识库助手**：聊天 + 引用溯源 + 管理台。验收标准：**多用户隔离**；可演示 **上传 → 问答 → 看引用** 完整业务流。目录：[`projects/04-fullstack-assistant/`](projects/04-fullstack-assistant/)。

本篇（195 PDF 高亮）与 [188～194](171.chat-message-list-ui-tutorial（front-end）.md) 共同构成 F2 前端 **对话与溯源** 闭环：

| 路线图 | 教程 | 在阶段 4 中的角色 |
|--------|------|-------------------|
| 188 | [171 消息列表](171.chat-message-list-ui-tutorial（front-end）.md) | 对话主界面 |
| 189 | [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) | 答案渲染 |
| 190 | [173 代码高亮](173.code-highlight-rag-tutorial（front-end）.md) | 技术文档可读性 |
| 191 | [174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) | 流式体验 |
| 192 | [175 中断](175.abort-controller-stream-tutorial（front-end）.md) | 可控生成 |
| 193 | [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) | 依据展示 |
| 194 | [177 侧栏预览](177.source-preview-sidebar-tutorial（front-end）.md) | 原文对照 |
| 195 | 本篇 PDF 高亮 | 可审计跳页 |

**下一阶段（F2 续 + 阶段 5）**：196 上传界面、197 索引进度、Langfuse 追踪——见路线图 **196+** 与 **阶段 5 生产化**。

### 14.5 30 分钟收官作业

1. 在 `04-fullstack-assistant` 演示 **点 [1] → 侧栏 PDF 第 n 页高亮**；  
2. 对照阶段 4 验收表逐项打勾；  
3. 准备 **5 分钟路演**：从 C 模块检索到 F2 溯源 UI。

### 14.6 面试 60 秒全栈版

「我们阶段 4 产品是知识库助手：后端 FastAPI + 向量库，前端 React。流式用 fetch + SSE 事件，delta 打字机，AbortController 停止。引用与 113 编号对齐，citations 事件在 done 前下发。点击引用开侧栏，PDF.js 按 metadata page 跳页并用 text layer 高亮 chunk。多租户 JWT + 检索前 ACL。能根据 Langfuse trace 定位 bad case。」

---

> **系列结语**  
> 从 [125 LangChain 核心](125.langchain-core-tutorial.md) 到本篇，你已走完路线图 **145～195** 的框架、评测、后端 API 与 **F2 前端溯源** 主线。接下来用 **阶段 4 项目** 把知识变成可演示的产品，再用 **阶段 5** 补上观测与部署。祝交付顺利。
"""

ARTICLE_174 = r'''# F2 前端（四）：流式打字机效果完全指南

> ChatGPT 把 **逐字流出** 变成用户心智里的「AI 在思考」。RAG 比纯聊天多两件事：**检索等待期** 与 **引用收尾**——若前端只会 `text += delta`，会出现闪烁、卡顿、引用编号乱跳。 [116 篇 SSE RAG](116.sse-rag-streaming-tutorial.md) 定义了后端事件；[路线图第 22 条](ENTERPRISE_RAG_ROADMAP.md) 强调 **流式 UI 渲染**。本篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F2 前端第四篇**（路线图第 **191** 条），**主线篇**：`fetch`/`EventSource` 接流、缓冲与 `requestAnimationFrame`、与 citations 挂载时机。前置：[116 SSE RAG](116.sse-rag-streaming-tutorial.md)、[7 SSE 基础](7.sse-tutorial.md)、[171 聊天列表](171.chat-message-list-ui-tutorial（front-end）.md)、[172 Markdown](172.markdown-render-rag-tutorial（front-end）.md)。

---

## 目录

1. [前言：打字机是体验基线，不是 CSS 动画](#1-前言打字机是体验基线不是-css-动画)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [流式打字机数据流](#3-流式打字机数据流)
4. [与 116 SSE 事件契约对齐](#4-与-116-sse-事件契约对齐)
5. [缓冲策略：逐字、按词、按帧](#5-缓冲策略逐字按词按帧)
6. [React 实现：useRagStream Hook](#6-react-实现useragstream-hook)
7. [与 Markdown 渲染协作](#7-与-markdown-渲染协作)
8. [检索中、生成中、引用挂载三态 UI](#8-检索中生成中引用挂载三态-ui)
9. [综合实战：TypewriterMessage 组件](#9-综合实战typewritermessage-组件)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [性能与可访问性](#11-性能与可访问性)
12. [综合概念地图](#12-综合概念地图)
13. [常见陷阱与 FAQ](#13-常见陷阱与-faq)
14. [总结与系列下一步](#14-总结与系列下一步)

---

## 1. 前言：打字机是体验基线，不是 CSS 动画

产品评审时，老板问：「为什么我们的 RAG 三秒后才突然蹦出整段字？」——后端明明 [116](116.sse-rag-streaming-tutorial.md) 已经在推 `delta`，前端却 **等 `done` 一次性 setState**。这不是模型慢，是 **UI 没接流**。

**流式打字机 UI（Streaming Typewriter UI）**：将 SSE/WebSocket 的文本增量以可控节奏渲染到消息气泡，使用户感知持续输出。  
通俗说：**字要一格格出来**；引用 `[1]` 要等 [116](116.sse-rag-streaming-tutorial.md) 的 `citations` 事件再变可点。

**读完本文，你应该能做到：**

1. 用 `fetch` + `ReadableStream` 或 `EventSource` 解析 [116](116.sse-rag-streaming-tutorial.md) 四类事件。  
2. 实现 §6 `useRagStream`，含缓冲与 `requestAnimationFrame`。  
3. 区分 **检索 spinner** 与 **生成打字机** 两阶段 UI。  
4. 在 `done` 后挂载 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) 数据。  
5. 与 [175 AbortController](175.abort-controller-stream-tutorial（front-end）.md) 预留 `signal`。  
6. 识别 §10 五种翻车。

### 1.1 F2 与路线图第 22 条

[路线图 A 模块第 22 条](ENTERPRISE_RAG_ROADMAP.md)：「流式 UI 渲染（逐字显示、中断）」。本篇覆盖 **逐字显示**；中断在 [175](175.abort-controller-stream-tutorial（front-end）.md)；后端协议在 [116](116.sse-rag-streaming-tutorial.md)。

### 1.2 术语双轨速查

| 中文 | English | 一句话 |
|------|---------|--------|
| 增量 | delta | 本次新增文本 |
| 打字机 | typewriter | 渐进显示 |
| 按帧刷新 | rAF batching | 每帧合并 delta |
| 尾事件 | citations / done | 流结束元数据 |
| 反压 | backpressure | 渲染跟不上生成 |

---

## 2. 本文边界与动手路径

**档位：F2 主线篇（路线图 191）。**

**本文讲：** 前端流解析、缓冲策略、React Hook、三态 UI、Markdown 协作、性能与 a11y。  
**本文不讲：** 后端 FastAPI 实现（见 [116](116.sse-rag-streaming-tutorial.md)）、WebSocket 双工（[117](117.websocket-rag-streaming-tutorial.md) 可选）。

### 2.1 动手路径表

| 步骤 | 你做什么 | 验收 |
|------|----------|------|
| A | 读 [116 §5](116.sse-rag-streaming-tutorial.md) 事件表 | 能手写 JSON |
| B | 跑 §6 Hook 接 mock 流 | 控制台见 delta |
| C | 接 [171](171.chat-message-list-ui-tutorial（front-end）.md) | 气泡逐字增长 |
| D | citations 在 done 后渲染 | `[1]` 可点击 |
| E | §10 五种错法 | 能口述 |
| F | Lighthouse 无长任务告警 | 可选 |

---

## 3. 流式打字机数据流

![流式打字机数据流](image/streaming-typewriter-ui/01-typewriter-flow.png)

```text
用户发送 query
  → POST /api/rag/ask (Accept: text/event-stream)
  → 服务端检索（非流式，可返回 X-Retrieve-Ms）
  → 打开 SSE：event: message  data: {"delta":"..."}
  → 前端解析 → 缓冲区 → rAF → setContent
  → event: citations
  → event: done → 关闭流，挂载引用 UI
```

**关键**：检索阶段 **没有 delta**——UI 应显示「正在检索知识库…」，避免用户以为卡住。

---

## 4. 与 116 SSE 事件契约对齐

| 事件 | 前端处理 |
|------|----------|
| `message` | `content += delta` |
| `citations` | `setCitations(payload)`，**勿**在首个 delta 前渲染可点链接 |
| `done` | `setStreaming(false)`，触发 [173](173.code-highlight-rag-tutorial（front-end）.md) 延迟高亮 |
| `error` |  toast + 保留已生成 partial |

```typescript
type RagStreamEvent =
  | { type: "message"; delta: string }
  | { type: "citations"; citations: Citation[] }
  | { type: "done"; finish_reason: string }
  | { type: "error"; message: string };
```

**与 [113 行内引用](113.inline-citation-tutorial.md)**：模型可能在 delta 里写 `[1]`，但 **链接** 应在 `citations` 到达后启用——否则 chunk_id 未绑定会跳错。

---

## 5. 缓冲策略：逐字、按词、按帧

![缓冲策略对比](image/streaming-typewriter-ui/02-buffer-strategies.png)

| 策略 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| 逐 token 渲染 | 每个 delta 立即 setState | 最跟手 | React 重渲染过多 |
| 按词（空格） | 缓冲到空格 flush | 中文需分词兜底 | 中文不友好 |
| **按帧 rAF** | 每帧合并 pending | 性能稳 | 略少「真逐字」 |
| 批量 50ms | setInterval | 简单 | 与屏刷不同步 |

**推荐默认**：**rAF 合并**——每帧最多更新一次 DOM，肉眼仍像打字机。

```typescript
let pending = "";
function pushDelta(delta: string) {
  pending += delta;
  if (!scheduled) {
    scheduled = true;
    requestAnimationFrame(() => {
      flush(pending);
      pending = "";
      scheduled = false;
    });
  }
}
```

中文无空格：按 **字符** 累积即可，勿强行按英文词切。

---

## 6. React 实现：useRagStream Hook

```typescript
// hooks/useRagStream.ts
import { useCallback, useRef, useState } from "react";

export interface Citation {
  index: number;
  chunk_id: string;
  title: string;
  excerpt: string;
  navigate_url?: string;
}

export function useRagStream() {
  const [content, setContent] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [phase, setPhase] = useState<"idle" | "retrieving" | "streaming" | "done" | "error">("idle");
  const abortRef = useRef<AbortController | null>(null);

  const ask = useCallback(async (query: string, sessionId?: string) => {
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setContent("");
    setCitations([]);
    setPhase("retrieving");

    const res = await fetch("/api/rag/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ query, session_id: sessionId }),
      signal: ac.signal,
    });
    if (!res.ok || !res.body) throw new Error("stream failed");

    setPhase("streaming");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";
      for (const block of blocks) {
        parseSseBlock(block, {
          onMessage: (delta) => setContent((c) => c + delta),
          onCitations: setCitations,
          onDone: () => setPhase("done"),
          onError: () => setPhase("error"),
        });
      }
    }
  }, []);

  const stop = useCallback(() => abortRef.current?.abort(), []);

  return { content, citations, phase, ask, stop };
}

function parseSseBlock(
  block: string,
  handlers: {
    onMessage: (d: string) => void;
    onCitations: (c: Citation[]) => void;
    onDone: () => void;
    onError: () => void;
  },
) {
  let event = "message";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return;
  const json = JSON.parse(data);
  if (event === "message") handlers.onMessage(json.delta ?? "");
  if (event === "citations") handlers.onCitations(json.citations ?? []);
  if (event === "done") handlers.onDone();
  if (event === "error") handlers.onError();
}
```

详见 [175 篇](175.abort-controller-stream-tutorial（front-end）.md) 的 `stop()` 与后端断开协作。

---

## 7. 与 Markdown 渲染协作

[172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 在流式下有两种模式：

1. **纯文本模式**（流式中）：`white-space: pre-wrap` 显示原始 Markdown，避免未闭合 `**` 抖动；  
2. **富文本模式**（done 后）：切 `ReactMarkdown` 完整渲染。

```tsx
{phase === "streaming" ? (
  <pre className="whitespace-pre-wrap font-sans text-sm">{content}</pre>
) : (
  <MarkdownAnswer content={content} citations={citations} />
)}
```

产品若坚持流式中也渲染列表：接受 **偶发样式闪动**，或每 300ms 节流重算 Markdown。

---

## 8. 检索中、生成中、引用挂载三态 UI

| 阶段 | UI | 输入框 |
|------|-----|--------|
| retrieving | 「正在检索…」+ 轻量 spinner | 禁用发送 |
| streaming | 打字机 + 闪烁光标 `▍` | 显示「停止」→ [175](175.abort-controller-stream-tutorial（front-end）.md) |
| done | 完整 Markdown + [176 卡片](176.citation-card-ui-tutorial（front-end）.md) | 恢复发送 |

**光标实现**：

```css
.typewriter-cursor::after {
  content: "▍";
  animation: blink 1s step-end infinite;
}
```

---

## 9. 综合实战：TypewriterMessage 组件

```tsx
// components/rag/TypewriterMessage.tsx
import { MarkdownAnswer } from "./MarkdownAnswer";
import { CitationCardList } from "./CitationCardList";

interface Props {
  content: string;
  citations: Citation[];
  phase: "retrieving" | "streaming" | "done" | "error";
  onStop?: () => void;
}

export function TypewriterMessage({ content, citations, phase, onStop }: Props) {
  if (phase === "retrieving") {
    return <div className="text-muted-foreground text-sm">正在检索知识库…</div>;
  }
  if (phase === "error") {
    return <div className="text-destructive text-sm">生成失败，请重试。</div>;
  }
  return (
    <div className="space-y-3">
      {phase === "streaming" ? (
        <pre className="typewriter-cursor whitespace-pre-wrap text-sm">{content}</pre>
      ) : (
        <MarkdownAnswer content={content} citations={citations} />
      )}
      {phase === "streaming" && onStop && (
        <button type="button" className="text-xs text-muted-foreground underline" onClick={onStop}>
          停止生成
        </button>
      )}
      {phase === "done" && citations.length > 0 && <CitationCardList items={citations} />}
    </div>
  );
}
```

---

## 10. 先错对对：五种典型翻车

### 10.1 错：等 done 才显示字

**对**：每个 `message` 事件更新 content。

### 10.2 错：citations 与 delta 竞态，提前可点 `[1]`

**对**：`citations` 到达前 `[1]` 渲染为灰色不可点。

### 10.3 错：每个 delta 全量 Markdown 解析

**对**：流式用 pre，done 再 Markdown（§7）。

### 10.4 错：无 retrieving 态

**对**：检索 1～3 秒也要反馈。

### 10.5 错：自动滚动抢用户阅读位置

**对**：仅当用户 **贴底** 时 `scrollIntoView`。

---

## 11. 性能与可访问性

- **长答案**：虚拟列表在 [171](171.chat-message-list-ui-tutorial（front-end）.md) 层做，单条消息内避免上万 DOM 节点；  
- **a11y**：`aria-live="polite"` 区域播报完成态，流式中勿每秒读屏；  
- **移动弱网**：delta 合并更重要，避免输入法冲突。

---

## 12. 综合概念地图

![流式打字机概念地图](image/streaming-typewriter-ui/03-concept-map.png)

---

## 13. 常见陷阱与 FAQ

### 13.1 EventSource 还是 fetch？

`EventSource` 仅 GET，RAG 常 POST body → **fetch + ReadableStream**（[175](175.abort-controller-stream-tutorial（front-end）.md) 亦需 AbortSignal）。

### 13.2 与 [117 WebSocket](117.websocket-rag-streaming-tutorial.md)？

80% 用本篇 + SSE；要同连接 **澄清/旁听** 再 WS。

### 13.3 Nginx 缓冲？

[116 §11](116.sse-rag-streaming-tutorial.md)：`X-Accel-Buffering: no`。

---

## 14. 总结与系列下一步

1. **打字机** = 接 [116](116.sse-rag-streaming-tutorial.md) delta + rAF 缓冲 + 三态 UI。  
2. **citations 收尾** 再挂可点引用，对齐 [113](113.inline-citation-tutorial.md)。  
3. **停止** 交 [175 AbortController](175.abort-controller-stream-tutorial（front-end）.md)。

### 14.1 系列下一步

| 目标 | 阅读 |
|------|------|
| 中断 | [175 AbortController](175.abort-controller-stream-tutorial（front-end）.md) |
| 引用卡片 | [176 引用卡片 UI](176.citation-card-ui-tutorial（front-end）.md) |
| 后端 SSE | [116 SSE RAG](116.sse-rag-streaming-tutorial.md) |

### 14.2 面试 30 秒版

「RAG 流式前端用 fetch 读 SSE，按 event 类型解析 message/citations/done。delta 用 requestAnimationFrame 合并更新，检索阶段单独 spinner。citations 到了再把行内 [n] 变链接。停止用 AbortController。done 后切 Markdown 渲染。」

''' + FOOTER_F2

ARTICLE_175 = r'''# F2 前端（五）：中断生成 AbortController 完全指南

> 用户点「停止生成」时，若只是 **前端不再显示新字**，而后端 LLM 仍在烧 Token，财务与 SLO 都会记一笔。 [174 流式打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) 负责把字冒出来；本篇负责 **真停**：`AbortController` 断开 HTTP 流、通知后端取消任务，并在 UI 上保留 **可读的 partial 答案**。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F2 前端第五篇**（路线图第 **192** 条），**地基篇**。可选对照 [6 WebSocket](6.websocket-tutorial.md)、[117 WebSocket RAG](117.websocket-rag-streaming-tutorial.md) 的 `cancel` 帧。前置：[174 流式打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)、[116 SSE RAG](116.sse-rag-streaming-tutorial.md)、[7 SSE](7.sse-tutorial.md)。

---

## 目录

1. [前言：停止必须是端到端的](#1-前言停止必须是端到端的)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [AbortController 中断链路](#3-abortcontroller-中断链路)
4. [fetch 流式 vs EventSource](#4-fetch-流式-vs-eventsource)
5. [React 状态机：idle / streaming / aborted](#5-react-状态机idle--streaming--aborted)
6. [后端如何感知断开](#6-后端如何感知断开)
7. [与 WebSocket cancel 的对照](#7-与-websocket-cancel-的对照)
8. [综合实战：可中断的 useRagStream](#8-综合实战可中断的-useragstream)
9. [先错对对：四种典型翻车](#9-先错对对四种典型翻车)
10. [多标签页与竞态](#10-多标签页与竞态)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：停止必须是端到端的

测试同学反馈：「点停止后 GPU 监控仍跳。」——前端 `setStreaming(false)` 了，但 **fetch 没 abort**，TCP 连接未关，Uvicorn 里异步生成器还在 `yield`。

**AbortController**（浏览器标准）：为 `fetch` 提供 `signal`，调用 `abort()` 后 **拒绝未完成的 Promise** 并 **取消 body 读取**，进而触发服务端连接断开（取决于框架）。  
通俗说：**用户点停，网线这端要先挂电话**。

**读完本文，你应该能做到：**

1. 每次提问 **新建** `AbortController`，停止时 `abort()`。  
2. 说明为何 RAG 应用 **优先 fetch 流** 而非 `EventSource`。  
3. 在后端 FastAPI 里 **检测 `Request.is_disconnected`** 停止 LLM。  
4. UI 展示 **已生成片段 +「已停止」** 标记。  
5. 对照 [117](117.websocket-rag-streaming-tutorial.md) 说明何时用 WS `cancel`。  
6. 识别 §9 四种翻车。

---

## 2. 本文边界与动手路径

**档位：F2 地基篇（路线图 192）。**

**本文讲：** AbortSignal、fetch SSE、前端状态机、后端断开、partial 保留、WS 对照。  
**本文不讲：** Kubernetes 级作业取消、跨 region 生成调度。

### 2.1 动手路径表

| 步骤 | 你做什么 | 验收 |
|------|----------|------|
| A | 读 §3 链路图 | 白板能画 |
| B | §8 Hook 加 stop | Network 里请求 canceled |
| C | 后端打印 disconnect | 日志见 client gone |
| D | partial 答案可继续复制 | 用户体验 |
| E | §9 先错对对 | 四种 |

---

## 3. AbortController 中断链路

![AbortController 中断链路](image/abort-controller-stream/01-abort-flow.png)

```text
用户点击「停止」
  → controller.abort()
  → reader.read() 抛 AbortError
  → fetch 连接关闭
  → 服务端 is_disconnected / CancelledError
  → 停止向 LLM 写入（若 SDK 支持）
  → UI: phase = "aborted"，保留 content
```

---

## 4. fetch 流式 vs EventSource

![EventSource 与 fetch 对比](image/abort-controller-stream/02-sse-vs-fetch.png)

| 能力 | EventSource | fetch + ReadableStream |
|------|-------------|------------------------|
| HTTP 方法 | GET only | POST 等 |
| 自定义 Header | 受限 | ✅ Authorization |
| AbortController | 部分浏览器支持差 | ✅ 标准 |
| RAG 问句 body | ❌ 需 query 参数 | ✅ JSON body |

**结论**：企业 RAG **默认 fetch**；[7 篇 EventSource](7.sse-tutorial.md) 适合演示 GET 流。

```typescript
const controller = new AbortController();
fetch("/api/rag/ask", { signal: controller.signal, /* ... */ });
// 停止：controller.abort();
```

---

## 5. React 状态机：idle / streaming / aborted

```typescript
type StreamPhase = "idle" | "retrieving" | "streaming" | "done" | "aborted" | "error";

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "START":
      return { phase: "retrieving", content: "", citations: [] };
    case "FIRST_DELTA":
      return { ...state, phase: "streaming" };
    case "ABORT":
      return { ...state, phase: "aborted" };
    case "DONE":
      return { ...state, phase: "done" };
    default:
      return state;
  }
}
```

**aborted 与 done 区别**：

- `done`：正常收尾，可有完整 `citations`；  
- `aborted`：可能 **无 citations** 或 partial citations——UI 文案「生成已停止」，勿假装完整 Grounding。

---

## 6. 后端如何感知断开

```python
# FastAPI 片段 — 与 [116](116.sse-rag-streaming-tutorial.md) 共用端点
from fastapi import Request
from starlette.responses import StreamingResponse

async def rag_ask(request: Request, body: AskBody):
    async def event_gen():
        try:
            for delta in llm_stream(prompt):
                if await request.is_disconnected():
                    break
                yield sse_message(delta)
        finally:
            await llm_task.cancel()  # 若 SDK 支持
    return StreamingResponse(event_gen(), media_type="text/event-stream")
```

OpenAI SDK：`stream` 循环中检测断开并 `break`；部分网关仍会计少量 token——**产品层接受**。

---

## 7. 与 WebSocket cancel 的对照

[6 WebSocket](6.websocket-tutorial.md) 与 [117 RAG WS](117.websocket-rag-streaming-tutorial.md) 可发：

```json
{ "type": "cancel", "stream_id": "uuid" }
```

| 场景 | 推荐 |
|------|------|
| 单向问答 + 停止 | **本篇 fetch abort** |
| 同连接澄清、旁听 | [117 WS cancel](117.websocket-rag-streaming-tutorial.md) |
| 已有 WS 基础设施 | 可统一 WS，非必须 |

**不要** 为停止单独上 WS——[116 SSE](116.sse-rag-streaming-tutorial.md) + abort 更简单。

---

## 8. 综合实战：可中断的 useRagStream

```typescript
export function useRagStream() {
  const abortRef = useRef<AbortController | null>(null);
  const [phase, setPhase] = useState<StreamPhase>("idle");
  const [content, setContent] = useState("");

  const ask = async (query: string) => {
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setPhase("retrieving");
    setContent("");
    try {
      const res = await fetch("/api/rag/ask", {
        method: "POST",
        signal: ac.signal,
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ query }),
      });
      // ... reader loop 同 [174](174.streaming-typewriter-ui-tutorial（front-end）.md)
      setPhase("done");
    } catch (e) {
      if ((e as Error).name === "AbortError") setPhase("aborted");
      else setPhase("error");
    }
  };

  const stop = () => abortRef.current?.abort();

  return { content, phase, ask, stop };
}
```

**每次 ask 必须 new AbortController**——复用旧 signal 已是 aborted 状态。

---

## 9. 先错对对：四种典型翻车

### 9.1 错：只停 UI 不 abort fetch

**对**：`stop()` 必须 `controller.abort()`。

### 9.2 错：abort 后清空 content

**对**：保留 partial，标注「已停止」。

### 9.3 错：并发两次 ask 共用一个 controller

**对**：新 ask 先 abort 旧请求。

### 9.4 错：aborted 仍渲染完整 citations

**对**：无 citations 事件则显示「引用未完整」。

---

## 10. 多标签页与竞态

同一 `session_id` 两标签同时问：后端应 **stream_id** 区分；前端 **后发的 ask abort 前一个**（§8 已做）。Session 存储见 [118 多轮](118.multi-turn-history-tutorial.md)。

---

## 11. 综合概念地图

![中断生成概念地图](image/abort-controller-stream/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

### 12.1 abort 后 HTTP 状态码？

常为 **client 断开**，服务端不一定返回 499 日志——以观测为准。

### 12.2 能否恢复继续生成？

产品可选「续写」= **新请求** 带 partial 上下文，非同一流恢复。

### 12.3 与 [175] 和 [174] 谁写 Hook？

本篇与 [174](174.streaming-typewriter-ui-tutorial（front-end）.md) 可 **同一 Hook**：174 管渲染节奏，175 管 abort。

---

## 13. 总结与系列下一步

1. **停止 = abort fetch + 后端 disconnect + partial 保留**。  
2. RAG 用 **POST fetch 流**，不用 EventSource 扛 body。  
3. WS cancel 见 [117](117.websocket-rag-streaming-tutorial.md)，非默认。

### 13.1 系列下一步

| 目标 | 阅读 |
|------|------|
| 引用 UI | [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) |
| 打字机 | [174 流式打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) |

### 13.2 面试 30 秒版

「每次提问 new AbortController，fetch 传 signal。用户点停止 abort()，catch AbortError 设 aborted 态，保留已生成 Markdown。后端 StreamingResponse 循环里 request.is_disconnected()  break。RAG 用 POST fetch 不用 EventSource。」

''' + FOOTER_F2

# Articles 176-178 continue with substantial content
ARTICLE_176 = r'''# F2 前端（六）：引用卡片 UI 完全指南

> 行内 `[1]` 适合短答案，但企业用户常需要 **扫一眼所有依据**：哪份制度、哪一页、相似度多少。 [113 行内引用](113.inline-citation-tutorial.md) 解决句末标注；[115 源文档导航](115.source-document-navigation-tutorial.md) 解决跳哪；本篇解决 **卡片长什么样、怎么排、怎么点**。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F2 前端第六篇**（路线图第 **193** 条），**主线篇**。前置：[113 行内引用](113.inline-citation-tutorial.md)、[115 源文档导航](115.source-document-navigation-tutorial.md)、[116 SSE RAG](116.sse-rag-streaming-tutorial.md)、[174 流式打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)。

---

## 目录

1. [前言：引用卡片是 Grounding 的「第二屏」](#1-前言引用卡片是-grounding-的第二屏)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [引用卡片解剖：字段与布局](#3-引用卡片解剖字段与布局)
4. [行内引用与卡片列表的分工](#4-行内引用与卡片列表的分工)
5. [citations JSON 契约](#5-citations-json-契约)
6. [CitationCard 组件实现](#6-citationcard-组件实现)
7. [与流式收尾事件衔接](#7-与流式收尾事件衔接)
8. [点击行为：侧栏 vs 新标签](#8-点击行为侧栏-vs-新标签)
9. [移动端与无障碍](#9-移动端与无障碍)
10. [先错对对：四种典型翻车](#10-先错对对四种典型翻车)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：引用卡片是 Grounding 的「第二屏」

法务反馈：「答案两句，但我需要对比三条制度原文。」只有 [113](113.inline-citation-tutorial.md) 行内 `[1][2]` 时，她要在正文里找编号；**引用卡片列表**在答案下方整齐列出 **来源标题、摘录、页码**，一点进 [177 侧栏预览](177.source-preview-sidebar-tutorial（front-end）.md)。

**引用卡片 UI（Citation Card UI）**：将 `citations[]` 渲染为可扫描的卡片列表，与行内 `[n]` 编号联动高亮。  
通俗说：**脚注区的「现代版」**，但仍要与 [113](113.inline-citation-tutorial.md) 编号一致。

**读完本文，你应该能做到：**

1. 设计 `Citation` TypeScript 类型，对齐 [115 navigate_url](115.source-document-navigation-tutorial.md)。  
2. 实现 §6 `CitationCard` + `CitationCardList`。  
3. 在 [174 done 态](174.streaming-typewriter-ui-tutorial（front-end）.md) 挂载卡片。  
4. 点击卡片触发 `onOpenSource(citation)` 供 [177](177.source-preview-sidebar-tutorial（front-end）.md) 消费。  
5. 处理 **无权限** 卡片灰显（[121 ACL](121.unauthorized-doc-filter-tutorial.md)）。  
6. 识别 §10 四种翻车。

---

## 2. 本文边界与动手路径

**档位：F2 主线篇（路线图 193）。**

**本文讲：** 卡片信息架构、JSON 契约、React 组件、流式时机、点击委托、响应式。  
**本文不讲：** 脚注式纯文末编号（[114](114.footnote-citation-tutorial.md) 可并存）、PDF 高亮实现（[178](178.pdf-highlight-locate-tutorial（front-end）.md)）。

---

## 3. 引用卡片解剖：字段与布局

![引用卡片结构](image/citation-card-ui/01-card-anatomy.png)

**推荐卡片字段（最小集）**：

| 字段 | 展示 | 来源 |
|------|------|------|
| `index` | 左上角 `[1]` | 与行内一致 |
| `title` | 文档名 | metadata `source` |
| `excerpt` | 2～3 行摘录 | chunk `text` 截断 |
| `page` | 「第 12 页」 | [52 metadata](52.metadata-source-page-tutorial.md) |
| `score` | 可选相似度 | 检索分数 |
| `navigate_url` | 不直接展示 | [115](115.source-document-navigation-tutorial.md) |

**布局**：桌面 **横向卡片 + 左编号**；移动 **全宽堆叠**。摘录 `line-clamp-3`，避免挤占答案区。

---

## 4. 行内引用与卡片列表的分工

![行内与卡片分工](image/citation-card-ui/02-inline-vs-card.png)

| 机制 | 适用 | 本篇 |
|------|------|------|
| [113 行内](113.inline-citation-tutorial.md) | 短答、数字依据 | 正文 `[n]` 可点 |
| [114 脚注](114.footnote-citation-tutorial.md) | 长报告 | 可折叠 |
| **卡片列表** | 多来源对比 | 答案下方 |

**产品建议**：默认 **行内 + 卡片并存**——行内负责「这句依据哪」，卡片负责「本次问了哪些文档」。

---

## 5. citations JSON 契约

与 [116 citations 事件](116.sse-rag-streaming-tutorial.md) 一致：

```typescript
export interface Citation {
  index: number;
  chunk_id: string;
  title: string;
  excerpt: string;
  page?: number;
  section?: string;
  score?: number;
  navigate_url?: string;
  allowed?: boolean; // false = [121] 无权预览
}
```

**编号**：`index` 从 1 开始，与 prompt 里 `[1]` 一致——见 [113 §5](113.inline-citation-tutorial.md)。

---

## 6. CitationCard 组件实现

```tsx
// components/rag/CitationCard.tsx
import { cn } from "@/lib/utils";

interface Props {
  citation: Citation;
  active?: boolean;
  onClick?: (c: Citation) => void;
}

export function CitationCard({ citation, active, onClick }: Props) {
  const disabled = citation.allowed === false;
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onClick?.(citation)}
      className={cn(
        "flex w-full gap-3 rounded-lg border p-3 text-left transition",
        active ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      <span className="text-primary shrink-0 font-mono text-sm">[{citation.index}]</span>
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium text-sm">{citation.title}</div>
        <p className="text-muted-foreground mt-1 line-clamp-3 text-xs">{citation.excerpt}</p>
        <div className="text-muted-foreground mt-2 flex gap-2 text-xs">
          {citation.page != null && <span>第 {citation.page} 页</span>}
          {citation.section && <span>{citation.section}</span>}
          {citation.score != null && <span>相关度 {(citation.score * 100).toFixed(0)}%</span>}
        </div>
      </div>
    </button>
  );
}

export function CitationCardList({
  items,
  activeIndex,
  onSelect,
}: {
  items: Citation[];
  activeIndex?: number;
  onSelect?: (c: Citation) => void;
}) {
  if (!items.length) return null;
  return (
    <div className="space-y-2 border-t pt-3">
      <div className="text-muted-foreground text-xs font-medium">参考来源 ({items.length})</div>
      {items.map((c) => (
        <CitationCard
          key={c.chunk_id}
          citation={c}
          active={c.index === activeIndex}
          onClick={onSelect}
        />
      ))}
    </div>
  );
}
```

---

## 7. 与流式收尾事件衔接

[174](174.streaming-typewriter-ui-tutorial（front-end）.md) + [116](116.sse-rag-streaming-tutorial.md)：

1. `streaming` 阶段 **不渲染** `CitationCardList`（或渲染 skeleton）；  
2. 收到 `citations` → 写入 state；  
3. `done` → 显示完整列表；  
4. 行内 `[n]` 点击与卡片点击 **共用** `onSelect`，`activeIndex` 同步。

```tsx
const handleCitationSelect = (c: Citation) => {
  setActiveCitation(c.index);
  openPreviewSidebar(c); // [177](177.source-preview-sidebar-tutorial（front-end）.md)
};
```

---

## 8. 点击行为：侧栏 vs 新标签

| 模式 | 行为 | 场景 |
|------|------|------|
| 侧栏预览 | `openPreviewSidebar` | 桌面对照阅读 |
| 新标签 | `window.open(navigate_url)` | 外链 wiki |
| 下载 | signed URL | 无预览器 |

默认企业内网：**侧栏**；`navigate_url` 仍由 [115](115.source-document-navigation-tutorial.md) 构造。

---

## 9. 移动端与无障碍

- 移动：**底部 Sheet** 代替右侧栏（[177](177.source-preview-sidebar-tutorial（front-end）.md) 响应式）；  
- `aria-label={`参考来源 ${index}：${title}`}`；  
- 键盘：卡片 `focus-visible` 轮廓清晰。

---

## 10. 先错对对：四种典型翻车

### 10.1 错：卡片 index 与行内 `[n]` 不一致

**对**：服务端 citations 与 prompt 编号同一映射。

### 10.2 错：流式中途渲染可点卡片

**对**：等 `citations` 事件。

### 10.3 错：excerpt 过长撑破布局

**对**：`line-clamp-3` + 侧栏看全文。

### 10.4 错：无权文档仍可点

**对**：`allowed: false` 灰显 + tooltip。

---

## 11. 综合概念地图

![引用卡片概念地图](image/citation-card-ui/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

### 12.1 还要 [114 脚注](114.footnote-citation-tutorial.md) 吗？

长报告可脚注为主、卡片为辅；FAQ 产品卡片足够。

### 12.2 score 展示吗？

可选；过低分数可灰显提醒「弱相关」。

### 12.3 与评测？

抽检卡片 excerpt 是否来自真 chunk——对接 [141 Faithfulness](141.ragas-faithfulness-tutorial.md)。

---

## 13. 总结与系列下一步

1. **引用卡片** = `citations[]` 的可扫列表，与 [113](113.inline-citation-tutorial.md) 编号联动。  
2. **流式** 在 `citations` 后挂载，对齐 [116](116.sse-rag-streaming-tutorial.md)。  
3. 点击进 [177 侧栏预览](177.source-preview-sidebar-tutorial（front-end）.md) 或 [178 PDF 高亮](178.pdf-highlight-locate-tutorial（front-end）.md)。

### 13.1 系列下一步

| 目标 | 阅读 |
|------|------|
| 侧栏预览 | [177 侧边栏原文预览](177.source-preview-sidebar-tutorial（front-end）.md) |
| 导航契约 | [115 源文档导航](115.source-document-navigation-tutorial.md) |

### 13.2 面试 30 秒版

「citations 事件带 index、chunk_id、excerpt、navigate_url。前端 CitationCardList 在 done 后渲染，与行内 [n] 同索引。点击打开侧栏预览，无权 allowed false 灰显。摘录 line-clamp，页码来自 metadata。」

''' + FOOTER_F2

ARTICLE_177 = r'''# F2 前端（七）：侧边栏原文预览完全指南

> 用户点 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) 或行内 `[1]` 时，若只弹 **chunk 文本 Toast**，Grounding 仍像「高级摘要」。**侧边栏原文预览（Source Preview Sidebar）** 在桌面端把布局切成 **左对话、右原文**，加载 PDF/Markdown/HTML，并预留 [178 PDF 高亮](178.pdf-highlight-locate-tutorial（front-end）.md) 接口。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F2 前端第七篇**（路线图第 **194** 条），**主线篇**。前置：[115 源文档导航](115.source-document-navigation-tutorial.md)、[176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)、[121 越权过滤](121.unauthorized-doc-filter-tutorial.md)、[52 溯源元数据](52.metadata-source-page-tutorial.md)。

---

## 目录

1. [前言：预览侧栏是「点引用」的默认归宿](#1-前言预览侧栏是点引用的默认归宿)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [双栏布局与响应式](#3-双栏布局与响应式)
4. [预览面板状态机](#4-预览面板状态机)
5. [按文档类型路由预览器](#5-按文档类型路由预览器)
6. [signed URL 与权限](#6-signed-url-与权限)
7. [与 citation 点击联动](#7-与-citation-点击联动)
8. [综合实战：PreviewSidebar 组件](#8-综合实战previewsidebar-组件)
9. [先错对对：四种典型翻车](#9-先错对对四种典型翻车)
10. [性能：懒加载与缓存](#10-性能懒加载与缓存)
11. [综合概念地图](#11-综合概念地图)
12. [常见陷阱与 FAQ](#12-常见陷阱与-faq)
13. [总结与系列下一步](#13-总结与系列下一步)

---

## 1. 前言：预览侧栏是「点引用」的默认归宿

销售演示时，客户点 `[1]`，右侧 **滑出员工手册 PDF 第 8 页**——这一屏往往决定采购。若只有 [176 卡片](176.citation-card-ui-tutorial（front-end）.md) 上的两行摘录，信任感不够。

**侧边栏原文预览**：在聊天界面旁展示源文档完整视图，根据 [115 navigate_url](115.source-document-navigation-tutorial.md) 与 metadata 定位页码/章节。  
通俗说：**左问右证**，审计最爱。

**读完本文，你应该能做到：**

1. 实现 **可拖拽宽度** 或固定比例双栏布局。  
2. 状态机覆盖 loading / preview / error / permission_denied。  
3. 按 `mime` 或扩展名路由 PDF、Markdown、HTML 预览器。  
4. 用 **signed URL** 拉取受 ACL 保护的文件（[121](121.unauthorized-doc-filter-tutorial.md)）。  
5. 与 [176 onSelect](176.citation-card-ui-tutorial（front-end）.md) 联动。  
6. 为 [178 PDF 高亮](178.pdf-highlight-locate-tutorial（front-end）.md) 留 `highlightText` prop。

---

## 2. 本文边界与动手路径

**档位：F2 主线篇（路线图 194）。**

**本文讲：** 布局、状态机、多格式预览、权限 URL、React 组件、性能。  
**本文不讲：** Office Online 全功能、协同批注、移动端原生 App。

---

## 3. 双栏布局与响应式

![侧边栏布局](image/source-preview-sidebar/01-sidebar-layout.png)

```tsx
// layouts/ChatWithPreviewLayout.tsx
export function ChatWithPreviewLayout({
  chat,
  preview,
  open,
}: {
  chat: React.ReactNode;
  preview: React.ReactNode;
  open: boolean;
}) {
  return (
    <div className="flex h-screen">
      <main className={cn("flex min-w-0 flex-1 flex-col", open && "lg:max-w-[55%]")}>{chat}</main>
      {open && (
        <aside className="hidden w-[45%] border-l lg:flex lg:flex-col">
          {preview}
        </aside>
      )}
    </div>
  );
}
```

**移动**：`open` 时全屏 Sheet 盖住对话，返回键关闭。

---

## 4. 预览面板状态机

![预览状态机](image/source-preview-sidebar/02-preview-states.png)

| 状态 | UI |
|------|-----|
| `idle` | 侧栏关闭或占位「点击引用查看原文」 |
| `loading` | Skeleton + 文档名 |
| `ready` | 预览器挂载 |
| `error` | 重试按钮 |
| `permission_denied` | 「无权查看该文档」 |

```typescript
type PreviewState =
  | { kind: "idle" }
  | { kind: "loading"; title: string }
  | { kind: "ready"; citation: Citation; url: string }
  | { kind: "error"; message: string }
  | { kind: "permission_denied" };
```

---

## 5. 按文档类型路由预览器

| 类型 | 组件 | 定位 |
|------|------|------|
| PDF | `PdfPreview`（[178](178.pdf-highlight-locate-tutorial（front-end）.md)） | `?page=12` |
| Markdown | `MdPreview` | `#heading-id` |
| HTML | `iframe` sandbox | `?highlight=` |

```tsx
function SourcePreviewRouter({ citation, url }: { citation: Citation; url: string }) {
  const ext = citation.title.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return <PdfPreview url={url} page={citation.page} excerpt={citation.excerpt} />;
  if (ext === "md") return <MdPreview url={url} section={citation.section} />;
  return <iframe title={citation.title} src={url} className="h-full w-full" sandbox="" />;
}
```

---

## 6. signed URL 与权限

```typescript
async function resolvePreviewUrl(citation: Citation): Promise<string> {
  const res = await fetch(`/api/citations/${citation.chunk_id}/preview-url`);
  if (res.status === 403) throw new PermissionDeniedError();
  if (!res.ok) throw new Error("preview url failed");
  const { url, expires_at } = await res.json();
  return url;
}
```

**原则**：预览 URL **短期有效**；chunk 级 ACL 与 [121](121.unauthorized-doc-filter-tutorial.md) 检索过滤 **双保险**。

---

## 7. 与 citation 点击联动

```tsx
const [preview, setPreview] = useState<PreviewState>({ kind: "idle" });

const openCitation = async (c: Citation) => {
  setPreview({ kind: "loading", title: c.title });
  setSidebarOpen(true);
  try {
    const url = await resolvePreviewUrl(c);
    setPreview({ kind: "ready", citation: c, url });
  } catch (e) {
    if (e instanceof PermissionDeniedError) setPreview({ kind: "permission_denied" });
    else setPreview({ kind: "error", message: "加载失败" });
  }
};
```

行内 `[1]` 点击：解析 `data-citation-index` 调同一 `openCitation`。

---

## 8. 综合实战：PreviewSidebar 组件

```tsx
export function PreviewSidebar({
  state,
  onClose,
}: {
  state: PreviewState;
  onClose: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b px-4 py-2">
        <span className="truncate text-sm font-medium">
          {state.kind === "ready" ? state.citation.title : "原文预览"}
        </span>
        <button type="button" onClick={onClose} aria-label="关闭预览">
          ✕
        </button>
      </header>
      <div className="flex-1 overflow-hidden">
        {state.kind === "loading" && <PreviewSkeleton />}
        {state.kind === "ready" && <SourcePreviewRouter citation={state.citation} url={state.url} />}
        {state.kind === "permission_denied" && <DeniedPanel />}
        {state.kind === "error" && <ErrorPanel message={state.message} />}
      </div>
    </div>
  );
}
```

---

## 9. 先错对对：四种典型翻车

### 9.1 错：侧栏只显示 chunk 文本

**对**：加载 **源文件** PDF/MD。

### 9.2 错：永久 URL 泄露

**对**：signed URL + 过期。

### 9.3 错：桌面侧栏在 mobile 仍占 45%

**对**：Sheet 全屏。

### 9.4 错：切换引用不卸载旧 iframe

**对**：`key={chunk_id}` 强制 remount。

---

## 10. 性能：懒加载与缓存

- 首次打开才 `import('react-pdf')`；  
- 同一 `doc_id` 的 PDF **blob 缓存** 5 分钟；  
- 预取：用户 hover 卡片 200ms 后 prefetch URL（可选）。

---

## 11. 综合概念地图

![侧边栏预览概念地图](image/source-preview-sidebar/03-concept-map.png)

---

## 12. 常见陷阱与 FAQ

### 12.1 iframe XSS？

`sandbox` 限制脚本；HTML 来源需 CSP。

### 12.2 与 [115](115.source-document-navigation-tutorial.md) 关系？

`navigate_url` 可指向 **前端路由** `/preview?chunk_id=`，由本篇组件消费。

---

## 13. 总结与系列下一步

1. **侧栏预览** = 双栏 + 状态机 + 多格式路由 + signed URL。  
2. 与 [176 卡片](176.citation-card-ui-tutorial（front-end）.md)、[113 行内](113.inline-citation-tutorial.md) 共用 `openCitation`。  
3. PDF 精确定位见 [178](178.pdf-highlight-locate-tutorial（front-end）.md)。

### 13.1 系列下一步

| 目标 | 阅读 |
|------|------|
| PDF 高亮 | [178 PDF 高亮定位](178.pdf-highlight-locate-tutorial（front-end）.md) |
| 导航 API | [115 源文档导航](115.source-document-navigation-tutorial.md) |

### 13.2 面试 30 秒版

「点引用开右侧 PreviewSidebar，resolvePreviewUrl 拿 signed URL。按扩展名路由 PdfPreview 或 MdPreview。状态机 loading ready error permission_denied。移动用 Sheet。chunk_id 作 key 防 iframe 残留。」

''' + FOOTER_F2

ARTICLE_178 = r'''# F2 前端（八）：PDF 高亮定位完全指南 —— 阶段 4 全栈收官

> 侧边栏已能打开 PDF（[177 篇](177.source-preview-sidebar-tutorial（front-end）.md)），但若不能 **跳到第 n 页并把 chunk 那句话标黄**，法务仍说「看不清依据在哪」。**PDF 高亮定位**把 [52 页码元数据](52.metadata-source-page-tutorial.md)、[115 导航](115.source-document-navigation-tutorial.md) 与 **PDF.js 文本层** 接到一起。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **F2 前端第八篇**（路线图第 **195** 条），**了解档**，也是 **路线图 145～195 批量教程的系列收官**。前置：[177 侧边栏预览](177.source-preview-sidebar-tutorial（front-end）.md)、[115 源文档导航](115.source-document-navigation-tutorial.md)、[42 PyMuPDF](42.pymupdf-tutorial.md)、[176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)。

---

## 目录

1. [前言：PDF 高亮是溯源体验的皇冠](#1-前言pdf-高亮是溯源体验的皇冠)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [PDF 高亮定位链路](#3-pdf-高亮定位链路)
4. [入库时应存什么：page 与 text anchor](#4-入库时应存什么page-与-text-anchor)
5. [定位策略：页码跳转、文本搜索、bbox](#5-定位策略页码跳转文本搜索bbox)
6. [react-pdf / PDF.js 实战](#6-react-pdf--pdfjs-实战)
7. [高亮层实现](#7-高亮层实现)
8. [扫描件与 OCR 降级](#8-扫描件与-ocr-降级)
9. [综合实战：PdfPreview 组件](#9-综合实战pdfpreview-组件)
10. [先错对对：四种典型翻车](#10-先错对对四种典型翻车)
11. [阶段 4 全栈产品验收清单](#11-阶段-4-全栈产品验收清单)
12. [综合概念地图](#12-综合概念地图)
13. [常见陷阱与 FAQ](#13-常见陷阱与-faq)
14. [总结：从 145 到 195，再到阶段 4 项目](#14-总结从-145-到-195再到阶段-4-项目)

---

## 1. 前言：PDF 高亮是溯源体验的皇冠

[企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **阶段 4：全栈产品** 的验收写的是：**上传 → 问答 → 看引用**。「看引用」的顶配体验，是 **PDF 第 12 页「年假 10 天」一句话高亮**——不是近似页，不是纯文本弹窗。

**PDF 高亮定位（PDF Highlight & Locate）**：根据 chunk 元数据与文本，在 PDF 查看器中滚动到目标页，并在文本层上叠加高亮矩形或 `<mark>`。  
通俗说：**点 [1]，右侧手册自动翻页并标黄**。

**读完本文，你应该能做到：**

1. 说明 [52 page](52.metadata-source-page-tutorial.md) 在定位中的必要性。  
2. 比较 **页码 + 文本搜索** 与 **入库 bbox** 两路线。  
3. 用 `react-pdf` 实现 §9 `PdfPreview`。  
4. 处理 **文本层为空** 的扫描 PDF 降级。  
5. 把能力接入 [177 PreviewSidebar](177.source-preview-sidebar-tutorial（front-end）.md)。  
6. 对照 [阶段 4 验收](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 打勾。

### 1.1 系列收官位置

```text
145 LangChain VectorStore … 后端 API … 188 消息列表 … 194 侧栏预览
195 PDF 高亮定位 ← 本篇（F2 收官，衔接阶段 4 项目）
196+ 上传界面、管理台 …
```

---

## 2. 本文边界与动手路径

**档位：F2 了解篇（路线图 195，加分项）。**

**本文讲：** PDF.js 集成、页码跳页、文本搜索高亮、bbox 预告、OCR 降级、阶段 4 验收。  
**本文不讲：** 完整 OCR 流水线（[55 篇](55.ocr-scanned-docs-tutorial.md)）、PDF 编辑、数字签名。

### 2.1 动手路径表

| 步骤 | 你做什么 | 验收 |
|------|----------|------|
| A | 检查向量库 metadata 有 `page` | [52 篇](52.metadata-source-page-tutorial.md) |
| B | `pnpm add react-pdf pdfjs-dist` | 能渲染第 1 页 |
| C | §9 跳页 + 文本高亮 | 点 [1] 标黄 |
| D | 接入 [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md) | 端到端 Demo |
| E | 对照 §11 阶段 4 清单 | 路演材料 |

---

## 3. PDF 高亮定位链路

![PDF 高亮定位链路](image/pdf-highlight-locate/01-pdf-locate-flow.png)

```text
用户点击 citation（[176](176.citation-card-ui-tutorial（front-end）.md)）
  → resolvePreviewUrl（[177](177.source-preview-sidebar-tutorial（front-end）.md)）
  → PdfPreview 加载 PDF
  → initialPage = citation.page
  → text layer 渲染完成
  → search excerpt 或应用 bbox overlay
  → scroll to highlight
```

---

## 4. 入库时应存什么：page 与 text anchor

| 字段 | 用途 | 来自 |
|------|------|------|
| `page` | 1-based 页码 | [52](52.metadata-source-page-tutorial.md) |
| `text` | chunk 原文搜索 | ingest |
| `char_start` / `char_end` | 可选页内偏移 | [42 PyMuPDF](42.pymupdf-tutorial.md) |
| `bbox` | 可选归一化框 | layout 解析 |

**最小可行**：`page` + `excerpt` 前 80 字 **子串搜索**——PoC 够用；错位时升级 bbox。

---

## 5. 定位策略：页码跳转、文本搜索、bbox

![文本匹配与 bbox](image/pdf-highlight-locate/02-bbox-vs-text.png)

| 策略 | 精度 | 成本 |
|------|------|------|
| 仅跳页 | 低 | 低 |
| 跳页 + 文本搜索 | 中 | 中（依赖文本层） |
| 入库 bbox | 高 | ingest 复杂 |
| OCR 区域 | 扫描件 | [55 OCR](55.ocr-scanned-docs-tutorial.md) |

**推荐路径**：阶段 4 项目 **先跳页+文本搜索**；法务强需求再加 bbox。

---

## 6. react-pdf / PDF.js 实战

```bash
pnpm add react-pdf pdfjs-dist
```

```tsx
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();
```

**务必开启 TextLayer**——高亮依赖文本 DIV 位置。

---

## 7. 高亮层实现

### 7.1 文本搜索高亮

```typescript
function normalizeForSearch(s: string) {
  return s.replace(/\s+/g, " ").trim().slice(0, 120);
}

async function findTextSpans(page: pdfjs.PDFPageProxy, query: string) {
  const textContent = await page.getTextContent();
  const full = textContent.items.map((it: any) => it.str).join("");
  const idx = full.indexOf(normalizeForSearch(query));
  if (idx < 0) return [];
  // 简化：映射 item 到 bbox，生产可用 pdf.js findController
  return [];
}
```

生产可用 **自定义 overlay div**，按 `transform` 绝对定位到 text layer 上。

### 7.2 bbox overlay（入库有 bbox 时）

```tsx
function BboxHighlight({ bbox }: { bbox: [number, number, number, number] }) {
  const [x0, y0, x1, y1] = bbox; // 归一化 0..1
  return (
    <div
      className="pointer-events-none absolute bg-yellow-300/40"
      style={{ left: `${x0 * 100}%`, top: `${y0 * 100}%`, width: `${(x1 - x0) * 100}%`, height: `${(y1 - y0) * 100}%` }}
    />
  );
}
```

---

## 8. 扫描件与 OCR 降级

文本层为空时：

1. 侧栏文案：「该页为扫描件，无法精确高亮，已跳转到第 n 页」；  
2. 不 **伪造** 高亮框；  
3. 长期接 [55 OCR](55.ocr-scanned-docs-tutorial.md) 把字放进可搜索层。

---

## 9. 综合实战：PdfPreview 组件

```tsx
interface PdfPreviewProps {
  url: string;
  page?: number;
  highlightText?: string;
}

export function PdfPreview({ url, page = 1, highlightText }: PdfPreviewProps) {
  const [numPages, setNumPages] = useState(0);
  const pageRef = useRef<HTMLDivElement>(null);

  return (
    <div className="h-full overflow-auto p-4">
      <Document file={url} onLoadSuccess={({ numPages }) => setNumPages(numPages)}>
        <div ref={pageRef} className="relative mx-auto w-fit">
          <Page pageNumber={page} renderTextLayer renderAnnotationLayer width={680} />
          {highlightText && <TextHighlightOverlay pageNumber={page} text={highlightText} />}
        </div>
      </Document>
      <div className="text-muted-foreground mt-2 text-center text-xs">
        第 {page} 页 / 共 {numPages} 页
      </div>
    </div>
  );
}
```

从 [177](177.source-preview-sidebar-tutorial（front-end）.md) 传入 `citation.page` 与 `citation.excerpt`。

---

## 10. 先错对对：四种典型翻车

### 10.1 错：页码 0-based 与 1-based 混用

**对**：UI 与 [52](52.metadata-source-page-tutorial.md) 统一 1-based。

### 10.2 错：无 text layer 仍画假高亮

**对**：诚实降级（§8）。

### 10.3 错：整 PDF 一次渲染所有页

**对**：单页或虚拟滚动。

### 10.4 错：高亮与引用 excerpt 不一致

**对**：用 citation 下发 excerpt，勿前端再截断错位。

---

## 11. 阶段 4 全栈产品验收清单

对照 [ENTERPRISE_RAG_ROADMAP 阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品)：

| 验收项 | 相关教程 | 你应演示 |
|--------|----------|----------|
| 聊天界面 | [171](171.chat-message-list-ui-tutorial（front-end）.md) | 多轮消息 |
| 流式答案 | [174](174.streaming-typewriter-ui-tutorial（front-end）.md)、[116](116.sse-rag-streaming-tutorial.md) | 打字机 |
| 可中断 | [175](175.abort-controller-stream-tutorial（front-end）.md) | 点停止 |
| 引用可点 | [113](113.inline-citation-tutorial.md)、[176](176.citation-card-ui-tutorial（front-end）.md) | 卡片+行内 |
| 原文预览 | [177](177.source-preview-sidebar-tutorial（front-end）.md) | 侧栏 |
| PDF 跳页高亮 | 本篇 | 标黄句 |
| 多用户隔离 | [166](166.tenant-isolation-backend-tutorial.md)、[164 JWT](164.jwt-auth-rag-tutorial.md) | 租户 A 不见 B 文档 |
| 上传索引 | 路线图 196+、[159 Celery](159.celery-async-queue-tutorial.md) | 后台任务 |

**项目目录**：[`projects/04-fullstack-assistant/`](projects/04-fullstack-assistant/)——用阶段 4 里程碑把 **145～195 教程** 落成可销售 Demo。

---

## 12. 综合概念地图

![PDF 高亮与阶段 4 全栈](image/pdf-highlight-locate/03-concept-map.png)

| 层 | 篇目 |
|----|------|
| 数据 | [52 page](52.metadata-source-page-tutorial.md)、[51 chunk_id](51.metadata-chunk-id-tutorial.md) |
| 检索 | [91 dense](91.dense-retrieval-tutorial.md)、[76 Chroma](76.chroma-vector-db-tutorial.md) |
| 生成 | [113 引用](113.inline-citation-tutorial.md)、[116 SSE](116.sse-rag-streaming-tutorial.md) |
| 前端 F2 | [171～177](171.chat-message-list-ui-tutorial（front-end）.md)、本篇 |
| 产品 | [阶段 4 全栈](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) |

---

## 13. 常见陷阱与 FAQ

### 13.1 一定用 react-pdf 吗？

也可用 PDF.js 原生 API 或 `@react-pdf-viewer/highlight` 插件——选型看许可与包体积。

### 13.2 多栏 PDF？

layout 复杂时 **bbox** 优于纯文本搜索—— ingest 用 [37 layout](37.pdf-layout-tables-tutorial.md)。

### 13.3 下一步学什么？

路线图 **196 上传界面**、**197 索引进度**、**阶段 5 Langfuse**——见 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md)。

---

## 14. 总结：从 145 到 195，再到阶段 4 项目

1. **PDF 高亮** = `page` 跳页 + text layer 搜索或 bbox overlay + 扫描件降级。  
2. 接入 [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md)，完成 **点引用看原文** 闭环。  
3. 本篇收官 **路线图 190～195 F2 前端溯源主线**；全栈交付以 **[阶段 4：企业知识库助手](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品)** 验收。

### 14.1 F2 前端八篇回顾

| 路线图 | 文件 | 关键词 |
|--------|------|--------|
| 188 | [171 消息列表](171.chat-message-list-ui-tutorial（front-end）.md) | 气泡、滚动 |
| 189 | [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) | XSS、渲染 |
| 190 | [173 代码高亮](173.code-highlight-rag-tutorial（front-end）.md) | hljs/shiki |
| 191 | [174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) | SSE delta |
| 192 | [175 中断](175.abort-controller-stream-tutorial（front-end）.md) | AbortController |
| 193 | [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) | citations UI |
| 194 | [177 侧栏预览](177.source-preview-sidebar-tutorial（front-end）.md) | 双栏 |
| 195 | 本篇 | PDF 高亮 |

### 14.2 与 C6 后端链路合龙

```text
检索 [91] → 生成 [110] → SSE [116] → 打字机 [174] → 引用 [176] → 侧栏 [177] → PDF [178]
```

### 14.3 学习目标自检

- [ ] PdfPreview 跳页正确  
- [ ] 文本层高亮或诚实降级  
- [ ] 阶段 4 验收表打勾  
- [ ] 能路演 5 分钟全栈 Demo  

''' + FOOTER_178
