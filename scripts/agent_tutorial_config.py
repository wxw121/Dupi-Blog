"""Per-doc metadata for Agent tutorial (214-254) beginner-tech-blog fixes."""

from __future__ import annotations

from pathlib import Path

# fmt: off
SERIES_DOCS: list[int] = list(range(214, 255))

TIER: dict[int, str] = {
    **{n: "地基篇" for n in range(214, 218)},
    **{n: "主线篇" for n in range(218, 237)},
    237: "收束篇",
    238: "主线篇（概念总览）",
    **{n: "主线篇" for n in range(239, 243)},
    243: "收束篇",
    **{n: "主线篇" for n in range(244, 246)},
    246: "收束篇",
    247: "收束篇",
    248: "主线篇",
    249: "主线篇",
    **{n: "综合实战篇" for n in range(250, 255)},
}

PART: dict[int, str] = {
    **{n: "Part 1" for n in range(214, 218)},
    **{n: "Part 2" for n in range(218, 226)},
    **{n: "Part 3" for n in range(226, 232)},
    **{n: "Part 4" for n in range(232, 238)},
    **{n: "Part 5" for n in range(238, 244)},
    **{n: "Part 6" for n in range(244, 250)},
    **{n: "Part 7" for n in range(250, 255)},
}

# 要不要读 — Part 3 进阶 + Part 4 Memory
OPTIONAL_READ: dict[int, dict[str, str]] = {
    228: {
        "suggest": "复杂多步任务、需要显式计划再执行时",
        "skip": "已用 ReAct 满足需求、任务步骤 ≤3 且固定",
        "return": "ReAct 出现反复试错、token 浪费明显时",
    },
    229: {
        "suggest": "对输出质量敏感（报告、代码、对外文案）",
        "skip": "低延迟聊天、简单工具调用",
        "return": "发现模型「一次生成」错误率高时",
    },
    230: {
        "suggest": "用户目标模糊、需拆成可执行子任务时",
        "skip": "单工具单次调用即可完成的请求",
        "return": "Agent 在复杂任务上步骤混乱时",
    },
    232: {
        "suggest": "准备设计会话状态或长期记忆前",
        "skip": "仅做无状态 RAG 问答",
        "return": "需要区分「上下文 / 状态 / 记忆 / 知识库」时",
    },
    233: {"suggest": "实现多轮对话、工作记忆管理", "skip": "单次问答", "return": "对话丢上下文时"},
    234: {"suggest": "跨会话个性化、用户偏好", "skip": "严格无状态客服", "return": "需要记住用户偏好时"},
    235: {"suggest": "决定什么写入长期记忆", "skip": "只用短期会话", "return": "记忆污染、幻觉记忆时"},
    236: {"suggest": "设计记忆召回策略", "skip": "记忆条目 <10", "return": "召回过多/过少时"},
}

