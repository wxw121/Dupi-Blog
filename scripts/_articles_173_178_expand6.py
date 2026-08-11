# -*- coding: utf-8 -*-
"""Expand6: final top-up sections (~600+ hanzi each)."""

E6 = {
    "173.code-highlight-rag-tutorial（front-end）.md": r'''
## 附录 Y：读者问答集锦（代码高亮）

**问：markdown 里既有代码又有表格，高亮会影响表格吗？**  
答：不会。高亮仅作用于 `code` 节点；表格走 [172 GFM](172.markdown-render-rag-tutorial（front-end）.md) 另一分支。注意表格单元格内行内 code 仍走行内样式。

**问：能否让用户切换高亮主题？**  
答：可以，在设置里切换 `hljs` 主题 CSS，与全局暗色模式联动。企业版可默认锁定品牌主题。

**问：代码块行号与 [115 页码](115.source-document-navigation-tutorial.md) 会混淆吗？**  
答：UI 上代码行号与 PDF 页码使用不同文案（「Ln」vs「第 n 页」），避免审计误解。

**问：本篇在阶段 4 是否必须？**  
答：了解档，非硬性；但技术类知识库强烈建议，否则 Demo 质量落后于竞品。

**问：下一步读什么？**  
答：[174 流式打字机](174.streaming-typewriter-ui-tutorial（front-end）.md) 让代码答案「流出来」，done 后再应用本篇高亮策略。
''',
    "174.streaming-typewriter-ui-tutorial（front-end）.md": r'''
## 附录 AD：读者问答集锦（流式打字机）

**问：能否用 CSS `animation` 假打字？**  
答：不推荐。真 delta 驱动才能与 [116](116.sse-rag-streaming-tutorial.md) 同步；假动画会在 citations 到达时不同步。

**问：检索很慢时要不要 fake 打字？**  
答：不要。检索阶段诚实 spinner；fake 打字误导用户以为已在生成。

**问：Vue 能实现吗？**  
答：可以。`useRagStream` 逻辑可迁 `composable`，模板用 `ref` 累积 content。路线图推荐 React/Next，见 [技术栈表](ENTERPRISE_RAG_ROADMAP.md#推荐技术栈)。

**问：与 OpenAI 官方 ChatUI 差异？**  
答：多 retrieving 态、citations 收尾、RAG 特有事件解析。

**问：下一步？**  
答：[175 中断](175.abort-controller-stream-tutorial（front-end）.md) 让用户能停；[176 卡片](176.citation-card-ui-tutorial（front-end）.md) 展示依据。
''',
    "175.abort-controller-stream-tutorial（front-end）.md": r'''
## 附录 AC：读者问答集锦（AbortController）

**问：iOS Safari abort 可靠吗？**  
答：现代 iOS 支持 fetch abort；仍需真机测后台挂起场景。

**问：停止后要不要自动重问？**  
答：产品选择。默认不自动，避免烧额度。

**问：能否用 RxJS 代替？**  
答：可以 `takeUntil(abort$)`，本质相同。

**问：后端 FastAPI 同步 def 路由？**  
答：流式应用 async；同步难以检测 disconnect。

**问：下一步？**  
答：[176 引用卡片](176.citation-card-ui-tutorial（front-end）.md)；可选 [117 WebSocket](117.websocket-rag-streaming-tutorial.md) 深潜。
''',
    "176.citation-card-ui-tutorial（front-end）.md": r'''
## 附录 AC：读者问答集锦（引用卡片）

**问：卡片能否横向滑动 Carousel？**  
答：移动端可以，注意与滚动冲突；桌面建议竖向列表。

**问：要显示检索 score 吗？**  
答：可选。B2B 技术用户喜欢分数；HR 场景可隐藏避免困惑。

**问：模型没写 [1] 但有卡片？**  
答：不应出现。cards 与行内应同源 citations 事件；若不一致修 prompt 或后处理。

**问：卡片缩略图必须吗？**  
答：非必须，加分项。

**问：下一步？**  
答：[177 侧栏预览](177.source-preview-sidebar-tutorial（front-end）.md) 点开原文。
''',
    "177.source-preview-sidebar-tutorial（front-end）.md": r'''
## 附录 AC：读者问答集锦（侧栏预览）

**问：能否三栏（对话+预览+目录）？**  
答：阶段 4 不建议。复杂度高，双栏足够。

**问：预览能否批注？**  
答：非 MVP。需另做协作功能。

**问：HTML 来源 XSS？**  
答：iframe sandbox + CSP；仅信任内网域。

**问：侧栏占满屏？**  
答：移动 Sheet 可 70vh；桌面最大 50% 宽。

**问：下一步？**  
答：[178 PDF 高亮](178.pdf-highlight-locate-tutorial（front-end）.md) 精确定位句段。
''',
    "178.pdf-highlight-locate-tutorial（front-end）.md": r'''
## 附录 AC：读者问答集锦（PDF 高亮 · 系列收官）

**问：没有 PDF 只有 Word？**  
答：预览走 Office 在线或转 PDF 入库；本篇聚焦 PDF.js 路线。

**问：高亮不准怎么办？**  
答：诚实降级仅跳页；长期加 bbox 或 OCR。

**问：145～195 学完够找工作吗？**  
答：够搭简历项目；还需阶段 4 Demo 与面试 storytelling。见 [阶段 6](ENTERPRISE_RAG_ROADMAP.md#阶段-6进阶与面试)。

**问：196 以后学什么？**  
答：上传 UI、索引进度、检索调试台、管理看板——同 F2 续。

**问：全栈闭环一句话？**  
答：「上传文档，流式问答，点引用，PDF 页内见高亮」——这就是 [阶段 4 全栈产品](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 的灵魂。恭喜完成 F2 溯源系列。
''',
}
