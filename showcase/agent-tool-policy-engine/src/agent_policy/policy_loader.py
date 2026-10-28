from __future__ import annotations

import fnmatch
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .model import Decision, SideEffect
from .normalize import normalize_domain, normalize_repo

_DECISIONS = {item.value: item for item in Decision}


@dataclass(frozen=True)
class PolicyDefaults:
    readonly: Decision = Decision.ALLOW
    local_write: Decision = Decision.ALLOW_SCOPED
    external: Decision = Decision.REQUIRE_APPROVAL
    destructive: Decision = Decision.REQUIRE_APPROVAL
    critical: Decision = Decision.DENY
    unknown: Decision = Decision.REQUIRE_APPROVAL


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    operation: str | None = None
    tool: str | None = None
    repos: tuple[str, ...] = ()
    branches: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    decision: Decision = Decision.REQUIRE_APPROVAL

    def matches(self, *, tool: str, operation: str, repo: str | None, branch: str | None, domain: str | None, side_effect: SideEffect) -> bool:
        if self.tool and not fnmatch.fnmatch(tool, self.tool.lower()):
            return False
        if self.operation and not fnmatch.fnmatch(operation, self.operation.lower()):
            return False
        if self.side_effects and side_effect.value not in self.side_effects:
            return False
        if self.repos and not _matches_any(repo, self.repos, normalize_repo):
            return False
        if self.branches and not _matches_any(branch, self.branches, lambda value: value):
            return False
        if self.domains and not _matches_any(domain, self.domains, normalize_domain):
            return False
        return True


@dataclass(frozen=True)
class Policy:
    defaults: PolicyDefaults = field(default_factory=PolicyDefaults)
    rules: tuple[PolicyRule, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    allowed_repos: tuple[str, ...] = ()
    allowed_branches: tuple[str, ...] = ("feat/*", "fix/*", "chore/*")
    allowed_domains: tuple[str, ...] = ()
    protected_branches: tuple[str, ...] = ("main", "master", "production", "prod")

    def default_for(self, side_effect: SideEffect) -> Decision:
        return getattr(self.defaults, side_effect.value)


def load_policy(path: str | Path) -> Policy:
    policy_path = Path(path)
    with policy_path.open("rb") as handle:
        data = tomllib.load(handle)
    project_root = policy_path.parent.parent
    defaults = _defaults(data.get("defaults", {}))
    resources = data.get("resources", {})
    rules = tuple(_rule(item, index) for index, item in enumerate(data.get("rules", []), start=1))
    return Policy(
        defaults=defaults,
        rules=rules,
        allowed_paths=tuple(_expand_path(str(item), project_root) for item in resources.get("allowed_paths", [])),
        allowed_repos=tuple(normalize_repo(str(item)) for item in resources.get("allowed_repos", []) if normalize_repo(str(item))),
        allowed_branches=tuple(str(item) for item in resources.get("allowed_branches", ["feat/*", "fix/*", "chore/*"])),
        allowed_domains=tuple(normalize_domain(str(item)) for item in resources.get("allowed_domains", []) if normalize_domain(str(item))),
        protected_branches=tuple(str(item) for item in resources.get("protected_branches", ["main", "master", "production", "prod"])),
    )


def _defaults(values: Mapping[str, Any]) -> PolicyDefaults:
    payload = {key: _decision(values.get(key), getattr(PolicyDefaults(), key)) for key in ("readonly", "local_write", "external", "destructive", "critical", "unknown")}
    return PolicyDefaults(**payload)


def _rule(item: Mapping[str, Any], index: int) -> PolicyRule:
    return PolicyRule(
        rule_id=str(item.get("id", f"rule-{index}")),
        operation=_lower(item.get("operation")),
        tool=_lower(item.get("tool")),
        repos=tuple(normalize_repo(str(value)) for value in item.get("repos", []) if normalize_repo(str(value))),
        branches=tuple(str(value) for value in item.get("branches", [])),
        domains=tuple(normalize_domain(str(value)) for value in item.get("domains", []) if normalize_domain(str(value))),
        side_effects=tuple(str(value).lower() for value in item.get("side_effects", [])),
        decision=_decision(item.get("decision"), Decision.REQUIRE_APPROVAL),
    )


def _decision(value: Any, fallback: Decision) -> Decision:
    if value is None:
        return fallback
    try:
        return _DECISIONS[str(value).lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported policy decision: {value!r}") from exc


def _lower(value: Any) -> str | None:
    return str(value).lower() if value is not None else None


def _expand_path(value: str, project_root: Path) -> str:
    if value == "${PROJECT_ROOT}":
        return str(project_root)
    return value


def _matches_any(value: str | None, patterns: tuple[str, ...], normalizer) -> bool:
    if value is None:
        return False
    normalized = normalizer(value)
    return bool(normalized and any(fnmatch.fnmatch(normalized, pattern.lower()) for pattern in patterns))
