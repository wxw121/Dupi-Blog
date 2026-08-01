---
title: "工具增强 RAG：让 Agent 调用外部工具"
slug: tool-augmented-rag
date: 2025-05-22
tags: [AI, RAG, Agent, Tool Use, LLM]
category: ai-ml
description: "RAG Agent 不只是检索文档——还能调用计算器、数据库、API、代码执行器等外部工具，实现真正的智能问答。"
---

## 学习目标

读完本篇，你能：

1. 解释「工具增强 RAG」与纯文档检索的分工边界
2. 用 JSON Schema 定义工具，并注册到 `ToolRegistry`
3. 实现 Agent 主循环：LLM 决定调哪个工具、把结果塞回对话
4. 跑通 §最小可运行示例（计算器 + mock 检索），完成一次带工具调用的问答

## 前置阅读

- **218 工具调用基础**（系列）：Function Calling 的基本概念
- **239 / 240**：检索增强策略；本篇把「检索」也封装成工具之一
- OpenAI API 的 `tools` 参数

## 环境要求

```bash
pip install openai requests
# 可选：pip install langchain langchain-openai matplotlib
```

- Python 3.10+
- `OPENAI_API_KEY`

## 本文边界

| 本篇讲 | 本篇不讲 |
|--------|----------|
| 工具注册、权限、重试、检索-as-tool | 查询分解策略 → **239** |
| 计算器 / SQL / API / 代码执行等工具 | 引用验证 → **242** |
| MCP 适配思路 | MCP 完整实战部署 |

## 动手路径

| 步骤 | 章节 | 交付物 |
|------|------|--------|
| 1 | §最小可运行示例 | 跑通 calculator + knowledge_search |
| 2 | §工具注册表 | 理解 JSON Schema 参数定义 |
| 3 | §Agent 主循环 | 理解 tool_calls 消息流 |
| 4 | §安全控制 | 配置角色权限与 SQL 校验 |
| 5 | §实战案例 | 理解数据分析类问题的工具链 |

> **可运行代码**：[`examples/rag-agent-lab/`](../../../examples/rag-agent-lab/) — `python main.py 241`

## 为什么 RAG 需要工具

**工具增强 RAG**（Tool-Augmented RAG）：在检索文档之外，让 Agent 还能调用计算器、数据库、API 等外部能力。
通俗说：RAG 负责「查资料」，工具负责「算数、查实时数据、画图」——各干各的。

**Function Calling**（函数调用）：LLM 不直接执行代码，而是输出「要调哪个函数、参数是什么」；你的程序执行后把结果还给 LLM。
通俗说：LLM 是指挥官，工具是士兵。

用户问："我们上个月的销售额比上上个月增长了多少百分比？"

纯文档检索能找到销售报告，但：
- 计算增长率需要**计算器**
- 实时数据需要查**数据库**
- 最新汇率需要调**API**
- 数据可视化需要**代码执行器**

工具增强 RAG = 检索能力 + 工具调用能力。

## 架构设计

读下图时，注意 Agent Loop 的四步：**分析 → 检索背景 → 调工具拿精确数据 → 综合回答**。检索和工具调用都由 LLM 按需在循环中触发。

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────────┐
│           Tool-Augmented RAG Agent              │
│                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 检索工具 │  │ 计算工具 │  │ API工具  │        │
│  └─────────┘  └─────────┘  └─────────┘        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 数据库   │  │ 代码执行 │  │ 图表生成 │        │
│  └─────────┘  └─────────┘  └─────────┘        │
│                                                 │
│  Agent Loop:                                    │
│  1. 分析问题 → 需要哪些工具？                    │
│  2. 检索文档 → 获取背景知识                      │
│  3. 调用工具 → 获取精确数据/计算结果             │
│  4. 综合所有信息 → 生成回答                      │
└─────────────────────────────────────────────────┘
```

## 最小可运行示例

下面演示「计算器 + 知识检索」两个工具，无需真实数据库。

- **前置**：`pip install openai`，设置 `OPENAI_API_KEY`
- **预期**：LLM 先检索「转化率定义」，再调计算器算百分比

```python
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
    import ast, operator
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg}

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
    {"type": "function", "function": {
        "name": "knowledge_search",
        "description": "检索内部知识库，查定义、政策等",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "calculator",
        "description": "数学计算，输入表达式如 (120/500)*100",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string"}}, "required": ["expression"]},
    }},
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
```

## 工具定义

> **阅读顺序**：建议先跑通上面示例，再阅读下面完整的 `ToolRegistry` 实现。

### 工具注册表

`ToolRegistry` 把工具名、JSON Schema 参数、处理函数绑在一起，并生成 OpenAI `tools` 列表。

```python
from dataclasses import dataclass
from typing import Callable, Any
import json


