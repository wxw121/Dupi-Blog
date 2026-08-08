"""Pass 4 metadata: image conclusions, hands-on paths, comparison tables, wrong-right blocks."""

from __future__ import annotations

import re

# 02-flow 图后收束（痛点/能力边界，不说「与代码逐一对应」）
FLOW_AFTER: dict[int, str] = {
    215: "对照上图：Chatbot/RAG/Workflow/Agent 在可控性与灵活性上各擅胜场——选型先看任务是否需要自主多步决策。",
    216: "对照上图：能用 Workflow 或 RAG 解决的场景不必上 Agent——复杂度与不可预测性是真实成本。",
    217: "对照上图：工具、编排、记忆、观测、治理五层分工——下文按层展开，避免把所有逻辑塞进一个 prompt。",
    218: "对照上图：模型只产出「调谁、传什么」；注册表与执行器负责校验、超时与审计——工具层是 Agent 的手。",
    219: "对照上图：Schema 同时服务模型、校验器与文档——三读者对齐后参数错误会在 ACT 前被拦住。",
    220: "对照上图：格式/业务/跨字段三层校验——坏参数不应进入执行器，否则重试只会放大破坏。",
    221: "对照上图：工具返回必须标准化为 `ToolResult`/`to_llm_string()`，否则模型读不懂失败语义。",
    222: "对照上图：超时、退避、熔断、降级是工具链四件套——没有它们，一次慢调用会拖死整个循环。",
    223: "对照上图：可重试的工具必须带幂等键——否则「再试一次」可能重复扣款或重复写入。",
    224: "对照上图：高风险动作先过 HITL 闸门——自动与人工审批要分级，不能全放行或全拦截。",
    225: "对照上图：RBAC/ABAC 决定「谁能调什么」——权限在 ACT 前检查，不是事后审计的补丁。",
    226: "对照上图：Observe→Think→Act 循环把 Part 2 工具链串进 ACT——没有停止条件会无限转圈（见 231）。",
    227: "对照上图：ReAct 是「Thought→Action→Observation」交替——Observation 必须回灌，否则等于盲走。",
    228: "对照上图：先 Plan 再 Execute——步骤多的任务比 ReAct 少绕圈，但计划过时需重规划。",
    229: "对照上图：Generator 产出草稿、Reflector 挑错再改——适合对外文案/代码等质量敏感输出。",
    230: "对照上图：Goal→Step→Action 分解——复杂目标先拆可执行子任务，再映射到工具。",
    231: "对照上图：步数/时间/Token 预算与显式完成信号——没有停止条件的 Agent 是生产事故。",
    232: "对照上图：工作记忆/会话状态/长期记忆/知识库不能混为一谈——写错抽屉会污染召回。",
    233: "对照上图：短期记忆管本轮槽位与中间结果——不是把所有聊天记录无差别塞回上下文。",
    234: "对照上图：长期记忆跨会话保留偏好与事实——写入前要有策略，否则噪声会固化成「用户画像」。",
    235: "对照上图：什么该写入长期记忆由策略门控——PII 与低置信信息默认不落库。",
    236: "对照上图：召回触发、排序与注入量要控预算——记忆太多与没有记忆一样会伤质量。",
    237: "对照上图：删除与导出是用户权利——Memory 系统必须能按 ID/用户级擦除，不能只做追加。",
    239: "对照上图：复杂问题先拆子查询再分别检索——「改写一次」解决不了多子题覆盖问题。",
    240: "对照上图：多轮检索要有防循环与去重——「再搜一次」必须比上一轮有新信息。",
    241: "对照上图：检索与 tool_calls 在同一决策环——模型既能查库也能调业务 API，但要有预算。",
    242: "对照上图：每个引用必须指回 Evidence——有 `[1]` 标记不等于证据真的支持该句。",
    243: "对照上图：Bad Case 要沿 trace 分层定位——规划/检索/工具/生成只修一层，避免 prompt 乱改。",
    244: "对照上图：七种编排模式是选型菜单——ReAct/Plan/FSM/事件驱动等按可控性与灵活性取舍。",
    245: "对照上图：FSM 用状态转移约束 Agent——比纯 prompt 更能防止跳步与越权。",
    246: "对照上图：Checkpoint 保存步骤/预算/工具结果——只存聊天记录无法恢复执行位置。",
    247: "对照上图：长等待与进程重启需要 Durable Execution——Activity 副作用与可重放逻辑要分离。",
    248: "对照上图：长任务进后台 Worker——同步 HTTP 扛不住数小时的人工等待与重试。",
    249: "对照上图：事件总线解耦步骤——每步可溯源、可重放，比巨型单体循环更易演进。",
    250: "对照上图：知识库 Agent 管上传/索引/检索生命周期——Part 7 五篇都在此 `shared/` 上扩展。",
    251: "对照上图：研究类问题需要多来源与交叉验证——单次 RAG 检索写不出可靠报告。",
    252: "对照上图：客服场景查单与退款分级——高风险 `refund` 必须走 HITL（224）。",
    253: "对照上图：代码审查按 diff 分块 lint——大 PR 不能一次塞满上下文。",
    254: "对照上图：运维扩容/清缓存属高风险——须权限确认（225）再 ACT。",
}

