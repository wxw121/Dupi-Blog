"""demo_tool_rag.py — 工具增强 RAG 最小示例"""
import json
from openai import OpenAI

client = OpenAI()

DOCS = {
    "转化率": "转化率 = 成交客户数 / 总线索数 × 100%",
}


def knowledge_search(query: str) -> str:
    for k, v in DOCS.items():
        if k in query:
            return v
    return "未找到相关文档"


def calculator(expression: str) -> str:
    import ast
    import operator

    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_eval(node.operand))
        raise ValueError("unsupported")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        return str(_eval(tree.body))
    except Exception as e:
        return f"Error: {e}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "knowledge_search",
            "description": "检索内部知识库，查定义、政策等",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "数学计算，输入表达式如 (120/500)*100",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]

HANDLERS = {"knowledge_search": knowledge_search, "calculator": calculator}


def answer(question: str) -> None:
    messages = [
        {"role": "system", "content": "你是数据分析助手。算数必须用 calculator，查定义用 knowledge_search。"},
        {"role": "user", "content": question},
    ]
    for _ in range(5):
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=TOOLS, temperature=0,
        )
        msg = resp.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            print("回答：", msg.content)
            return
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = HANDLERS[tc.function.name](**args)
            print(f"工具 {tc.function.name}({args}) → {result}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})


if __name__ == "__main__":
    answer("华东成交120/总线索500，华南95/380，转化率谁高？高多少个百分点？")