@dataclass
class ToolDefinition:
    """工具定义。"""
    name: str
    description: str
    parameters: dict  # JSON Schema
    handler: Callable
    requires_auth: bool = False
    timeout_seconds: int = 30


class ToolRegistry:
    """工具注册表。"""
    
    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition):
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> ToolDefinition | None:
        return self.tools.get(name)
    
    def get_openai_schema(self) -> list[dict]:
        """生成 OpenAI function calling 格式的工具列表。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in self.tools.values()
        ]
    
    def execute(self, name: str, arguments: dict) -> Any:
        """执行工具。"""
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool.handler(**arguments)
```

### 常用工具实现

下面实现几类常见工具。**计算器**用 `ast` 解析表达式，避免 `eval()` 的安全风险（见 §安全控制）。

```python
import ast
import operator
import requests
import sqlite3

_CALC_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _CALC_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _CALC_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


def calculator(expression: str) -> str:
    """安全计算器（仅支持四则运算与括号）。"""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: invalid characters"
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        return str(_safe_eval(tree.body))
    except Exception as e:
        return f"Error: {e}"


# ✗ 错误写法：eval(expression) — 即使限制字符集，仍有注入风险
# ✓ 正确写法：用 ast 只解析数学运算节点


def sql_query(query: str, database: str = "analytics.db") -> str:
    """执行 SQL 查询（只读）。"""
    # 安全检查：只允许 SELECT
    if not query.strip().upper().startswith("SELECT"):
        return "Error: only SELECT queries allowed"
    
    try:
        conn = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        # 格式化结果
        result = [columns]
        result.extend(rows[:20])  # 限制返回行数
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return f"Error: {e}"


def web_api(url: str, method: str = "GET", params: dict = None) -> str:
    """调用外部 API。"""
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            timeout=10,
        )
        return response.text[:2000]
    except Exception as e:
        return f"Error: {e}"


def code_executor(code: str, language: str = "python") -> str:
    """执行代码片段（教学示例，生产环境请用 Docker 沙箱）。"""
    # ⚠️ 以下为简化演示，存在安全风险；生产环境见 §安全控制 的 Docker 沙箱方案
    import subprocess
    import tempfile
    import os
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout[:2000]
        if result.stderr:
            output += f"\nSTDERR: {result.stderr[:500]}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: execution timeout"
    finally:
        os.unlink(temp_path)


def chart_generator(data: str, chart_type: str = "bar",
                    title: str = "") -> str:
    """生成图表（返回文件路径）。"""
    import matplotlib.pyplot as plt
    
    parsed_data = json.loads(data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if chart_type == "bar":
        ax.bar(parsed_data["labels"], parsed_data["values"])
    elif chart_type == "line":
        ax.plot(parsed_data["labels"], parsed_data["values"])
    elif chart_type == "pie":
        ax.pie(parsed_data["values"], labels=parsed_data["labels"])
    
    ax.set_title(title)
    
    output_path = f"/tmp/chart_{hash(title) % 10000}.png"
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    return f"Chart saved to: {output_path}"
```

### 注册所有工具

```python
def create_tool_registry() -> ToolRegistry:
    """创建并注册所有工具。"""
    registry = ToolRegistry()
    
    registry.register(ToolDefinition(
        name="calculator",
        description="执行数学计算。输入数学表达式，返回计算结果。",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '(100-80)/80*100'"
                }
            },
            "required": ["expression"]
        },
        handler=calculator,
    ))
    
    registry.register(ToolDefinition(
        name="sql_query",
        description="在分析数据库上执行只读 SQL 查询。",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SELECT SQL 查询语句"
                }
            },
            "required": ["query"]
        },
        handler=sql_query,
    ))
    
    registry.register(ToolDefinition(
        name="web_api",
        description="调用外部 HTTP API 获取实时数据。",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API URL"},
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "params": {"type": "object", "description": "查询参数"},
            },
            "required": ["url"]
        },
        handler=web_api,
    ))
    
    registry.register(ToolDefinition(
        name="code_executor",
        description="执行 Python 代码片段，用于数据处理和分析。",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python 代码"},
            },
            "required": ["code"]
        },
        handler=code_executor,
    ))
    
    registry.register(ToolDefinition(
        name="chart_generator",
        description="根据数据生成图表。",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "JSON 数据 {labels:[], values:[]}"},
                "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                "title": {"type": "string"},
            },
            "required": ["data"]
        },
        handler=chart_generator,
    ))
    
    return registry
```

## Agent 主循环

`ToolAugmentedRAG` 把检索器封装进工具注册表（`knowledge_search`），由 LLM 在循环中决定何时检索、何时调其他工具。构造时需传入已注册 `knowledge_search` 的 `ToolRegistry`。

```python
from openai import OpenAI

client = OpenAI()


class ToolAugmentedRAG:
    """工具增强 RAG Agent。"""
    
    def __init__(self, tool_registry: ToolRegistry, max_iterations: int = 5):
        self.tools = tool_registry
        self.max_iterations = max_iterations
    
    def answer(self, question: str) -> dict:
        """完整的工具增强 RAG 流程。"""
        
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": question},
        ]
        
        tool_results = []
        
        for iteration in range(self.max_iterations):
            # LLM 决策：是否需要调用工具
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools.get_openai_schema(),
                tool_choice="auto",
                temperature=0,
            )
            
            msg = response.choices[0].message
            messages.append(msg)
            
            # 如果没有工具调用，说明 LLM 准备好回答了
            if not msg.tool_calls:
                return {
                    "answer": msg.content,
                    "tool_calls": tool_results,
                    "iterations": iteration + 1,
                }
            
            # 执行工具调用
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                # 执行
                result = self.tools.execute(func_name, func_args)
                
                tool_results.append({
                    "tool": func_name,
                    "args": func_args,
                    "result": str(result)[:500],
                })
                
                # 把结果加入消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
        
        # 达到最大迭代，强制生成回答
        messages.append({
            "role": "user",
            "content": "基于以上所有信息，给出最终回答。"
        })
        final = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
        )
        
        return {
            "answer": final.choices[0].message.content,
            "tool_calls": tool_results,
            "iterations": self.max_iterations,
        }
    
    def _system_prompt(self) -> str:
        return """你是一个工具增强的 RAG 助手。你可以：
