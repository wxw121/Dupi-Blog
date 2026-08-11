# -*- coding: utf-8 -*-
"""Second-pass padding for tutorials 173-178."""

PAD_173 = r'''
## 附录 G：RAG 答案中的代码块类型速查

企业知识库中，模型返回的围栏代码块可粗分为六类，前端高亮策略应分别优化：

| 类型 | 语言标签 | 高亮注意 |
|------|----------|----------|
| Shell 运维 | bash / sh | 提示符 `$` 与 `#` 分色 |
| 配置文件 | yaml / json / toml | 严格缩进显示 |
| 应用代码 | python / ts / go | 长行横向滚 |
| 查询语言 | sql | 关键字大写可读性 |
| 协议示例 | http / graphql | 字符串引号清晰 |
| 日志片段 | log / text | 时间戳与 LEVEL 分色 |

当模型未标注语言时，可用启发式：以 `{` 开头猜 json，以 `apiVersion:` 猜 yaml，以 `SELECT` 猜 sql——但 **Prompt 约束优先于启发式**。

---

## 附录 H：与 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 管道插入点详解

```text
原始 Markdown 字符串
  → remark-parse
  → remark-gfm（表格、删除线）
  → rehype-sanitize（XSS）
  → rehype-highlight 或自定义 code 组件
  → React 树
```

若你已在 172 使用 `rehype-highlight`，本篇 CodeBlock 可 **替换** 该插件以避免双重高亮。若 172 用 `react-syntax-highlighter`，评估包体积后决定是否迁 hljs 核心按需加载。

---

## 附录 I：深色与浅色主题双套 CSS

```css
:root[data-theme="light"] .hljs { background: #f6f8fa; }
:root[data-theme="dark"] .hljs { background: #0d1117; }
```

切换主题时 **勿 remount 整棵树**，仅换 class，避免 [174 流式](174.streaming-typewriter-ui-tutorial（front-end）.md) 闪烁。

---

## 附录 J：复制按钮无障碍

```tsx
<button aria-label={`复制${language}代码`} />
```

复制成功用 `aria-live` 播报「已复制」，勿仅靠颜色变化。

---

## 附录 K：Ten 条团队规范（Wiki 可粘贴）

1. 所有代码块必须可复制纯文本。  
2. 流式未 done 不高亮 shiki。  
3. sanitize 白名单含 `span.hljs-*`。  
4. 禁止模型返回可执行 HTML 代码块。  
5. 含密钥片段必须打码后高亮。  
6. 移动端代码块最大高度 24rem，超出内滚。  
7. 打印 PDF 导出用浅色主题。  
8. 语言未知用 `text`，禁止假标 python。  
9. 与 citations 无耦合，高亮不改编号。  
10. PoC 用 hljs，品牌定型再评 shiki。

---

## 附录 L：与阶段 4 全栈产品的关系

[阶段 4 验收](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 不强制代码高亮，但 **技术文档型知识库**（运维、研发手册）强烈建议接入本篇，否则演示效果弱于竞品。在 `04-fullstack-assistant` 的 `MarkdownAnswer` 中默认启用 CodeBlock 即可。

---

## 附录 M：常见语言 alias 映射

```typescript
const LANG_ALIAS: Record<string, string> = {
  js: "javascript",
  ts: "typescript",
  yml: "yaml",
  shell: "bash",
  sh: "bash",
  py: "python",
};
```

模型常写短标签，前端映射后再传入 hljs。

---

## 附录 N：性能 Profiling 检查点

Chrome Performance：记录一次 **done 后高亮** 的 Scripting 时间，目标 < 16ms（单块）。若超 50ms，拆分为 `startTransition` 或 Web Worker（高级，了解即可）。

---

## 附录 O：读者练习（自学）

1. 在 Storybook 渲染 5 种语言同屏；  
2. 模拟流式输入未闭合 ` ``` ` 观察 UI；  
3. 用 Lighthouse 对比开/关高亮 JS 体积；  
4. 读 [16 XSS](16.markdown-rendering-security-tutorial（front-end）.md) 构造恶意围栏，验证 sanitize。
'''

