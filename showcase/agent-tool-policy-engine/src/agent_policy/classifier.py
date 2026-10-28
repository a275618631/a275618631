from __future__ import annotations

import re

from .model import SideEffect, ToolCall

_CRITICAL = re.compile(r"(?:^|[\s._:/-])(secret|token|oauth|credential|iam|payment|production|prod)(?=$|[\s._:/-])", re.I)
_DESTRUCTIVE = re.compile(r"(?:^|[\s._:/-])(delete|remove|drop|destroy|move|rename|force|reset)(?=$|[\s._:/-])", re.I)
_EXTERNAL = re.compile(r"(?:^|[\s._:/-])(push|send|email|post|deploy|publish|share|upload|network|http)(?=$|[\s._:/-])", re.I)
_LOCAL_WRITE = re.compile(r"(?:^|[\s._:/-])(write|edit|create|patch|apply|commit|mkdir)(?=$|[\s._:/-])", re.I)
_READONLY = re.compile(r"(?:^|[\s._:/-])(read|list|search|stat|test|lint|review|status|get|describe|show|diff|check)(?=$|[\s._:/-])", re.I)


def classify_side_effect(call: ToolCall) -> SideEffect:
    if isinstance(call.side_effect, SideEffect) and call.side_effect is not SideEffect.UNKNOWN:
        return call.side_effect
    explicit = str(call.side_effect).lower()
    if explicit in {item.value for item in SideEffect if item is not SideEffect.UNKNOWN}:
        return SideEffect(explicit)

    signal = " ".join(filter(None, [call.tool, call.operation, call.target, call.path, call.repo, call.branch, call.domain]))
    if _CRITICAL.search(signal) or call.environment in {"production", "prod"}:
        return SideEffect.CRITICAL
    if _DESTRUCTIVE.search(signal) or call.protected_resource:
        return SideEffect.DESTRUCTIVE
    if _EXTERNAL.search(signal):
        return SideEffect.EXTERNAL
    if _LOCAL_WRITE.search(signal):
        return SideEffect.LOCAL_WRITE
    if _READONLY.search(signal):
        return SideEffect.READONLY
    return SideEffect.UNKNOWN
