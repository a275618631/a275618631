"""
Terminology Registry and Slang/Alias Resolution for Factory Floor.
Implements W3C SKOS preferred and alternate label resolution with 3-state outputs.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from core.schema import Terminology, TerminologyStatus, ResolutionState


class ResolutionResult(BaseModel):
    state: ResolutionState
    query_term: str
    canonical_entity_id: Optional[str] = None
    pref_label: Optional[str] = None
    candidates: List[str] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
    matched_term_id: Optional[str] = None


class TerminologyRegistry:
    """
    Registry for domain terminology, equipment aliases, and factory jargon.
    Provides Exact, Candidate, and Ambiguous multi-state query resolution.
    """

    def __init__(self) -> None:
        self._terms: Dict[str, Terminology] = {}
        # Explicit ambiguity rules (e.g. "跳掉" -> motor trip, breaker trip, interlock)
        self._ambiguity_map: Dict[str, Dict[str, Any]] = {
            "跳掉": {
                "clarification": "「跳掉」具有多種可能成因，請確認是：(1) 馬達過載跳脫 (Motor Trip) (2) 無熔絲開關跳脫 (Breaker Trip) (3) 安全互鎖觸發 (Interlock Trip)",
                "candidate_entities": ["OVERLOAD_TRIP", "BREAKER_TRIP", "SAFETY_INTERLOCK_TRIP"]
            },
            "沒動作": {
                "clarification": "「沒動作」可能為電源缺失、控制信號未到達或機構卡死，請確認是訊號端還是動力端？",
                "candidate_entities": ["SIGNAL_MISSING", "POWER_LOSS", "MECHANICAL_JAM"]
            }
        }

    def register_term(self, term: Terminology) -> None:
        """Register or update a terminology record."""
        self._terms[term.term_id] = term

    def get_term(self, term_id: str) -> Optional[Terminology]:
        return self._terms.get(term_id)

    def resolve(self, query: str, scope: Optional[str] = None) -> ResolutionResult:
        """
        Resolve a user query or slang into canonical entity.
        Returns EXACT, CANDIDATE, AMBIGUOUS, or UNKNOWN.
        """
        clean_q = query.strip()
        q_lower = clean_q.lower()

        # 1. Check explicit ambiguity map
        for ambig_key, ambig_info in self._ambiguity_map.items():
            if ambig_key.lower() == q_lower:
                return ResolutionResult(
                    state=ResolutionState.AMBIGUOUS,
                    query_term=clean_q,
                    candidates=ambig_info["candidate_entities"],
                    clarification_prompt=ambig_info["clarification"]
                )

        # 2. Check exact matches in Terminology registry
        # We prioritize matching terms that match scope if provided, then global.
        exact_matches: List[Terminology] = []
        partial_matches: List[Terminology] = []

        for term in self._terms.values():
            if term.status != TerminologyStatus.APPROVED.value:
                continue

            # Scope filtering: term scope must match or be global
            if scope and term.scope != "global" and term.scope != scope:
                continue

            # Check preferred label
            if term.pref_label.strip().lower() == q_lower:
                exact_matches.append(term)
                continue

            # Check alt labels
            for alt in term.alt_labels:
                if alt.strip().lower() == q_lower:
                    exact_matches.append(term)
                    break
            else:
                # Check substring partial match
                if q_lower in term.pref_label.lower() or any(q_lower in alt.lower() for alt in term.alt_labels):
                    partial_matches.append(term)

        # Evaluate exact matches
        if len(exact_matches) == 1:
            m = exact_matches[0]
            return ResolutionResult(
                state=ResolutionState.EXACT,
                query_term=clean_q,
                canonical_entity_id=m.canonical_entity_id,
                pref_label=m.pref_label,
                matched_term_id=m.term_id
            )
        elif len(exact_matches) > 1:
            # Multiple exact matches across different scopes or entities -> Ambiguous
            return ResolutionResult(
                state=ResolutionState.AMBIGUOUS,
                query_term=clean_q,
                candidates=[m.canonical_entity_id for m in exact_matches],
                clarification_prompt=f"發現多個同名或別名實體 ({[m.pref_label for m in exact_matches]})，請指明具體設備或範圍。"
            )

        # Evaluate partial matches -> Candidate
        if partial_matches:
            unique_candidates = list(dict.fromkeys([m.canonical_entity_id for m in partial_matches]))
            if len(unique_candidates) == 1:
                m = partial_matches[0]
                return ResolutionResult(
                    state=ResolutionState.CANDIDATE,
                    query_term=clean_q,
                    canonical_entity_id=m.canonical_entity_id,
                    pref_label=m.pref_label,
                    candidates=[m.canonical_entity_id],
                    clarification_prompt=f"是否意指 {m.pref_label} ({m.canonical_entity_id})？"
                )
            return ResolutionResult(
                state=ResolutionState.CANDIDATE,
                query_term=clean_q,
                candidates=unique_candidates,
                clarification_prompt=f"發現多個可能候選，請確認：{unique_candidates}"
            )

        return ResolutionResult(
            state=ResolutionState.UNKNOWN,
            query_term=clean_q,
            clarification_prompt=f"查無符合「{clean_q}」之標準術語或現場別名。"
        )
