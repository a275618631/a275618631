from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Decision(str, Enum):
    ALLOW = "allow"
    ALLOW_SCOPED = "allow_scoped"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class SideEffect(str, Enum):
    READONLY = "readonly"
    LOCAL_WRITE = "local_write"
    EXTERNAL = "external"
    DESTRUCTIVE = "destructive"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolCall:
    """Structured input supplied by a host adapter.

    The evaluator intentionally does not consume prompt text as a security
    signal.  Hosts should provide structured fields when they have them.
    """

    tool: str
    operation: str
    target: str | None = None
    side_effect: SideEffect | str = SideEffect.UNKNOWN
    path: str | None = None
    repo: str | None = None
    branch: str | None = None
    domain: str | None = None
    environment: str | None = None
    protected_resource: bool = False
    approval_context: str | None = None
    prompt_override: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def with_side_effect(self, side_effect: SideEffect) -> "ToolCall":
        return ToolCall(
            tool=self.tool,
            operation=self.operation,
            target=self.target,
            side_effect=side_effect,
            path=self.path,
            repo=self.repo,
            branch=self.branch,
            domain=self.domain,
            environment=self.environment,
            protected_resource=self.protected_resource,
            approval_context=self.approval_context,
            prompt_override=self.prompt_override,
            metadata=dict(self.metadata),
        )


@dataclass(frozen=True)
class DecisionResult:
    decision: Decision
    reason_code: str
    side_effect: SideEffect
    normalized_target: str | None = None
    matched_rule_id: str | None = None
    scope_verified: bool = False
    audit_context: Mapping[str, Any] = field(default_factory=dict)