1. 检索内部知识库获取背景信息
2. 使用计算器做精确计算
3. 查询数据库获取实时数据
4. 调用外部 API 获取最新信息
5. 执行代码做数据分析
6. 生成图表做可视化

工作流程：
1. 先分析问题需要什么信息
2. 检索知识库获取背景
3. 如果需要精确数据，调用相应工具
4. 综合所有信息给出回答

注意：
- 计算必须用计算器，不要心算
- 数据必须查数据库，不要编造
- 如果工具返回错误，尝试修正参数重试"""
```

## 检索作为工具

把向量检索封装成 `knowledge_search` 工具，让 LLM 自己决定何时查文档。`vector_store` 需替换为你的实现（LangChain `similarity_search` 等）。

```python
def make_retrieval_tool(vector_store):
    """工厂函数：绑定 vector_store，避免闭包捕获错误。"""

    def retrieval_tool(query: str, collection: str = "default", top_k: int = 5) -> str:
        results = vector_store.similarity_search(query, k=top_k)
        formatted = []
        for i, doc in enumerate(results):
            formatted.append(
                f"[{i+1}] 来源: {doc.metadata.get('source', '未知')}\n"
                f"{doc.page_content[:300]}"
            )
        return "\n---\n".join(formatted)

    return retrieval_tool


# 注册示例（在 create_tool_registry 中调用）
# registry.register(ToolDefinition(
#     name="knowledge_search",
#     description="在内部知识库中检索相关文档。用于获取背景知识、政策规定、历史数据等。",
#     parameters={...},
#     handler=make_retrieval_tool(vector_store),
# ))
```

下面保留简写版注册片段供参考：

```python
def retrieval_tool(query: str, collection: str = "default",
                   top_k: int = 5) -> str:
    """把检索也封装为工具（需事先注入 vector_store）。"""
    results = vector_store.similarity_search(query, k=top_k)
    
    formatted = []
    for i, doc in enumerate(results):
        formatted.append(
            f"[{i+1}] 来源: {doc.metadata.get('source', '未知')}\n"
            f"{doc.page_content[:300]}"
        )
    
    return "\n---\n".join(formatted)


# 注册检索工具
registry.register(ToolDefinition(
    name="knowledge_search",
    description="在内部知识库中检索相关文档。用于获取背景知识、政策规定、历史数据等。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "检索查询"},
            "collection": {"type": "string", "description": "知识库名称"},
            "top_k": {"type": "integer", "description": "返回结果数", "default": 5},
        },
        "required": ["query"]
    },
    handler=retrieval_tool,
))
```

## 工具选择策略

### 自动路由

```python
class ToolRouter:
    """根据问题类型自动选择工具。"""
    
    ROUTING_RULES = {
        "calculator": ["计算", "多少", "百分比", "增长", "平均", "总计"],
        "sql_query": ["数据库", "查询", "统计", "记录", "表中"],
        "web_api": ["实时", "最新", "当前", "天气", "汇率", "股价"],
        "code_executor": ["分析", "处理", "转换", "格式化", "批量"],
        "chart_generator": ["图表", "可视化", "趋势图", "柱状图", "饼图"],
        "knowledge_search": ["政策", "规定", "文档", "手册", "指南"],
    }
    
    def suggest_tools(self, question: str) -> list[str]:
        """建议使用的工具。"""
        suggestions = []
        for tool, keywords in self.ROUTING_RULES.items():
            if any(kw in question for kw in keywords):
                suggestions.append(tool)
        
        # 默认总是建议知识检索
        if "knowledge_search" not in suggestions:
            suggestions.append("knowledge_search")
        
        return suggestions
```

### 工具链编排

```python
class ToolChain:
    """预定义的工具链（常见任务模式）。"""
    
    CHAINS = {
        "data_analysis": [
            "sql_query",       # 1. 查数据
            "code_executor",   # 2. 分析处理
            "chart_generator", # 3. 可视化
        ],
        "fact_check": [
            "knowledge_search",  # 1. 检索内部知识
            "web_api",           # 2. 验证外部来源
            "calculator",        # 3. 数值验证
        ],
        "report_generation": [
            "sql_query",         # 1. 获取数据
            "knowledge_search",  # 2. 获取背景
            "code_executor",     # 3. 数据处理
            "chart_generator",   # 4. 生成图表
        ],
    }
    
    def get_chain(self, task_type: str) -> list[str]:
        return self.CHAINS.get(task_type, ["knowledge_search"])
    
    def classify_task(self, question: str) -> str:
        """分类任务类型。"""
        if any(w in question for w in ["分析", "趋势", "统计"]):
            return "data_analysis"
        if any(w in question for w in ["验证", "核实", "是否属实"]):
            return "fact_check"
        if any(w in question for w in ["报告", "汇总", "总结"]):
            return "report_generation"
        return "general"
```

## 安全控制

### 工具权限

```python
class ToolPermission:
    """工具权限控制。"""
    
    ROLE_PERMISSIONS = {
        "viewer": ["knowledge_search", "calculator"],
        "analyst": ["knowledge_search", "calculator", "sql_query", "chart_generator"],
        "admin": ["knowledge_search", "calculator", "sql_query", "web_api",
                  "code_executor", "chart_generator"],
    }
    
    def __init__(self, user_role: str):
        self.allowed_tools = set(self.ROLE_PERMISSIONS.get(user_role, []))
    
    def can_use(self, tool_name: str) -> bool:
        return tool_name in self.allowed_tools
    
    def filter_tools(self, registry: ToolRegistry) -> list[dict]:
        """过滤出用户有权限的工具。"""
        return [
            schema for schema in registry.get_openai_schema()
            if schema["function"]["name"] in self.allowed_tools
        ]
```

### 输入验证

```python
class ToolInputValidator:
    """工具输入验证。"""
    
    def validate_sql(self, query: str) -> tuple[bool, str]:
        """SQL 注入防护。"""
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
                     "TRUNCATE", "EXEC", "EXECUTE", "--", ";"]
        upper_query = query.upper()
        for word in forbidden:
            if word in upper_query:
                return False, f"Forbidden keyword: {word}"
        if not upper_query.strip().startswith("SELECT"):
            return False, "Only SELECT allowed"
        return True, ""
    
    def validate_url(self, url: str) -> tuple[bool, str]:
        """URL 白名单验证。"""
        allowed_domains = ["api.internal.com", "data.partner.com"]
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.hostname not in allowed_domains:
            return False, f"Domain not allowed: {parsed.hostname}"
        return True, ""
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """代码安全检查。"""
        forbidden = ["import os", "import sys", "subprocess", "open(",
                     "eval(", "exec(", "__import__", "importlib"]
        for pattern in forbidden:
            if pattern in code:
                return False, f"Forbidden pattern: {pattern}"
        return True, ""
```

## 错误处理与重试

```python
class ToolExecutor:
    """带错误处理和重试的工具执行器。"""
    
    def __init__(self, registry: ToolRegistry, max_retries: int = 2):
        self.registry = registry
        self.max_retries = max_retries
    
    def execute_with_retry(self, tool_name: str, args: dict) -> str:
        """执行工具，失败时让 LLM 修正参数重试。"""
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self.registry.execute(tool_name, args)
                
                # 检查是否是错误结果
                if isinstance(result, str) and result.startswith("Error:"):
                    if attempt < self.max_retries:
                        # 让 LLM 修正参数
                        args = self._fix_args(tool_name, args, result)
                        continue
                    return result
                
                return str(result)
            
            except Exception as e:
                if attempt < self.max_retries:
                    args = self._fix_args(tool_name, args, str(e))
                    continue
                return f"Error after {self.max_retries} retries: {e}"
        
        return "Error: max retries exceeded"
    
    def _fix_args(self, tool_name: str, current_args: dict,
                  error: str) -> dict:
        """让 LLM 根据错误信息修正工具参数。"""
        
        tool = self.registry.get(tool_name)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""工具 {tool_name} 执行失败。
参数：{json.dumps(current_args)}
错误：{error}
工具描述：{tool.description}
参数定义：{json.dumps(tool.parameters)}

请修正参数，输出 JSON。"""
            }],
            temperature=0,
            response_format={"type": "json_object"},
        )
        
        return json.loads(response.choices[0].message.content)
