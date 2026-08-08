"""Tutorial 253 — Code Review Agent."""

from __future__ import annotations

from shared.base import BaseAgent
from shared.types import AgentTrace, ToolResult


class CodeReviewAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self.register_tool("parse_diff", self.parse_diff)
        self.register_tool("lint_chunk", self.lint_chunk)

    def parse_diff(self, diff: str) -> ToolResult:
        files = [ln[4:] for ln in diff.splitlines() if ln.startswith("+++")]
        return ToolResult(success=True, data=files)

    def lint_chunk(self, code: str) -> ToolResult:
        issues = []
        if "eval(" in code:
            issues.append("avoid eval()")
        return ToolResult(success=True, data=issues)

    def run(self, goal: str) -> AgentTrace:
        self.trace = AgentTrace(goal=goal)
        diff = "+++ a/app.py\n+result = eval(user_input)\n"
        files = self.run_tool("parse_diff", diff=diff).data
        issues = self.run_tool("lint_chunk", code=diff).data
        print("files:", files, "issues:", issues)
        return self.trace


def main() -> None:
    CodeReviewAgent().run("审查 PR")
    print("OK — CodeReviewAgent (253)")


if __name__ == "__main__":
    main()