FLOW_PREAMBLE: dict[int, str] = {
    251: "读下图时，先看「简单 RAG 做研究」的局限——单次检索、信息片面、无法交叉验证；下文用多步研究管道补齐。",
}

# 01-idea 图后收束（去模板句）
IDEA_AFTER: dict[int, str] = {
    214: "对照上图：Level 0 纯 RAG 到 Level 2 最小 Agent 循环——关键跃迁是「能观察环境并选工具」，不是多检索几次。",
    215: "对照上图：四形态对比的核心轴是「谁决定下一步」——越往 Agent 越自主，也越难测与控。",
    216: "对照上图：决策树入口是「步骤是否固定、是否需工具写外部世界」——满足 Workflow/RAG 就别硬上 Agent。",
    217: "对照上图：企业 Agent 五层——工具与权限在底层，编排与记忆在中层，观测与治理贯穿全程。",
    218: "对照上图：Tool Calling 三段式——模型提议、注册表校验、执行器落地；缺一段都会断链。",
    219: "对照上图：Schema 是模型与执行器之间的契约——字段描述直接影响模型会不会填对参数。",
    220: "对照上图：校验分格式/业务/跨字段——越早拦截坏参数，ACT 越安全、重试越有意义。",
    221: "对照上图：统一 `ToolResult` 让模型能区分成功、业务失败与系统错误——别只返回裸字符串。",
    222: "对照上图：超时+退避+熔断+降级——工具失败要可恢复，不能把整个 Agent 吊死。",
    223: "对照上图：幂等键让「安全重试」成为可能——支付、写入类工具必备。",
    224: "对照上图：HITL 是风险闸门——AUTO/CONFIRM/BLOCK 分级比「全人工」或「全自动」更贴近生产。",
    225: "对照上图：最小权限原则——Agent 只能调业务允许的工具，权限检查在 ACT 前。",
    226: "对照上图：OTA 循环是 Part 3 主轴——Observe 收反馈，Think 选工具，Act 调 Part 2 能力链。",
    227: "对照上图：ReAct 把推理与行动交织——没有 Observation 回灌，Thought 就是空谈。",
    228: "对照上图：Plan-and-Execute 先路线图后开车——适合步骤多、试错成本高的任务。",
    229: "对照上图：Reflection 用 Reflector 挑 Generator 的错——适合质量敏感、可自检的输出。",
    230: "对照上图：任务分解把模糊 Goal 变成可执行 Step——再映射到具体工具调用。",
    231: "对照上图：停止条件=预算+完成信号——没有上限的循环在生产上等于事故。",
    232: "对照上图：五类记忆各管各的抽屉——别把知识库、会话状态与长期偏好混写。",
    233: "对照上图：短期记忆=本轮工作区——槽位、中间结果、最近工具输出，不是永久档案。",
    234: "对照上图：长期记忆跨会话——写入要谨慎，召回要可删（237）。",
    235: "对照上图：写入策略决定什么能进档案柜——默认宁缺毋滥，PII 先过滤。",
    236: "对照上图：召回策略决定注入多少记忆——过多会挤掉任务上下文。",
    237: "对照上图：隐私与删除是 Memory 的合规底座——必须能按用户/条目擦除。",
    238: "对照上图：左普通 RAG 一次检索易缺证据；右 Agentic RAG 在充分性 False 时继续检索，两侧齐全后再生成。",
    239: "对照上图：Query Planning 是「旅行规划师」不是「查询改写器」——价值在结构化拆解子问题。",
    240: "对照上图：多步检索每轮要有新证据——否则是空转，需防循环与去重。",
    241: "对照上图：Tool-Augmented RAG 把检索与业务 API 放进同一 tool 循环——仍受预算约束。",
    242: "对照上图：引用验证查的是「证据是否支持该句」——不是数 `[1]` 有几个。",
    243: "对照上图：调试要沿 trace 看全链——最终答案错不等于生成层错，可能是规划或检索层。",
    244: "对照上图：七种工作流模式是编排选型菜单——按可控性、延迟、可测性取舍。",
    245: "对照上图：状态机用显式状态约束转移——比纯自然语言更能防跳步。",
    246: "对照上图：Checkpoint 是游戏存档——要能恢复步骤、预算与工具结果，不只存聊天。",
    247: "对照上图：Durable Execution 让「进程死了任务不死」——长等待与重试由平台托管。",
    248: "对照上图：后台任务+进度推送——长 Agent 不能绑在 HTTP 请求线程上。",
    249: "对照上图：事件驱动把步骤拆成可溯源事件——利于审计、重放与横向扩展。",
    250: "对照上图：知识库 Agent 覆盖上传→索引→检索——Part 7 的 `shared/` 从这里起步。",
    251: "对照上图：研究 Agent 走「分解→多轮搜索→交叉验证→综合报告」——不是单次检索总结。",
    252: "对照上图：客服 Agent 查单可自动、退款需确认——风险分级决定 HITL 闸门。",
    253: "对照上图：审查 Agent 按 diff 分块——大变更拆块才能控上下文与误报。",
    254: "对照上图：运维 Agent 对扩容/清缓存等操作强制确认——高风险 ACT 必须可审计。",
}