BOUNDARY: dict[int, str] = {
    214: "前驱篇 [201 Agentic RAG](201.agentic-rag-tutorial.md) 与 RAG 系列（检索/生成）。本篇 RAG→Agent 最小演化（Level 0→2）。不讲 LLM API 与生产部署。接续 [215](215.agent-vs-rag-vs-workflow-tutorial.md) 四形态选型。",
    215: "前驱篇 [214](214.rag-to-agent-transition-tutorial.md) 已区分 RAG 与 Agent。本篇 Chatbot/RAG/Workflow/Agent 选型。不讲 LangGraph 等框架安装。接续 [216](216.when-not-to-use-agent-tutorial.md)。",
    216: "前驱篇 [215](215.agent-vs-rag-vs-workflow-tutorial.md) 已能选型。本篇何时不该上 Agent。不讲实现细节。接续 [217](217.enterprise-agent-architecture-overview-tutorial.md)。",
    217: "前驱篇 [214–216](214.rag-to-agent-transition-tutorial.md) 边界与选型。本篇五层企业架构总览。不讲单层完整实现。接续 [218](218.tool-calling-basics-tutorial.md) 工具层。",
    218: "前驱篇 [217](217.enterprise-agent-architecture-overview-tutorial.md) 工具层职责。本篇 `ToolRegistry` + `ToolExecutor`。不讲 OpenAI SDK 专有字段。接续 [219](219.tool-schema-design-tutorial.md)。",
    219: "前驱篇 [218](218.tool-calling-basics-tutorial.md) 注册表与执行器。本篇 Schema 三读者与 Pydantic。不讲各云 function 差异。接续 [220](220.tool-parameter-validation-tutorial.md)。",
    220: "前驱篇 [219](219.tool-schema-design-tutorial.md) Schema 契约。本篇格式/业务/跨字段三层校验。不讲前端表单。接续 [221](221.tool-result-normalization-tutorial.md)。",
    221: "前驱篇 [220](220.tool-parameter-validation-tutorial.md) 入参校验。本篇 `StandardToolResult` 与 `to_llm_string()`。不讲 gRPC/MQ。接续 [222](222.tool-error-timeout-retry-tutorial.md)。",
    222: "前驱篇 [221](221.tool-result-normalization-tutorial.md) 标准返回。本篇超时/退避/熔断/降级。不讲 K8s 网络排障。接续 [223](223.idempotent-agent-tools-tutorial.md)。",
    223: "前驱篇 [222](222.tool-error-timeout-retry-tutorial.md) 重试策略。本篇 idempotency key 与幂等模式。不讲 2PC/Saga 全貌。接续 [224](224.human-in-the-loop-agent-tutorial.md)。",
    224: "前驱篇 [223](223.idempotent-agent-tools-tutorial.md) 可安全重试。本篇 HITL 审批分级。不讲审批 UI/OA。接续 [225](225.agent-tool-permission-boundary-tutorial.md)。",
    225: "前驱篇 [224](224.human-in-the-loop-agent-tutorial.md) 人工闸门。本篇 RBAC/ABAC 与最小权限。不讲 IAM 控制台。接续 [226](226.agent-loop-observe-think-act-tutorial.md) 接入 ACT。",
    226: "前驱篇 [218–225](218.tool-calling-basics-tutorial.md) 工具工程全链。本篇 OTA 循环与 Part 2 继承表。不讲异步细节（见 [222](222.tool-error-timeout-retry-tutorial.md)）。接续 [227](227.react-agent-pattern-tutorial.md)。",
    227: "前驱篇 [226](226.agent-loop-observe-think-act-tutorial.md) OTA 循环。本篇 ReAct 解析。不讲框架封装。接续 [228](228.plan-and-execute-agent-tutorial.md)。",
    228: "前驱篇 [227](227.react-agent-pattern-tutorial.md) ReAct。本篇 Plan-and-Execute。不讲 MCTS/动态重规划。接续 [229](229.reflection-agent-pattern-tutorial.md)。",
    229: "前驱篇 [228](228.plan-and-execute-agent-tutorial.md) 计划驱动。本篇 Generator/Reflector 自检。不讲无限自改。接续 [230](230.task-decomposition-agent-tutorial.md)。",
    230: "前驱篇 [229](229.reflection-agent-pattern-tutorial.md) 质量自检。本篇 Goal/Step/Action 分解。不讲 Multi-Agent。接续 [231](231.agent-stop-condition-tutorial.md)。",
    231: "前驱篇 [226–230](226.agent-loop-observe-think-act-tutorial.md) 循环与规划。本篇停止条件与预算。不讲 RL 探索。接续 [232](232.agent-memory-types-tutorial.md)。",
    232: "前驱篇 [231](231.agent-stop-condition-tutorial.md) 有界循环。本篇五类记忆地图（vs RAG 库）。不讲向量 DDL。接续 [233](233.short-term-agent-memory-tutorial.md)。",
    233: "前驱篇 [232](232.agent-memory-types-tutorial.md) 记忆分类。本篇会话状态与工作记忆。不讲浏览器 Storage。接续 [234](234.long-term-agent-memory-tutorial.md)。",
    234: "前驱篇 [233](233.short-term-agent-memory-tutorial.md) 单会话上下文。本篇跨会话长期记忆。不讲 embedding 微调。接续 [235](235.memory-write-policy-tutorial.md)。",
    235: "前驱篇 [234](234.long-term-agent-memory-tutorial.md) + [220](220.tool-parameter-validation-tutorial.md) 校验。本篇写入策略与 PII 过滤。合规见 [237](237.memory-privacy-deletion-tutorial.md)。接续 [236](236.memory-retrieval-policy-tutorial.md)。",
    236: "前驱篇 [235](235.memory-write-policy-tutorial.md) 写入策略。本篇召回触发与排序注入。混合检索见 RAG 系列。接续 [237](237.memory-privacy-deletion-tutorial.md)。",
    237: "前驱篇 [232–236](232.agent-memory-types-tutorial.md) Memory 读写链。本篇删除管道与隐私。向量库见 RAG 系列。接续 [238](238.agentic-rag-architecture-tutorial.md)。",
    238: "前驱篇 [214](214.rag-to-agent-transition-tutorial.md) + [226–231](226.agent-loop-observe-think-act-tutorial.md) + [237](237.memory-privacy-deletion-tutorial.md)。本篇 Agentic RAG 四组件总览。不讲组件细节。接续 [239–242](239.query-planning-rag-agent-tutorial.md) 与 [`rag-agent-lab`](../examples/rag-agent-lab/)。",
    239: "前驱篇 [238](238.agentic-rag-architecture-tutorial.md) Query Planning 位。本篇子查询拆解与计划校验。代码 `main.py 239`。接续 [240](240.multi-step-retrieval-agent-tutorial.md)。",
    240: "前驱篇 [239](239.query-planning-rag-agent-tutorial.md) 查询规划。本篇多步检索与防循环。代码 `main.py 240`。接续 [241](241.tool-augmented-rag-tutorial.md)。",
    241: "前驱篇 [218–225](218.tool-calling-basics-tutorial.md) 工具 + [239–240](239.query-planning-rag-agent-tutorial.md) 检索。本篇 tool-augmented RAG。不讲 Multi-Agent。代码 `main.py 241`。接续 [242](242.rag-agent-citation-verification-tutorial.md)。",
    242: "前驱篇 [241](241.tool-augmented-rag-tutorial.md) 生成链。本篇引用验证与修正。代码 `main.py 242`。接续 [243](243.rag-agent-bad-case-debugging-tutorial.md)。",
    243: "前驱篇 [239–242](239.query-planning-rag-agent-tutorial.md) Agentic RAG 全链。本篇 trace 反查与根因分层。代码 `main.py 243`。接续 [244](244.agent-workflow-patterns-tutorial.md)。",
    244: "前驱篇 [215](215.agent-vs-rag-vs-workflow-tutorial.md) Workflow + [243](243.rag-agent-bad-case-debugging-tutorial.md) 质量收束。本篇七种编排模式。代码 `main.py 244`。接续 [245](245.state-machine-agent-tutorial.md)。",
    245: "前驱篇 [244](244.agent-workflow-patterns-tutorial.md) 编排模式。本篇 FSM 约束。持久化见 [246–247](246.agent-checkpoint-resume-tutorial.md)。接续 [246](246.agent-checkpoint-resume-tutorial.md)。",
    246: "前驱篇 [245](245.state-machine-agent-tutorial.md) 长流程 FSM。本篇 checkpoint save/load。不讲跨机房容灾。接续 [247](247.durable-agent-execution-tutorial.md)。",
    247: "前驱篇 [246](246.agent-checkpoint-resume-tutorial.md) 手动检查点。本篇 Temporal/持久执行。`temporal_minimal.py`。接续 [248](248.agent-background-job-tutorial.md)。",
    248: "前驱篇 [247](247.durable-agent-execution-tutorial.md) 可靠执行。本篇后台 Worker 与进度推送。不讲 MQ 集群。接续 [249](249.agent-event-driven-architecture-tutorial.md)。",
    249: "前驱篇 [248](248.agent-background-job-tutorial.md) 异步任务。本篇事件总线与 Event Sourcing。接续 [250](250.build-knowledge-base-agent-tutorial.md)。",
    250: "前驱篇 [214–249](214.rag-to-agent-transition-tutorial.md) 全系约束。本篇知识库 Agent（`agent-platform/` 起点）。不讲重复 Part 2。接续 [251–254](251.build-research-agent-tutorial.md)。",
    251: "前驱篇 [250](250.build-knowledge-base-agent-tutorial.md) `shared/`。本篇研究 Agent。`demo_251`。接续 [252](252.build-customer-support-agent-tutorial.md)。",
    252: "前驱篇 [250](250.build-knowledge-base-agent-tutorial.md) + [224](224.human-in-the-loop-agent-tutorial.md) HITL。本篇客服与退款审批。`demo_252`。接续 [253](253.build-code-review-agent-tutorial.md)。",
    253: "前驱篇 [250–252](250.build-knowledge-base-agent-tutorial.md) 平台模式。本篇 diff 分块审查。`demo_253`。接续 [254](254.build-admin-ops-agent-tutorial.md)。",
    254: "前驱篇 [250–253](250.build-knowledge-base-agent-tutorial.md) + [224–225](224.human-in-the-loop-agent-tutorial.md)。本篇运营 Agent，收束 Part 7。`demo_254`。接续系列第二阶段（255+）。",
}

