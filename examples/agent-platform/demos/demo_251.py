"""Tutorial 251 — Research Agent (extends 250 shared base)."""

from __future__ import annotations

from demos.demo_250 import KnowledgeBaseAgent
from shared.types import ToolResult


class ResearchAgent(KnowledgeBaseAgent):
    def synthesize(self, notes: list[str]) -> ToolResult:
        body = "\n".join(f"- {n}" for n in notes)
        return ToolResult(success=True, data={"report": f"## 研究摘要\n{body}"})

    def run_research(self, topic: str) -> None:
        self.register_tool("synthesize", self.synthesize)
        up = self.run_tool("upload", title=topic, content=f"{topic} 要点一。\n\n{topic} 要点二。")
        self.run_tool("index", doc_id=up.data["doc_id"])
        hits = self.run_tool("search", query=topic).data or []
        rep = self.run_tool("synthesize", notes=hits)
        print(rep.data["report"])


def main() -> None:
    ResearchAgent().run_research("Agentic RAG")
    print("OK — ResearchAgent (251)")


if __name__ == "__main__":
    main()
