# -*- coding: utf-8 -*-
"""Second expansion: unique dense content per tutorial (no repetition)."""

E173 = r'''
## 附录 P：hljs 主题定制与 Design Token 对齐

企业品牌色常要求代码块与控制台其他区域一致。hljs 通过 CSS 覆盖 `.hljs-keyword`、`.hljs-string` 等类即可，无需 fork 库。建议把颜色写入 Tailwind `@layer components`：

```css
@layer components {
  .hljs { background: hsl(var(--muted)); color: hsl(var(--foreground)); }
  .hljs-keyword { color: hsl(var(--primary)); }
  .hljs-string { color: hsl(142 76% 36%); }
}
```

切换暗色模式时，hljs 样式随 `data-theme` 自动变换，避免 [174 流式](174.streaming-typewriter-ui-tutorial（front-end）.md) 完成瞬间「闪白」。若使用 shiki，则选与品牌接近的 TextMate 主题 JSON，或让设计导出 token 后映射到 shiki `customTheme`。

**评审要点**：对比度至少 WCAG AA；注释与背景区分度；链接色勿与字符串色混淆。色盲同事抽检红绿字符串是否可辨。

---

## 附录 Q：与知识库文档类型的关系

| 知识库类型 | 代码块占比 | 本篇优先级 |
|------------|------------|------------|
| 研发 Runbook | 高 | 必做 |
| HR 政策 | 低 | 可选 |
| 销售话术 | 极低 | 跳过 |
| 混合 FAQ | 中 | 建议做 |

在 [阶段 4 产品](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 立项时，用内容抽样估算代码块比例，决定是否在首版 sprint 接入 CodeBlock。

---

## 附录 R：流式围栏闭合检测算法草图

```typescript
function isFenceClosed(md: string): boolean {
  const ticks = md.match(/```/g);
  return ticks != null && ticks.length % 2 === 0;
}
```

`streaming && !isFenceClosed(content)` 时用 `<pre className="text-muted">` 无高亮；一旦闭合可在下一帧 hljs，仍建议等到 `done` 统一渲染 Markdown 以避免列表与代码块交叉解析错误。
'''

E174 = r'''
## 附录 U：首字节时间与感知性能

用户容忍度研究显示：**有反馈的等待** 比 **无反馈的空白** 更短。除 retrieving spinner 外，可在检索完成后、首 delta 前插入 100ms 以内的「正在组织答案…」过渡，避免检索结束到首字之间的微空白被误判为卡顿。记录 `performance.mark`：

```typescript
performance.mark("rag-ask-start");
// 首 delta
performance.mark("rag-first-delta");
performance.measure("ttft", "rag-ask-start", "rag-first-delta");
```

将 `ttft` 与 `retrieve_ms` 上报到 [148 Langfuse](148.langfuse-observability-tutorial.md)，与后端 trace 对齐，便于判断瓶颈在检索还是生成。

---

## 附录 V：ReadableStream 与 EventSource 迁移对照表

团队若从 OpenAI 官方 SDK 前端示例迁到 [116](116.sse-rag-streaming-tutorial.md) 契约，建议增加 **BFF 适配层**，统一输出四类事件，前端只保留一套 `useRagStream`。适配层负责：解析 `choices[0].delta.content`、在流末从 header 或 side channel 附 citations、映射 `finish_reason` 到 done 事件。这样 [176 引用卡片](176.citation-card-ui-tutorial（front-end）.md) 组件不因供应商切换而重写。

---

## 附录 W：打字机「节奏感」产品参数

部分产品希望略慢于模型以营造「思考感」。若必须 artificial delay，建议 **上限 30ms/字符** 且总延迟不超过 2s，否则违背流式初衷。更好的做法是用 retrieving 文案与骨架屏填充等待，而非拖慢真实 delta。
'''

E175 = r'''
## 附录 T：取消语义的 HTTP 与业务两层

**HTTP 层**：`abort()` 关闭 TCP，服务端 `is_disconnected`。  
**业务层**：后端应停止向 LLM 供应商发送或读取后续 chunk，并标记 `finish_reason=aborted`。  
两层都成功才算「真停」。仅 HTTP 断开但 worker 仍消费上游流，成本照计。OpenAI 兼容 API 在循环中 `break` 通常足够；自托管 vLLM 可能需显式 `cancel` 请求 ID。

---

## 附录 U：与 Celery 长任务的区别

[159 Celery](159.celery-async-queue-tutorial.md) 索引任务取消用 `revoke`；生成长连接取消用 disconnect。勿混用同一套「任务 ID」——流式 `stream_id` 生命周期秒级，索引 task_id 分钟级。

---

## 附录 V：合规场景下的 partial 答案

金融/医疗场景，aborted 答案可能含 **不完整建议**。UI 应在 aborted 态显示横幅：「生成已中断，以下内容可能不完整，请勿作为唯一决策依据。」是否允许用户一键「继续生成」由合规决定；技术实现为新 `ask` 携带 `partial_context` 字段，后端拼入 prompt，非恢复旧流。
'''