HANDS_ON: dict[int, str] = {}  # populated from agent_tutorial_pass4_data.HANDS_ON_ALL at import

def _load_hands_on() -> dict[int, str]:
    import sys
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from agent_tutorial_pass4_data import HANDS_ON_ALL
        return dict(HANDS_ON_ALL)
    except ImportError:
        return {
            214: "① 读 §最小示例 → ② `python docs/../examples/agent-platform/demos/demo_214.py`（或文内 `demo_transition()`）→ ③ 对照 §工程化版本",
            218: "① 读 §最小示例 → ② 运行 `demo_registry()` → ③ 接 §工具执行器 `demo_executor()`",
            226: "① 读 Part 2 继承表 → ② 运行 §最小示例 `demo_ota_loop()` → ③ 对照 §工程化版本",
            239: "① 读本文架构 → ② `cd examples/rag-agent-lab && python main.py 239` → ③ 回读 §怎么做",
            243: "① `python main.py 243`（无需 API）→ ② 对照 §根因分层表做自检",
            244: "① `python main.py 244` → ② 对照 §七种模式决策表",
            247: "① 读 246 检查点 → ② `python temporal_minimal.py`（需 Docker）",
            250: "① `cd examples/agent-platform && pip install -r requirements.txt` → ② `python -m demos.demo_250` → ③ 251 在此基础上扩展",
        }