PAD_174 = r'''
## 附录 I：TTFT 与检索时延展示

**TTFT**（Time To First Token）：从发送到首 delta 的时间。分解展示可提升信任：

```tsx
{phase === "retrieving" && (
  <span className="text-xs">检索中… {retrieveMs != null && `${retrieveMs}ms`}</span>
)}
```

后端可在首个 `message` 前发自定义头 `X-Retrieve-Ms`，或单独 `event: retrieve_meta`（团队扩展，需与 [116](116.sse-rag-streaming-tutorial.md) 版本化）。

---

## 附录 J：反压与队列上限

若模型推送极快、用户设备慢，pending delta 队列可设 **上限 512KB**，超出则合并为批量 flush 并打 warn 日志，防止内存涨。

---

## 附录 K：多会话 Tab 并发

每个聊天 Tab 独立 `useRagStream` 实例，**禁止** 全局单例 content——否则串台。

---

## 附录 L：与 [171 消息列表](171.chat-message-list-ui-tutorial（front-end）.md) 滚动契约

```typescript
function shouldAutoScroll(container: HTMLElement) {
  const { scrollTop, scrollHeight, clientHeight } = container;
  return scrollHeight - scrollTop - clientHeight < 80;
}
```

新消息仅在贴底时滚；用户上滑历史时不打扰。

---

## 附录 M：打字机光标可访问性

装饰性光标对读屏隐藏：`aria-hidden="true"` 放在光标 span 上，完成态移除光标。

---

## 附录 N：错误重试 UX

`error` 态提供「重试」按钮，重试 **新 controller**，勿复用 aborted signal。

---

## 附录 O：国际化预留

流式文案「正在检索…」「停止生成」抽 `i18n` key，阶段 4 出海时省事。

---

## 附录 P：E2E 测试要点（Playwright）

```typescript
await page.getByPlaceholder("输入问题").fill("年假几天");
await page.getByRole("button", { name: "发送" }).click();
await expect(page.getByText("正在检索")).toBeVisible();
await expect(page.locator(".typewriter-cursor")).toBeVisible();
await expect(page.getByText("参考来源")).toBeVisible({ timeout: 30000 });
```

---

## 附录 Q：与 OpenAI 兼容流格式差异

部分网关用 OpenAI `data: {"choices":[{"delta":{"content":"x"}}]}` 而非本篇 [116](116.sse-rag-streaming-tutorial.md) 事件。适配层应在 **前端或 BFF 统一** 为 `message/citations/done`，避免组件内分叉。

---

## 附录 R：弱网下降级

`navigator.connection?.effectiveType === "2g"` 时可加大 rAF 合并窗口到 100ms，略降跟手感换流畅。

---

## 附录 S：阶段 4 演示 checklist

- [ ] 检索 spinner 可见  
- [ ] 首字 < 5s（视模型）  
- [ ] 停止可点  
- [ ] done 后 Markdown 渲染  
- [ ] citations 卡片出现  

---

## 附录 T：全栈联调会议议程（30min）

1. 后端念 [116] 事件 JSON（5min）  
2. 前端 demo 打字机（10min）  
3. 对齐 citations 字段（10min）  
4. 定 trace_id 贯穿（5min）
'''