# 03-concept-map 图后收束
MAP_AFTER: dict[int, str] = {
    214: "对照上图：Level 0→2 演化路线——下一篇 215 在四形态里给选型坐标。",
    215: "对照上图：四形态地图——读完可用「步骤是否固定、要不要写外部世界」快速选型。",
    216: "对照上图：不该用 Agent 的信号清单——与 215 选型表配合使用。",
    217: "对照上图：五层架构地图——218 起从工具层向下实现。",
    218: "对照上图：注册表/执行器/审计三角——219 起补 Schema 与校验。",
    219: "对照上图：Schema 三读者——字段变更要同时想模型、校验器与文档。",
    220: "对照上图：三层校验地图——221 接结果标准化。",
    221: "对照上图：结果标准化后 222 才能做超时重试。",
    222: "对照上图：弹性工具链——223 幂等让重试安全。",
    223: "对照上图：幂等+重试——224 HITL 管高风险。",
    224: "对照上图：HITL 分级——225 补权限边界。",
    225: "对照上图：权限边界收束 Part 2——226 接入 OTA 循环。",
    226: "对照上图：OTA 与 Part 2 继承表——227 起进 ReAct 等模式。",
    227: "对照上图：ReAct 在 OTA 的 THINK/ACT 里落地——228 Plan-and-Execute 是另一种 THINK。",
    228: "对照上图：Plan vs ReAct——229 Reflection 补质量环。",
    229: "对照上图：Reflection 环——230 任务分解处理复杂 Goal。",
    230: "对照上图：分解→执行链——231 补停止条件。",
    231: "对照上图：预算与停止——232 起进 Memory 专题。",
    232: "对照上图：五类记忆地图——233 短期、234 长期、235 写入、236 召回。",
    233: "对照上图：短期记忆在会话内——234 跨会话。",
    234: "对照上图：长期记忆链——235 写入策略、236 召回策略。",
    235: "对照上图：写入策略门——236 召回、237 删除。",
    236: "对照上图：召回注入链——237 隐私收束 Part 4。",
    237: "对照上图：Memory 合规收束——238 进 Agentic RAG 总览。",
    238: "对照上图：四组件+证据库/预算——239 Query Planning 是第一站。",
    239: "对照上图：Planning→检索→证据——240 多步检索加深。",
    240: "对照上图：多步检索环——241 接 tool-augmented。",
    241: "对照上图：检索+工具双环——242 引用验证。",
    242: "对照上图：验证链——243 Bad Case 调试收束质量。",
    243: "对照上图：trace 分层调试——244 工作流编排。",
    244: "对照上图：七种模式——245 FSM、246 检查点进可靠性线。",
    245: "对照上图：FSM 约束——246 checkpoint、247 Temporal。",
    246: "对照上图：手动 checkpoint——247 平台化持久执行。",
    247: "对照上图：Durable 语义——248 后台、249 事件驱动。",
    248: "对照上图：后台任务——249 事件总线。",
    249: "对照上图：事件驱动收束 Part 6——250 综合实战起步。",
    250: "对照上图：知识库平台——251 研究、252 客服、253 审查、254 运维。",
    251: "对照上图：研究管道——252 客服接 HITL。",
    252: "对照上图：客服+HITL——253 审查、254 运维。",
    253: "对照上图：分块审查——254 高风险运维收束 Part 7。",
    254: "对照上图：Part 7 收束——系列第二阶段（255+）可从此平台继续扩展。",
}

