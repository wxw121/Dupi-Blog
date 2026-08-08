"""Pass 5 metadata: series rename, 02-flow for 237/239/240, glossary expansion, §怎么做术语表."""

from __future__ import annotations

SERIES_OLD = "agent-rag-series-239-248.md"
SERIES_NEW = "agent-rag-series-238-254.md"
SERIES_LINK_LABEL = "Agent/RAG 工程系列 238–254"

# (term, english, 通俗说) — append if term not already in glossary block
GLOSSARY_APPEND: dict[int, list[tuple[str, str, str]]] = {
    216: [
        ("Workflow", "工作流", "步骤与分支由开发者写死，像工厂流水线。"),
    ],
    219: [
        ("Pydantic", "数据校验库", "用类型声明描述参数形状，自动校验并生成错误信息。"),
    ],
    220: [
        ("跨字段校验", "Cross-field Validation", "多个参数组合起来才合法，如起止日期、金额区间。"),
    ],
    221: [
        ("ToolResult", "工具结果", "统一的成功/失败/数据包装，模型和日志都读它。"),
    ],
    222: [
        ("熔断器", "Circuit Breaker", "连续失败后暂时拒绝调用，给下游恢复时间。"),
    ],
    223: [
        ("幂等键", "Idempotency Key", "同一业务请求的唯一编号，重试时不会重复执行。"),
    ],
    224: [
        ("CONFIRM", "需确认级别", "工具默认暂停，等人点同意再执行。"),
    ],
    225: [
        ("ABAC", "属性访问控制", "按用户属性+资源属性动态判断，比固定角色更细。"),
    ],
    226: [
        ("EVALUATE", "评估步", "每轮 ACT 后判断任务是否完成，未完成则继续 OTA。"),
    ],
    228: [
        ("重规划", "Re-planning", "执行中发现计划过时，重新生成剩余步骤。"),
    ],
    229: [
        ("Reflector", "反思器", "专门挑 Generator 输出里的错误与遗漏。"),
    ],
    230: [
        ("子任务", "Sub-task", "从大目标拆出的可单独执行的一步。"),
    ],
    231: [
        ("完成信号", "Completion Signal", "模型或规则显式声明「任务结束」，避免空转。"),
    ],
    232: [
        ("工作记忆", "Working Memory", "当前任务草稿纸，任务结束可丢弃。"),
    ],
    233: [
        ("会话状态", "Session State", "本轮对话的槽位表，如订单号、当前步骤。"),
    ],
    234: [
        ("用户画像", "User Profile", "跨会话的稳定偏好摘要，不是全文聊天记录。"),
    ],
    235: [
        ("PII", "个人可识别信息", "姓名、电话、证件号等，写入前要过滤或脱敏。"),
    ],
    236: [
        ("注入预算", "Injection Budget", "本轮最多往 prompt 塞几条记忆，防止挤爆上下文。"),
    ],
    237: [
        ("删除管道", "Deletion Pipeline", "跨主库/向量/缓存/备份的编排清理流程。"),
        ("Outbox", "发件箱模式", "先记「待删除」再异步清各系统，失败可重试。"),
    ],
    239: [
        ("Query Planning", "查询规划", "把复杂问题拆成带数据源、过滤条件与期望证据的多份子查询。"),
        ("RRF", "Reciprocal Rank Fusion", "多路检索结果按排名倒数加权融合为统一列表。"),
        ("Sufficiency Check", "充分性检查", "判断当前证据是否足以回答，不足则继续检索。"),
    ],
    240: [
        ("多步检索", "Multi-Step Retrieval", "后一步查什么由前一步证据决定，不是一次规划到底。"),
        ("证据饱和", "Evidence Saturation", "新一轮检索没有新 evidence_id 时，应停止或换策略。"),
        ("查询依赖", "Query Dependency", "子问题 B 的检索词依赖子问题 A 的结果。"),
    ],
    241: [
        ("tool_calls", "工具调用列表", "模型一次可请求多个工具，执行后再回灌结果。"),
        ("检索工具", "Retrieval Tool", "把向量库/API 查询封装成与普通工具同形的函数。"),
        ("工具循环", "Tool Loop", "生成→执行 tool→再生成，直到不再请求工具。"),
    ],
    242: [
        ("Citation", "引用", "答案中指向证据片段的标注，如 [1] 对应 evidence_id。"),
        ("证据支持度", "Support Check", "判断某句结论是否被引用文本真正蕴含。"),
        ("修正轮", "Correction Pass", "验证失败后让模型按证据重写或披露不确定。"),
    ],
    243: [
        ("Trace", "执行轨迹", "规划/检索/工具/生成的有序记录，用于回放与定位。"),
        ("根因分层", "Layered Root Cause", "按层判断错在规划、检索、工具还是生成。"),
        ("回归集", "Regression Set", "修 bug 后反复跑的 bad case 集合。"),
    ],
    244: [
        ("编排模式", "Orchestration Pattern", "ReAct/FSM/事件驱动等组织 Agent 步骤的方式。"),
    ],
    245: [
        ("FSM", "有限状态机", "用状态与合法转移约束 Agent，禁止乱跳。"),
    ],
    246: [
        ("恢复点", "Resume Point", "从 checkpoint 继续执行时的步骤与预算快照。"),
    ],
    247: [
        ("Activity", "Temporal 活动", "有副作用的外部操作，可重试且需幂等。"),
        ("Workflow", "Temporal 工作流", "可重放的编排逻辑，进程死了也能续跑。"),
    ],
    248: [
        ("Job", "后台任务", "异步执行的长 Agent，用 job_id 查询进度。"),
    ],
    249: [
        ("Event Sourcing", "事件溯源", "用不可变事件序列重建状态，便于审计。"),
    ],
    250: [
        ("KnowledgeBaseAgent", "知识库 Agent", "封装上传/索引/检索生命周期的 Agent 基类。"),
        ("ToolResult", "工具结果", "Part 7 统一的 success/data/error 返回形。"),
    ],
    251: [
        ("交叉验证", "Cross Verification", "多来源信息对照，标记冲突与置信度。"),
        ("synthesize", "综合工具", "把多条要点合并成带结构的报告。"),
    ],
    252: [
        ("PermissionLevel", "权限级别", "AUTO 自动执行，CONFIRM 需人工确认。"),
        ("退款闸门", "Refund Gate", "高风险客服动作必须 HITL 后再执行。"),
    ],
    253: [
        ("parse_diff", "Diff 解析", "从 unified diff 提取变更文件与代码块。"),
        ("lint_chunk", "分块检查", "大 PR 按块静态分析，避免上下文溢出。"),
    ],
    254: [
        ("高风险操作", "High-risk Ops", "扩容、清缓存等须确认且可审计的运维动作。"),
        ("OpsAgent", "运维 Agent", "在权限边界内执行基础设施变更的 Agent。"),
    ],
}

