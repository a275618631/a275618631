"""
Deterministic Verifier for Engineering Claims and Citations.
Implements the core safety gate:
"No unsupported actionable claim reaches the user."
"""

import re
from typing import List, Optional, Tuple, Any
from pydantic import BaseModel, Field
from core.evidence import EvidencePackage
from core.schema import ClaimDomain


class ClaimItem(BaseModel):
    statement: str
    claim_type: str = "PROCEDURE"  # PROCEDURE, SAFETY, CURRENT_STATE, HISTORICAL_CASE, HYPOTHESIS
    is_actionable: bool = False
    evidence_ids: List[str] = Field(default_factory=list)
    numeric_assertions: List[str] = Field(default_factory=list)  # e.g. ["45 Nm", "2.0 bar"]


class VerificationResult(BaseModel):
    passed: bool
    status_code: str  # PASS, FAILED_MISSING_EVIDENCE, FAILED_NUMERIC_MISMATCH, FAILED_UNSUPPORTED_ACTION, CONFLICT_DETECTED, ABSTAINED
    failure_reasons: List[str] = Field(default_factory=list)
    checked_claims_count: int = 0
    passed_claims_count: int = 0


class DeterministicVerifier:
    """
    Deterministic safety and citation verification gate.
    Does not use LLM for verification; relies on exact rule and string/numeric audits.
    """

    def __init__(self, evidence_pkg: EvidencePackage) -> None:
        self.evidence_pkg = evidence_pkg

    def verify_citation_exists(self, evidence_id: str) -> bool:
        """Check if cited evidence ID exists in the package."""
        return self.evidence_pkg.get_evidence(evidence_id) is not None

    def verify_numeric_grounding(self, numeric_val: str, evidence_ids: List[str]) -> bool:
        """
        Verify that a specific numeric assertion (e.g. '45 Nm' or '45')
        is physically present in at least one cited evidence snippet or block content.
        """
        clean_num = numeric_val.strip()
        # Extract base digits/tokens for flexible match
        # Match e.g. '45' or '45 Nm' or '45Nm'
        parts = clean_num.split()
        num_part = parts[0] if parts else clean_num

        for eid in evidence_ids:
            ev = self.evidence_pkg.get_evidence(eid)
            if not ev:
                continue

            search_corpus = ev.content_snippet
            if ev.block_id:
                block = self.evidence_pkg.get_block(ev.block_id)
                if block:
                    search_corpus += " " + block.content

            # Look for exact string or num part
            if clean_num.lower() in search_corpus.lower():
                return True
            # Case where units might be connected, e.g., 45Nm
            if num_part in search_corpus:
                return True

        return False

    def verify_claim(self, claim: ClaimItem) -> Tuple[bool, List[str]]:
        """Verify an individual claim."""
        reasons: List[str] = []

        # 1. Actionable claim MUST have valid evidence_ids
        if claim.is_actionable:
            if not claim.evidence_ids:
                reasons.append(f"可執行操作主張「{claim.statement}」未附帶任何依據 (evidence_id)")
            else:
                for eid in claim.evidence_ids:
                    if not self.verify_citation_exists(eid):
                        reasons.append(f"主張所引用的依據「{eid}」在 EvidencePackage 中不存在")

        # 2. Check numeric assertions
        for num_assert in claim.numeric_assertions:
            if not self.verify_numeric_grounding(num_assert, claim.evidence_ids):
                reasons.append(f"數值主張「{num_assert}」無法在對應依據中被精確證實")

        # 3. Check historical case vs confirmed cause
        if claim.claim_type == "CURRENT_STATE" or claim.claim_type == "CONFIRMED_CAUSE":
            for eid in claim.evidence_ids:
                ev = self.evidence_pkg.get_evidence(eid)
                if ev and ev.claim_domain == ClaimDomain.HISTORICAL_CASE.value:
                    reasons.append(f"歷史案例 ({eid}) 僅能作為歷史經驗參考，不可直接作為本次已證實成因 ({claim.statement})")

        return (len(reasons) == 0), reasons

    def verify_all(
        self,
        claims: List[ClaimItem],
        is_conflict: bool = False,
        no_evidence_available: bool = False
    ) -> VerificationResult:
        """
        Run the complete verification gate on all claims.
        """
        # Conflict gate
        if is_conflict:
            return VerificationResult(
                passed=False,
                status_code="CONFLICT_DETECTED",
                failure_reasons=["偵測到有效程序文件間存在衝突，系統禁止下達操作指令，必須呈報現場工程師處置。"],
                checked_claims_count=len(claims),
                passed_claims_count=0
            )

        # No evidence available gate
        if no_evidence_available or not self.evidence_pkg.evidences:
            # If any claim is actionable, FAIL
            has_actionable = any(c.is_actionable for c in claims)
            if has_actionable:
                return VerificationResult(
                    passed=False,
                    status_code="FAILED_UNSUPPORTED_ACTION",
                    failure_reasons=["在缺乏有效佐證的情況下，嚴禁輸出任何可執行工程處方。"],
                    checked_claims_count=len(claims),
                    passed_claims_count=0
                )
            else:
                return VerificationResult(
                    passed=True,
                    status_code="ABSTAINED",
                    failure_reasons=["查無充分現場資料，系統已正確棄權並要求現場確認。"],
                    checked_claims_count=len(claims),
                    passed_claims_count=len(claims)
                )

        all_reasons: List[str] = []
        passed_count = 0

        for c in claims:
            ok, reasons = self.verify_claim(c)
            if ok:
                passed_count += 1
            else:
                all_reasons.extend(reasons)

        if all_reasons:
            status = "FAILED_MISSING_EVIDENCE" if any("不存在" in r for r in all_reasons) else "FAILED_VERIFICATION"
            if any("數值主張" in r for r in all_reasons):
                status = "FAILED_NUMERIC_MISMATCH"
            return VerificationResult(
                passed=False,
                status_code=status,
                failure_reasons=all_reasons,
                checked_claims_count=len(claims),
                passed_claims_count=passed_count
            )

        return VerificationResult(
            passed=True,
            status_code="PASS",
            failure_reasons=[],
            checked_claims_count=len(claims),
            passed_claims_count=passed_count
        )
