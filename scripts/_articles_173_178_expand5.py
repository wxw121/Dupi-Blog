# -*- coding: utf-8 -*-
"""Expand5: large unique closing sections per article."""

E5 = {
    "173.code-highlight-rag-tutorial（front-end）.md": r'''
## 附录 X：从开发到上线的代码高亮检查（完整走读）

**第 1 周：PoC**  
在现有 [172 Markdown](172.markdown-render-rag-tutorial（front-end）.md) 分支上新建 `feature/code-highlight`。安装 `highlight.js` 核心包与 `github-dark` 样式。实现 §9 `CodeBlock`，Storybook 故事涵盖 python/bash/yaml/json 四栏。与设计师确认暗色背景下字符串与注释对比度。合并门槛：Lighthouse 性能分下降不超过 3 分。

**第 2 周：集成**  
接入 [171 助手消息](171.chat-message-list-ui-tutorial（front-end）.md) 气泡。确认 `rehype-sanitize` 白名单包含 `span` 的 `class` 属性（hljs 依赖）。编写单元测试：给定 Markdown 输入，快照 html 结构，防止升级破坏。与 [174 流式](174.streaming-typewriter-ui-tutorial（front-end）.md) 联调：streaming 态灰底，done 态高亮。

**第 3 周：安全与合规**  
邀请安全同事 review [16 XSS](16.markdown-rendering-security-tutorial（front-end）.md) 路径。构造 OWASP 向量：围栏内 script、onerror img、javascript: 链接。全部应被 sanitize 或转义。确认复制按钮不写日志中的密钥（若代码块含 token，走 [122 打码](122.content-safety-filter-tutorial.md)）。

**第 4 周：上线与观测**  
灰度 10% 用户，监控 `hljs_error` 率（语言不支持）、首屏 JS 体积、复制按钮点击率。编写运维 runbook：如何切换 shiki、如何回滚 hljs。在 [ENTERPRISE_RAG_ROADMAP](ENTERPRISE_RAG_ROADMAP.md) F2 清单勾选第 190 项。

**常见问答复盘**：  
问：为何不用 Monaco？答：体积与 RAG 只读场景不符。  
问：能否运行代码？答：不在本篇范围，需沙箱项目。  
问：打印偏色？答：切换打印 CSS 浅色 hljs 主题。
''',
    "174.streaming-typewriter-ui-tutorial（front-end）.md": r'''
## 附录 AC：流式打字机上线四周计划

**Week1 协议对齐**  
前后端共读 [116 SSE RAG](116.sse-rag-streaming-tutorial.md)，冻结 `message/citations/done/error` JSON。用 curl 录屏保存 golden 流文件，前端写解析单测不必连真后端。

**Week2 Hook 与 UI**  
落地 §6 `useRagStream` 与 §9 `TypewriterMessage`。实现 retrieving/streaming/done 三态。rAF 合并 delta。禁止 done 前可点 citations。

**Week3 边缘场景**  
长答案内存测试；弱网 throttle；StrictMode 双 mount abort；与 [175 停止](175.abort-controller-stream-tutorial（front-end）.md) 联调。Nginx `proxy_buffering off` 在预发验证。

**Week4 指标与路演**  
上报 TTFT、retrieve_ms、stream_duration。准备阶段 4 路演脚本：问年假 → 检索 spinner → 打字机 → 卡片。路线图第 191 项勾选。

**与路线图第 22 条对齐说明**：  
A 模块第 22 条要求「逐字显示与中断」——本篇完成逐字，[175](175.abort-controller-stream-tutorial（front-end）.md) 完成中断，二者合起来满足阶段 0/4 对流式 UI 的验收表述。
''',
    "175.abort-controller-stream-tutorial（front-end）.md": r'''
## 附录 AB：中断能力生产就绪清单（逐项签字）

1. 前端每次 `ask` 新建 `AbortController`（开发负责人签字）。  
2. `stop()` 调用 `abort()` 且 catch `AbortError` 不报 Sentry（前端签字）。  
3. 后端 `StreamingResponse` 循环检测 `is_disconnected`（后端签字）。  
4. OpenAI/兼容 SDK 循环可 break（后端签字）。  
5. aborted 保留 partial 文案（产品确认）。  
6. 无 citations 时不可点 [n]（前端签字）。  
7. 压测 stop 率 10% 时 GPU 利用率下降（运维签字）。  
8. 文档/wiki 链接本篇与 [117 WS](117.websocket-rag-streaming-tutorial.md) 选型（架构签字）。

**回归用例**：Playwright 问句 → 等待 1s → 点停止 → 断言 Network canceled → 断言气泡仍含 partial 文本 → 断言 phase=aborted。

**未做事项（明确 out of scope）**：跨设备续传同一流、WS cancel 帧（除非已选 [117](117.websocket-rag-streaming-tutorial.md)）、Celery revoke 混用。
''',
    "176.citation-card-ui-tutorial（front-end）.md": r'''
## 附录 AB：引用卡片从 Mock 到生产的字段演进

**V0 Mock**（前端独自开发）：`{ index, title, excerpt }` 写死在 Storybook。  
**V1 联调**（接 [116 citations](116.sse-rag-streaming-tutorial.md)）：补 `chunk_id`、`page`、`navigate_url`。  
**V2 权限**（接 [121 ACL](121.unauthorized-doc-filter-tutorial.md)）：补 `allowed`。  
**V3 评测**（接 [141 Faithfulness](141.ragas-faithfulness-tutorial.md)）：日志记录卡片曝光与点击，供人工抽检 excerpt 是否.support 行内句子。

**UI 回归矩阵**：0 条 citations、1 条、5 条、超长 excerpt、无权、缺 page、缺 navigate_url 各一例。

**与 [113 行内](113.inline-citation-tutorial.md) 联调会议议程**：确认 index 从 1 开始；确认模型未编造 [99]；确认 done 后卡片与行内同时可点。

**路线图 193 主线验收**：业务方能在移动端点卡片打开 [177 侧栏](177.source-preview-sidebar-tutorial（front-end）.md)，无需读 chunk JSON。
''',
    "177.source-preview-sidebar-tutorial（front-end）.md": r'''
## 附录 AB：侧栏预览跨职能交付手册

**后端**（2d）：实现 `GET /api/citations/{chunk_id}/preview-url`，返回 signed URL + mime + expires_at；403 走 [121](121.unauthorized-doc-filter-tutorial.md)。  
**前端**（3d）：`ChatWithPreviewLayout` + `PreviewSidebar` 状态机 + 懒加载 PDF 模块。  
**设计**（1d）：双栏比例、Sheet 移动态、错误插画。  
**QA**（2d）：PDF/MD/HTML 各两文档；过期 URL；无权；大文件 range。  
**法务**（0.5d）：确认预览 audit log 保留天数。

**与 [115 navigate_url](115.source-document-navigation-tutorial.md) 分工**：navigate 可以是前端路由；preview-url 负责鉴权后的字节访问。不要在前端拼永久 S3 路径。

**阶段 4 演示彩排**：台词强调「左问右证」——这是与通用聊天机器人差异化的 **Grounding 卖点**。彩排时关闭侧栏再打开，测 `key={chunk_id}` 无残留。

**路线图 194 勾选**：侧栏可在预发环境由 PM 独立验收，无需等 PDF 高亮（178）完成，但完整溯源需 178。
''',
    "178.pdf-highlight-locate-tutorial（front-end）.md": r'''
## 附录 AB：PDF 高亮与阶段 4 全栈 —— 实施手册

**目标**：在 `projects/04-fullstack-assistant/` 实现「点引用 → 侧栏 PDF 第 n 页 → 句段高亮」，满足 [ENTERPRISE_RAG_ROADMAP 阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 的「看引用」顶配体验。

**依赖 metadata**（入库团队负责，见 [52 page](52.metadata-source-page-tutorial.md)）：每个 chunk 至少 `page`；推荐存 `excerpt` 前 120 字用于搜索。高级团队入库 `bbox` 归一化坐标（[42 PyMuPDF](42.pymupdf-tutorial.md)）。

**前端任务拆分**：  
（1）`PdfPreview` 跳页；（2）TextLayer 启用；（3）`highlightText` 搜索或 bbox overlay；（4）扫描件降级文案；（5）接入 [177](177.source-preview-sidebar-tutorial（front-end）.md)。

**后端**：无额外 API 亦可，预览仍用 signed URL；可选提供 `GET /chunks/{id}/anchors` 返回 bbox。

**验收录像脚本（5min）**：上传 handbook.pdf → 索引完成 → 问「年假」→ 流式答案 → 点 [1] → 侧栏第 12 页黄标「年假 10 天」→ 切换租户验证隔离。

**系列收官陈述**：路线图 **190～195** 构成 F2 前端 **对话与溯源** 完整链条；**145～195** 批量教程覆盖框架、评测、API 与 UI。你已不再需要「更多概念」，而是需要 **把 04 项目跑通并录制 Demo**。下一阶段 **196 上传 UI**、**197 索引进度** 补运营闭环；**阶段 5** 补 Langfuse 与 Docker。祝你在全栈 RAG 工程师路上交付顺利。
''',
}