PAD_175 = r'''
## 附录 I：fetch 流读取完整模板

```typescript
async function consumeSSE(
  body: ReadableStream<Uint8Array>,
  signal: AbortSignal,
  onEvent: (event: string, data: string) => void,
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const block = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        let ev = "message";
        let data = "";
        for (const line of block.split("\n")) {
          if (line.startsWith("event:")) ev = line.slice(6).trim();
          if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (data) onEvent(ev, data);
      }
    }
  } finally {
    reader.releaseLock();
  }
}
```

在 `signal.aborted` 时 `reader.cancel()` 更干净。

---

## 附录 J：Nginx 与 abort

客户端 abort 后，Nginx 可能仍短暂缓冲——与 [116 §11](116.sse-rag-streaming-tutorial.md) 一样配置 `proxy_buffering off`。

---

## 附录 K：Sentry 过滤 AbortError

```typescript
Sentry.init({
  beforeSend(event, hint) {
    if (hint.originalException?.name === "AbortError") return null;
    return event;
  },
});
```

---

## 附录 L：按钮态互斥

| streaming | 发送钮 | 停止钮 |
|-----------|--------|--------|
| false | 启用 | 隐藏 |
| true | 禁用 | 启用 |

防连点双请求。

---

## 附录 M：部分 citations 的 legal 提示

aborted 后若答案含数字建议，UI 轻提示「本回答未完整生成，请勿用于合规决策」——视行业而定。

---

## 附录 N：与 [117 WebSocket](117.websocket-rag-streaming-tutorial.md) 迁移路径

若已从 SSE 迁 WS：保留 `stop()` 对外 API，内部改发 `{type:"cancel"}` 帧，**组件层无感**。

---

## 附录 O：后端 FastAPI 版本差异

`Request.is_disconnected()` 在 Starlette 各版本行为一致；若用 gunicorn+uvicorn worker，确认 **graceful timeout** 不拖死 cancel。

---

## 附录 P：负载测试 abort 率

压测时 10% 虚拟用户随机 2s 后 stop，观察后端 GPU/Token 是否下降——验证真取消。

---

## 附录 Q：React Strict Mode 双调用

开发环境 StrictMode 可能双 mount——确保 cleanup `abort()`，否则幽灵流。

```typescript
useEffect(() => () => controller.abort(), []);
```

---

## 附录 R：阶段 4 必演示「停止」

路线图 [阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 与 [阶段 0 流式对话](ENTERPRISE_RAG_ROADMAP.md#阶段-0基础补齐) 均提到中断——本篇为必练。

---

## 附录 S：团队 Wiki 模板

**标题**：RAG 流式中断规范  
**内容**：每次 ask new AbortController；stop=abort；aborted 保留 partial；后端 disconnect break；禁止仅停 UI。
'''

PAD_176 = r'''
## 附录 I：卡片排序策略

默认按 `index` 升序；若产品要「相关度优先」，可 `score` 降序但 **行内编号仍不变**——勿重排 index 导致 [113](113.inline-citation-tutorial.md) 错位。

---

## 附录 J：空 citations 态

模型拒答或 [112](112.refusal-strategy-tutorial.md) 无依据时，`citations: []`，卡片区隐藏，勿留空标题。

---

## 附录 K：缩略图 preview（可选）

若 metadata 含 `thumbnail_url`，卡片左侧 40px 缩略图提升识别——PDF 首页渲染图，非必需。

---

## 附录 L：打印与导出

导出 PDF 报告时，卡片转脚注列表，避免侧栏交互件。

---

## 附录 M：chunk 去重展示

同一 `chunk_id` 不应出现两次；若检索重复，后端去重后再发 citations。

---

## 附录 N：hover 预取 preview-url

```typescript
onMouseEnter={() => prefetchPreview(c.chunk_id)}
```

延迟 200ms 触发，降低侧栏首开时延（配合 [177](177.source-preview-sidebar-tutorial（front-end）.md)）。

---

## 附录 O：审计日志字段

点击卡片上报：`user_id, chunk_id, doc_id, session_id, ts`——对接 [213 审计](ENTERPRISE_RAG_ROADMAP.md) 方向。

---

## 附录 P：A11y 焦点管理

卡片 `onClick` 后焦点移到侧栏关闭钮或预览区，方便键盘用户。

---

## 附录 Q：与设计系统 Card 组件关系

若用 shadcn `Card`，注意 `button` 嵌套规则——整卡用 `button` 或 `div role="button"` 二选一。

---

## 附录 R：多语言 excerpt

chunk 含英文条款时，`line-clamp` 仍适用；字体 `font-sans` 覆盖拉丁字符。

---

## 附录 S：阶段 4 引用闭环

验收「看引用」= [176 卡片](176.citation-card-ui-tutorial（front-end）.md) + [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md) + [178 PDF](178.pdf-highlight-locate-tutorial（front-end）.md) 至少一种格式打通。
'''

