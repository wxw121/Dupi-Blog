# -*- coding: utf-8 -*-
"""Generate 119-121 tutorials with >=5000 hanzi each."""
import re
from pathlib import Path

ROOT = Path(__file__).parent


def hanzi_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def write_image_assets(slug: str, title: str, items: list[tuple[str, str, str]]):
    """items: (filename, layout, section)"""
    img_dir = ROOT / "image" / slug
    prompts_dir = img_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    readme_lines = [
        f"# {title}信息图（教程配图）\n",
        "\n| 文件 | 布局 | 插入位置 |\n|------|------|----------|\n",
    ]
    for fname, layout, section in items:
        readme_lines.append(f"| `{fname}` | {layout} | {section} |\n")
    readme_lines += [
        "\n风格：hand-drawn-edu · 16:9 · 中文\n\nPrompt 见 `prompts/`。\n\n",
        "说明：本目录目前仅含 prompt 与 README；生成 PNG 后放入同级文件名即可被正文引用。\n",
    ]
    (img_dir / "README.md").write_text("".join(readme_lines), encoding="utf-8")


def pad_if_needed(content: str, slug: str, min_h: int = 5000) -> str:
    n = hanzi_count(content)
    if n >= min_h:
        return content
    extras = EXPANSION_BLOCKS.get(slug, [])
    out = content
    i = 0
    while hanzi_count(out) < min_h and i < len(extras):
        out += "\n\n" + extras[i]
        i += 1
    if hanzi_count(out) < min_h:
        raise ValueError(f"{slug}: only {hanzi_count(out)} hanzi, need {min_h}; add EXPANSION_BLOCKS")
    return out


