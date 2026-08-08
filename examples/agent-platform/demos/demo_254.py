"""Tutorial 254 — Admin Ops Agent (high-risk confirm)."""

from __future__ import annotations

from shared.base import BaseAgent
from shared.types import AgentTrace, PermissionLevel, ToolResult


class OpsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self.register_tool("scale_service", self.scale_service, PermissionLevel.CONFIRM)
        self.register_tool("purge_cache", self.purge_cache, PermissionLevel.CONFIRM)

    def scale_service(self, replicas: int) -> ToolResult:
        return ToolResult(success=True, data={"replicas": replicas})

    def purge_cache(self, key: str) -> ToolResult:
        return ToolResult(success=True, data={"purged": key})

    def run(self, goal: str) -> AgentTrace:
        self.trace = AgentTrace(goal=goal)
        print("[HITL] 扩容需管理员确认 — demo 自动批准")
        print(self.run_tool("scale_service", replicas=5))
        print(self.run_tool("purge_cache", key="session:*"))
        return self.trace


def main() -> None:
    OpsAgent().run("高峰扩容")
    print("OK — OpsAgent (254)")


if __name__ == "__main__":
    main()
