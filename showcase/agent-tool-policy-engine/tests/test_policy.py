from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from agent_policy.adapters.codex_rules import ENFORCEMENT_STATUS as CODEX_RULES_ENFORCEMENT_STATUS
from agent_policy.adapters.codex_rules import render_safe_rules, verify_rules_text
from agent_policy.adapters.local_tool import ENFORCEMENT_STATUS as LOCAL_TOOL_ENFORCEMENT_STATUS
from agent_policy.adapters.local_tool import LocalToolAdapter
from agent_policy.audit import event, to_jsonl
from agent_policy.evaluator import evaluate
from agent_policy.model import Decision, SideEffect, ToolCall
from agent_policy.normalize import is_within_path, normalize_branch, normalize_path
from agent_policy.policy_loader import load_policy


ROOT = Path(__file__).parents[1]


class PolicyCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(ROOT / "policies" / "policy.toml")

    def test_readonly_is_allowed(self):
        result = evaluate(ToolCall("git", "git.status", side_effect=SideEffect.READONLY), self.policy)
        self.assertEqual(result.decision, Decision.ALLOW)

    def test_search_and_lint_are_readonly(self):
        for operation in ("search", "lint", "test", "git.diff"):
            with self.subTest(operation=operation):
                result = evaluate(ToolCall("tool", operation), self.policy)
                self.assertEqual(result.decision, Decision.ALLOW)

    def test_scoped_workspace_write(self):
        result = evaluate(ToolCall("apply_patch", "write", path=str(ROOT / "src" / "x.py")), self.policy)
        self.assertEqual(result.decision, Decision.ALLOW_SCOPED)
        self.assertTrue(result.scope_verified)

    def test_outside_workspace_write_requires_approval(self):
        result = evaluate(ToolCall("apply_patch", "write", path="/tmp/outside.py"), self.policy)
        self.assertEqual(result.decision, Decision.REQUIRE_APPROVAL)

    def test_external_side_effect_requires_approval(self):
        result = evaluate(ToolCall("mailer", "send_email", side_effect=SideEffect.EXTERNAL), self.policy)
        self.assertEqual(result.decision, Decision.REQUIRE_APPROVAL)

    def test_destructive_action_requires_approval(self):
        result = evaluate(ToolCall("filesystem", "delete_file", side_effect=SideEffect.DESTRUCTIVE), self.policy)
        self.assertEqual(result.decision, Decision.REQUIRE_APPROVAL)

    def test_feature_branch_push_is_scoped(self):
        result = evaluate(ToolCall("git", "git.push", repo="a275618631/demo", branch="feat/policy", side_effect=SideEffect.EXTERNAL), self.policy)
        self.assertEqual(result.decision, Decision.ALLOW_SCOPED)

    def test_protected_branch_is_denied(self):
        result = evaluate(ToolCall("git", "git.push", repo="a275618631/demo", branch="main", side_effect=SideEffect.EXTERNAL), self.policy)
        self.assertEqual(result.decision, Decision.DENY)

    def test_unknown_side_effect_fails_safe(self):
        result = evaluate(ToolCall("custom", "mystery"), self.policy)
        self.assertEqual(result.decision, Decision.REQUIRE_APPROVAL)

    def test_critical_is_denied(self):
        result = evaluate(ToolCall("iam", "create-token", side_effect=SideEffect.CRITICAL), self.policy)
        self.assertEqual(result.decision, Decision.DENY)

    def test_prompt_override_is_ignored(self):
        result = evaluate(ToolCall("git", "git.push", repo="a275618631/demo", branch="main", prompt_override=True, side_effect=SideEffect.EXTERNAL), self.policy)
        self.assertEqual(result.decision, Decision.DENY)

    def test_path_traversal_does_not_escape_scope(self):
        path = str(ROOT / "src" / ".." / ".." / "outside.py")
        result = evaluate(ToolCall("apply_patch", "write", path=path), self.policy)
        self.assertEqual(result.decision, Decision.REQUIRE_APPROVAL)

    def test_symlink_target_does_not_escape_scope(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            allowed = base / "allowed"
            outside = base / "outside"
            allowed.mkdir()
            outside.mkdir()
            link = allowed / "linked"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable on this runner")
            self.assertFalse(is_within_path(str(link / "secret.txt"), str(allowed)))

    def test_normalization_is_cross_platform(self):
        self.assertEqual(normalize_path(r"C:\\work\\repo\\..\\repo\\file.py"), "C:/work/repo/file.py")
        self.assertEqual(normalize_branch("refs/heads/feat/demo"), "feat/demo")
        self.assertTrue(is_within_path("C:/work/repo/file.py", "C:/work/repo"))

    def test_invalid_rule_decision_is_rejected(self):
        bad = ROOT / "tests" / "invalid-policy.toml"
        bad.write_text('[[rules]]\ndecision = "maybe"\n', encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                load_policy(bad)
        finally:
            bad.unlink()

    def test_malformed_tool_fields_fail_safe(self):
        result = evaluate(ToolCall(tool=None, operation=None), self.policy)
        self.assertEqual(result.decision, Decision.REQUIRE_APPROVAL)


class AuditAndAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(ROOT / "policies" / "policy.toml")

    def test_secret_values_never_appear_in_audit(self):
        result = evaluate(ToolCall("git", "git.status", metadata={"token": "ghp_test_secret_value"}), self.policy)
        payload = event(ToolCall("git", "git.status"), result)
        rendered = to_jsonl(payload)
        self.assertNotIn("ghp_test_secret_value", rendered)
        self.assertNotIn("prompt", rendered)

    def test_audit_contains_fingerprint_not_target(self):
        call = ToolCall("git", "git.status", target="/private/project")
        result = evaluate(call, self.policy)
        payload = event(call, result)
        rendered = json.dumps(payload)
        self.assertNotIn("/private/project", rendered)
        self.assertIn("target_fingerprint", rendered)

    def test_local_adapter_never_runs_command(self):
        adapter = LocalToolAdapter(self.policy)
        result = adapter.preflight(["git", "status"], cwd=str(ROOT))
        self.assertEqual(result.decision, Decision.ALLOW)

    def test_codex_rules_preview_is_reviewable(self):
        text = render_safe_rules()
        self.assertTrue(verify_rules_text(text))
        self.assertIn("remote side effect", text.lower())

    def test_unsupported_hooks_are_explicit(self):
        self.assertEqual(LOCAL_TOOL_ENFORCEMENT_STATUS, "unsupported_preflight_only")
        self.assertEqual(CODEX_RULES_ENFORCEMENT_STATUS, "unsupported_preview_only")


if __name__ == "__main__":
    unittest.main()
