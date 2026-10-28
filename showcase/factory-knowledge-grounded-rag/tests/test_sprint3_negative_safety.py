import pytest
from core.evidence import EvidencePackage, EvidenceItem
from core.schema import NormalizedBlock
from core.verifier import DeterministicVerifier, ClaimItem


def test_negative_safety_numeric_mismatch():
    """Verify verifier blocks claim when numeric assertion does not match evidence snippet."""
    block = NormalizedBlock(
        block_id="b1",
        document_id="DOC-08",
        page=1,
        block_type="procedure_step",
        parser="test_parser",
        parser_version="1.0",
        content="主軸預緊力矩標準為 45 Nm，禁止超過 50 Nm。"
    )
    pkg = EvidencePackage(
        evidences={
            "EV-001": EvidenceItem(
                evidence_id="EV-001",
                source_id="DOC-08",
                claim_domain="PROCEDURE",
                block_id="b1",
                content_snippet="主軸預緊力矩標準為 45 Nm"
            )
        },
        blocks={"b1": block}
    )
    verifier = DeterministicVerifier(pkg)

    fake_claim = ClaimItem(
        statement="請使用氣動工具將螺栓鎖緊至 80 Nm。",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=["EV-001"],
        numeric_assertions=["80 Nm"]
    )
    res = verifier.verify_all([fake_claim])
    assert res.passed is False
    assert res.status_code == "FAILED_NUMERIC_MISMATCH"


def test_negative_safety_missing_evidence_citation():
    """Verify verifier blocks claim citing non-existent evidence_id."""
    pkg = EvidencePackage(evidences={
        "EV-001": EvidenceItem(
            evidence_id="EV-001",
            source_id="DOC-01",
            claim_domain="PROCEDURE",
            content_snippet="標準手冊內文"
        )
    })
    verifier = DeterministicVerifier(pkg)

    ghost_claim = ClaimItem(
        statement="執行全面拆解作業。",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=["EV-999"]
    )
    res = verifier.verify_all([ghost_claim])
    assert res.passed is False
    assert res.status_code == "FAILED_MISSING_EVIDENCE"


def test_negative_safety_historical_case_as_confirmed_cause():
    """Verify verifier blocks historical case being falsely stated as confirmed current cause."""
    pkg = EvidencePackage(evidences={
        "EV-001": EvidenceItem(
            evidence_id="EV-001",
            source_id="DOC-11_HIST",
            content_snippet="2025年4月曾因潤滑不足造成主軸軸承燒毀。",
            claim_domain="HISTORICAL_CASE"
        )
    })
    verifier = DeterministicVerifier(pkg)

    false_cause_claim = ClaimItem(
        statement="本次異常已證實為主軸軸承燒毀。",
        claim_type="CURRENT_STATE",
        is_actionable=False,
        evidence_ids=["EV-001"]
    )
    res = verifier.verify_all([false_cause_claim])
    assert res.passed is False
    assert any("歷史案例" in reason for reason in res.failure_reasons)
