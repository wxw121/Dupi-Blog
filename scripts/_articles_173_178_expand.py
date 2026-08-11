# -*- coding: utf-8 -*-
"""Expansion blocks to pad tutorials 173-178 to >=5000 hanzi."""

EXPANSION_173 = r'''
## 附录 A：代码高亮场景案例库

### A.1 运维 Runbook 里的 YAML 片段

**场景**：RAG 返回 Deployment 片段，缩进错乱导致同事复制进集群报错。

**处理**：hljs `language-yaml` 着色 + 复制按钮；在 [110 Prompt](110.rag-prompt-template-tutorial.md) 要求保留原始缩进。

**复盘**：把该 query 纳入金标，检查 faithfulness。

### A.2 API 网关 curl 示例

**场景**：答案含 `curl -H "Authorization: Bearer ..."`，关键字与引号难辨。

**处理**：`language-bash` 高亮；复制后仍走 [122 安全](122.content-safety-filter-tutorial.md) 打码 token。

### A.3 内网 SQL 查询片段

**场景**：数据分析问答返回 `SELECT`，无高亮时 `JOIN` 与列名粘连。

**处理**：shiki 主题与 DataGrip 接近，降低认知切换成本。

### A.4 多语言混排代码块

**场景**：同一条答案里先 `python` 再 `json`。

**处理**：每围栏独立 `CodeBlock`，按 `className` 解析语言，禁止全局默认 python。

---

## 附录 B：代码高亮联调检查单（20 项）

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 与 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) sanitize 共存 | 无 script 执行 |
| 2 | 行内 code 与块级分离 | 行内无 hljs 整块背景 |
| 3 | 流式未闭合围栏 | 灰底不闪 |
| 4 | done 后高亮 | 颜色完整 |
| 5 | 复制纯文本 | 粘贴终端可运行 |
| 6 | 暗色主题对比度 | WCAG AA |
| 7 | 横向超长行 | overflow-x auto |
| 8 | 移动双指滚动 | 不触发页面横向乱滚 |
| 9 | 语言未知 | fallback text |
| 10 | 空代码块 | 不渲染 0 高度 |
| 11 | 与 [174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) 状态 | streaming 策略一致 |
| 12 | 打印样式 | 浅色可读 |
| 13 | SSR hydration | 无水合闪动 |
| 14 | 包体积 | hljs 按需 registerLanguage |
| 15 | 与 [173] 同页多块 | 不共享 DOM id |
| 16 | API Key 片段 | 打码后高亮 |
| 17 | diff 围栏 | 可选 language-diff |
| 18 | 日志片段 | language-log |
| 19 | 性能 10 块代码 | 无明显卡顿 |
| 20 | 评测抽检 | 高亮不改变原文语义 |

---

## 附录 C：highlight.js 按需加载示例

```typescript
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import bash from "highlight.js/lib/languages/bash";
import yaml from "highlight.js/lib/languages/yaml";
import json from "highlight.js/lib/languages/json";

hljs.registerLanguage("python", python);
hljs.registerLanguage("bash", bash);
hljs.registerLanguage("yaml", yaml);
hljs.registerLanguage("json", json);
```

**收益**：首屏 JS 下降，适合 [阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 外网访问。

---

## 附录 D：与 shiki 迁移清单

| 步骤 | 动作 |
|------|------|
| 1 | 选主题 `github-dark` |
| 2 | 流结束后 `codeToHtml` 批处理 |
| 3 | 缓存 `Map<hash, html>` |
| 4 | 对比 PoC 首屏 LCP |
| 5 | 团队投票是否切换 |

---

## 附录 E：一周落地节奏（了解篇）

| 天 | 任务 | 产出 |
|----|------|------|
| 周一 | 读 172 + 本篇 §4 | 选型表 |
| 周二 | hljs CodeBlock | Storybook |
| 周三 | 接 171 气泡 | 集成 PR |
| 周四 | 流式策略 | 与 174 联调 |
| 周五 | 检查单 B | 演示 |

---

## 附录 F：面试追问速答

**问**：为什么 RAG 前端要高亮而不是后端？  
**答**：答案是 Markdown 字符串，前端已有解析链；后端 Pygments 增加往返与缓存复杂度。

**问**：流式每个 token 高亮行吗？  
**答**：不行，未闭合围栏与性能都不允许；done 后一次高亮。

**问**：hljs 输出用 innerHTML 安全吗？  
**答**：hljs 对输入转义；用户原始 HTML 必须先 sanitize。
'''