```

## 与 LangChain 集成

动态创建 LangChain 工具时，须用**工厂函数**绑定 handler，避免 for 循环闭包陷阱。

```python
from functools import partial
from langchain.tools import tool as lc_tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


def create_langchain_tools(registry: ToolRegistry):
    """把自定义工具注册表转为 LangChain 工具。"""
    lc_tools = []
    for name, tool_def in registry.tools.items():
        handler = tool_def.handler  # 绑定到局部变量，避免闭包捕获循环变量

        @lc_tool(name=tool_def.name, description=tool_def.description)
        def _wrapper(handler=handler, **kwargs) -> str:
            return str(handler(**kwargs))

        lc_tools.append(_wrapper)
    return lc_tools


def create_langchain_agent(registry: ToolRegistry):
    """创建 LangChain 工具增强 Agent。"""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = create_langchain_tools(registry)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是工具增强的 RAG 助手。先分析问题，按需检索和调用工具，再综合回答。"),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
```

> LangChain 版本差异较大，请以你安装的版本文档为准；核心是 **Prompt 用 ChatPromptTemplate**，工具 handler 用工厂绑定。

## 性能优化

### 工具结果缓存

```python
from functools import lru_cache
import hashlib
import time


class ToolResultCache:
    """工具结果缓存。"""
    
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, tool_name: str, args: dict) -> str | None:
        key = self._make_key(tool_name, args)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["time"] < self.ttl:
                return entry["result"]
            del self.cache[key]
        return None
    
    def set(self, tool_name: str, args: dict, result: str):
        key = self._make_key(tool_name, args)
        self.cache[key] = {"result": result, "time": time.time()}
    
    def _make_key(self, tool_name: str, args: dict) -> str:
        content = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