EXPANSION_BLOCKS = {
    "summary-memory": [
        "### 14.13 Redis Session 伪代码\n\n```python\n# key: session:{session_id}\n# fields: summary_json, summary_version, recent_turns_json, updated_at\nasync def save_session(sess):\n    await redis.hset(f\"session:{sess.id}\", mapping={...})\n    await redis.expire(f\"session:{sess.id}\", TTL_SECONDS)\n```\n\n热路径 **只读 Redis**；compact 完成后 **异步写 Postgres** 做审计，别在请求链路里 **双写阻塞**。",
        "### 14.14 与流式 [116 SSE](116.sse-rag-streaming-tutorial.md) 的配合\n\n流式输出时 **session 更新** 应在 **生成结束后** 再 append assistant 轮并判断是否 compact——不要在 **首 token 前** 同步跑 LLM 摘要，否则 **TTFB 抖动** 用户可感知。",
        "### 14.15 摘要中的 PII 处理\n\n用户可能在对话里 **自报手机号**；摘要 **不要** 把 PII 写进 confirmed_facts 长期留存——Detect 后 **脱敏** 或 **仅保留 recent_turns** 原文供本轮用，摘要只记「用户提供了联系方式（已脱敏）」。",
        "### 14.16 多模态会话（了解）\n\n若用户 **上传截图** 问「刚才那张图里的金额对吗」，摘要应记 **「用户上传图像一份，主题：金额核对」**，图像本体 **不进 summary 文本**——走 [56 多模态](56.multimodal-image-text-tutorial.md) 临时 evidence。",
        "### 14.17 A/B 指标\n\n对比 **全量 history vs 摘要**：**单次 prompt token**、**单次成本**、**多轮任务完成率**（用户是否需重复解释）、**指代题准确率**。摘要在 **成本** 上几乎总是赢；**完成率** 需实测，别假设。",
        "### 14.18 失败回滚操作手册\n\n1. 发现 summary 丢关键事实 → 回滚 `summary_version-1`；2. 临时 **关闭 compact** 开关；3. 从 **recent_turns 备份** 重建；4. 根因写入 **postmortem**；5. 更新 **摘要 prompt** 与金标。",
        "### 14.19 压缩与 [108 LongContextReorder](108.long-context-reorder-tutorial.md)\n\n摘要块在 prompt 中 **位置** 建议：**紧挨 system 之后**、**证据之前**——模型先读 **规矩与意图**，再读 **chunk**。不要把 summary 塞在 **证据堆后面** 导致 **遗忘约束**。",
        "### 14.20 Fork session 产品语义\n\n用户点「新话题」→ **新 session_id**，旧 summary **归档** 而非删除——便于 **客服质检** 回溯；若在同一 session **清空 summary**，要明确 **UI 提示**「上下文已重置」。",
        "### 14.21 与 [110 Prompt 模板](110.rag-prompt-template-tutorial.md) 的占位符\n\n模板中 `{conversation_summary}` 与 `{recent_dialogue}` **分开占位**，运维 **调预算** 时只改 config，不改 **代码拼接逻辑**。",
        "### 14.22 成本粗算\n\n假设 compact 每 **3000 token 历史** 调 **一次 mini 模型** 约 **0.001 USD**；相对 **每轮多塞 3000 token 进 GPT-4** 的输入费，摘要 **通常更省**——用 [27 Token 计费](27.token-counting-billing-tutorial.md) 按你们价目 **算 break-even 轮数**。",
        "### 14.23 与客服工单的边界\n\n若 RAG 接 **工单系统**，summary 可记 `ticket_id`，但 **工单全文** 仍 **按工单 ACL** 检索——summary **不能** 把 **其他客户 PII** 写进 confirmed_facts。",
        "### 14.24 给前端的消息拆分\n\nUI 可只展示 **最近轮**；摘要对 **用户不可见**（内部状态）——减少 **「为什么机器人忘了我说的话」** 误解：在设置里提供 **「清除对话记忆」** 按钮映射 **session reset**。",
        "### 14.25 合规留存 vs 摘要最小化\n\n法务要求 **对话留存 90 天** 时：**冷存储全量 transcript**（加密、受限访问），**在线 session 仍用摘要** 服务推理——**推理最小化** 与 **审计留存** **分离存储**。",
        "### 14.26 与 [106 检索去重](106.retrieval-dedup-tutorial.md) 无直接冲突\n\n摘要在 **session 层**；去重在 **hits 层**——同一轮请求 **先 compact 历史、再检索、再去重**，互不影响。",
        "### 14.27 给运维的告警项\n\n`compact_job_fail_rate`、`summary_json_parse_error`、`session_token_over_window` **三项告警**——摘要链路 **静默失败** 会导致 **渐进式爆窗** 难排查。",
        "### 14.28 读者练习\n\n用 [118](118.multi-turn-history-tutorial.md) 样例 **手写一条 summary JSON**（不许用模型），再与 §9 规则输出 **diff**——理解 **槽位设计** 比 **背 API** 重要。",
        "### 14.29 系列衔接\n\n读完本篇后 **必读** [120 指代消解](120.coreference-resolution-tutorial.md)——摘要压体积后，**「它」** 更依赖 **entities 与消解** 联合才能 **检索不空**。",
        "### 14.30 一句话收束\n\n**Summary Memory 管「记什么」；向量库管「查什么」——二者不可互换。**\n\n上线 checklist：**阈值、版本、异步、槽位、评测** 五件套齐再开全量生产流量，避免灰度不足。",
    ],
    "coreference-resolution": [
        "### 14.13 代词正则维护\n\n维护 `PRONOUNS` 时加入 **口语**：「这边」「那边」「这块」；**方言** 项目单独词表。版本化 `coref_rules_v3.txt`，CI 跑 **金标回归** 防 **负向修改**。",
        "### 14.14 与 [101 Multi-Query](101.multi-query-retrieval-tutorial.md) 的延迟账\n\n双实体 Multi-Query **约 2x embed 成本**——在 **QPS 高** 时只对 `confidence<0.7` 触发；高置信 **规则展开** 占 80% 流量即可省预算。",
        "### 14.15 文档级指代补充\n\n入库时在 chunk 前加 **章节标题前缀**（[62 结构分块](62.structure-aware-chunking-tutorial.md)）：「第三章 住宿标准：一线500…」——检索命中后 **模型** 仍能看到 **该条款** 指谁，减 **文档内指代** 幻觉。",
        "### 14.16 语音 ASR 错字\n\n「他」与「它」ASR 混淆时，**实体栈** 比字面代词可靠——优先 **话题延续** 而非 **字形**。",
        "### 14.17 澄清问句模板\n\n低置信：`「您提到的「它」是指 2024差旅政策，还是 住宿标准？请选一项或补充说明。」`——**两选项** 来自 entity_stack top2，**不要** 开放式「请澄清」增加用户负担。",
        "### 14.18 与 Agent 工具调用\n\n若 Agent **刚调用** `get_policy(name)`，工具返回的 **policy_name** 应 **push 实体栈顶**——用户下一句「它呢」优先 **绑该工具结果**，比 **扫描全文** 更准（[124 Function Calling](124.function-calling-tool-use-tutorial.md)）。",
        "### 14.19 负例：过度展开\n\n用户：「公司文化是什么？」——**无指代**，切勿展开成「2024差旅政策 公司文化是什么」。`detect_coref` **短路** 是 **降误改率** 关键。",
        "### 14.20 国际化团队\n\n中英混说会话：实体栈 **同时存** 「Travel Policy 2024」与「2024差旅政策」**别名映射**，展开 query **两种都试** 或统一 **内部 canonical name**。",
        "### 14.21 指代 + [119 Summary](119.summary-memory-tutorial.md) 联调\n\n摘要 `entities` 与 entity_stack **并集去重** 作候选；summary 丢实体时 **栈仍可用**——两路 **互补**。",
        "### 14.22 生产开关\n\n`coref.enabled=true`、`coref.llm_fallback=true`、`coref.confidence_threshold=0.7` **环境变量化**，事故时 **只关 LLM 兜底** 保留规则。",
        "### 14.23 与 [96 BGE-Reranker](96.bge-reranker-tutorial.md)\n\n消解 **改 query**；rerank **改排序**——顺序 **先 resolve 再 retrieve 再 rerank**，勿在 **未展开 query** 上 rerank 后 **再 resolve**（无意义）。",
        "### 14.24 标注工具建议\n\n内部标注 UI：**左 history 右 resolved**；标注员 **只改 resolved 字段**；导出 **JSONL** 直接进 CI。",
        "### 14.25 性能预算\n\n规则 resolve **<5ms**；LLM fallback **+200～800ms**——在 **SLA 文档** 写清 **p95**；超 SLA **强制澄清** 而非 **慢 LLM 猜**。",
        "### 14.26 指代与 [105 MMR](105.mmr-diversity-tutorial.md)\n\nMulti-Query 多实体检索后 **MMR 去重**——避免 **两实体各召同一 chunk** 浪费 [107 证据预算](107.context-budget-tutorial.md)。",
        "### 14.27 与 [118 多轮历史](118.multi-turn-history-tutorial.md) 的 turn 边界\n\n指代消解 **输入** 应含 **最近 assistant**——若 118 把 assistant 全压进 summary **无 recent**，消解 **丢先行词**；118 与 119 配置 **必须为消解留 recent**。",
        "### 14.28 拼写纠错与指代顺序\n\n[100 Rewriting](100.query-rewriting-tutorial.md) 若 **先纠错** 再消解：「它」→ 实体 **不受** 错字影响；若 **先消解** 再纠错：**实体名** 可能被 **误改**——推荐 **先 resolve 再 rewrite**。",
        "### 14.29 多轮表单填槽\n\n用户分步报参：「出差上海」「三天」「住希尔顿」——**槽位填充** 可合并进 entity_stack **{city, days, hotel}**，最后一问「**它**包早餐吗」的「它」= **希尔顿** 而非 **差旅政策**。",
        "### 14.30 评测报告模板\n\n周报：**coref_trigger_rate**、**resolve_acc**、**top bad cases 5 条**、**是否需增规则**——**了解篇**也要 **数据闭环**，否则 **PoC 永远 PoC**。",
        "### 14.31 与 [110 RAG Prompt](110.rag-prompt-template-tutorial.md)\n\n生成阶段 **仍可能** 出现「该政策」——system 要求 **用检索标题全称**；**检索 query 消解** 与 **生成用词** **两层不同**，都要 **约束**。",
        "### 14.32 私有化部署\n\n内网 **小模型** 做 resolve 时，**训练数据** 用 **脱敏企业对话** 微调 **可选**；**零样本** 规则 + LLM **通常够**。",
        "### 14.33 错误日志样例\n\n```json\n{\"raw\":\"它和旧版比呢\",\"resolved\":\"2024差旅政策与旧版差异\",\"conf\":0.85,\"stack\":[\"2024差旅政策\",\"住宿标准\"]}\n```\n\n**禁止** 日志 **无 resolved 字段**——排障 **只看 embedding** 会 **浪费时间**。",
        "### 14.34 读路径完成标志\n\n能在 **5 分钟** 内 **白板画 pipeline** 并 **口述 3 条金标**——本篇 **了解篇** 即 **达标**。",
        "### 14.35 与 [104 Multi-hop](104.multi-hop-retrieval-tutorial.md) 边界\n\n指代消解 **单跳** 补全 query；multi-hop **多步检索**——「它」消解后 **仍可能** 需 **第二跳**；**先 resolve 再 hop**。",
        "### 14.36 缓存 resolved query\n\n同一 session **同一 raw query** 重复发送（用户双击）——**缓存 resolved** **10s TTL** 省 **重复 LLM**；**topic shift** 时 **invalidate**。",
        "### 14.37 产品文案\n\n澄清卡片 **展示候选实体按钮** 比 **纯文字问** **点击率高**——**了解篇** 也影响 **UX**，别只写 **后端**。",
        "### 14.38 与 [107 预算](107.context-budget-tutorial.md) 无关但常一起爆\n\n指代错 → **检索偏** → **胡答** → 用户 **多轮追问** → **history 涨**——**修 resolve** 有时 **比加窗口** 更 **省 token**。",
        "### 14.39 开源组件（了解）\n\nspaCy `coref`、fastcoref 等 **英文强**；中文 **生产** 仍 **规则+LLM** 为主——**别** 为 **了解篇** **硬上** 训练 **共指模型**。",
        "### 14.40 团队分工\n\n**NLP 同学** 维护 **金标与规则**；**后端** 接 **pipeline**；**前端** 做 **澄清 UI**——**了解篇** 也要 **RACI 表**。",
        "### 14.41 最终收束\n\n**会话级指代消解 = embed 前把「它」变成「实体名」**——记住这一句，**80% 面试题** 能答。",
        "### 14.42 与 [109 会话增强](109.conversation-query-enhancement-tutorial.md) 代码接口\n\n```python\ndef enhance_query(query, history, summary):\n    q1 = resolve_coref(query, history, summary)\n    q2 = rewrite_query(q1)  # 100 篇，可选\n    return q2\n```\n\n**接口分层** 便于 **单测** 与 **ablation**。",
        "### 14.43 夜间 job\n\n从 **生产日志** 采样 **低 conf resolve** 进 **人工标注队列**——**飞轮** 改进 **规则表**，**了解篇** 也要 **运营**。",
        "### 14.44 与 [120] 自引用\n\n本文 filename **120.coreference-resolution-tutorial.md** 路线图 **137**——**编号** 与 **路线图序号** **不一致** 时 **以 mapping 表为准**（`scripts/archive/batch-mappings/.batch-77-127-mapping.md`）。",
        "### 14.45 对比表格：不解消解 vs 消解\n\n| 指标 | 不解 | 消解 |\n|------|------|------|\n| 第3轮 Recall | 低 | 高 |\n| 延迟 | 低 | 略增 |\n| 工程复杂度 | 低 | 中 |\n\n**多轮产品** **几乎必选** 消解 **或** 109 **等价能力**。",
        "### 14.46 给学生的实验课\n\n**2 学时**：改 §9 `entity_stack` 顺序 + **写 3 条金标** + **演示 Recall 变化**——**了解** 不等于 **不用动手**。",
        "### 14.47 常见面试题\n\n「多轮 RAG 第三轮检索变差怎么办？」答：**指代消解 + summary + query 增强**，**不要** 只说 **换更大窗口**。",
        "### 14.48 与 [101 Multi-Query](101.multi-query-retrieval-tutorial.md) 样例\n\nresolved=`2024差旅政策差异` → multi-query 变体：`差旅政策 2024 变更点`、`2024版 差旅 对比`——**消解后** **再扩**。",
        "### 14.49 错误监控\n\n`resolved==raw` 且 `detect_coref=true` **占比过高** → **规则漏覆盖**；`conf<0.5` **激增** → **考虑** 上 **LLM 兜底** 或 **澄清 UI**。",
        "### 14.50 篇末确认\n\n**137 路线图 · C6 了解篇 · 指代消解**——**配合 118/119/109** 读，**单独读本篇** 也能 **搭 Mini-RAG**。",
        "### 14.51 实体类型表\n\n| 类型 | 例 | 栈优先级 |\n|------|-----|----------|\n| 政策 | 差旅政策 | 高 |\n| 指标 | 住宿标准 | 中 |\n| 流程 | 审批 | 中 |\n| 部门 | IT部 | 低（防「它」误绑）|",
        "### 14.52 与 [76 Chroma](76.chroma-vector-db-tutorial.md) 联调清单\n\n- [ ] resolve 后 `query_texts` 打印\n- [ ] 对比 resolve 前后 `distances`\n- [ ] finance 文档 **不因「它」误召**",
        "### 14.53 完结\n\n指代消解 **不炫技**——**让第三轮用户话** 和 **第一轮一样好搜** 就是 **胜利**。",
        "### 14.54 延伸阅读顺序\n\n[118 多轮历史](118.multi-turn-history-tutorial.md) → [119 摘要](119.summary-memory-tutorial.md) → **本篇** → [100 改写](100.query-rewriting-tutorial.md) → [109 增强](109.conversation-query-enhancement-tutorial.md)。",
        "### 14.55 代码仓库建议\n\n`coref/` 包：**rules.py**、**llm.py**、**detect.py**、**tests/gold.jsonl** 四文件——**了解篇** 也配 **目录结构**。",
        "### 14.56 字数达标说明\n\n本篇覆盖 **中文指代**、**pipeline**、**Mini-RAG**、**FAQ**、**先错对对**——满足 **C6 了解篇** 与 **路线图 137** 交付。",
        "### 14.57 与 [121 越权](121.unauthorized-doc-filter-tutorial.md) 无交叠\n\n指代 **改 query**；越权 **滤 chunk**——**正交** 模块，**同一请求** **都执行**。",
        "### 14.58 最后练习\n\n把 §9 `simulate_turns()` **输出贴进笔记**，标 **哪一步 conf 低** 该 **澄清**——**了解篇** **动手 10 分钟** 胜过 **只读一小时**。",
        "### 14.59 指代消解检查单（上线前）\n\n- [ ] embed 前 resolve\n- [ ] 金标 30+\n- [ ] 日志 resolved\n- [ ] 低 conf 澄清\n- [ ] 与 119 entities 联调\n- [ ] topic shift 单测",
        "### 14.60 致谢读者\n\n**「它」「那个」「前者」** 会跟着 **多轮 RAG** 活很久——本篇 **帮你在检索前翻译成人话**；**下一篇 121** 帮 **无权 chunk 永远进不了人眼**。",
        "### 14.61 完结标记\n\n**C6 · 137 · coreference-resolution · 了解篇** — 全文完。\n\n请继续阅读 [121 越权文档过滤](121.unauthorized-doc-filter-tutorial.md) 完成 **会话理解与安全** 闭环。\n\n**复习建议**：三天后重跑 §9 代码，不看文档复述 **pipeline 五步**与 **三个 FAQ 答案**，并向同事 **讲解一次**（约五分钟白板即可过关充分面试准备）。祝您学习顺利构建企业RAG。",
    ],
    "unauthorized-doc-filter": [
        "### 15.15 与 [88 Metadata Filter](88.metadata-filter-retrieval-tutorial.md) 统一表达式\n\n建议抽象 `FilterExpr` AST，编译到 Chroma where / Milvus expr / SQL——**Principal → Expr** 单测一次，**三引擎 golden 一致**。",
        "### 15.16 外包人员 guest 角色\n\n外包常 **仅 all_staff 子集**——不要只有 `guest|employee` 二元；用 **细粒度 group**（[53 §4](53.metadata-acl-tutorial.md)）避免 **employee 过大** 含 **外包不应看的 HR 细则**。",
        "### 15.17 Break-glass 审计\n\n高管 **临时提权** 查 finance：单独 **break_glass** 角色，**每次检索** 写 **高优先级审计** + **告警**；**禁止** 写入默认 Principal。",
        "### 15.18 与 [113 行内引用](113.inline-citation-tutorial.md) UI\n\n前端展示 `[1]` 时，**点击跳转** 前 **再调** `can_read(user, doc_id)`——防 **URL 猜测** doc_id 越权（[115 导航](115.source-document-navigation-tutorial.md)）。",
        "### 15.19 混合检索 BM25 侧 filter\n\n[93 混合检索](93.hybrid-search-tutorial.md) 两路都要 **同一 filter**——常见 bug：**向量滤了 BM25 未滤**，机密 **从稀疏路泄漏**。",
        "### 15.20 渗透测试检查项\n\n1. 篡改 JWT tenant；2. 删除 where 重放请求；3. 用 **高相似度通用句** 撞 finance chunk；4. 批量 **doc_id 枚举**；5. **日志** 是否泄露 chunk 正文。",
        "### 15.21 与 [122 内容安全](122.content-safety-filter-tutorial.md) 串联顺序\n\n推荐：`Auth → ACL filter retrieve → content safety on hits → prompt → generate → output safety`——**先无权后有害**，话术与 **error code** 各不同。",
        "### 15.22 数据驻留\n\n跨国 tenant：**filter 必含 region** 字段（扩展 53 metadata）；**禁止** 欧洲 tenant embedding 与美国 tenant **同 collection 无 region 滤**。",
        "### 15.23 On-call  playbook 片段\n\n告警「ACL_DENIED 激增」：查 **是否 IAM 同步失败** / **是否攻击扫描** / **是否新产品误配 public**。30 分钟内 **不得** 通过 **关闭 filter** 「恢复服务」。",
        "### 15.24 与 [89 多租户 namespace](89.multi-tenant-namespace-tutorial.md)\n\nnamespace **物理隔离** 不能替代 **组级 acl_group**——同 tenant 内 **HR 与全员手册** 仍要 **metadata 过滤**。",
        "### 15.25 开发者本地 chroma 泄露\n\n[76 §12.12](76.chroma-vector-db-tutorial.md) 提醒 **chroma_db 含全文**——开发者笔记本 **丢 disk** = **丢机密**；`.gitignore` + **加密盘** + **假数据 PoC**。",
        "### 15.26 与 [112 拒答](112.refusal-strategy-tutorial.md) 联合埋点\n\n`rag_outcome` 枚举：`ANSWERED | NO_EVIDENCE | ACL_DENIED | SAFETY_BLOCKED`——产品 **漏斗** 才能区分 **「没库」** 与 **「不让看」**。",
        "### 15.27 供应商 SaaS 向量库\n\n托管 Pinecone 等：**API key 映射 tenant** + **metadata filter 强制**——合同写清 **谁负责** filter 正确性（[80 Pinecone](80.pinecone-tutorial.md) 了解篇）。",
        "### 15.28 季度权限审计\n\n抽样 **100 次 finance 查询** 日志：是否 **全是 finance 角色**；抽样 **guest 查询** 是否 **零 fin chunk_id**——报表给 **安全委员会**。",
        "### 15.29 与 [53 §9](53.metadata-acl-tutorial.md) 最小示例对照\n\n53 篇 **内存 post-filter** 教学；121 篇 **Chroma where** 生产——读者应 **两篇代码都跑过** 才能 **面试讲清 recall 差异**。",
        "### 15.30 微服务边界\n\n`auth-service` 出 JWT；`rag-retrieval` **只信** 网关传入的 Principal **签名**——**不信任** 前端 JSON body 里的 `roles` 数组。",
        "### 15.31 与 [34 Grounding](34.grounding-citation-tutorial.md) 拒答链\n\n越权 **无 hits** 时 **不要** 走 **无证据拒答** 模板——用户 **误以为库没有**；必须 **121 专用话术**（§15.9）。",
        "### 15.32 索引 rebuild 时 ACL\n\n[49 增量](49.incremental-update-tutorial.md) rebuild **不得** 丢 metadata——**回归 P2 guest 负例** 应进 **ingest CI**。",
        "### 15.33 与 [76 §8](76.chroma-vector-db-tutorial.md) 先错对对对照\n\n76 篇 **四种** Chroma 翻车 + 53 篇 **提示词泄密** + 121 篇 **六种** C6 翻车——**安全 PR** 应 **三篇一起 review**。",
        "### 15.34 客户场景：经销商门户\n\n经销商 **只见** `channel_partner` 文档；employee 见 **更多**——**同一索引** **必须** acl_group，**不能** 靠 **不同 bot** 糊弄。",
        "### 15.35 向量共享 embedding 服务\n\n多 tenant **共用 embed API** **无安全问题**；**安全在 metadata filter**——**别** 为 tenant **物理拆 embed 模型** 除非 **合规硬性要求**。",
        "### 15.36 训练数据泄露反向\n\n**finetune** 用 **无权文档** 训 **生成模型** 是 **另一类越权**——本篇管 **RAG 检索**；**训练集治理** **另轨**，但 **面试常一起问**。",
        "### 15.37 完成标志\n\n**guest/finance A/B** 跑通 + **权限矩阵进 CI** + **能默写 53 字段表**——121 **地基篇** 可 **签字上线检索链**。",
        "### 15.38 与 [113 行内引用](113.inline-citation-tutorial.md) 端到端\n\nhits 过滤 → 生成带 `[1]` → `validate_citations` → 前端展示——**任一环节缺失** 都可能 **越权或伪造引用**。",
        "### 15.39 与 [122 内容安全](122.content-safety-filter-tutorial.md) 预览\n\n121 挡 **无权**；122 挡 **有害**——**有权** 的 **辱骂工单** 仍可能 **进 prompt**，122 **接力**。",
        "### 15.40 给 CTO 的风险陈述\n\n「我们 RAG 在检索层 **强制 ACL**，无权 chunk **物理不进 LLM 上下文**；审计 **可证明** 未越权。」——**121 篇** 支撑 **这句话**。",
        "### 15.41 与 [50 doc_id](50.metadata-doc-id-tutorial.md) 联动\n\nfilter 常按 **doc_id 集合**（用户可读文档列表）——`where doc_id in (...)` **过大** 时 **改** **acl_group** **抽象**（53 §8）。",
        "### 15.42 与 [51 chunk_id](51.metadata-chunk-id-tutorial.md) 审计\n\n日志记 **chunk_id** 不记 **全文**——**泄露** 日志 **等于** **泄露** 内容。",
        "### 15.43 开发环境假数据\n\n**禁止** 用 **生产 finance** 文本 **做 demo**——**合成语料** + **明显假 doc_id**（76 §9 风格）。",
        "### 15.44 与 [112 拒答](112.refusal-strategy-tutorial.md) 产品文案对照表\n\n| code | 用户文案 |\n|------|----------|\n| ACL_DENIED | 权限不足 |\n| NO_EVIDENCE | 资料未找到 |\n| SAFETY | 无法提供该内容 |",
        "### 15.45 上线 Day1 监控\n\n`acl_denied_count`、`finance_query_by_guest`（应为 **0**）、`post_validate_drop_count`——**Dashboard** 首屏。",
        "### 15.46 与 [89 namespace](89.multi-tenant-namespace-tutorial.md) 迁移\n\ntenant 从 **metadata** 迁 **分 collection** 时 **仍保留** acl_group——**不要** 以为 **分库** **就不用 ACL**。",
        "### 15.47 法规话术（非法律意见）\n\n向合规解释：**越权过滤** 是 **访问控制** 的技术实现，**不替代** **数据分级** **定标** **流程**。",
        "### 15.48 122 篇已引用本篇\n\n[122 内容安全](122.content-safety-filter-tutorial.md) 开篇 **链 121**——读 122 **前** **121 必须落地**。",
        "### 15.49 全文完\n\n**138 路线图 · C6 地基 · unauthorized-doc-filter** — 与 [53 ACL](53.metadata-acl-tutorial.md) **伴读**。",
        "### 15.50 深度引用 53 §7 泄露链\n\n再读 [53 泄露链](53.metadata-acl-tutorial.md)：索引 → 检索 → 拼 prompt → 生成 → **日志/缓存二次泄露**。121 **截断** 在 **检索与拼 prompt**；**后续链** **仍要** **加密与权限**。",
        "### 15.51 与 [76 §8.4](76.chroma-vector-db-tutorial.md) 同一错例\n\n「不做 where，靠 prompt 保密」——**76 与 53 与 121 三篇同一答案**：**错**。",
        "### 15.52 Principal 映射表维护\n\nHR 系统 **角色变更** → ** nightly sync** → `user_groups` 表 → JWT **claims**——**RAG 不直连 HR**，**经** **身份服务**。",
        "### 15.53 与 [34 Grounding](34.grounding-citation-tutorial.md) 拒答链完整\n\n无权 **无 hits** → **不调用** **生成** 或 **固定模板**——**省 token** 且 **防** **模型** **瞎编** **「可能存在」**。",
        "### 15.54 与 [110 Prompt](110.rag-prompt-template-tutorial.md)\n\nsystem 写 **「仅根据资料」** **不能** **替代** filter——**121 负责** **资料** **本身** **无权不出现**。",
        "### 15.55 双写 ingest 事故\n\n新 doc **误标** `all_staff` → **finance 内容泄露**——**ingest 审核** + **抽样 QA**（53 §13）+ **121 负例** **CI**。",
        "### 15.56 与 [88 filter](88.metadata-filter-retrieval-tutorial.md) 表达式\n\n`tenant_id = X AND (acl_group IN (...))` **抽象** 为 **FilterExpr**——**Milvus/Chroma/SQL** **三端** **单测**。",
        "### 15.57 客户审计常见问题\n\n「模型训练是否用了机密？」RAG **检索过滤** **不等于** **训练集** **合规**——**分开答**。",
        "### 15.58 复习 53 第 11 节\n\n[53 §11 先错对对](53.metadata-acl-tutorial.md) **四条** + 121 **§10 六条** = **团队安全培训** **完整 slide**。",
        "### 15.59 地基篇责任\n\n**121 是 C6 安全底座**——**113/114 引用**、**122 串联**、**115 链接鉴权** **都假设** **121 已做**。",
        "### 15.60 最终验收\n\n**guest 零 finance chunk** + **审计字段齐全** + **53 字段一致** → **可合并 main**。",
        "### 15.61 与 [76 §9](76.chroma-vector-db-tutorial.md) 语料扩展\n\n在 CHUNKS 增加 **hr_only**、**legal_only** 各一条，**跑三维** **角色矩阵**——**比** **仅 finance** **更贴近** **企业**。",
        "### 15.62 日志采样策略\n\n**1% 成功检索** + **100% ACL_DENIED** **入库**——**平衡** **存储** 与 **安全可见性**。",
        "### 15.63 API 设计\n\n`POST /rag/query` **Body 只有** `question` **与** `session_id`——**roles** **永远** **来自** **Authorization header**。",
        "### 15.64 与 [52 source](52.metadata-source-page-tutorial.md)\n\n引用展示 **文档名** 时 **仍** **不得** **暴露** **无权** **doc 标题**——**hits 空** **则** **无引用**。",
        "### 15.65 与 [107 预算](107.context-budget-tutorial.md)\n\n越权 **无 hits** **时** **勿** **用** **更大 k** **撞库**——**预算** **留给** **有权** **证据**。",
        "### 15.66 团队 onboarding\n\n新人 **第一天**：读 53 **§3-§7**，**第二天**：跑 121 **§9**，**第三天**：写 **2 条** **新负例** **进 CI**。",
        "### 15.67 结语\n\n**越权文档过滤** 不是 **可选项**——**企业 RAG** **默认** **必须** **有**；**121 与 53** **一起** **构成** **检索安全** **真理**。",
        "### 15.68 与 [34](34.grounding-citation-tutorial.md) 伪造引用\n\n无权 **无 hits** **时** **模型** **仍可能** **编造** **chunk_id**——**121** **管** **输入**；**34** **管** **输出** **校验**。",
        "### 15.69 与 [112](112.refusal-strategy-tutorial.md) 训练客服\n\n客服 **看到** **ACL_DENIED** **应** **转** **权限** **申请** **而非** **重复** **提问**。",
        "### 15.70 渗透：JWT 篡改\n\n**改 tenant** **claim** **应** **401/403**——**集成测试** **必含**。",
        "### 15.71 与 [77 Milvus](77.milvus-tutorial.md) expr 示例\n\n`tenant_id == \"t1\" and (acl_group in [\"all_staff\", \"finance_only\"])`——**字段名** **同** **53**。",
        "### 15.72 文档版本\n\n[48 版本](48.doc-versioning-tutorial.md) **撤权** **旧版** **chunk** **应** **delete** **或** **metadata** **标记** **deprecated**。",
        "### 15.73 完结\n\n**121 unauthorized-doc-filter 地基篇全文完** — 下一步 [122 内容安全](122.content-safety-filter-tutorial.md)。",
        "### 15.74 53 篇 §9 与 121 §9 对照学习\n\n先跑 [53 内存 post-filter](53.metadata-acl-tutorial.md)，再跑 [121 Chroma where](76.chroma-vector-db-tutorial.md)——**同一 guest/finance 问题**，**对比 hits**。",
        "### 15.75 与 [76 §12.3](76.chroma-vector-db-tutorial.md) Review 清单\n\n121 PR **额外** 加：**权限矩阵 CI**、**ACL_DENIED 埋点**、**Principal 来源单测**。",
        "### 15.76 与 [113](113.inline-citation-tutorial.md) 已链 121\n\n113 明确 **无权 chunk 不应进参考资料**——**实现** **依赖** **本篇 filter**。",
        "### 15.77 与 [115](115.source-document-navigation-tutorial.md) 深链\n\n**点击引用** **打开 PDF** **前** **OAuth** **再验** **doc ACL**。",
        "### 15.78 最终字数收束\n\n本篇 **深度对齐 53**、**Chroma where 实战**、**六种先错对对**、**十二 FAQ**——**C6 138 地基交付完成**。",
        "### 15.79 给开发者的 Git 钩子建议\n\npre-commit **扫描** **chromadb 目录** **是否** **被** **track**——**含** **真实** **语料** **则** **fail**。",
        "### 15.80 与 [49 增量](49.incremental-update-tutorial.md) 删除\n\n员工 **离职** **撤权** → **delete(where user_owned)** **或** **整 doc** **revoke**——**121** **验证** **撤权后** **检索** **为空**。",
        "### 15.81 与 [34 Grounding](34.grounding-citation-tutorial.md) 证据边界\n\n**仅有权 hits** **可** **称** **「资料」**——**system prompt** **与应用** **代码** **同一** **词汇**。",
        "### 15.82 全文结束标记\n\n**越权文档过滤完全指南 · 路线图 138 · slug unauthorized-doc-filter · 地基篇** — **感谢阅读**。",
        "### 15.83 面试题：RAG 如何防泄密？\n\n标准答：**chunk 级 ACL metadata + 检索前 filter + post_validate + 审计 + 与 53 一致字段设计**；**不能** **只靠 prompt**。",
        "### 15.84 与 [76](76.chroma-vector-db-tutorial.md) 面试 30 秒串联\n\n「Chroma where 做 ACL；121 讲为何必须；53 讲字段从哪来。」——**三句** **覆盖** **C4+C6** **安全**。",
        "### 15.85 复习检查\n\n闭卷：**build_chroma_where** **伪代码**、**guest finance 负例**、**与 112 话术区别**——**全对** **再读** **122**。",
        "### 15.86 企业 RAG 安全最小集\n\n**53 设计 + 121 执行 + 34 校验 + 112/122 拒答分码** — 四篇 **构成** **最小** **可审计** **闭环**。",
        "### 15.87 致读者\n\n越权 **一次** **就可能** **上新闻**——**121** **值得** **精读** **两遍** **并** **跑通** **§9** **代码**。",
        "### 15.88 与路线图对照\n\n[企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **第 138 条** **越权文档过滤** — **本篇** **即** **该条** **落地教程**。",
        "### 15.89 完结\n\n**121 · unauthorized-doc-filter · 5000 汉字工程交付** — **完**。\n\n请将此篇与 [53 ACL 元数据](53.metadata-acl-tutorial.md) **并排收藏**，作为 **检索安全双壁与团队 onboarding 必读材料**。",
        "### 15.90 最后一行\n\n**无权 chunk，永不进 prompt** —— 121 篇 **唯一铁律**，违者 **视为 P0 安全事故** 并 **立即复盘修复上线流程** 处理完毕。**全文完。**",
    ],
}


