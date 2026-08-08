"""Series-wide term lexicon for body first-use scanning (214-254)."""

from __future__ import annotations

# term -> (english_label, definition, tongsu, introduced_in_doc)
# introduced_in_doc: 首次应在该篇文首术语块解释；更早篇目出现则视为沿用。
TERM_LEXICON: dict[str, tuple[str, str, str, int]] = {}

def _add(term: str, en: str, defn: str, tongsu: str, doc: int) -> None:
    if term not in TERM_LEXICON:
        TERM_LEXICON[term] = (en, defn, tongsu, doc)


# Part 1
_add("RAG", "Retrieval-Augmented Generation", "检索增强生成架构", "先查资料再让模型回答", 214)
_add("Agent", "智能体", "能感知、决策并执行工具的自主系统", "拿到目标后自己多步尝试", 214)
_add("工具", "Tool", "Agent 可调用的外部能力", "搜索、算数、写库等办事能力", 214)
_add("Workflow", "工作流", "预定义步骤与分支的编排", "开发者写死的流水线", 215)
_add("Chatbot", "聊天机器人", "以对话为主的问答系统", " mainly 被动问答", 215)

# Part 2
_add("Tool Calling", "工具调用", "模型输出结构化工具名与参数", "给助理一张办事清单", 218)
_add("JSON Schema", "JSON 模式", "描述 JSON 参数形状的契约", "表格模板，填错退回", 218)
_add("ToolRegistry", "工具注册表", "集中登记工具定义与权限", "工具箱目录册", 218)
_add("ToolExecutor", "工具执行器", "校验并执行工具调用的组件", "真正动手干活的执行层", 218)
_add("Pydantic", "数据校验库", "用类型声明校验数据结构", "自动检查参数形状", 219)
_add("ToolResult", "工具结果", "统一的 success/data/error 返回", "模型读得懂的办事回执", 220)
_add("幂等键", "Idempotency Key", "标识同一业务请求的唯一键", "重试不会重复扣款", 223)
_add("HITL", "Human-in-the-Loop", "高风险操作需人工确认", "敏感动作先问人", 224)
_add("CONFIRM", "需确认级别", "工具调用前暂停等人批准", "默认先问再干", 224)
_add("RBAC", "基于角色的访问控制", "按角色授予工具权限", "职位决定能调什么", 225)
_add("ABAC", "基于属性的访问控制", "按用户与资源属性动态授权", "比固定角色更细", 225)

# Part 3
_add("OTA 循环", "Observe-Think-Act", "观察-思考-行动的 Agent 主循环", "看一眼→想→动手→再看", 226)
_add("ReAct", "Reasoning + Acting", "推理与行动交替的 Agent 模式", "边想边做边看结果", 227)
_add("Plan-and-Execute", "计划与执行", "先列计划再逐步执行", "先画路线图再开车", 228)
_add("Reflection", "反思", "生成后自检并修正", "写完让编辑挑错", 229)
_add("Reflector", "反思器", "挑 Generator 错误的组件", "专门找茬的编辑", 229)
_add("Generator", "生成器", "产出初稿的组件", "先写一版的作者", 229)

# Part 4
_add("工作记忆", "Working Memory", "当前任务的中间结果", "任务草稿纸", 232)
_add("会话状态", "Session State", "本轮对话槽位与进度", "柜台登记表", 233)
_add("长期记忆", "Long-term Memory", "跨会话用户偏好与事实", "客户档案柜", 234)
_add("PII", "个人可识别信息", "可识别个人的敏感字段", "姓名电话证件号等", 235)
_add("Outbox", "发件箱模式", "异步可靠投递的出站表", "先记待办再慢慢清", 237)

# Part 5 Agentic RAG
_add("Agentic RAG", "自主检索增强", "由证据驱动的多步检索决策循环", "侦探式查案", 238)
_add("Query Planning", "查询规划", "拆子问题并选数据源与过滤", "旅行规划师列行程", 238)
_add("Evidence", "证据", "可引用的检索原文片段", "卷宗复印件", 238)
_add("Sufficiency Check", "充分性检查", "判断证据是否够回答", "证据没齐别生成", 238)
_add("RRF", "Reciprocal Rank Fusion", "多路检索按排名融合", "多份榜单合成总榜", 239)
_add("多步检索", "Multi-Step Retrieval", "后步查询依赖前步证据", "走一步看一步", 240)
_add("证据饱和", "Evidence Saturation", "新检索无新 evidence 的状态", "捞不出新线索就该停", 240)
_add("tool_calls", "工具调用列表", "模型请求的工具调用批次", "一次可点多个工具", 241)
_add("Citation", "引用", "指向证据的标注", "答案脚注", 242)
_add("Trace", "执行轨迹", "全链路可回放记录", "办案全程录像", 243)

# Part 6
_add("FSM", "有限状态机", "用状态转移约束流程", "红绿灯式流程", 245)
_add("Checkpoint", "检查点", "持久化中间执行状态", "游戏存档点", 246)
_add("Temporal", "Temporal", "持久化工作流执行平台", "进程死了任务不死", 247)
_add("Activity", "活动", "有副作用的可重试工作单元", "真正干活的步骤", 247)
_add("Event Sourcing", "事件溯源", "用事件序列重建状态", "账本式不可篡改记录", 249)

# Part 7
_add("KnowledgeBaseAgent", "知识库 Agent", "管理上传索引检索的 Agent", "知识库管家", 250)
_add("PermissionLevel", "权限级别", "工具自动/需确认等级", "AUTO 与 CONFIRM 分级", 252)

# Aliases (same introduced_in as canonical)
ALIASES: dict[str, str] = {
    "Query Rewriting": "Query Planning",
    "Human-in-the-Loop": "HITL",
    "Idempotency Key": "幂等键",
    "Multi-Step Retrieval": "多步检索",
    "Tool Loop": "tool_calls",
    "Retrieval Tool": "tool_calls",
    "OTA": "OTA 循环",
    "Observe-Think-Act": "OTA 循环",
}

# 系列前驱篇已充分解释，后续篇出现不记轻微
SERIES_REUSE_OK: set[str] = {
    "RAG",
    "Agent",
    "工具",
    "Workflow",
    "Chatbot",
    "LLM",
    "JSON",
    "API",
}

SKIP_TERMS: set[str] = {
    "Python",
    "HTTP",
    "SDK",
    "Docker",
    "Redis",
    "SQL",
    "GDPR",
    "OK",
    "Part",
    "Level",
    "demo",
    "main",
    "True",
    "False",
    "None",
}