```

### 并行工具调用

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def parallel_tool_calls(tool_calls: list[dict], registry: ToolRegistry) -> list[str]:
    """并行执行多个工具调用。"""
    
    results = [None] * len(tool_calls)
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                registry.execute,
                tc["name"],
                tc["arguments"]
            ): i
            for i, tc in enumerate(tool_calls)
        }
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result(timeout=30)
            except Exception as e:
                results[idx] = f"Error: {e}"
    
    return results
```

## 监控与日志

```python
import logging

logger = logging.getLogger("tool_rag")


class ToolCallLogger:
    """工具调用日志。"""
    
    def log_call(self, tool_name: str, args: dict, result: str,
                 latency_ms: float, success: bool):
        logger.info(json.dumps({
            "event": "tool_call",
            "tool": tool_name,
            "args": args,
            "result_preview": result[:200],
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": time.time(),
        }, ensure_ascii=False))
    
    def log_agent_run(self, question: str, tool_calls: list,
                      total_latency_ms: float, answer_length: int):
        logger.info(json.dumps({
            "event": "agent_run",
            "question": question[:100],
            "num_tool_calls": len(tool_calls),
            "tools_used": [tc["tool"] for tc in tool_calls],
            "total_latency_ms": total_latency_ms,
            "answer_length": answer_length,
        }, ensure_ascii=False))
```

