# -*- coding: utf-8 -*-
"""Final expansion to reach >=5000 hanzi without generic repetition."""

FINAL = {
    "173.code-highlight-rag-tutorial（front-end）.md": r'''
## 附录 V：企业落地周会演示脚本（代码高亮专项）

**对象**：研发 + 运维 + 产品  
**时长**：15 分钟  

1. 展示无高亮灰框答案，让运维找 `apiVersion`（故意困难）。  
2. 刷新页面，启用本篇 CodeBlock，同一答案关键字分色，复制进终端一次成功。  
3. 打开 DevTools Network，演示流式 done 后高亮不阻塞 delta（与 [174](174.streaming-typewriter-ui-tutorial（front-end）.md) 联调视频）。  
4. 展示 sanitize：构造含 `<script>` 的恶意围栏被剥离，hljs 仍正常。  
5. Q&A：hljs vs shiki 选型表（§4）发 wiki。

**会后产出**：在 `04-fullstack-assistant` 提 PR 接入 `MarkdownAnswer`；检查单附录 B 指派负责人每周抽检。

---

## 附录 W：与竞品 Demo 对齐清单

| 竞品能力 | 本篇覆盖 | 备注 |
|----------|----------|------|
| ChatGPT 代码着色 | ✅ | done 后高亮 |
| 一键复制 | ✅ | 纯文本 |
| 流式代码不闪 | ✅ | 延迟策略 |
| IDE 运行 | ❌ | 非范围 |

路演时诚实说明边界，避免现场被问「能不能跑代码」翻车。
''',
    "174.streaming-typewriter-ui-tutorial（front-end）.md": r'''
## 附录 AA：流式 UI 故障演练（Game Day）

每月一次前端 Game Day，模拟四种故障：  
（1）后端 30s 无 delta——UI 应超时 error；  
（2）citations 事件丢失——行内 [1] 保持不可点并 Sentry 告警；  
（3）delta 乱码 UTF-8 截断——解析器不崩溃，显示可恢复错误；  
（4）用户极速连点发送——仅最后一次生效，旧流 abort。  

记录 MTTR 与复盘 issue，纳入 [144 回归集](144.regression-test-set-tutorial.md)。

---

## 附录 AB：与 SpeakEasy 阶段 0 项目的关系

[阶段 0](ENTERPRISE_RAG_ROADMAP.md#阶段-0基础补齐) 的 `projects/00-llm-streaming/` 已练过纯 LLM 流式；本篇在其上叠加 **RAG 三态**（检索/生成/引用）与 citations 契约。建议把阶段 0 的 `useStream` 重命名为 `useLlmStream`，新建 `useRagStream` 避免语义混淆。
''',
    "175.abort-controller-stream-tutorial（front-end）.md": r'''
## 附录 Z：中断功能的产品文案与埋点

| 埋点 | 字段 |
|------|------|
| rag_stop_click | session_id, stream_id, elapsed_ms, partial_chars |
| rag_stop_success | backend_disconnected: bool |

产品看板：停止率 = stop / ask。停止率异常高可能说明答案太长或检索不准，应联动 [151 检索遗漏](151.bad-case-retrieval-miss-tutorial.md) 分析，而非只优化按钮颜色。

---

## 附录 AA：法务与客服培训要点

客服需知：用户停止后 **已显示文字仍可能不完整**，不可截图作为最终政策解释。系统应提供「重新生成完整答案」按钮，走新请求。培训幻灯片链接本篇 §9 partial 保留策略与 [112 拒答](112.refusal-strategy-tutorial.md) 区分。
''',
    "176.citation-card-ui-tutorial（front-end）.md": r'''
## 附录 Z：引用卡片视觉规范（供设计稿）

- 卡片最小高度 72px，最大高度 120px（含摘录）。  
- 索引 `[n]` 使用等宽字体，与正文 [n] 颜色 token 一致。  
- hover 阴影 elevation-1，active 边框 2px primary。  
- 无权状态 opacity 0.45，cursor not-allowed。  

设计交付 Figma 组件名：`CitationCard / Default / Disabled / Active`，开发直接映射 §6 组件 variant。

---

## 附录 AA：A/B 实验想法

[153 A/B](153.ab-experiment-rag-tutorial.md) 可测：仅行内 vs 行内+卡片 对 **用户点击率、停留时长、faithfulness 人工分** 的影响。假设：卡片提升点击率但移动端增加滚动——用数据决策默认折叠策略。
''',
    "177.source-preview-sidebar-tutorial（front-end）.md": r'''
## 附录 Z：侧栏宽度与用户偏好持久化

`localStorage` 存 `previewWidthPercent`，下次访问恢复。注意 GDPR：仅偏好、不含 PII。拖曳释放时 debounce 500ms 写入。

---

## 附录 AA：与知识库版本的联动

[48 文档版本](48.doc-versioning-tutorial.md) 变更后，旧 `chunk_id` 可能指向旧 PDF。预览 API 应返回 `doc_version`，侧栏 header 显示「员工手册 v3」；若用户书签旧链接，提示「文档已更新」并提供跳转最新版 navigate_url。
''',
    "178.pdf-highlight-locate-tutorial（front-end）.md": r'''
## 附录 Z：阶段 4 全栈产品 —— 从路线图到可售卖 Demo

[ENTERPRISE_RAG_ROADMAP 阶段 4](ENTERPRISE_RAG_ROADMAP.md#阶段-4全栈产品) 不是再写一篇教程，而是交付 **`projects/04-fullstack-assistant/`**：

**必须演示的业务流**  
① 租户管理员上传 PDF → ② 后台 Celery 索引（[159](159.celery-async-queue-tutorial.md)）→ ③ 员工登录问政策 → ④ [174](174.streaming-typewriter-ui-tutorial（front-end）.md) 流式答案 → ⑤ 点 [176](176.citation-card-ui-tutorial（front-end）.md) 卡片 → ⑥ [177](177.source-preview-sidebar-tutorial（front-end）.md) 侧栏打开 → ⑦ 本篇 PDF 跳页高亮。

**多用户隔离**：租户 A 的引用打不开的文档，租户 B 不可见（[166](166.tenant-isolation-backend-tutorial.md)、[121](121.unauthorized-doc-filter-tutorial.md)）。

**简历一句话**：「全栈 RAG 知识库助手，覆盖 ingest 到 PDF 溯源 UI，阶段 4 验收通过。」

**之后**：阶段 5 加 Langfuse trace、Docker Compose（路线图 202–203）；阶段 6 选做 Graph RAG 模块讲故事。

---

## 附录 AA：190～195 系列思维导图（文字版）

```text
                    [阶段4 全栈产品]
                           |
        +------------------+------------------+
        |                  |                  |
    对话壳 171          渲染 172           流式 174-175
        |                  |                  |
        +--------+---------+---------+--------+
                 |                   |
            高亮 173              引用 176
                 |                   |
                 +--------+----------+
                          |
                    侧栏 177 → PDF 178
```

至此，F2 前端 **溯源体验** 闭环完成；196 起补 **管理台与运营**，让产品从 Demo 走向内部上线。
''',
}