EXPANSION_174 = r'''
## 附录 A：流式 UI 场景案例库

### A.1 检索三秒空窗

**场景**：向量库冷启动，检索 2.8s，用户以为死机。

**处理**：独立 `retrieving` 态 + 文案「正在检索知识库（约 3 秒）」；可选展示检索到的 doc 数量 preview。

### A.2 长答案卡顿

**场景**：五千字政策解读，每个 delta setState 导致输入框掉帧。

**处理**：rAF 合并 + [172](172.markdown-render-rag-tutorial（front-end）.md) done 后一次 Markdown。

### A.3 引用提前可点

**场景**：模型先输出 `[1]`，citations 未到，用户点进 404。

**处理**：灰色不可点，citations 后启用 pointer-events。

### A.4 用户上滑阅读时自动滚底

**场景**：自动 scroll 抢控制权，体验极差。

**处理**：仅 `distanceToBottom < 80px` 时自动滚。

---

## 附录 B：SSE 解析健壮性

```typescript
function safeJsonParse(line: string): unknown | null {
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}
```

**半包问题**：`buffer` 累积到 `\n\n` 再切；勿假设一次 read 等于一个事件。

**心跳**：部分代理发 `: ping` 注释行，解析器应忽略。

---

## 附录 C：与路线图第 22 条对照

[路线图 A.22](ENTERPRISE_RAG_ROADMAP.md)：流式 UI 渲染（逐字显示、中断）。

| 能力 | 本篇 | [175](175.abort-controller-stream-tutorial（front-end）.md) |
|------|------|--------------------------------------------------|
| 逐字显示 | ✅ rAF | — |
| 中断 | 预留 stop | ✅ abort |

---

## 附录 D：性能预算

| 指标 | 目标 |
|------|------|
| 单 delta 处理 | < 4ms |
| rAF 内合并 | 无长任务 > 50ms |
| 内存 | 单条消息 < 2MB 文本 |

---

## 附录 E：可访问性细则

- `aria-live="polite"` 仅在 `done` 时播报「回答已完成」；  
- 停止按钮 `aria-label="停止生成"`；  
- 检索 spinner 带 `role="status"`。

---

## 附录 F：联调日志字段

前端上报：`trace_id`、`ttft_ms`（首 delta）、`retrieve_ms`、`total_stream_ms`、`aborted`。

与 [147 LangSmith](147.langsmith-tracing-tutorial.md) 对齐，便于 E 轨评测。

---

## 附录 G：Mock 流本地开发

```typescript
export async function* mockRagStream(): AsyncGenerator<RagStreamEvent> {
  yield { type: "message", delta: "根据" };
  await sleep(30);
  yield { type: "message", delta: "员工手册，年假为 10 天[1]。" };
  yield {
    type: "citations",
    citations: [{ index: 1, chunk_id: "c1", title: "手册.pdf", excerpt: "年假 10 天" }],
  };
  yield { type: "done", finish_reason: "stop" };
}
```

无后端时先跑通 [171](171.chat-message-list-ui-tutorial（front-end）.md) 布局。

---

## 附录 H：面试深度追问

**问**：为什么不用 WebSocket？  
**答**：单向问答 SSE/fetch 足够；双向见 [117](117.websocket-rag-streaming-tutorial.md)。

**问**：打字机延迟 artificial delay 要做吗？  
**答**：一般不要人为 sleep；跟随模型真实 delta，仅合并帧。

**问**：多轮历史放哪？  
**答**：POST body，见 [118](118.multi-turn-history-tutorial.md)；流式协议不变。
'''

