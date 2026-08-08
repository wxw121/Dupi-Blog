"""Tutorial 214 — RAG to Agent minimal evolution (stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    goal: str
    steps_taken: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    done: bool = False
    result: str = ""


def rag_answer(query: str, documents: list[str]) -> str:
    relevant = [d for d in documents if query.lower() in d.lower()]
    context = "\n".join(relevant[:3])
    return f"根据文档：\n{context}\n\n回答：这是关于「{query}」的信息。"


class MinimalAgent:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.tools = {
            "search": self._tool_search,
            "calculate": self._tool_calculate,
            "answer": self._tool_answer,
        }

    def run(self, goal: str, max_steps: int = 5) -> AgentState:
        state = AgentState(goal=goal)
        for _ in range(max_steps):
            if "计算" in goal:
                state.steps_taken.append("calculate")
                state.result = self._tool_calculate(goal)
                state.done = True
                break
            state.steps_taken.append("search")
            obs = self._tool_search(goal)
            state.observations.append(obs)
            state.steps_taken.append("answer")
            state.result = self._tool_answer(obs)
            state.done = True
            break
        return state

    def _tool_search(self, query: str) -> str:
        rel = [d for d in self.documents if any(w in d.lower() for w in query.lower().split())]
        return "\n".join(rel[:2]) if rel else "未找到"

    def _tool_calculate(self, expr: str) -> str:
        import re

        nums = [int(n) for n in re.findall(r"\d+", expr)]
        if "+" in expr and len(nums) >= 2:
            return str(sum(nums))
        return "无法解析"

    def _tool_answer(self, text: str) -> str:
        return text


def main() -> None:
    docs = ["Python 是一种解释型编程语言", "Agent 是能自主决策的系统"]
    print(rag_answer("Python", docs))
    st = MinimalAgent(docs).run("什么是 Agent？")
    print(st.result)
    print("OK — 214 transition demo")


if __name__ == "__main__":
    main()