# 动手路径（全系列）
HANDS_ON_ALL: dict[int, str] = {
    214: "① 读 §最小示例 Level 0→2 → ② `python -m demos.demo_214`（`examples/agent-platform`）→ ③ 对照 §工程化版本",
    215: "① 读 §它解决什么问题 四形态图 → ② 用文中决策表给 3 个场景选型 → ③ 读 §什么时候不要这么做",
    216: "① 读 §决策树 → ② 标出自己项目里「不该用 Agent」的信号 → ③ 对照 §常见失败模式",
    217: "① 扫五层架构图 → ② 画自己系统分层草图 → ③ 按 §下一步 进入 218 工具层",
    218: "① 读 §最小示例 → ② 运行 `demo_registry()` + `demo_executor()` → ③ 试 §先错对对",
    219: "① 读 Schema 三读者 → ② 运行文末 `demo_schema()` → ③ 故意改错字段观察校验",
    220: "① 读三层校验表 → ② 运行 `demo_validation()` → ③ 对照 §常见失败模式",
    221: "① 读 `StandardToolResult` → ② 运行 `demo_normalize()` → ③ 看 `to_llm_string()` 输出",
    222: "① 读超时/退避配置 → ② 运行 `demo_retry()` → ③ 模拟慢工具触发熔断",
    223: "① 读幂等键设计 → ② 运行 `demo_idempotent()` → ③ 同一 key 连调两次对比",
    224: "① 读 HITL 分级表 → ② 运行 `demo_hitl()` → ③ 改权限为 BLOCK 观察行为",
    225: "① 读 RBAC 表 → ② 运行 `demo_permissions()` → ③ 对照 §生产环境注意事项",
    226: "① 读 Part 2 继承表 → ② 运行 `demo_ota_loop()` → ③ 对照 §工程化版本",
    227: "① 读 ReAct 概念地图 → ② 运行 `demo_react()` → ③ 试 §先错对对",
    228: "① 读 Plan vs ReAct 表 → ② 运行 `demo_plan_execute()` → ③ 试 §先错对对",
    229: "① 读 Generator/Reflector 环 → ② 运行 `demo_reflection()` → ③ 看迭代如何改输出",
    230: "① 读 Goal/Step 分解 → ② 运行 `demo_decompose()` → ③ 对照 §常见失败模式",
    231: "① 读预算表 → ② 运行 `demo_stop()` → ③ 去掉停止条件观察死循环风险",
    232: "① 读五类记忆地图 → ② 运行 `demo_memory_types()` → ③ 试 §先错对对",
    233: "① 读会话状态设计 → ② 运行 `demo_short_term()` → ③ 试 §先错对对",
    234: "① 读长期记忆模型 → ② 运行 `demo_long_term()` → ③ 对照 235 写入策略",
    235: "① 读写入策略表 → ② 运行 `demo_write_policy()` → ③ 对照 237 删除",
    236: "① 读召回策略 → ② 运行 `demo_retrieval_policy()` → ③ 调注入条数看上下文占用",
    237: "① 读删除管道 → ② 运行 `demo_deletion()` → ③ 对照 GDPR 场景清单",
    238: "① 读 §是什么 充分性闸门 → ② 扫 §怎么做 四组件 → ③ 进 239+ lab 写代码",
    239: "① 读 Query Planning 直觉 → ② `cd examples/rag-agent-lab && python main.py 239` → ③ 回读 §怎么做",
    240: "① 读多步检索防循环 → ② `python main.py 240` → ③ 试 §先错对对",
    241: "① 读 tool 循环 → ② `python main.py 241` → ③ 对照 §权限与预算",
    242: "① 读引用验证规则 → ② `python main.py 242` → ③ 故意造假引用跑验证",
    243: "① `python main.py 243`（无需 API）→ ② 对照 §对照前文 trace 表 → ③ 自建 1 条 bad case",
    244: "① `python main.py 244` → ② 对照 §七种模式决策表 → ③ 为场景选一种模式",
    245: "① 读 FSM 转移表 → ② 运行 `demo_fsm()` → ③ 试非法转移",
    246: "① 读 checkpoint 字段 → ② 运行 `demo_checkpoint()` → ③ 对照 §旧写法表",
    247: "① 读 246 checkpoint → ② 对照 §对照前文 Temporal 表 → ③ `python temporal_minimal.py`（需 Docker）",
    248: "① 读后台任务模型 → ② 运行 `demo_background()` → ③ 对照进度推送输出",
    249: "① 读事件溯源表 → ② 运行 `demo_events()` → ③ 画自己系统的 event 列表",
    250: "① `cd examples/agent-platform && pip install -r requirements.txt` → ② `python -m demos.demo_250` → ③ 251 在此基础上扩展",
    251: "① 读研究管道 prose → ② `python -m demos.demo_251` → ③ 对照 §综合实战 diff 树",
    252: "① 读 HITL 退款流 → ② `python -m demos.demo_252` → ③ 验收 `[HITL]` 与 refund",
    253: "① 读 diff 分块 → ② `python -m demos.demo_253` → ③ 改 diff 测 `eval()` 误报",
    254: "① 读高风险确认 → ② `python -m demos.demo_254` → ③ 验收扩容与清缓存 HITL",
}