EXPANSION_175 = r'''
## 附录 A：中断场景案例库

### A.1 用户快速连点发送

**场景**：前一个答案还在流，第二个问题发出。

**处理**：新 ask 先 `abort()` 旧 controller；UI 标记旧消息 `superseded`。

### A.2 停止后仍扣费

**场景**：网关未断开，Token 继续计。

**处理**：后端 `is_disconnected` + SDK cancel；财务看板对 abort 率建指标。

### A.3 停止后 citations 半拉

**场景**：abort 在 citations 前，答案有句末 `[1]` 无卡片。

**处理**：aborted 态不渲染可点引用；文案「引用未完整加载」。

### A.4 移动端切后台

**场景**：系统挂起连接，行为因浏览器而异。

**处理**：`visibilitychange` 可选自动 abort 或提示恢复。

---

## 附录 B：AbortError 处理模式

```typescript
try {
  await runStream(ac.signal);
} catch (e) {
  if (e instanceof DOMException && e.name === "AbortError") {
    return; // 用户主动停止，非错误
  }
  showErrorToast(e);
}
```

勿把 AbortError 打 error 级日志污染 Sentry。

---

## 附录 C：与 [6 WebSocket](6.websocket-tutorial.md) 可选对照

| 消息 | 方向 | 用途 |
|------|------|------|
| cancel | C→S | 停止生成 |
| ping | 双向 | 保活 |

**何时升级 WS**：协作旁听、输入状态、同连接多轮澄清——非仅停止。

---

## 附录 D：后端 Python 取消模式

```python
import asyncio

async def stream_with_cancel(gen, request: Request):
    task = asyncio.create_task(anext_or_none(gen))
    while True:
        if await request.is_disconnected():
            task.cancel()
            break
        # ...
```

注意 asyncio 与同步 SDK 混用时的线程边界。

---

## 附录 E：UI 文案规范

| 状态 | 文案 |
|------|------|
| aborted | 「已停止生成」 |
| error | 「生成失败，请重试」 |
| done | 无额外标签 |

勿用「出错」描述用户主动停止。

---

## 附录 F：安全：abort 能被滥用吗？

攻击者频繁 abort 可能造成连接抖动——配合 [186 Rate Limit](169.rate-limiting-api-tutorial.md) 限制每用户并发流。

---

## 附录 G：联调检查单（16 项）

| # | 项 | 标准 |
|---|-----|------|
| 1 | stop 调 abort | Network canceled |
| 2 | partial 保留 | 文本仍在 |
| 3 | 新 ask 杀旧流 | 单活跃流 |
| 4 | AbortError 静默 | 无红 toast |
| 5 | 后端 disconnect 日志 | 有记录 |
| 6 | Token 计费趋停 | 监控验证 |
| 7 | citations 不完整态 | UI 诚实 |
| 8 | 与 174 phase | aborted 枚举 |
| 9 | 按钮 loading | 停止可点 |
| 10 | 键盘 Esc | 可选绑定 stop |
| 11 | 移动端 | 同行为 |
| 12 | 并发 session | stream_id 隔离 |
| 13 | 重试 | 新 controller |
| 14 | WS 对照文档 | 117 链接 |
| 15 | E2E 测试 | Playwright abort |
| 16 | 阶段 4 验收 | 演示停止 |

---

## 附录 H：面试速答扩展

**问**：EventSource 能 abort 吗？  
**答**：支持有限且难 POST；RAG 用 fetch。

**问**：停止后能否续写？  
**答**：产品层新请求，带 partial 作上下文，非同一 HTTP 流恢复。
'''

EXPANSION_176 = r'''
## 附录 A：引用卡片产品案例

### A.1 多文档对比选型

**场景**：采购问「三个供应商付款条款差异」。

**处理**：卡片列表并排三 doc title + excerpt，点击分别开 [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md)。

### A.2 弱相关灰显

**场景**：rerank 分低但仍进 top-k。

**处理**：`score < 0.35` 卡片降透明度，tooltip「弱相关，仅供参考」。

### A.3 同一 doc 多 chunk

**场景**：[1][2] 都来自员工手册不同页。

**处理**：title 相同，excerpt 与 page 区分；勿合并为一张卡。

### A.4 无权文档

**场景**：检索 bug 泄露标题。

**处理**：`allowed: false`，卡片不可点，联系 [121 ACL](121.unauthorized-doc-filter-tutorial.md)。

---

## 附录 B：Citation JSON 完整示例

```json
{
  "citations": [
    {
      "index": 1,
      "chunk_id": "handbook-v3:p12:c004",
      "title": "员工手册.pdf",
      "excerpt": "带薪年假原则上为 10 个工作日……",
      "page": 12,
      "section": "第三章 休假",
      "score": 0.89,
      "navigate_url": "/preview?chunk_id=handbook-v3:p12:c004",
      "allowed": true
    }
  ]
}
```

与 [116 citations 事件](116.sse-rag-streaming-tutorial.md) 字段一致。

---

## 附录 C：行内与卡片联动高亮

```tsx
const [activeIndex, setActiveIndex] = useState<number>();

// Markdown 内 [1] 点击
onCitationClick={(idx) => setActiveIndex(idx)}

// 卡片 active 样式同步
<CitationCard active={c.index === activeIndex} />
```

---

## 附录 D：设计 Token 建议

| Token | 值 |
|-------|-----|
| 卡片圆角 | 8px |
| 摘录字号 | 12px |
| 索引字号 | 14px mono |
| 间距 | 8px gap |

与 [171](171.chat-message-list-ui-tutorial（front-end）.md) 气泡内边距对齐。

---

## 附录 E：脚注 [114](114.footnote-citation-tutorial.md) 并存策略

长报告：正文脚注编号 + 底部卡片可折叠「查看所有来源」。短 FAQ：仅卡片即可。

---

## 附录 F：评测挂钩

[141 Faithfulness](141.ragas-faithfulness-tutorial.md)：抽检「卡片 excerpt 是否支持带 [n] 的句子」。

[151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md)：若卡片与问题无关，先修检索非 UI。

---

## 附录 G：移动端 Bottom Sheet

```tsx
<Sheet open={open} onOpenChange={setOpen}>
  <SheetContent side="bottom" className="h-[70vh]">
    <CitationCardList items={citations} onSelect={openPreview} />
  </SheetContent>
</Sheet>
```

---

## 附录 H：一周交付节奏（主线）

| 天 | 产出 |
|----|------|
| 周一 | 类型 + 静态卡片 |
| 周二 | 接 citations 事件 |
| 周三 | 行内联动 |
| 周四 | 侧栏点击 |
| 周五 | ACL 灰显 + 演示 |
'''

