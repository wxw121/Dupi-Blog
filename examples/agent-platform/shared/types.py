"""Shared datatypes — introduced in tutorial 250."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(str, Enum):
    AUTO = "auto"
    CONFIRM = "confirm"
    FORBIDDEN = "forbidden"


@dataclass
class ToolResult:
  success: bool
  data: Any = None
  error: str | None = None


@dataclass
class AgentStep:
  action: str
  observation: str
  ts: float = 0.0


@dataclass
class AgentTrace:
  goal: str
  steps: list[AgentStep] = field(default_factory=list)
