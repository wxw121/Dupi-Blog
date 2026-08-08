"""Tutorial 250 — Knowledge Base Agent demo."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from shared.base import BaseAgent
from shared.types import AgentTrace, ToolResult


class DocState(str, Enum):
    UPLOADED = "uploaded"
    INDEXED = "indexed"
    FAILED = "failed"


@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    state: DocState = DocState.UPLOADED
    chunks: list[str] = field(default_factory=list)


class KnowledgeBaseAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self.documents: dict[str, Document] = {}
        self.vector_store: dict[str, list[str]] = {}
        self.register_tool("upload", self.upload)
        self.register_tool("index", self.index_doc)
        self.register_tool("search", self.search)

    def upload(self, title: str, content: str) -> ToolResult:
        doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        self.documents[doc_id] = Document(doc_id=doc_id, title=title, content=content)
        return ToolResult(success=True, data={"doc_id": doc_id})

    def index_doc(self, doc_id: str) -> ToolResult:
        doc = self.documents.get(doc_id)
        if not doc:
            return ToolResult(success=False, error="not found")
        doc.chunks = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
        doc.state = DocState.INDEXED
        self.vector_store[doc_id] = doc.chunks
        return ToolResult(success=True, data={"chunks": len(doc.chunks)})

    def search(self, query: str) -> ToolResult:
        hits: list[str] = []
        for chunks in self.vector_store.values():
            hits.extend(c for c in chunks if query.lower() in c.lower())
        return ToolResult(success=True, data=hits[:3])

    def run(self, goal: str) -> AgentTrace:
        self.trace = AgentTrace(goal=goal)
        up = self.run_tool("upload", title="FAQ", content="Agent 是能自主决策的系统。\n\nRAG 是检索增强生成。")
        doc_id = up.data["doc_id"]
        self.run_tool("index", doc_id=doc_id)
        sr = self.run_tool("search", query="Agent")
        print("upload:", up)
        print("search:", sr)
        return self.trace


def main() -> None:
    agent = KnowledgeBaseAgent()
    agent.run("索引并搜索知识库")
    print("OK — KnowledgeBaseAgent (250)")


if __name__ == "__main__":
    main()