HANDS_ON.update(_load_hands_on())

GLOSSARY: dict[int, list[tuple[str, str, str]]] = {
    # (term, english, 通俗说)
    214: [
        ("RAG", "Retrieval-Augmented Generation", "先查资料再让模型回答，像开卷考试。"),
        ("Agent", "智能体", "拿到目标后自己多步尝试、调用工具，直到做完或触发停止。"),
        ("工具", "Tool", "Agent 能调用的外部能力，如搜索、算数、写数据库。"),
    ],
    215: [
        ("Workflow", "工作流", "步骤和分支由开发者写死，像工厂流水线。"),
        ("Chatbot", "聊天机器人", " mainly 一问一答，不主动改外部世界。"),
    ],
    218: [
        ("Tool Calling", "工具调用", "模型输出结构化「要调哪个函数、参数是什么」。"),
        ("JSON Schema", "JSON 模式", "描述参数长什么样的说明书，便于校验。"),
    ],
    226: [
        ("OTA 循环", "Observe-Think-Act", "看一眼环境→想下一步→动手→再看结果，循环直到完成。"),
    ],
    227: [
        ("ReAct", "Reasoning + Acting", "边想边做：先写 Thought，再选 Action，再看 Observation。"),
    ],
    238: [
        ("Agentic RAG", "自主检索增强", "检索几次、查什么由系统根据中间证据决定，不是固定管道。"),
        ("Query Planning", "查询规划", "把复杂问题拆成多个可检索子问题。"),
        ("Evidence", "证据", "检索到的原文片段，生成答案时必须能指回它。"),
    ],
}