EXPANSION_177 = r'''
## 附录 A：侧栏预览场景案例

### A.1 宽屏法务对照

**场景**：左答案右 PDF，逐条核对条款。

**处理**：默认 55/45 分栏，可拖曳调整到 50/50。

### A.2 内网 wiki HTML

**场景**：navigate_url 指向 `https://wiki.internal/page/123`。

**处理**：iframe sandbox + SSO cookie 域一致；失败提示开新窗。

### A.3 Markdown 仓库文件

**场景**：`handbook.md#休假制度`。

**处理**：`MdPreview` fetch raw + `rehype-slug` 锚点滚动。

### A.4 signed URL 过期

**场景**：用户侧栏停 30 分钟再滚动，403。

**处理**：捕获过期，一键 `refreshPreviewUrl()`。

---

## 附录 B：Preview API 契约

```
GET /api/citations/{chunk_id}/preview-url
→ 200 { "url": "https://...", "expires_at": "ISO8601", "mime": "application/pdf" }
→ 403 { "code": "FORBIDDEN" }
→ 404 chunk 不存在
```

与 [115 navigate_url](115.source-document-navigation-tutorial.md) 互补：navigate 可走前端路由，preview-url 走 API 鉴权。

---

## 附录 C：布局拖曳宽度（可选）

```tsx
const [width, setWidth] = useState(45); // percent
// mousedown on resizer → mousemove 更新 width
```

注意 `min-width` 防止预览区过窄不可读。

---

## 附录 D：键盘快捷键

| 键 | 行为 |
|----|------|
| Esc | 关闭侧栏 |
| Ctrl+\\ | 切换侧栏（可选） |

---

## 附录 E：与 [178 PDF](178.pdf-highlight-locate-tutorial（front-end）.md) 接口

```tsx
<PdfPreview
  url={url}
  page={citation.page}
  highlightText={citation.excerpt}
/>
```

侧栏负责壳，178 负责页内高亮。

---

## 附录 F：缓存策略

```typescript
const urlCache = new Map<string, { url: string; exp: number }>();

function getCachedUrl(chunkId: string) {
  const hit = urlCache.get(chunkId);
  if (hit && Date.now() < hit.exp) return hit.url;
  return null;
}
```

TTL 取 `expires_at - 60s` 安全边际。

---

## 附录 G：错误态文案

| code | 文案 |
|------|------|
| FORBIDDEN | 您无权查看该文档 |
| NOT_FOUND | 原文已删除或迁移 |
| NETWORK | 网络异常，点击重试 |

---

## 附录 H：阶段 4 演示脚本（5 分钟）

1. 登录租户 A；  
2. 问「年假几天」；  
3. 流式答案；  
4. 点卡片；  
5. 侧栏 PDF 第 12 页；  
6. 高亮句（178）；  
7. 切换租户 B 验证隔离。

---

## 附录 I：面试扩展

**问**：为何不用新标签默认？  
**答**：对照阅读效率；外链 wiki 才新开窗。

**问**：iframe 安全？  
**答**：sandbox + 可信源白名单。
'''

