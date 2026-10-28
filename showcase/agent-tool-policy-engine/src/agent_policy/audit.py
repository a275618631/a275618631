from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping

from .model import DecisionResult, ToolCall

_SECRET_KEY = re.compile(r"(?:token|secret|password|passwd|cookie|oauth|authorization|api[_-]?key|private[_-]?key)", re.I)
_SECRET_VALUE = re.compile(r"(?:bearer\s+|sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,})", re.I)


def redact(value: Any, *, key: str | None = None) -> Any:
    if key and _SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str) and _SECRET_VALUE.search(value):
        return "[REDACTED]"
    return value


def event(call: ToolCall, result: DecisionResult, *, outcome: str = "evaluated", session_id: str | None = None) -> dict[str, Any]:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": session_id,
        "tool": call.tool,
        "operation": call.operation,
        "normalized_target_fingerprint": result.audit_context.get("target_fingerprint"),
        "decision": result.decision.value,
        "matched_rule_id": result.matched_rule_id,
        "reason_code": result.reason_code,
        "outcome": outcome,
    }
    return redact(payload)


def to_jsonl(payload: Mapping[str, Any]) -> str:
    return json.dumps(redact(dict(payload)), ensure_ascii=False, sort_keys=True)