## 实战案例：企业数据分析助手

### 场景

用户问："对比一下华东和华南区域上季度的客户转化率，哪个更好？给我画个图。"

Agent 的执行过程：

```
Step 1: knowledge_search("客户转化率 计算方式 定义")
  → 找到：转化率 = 成交客户数 / 总线索数 * 100%

Step 2: sql_query("SELECT region, COUNT(CASE WHEN status='won' THEN 1 END) as won, COUNT(*) as total FROM leads WHERE quarter='2025Q1' AND region IN ('华东','华南') GROUP BY region")
  → 结果：华东 won=120, total=500; 华南 won=95, total=380

Step 3: calculator("(120/500)*100")
  → 华东转化率: 24%

Step 4: calculator("(95/380)*100")
  → 华南转化率: 25%

Step 5: chart_generator(data={"labels":["华东","华南"],"values":[24,25]}, chart_type="bar", title="Q1客户转化率对比")
  → 图表已生成

Final Answer: 华南区域上季度客户转化率(25%)略高于华东(24%)...
```

### 完整实现

```python
class EnterpriseAnalyticsAgent(ToolAugmentedRAG):
    """企业数据分析 Agent。"""
    
    def __init__(self, vector_store):
        registry = create_tool_registry()
        # 把检索注册为 knowledge_search 工具
        registry.register(ToolDefinition(
            name="knowledge_search",
            description="在内部知识库中检索相关文档。",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=make_retrieval_tool(vector_store),
        ))
        super().__init__(registry, max_iterations=8)
    
    def analyze(self, question: str, user_role: str = "analyst") -> dict:
        """执行数据分析。"""
        
        # 权限过滤
        permission = ToolPermission(user_role)
        available_tools = permission.filter_tools(self.tools)
        
        # 执行
        result = self.answer(question)
        
        # 记录日志
        logger.info(json.dumps({
            "question": question,
            "role": user_role,
            "tools_used": [tc["tool"] for tc in result["tool_calls"]],
            "iterations": result["iterations"],
        }, ensure_ascii=False))
        
        return result
```

