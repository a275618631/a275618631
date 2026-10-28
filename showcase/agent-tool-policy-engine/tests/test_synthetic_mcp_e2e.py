from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from agent_policy.evaluator import evaluate
from agent_policy.model import Decision, SideEffect, ToolCall
from agent_policy.policy_loader import load_policy


ROOT = Path(__file__).parents[1]


class SyntheticMCPHandler:
    """A disposable in-process stand-in for an MCP tool handler."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def call(self, tool_name: str, **arguments: object) -> dict[str, object]:
        self.calls.append((tool_name, arguments))
        return {"tool": tool_name, "status": "executed"}


class PolicyGatedMCPClient:
    """Minimal host-side flow: evaluate first, invoke only when allowed."""

    def __init__(self, policy, handler: SyntheticMCPHandler) -> None:
        self.policy = policy
        self.handler = handler

    def invoke(self, call: ToolCall, **arguments: object):
        decision = evaluate(call, self.policy)
        if decision.decision in {Decision.ALLOW, Decision.ALLOW_SCOPED}:
            return decision, self.handler.call(call.operation, **arguments)
        return decision, None


class SyntheticMCPE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(ROOT / "policies" / "policy.toml")

    def test_readonly_call_reaches_handler_after_allow(self):
        handler = SyntheticMCPHandler()
        client = PolicyGatedMCPClient(self.policy, handler)

        decision, response = client.invoke(
            ToolCall("mcp", "filesystem.list", side_effect=SideEffect.READONLY),
            path="src",
        )

        self.assertEqual(decision.decision, Decision.ALLOW)
        self.assertEqual(response, {"tool": "filesystem.list", "status": "executed"})
        self.assertEqual([name for name, _ in handler.calls], ["filesystem.list"])

    def test_external_call_stops_before_handler_without_approval(self):
        handler = SyntheticMCPHandler()
        client = PolicyGatedMCPClient(self.policy, handler)

        decision, response = client.invoke(
            ToolCall("mcp", "mailer.send_email", side_effect=SideEffect.EXTERNAL),
            recipient="synthetic@example.invalid",
        )

        self.assertEqual(decision.decision, Decision.REQUIRE_APPROVAL)
        self.assertIsNone(response)
        self.assertEqual(handler.calls, [])

    def test_critical_call_is_denied_before_handler(self):
        handler = SyntheticMCPHandler()
        client = PolicyGatedMCPClient(self.policy, handler)

        decision, response = client.invoke(
            ToolCall("mcp", "iam.create_token", side_effect=SideEffect.CRITICAL),
            principal="synthetic",
        )

        self.assertEqual(decision.decision, Decision.DENY)
        self.assertIsNone(response)
        self.assertEqual(handler.calls, [])


if __name__ == "__main__":
    unittest.main()