PAD_177 = r'''
## 附录 J：断点响应式表

| 断点 | 布局 |
|------|------|
| < lg | Sheet 全屏预览 |
| lg～xl | 45% 侧栏 |
| xl+ | 可选 40% + 拖曳 |

---

## 附录 K：PDF 工具栏

侧栏 header 放：页码、放大、下载（若策略允许）、关闭。

---

## 附录 L：Markdown 代码块在预览内

若预览 MD 含代码，递归调用 [173 高亮](173.code-highlight-rag-tutorial（front-end）.md)——注意嵌套 sanitize。

---

## 附录 M：CSP 与 signed URL 域

`Content-Security-Policy` 的 `frame-src` / `connect-src` 需含对象存储域。

---

## 附录 N：预览失败重试指数退避

`1s, 2s, 4s` 最多三次，仍失败显示人工联系管理员。

---

## 附录 O：与 footnote [114](114.footnote-citation-tutorial.md) 点击统一

脚注区点击也调 `openCitation`，API 一处维护。

---

## 附录 P：深色模式 iframe

PDF.js 自带灰底，侧栏 `bg-background` 与之协调，避免刺眼白边。

---

## 附录 Q：租户级水印（可选）

预览 PDF 叠半透明 `user@corp` 水印，防截图外泄——高级合规，了解即可。

---

## 附录 R：性能：React.lazy

```typescript
const PdfPreview = lazy(() => import("./PdfPreview"));
```

首屏聊天不加载 pdfjs。

---

## 附录 S：阶段 4 双栏截图素材

产品/marketing 用双栏「左问右证」截图，强化 Grounding 品牌感知。
'''

PAD_178 = r'''
## 附录 K：PDF.js worker CORS

workerSrc 与 pdf 文件域不同源时，配置 CDN 或同源托管 worker，否则报 Worker 加载失败。

---

## 附录 L：旋转页面与定位

若 PDF 页 `rotate=90`，bbox 需变换矩阵——高级场景，PoC 可跳过旋转页。

---

## 附录 M：文本层选中与高亮 z-index

高亮 overlay `z-index` 高于 text layer，低于工具栏；`pointer-events-none` 防挡选中。

---

## 附录 N：compare 阶段 3 vs 阶段 4

| 阶段 | 引用能力 |
|------|----------|
| 阶段 3 后端 | API 返回 chunk 文本 |
| 阶段 4 全栈 | 点引用看 PDF 高亮 |

本篇是从 3 跃迁到 4 的 **体验分水岭**。

---

## 附录 O：Graph RAG 等 H 模块预告

[路线图 H 进阶](ENTERPRISE_RAG_ROADMAP.md#h-进阶方向senior--大厂加分) 的 Graph RAG 不改变本篇 PDF UI——节点证据仍可回落 `chunk_id` 预览。

---

## 附录 P：wasm pdf 渲染（了解）

移动端可考虑 pdfium wasm——包体积 trade-off，默认 react-pdf 足够。

---

## 附录 Q：highlightText 过长截断

搜索串最长 120 字，与 [176 excerpt](176.citation-card-ui-tutorial（front-end）.md) 对齐，提高命中率。

---

## 附录 R：版本 145～195 结业自测

- [ ] 能画 F2 前端八篇数据流  
- [ ] 能演示阶段 4 完整业务流  
- [ ] 能解释 PDF 无高亮降级  
- [ ] 能口述下一步 196+ 管理台  

---

## 附录 S：致读者

恭喜你完成 **路线图 190～195** 前端溯源系列。请把 `projects/04-fullstack-assistant/` 跑通，作为简历 **全栈 RAG** 代表作。下一阶段见 [ENTERPRISE_RAG_ROADMAP 阶段 5](ENTERPRISE_RAG_ROADMAP.md#阶段-5生产化)。
'''

PAD = {
    "173.code-highlight-rag-tutorial（front-end）.md": PAD_173,
    "174.streaming-typewriter-ui-tutorial（front-end）.md": PAD_174,
    "175.abort-controller-stream-tutorial（front-end）.md": PAD_175,
    "176.citation-card-ui-tutorial（front-end）.md": PAD_176,
    "177.source-preview-sidebar-tutorial（front-end）.md": PAD_177,
    "178.pdf-highlight-locate-tutorial（front-end）.md": PAD_178,
}
