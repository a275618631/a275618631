from __future__ import annotations

import fnmatch

from .classifier import classify_side_effect
from .model import Decision, DecisionResult, SideEffect, ToolCall
from .normalize import is_within_path, normalize_tool_call, target_fingerprint
from .policy_loader import Policy, PolicyRule


def evaluate(call: ToolCall, policy: Policy) -> DecisionResult:
    normalized = normalize_tool_call(call)
    side_effect = classify_side_effect(normalized)
    target = normalized.path or normalized.target or normalized.repo or normalized.domain
    base = policy.default_for(side_effect)
    matched_rule: PolicyRule | None = next(
        (rule for rule in policy.rules if rule.matches(
            tool=normalized.tool,
            operation=normalized.operation,
            repo=normalized.repo,
            branch=normalized.branch,
            domain=normalized.domain,
            side_effect=side_effect,
        )),
        None,
    )
    decision = matched_rule.decision if matched_rule else base
    reason = f"default_{side_effect.value}"

    if side_effect is SideEffect.CRITICAL:
        return _result(Decision.DENY, "critical_default_deny", normalized, side_effect, matched_rule)
    if _protected_branch(normalized.branch, policy.protected_branches) and normalized.operation in {"git.push", "git.force_push", "git.reset"}:
        return _result(Decision.DENY, "protected_branch", normalized, side_effect, matched_rule)
    if side_effect is SideEffect.READONLY:
        return _result(decision if decision is not Decision.DENY else Decision.DENY, reason, normalized, side_effect, matched_rule)
    if decision is Decision.ALLOW_SCOPED:
        if _scope_verified(normalized, policy):
            return _result(decision, "scoped_resource_allowed", normalized, side_effect, matched_rule, scope_verified=True)
        return _result(Decision.REQUIRE_APPROVAL, "scope_not_verified", normalized, side_effect, matched_rule)
    if decision is Decision.ALLOW:
        if side_effect in {SideEffect.EXTERNAL, SideEffect.DESTRUCTIVE, SideEffect.CRITICAL}:
            return _result(Decision.REQUIRE_APPROVAL, "unsafe_unscoped_allow_downgraded", normalized, side_effect, matched_rule)
        return _result(decision, "policy_allow", normalized, side_effect, matched_rule)
    return _result(decision, reason if matched_rule is None else "matched_policy_rule", normalized, side_effect, matched_rule)


def _scope_verified(call: ToolCall, policy: Policy) -> bool:
    path_ok = bool(policy.allowed_paths and call.path and any(is_within_path(call.path, root) for root in policy.allowed_paths))
    repo_ok = bool(policy.allowed_repos and call.repo and any(fnmatch.fnmatch(call.repo, pattern.lower()) for pattern in policy.allowed_repos))
    branch_ok = bool(call.branch and any(fnmatch.fnmatch(call.branch, pattern.lower()) for pattern in policy.allowed_branches))
    domain_ok = bool(policy.allowed_domains and call.domain and any(fnmatch.fnmatch(call.domain, pattern.lower()) for pattern in policy.allowed_domains))
    return path_ok or (repo_ok and (not policy.allowed_branches or branch_ok)) or domain_ok


def _protected_branch(branch: str | None, patterns: tuple[str, ...]) -> bool:
    return bool(branch and any(fnmatch.fnmatch(branch.lower(), pattern.lower()) for pattern in patterns))


def _result(decision: Decision, reason: str, call: ToolCall, side_effect: SideEffect, rule: PolicyRule | None, *, scope_verified: bool = False) -> DecisionResult:
    return DecisionResult(
        decision=decision,
        reason_code=reason,
        side_effect=side_effect,
        normalized_target=call.path or call.target or call.repo or call.domain,
        matched_rule_id=rule.rule_id if rule else None,
        scope_verified=scope_verified,
        audit_context={
            "tool": call.tool,
            "operation": call.operation,
            "target_fingerprint": target_fingerprint(call.path or call.target or call.repo or call.domain),
            "decision": decision.value,
            "reason_code": reason,
        },
    )
