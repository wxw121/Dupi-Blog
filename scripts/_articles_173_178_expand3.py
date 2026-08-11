# -*- coding: utf-8 -*-
"""Third expansion block — topic-specific FAQ deep dives."""

from _articles_173_178_expand2 import EXPAND2

MORE = {
    "173.code-highlight-rag-tutorial（front-end）.md": r'''
## 附录 S：逐语言 registerLanguage 清单建议

PoC 阶段至少注册：`python`、`bash`、`yaml`、`json`、`sql`、`typescript`、`markdown`（文档内嵌 md 时）、`text` 兜底。每增加一种语言，在 bundle analyzer 中确认 gzip 增量；超过 200KB 考虑动态 `import()` 语言包。与 [172](172.markdown-render-rag-tutorial（front-end）.md) 共用的 `MarkdownAnswer` 组件应导出 `SUPPORTED_LANGS` 常量供 CMS 或运营文档引用。

## 附录 T：代码块内联与块级边界回归

行内 `` `not code` `` 不应触发 hljs 整块背景；块级才用 `<pre>`。回归用例：一句话里三个反引号、四反引号嵌套、表格单元格内代码。任何升级 `react-markdown` 大版本后跑一遍 Storybook 快照。

## 附录 U：与 [110 Prompt](110.rag-prompt-template-tutorial.md) 协同

在 system 中增加：「若输出代码，必须使用围栏并标注语言，如 \`\`\`python」。比前端猜测语言稳定一个数量级。Bad case 归因见 [152 胡编](152.bad-case-hallucination-tutorial.md)——代码块若与 chunk 不一致，先查生成而非高亮。
''',
    "174.streaming-typewriter-ui-tutorial（front-end）.md": r'''
## 附录 X：多模型路由下的流式一致性

[185 多模型路由](168.multi-model-routing-tutorial.md) 切换供应商时，delta 粒度可能变（有的一次一字，有的一次一句）。前端 rAF 合并策略应 **与粒度解耦**，始终按帧 flush。在 UI 角落可展示「由 xxx 模型生成」增强信任，字段来自 `done` 事件扩展。

## 附录 Y：会话恢复与断线重连

SSE 自动重连会重复部分事件——若不做 `event id` 去重，可能 duplicate 文本。企业 RAG POST 流一般 **不重连** 同一答案，而是提示失败让用户点重试；与 [7 SSE](7.sse-tutorial.md) 的 GET 重连语义区分。若必须重连，后端应支持 `Last-Event-ID` 并从断点续传 delta（复杂，阶段 5 再考虑）。

## 附录 Z：与 [118 多轮历史](118.multi-turn-history-tutorial.md) 的 UI 契约

每轮 assistant 消息独立 `messageId` 与 `stream phase`；历史消息永远是 `done` 态，不再打字机。新轮 `ask` 时滚动到底部但不影响用户正在阅读的历史轮。列表虚拟化时，确保进行中的那条消息 **始终挂载** 在 DOM，避免 Hook 丢失。
''',
    "175.abort-controller-stream-tutorial（front-end）.md": r'''
## 附录 W：停止按钮的权限与配额

[186 速率限制](169.rate-limiting-api-tutorial.md) 下，频繁 abort 仍算一次 ask 配额与否，应在产品条款定义。技术上每次 abort 仍可能产生检索成本——若检索已完成，abort 只能省生成。可在 UI 提示：「停止将保留已检索到的上下文，下次提问将重新检索。」

## 附录 X：Service Worker 与 PWA

PWA 缓存不应缓存 `text/event-stream` 响应。`fetch` abort 在 SW 介入时行为因浏览器而异——企业内网 PWA 场景需在 SW 中 bypass 流式 API 路径。

## 附录 Y：与 [117 WebSocket](117.websocket-rag-streaming-tutorial.md) cancel 帧字段

若双栈并存，定义统一 `client.stop(stream_id)` 语义：HTTP 侧 `abort()`，WS 侧 `{"type":"cancel","stream_id"}`。`stream_id` 由服务端在首个事件返回，前端保存至 ref，停止时带上。
''',
    "176.citation-card-ui-tutorial（front-end）.md": r'''
## 附录 W：卡片排序与业务规则

法务类文档可加权 `doc_type=policy` 卡片置顶；仍保持行内 `[n]` 与模型一致，仅 **卡片列表顺序** 可重排并标注「已按相关性排序」。切勿修改 `index` 字段本身。

## 附录 X：无 navigate_url 的诚实展示

[115](115.source-document-navigation-tutorial.md) 元数据缺失时，卡片仍展示 excerpt，但主按钮变「仅查看摘要」，侧栏不打开空 PDF。页码字段隐藏，勿显示「第 ? 页」。

## 附录 Y：与 [114 脚注](114.footnote-citation-tutorial.md) 样式共存

长答案底部可同时有脚注区与卡片列表：脚注供打印，卡片供交互。CSS 上脚注用小号上标，卡片用卡片阴影，层次分清。
''',
    "177.source-preview-sidebar-tutorial（front-end）.md": r'''
## 附录 W：打印与导出侧栏内容

用户可能想打印「答案+原文」。打印 CSS `@media print` 隐藏聊天输入框，展开侧栏内容到正文下方，PDF 预览转静态截图或分页链接——完整 PDF 打印仍建议浏览器原生打印预览区。

## 附录 X：并发打开多个引用

默认 **单例侧栏** 只显示当前 citation；若产品要「固定对比两篇」，可升级为多 tab 预览，复杂度显著上升，阶段 4 不建议首版就做。

## 附录 Y：审计：谁看了哪页

预览 API 记 audit log：`user_id, chunk_id, page, action=preview`。对接企业 [213 审计日志](ENTERPRISE_RAG_ROADMAP.md) 方向，满足等保问询。
''',
    "178.pdf-highlight-locate-tutorial（front-end）.md": r'''
## 附录 W：PDF 密码保护文档

加密 PDF 需密码才能渲染 text layer——预览 API 应返回 `code=ENCRYPTED_PDF`，侧栏提示联系管理员，勿无限 spinner。

## 附录 X：横向与纵向混合排版

部分扫描件纠偏后页宽高比异常，跳页仍正确但高亮框偏移——bbox 路线优于纯文本搜索。入库阶段用 [37 layout](37.pdf-layout-tables-tutorial.md) 记录旋转角。

## 附录 Y：收官：从 190 到 195 的能力拼图

| 能力 | 用户感知 |
|------|----------|
| 190 代码高亮 | 技术答案可读 |
| 191 打字机 | AI 在回答 |
| 192 中断 | 我能掌控 |
| 193 引用卡片 | 依据透明 |
| 194 侧栏 | 左问右证 |
| 195 PDF 高亮 | 可审计闭环 |

六篇叠加，完成 [阶段 4 全栈产品](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 面向业务方的 **信任感** 交付。下一步用 `projects/04-fullstack-assistant/` 把拼图焊成可点击的 Demo，并在阶段 5 补上 Langfuse 与 Docker，让系统可运维、可迭代。
''',
}

# merge into EXPAND2 for import side
EXPAND2_MERGED = {k: EXPAND2.get(k, "") + "\n\n" + MORE.get(k, "") for k in set(EXPAND2) | set(MORE)}