COMPARISON_TABLE: dict[int, str] = {
    243: """
### 对照前文：盲改 prompt vs trace 调试

| 旧写法（239–242 无调试体系） | 收束写法（本篇） | 何时用 |
|------------------------------|------------------|--------|
| 用户报错就改 prompt | trace 反查 + 根因分层（规划/检索/工具/生成） | 多步 Agentic RAG 失败 |
| 只看最终答案对错 | 保存 bad case + 回归集 | 防止修 A 坏 B |
| 一次改多层 | **一次只修一层** | 243 核心调试原则 |
| 无复现材料 | `main.py 243` 可离线复现 | 团队协作与 CI 回归 |

""",
    247: """
### 对照前文：手动检查点 vs Temporal 持久执行

| 旧写法（246） | 收束写法（本篇） | 何时用 |
|---------------|------------------|--------|
| 内存 `save/load_checkpoint` | Temporal Workflow + Activity | 进程会重启、任务要活数天 |
| 自己 sleep 等审批 | 平台托管 timer / signal | 人工等待跨小时/天 |
| 副作用写在循环里 | Activity 幂等 + 可重放逻辑分离 | 重试不重复扣款/写入 |
| 单进程 demo | `temporal_minimal.py`（需 Docker） | 生产级长流程 Agent |

""",
}

