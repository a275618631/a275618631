"""
Deterministic Offline LLM Adapter for Reproducible Industrial Safety Verification.
Generates structured FactoryDiagnosisResponse without external GPU/network dependencies.
Strictly grounds all actionable steps in the provided EvidencePackage.
"""

import re
from typing import Optional, List, Any
from core.interfaces import BaseLLM
from core.schema import ClaimDomain
from core.evidence import EvidencePackage
from core.response_schema import FactoryDiagnosisResponse
from core.verifier import ClaimItem, DeterministicVerifier


class DeterministicMockLLM(BaseLLM):
    """
    Deterministic generation engine for evaluation and offline validation.
    Guarantees that:
    1. If evidence is empty, it abstains (unknowns/field checks populated, 0 actionable steps).
    2. If evidence exists, actionable steps explicitly reference existing evidence IDs.
    3. Numerical values in evidence are extracted faithfully.
    """

    def generate_structured(self, prompt: str, schema_cls: Any) -> Any:
        # Fallback for generic BaseLLM call
        return schema_cls(query=prompt)

    def generate_diagnosis(
        self,
        query: str,
        evidence_pkg: EvidencePackage,
        asset_id: Optional[str] = "Y52",
        is_conflict: bool = False
    ) -> FactoryDiagnosisResponse:
        """
        Generate grounded, partitioned FactoryDiagnosisResponse.
        """
        # Case A: Conflict detected between documents
        if is_conflict:
            verifier = DeterministicVerifier(evidence_pkg)
            v_res = verifier.verify_all([], is_conflict=True)
            return FactoryDiagnosisResponse(
                query=query,
                asset_id=asset_id,
                unknowns=["現場文件存在數值或程序衝突，系統拒絕下達操作指令。"],
                required_field_checks=["請設備主管工程師介入審查衝突文件版本。"],
                claims=[],
                verification_status="CONFLICT_DETECTED",
                verification_details=v_res.model_dump()
            )

        # Case B: No evidence available -> MUST ABSTAIN
        if not evidence_pkg.evidences:
            claim_abstain = ClaimItem(
                statement="目前知識庫查無相關有效文件或測點數據，無法提供可執行處方。",
                claim_type="HYPOTHESIS",
                is_actionable=False
            )
            verifier = DeterministicVerifier(evidence_pkg)
            v_res = verifier.verify_all([claim_abstain], no_evidence_available=True)
            return FactoryDiagnosisResponse(
                query=query,
                asset_id=asset_id,
                unknowns=[f"未在標準文件中檢索到「{query}」之相關規範。"],
                required_field_checks=["請攜帶儀表至現場進行手動量測與確認。", "核對設備出廠銘牌代號。"],
                claims=[claim_abstain],
                verification_status=v_res.status_code,
                verification_details=v_res.model_dump()
            )

        # Case C: Valid evidence available -> Build partitioned grounded response
        confirmed_facts = []
        hist_cases = []
        hypotheses = []
        procedure_steps = []
        claims = []

        for ev_id, ev in evidence_pkg.evidences.items():
            snippet = ev.content_snippet.strip()
            block = evidence_pkg.get_block(ev.block_id) if ev.block_id else None

            # 1. Spec & Current state observations
            if ev.claim_domain in [ClaimDomain.CURRENT_STATE.value, ClaimDomain.DESIGN_CONFIGURATION.value]:
                confirmed_facts.append(f"[{ev_id}] {snippet}")
                claims.append(ClaimItem(
                    statement=snippet,
                    claim_type=ev.claim_domain,
                    is_actionable=False,
                    evidence_ids=[ev_id]
                ))

            # 2. Historical cases
            elif ev.claim_domain == ClaimDomain.HISTORICAL_CASE.value:
                hist_cases.append(f"[{ev_id}] 歷史維修紀錄參考：{snippet}")
                claims.append(ClaimItem(
                    statement=snippet,
                    claim_type="HISTORICAL_CASE",
                    is_actionable=False,
                    evidence_ids=[ev_id]
                ))

            # 3. Actionable procedure & safety steps
            elif ev.claim_domain in [ClaimDomain.PROCEDURE.value, ClaimDomain.SAFETY.value, ClaimDomain.FAILURE_MODE.value]:
                # Extract numeric assertions (e.g. 45 Nm, 25 bar, 0.55 MPa, 65°C)
                num_matches = re.findall(r"\b\d+(?:\.\d+)?\s*(?:Nm|bar|MPa|rpm|°C|公升|克|p|p/r|ppr|MΩ)\b", snippet)

                step_text = f"依據文件指引：{snippet}"
                procedure_steps.append(f"[{ev_id}] {step_text}")

                claims.append(ClaimItem(
                    statement=step_text,
                    claim_type=ev.claim_domain,
                    is_actionable=True,
                    evidence_ids=[ev_id],
                    numeric_assertions=num_matches
                ))

        # Run Deterministic Verifier Gate
        verifier = DeterministicVerifier(evidence_pkg)
        v_res = verifier.verify_all(claims)

        return FactoryDiagnosisResponse(
            query=query,
            asset_id=asset_id,
            confirmed_facts=confirmed_facts,
            historical_similar_cases=hist_cases,
            current_hypotheses=hypotheses,
            approved_procedure_steps=procedure_steps,
            unknowns=[],
            required_field_checks=["作業前請確認現場安全防護符合 LOTO 規範。"] if procedure_steps else [],
            claims=claims,
            verification_status=v_res.status_code,
            verification_details=v_res.model_dump()
        )
