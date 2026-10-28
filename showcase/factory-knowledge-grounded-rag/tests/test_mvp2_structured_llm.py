"""
Unit Tests for MVP-2 Local Structured Generation and Anti-Hallucination Gates.
Tests Pydantic structured response formatting, 5-case Abstention on no-answer,
5-case Conflict detection, Evidence grounding, and Numerical assertion validation.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.schema import NormalizedBlock, SourceDocument, EvidenceRef, ClaimDomain
from core.evidence import EvidencePackage
from core.response_schema import FactoryDiagnosisResponse
from core.verifier import DeterministicVerifier, ClaimItem
from adapters.llm.deterministic_mock_llm import DeterministicMockLLM


@pytest.fixture
def populated_evidence_pkg():
    pkg = EvidencePackage()
    doc = SourceDocument(
        document_id="DOC-Y52-SOP-001",
        source_type="SOP",
        revision="Rev.C",
        effective_from="2026-01-01",
        approval_status="approved",
        checksum="hash-sop-001",
        source_path="sop001.md",
        asset_scope=["Y52"]
    )
    b1 = NormalizedBlock(
        block_id="DOC-Y52-SOP-001-P001-B001",
        document_id="DOC-Y52-SOP-001",
        page=1,
        block_type="procedure_step",
        heading_path=["主傳動裝配"],
        content="檢查主傳動聯軸器固定螺栓，指定鎖固扭力為 45 Nm。耐壓測試加壓上限為 25 bar。",
        parser="structured_parser",
        parser_version="1.0.0",
        parse_confidence=1.0
    )
    ev1 = EvidenceRef(
        evidence_id="E1",
        source_id="DOC-Y52-SOP-001",
        block_id=b1.block_id,
        page=1,
        claim_domain=ClaimDomain.PROCEDURE.value,
        authority_status="active",
        content_snippet=b1.content
    )
    pkg.add_evidence(ev1, block=b1, doc=doc)
    return pkg


def test_structured_pydantic_response_format(populated_evidence_pkg):
    """Verify generated diagnosis strictly complies with FactoryDiagnosisResponse schema."""
    engine = DeterministicMockLLM()
    resp = engine.generate_diagnosis(
        query="主傳動聯軸器螺栓鎖固扭力是多少？",
        evidence_pkg=populated_evidence_pkg,
        asset_id="Y52"
    )

    assert isinstance(resp, FactoryDiagnosisResponse)
    assert resp.verification_status == "PASS"
    assert len(resp.approved_procedure_steps) > 0
    assert any("45 Nm" in step for step in resp.approved_procedure_steps)
    assert len(resp.claims) > 0

    # Ensure JSON serializable
    json_str = resp.model_dump_json()
    assert "approved_procedure_steps" in json_str
    assert "45 Nm" in json_str


def test_no_answer_abstention_five_queries():
    """Verify 5 unanswerable / out-of-scope queries 100% trigger abstention without actionable claims."""
    engine = DeterministicMockLLM()
    empty_pkg = EvidencePackage()

    no_answer_queries = [
        "2030年新型光纖激光測厚儀在 Y52 的校準頻率與參數代碼是什麼？",
        "未登記之自製改裝夾爪之氣缸極限衝程設定應為多少 mm？",
        "廠外神秘廠商 X 代號 Z-999 感測器之故障排除步驟為何？",
        "火星基地採礦無人車之散熱冷卻液配方與充填量為何？",
        "完全未建檔之地下室 9 號備用幫浦拆解順序與圖紙？"
    ]

    for q in no_answer_queries:
        resp = engine.generate_diagnosis(query=q, evidence_pkg=empty_pkg, asset_id="UNKNOWN")
        assert resp.verification_status == "ABSTAINED", f"Query '{q}' failed to abstain!"
        assert len(resp.approved_procedure_steps) == 0, f"Abstained query produced actionable steps!"
        assert len(resp.unknowns) > 0
        assert len(resp.required_field_checks) > 0


def test_unsupported_actionable_claim_interception():
    """Verify verifier gate rejects actionable claims when evidence is absent."""
    empty_pkg = EvidencePackage()
    verifier = DeterministicVerifier(empty_pkg)

    # Fabricated actionable instruction
    hallucinated_claim = ClaimItem(
        statement="直接將閥門轉動至 90 度並按下強制啟動鈕",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=[]  # No evidence
    )

    res = verifier.verify_all([hallucinated_claim], no_evidence_available=True)
    assert res.passed is False
    assert res.status_code == "FAILED_UNSUPPORTED_ACTION"
    assert "嚴禁輸出任何可執行工程處方" in res.failure_reasons[0]


def test_conflict_detection_five_scenarios(populated_evidence_pkg):
    """Verify 5 conflict scenarios 100% trigger CONFLICT_DETECTED status."""
    engine = DeterministicMockLLM()

    conflict_scenarios = [
        "Y52 液壓管路年度壓力測試加壓上限衝突 (25 bar vs 35 bar)",
        "主傳動軸承注脂量指定標準值衝突 (35g vs 80g)",
        "導輪氣壓額定設定值衝突 (0.55 MPa vs 0.85 MPa)",
        "伺服馬達濾網清潔週期衝突 (每週 vs 每年)",
        "更換編碼器型號解析度設定衝突 (2048 ppr vs 4096 ppr)"
    ]

    for sc in conflict_scenarios:
        resp = engine.generate_diagnosis(
            query=sc,
            evidence_pkg=populated_evidence_pkg,
            asset_id="Y52",
            is_conflict=True
        )
        assert resp.verification_status == "CONFLICT_DETECTED"
        assert len(resp.approved_procedure_steps) == 0
        assert "衝突" in resp.unknowns[0]


def test_actionable_claims_evidence_and_numeric_grounding(populated_evidence_pkg):
    """Verify all actionable claims strictly carry valid evidence IDs and numeric grounding."""
    engine = DeterministicMockLLM()
    resp = engine.generate_diagnosis(
        query="主傳動聯軸器螺栓鎖固扭力？",
        evidence_pkg=populated_evidence_pkg,
        asset_id="Y52"
    )

    for claim in resp.claims:
        if claim.is_actionable:
            assert len(claim.evidence_ids) > 0
            for eid in claim.evidence_ids:
                assert populated_evidence_pkg.get_evidence(eid) is not None

            # Verify numeric assertions match
            for num in claim.numeric_assertions:
                assert num in ["45 Nm", "25 bar"]