EXPANSION_178 = r'''
## 附录 A：PDF 定位案例库

### A.1 页码偏移

**场景**：封面算页导致 UI 第 12 页与 PDF 第 14 页。

**处理**：入库统一「印刷页」定义；[48 版本](48.doc-versioning-tutorial.md) 变更时重算。

### A.2 双栏排版文本搜索失败

**场景**：chunk 跨栏，简单 indexOf 失败。

**处理**：降级仅跳页；长期用 bbox。

### A.3 扫描合同

**场景**：无 text layer。

**处理**：§8 诚实文案 + [55 OCR](55.ocr-scanned-docs-tutorial.md) 路线。

### A.4 超大 PDF 200 页

**场景**：一次 render 全部页内存爆。

**处理**：单页模式 + 页码输入框跳转。

---

## 附录 B：PyMuPDF 入库 bbox 预告

```python
# ingest 时可选写入 metadata
block = page.get_text("dict")["blocks"]
# 匹配 chunk 文本 → 合并 bbox → 归一化
metadata["bbox"] = [x0, y0, x1, y1]  # 0..1
```

解析细节见 [42 PyMuPDF](42.pymupdf-tutorial.md)、[37 layout](37.pdf-layout-tables-tutorial.md)。

---

## 附录 C：@react-pdf-viewer/highlight 插件

若不想手写 overlay，可评估社区插件：

```bash
pnpm add @react-pdf-viewer/core @react-pdf-viewer/highlight
```

权衡：包体积 vs 开发速度。

---

## 附录 D：文本规范化细节

```typescript
function normalizeForSearch(s: string) {
  return s
    .replace(/\u00a0/g, " ")
    .replace(/[\u200b-\u200d\ufeff]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
```

PDF 文本层常有奇怪空白。

---

## 附录 E：阶段 4 与阶段 5 衔接

| 阶段 | 目标 | 与本篇关系 |
|------|------|------------|
| [阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) | 可演示产品 | PDF 高亮为加分验收 |
| [阶段 5](ENTERPRISE_RAG_ROADMAP.md#阶段-5生产化) | Langfuse + Docker | 在 04 项目扩展 |

---

## 附录 F：F2 前端系列与后端合龙表

| 后端 | 前端 | 数据契约 |
|------|------|----------|
| [156 FastAPI 结构](156.fastapi-project-structure-tutorial.md) | [171 列表](171.chat-message-list-ui-tutorial（front-end）.md) | messages[] |
| [116 SSE](116.sse-rag-streaming-tutorial.md) | [174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) | delta/citations |
| [167 OpenAI 封装](167.openai-api-wrapper-tutorial.md) | [175 中断](175.abort-controller-stream-tutorial（front-end）.md) | disconnect |
| 检索 metadata | [176 卡片](176.citation-card-ui-tutorial（front-end）.md) | citations |
| [115 导航](115.source-document-navigation-tutorial.md) | [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md) | preview-url |
| [52 page](52.metadata-source-page-tutorial.md) | 本篇 | page+highlight |

---

## 附录 G：145～195 学习路径回顾

```text
D 框架 145-154 → E 评测 155-171 → F1 后端 172-187 → F2 前端 188-195
```

本篇为 **F2 收官**，下一阶段 **196 上传 UI** 进入管理台。

---

## 附录 H：全栈面试 10 问

1. 阶段 4 验收标准？  
2. citations 何时下发？  
3. Abort 如何传到后端？  
4. signed URL 为何需要？  
5. PDF 无 text layer 怎么办？  
6. 行内与卡片如何编号一致？  
7. 多租户预览如何隔离？  
8. 流式为何用 fetch 非 EventSource？  
9. 代码高亮为何延迟？  
10. 下一步 196 做什么？

---

## 附录 I：项目目录建议

```
projects/04-fullstack-assistant/
  frontend/src/components/rag/
    TypewriterMessage.tsx    # 174
    CitationCard.tsx         # 176
    PreviewSidebar.tsx       # 177
    PdfPreview.tsx           # 178
  backend/app/api/rag.py     # 116
```

与路线图项目结构一致，便于评审 clone 即跑。

---

## 附录 J：致谢与继续学习

走完 190～195，你已具备 **企业知识库助手** 的前端溯源闭环。请打开 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md)，勾选 F2 清单，推进 **阶段 4 里程碑项目**。祝全栈交付顺利。
'''

EXPANSIONS = {
    "173.code-highlight-rag-tutorial（front-end）.md": EXPANSION_173,
    "174.streaming-typewriter-ui-tutorial（front-end）.md": EXPANSION_174,
    "175.abort-controller-stream-tutorial（front-end）.md": EXPANSION_175,
    "176.citation-card-ui-tutorial（front-end）.md": EXPANSION_176,
    "177.source-preview-sidebar-tutorial（front-end）.md": EXPANSION_177,
    "178.pdf-highlight-locate-tutorial（front-end）.md": EXPANSION_178,
}