WRONG_RIGHT: dict[int, str] = {
    215: """
### 先错后对：选型

```text
❌ 所有聊天入口都做成 Agent（步骤其实固定）
✅ 固定流程用 Workflow，问答用 RAG，只有需自主多步时用 Agent
```
""",
    219: """
### 先错后对：Schema 缺描述

```python
# ❌ 模型不知道 amount 是「分」还是「元」
{"amount": {"type": "number"}}

# ✅ 描述写清单位与约束
{"amount": {"type": "number", "description": "金额，单位：分，必须 > 0"}}
```
""",
    228: """
### 先错后对：无计划直接 ReAct

```text
❌ 复杂任务直接 ReAct → 反复试错、token 浪费
✅ 步骤 ≥4 且可预先列出时，先 Plan 再 Execute（本篇模式）
```
""",
    233: """
### 先错后对：短期记忆当长期库

```python
# ❌ 每轮对话全量写入「长期记忆」
memory.save(full_chat_transcript)

# ✅ 短期：本轮槽位；长期：经 235 策略提取后的稳定事实
session.update_slot("order_id", value)
```
""",
    240: """
### 先错后对：空转检索

```text
❌ 检索 3 轮但 evidence 集合不变 → 浪费预算
✅ 每轮记录新 evidence_id；无新增则停止或换 query（见本篇防循环）
```
""",
    248: """
### 先错后对：同步 HTTP 跑长任务

```text
❌ POST /agent/run 阻塞 30 分钟等人工审批
✅ 202 接受任务 + job_id，Worker 后台跑，SSE/WebSocket 推进度（本篇）
```
""",
    251: """
### 先错后对：单次检索写报告

```text
❌ 用户要「市场格局」→ 一次 vector search → 直接总结
✅ 分解子问题 → 多轮检索 → 交叉验证 → synthesize（见 demo_251）
```
""",
}

COMPREHENSIVE_251_254: dict[int, str] = {
    251: """## 综合实战

**阅读顺序：** [250](250.build-knowledge-base-agent-tutorial.md) `shared/` → 本篇 → [252](252.build-customer-support-agent-tutorial.md)。

**相对 250 新增：**

```text
examples/agent-platform/
├── shared/              # 沿用 250
└── demos/
    ├── demo_250.py      # KnowledgeBaseAgent
    └── demo_251.py      # + ResearchAgent.synthesize / run_research
```

**关键扩展：** `ResearchAgent` 继承 `KnowledgeBaseAgent`，在 `run_research()` 中串联 upload→index→search→synthesize。

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_251
```

**验收：** 输出 `## 研究摘要` 与至少 2 条要点 bullet；末尾 `OK — ResearchAgent (251)`。

""",
    252: """## 综合实战

**阅读顺序：** [250](250.build-knowledge-base-agent-tutorial.md) + [224](224.human-in-the-loop-agent-tutorial.md) HITL → 本篇。

**相对 250 新增：**

```text
demos/demo_252.py
├── SupportAgent extends BaseAgent
├── lookup_order  (PermissionLevel.AUTO)
└── refund        (PermissionLevel.CONFIRM → 打印 [HITL])
```

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_252
```

**验收：** 控制台出现 `[HITL]` 提示与 `refund` 成功 `ToolResult`。

""",
    253: """## 综合实战

**阅读顺序：** [250](250.build-knowledge-base-agent-tutorial.md) 平台模式 → 本篇 diff 工具。

**相对 250 新增：**

```text
demos/demo_253.py
├── parse_diff   # 从 unified diff 提取文件列表
└── lint_chunk   # 分块静态检查（示例：拦截 eval()）
```

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_253
```

**验收：** 打印 `issues: ['avoid eval()']` 与 `OK — CodeReviewAgent (253)`。

""",
    254: """## 综合实战

**阅读顺序：** [250–253](250.build-knowledge-base-agent-tutorial.md) + [225](225.agent-tool-permission-boundary-tutorial.md) 高风险确认。

**相对 250 新增：**

```text
demos/demo_254.py
├── scale_service  (CONFIRM)
└── purge_cache    (CONFIRM)
```

**运行：**

```bash
cd examples/agent-platform && python -m demos.demo_254
```

**验收：** 扩容与清缓存均经 HITL 提示后返回 `success=True`；末尾 `OK — OpsAgent (254)`。

""",
}

FLOW_PREAMBLE_DEFAULT = "读下图时，先看能力边界与痛点流程——与 §最小示例 代码互补，不是逐步对照。"

TEMPLATE_IDEA = re.compile(
    r"对照上图：[^—\n]+——建立本专题直觉，留意图中标注的输入/输出或对比关系，再读下文。"
)
TEMPLATE_MAP = re.compile(
    r"对照上图：[^。\n]+概念地图——把全篇概念串成一张地图[^。\n]*。"
)
TEMPLATE_FLOW_OLD = "对照上图：流程图步骤与下文 §最小示例 代码逐一对应，建议先扫一眼再读代码。"
TEMPLATE_FLOW_PREAMBLE_OLD = "读下图时，先看流程要点，再对照 §最小示例 代码。"
