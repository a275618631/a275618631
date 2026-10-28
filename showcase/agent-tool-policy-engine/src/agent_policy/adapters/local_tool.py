from __future__ import annotations

import os
from dataclasses import dataclass

from ..evaluator import evaluate
from ..model import DecisionResult, ToolCall
from ..policy_loader import Policy

ENFORCEMENT_STATUS = "unsupported_preflight_only"


@dataclass(frozen=True)
class LocalToolAdapter:
    """A safe preflight adapter for a user-controlled CLI/MCP handler.

    It only classifies and returns a decision.  It never invokes the command.
    """

    policy: Policy

    def preflight(self, argv: list[str], *, cwd: str | None = None) -> DecisionResult:
        if not argv:
            call = ToolCall(tool="local", operation="unknown")
        else:
            tool = os.path.basename(argv[0])
            subcommand = argv[1] if len(argv) > 1 else "run"
            operation = f"{tool}.{subcommand}"
            target = next((item for item in argv[2:] if item.startswith(("/", "~/", "C:\\", "D:\\"))), cwd)
            call = ToolCall(tool=tool, operation=operation, target=target, path=target)
        return evaluate(call, self.policy)
