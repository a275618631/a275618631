from __future__ import annotations

from ..model import Decision

ENFORCEMENT_STATUS = "unsupported_preview_only"


def render_safe_rules() -> str:
    """Render a reviewable Codex rules fragment; it is not installed automatically."""
    return """# Generated preview: review before installing in Codex rules.
prefix_rule(pattern=[\"git\", \"status\"], decision=\"allow\")
prefix_rule(pattern=[\"git\", \"diff\"], decision=\"allow\")
prefix_rule(pattern=[\"git\", \"push\"], decision=\"ask\", justification=\"Remote side effect requires review.\")
prefix_rule(pattern=[\"git\", \"reset\", \"--hard\"], decision=\"deny\", justification=\"Destructive operation is blocked.\")
"""


def verify_rules_text(text: str) -> bool:
    required = [
        'pattern=["git", "status"]',
        'pattern=["git", "diff"]',
        'pattern=["git", "push"]',
        'pattern=["git", "reset", "--hard"]',
    ]
    return all(fragment in text for fragment in required) and "decision=\"allow\"" in text and "decision=\"deny\"" in text


def decision_requires_host_approval(decision: Decision) -> bool:
    return decision is Decision.REQUIRE_APPROVAL
