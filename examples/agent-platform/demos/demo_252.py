"""Tutorial 252 — Customer Support Agent with mock HITL."""

from __future__ import annotations

from shared.base import BaseAgent
from shared.types import AgentTrace, PermissionLevel, ToolResult


class SupportAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self.register_tool("lookup_order", self.lookup_order, PermissionLevel.AUTO)
        self.register_tool("refund", self.refund, PermissionLevel.CONFIRM)

    def lookup_order(self, order_id: str) -> ToolResult:
        return ToolResult(success=True, data={"order_id": order_id, "status": "shipped"})

    def refund(self, order_id: str) -> ToolResult:
        return ToolResult(success=True, data={"refunded": order_id})

    def run(self, goal: str) -> AgentTrace:
        self.trace = AgentTrace(goal=goal)
        order = self.run_tool("lookup_order", order_id="ORD-1")
        print("lookup:", order)
        if self.permissions["refund"] == PermissionLevel.CONFIRM:
            print("[HITL] 等待人工确认退款…（demo 自动批准）")
        refund = self.run_tool("refund", order_id="ORD-1")
        print("refund:", refund)
        return self.trace


def main() -> None:
    SupportAgent().run("处理退款")
    print("OK — SupportAgent (252)")


if __name__ == "__main__":
    main()
