"""temporal_minimal.py — 247 最小 Temporal 验证（需 Docker Temporal Server）"""
import asyncio
import uuid
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class RetrievalInput:
    query: str


@activity.defn
async def retrieve_documents(inp: RetrievalInput) -> list[str]:
    return [f"mock doc about {inp.query}"]


@activity.defn
async def generate_answer(query: str, docs: list[str]) -> str:
    return f"Answer for {query}: {docs[0]}"


@workflow.defn
class RAGWorkflow:
    @workflow.run
    async def run(self, query: str) -> str:
        docs = await workflow.execute_activity(
            retrieve_documents,
            RetrievalInput(query),
            start_to_close_timeout=timedelta(seconds=10),
        )
        return await workflow.execute_activity(
            generate_answer,
            args=[query, docs],
            start_to_close_timeout=timedelta(seconds=10),
        )


async def main():
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="rag-agent-queue",
        workflows=[RAGWorkflow],
        activities=[retrieve_documents, generate_answer],
    ):
        handle = await client.start_workflow(
            RAGWorkflow.run,
            "什么是 RAG？",
            id=f"rag-{uuid.uuid4()}",
            task_queue="rag-agent-queue",
        )
        print(await handle.result())


if __name__ == "__main__":
    asyncio.run(main())
