from __future__ import annotations

from dataclasses import dataclass

from ..evaluator import evaluate
from ..model import DecisionResult, ToolCall
from ..policy_loader import Policy


@dataclass(frozen=True)
class GenericPolicyAdapter:
    policy: Policy

    def decide(self, call: ToolCall) -> DecisionResult:
        return evaluate(call, self.policy)