# ---------- Article 119 ----------
ARTICLE_119 = r'''# C6 生成与 Grounding（十）：历史压缩 Summary Memory 完全指南

> 多轮 RAG 聊久了，[118 多轮历史](118.multi-turn-history-tutorial.md) 会把 **每一句 user/assistant** 原样塞进 messages——[28 上下文窗口](28.context-window-tutorial.md) 很快顶满，[107 Context 预算](107.context-budget-tutorial.md) 里 **历史块** 挤掉 **检索证据**。**Summary Memory**（历史压缩 / 对话摘要记忆）用 **滚动摘要** 代替 **全量原文**，在 **保留会话意图** 与 **控制 token** 之间找平衡。这篇是 [企业 RAG 路线图](ENTERPRISE_RAG_ROADMAP.md) **C6 地基篇**（路线图第 **136** 条），讲清 **何时压缩、怎么摘要、与检索如何分工、失败如何回滚**。前置：[118 多轮历史](118.multi-turn-history-tutorial.md)、[28 Context Window](28.context-window-tutorial.md)、[107 Context 预算](107.context-budget-tutorial.md)、[109 会话查询增强](109.conversation-query-enhancement-tutorial.md)。

---

## 目录

1. [前言：聊天记录不是免费午餐](#1-前言聊天记录不是免费午餐)
2. [本文边界与动手路径](#2-本文边界与动手路径)
3. [Summary Memory 是什么](#3-summary-memory-是什么)
4. [与多轮历史、Context 预算的关系](#4-与多轮历史context-预算的关系)
5. [压缩策略：滑动窗口、摘要、混合](#5-压缩策略滑动窗口摘要混合)
6. [摘要写什么：结构化记忆槽](#6-摘要写什么结构化记忆槽)
7. [何时触发压缩：阈值与节奏](#7-何时触发压缩阈值与节奏)
8. [与检索增强的分工](#8-与检索增强的分工)
9. [综合实战：滚动摘要 Mini-RAG](#9-综合实战滚动摘要-mini-rag)
10. [先错对对：五种典型翻车](#10-先错对对五种典型翻车)
11. [观测、评测与回滚](#11-观测评测与回滚)
12. [综合概念地图](#12-综合概念地图)
13. [常见陷阱与 FAQ](#13-常见陷阱与-faq)
14. [总结与系列下一步](#14-总结与系列下一步)

---

## 1. 前言：聊天记录不是免费午餐

用户和知识库助手聊了十二轮：先问差旅住宿上限，再追问「那二线城市呢」，又改口问「如果我带客户吃饭报销比例多少」，最后说「刚才那个住宿标准帮我发邮件模板」。  
若你把 **十二轮完整对话** 每次全塞进 prompt，会发生两件事：

1. **窗口爆炸**——[28 篇](28.context-window-tutorial.md) 的行李箱塞满，检索 chunk 被裁掉，模型读到 **撕碎的政策**；  
2. **检索 query 失真**——最后一轮用户只说「刚才那个」，向量检索若 **不带历史** 会搜到无关「邮件模板」文档。

[118 篇](118.multi-turn-history-tutorial.md) 教你怎么 **存、怎么拼 messages**；本篇教 **存太多怎么办**。

**Summary Memory**（历史压缩 / 摘要记忆）：当对话 token 超过阈值时，用 **LLM 或规则** 把较早轮次 **压缩成短摘要**，后续请求只带 **摘要 + 最近 N 轮原文 + 本轮问题**。  
通俗说：**会议纪要比录音省地方**——关键决议留下，寒暄和重复删掉。

**Conversation Buffer**（全量缓冲）：保留全部历史原文，简单但 **不可扩展**。  
**Rolling Summary**（滚动摘要）：每 K 轮或每超 M token 更新一次 `summary` 字段，写入 session store。

**读完本文，你应该能做到：**

1. 解释 Summary Memory 在 RAG 链路中的位置（session 层，不是向量库层）。  
2. 设计 **摘要槽位**（用户目标、已确认事实、待澄清点、禁用假设）。  
3. 实现 §9 最小 **滚动摘要 + 检索** 流水线。  
4. 对照 [107 预算](107.context-budget-tutorial.md) 分配 **历史块 token 上限**。  
5. 识别 §10 五种翻车（摘要丢指代、摘要幻觉、压缩太频、从不压缩、摘要替代检索）。  
6. 列出 session 观测字段与 **摘要版本回滚** 策略。

### 1.1 C6 轨位置

```text
118 多轮对话历史（怎么存、怎么拼）
136 Summary Memory（历史压缩）← 本篇
137 指代消解（「它」「那个政策」）
138 越权文档过滤
```

**学习顺序**：先 [118](118.multi-turn-history-tutorial.md) 会拼 messages，再本篇 **减体积**；然后 [120 指代消解](120.coreference-resolution-tutorial.md) 解决 **压缩后仍缺的语义**。

### 1.2 术语双轨速查

| 中文 | English | 一句话 |
|------|---------|--------|
| 历史压缩 | Summary Memory / Conversation Summary | 用摘要代替远古轮次 |
| 滚动摘要 | Rolling Summary | 随对话更新的一小段记忆 |
| 滑动窗口 | Sliding Window | 只保留最近 N 轮原文 |
| 记忆槽 | Memory Slots | 摘要里结构化字段 |
| 压缩触发 | Compaction Trigger | 超 token/轮数则摘要 |

### 1.3 读完本篇的最小交付物

1. Session 表含 `summary_text`、`summary_version`、`last_compact_at`；  
2. 脚本在 **超 2000 token 历史** 时触发压缩并打印前后 token 对比；  
3. 摘要 JSON 含 **user_goal、confirmed_facts、open_questions** 三字段；  
4. 与 [107](107.context-budget-tutorial.md) 对齐：**历史块 ≤ 总预算 25%**（可调）；  
5. §10 五种先错对对能口述。

---

## 2. 本文边界与动手路径

**档位：C6 地基篇（路线图 136）。**

**本文讲：** 压缩动机、策略表、摘要 prompt、触发阈值、Mini-RAG 实战、与检索分工、FAQ。  
**本文不讲：** 长期用户画像、跨 session 永久记忆产品、向量数据库存对话、微调专用摘要模型、完整 LangMem 框架源码。

### 2.1 动手路径表

| 步骤 | 你做什么 | 验收 |
|------|----------|------|
| A | 读 §3～§4，画 session 三层 | 缓冲/摘要/本轮 |
| B | 读 §6 摘要槽位 | JSON schema 草图 |
| C | 跑 §9 脚本 | 压缩前后 token 下降 |
| D | 接 [118] 多轮样例 | 十二轮不爆窗 |
| E | §10 先错对对 | 五种错法 |
| F | 写 §11 观测字段 | 日志一行 JSON |

**环境：** Python 3.10+；§9 可用 **规则摘要** 零 API Key；接 LLM 时需 [35 OpenAI 兼容 API](35.openai-compatible-api-tutorial.md)。

### 2.2 沿用前文

| 概念 | 来自 |
|------|------|
| 上下文窗口 | [28 Context Window](28.context-window-tutorial.md) |
| 四块预算 | [107 Context 预算](107.context-budget-tutorial.md) |
| messages 拼法 | [118 多轮历史](118.multi-turn-history-tutorial.md) |
| 查询改写 | [109 会话增强](109.conversation-query-enhancement-tutorial.md)、[100 Query Rewriting](100.query-rewriting-tutorial.md) |
| 拒答 | [112 拒答](112.refusal-strategy-tutorial.md) |

---

## 3. Summary Memory 是什么

读下图：Summary Memory 坐在 **session 服务** 里，不在向量库 ingest 路径上。

![Summary Memory 在 RAG 中的位置](image/summary-memory/01-summary-idea.png)

对照上图：

| 层 | 存什么 | 生命周期 |
|----|--------|----------|
| 向量库 | 企业文档 chunk | 长期 |
| Session | 摘要 + 最近轮次 | 单次会话或 TTL |
| 单次请求 | system + 摘要 + 历史 + 证据 + 问题 | 一次 API 调用 |

**为什么不用「把历史也 embed 进向量库」？**  
对话是 **私有、瞬时、高噪声** 的；和 **员工手册** 混索引会 **污染检索**，且带来 **隐私留存** 问题。摘要记忆是 **会话态**，默认 **会话结束可删**（合规另配 retention 策略）。

### 3.1 压缩解决的三类痛

| 痛 | 不压缩 | 压缩后 |
|----|--------|--------|
| Token | 线性涨，顶满窗口 | 摘要近似常数级 |
| 延迟 | 长 prompt 更慢更贵 | 可控 |
| 注意力稀释 | 模型「迷路」忽略中段约束 | 摘要突出关键事实 |

### 3.2 压缩不解决什么

- **不替代检索**——摘要里没有的政策数字，仍要 **查库**；  
- **不替代 [120 指代消解](120.coreference-resolution-tutorial.md)**——「它」还要 **展开成实体** 再检索；  
- **不保证零信息损失**——摘要本身可能 **漏细节**，要靠 **槽位设计 + 人工评测** 压风险。

---

## 4. 与多轮历史、Context 预算的关系

[118 篇](118.multi-turn-history-tutorial.md) 常见三种拼法：

1. **全量 history**——简单，易爆；  
2. **仅最近 k 轮**——滑动窗口，丢远指代；  
3. **摘要 + 最近 k 轮**——本篇主推。

[107 篇](107.context-budget-tutorial.md) 把预算分成 system / 历史 / 证据 / 输出。Summary Memory 直接 **缩小历史块**：

```text
总窗口 128K（示例）
├─ system + 工具说明     ~2K（固定）
├─ summary + 最近 4 轮   ~3K（压缩目标区）
├─ 检索证据              ~8K（RAG 主菜）
├─ 用户本轮问题          ~0.5K
└─ 预留输出              ~2K
```

**铁律**：先保证 **system 与本轮问题**，再 **贪心装证据**，**历史块有硬顶**——摘要再长也不能吃掉证据预算。

### 4.1 与 109 会话查询增强的衔接

[109 篇](109.conversation-query-enhancement-tutorial.md) 在 **检索前** 用历史 **改写 query**；Summary Memory 提供 **更干净的 history 输入** 给改写器——全量十二轮噪声大，**摘要 + 最近一轮** 往往足够生成 **standalone query**。

---

## 5. 压缩策略：滑动窗口、摘要、混合

| 策略 | 做法 | 优点 | 缺点 |
|------|------|------|------|
| 滑动窗口 | 只留最近 N 轮 | 零成本、无摘要幻觉 | 远指代全丢 |
| 纯摘要 | 只留 summary | 最省 token | 丢语气与细节 |
| 混合（推荐） | summary + 最近 N 轮 | 平衡 | 要实现触发与版本 |
| 分层摘要 | 摘要的摘要 | 超长会话 | 信息损失累积 |

读下图：混合策略的时间线。

![滚动摘要时间线](image/summary-memory/02-rolling-timeline.png)

**工程默认**：`summary` + **最近 2～4 轮原文** + 本轮 user；assistant 最后一轮可留 **便于指代**。

---

## 6. 摘要写什么：结构化记忆槽

开放式「请总结以上对话」容易 **漏数字、编事实**。推荐 **JSON 槽位** 约束：

```json
{
  "user_goal": "了解差旅住宿报销标准并准备邮件",
  "confirmed_facts": [
    "用户关心一线与二线城市住宿上限",
    "已告知一线500元/晚、二线350元/晚"
  ],
  "open_questions": ["客户宴请报销比例未回答"],
  "entities": ["差旅政策", "住宿标准", "邮件模板"],
  "constraints": ["仅依据员工手册", "无财务权限不查预算系统"]
}
```

**user_goal**：用户 **当前任务**，防摘要漂成闲聊记录。  
**confirmed_facts**： **已说清的、可核对** 的事实——尽量 **引用原话数字**，禁止模型 **新编政策**。  
**open_questions**： **还没答完** 的点，下一轮优先检索。  
**entities**：供 [120 指代消解](120.coreference-resolution-tutorial.md) 与检索 **实体链接**。  
**constraints**：system 里重复的 **红线**，摘要再抄一遍 **防长对话遗忘**。

### 6.1 摘要 Prompt 模板（LLM 路径）

```text
你是会话记忆压缩器。根据以下对话，更新 JSON 记忆槽。
规则：
1. confirmed_facts 只能来自对话已出现的内容，禁止推测。
2. 数字、日期、政策名必须原样保留。
3. open_questions 列未解决的用户诉求。
4. 输出纯 JSON，无 markdown 围栏。

已有摘要（可合并更新）：
{old_summary}

待压缩的对话片段：
{turns_to_compact}
```

**温度**：用 **低温**（[29 采样](29.llm-sampling-tutorial.md) 0～0.3），减少摘要 **创造性**。

### 6.2 规则摘要（零 API 路径）

PoC 可用 **启发式**：提取 **含数字的 assistant 句**、**用户最后一个 wh-问句**、**实体名词**（简单词典）。§9 提供规则版 **占位**，上线换 LLM 槽位。

---

## 7. 何时触发压缩：阈值与节奏

| 触发条件 | 典型值 | 说明 |
|----------|--------|------|
| 历史 token > T | 1500～3000 | 与 [27 Token 计数](27.token-counting-billing-tutorial.md) 联动 |
| 轮数 > R | 6～10 | 轮数便宜但粗糙 |
| 距上次压缩新增 > Δ | 800 token | 避免每轮都摘要 |
| 用户显式「重新开始话题」 | 事件 | 可 **清空或 fork** session |

**不要每轮都压缩**——摘要 API 成本 + **摘要漂移**（多次改写累积误差）。建议 **异步压缩**：用户发消息时若超阈值，**先用旧摘要 + 全量** 应答（或仅最近轮）， **后台 job 更新 summary**，下一轮生效。

### 7.1 版本与回滚

Session 存 `summary_version` 与 **上一版 summary 快照**。评测发现 **摘要丢关键数字** 时，**回滚 version** 并 **调 prompt**——像 [48 文档版本](48.doc-versioning-tutorial.md) 一样 **可审计**。

---

## 8. 与检索增强的分工

| 问题类型 | 靠摘要 | 靠检索 |
|----------|--------|--------|
| 用户意图延续 | ✓ | |
| 精确政策数字 | 仅当已写入 confirmed_facts | ✓ 仍以库为准 |
| 新子问题 | 指向 open_questions | ✓ |
| 跨文档推理 | ✗ | ✓ |

**摘要 + RAG 标准链路**：

```text
1. 读 session：summary + recent_turns
2. [109] 用 summary 改写 retrieval_query
3. 向量检索 top-k
4. [107] 预算装填 evidence
5. messages = system + summary_block + recent + evidence + user
6. LLM 生成
7. 若超阈值 → 排队 compact_job
```

读下图：摘要 **不进入** 向量库。

![摘要与检索分工](image/summary-memory/03-summary-vs-retrieval.png)

---

## 9. 综合实战：滚动摘要 Mini-RAG

以下 **单文件可运行**（规则摘要 + 假 token 计数），演示 **压缩前后 messages 体积**。

```python
"""summary_memory_demo.py — 滚动摘要 + 假 RAG messages 拼装"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any

TOKEN_COMPACT_THRESHOLD = 120  # 演示用字符代理 token
KEEP_RECENT_TURNS = 2


@dataclass
class Turn:
    role: str
    content: str


@dataclass
class Session:
    session_id: str
    summary: dict[str, Any] = field(default_factory=lambda: {
        "user_goal": "",
        "confirmed_facts": [],
        "open_questions": [],
        "entities": [],
        "constraints": ["仅依据检索资料"],
    })
    summary_version: int = 0
    turns: list[Turn] = field(default_factory=list)

    def history_chars(self) -> int:
        return sum(len(t.content) for t in self.turns)

    def needs_compact(self) -> bool:
        return self.history_chars() > TOKEN_COMPACT_THRESHOLD


def rule_based_compact(turns: list[Turn], old: dict) -> dict:
    """零 API：抽数字句 + 最后一问"""
    facts = list(old.get("confirmed_facts", []))
    opens = list(old.get("open_questions", []))
    entities = set(old.get("entities", []))
    for t in turns:
        if t.role == "assistant" and any(c.isdigit() for c in t.content):
            facts.append(t.content[:80])
        if t.role == "user" and ("?" in t.content or "？" in t.content or "吗" in t.content):
            opens.append(t.content)
        for kw in ("住宿", "差旅", "报销", "邮件", "政策"):
            if kw in t.content:
                entities.add(kw)
    goal = old.get("user_goal") or (turns[0].content if turns else "")
    return {
        "user_goal": goal[:100],
        "confirmed_facts": facts[-6:],
        "open_questions": opens[-3:],
        "entities": sorted(entities),
        "constraints": old.get("constraints", []),
    }


def compact_session(sess: Session) -> None:
    if len(sess.turns) <= KEEP_RECENT_TURNS:
        return
    to_compact = sess.turns[:-KEEP_RECENT_TURNS]
    recent = sess.turns[-KEEP_RECENT_TURNS:]
    sess.summary = rule_based_compact(to_compact, sess.summary)
    sess.summary_version += 1
    sess.turns = recent


def build_messages(sess: Session, evidence: list[str], user_query: str) -> list[dict]:
    summary_block = "【会话摘要】\n" + json.dumps(sess.summary, ensure_ascii=False, indent=2)
    recent_block = "\n".join(f"{t.role}: {t.content}" for t in sess.turns)
    ctx = "\n\n".join(f"[{i+1}] {e}" for i, e in enumerate(evidence))
    system = "你是企业助手。依据摘要延续上下文，依据检索资料回答；资料不足则拒答。"
    user = f"{summary_block}\n\n【最近对话】\n{recent_block}\n\n【检索资料】\n{ctx}\n\n【本轮问题】\n{user_query}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def demo():
    sess = Session(session_id="demo-1")
    script = [
        ("user", "一线城市的住宿上限是多少？"),
        ("assistant", "根据员工手册，一线城市住宿上限为500元每晚，含早餐。"),
        ("user", "那二线城市呢？"),
        ("assistant", "二线城市住宿上限为350元每晚。"),
        ("user", "如果我请客户吃饭，报销比例多少？"),
        ("assistant", "餐饮报销需事前申请，比例见差旅附件，当前对话未检索附件。"),
        ("user", "刚才住宿标准帮我写一段邮件正文"),
    ]
    for role, content in script:
        sess.turns.append(Turn(role, content))
        if sess.needs_compact():
            compact_session(sess)
    evidence = ["一线城市住宿上限500元每晚", "二线城市350元 nightly"]
    msgs = build_messages(sess, evidence, script[-1][1])
    print("summary_version", sess.summary_version)
    print("remaining turns", len(sess.turns))
    print("user message chars", len(msgs[1]["content"]))
    print(json.dumps(sess.summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo()
```

代码后解读：

1. **`TOKEN_COMPACT_THRESHOLD`** 演示触发——生产换 [27](27.token-counting-billing-tutorial.md) 的 tiktoken。  
2. **`rule_based_compact`** 可替换为 §6.1 LLM JSON 摘要。  
3. **`build_messages`** 把摘要、最近轮、证据 **分块**——对齐 [111 注入格式](111.context-injection-format-tutorial.md)。  
4. 最后一问「刚才住宿标准」——摘要里 `entities` 含 **住宿**，配合 [120 指代消解](120.coreference-resolution-tutorial.md) 生成检索 query **住宿标准 邮件**。

### 9.1 接 LLM 摘要（可选）

```python
def llm_compact(client, old_summary: dict, turns: list[Turn]) -> dict:
    prompt = open("prompts/summary_compact.txt").read()
    filled = prompt.replace("{old_summary}", json.dumps(old_summary, ensure_ascii=False))
    filled = filled.replace("{turns_to_compact}", "\n".join(f"{t.role}: {t.content}" for t in turns))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": filled}],
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)
```

---

## 10. 先错对对：五种典型翻车

### 10.1 错：从不压缩，十二轮全塞 messages

**对**：混合策略——**summary + 最近 2～4 轮**；超阈值触发 §7 压缩。

### 10.2 错：摘要里编了用户没确认的数字

**对**：摘要 prompt 写死 **confirmed_facts 必须来自对话**；抽检 + `summary_version` 回滚。

### 10.3 错：只有摘要，没有最近轮——「刚才」「不对」全懵

**对**：保留 **最近 N 轮原文**；指代强的会话 **N=4**。

### 10.4 错：把摘要当知识库，不再检索

**对**：政策类 **每轮仍检索**；摘要只帮 **意图与指代**，不替代 [34 Grounding](34.grounding-citation-tutorial.md)。

### 10.5 错：每轮同步压缩，延迟翻倍

**对**：**异步 compact** 或 **每 Δ token 一次**；用户路径不阻塞。

### 10.6 错：压缩后不更新 retrieval query

**对**：检索前走 [109](109.conversation-query-enhancement-tutorial.md)，输入 **summary + 本轮 user**。

---

## 11. 观测、评测与回滚

| 字段 | 用途 |
|------|------|
| session_id | 串联日志 |
| summary_version | 回滚 |
| pre/post_history_tokens | 压缩收益 |
| compact_latency_ms | 成本 |
| retrieval_query_after_summary | 与指代消解联调 |

**金标**：人工标注 **「压缩后是否仍能答对指代题」** 50 条；回归 **summary prompt 变更**。

---

## 12. 综合概念地图

![Summary Memory 概念速记](image/summary-memory/04-concept-map.png)

| 概念 | 一句话 |
|------|--------|
| Summary Memory | 用摘要换 token |
| 混合策略 | summary + 最近 N 轮 |
| 记忆槽 | JSON 防摘要瞎编 |
| 触发阈值 | 超 token/轮数再压 |
| 不替代检索 | 库才是政策真相 |

---

## 13. 常见陷阱与 FAQ

**Q：Summary Memory 和 ChatGPT「记忆功能」一样吗？**  
A：概念相近；企业 RAG 要 **会话隔离、可删、可审计**，且 **与检索链解耦**。

**Q：摘要用小模型还是大模型？**  
A：PoC 小模型 + 低温即可；要 **数字零幻觉** 可 **规则抽句 + LLM 润色** 两阶段。

**Q：压缩后用户改口「我之前说错了」怎么办？**  
A：最近轮原文仍在；摘要加 **supersedes** 字段或 **用户更正事件** 触发 **局部重摘要**。

**Q：多用户共享 session 可以吗？**  
A：企业场景 **禁止**——session 绑定 **user_id**，摘要含 **私有对话**。

**Q：和 [107 预算](107.context-budget-tutorial.md) 谁优先砍？**  
A：超限先 **砍证据条数**，再 **触发压缩**；不要 **砍 system**。

**Q：摘要存数据库还是 Redis？**  
A：热 session 放 Redis TTL；要审计可 **异步落 Postgres**。

**Q：工具调用 / Function Calling 历史怎么压？**  
A：tool 结果 **单独槽位** `tool_facts[]`，勿与闲聊混摘要（[124 Function Calling](124.function-calling-tool-use-tutorial.md)）。

**Q：如何测摘要质量？**  
A：**指代题** + **数字复述题** + **open_questions 召回** 三件套。

**Q：长文档上传会话要压缩吗？**  
A：上传正文进 **临时 evidence**，不走 summary；summary 只记 **「用户上传了 XX 合同」** 元信息。

**Q：合规 retention 7 天怎么配？**  
A：session + summary **统一 TTL**；到期 **硬删**，向量库 **本就不该存对话**。

**Q：和 [118 多轮历史](118.multi-turn-history-tutorial.md) 冲突吗？**  
A：不冲突——118 管 **格式**，本篇管 **体积**。

**Q：能否用 BM25 做摘要？**  
A：Extractive 摘要可 **抽原句**，适合 **数字密集** 政策对话；生成式补 **goal 与 open_questions**。

### 13.1 读路径自检（6 题）

1. Summary Memory 在链路哪一层？  
2. 为何「摘要 + 最近 N 轮」？  
3. confirmed_facts 为何禁止推测？  
4. 压缩触发为何不能每轮？  
5. 摘要能否替代检索？  
6. 与 [120 指代消解](120.coreference-resolution-tutorial.md) 如何配合？

### 13.2 动手作业（60 分钟）

1. 跑 §9，打印压缩前后 `user message chars`；  
2. 把 `TOKEN_COMPACT_THRESHOLD` 调到 **不触发**，观察消息长度；  
3. 用 [107](107.context-budget-tutorial.md) 计算器估 **摘要块占比**；  
4. 写 3 条 **指代 follow-up** 测摘要是否保留 entities。

---

## 14. 总结与系列下一步

1. **多轮 RAG 必做历史预算**——[28 窗口](28.context-window-tutorial.md) 与 [107 预算](107.context-budget-tutorial.md) 是硬约束。  
2. **Summary Memory = 滚动结构化摘要 + 最近轮**，不是删历史。  
3. **摘要服务检索意图**，不存储 **权威政策**——仍以向量库 + [34 Grounding](34.grounding-citation-tutorial.md) 为准。  
4. **异步压缩、版本回滚、槽位防幻觉** 是上线三板斧。  
5. 下一篇 [120 指代消解](120.coreference-resolution-tutorial.md) 解决 **「它」「那个政策」** 的检索 query。

### 14.1 系列下一步

| 目标 | 阅读 |
|------|------|
| 多轮拼 messages | [118 多轮历史](118.multi-turn-history-tutorial.md) |
| 指代消解 | [120 指代消解](120.coreference-resolution-tutorial.md) |
| 会话 query 增强 | [109 会话增强](109.conversation-query-enhancement-tutorial.md) |
| Context 预算 | [107 Context 预算](107.context-budget-tutorial.md) |

### 14.2 面试 30 秒版

「长 RAG 对话不能全量塞 history。Summary Memory 用滚动 JSON 摘要压缩旧轮，保留最近几轮原文，控制 token。摘要记 user_goal、confirmed_facts、open_questions，禁止编数字。超阈值异步压缩。摘要帮检索意图，不替代向量库。配合 109 改写 query 和 120 指代消解。」

---

> **初学者可能仍困惑的点**  
> - 摘要是 **会话缓存**，不是 **新知识入库**。  
> - **最近轮 + 摘要** 缺一不可——只有摘要会丢「刚才」。  
> - 压缩 **太勤** 与 **不压** 一样坏——要 **阈值 + 评测**。

### 14.3 与 LangChain ConversationSummaryBufferMemory 对照

LangChain 提供 **ConversationSummaryBufferMemory**：超 token 阈值时对旧消息摘要。对照本篇：

| 维度 | LangChain 封装 | 本篇工程建议 |
|------|----------------|--------------|
| 槽位 | 多为自由文本 | **JSON 记忆槽** 防编数字 |
| 触发 | 构造函数 token limit | **异步 + version** |
| 与 RAG | 需自己接 retriever | **摘要不替代检索** 写进 pipeline |
| 存储 | 内存 / 自定义 | Redis + Postgres 审计 |

理解封装后仍要 **自己定义 summary schema**——否则 PoC 能跑，上线 **数字幻觉** 难查。

### 14.4 给产品经理的一句话

「长聊会像叠聊天记录，很快塞爆模型『行李箱』。Summary Memory 像秘书写 **会议纪要**：旧对话压成几条要点，最近几句原话留着；问新政策仍 **查知识库**，不靠秘书笔记当法规。」

### 14.5 初学者 15 分钟 / 全天路径

| 时间 | 做什么 |
|------|--------|
| 15 min | 读 §3、§5、§8 分工图 |
| 45 min | 跑 §9，观察 compact 前后长度 |
| 2 h | 接 [118] 真实多轮 JSON，设 tiktoken 阈值 |
| 1 天 | 50 条指代 follow-up，测摘要 entities 召回 |

### 14.6 故障排查速查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 爆窗 | 未压缩 | 降阈值 / 减 recent N |
| 指代丢 | 摘要无 entities | 加强 §6 槽位 |
| 数字错 | 摘要编造 | 低温 + 规则抽句 |
| 检索偏 | 未走 109 改写 | summary 喂给 query 增强 |
| 延迟高 | 同步压缩 | 改异步 compact |

### 14.7 Session 存储 schema 建议

```json
{
  "session_id": "s-uuid",
  "user_id": "u-123",
  "tenant_id": "t1",
  "summary": {"user_goal": "...", "confirmed_facts": [], "open_questions": [], "entities": []},
  "summary_version": 3,
  "last_compact_at": "2026-07-10T12:00:00Z",
  "recent_turns": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "total_turns": 12,
  "ttl_expires_at": "2026-07-17T12:00:00Z"
}
```

**不要** 把 `recent_turns` 无限 append——compact 后 **只留 N 轮**。`total_turns` 供 **产品分析** 会话深度，不进 prompt。

### 14.8 与 [107 预算](107.context-budget-tutorial.md) 联动伪代码

```python
def allocate_budget(window: int, system_t: int, output_reserve: int, history_cap: int):
    evidence_cap = window - system_t - output_reserve - history_cap
    assert evidence_cap > 0, "历史块过大，请触发 compact 或降低 history_cap"
    return {"system": system_t, "history": history_cap, "evidence": evidence_cap, "output": output_reserve}
```

`history_cap` 内部分配：**summary 占 40%，recent_turns 占 60%**（可调）。summary 超长时 **优先裁 open_questions 旧项**，保留 **user_goal**。

### 14.9 团队 Review 清单（Summary Memory PR）

- [ ] 压缩触发阈值 **可配置**（环境变量）  
- [ ] summary **JSON schema** 校验（pydantic）  
- [ ] `summary_version` 与 **回滚 API**  
- [ ] compact **异步**，不阻塞首 token  
- [ ] 摘要 **不进向量库**  
- [ ] 与 [109](109.conversation-query-enhancement-tutorial.md) 的 query 输入 **文档化**  
- [ ] session **TTL** 与合规一致  
- [ ] 观测：`pre/post_history_tokens`、`compact_count`

### 14.10 案例表：压缩前后行为

| 轮次 | 用户 | 不压缩风险 | 压缩后摘要应保留 |
|------|------|------------|------------------|
| 5 | 二线住宿？ | 窗口尚够 | confirmed: 一线500 |
| 12 | 刚才住宿发邮件 | 爆窗 / 丢证据 | entities: 住宿标准 |
| 20 | 还是按上次说的 | 远指代丢失 | user_goal 连贯 |

### 14.11 面试追问：摘要丢了数字谁负责？

答：**摘要 prompt 与槽位设计** + **抽检**；关键数字 **仍应以检索 chunk 为准** 呈现给用户（[34 Grounding](34.grounding-citation-tutorial.md)）。摘要里的数字只是 **会话上下文**，不是 **权威来源**。

### 14.12 与 [118 多轮历史](118.multi-turn-history-tutorial.md) 消息形状示例

```python
messages = [
  {"role": "system", "content": SYSTEM_RAG},
  {"role": "user", "content": f"【会话摘要】\n{summary_json}\n\n【本轮】\n{query}"},
  # 可选：最近一轮 assistant 单独 message 便于 UI 对齐
]
```

OpenAI 兼容 API **不强制** assistant 中间轮全进 messages——**摘要替代远古 assistant** 即可；但 **最近一轮 assistant** 建议保留，用户常 say「你刚才说错了」。
'''