# Per-doc mermaid for §最小示例 (replaces misplaced 02-flow image)
MINIMAL_MERMAID: dict[int, str] = {
    214: """```mermaid
flowchart LR
  L0[Level 0 纯 RAG] --> L1[Level 1 路由]
  L1 --> L2[Level 2 最小 Agent 循环]
  L2 -->|观察| O[环境/工具结果]
  O -->|思考| T[选工具或结束]
  T -->|行动| A[search / calculate / answer]
```""",
    226: """```mermaid
flowchart TB
  O[OBSERVE 观察] --> T[THINK 思考]
  T --> A[ACT 执行工具]
  A --> E{EVALUATE 是否完成?}
  E -->|否| O
  E -->|是| OUT[输出结果]
```""",
    218: """```mermaid
sequenceDiagram
  participant LLM
  participant Registry as ToolRegistry
  participant Exec as ToolExecutor
  LLM->>Registry: 选择工具名+参数
  Registry->>Exec: 校验参数
  Exec->>Exec: 执行+超时+审计
  Exec-->>LLM: ToolCallResult
```""",
}

# Post-image conclusions: key = image filename suffix pattern
IMAGE_AFTER: dict[str, str] = {
    "01-": "对照上图：先抓住「要解决什么矛盾」，再读下文机制与代码。",
    "02-": "对照上图：流程图强调能力边界与多步/分支/工具调用——这正是从 RAG 走向 Agent 的动机。",
    "03-": "对照上图：把全篇概念串成一张地图；下一篇会沿其中一条边继续加深。",
}

LAB_FOOTER: dict[int, str] = {
    244: "\n可运行示例：`cd examples/rag-agent-lab && python main.py 244`（无需 API）。\n",
    247: "\n可运行示例：`cd examples/rag-agent-lab && pip install temporalio && python temporal_minimal.py`（需 Docker Temporal）。\n",
}

BLOG_POST: dict[int, str] = {
    239: "239-query-planning-rag-agent.md",
    240: "240-multi-step-retrieval-agent.md",
    241: "241-tool-augmented-rag.md",
    242: "242-rag-agent-citation-verification.md",
    243: "243-rag-agent-bad-case-debugging.md",
    244: "244-agent-workflow-patterns.md",
    245: "245-state-machine-agent.md",
    246: "246-agent-checkpoint-resume.md",
    247: "247-durable-agent-execution.md",
    248: "248-agent-background-job.md",
    249: "249-agent-event-driven-architecture.md",
    250: "250-build-knowledge-base-agent.md",
}

CONCEPT_MAP_TABLE: dict[int, str] = {
    228: """
### 概念地图（ReAct ↔ Plan-and-Execute）

| 你已见过 | 正式名称 | 通俗说 |
|----------|----------|--------|
| 边想边调工具 | ReAct（227） | 走一步看一步，灵活但易绕圈 |
| 先列计划再逐步执行 | Plan-and-Execute | 先画路线图再开车，适合步骤多的任务 |
| §226 OTA 的 THINK | Planning | 决定「下一步干什么」 |
| §226 OTA 的 ACT | Execution | 真正调用工具 |
""",
    232: """
### 概念地图（五类记忆）

| 类型 | 存什么 | 通俗说 | 与 RAG 知识库 |
|------|--------|--------|----------------|
| 工作记忆 | 当前任务中间结果 | 草稿纸 | 不同：不替代文档库 |
| 会话状态 | 本轮对话槽位 | 柜台上的登记表 | 不同 |
| 长期记忆 | 跨会话偏好/事实 | 客户档案 | 不同：主观、可删 |
| 语义记忆 | 抽象经验 | 「这类问题先查订单」 | 可重叠，需权限 |
| 情景记忆（Episodic） | 历史事件轨迹 | 日记 | 用于审计与调试 |
""",
    226: """
### Part 2 能力继承（接入 OTA 的 ACT 阶段）

| Part 2 篇 | 能力 | 在 OTA 哪一步用 |
|-------------|------|-----------------|
| 220 参数校验 | 拦截非法 tool 参数 | ACT 前 |
| 222 重试/超时 | 工具失败恢复 | ACT 中 |
| 223 幂等 | 安全重试 | ACT 中 |
| 224 HITL | 高风险需人工确认 | ACT 前/后 |
| 225 权限边界 | 谁能调什么工具 | ACT 前 |
""",
}

# Files using 是什么/为什么/怎么做 instead of standard sections
NARRATIVE_DOCS: set[int] = {237, 238, 239, 240}
