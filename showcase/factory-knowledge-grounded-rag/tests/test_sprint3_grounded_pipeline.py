import pytest
from core.schema import NormalizedBlock
from core.evidence_builder import EvidenceBuilder
from core.verifier import DeterministicVerifier, ClaimItem


def test_end_to_end_grounded_pipeline_integration():
    """Verify the integration flow: Block -> EvidenceBuilder -> Verifier."""
    b1 = NormalizedBlock(
        block_id="b-y52",
        document_id="DOC-08_Y52",
        page=1,
        block_type="procedure_step",
        parser="test_parser",
        parser_version="1.0",
        content="CNC 車床 Y52 主軸運轉檢查：若溫度超過 65 度 C，需檢查潤滑油路與冷卻泵浦。鎖定扭矩標準為 45 Nm。",
        metadata={"domain": "PROCEDURE"}
    )
    evidence_pkg = EvidenceBuilder.build([b1])
    assert len(evidence_pkg.evidences) == 1

    valid_claim = ClaimItem(
        statement="檢查主軸鎖定扭矩，標準為 45 Nm。",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=["EV-001"],
        numeric_assertions=["45 Nm"]
    )
    verifier = DeterministicVerifier(evidence_pkg)
    v_res = verifier.verify_all([valid_claim])
    assert v_res.passed is True
    assert v_res.status_code == "PASS"
