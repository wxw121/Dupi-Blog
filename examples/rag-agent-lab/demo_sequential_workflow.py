"""demo_sequential_workflow.py — 244 顺序链最小示例（无需 LLM）"""
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class StepResult:
    step_name: str
    output: Any
    success: bool
    error: str = ""


class SequentialWorkflow:
    def __init__(self, name: str):
        self.name = name
        self.steps: list[tuple[str, Callable]] = []

    def add_step(self, name: str, handler: Callable):
        self.steps.append((name, handler))
        return self

    def run(self, initial_input: Any) -> list[StepResult]:
        results, current = [], initial_input
        for step_name, handler in self.steps:
            try:
                current = handler(current)
                results.append(StepResult(step_name, current, True))
            except Exception as e:
                results.append(StepResult(step_name, None, False, str(e)))
                break
        return results


def analyze(text: str) -> dict:
    return {"intent": "query", "entities": ["产品A"], "text": text}


def retrieve(ctx: dict) -> list:
    return [{"content": f"关于{ctx['entities'][0]}的使用说明..."}]


def generate(docs: list) -> str:
    return f"基于 {len(docs)} 篇文档的回答：{docs[0]['content']}"


if __name__ == "__main__":
    workflow = SequentialWorkflow("rag-pipeline")
    workflow.add_step("analyze", analyze).add_step("retrieve", retrieve).add_step("generate", generate)
    for r in workflow.run("产品A怎么用？"):
        print(r.step_name, "OK" if r.success else f"FAIL: {r.error}", "->", r.output)