## 工具增强的评估

### 评估维度

| 维度 | 指标 | 目标 |
|------|------|------|
| 工具选择准确率 | 选对工具 / 总调用 | > 90% |
| 参数正确率 | 参数正确 / 总调用 | > 85% |
| 任务完成率 | 成功回答 / 总问题 | > 80% |
| 平均工具调用数 | 每次回答的调用次数 | < 4 |
| 端到端延迟 | 从问题到回答 | < 10s |

### 测试用例

```python
TEST_CASES = [
    {
        "question": "上个月的总销售额是多少？",
        "expected_tools": ["sql_query"],
        "expected_answer_contains": ["销售额", "万元"],
    },
    {
        "question": "今年比去年增长了多少百分比？",
        "expected_tools": ["sql_query", "calculator"],
        "expected_answer_contains": ["%"],
    },
    {
        "question": "画一个各区域销售对比图",
        "expected_tools": ["sql_query", "chart_generator"],
        "expected_answer_contains": ["图表", "png"],
    },
    {
        "question": "我们的退货政策是什么？",
        "expected_tools": ["knowledge_search"],
        "expected_answer_contains": ["退货", "天"],
    },
]
```

## 常见问题

**Q: 工具调用失败怎么办？**

A: 三层处理：① 自动重试（修正参数）；② 降级（用检索替代）；③ 告知用户（说明哪个工具失败了）。

**Q: 如何防止 LLM 滥用工具？**

A: ① 设置每次对话的工具调用上限；② 对昂贵工具（API、代码执行）加确认步骤；③ 监控异常调用模式。

**Q: 工具太多 LLM 选不准怎么办？**

A: ① 工具描述要精准（什么时候用、什么时候不用）；② 先用路由层筛选候选工具（不超过 5 个）；③ 工具分组，按任务类型加载。

**Q: 如何调试工具增强 Agent？**

A: 记录完整的工具调用链：问题→决策→工具→参数→结果→最终回答。每一步都可追溯。用 verbose 模式开发，生产环境只记关键指标。

## MCP（Model Context Protocol）集成

**MCP**（Model Context Protocol，模型上下文协议）：一种标准化方式，让 Agent 发现和调用外部工具服务。
通俗说：工具不再写死在代码里，而是像插件一样注册到 MCP Server，Agent 按需加载。

工具增强 RAG 的最新趋势是用 MCP 统一工具接口：

```python
class MCPToolAdapter:
    """把 MCP Server 的工具适配为 Agent 可用工具。"""
    
    def __init__(self, mcp_client):
        self.client = mcp_client
        self._tools_cache = None
    
    def get_tools(self) -> list[ToolDefinition]:
        """从 MCP Server 获取工具列表。"""
        if self._tools_cache is None:
            mcp_tools = self.client.list_tools()
            self._tools_cache = [
                ToolDefinition(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["inputSchema"],
                    handler=lambda **kwargs, _name=t["name"]: self.client.call_tool(_name, kwargs),
                )
                for t in mcp_tools
            ]
        return self._tools_cache
    
    def register_to(self, registry: ToolRegistry):
        """把 MCP 工具注册到工具注册表。"""
        for tool in self.get_tools():
            registry.register(tool)
```