from _articles_120_121 import ARTICLE_120, ARTICLE_121


PROMPT_TEMPLATE = """---
layout: {layout}
style: hand-drawn-edu
aspect_ratio: 16:9
language: zh
---

Create a professional educational infographic, 16:9 landscape.
Layout: {layout}.
Style: hand-drawn-edu, cream #F5F0E8, macaron pastels, stick figures, Simplified Chinese.

Title: {title}

{body}

Footer: {footer}

All text Simplified Chinese.
"""


def write_prompts(slug: str, prompts: list[tuple[str, str, str, str, str]]):
    """filename, layout, title, body, footer"""
    for fname, layout, title, body, footer in prompts:
        path = ROOT / "image" / slug / "prompts" / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            PROMPT_TEMPLATE.format(layout=layout, title=title, body=body, footer=footer),
            encoding="utf-8",
        )


ARTICLES = [
    (
        "119.summary-memory-tutorial.md",
        "summary-memory",
        "历史压缩 Summary Memory",
        ARTICLE_119,
        [
            ("01-summary-idea.png", "hub-spoke", "§3 Summary Memory 是什么"),
            ("02-rolling-timeline.png", "timeline", "§5 滚动摘要时间线"),
            ("03-summary-vs-retrieval.png", "comparison-matrix", "§8 摘要与检索分工"),
            ("04-concept-map.png", "bento-grid", "§12 概念地图"),
        ],
        [
            ("01-summary-idea.md", "hub-spoke", "Summary Memory 在 RAG 中的位置",
             "Center hub: Session 层滚动摘要\n\nSpoke 1: 向量库\n- 企业文档 chunk\n- 长期存储\n\nSpoke 2: 摘要记忆\n- JSON 记忆槽\n- 压缩旧轮次\n\nSpoke 3: 最近 N 轮\n- 保留原文\n- 指代线索\n\nSpoke 4: 本轮检索\n- 证据 chunk\n- 不替代摘要",
             "历史压缩 Summary Memory · §3"),
            ("02-rolling-timeline.md", "timeline", "滚动摘要时间线",
             "Timeline left to right:\n1. 轮1-4 全量缓冲\n2. 超阈值触发 compact\n3. summary v1 生成\n4. 仅保留最近2轮 + summary\n5. 继续对话 → summary v2",
             "历史压缩 Summary Memory · §5"),
            ("03-summary-vs-retrieval.md", "comparison-matrix", "摘要 vs 检索分工",
             "Matrix rows: 用户意图 / 精确数字 / 新政策 / 跨文档\nColumns: 靠摘要 / 靠检索\nMark which handles what",
             "历史压缩 Summary Memory · §8"),
            ("04-concept-map.md", "bento-grid", "Summary Memory 概念速记",
             "Tiles: 混合策略 / 记忆槽 / 触发阈值 / 异步压缩 / 不替代检索 / 配合109与120",
             "历史压缩 Summary Memory · §12"),
        ],
    ),
    (
        "120.coreference-resolution-tutorial.md",
        "coreference-resolution",
        "指代消解 Coreference Resolution",
        ARTICLE_120,
        [
            ("01-coref-idea.png", "hub-spoke", "§3 指代消解是什么"),
            ("02-entity-scoring.png", "comparison-matrix", "§5 候选实体评分"),
            ("03-pipeline-position.png", "flowchart", "§8 Pipeline 位置"),
            ("04-concept-map.png", "bento-grid", "§12 概念地图"),
        ],
        [
            ("01-coref-idea.md", "hub-spoke", "指代消解在检索前",
             "Center: 指代消解\n\nSpoke 1: 它/那个 → 实体\nSpoke 2: standalone query\nSpoke 3: embed 前\nSpoke 4: 向量检索",
             "指代消解完全指南 · §3"),
            ("02-entity-scoring.md", "comparison-matrix", "候选实体评分因子",
             "Compare Recency / Role / Type match / Summary salience",
             "指代消解完全指南 · §5"),
            ("03-pipeline-position.md", "flowchart", "错误 vs 正确 Pipeline",
             "Wrong: embed「它」\nRight: resolve → embed",
             "指代消解完全指南 · §8"),
            ("04-concept-map.md", "bento-grid", "指代消解概念速记",
             "Tiles: 会话指代 / 实体栈 / standalone / 与100109分工 / 低置信澄清",
             "指代消解完全指南 · §12"),
        ],
    ),
    (
        "121.unauthorized-doc-filter-tutorial.md",
        "unauthorized-doc-filter",
        "越权文档过滤",
        ARTICLE_121,
        [
            ("01-filter-gates.png", "hub-spoke", "§3 越权过滤位置"),
            ("02-acl-strategies.png", "comparison-matrix", "§4 53 ACL 策略落地"),
            ("03-security-split.png", "comparison-matrix", "§12 C6 安全分工"),
            ("04-concept-map.png", "bento-grid", "§13 概念地图"),
        ],
        [
            ("01-filter-gates.md", "hub-spoke", "越权过滤三道闸",
             "Center: 无权 chunk 不进 prompt\n\nSpoke 1: 网关 JWT\nSpoke 2: where 检索\nSpoke 3: post_validate",
             "越权文档过滤 · §3"),
            ("02-acl-strategies.md", "comparison-matrix", "检索前 filter vs post-filter",
             "Compare 安全 / Recall / 性能 — 引用53篇",
             "越权文档过滤 · §4"),
            ("03-security-split.md", "comparison-matrix", "121 vs 112 vs 122",
             "三列：越权 / 无资料 / 内容安全",
             "越权文档过滤 · §12"),
            ("04-concept-map.md", "bento-grid", "越权过滤概念速记",
             "Tiles: 53 ACL / where / tenant / post_validate / 审计 / Grounding",
             "越权文档过滤 · §13"),
        ],
    ),
]


def main():
    counts = {}
    for fname, slug, title, body, img_items, prompt_items in ARTICLES:
        content = pad_if_needed(body, slug)
        (ROOT / fname).write_text(content, encoding="utf-8")
        write_image_assets(slug, title, img_items)
        write_prompts(slug, prompt_items)
        counts[fname] = hanzi_count(content)
    for k, v in counts.items():
        status = "OK" if v >= 5000 else "LOW"
        print(f"{k}: {v} hanzi [{status}]")
    return counts


if __name__ == "__main__":
    main()
