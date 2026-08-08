"""Minimal agent base — tutorials 250–254 extend this class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from shared.types import AgentTrace, PermissionLevel, ToolResult


class BaseAgent(ABC):
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., ToolResult]] = {}
        self.permissions: dict[str, PermissionLevel] = {}
        self.trace = AgentTrace(goal="")

    def register_tool(
        self,
        name: str,
        fn: Callable[..., ToolResult],
        permission: PermissionLevel = PermissionLevel.AUTO,
    ) -> None:
        self.tools[name] = fn
        self.permissions[name] = permission

    def run_tool(self, name: str, **kwargs: Any) -> ToolResult:
        if name not in self.tools:
            return ToolResult(success=False, error=f"unknown tool: {name}")
        if self.permissions.get(name) == PermissionLevel.FORBIDDEN:
            return ToolResult(success=False, error="forbidden")
        return self.tools[name](**kwargs)

    @abstractmethod
    def run(self, goal: str) -> AgentTrace:
        ...