MCP 的好处：
- 工具以独立进程运行，天然隔离
- 标准协议，不同 Agent 框架都能用
- 工具可以动态发现和加载
- 社区生态丰富（数据库、文件系统、浏览器等）

## 工具增强 vs 纯 RAG 的选择

什么时候用纯 RAG：
- 问题只需要文档知识
- 不需要精确计算
- 不需要实时数据
- 延迟要求极高（< 2s）

什么时候用工具增强：
- 需要精确数值（计算、统计）
- 需要实时/动态数据
- 需要执行操作（不只是查询）
- 需要多源数据聚合
- 需要可视化输出

大多数生产系统是混合的：简单问题走纯 RAG，复杂问题走工具增强。

## 参考资源

- Toolformer: Language Models Can Teach Themselves to Use Tools (2023)
- Gorilla: Large Language Model Connected with Massive APIs (2023)
- OpenAI Function Calling Documentation
- Anthropic Tool Use Guide
- Model Context Protocol Specification (2024)
- LangChain Tools and Agents Documentation

## 工具描述的最佳实践

好的工具描述应该包含：

1. **做什么**：一句话说明功能
2. **什么时候用**：明确的触发条件
3. **什么时候不用**：避免误用
4. **参数说明**：每个参数的含义和示例
5. **返回值说明**：返回什么格式的数据
6. **限制**：超时、频率限制、数据量限制

```python
# 好的工具描述示例
GOOD_DESCRIPTION = """在分析数据库上执行只读 SQL 查询。

使用场景：需要查询销售数据、用户数据、产品数据等结构化数据时。
不适用：查询文档、政策、手册等非结构化内容（用 knowledge_search）。

限制：
- 只支持 SELECT 语句
- 最多返回 100 行
- 查询超时 10 秒
- 可用表：leads, deals, products, users

示例：SELECT region, SUM(amount) FROM deals GROUP BY region
"""
```

工具描述的质量直接决定 LLM 选择工具的准确率。花时间写好描述，比调 prompt 有效得多。

## 附录：工具增强 Agent 检查清单

上线前确认：

- [ ] 所有工具有权限控制
- [ ] SQL 工具有注入防护
- [ ] 代码执行在沙箱中
- [ ] API 调用有白名单
- [ ] 工具调用有频率限制
- [ ] 错误处理覆盖所有工具
- [ ] 日志记录完整调用链
- [ ] 监控告警配置完成
- [ ] 工具描述经过测试验证
- [ ] 端到端测试覆盖主要场景
- [ ] 降级方案（工具不可用时）
- [ ] 用户确认机制（危险操作）

每一项都做到位，才能安心上线。

## 总结

工具增强 RAG 的核心价值：

| 能力 | 纯 RAG | 工具增强 RAG |
|------|--------|-------------|
| 事实查询 | 能回答 | 能回答 |
| 精确计算 | 不可靠 | 精确 |
| 实时数据 | 无法获取 | API/DB 获取 |
| 数据分析 | 无法执行 | 代码执行 |
| 可视化 | 无法生成 | 图表生成 |

**实施建议**（由易到难）：计算器 + SQL → 检索-as-tool → API → 代码执行（风险最高）。

**何时不必用工具增强**：纯文档问答、延迟要求 < 2s、无精确计算/实时数据需求。

**安全永远是第一位**：权限控制、输入验证、沙箱执行。

**系列下一步**：[242 RAG Agent 引用验证](rag-agent-citation-verification) —— 确保回答有据可查。

工具增强 RAG 是 Agent 落地的核心能力。掌握它，你的 AI 应用就超越了 90% 的竞品。

---
*本文代码已在 Python 3.11 + OpenAI API 环境验证。*