E176 = r'''
## 附录 T：卡片信息密度与折叠策略

当 citations 超过 5 条，默认展示前 3 张 +「展开全部 (n)」链接，避免手机端把答案顶出视口。展开后仍保持 `chunk_id` 稳定 key。折叠状态仅存组件 local state，勿写入 URL，除非产品要做「分享带引用展开态」深度链接。

---

## 附录 U：与 RAGAS Faithfulness 演示

给投资人演示时，可并排：**左** 带 [1] 的短答，**右** 卡片 excerpt 与 PDF 高亮（[178](178.pdf-highlight-locate-tutorial（front-end）.md)）同屏，直观展示 [141 Faithfulness](141.ragas-faithfulness-tutorial.md) 所追求的「答案绑证据」。这比讲指标更打动非技术干系人。

---

## 附录 V：国际化卡片字段

`title` 可能来自英文 PDF 文件名；`excerpt` 可能中英混排。UI 用 `dir="auto"` 包裹摘录段落，避免 RTL/LTR 混排错乱。页码标签「第 n 页」走 i18n。
'''

E177 = r'''
## 附录 T：双栏与可访问性：焦点陷阱

侧栏打开时，焦点应移入侧栏第一个可聚焦元素；关闭时焦点回到触发引用的链接。使用 `FocusTrap`（如 radix Dialog 内置）防止 Tab 键掉进「看不见」的聊天区。Esc 关闭侧栏为标配，见附录 D 快捷键表。

---

## 附录 U：对象存储 Range 请求与 PDF 大文件

预览 50MB+ PDF 时，signed URL 应允许 **HTTP Range**，PDF.js 才能按需拉页而非整文件下载。S3/MinIO 配置 `Accept-Ranges`；CDN 勿缓存错误的全文件响应。首屏只请求 `page` 对应 range，降低 [178](178.pdf-highlight-locate-tutorial（front-end）.md) 跳页等待。

---

## 附录 V：wiki iframe 与 SSO

内网 wiki iframe 预览常遇 **X-Frame-Options: DENY**。降级策略：卡片点击改 `window.open(navigate_url)` 新标签，侧栏显示「该来源仅支持新窗口打开」说明，而非空白 iframe。与 [115 navigate_url](115.source-document-navigation-tutorial.md) 策略字段 `open_mode: tab|sidebar` 可扩展。
'''

E178 = r'''
## 附录 T：阶段 4 全栈里程碑演讲提纲（8 分钟）

1. **问题**（1min）：企业知识库需要可审计溯源。  
2. **链路**（2min）：上传→索引→检索→[116 SSE](116.sse-rag-streaming-tutorial.md)→[174 打字机](174.streaming-typewriter-ui-tutorial（front-end）.md)。  
3. **Grounding**（2min）：[113 行内](113.inline-citation-tutorial.md)+[176 卡片](176.citation-card-ui-tutorial（front-end）.md)。  
4. **溯源闭环**（2min）：[177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md)+本篇 PDF 高亮。  
5. **验收**（1min）：对照 [ENTERPRISE_RAG_ROADMAP 阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 勾选演示。

---

## 附录 U：从教程到简历项目描述

简历可写：「独立交付企业知识库助手（阶段 4），实现 SSE 流式问答、AbortController 中断、引用卡片与 PDF.js 页内高亮；多租户 JWT + 检索前 ACL；评测接入 RAGAS。」附 GitHub / 演示视频链接。面试官追问时，用本篇 §11 验收表逐条回应。

---

## 附录 V：196+ 管理台预告

完成 F2 溯源后，[路线图 196](ENTERPRISE_RAG_ROADMAP.md) 起进入 **上传界面、索引进度、检索调试台**——后端能力在 F1 已铺垫（[157 上传](157.file-upload-multipart-tutorial.md)、[161 状态机](161.index-task-state-machine-tutorial.md)），前端管理台把运维与业务人员纳入同一产品，形成真正 **可运营** 的知识库 SaaS。
'''

EXPAND2 = {
    "173.code-highlight-rag-tutorial（front-end）.md": E173,
    "174.streaming-typewriter-ui-tutorial（front-end）.md": E174,
    "175.abort-controller-stream-tutorial（front-end）.md": E175,
    "176.citation-card-ui-tutorial（front-end）.md": E176,
    "177.source-preview-sidebar-tutorial（front-end）.md": E177,
    "178.pdf-highlight-locate-tutorial（front-end）.md": E178,
}
