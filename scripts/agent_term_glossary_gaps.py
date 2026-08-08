"""Append missing glossary entries found by body-term scan."""

from __future__ import annotations

# doc -> list of (term, en, defn, tongsu)
GLOSSARY_GAP_FIX: dict[int, list[tuple[str, str, str, str]]] = {
    224: [
        (
            "HITL",
            "Human-in-the-Loop",
            "高风险或不可逆操作前插入人工审批闸门",
            "敏感动作先问人再执行",
        ),
    ],
    225: [
        (
            "RBAC",
            "Role-Based Access Control",
            "按角色授予工具与资源访问权限",
            "职位决定能调什么工具",
        ),
    ],
    228: [
        (
            "Plan-and-Execute",
            "计划与执行",
            "先由 Planner 产出步骤列表，再由 Executor 逐步调用工具",
            "先画路线图再开车，适合步骤多的任务",
        ),
    ],
    229: [
        (
            "Reflection",
            "反思模式",
            "生成器产出草稿、反思器挑错后再改一版",
            "写完让编辑挑错再改",
        ),
        (
            "Generator",
            "生成器",
            "产出初稿的组件，与 Reflector 配对",
            "先写一版的作者",
        ),
    ],
    238: [
        (
            "Query Planning",
            "查询规划",
            "把复杂问题拆成可检索子问题并选数据源",
            "旅行规划师列行程，不是改写一句话",
        ),
    ],
    247: [
        (
            "Temporal",
            "Temporal",
            "托管长流程、重试与人工等待的持久执行平台",
            "进程死了任务还能续跑的平台",
        ),
    ],
}