FLOW_02_INSERT: dict[int, str] = {
    237: """
读下图时，看 Memory 删除管道五步：创建→标记删除→清向量/缓存→备份失效→审计留痕。

![Memory 隐私与删除流程](../image/memory-privacy-deletion/02-memory-privacy-deletion-flow.png)

对照上图：删除不是单表 `DELETE`——要编排主库、向量索引、缓存与备份；Outbox 保证各系统最终一致。
""",
    239: """
读下图时，看 Query Planning 五步：理解问题→拆子问题→选数据源→生成检索查询→输出执行计划。

![RAG Agent 的 Query Planning流程](../image/query-planning-rag-agent/02-query-planning-rag-agent-flow.png)

对照上图：每个子问题都要绑定数据源与过滤条件；计划输出的是可执行检索指令，不是改写后的单句。
""",
    240: """
读下图时，看多步检索循环：接收输入→校验决策→执行检索→记录观测→输出或进入下一轮。

![多步检索执行流程](../image/multi-step-retrieval-agent/02-multi-step-retrieval-agent-flow.png)

对照上图：后一步查询由前一步 evidence 驱动；每轮应产生新 evidence_id，否则触发饱和停止（见 §先错对对）。
""",
}

# §怎么做 开头术语速查（叙事篇）
HOWTO_TERM_TABLE: dict[int, str] = {
    237: """
### 本节术语速查

| 术语 | 通俗说 |
|------|--------|
| 删除管道 | 跨主库/向量/缓存/备份的编排清理，不是一条 SQL |
| Outbox | 先记待删除再异步清各系统，失败可重试 |
| 软删除 vs 硬删除 | 先对用户不可见，再物理清除各副本 |

""",
    238: """
### 本节术语速查

| 术语 | 通俗说 |
|------|--------|
| Query Planning | 拆子问题并选数据源，不是改写一句话 |
| Sufficiency Check | 证据够不够，对比类必须两侧齐 |
| Evidence Store | 所有检索片段的仓库，引用指回这里 |
| Budget Controller | 检索次数/条数/耗时的硬上限 |

""",
    239: """
### 本节术语速查

| 术语 | 通俗说 |
|------|--------|
| Query Planning | 输出多份子查询计划，每份含数据源与 filters |
| expected_evidence | 定义「什么叫找到了」，供充分性判断 |
| RRF | 多路检索结果按排名融合 |

""",
    240: """
### 本节术语速查

| 术语 | 通俗说 |
|------|--------|
| 多步检索 | 下一步查什么由上一步证据决定 |
| 证据饱和 | 新一轮没有新 evidence 就应停或换 query |
| 查询依赖 | B 的检索词依赖 A 的结果 |

""",
}

# 术语通俗说（与专业定义区分）
TONGSU_SHORT: dict[str, str] = {
    "Query Planning": "像旅行规划师列行程，不是把一句话改写得更长",
    "RRF": "把几份检索榜单合并成一份更稳的总榜",
    "Sufficiency Check": "证据没齐就别急着生成答案",
    "多步检索": "走一步看一步，下一步查什么看上一步线索",
    "证据饱和": "新一轮检索没捞到新东西就该停",
    "查询依赖": "B 题怎么查要等 A 题的结果",
    "tool_calls": "模型一次可点多个工具按钮",
    "检索工具": "把查库封装成和普通工具一样的函数",
    "工具循环": "调工具→看结果→再想→再调，直到够用",
    "Citation": "答案里的脚注，必须指回证据原文",
    "证据支持度": "这句话证据里到底有没有说",
    "修正轮": "验证失败后按证据重写或承认不确定",
    "Trace": "全程录像，方便回放查哪一步错了",
    "根因分层": "先判断错在规划、检索还是生成",
    "回归集": "修完 bug 反复跑的错题本",
    "Checkpoint": "游戏存档，能恢复步骤和预算",
    "恢复点": "读档后从哪一步接着干",
    "Activity": "真正干活的副作用步骤，可重试",
    "Workflow": "编排逻辑本身，进程死了也能续",
    "删除管道": "跨库清理的流水线，不是一条 SQL",
    "Outbox": "先记待办再异步清，失败能重试",
}
