"""
Unit Tests for MVP-0 Core Contracts and Gates.
Tests Canonical Schemas, Terminology 3-state resolution, Authority matrix,
and Deterministic Verifier safety checks.
"""

import os
import sys
import json
import pytest

# Ensure factory-knowledge is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.schema import (
    SourceDocument, NormalizedBlock, Asset, Terminology, FaultCase,
    CurrentObservation, EvidenceRef, ClaimDomain, ApprovalStatus, RootCauseStatus,
    ResolutionState
)
from core.identity import AssetRegistry
from core.terminology import TerminologyRegistry
from core.authority import AuthorityResolver, AuthorityStatus
from core.evidence import EvidencePackage
from core.verifier import DeterministicVerifier, ClaimItem


def test_canonical_schemas_serialization():
    """Verify all 7 canonical schemas can serialize and deserialize cleanly."""
    doc = SourceDocument(
        document_id="DOC-Y52-001",
        source_type="OEM_MANUAL",
        revision="Rev.C",
        effective_from="2026-01-01",
        checksum="sha256:abc123mockhash",
        source_path="source/manual/Y52_manual.pdf",
        asset_scope=["Y52"]
    )
    doc_json = doc.model_dump_json()
    assert "DOC-Y52-001" in doc_json
    doc_restored = SourceDocument.model_validate_json(doc_json)
    assert doc_restored.revision == "Rev.C"

    block = NormalizedBlock(
        block_id="DOC-Y52-001-P083-B04",
        document_id="DOC-Y52-001",
        page=83,
        block_type="procedure_step",
        heading_path=["維護", "編碼器", "檢查"],
        content="檢查聯軸器固定螺栓，指定扭力為 45 Nm。",
        parser="structured_parser",
        parser_version="1.0.0",
        parse_confidence=0.99
    )
    block_restored = NormalizedBlock.model_validate_json(block.model_dump_json())
    assert block_restored.page == 83

    asset = Asset(
        asset_id="Y52-PE-01",
        canonical_name="入側光電感測器",
        parent_asset_id="Y52",
        asset_type="sensor",
        status="active"
    )
    assert Asset.model_validate_json(asset.model_dump_json()).asset_id == "Y52-PE-01"

    term = Terminology(
        term_id="TERM-Y52-PE01",
        canonical_entity_id="Y52-PE-01",
        pref_label="Photoelectric Sensor",
        alt_labels=["光電", "PE", "入側光電", "Photo sensor"],
        scope="Y52",
        status="approved"
    )
    assert len(Terminology.model_validate_json(term.model_dump_json()).alt_labels) == 4

    case = FaultCase(
        case_id="CASE-2025-0318-Y52",
        asset_id="Y52",
        symptom="張力瞬間掉到 0",
        alarm_ids=["A3025"],
        observed_signals=[{"tag": "Y52-ENC-FB", "value": 0}],
        checks_performed=["檢查接頭接線"],
        confirmed_cause="接頭鬆脫",
        root_cause_status=RootCauseStatus.CONFIRMED.value,
        action_taken="重新插拔並鎖緊",
        result="restored",
        source_ids=["WO-2025-0318"],
        review_status="approved"
    )
    assert FaultCase.model_validate_json(case.model_dump_json()).root_cause_status == "confirmed"

    obs = CurrentObservation(
        asset_id="Y52",
        tag_id="Y52-ENC-FB",
        value=0,
        unit="rpm",
        observed_at="2026-09-23T10:31:42+08:00",
        quality="good",
        source="historian"
    )
    assert CurrentObservation.model_validate_json(obs.model_dump_json()).value == 0

    ev = EvidenceRef(
        evidence_id="E1",
        source_id="DOC-Y52-001",
        block_id="DOC-Y52-001-P083-B04",
        claim_domain=ClaimDomain.PROCEDURE.value,
        authority_status="active",
        content_snippet="指定扭力為 45 Nm"
    )
    assert EvidenceRef.model_validate_json(ev.model_dump_json()).evidence_id == "E1"


def test_asset_registry_hierarchy():
    """Verify AssetRegistry hierarchical navigation."""
    reg = AssetRegistry()
    line = Asset(asset_id="LINE-01", canonical_name="冷軋一線", asset_type="line", status="active")
    machine = Asset(asset_id="Y52", canonical_name="Y52導輪機", parent_asset_id="LINE-01", asset_type="machine", status="active")
    sensor = Asset(asset_id="Y52-PE-01", canonical_name="入側光電", parent_asset_id="Y52", asset_type="sensor", status="active")

    reg.register_asset(line)
    reg.register_asset(machine)
    reg.register_asset(sensor)

    children = reg.get_children("Y52")
    assert len(children) == 1
    assert children[0].asset_id == "Y52-PE-01"

    ancestors = reg.get_ancestors("Y52-PE-01")
    assert len(ancestors) == 2
    assert ancestors[0].asset_id == "Y52"
    assert ancestors[1].asset_id == "LINE-01"


def test_terminology_three_state_resolution():
    """Verify TerminologyRegistry Exact, Candidate, and Ambiguous 3-state resolution."""
    reg = TerminologyRegistry()
    term1 = Terminology(
        term_id="TERM-01",
        canonical_entity_id="Y52-PE-01",
        pref_label="Photoelectric Sensor",
        alt_labels=["光電", "PE", "Photo sensor", "入側光電"],
        scope="Y52",
        status="approved"
    )
    term2 = Terminology(
        term_id="TERM-02",
        canonical_entity_id="Y52-ENC-01",
        pref_label="Rotary Encoder",
        alt_labels=["編碼器", "入側 encoder"],
        scope="Y52",
        status="approved"
    )
    reg.register_term(term1)
    reg.register_term(term2)

    # 1. Exact alias resolutions
    res1 = reg.resolve("光電", scope="Y52")
    assert res1.state == ResolutionState.EXACT
    assert res1.canonical_entity_id == "Y52-PE-01"

    res2 = reg.resolve("PE", scope="Y52")
    assert res2.state == ResolutionState.EXACT
    assert res2.canonical_entity_id == "Y52-PE-01"

    res3 = reg.resolve("Photo sensor", scope="Y52")
    assert res3.state == ResolutionState.EXACT
    assert res3.canonical_entity_id == "Y52-PE-01"

    res4 = reg.resolve("入側 encoder", scope="Y52")
    assert res4.state == ResolutionState.EXACT
    assert res4.canonical_entity_id == "Y52-ENC-01"

    # 2. Ambiguous query resolution (e.g. "跳掉")
    res_ambig = reg.resolve("跳掉")
    assert res_ambig.state == ResolutionState.AMBIGUOUS
    assert res_ambig.canonical_entity_id is None
    assert len(res_ambig.candidates) >= 2
    assert "clarification" in res_ambig.clarification_prompt or "請確認" in res_ambig.clarification_prompt

    # 3. Unknown query resolution
    res_unk = reg.resolve("完全不存在的太空設備")
    assert res_unk.state == ResolutionState.UNKNOWN


def test_authority_resolver_revision_and_conflict():
    """Verify AuthorityResolver lifecycle handling and conflict detection."""
    resolver = AuthorityResolver()

    # Active doc Rev.C
    doc_c = SourceDocument(
        document_id="DOC-Y52-REV-C",
        source_type="SOP",
        revision="Rev.C",
        effective_from="2026-01-01",
        approval_status=ApprovalStatus.APPROVED.value,
        checksum="hash-c",
        source_path="c.pdf"
    )
    # Superseded doc Rev.B
    doc_b = SourceDocument(
        document_id="DOC-Y52-REV-B",
        source_type="SOP",
        revision="Rev.B",
        effective_from="2024-01-01",
        approval_status=ApprovalStatus.SUPERSEDED.value,
        superseded_by="DOC-Y52-REV-C",
        checksum="hash-b",
        source_path="b.pdf"
    )
    resolver.register_document(doc_c)
    resolver.register_document(doc_b)

    is_act_c, status_c, _ = resolver.is_document_active("DOC-Y52-REV-C")
    assert is_act_c is True
    assert status_c == AuthorityStatus.ACTIVE

    is_act_b, status_b, _ = resolver.is_document_active("DOC-Y52-REV-B")
    assert is_act_b is False
    assert status_b == AuthorityStatus.SUPERSEDED

    # Conflict detection between 2 active procedures
    doc_proc1 = SourceDocument(
        document_id="DOC-P1",
        source_type="SOP",
        revision="A",
        effective_from="2026-01-01",
        approval_status=ApprovalStatus.APPROVED.value,
        checksum="h1",
        source_path="p1.pdf"
    )
    doc_proc2 = SourceDocument(
        document_id="DOC-P2",
        source_type="SOP",
        revision="A",
        effective_from="2026-01-01",
        approval_status=ApprovalStatus.APPROVED.value,
        checksum="h2",
        source_path="p2.pdf"
    )
    resolver.register_document(doc_proc1)
    resolver.register_document(doc_proc2)

    conflict = resolver.detect_procedure_conflict([
        {"doc_id": "DOC-P1", "asset_id": "Y52", "parameter": "test_pressure", "value": "25 bar"},
        {"doc_id": "DOC-P2", "asset_id": "Y52", "parameter": "test_pressure", "value": "35 bar"}
    ])
    assert conflict is not None
    assert "衝突" in conflict.description
    assert "DOC-P1" in conflict.conflicting_doc_ids
    assert "DOC-P2" in conflict.conflicting_doc_ids


def test_deterministic_verifier_gates():
    """Verify DeterministicVerifier citation, numeric, abstention, and conflict gates."""
    pkg = EvidencePackage()
    ev1 = EvidenceRef(
        evidence_id="E1",
        source_id="DOC-Y52-001",
        block_id="B1",
        claim_domain=ClaimDomain.PROCEDURE.value,
        authority_status="active",
        content_snippet="主傳動聯軸器螺栓鎖固扭力指定為 45 Nm。"
    )
    block1 = NormalizedBlock(
        block_id="B1",
        document_id="DOC-Y52-001",
        page=1,
        block_type="procedure_step",
        content="主傳動聯軸器螺栓鎖固扭力指定為 45 Nm。",
        parser="structured",
        parser_version="1.0",
        parse_confidence=1.0
    )
    pkg.add_evidence(ev1, block=block1)

    verifier = DeterministicVerifier(pkg)

    # 1. Valid actionable claim with correct evidence and exact numeric value (45 Nm)
    valid_claim = ClaimItem(
        statement="將聯軸器螺栓鎖緊至 45 Nm",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=["E1"],
        numeric_assertions=["45 Nm"]
    )
    res_valid = verifier.verify_all([valid_claim])
    assert res_valid.passed is True
    assert res_valid.status_code == "PASS"

    # 2. Invalid citation: citing non-existent evidence E99
    invalid_cite_claim = ClaimItem(
        statement="執行校正程序",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=["E99"]
    )
    res_cite_fail = verifier.verify_all([invalid_cite_claim])
    assert res_cite_fail.passed is False
    assert res_cite_fail.status_code == "FAILED_MISSING_EVIDENCE"

    # 3. Numeric mismatch: claiming 120 Nm when evidence only has 45 Nm
    num_mismatch_claim = ClaimItem(
        statement="鎖緊扭力設定為 120 Nm",
        claim_type="PROCEDURE",
        is_actionable=True,
        evidence_ids=["E1"],
        numeric_assertions=["120 Nm"]
    )
    res_num_fail = verifier.verify_all([num_mismatch_claim])
    assert res_num_fail.passed is False
    assert res_num_fail.status_code == "FAILED_NUMERIC_MISMATCH"

    # 4. No evidence available with actionable claim -> MUST FAIL
    empty_verifier = DeterministicVerifier(EvidencePackage())
    res_empty_action = empty_verifier.verify_all([valid_claim])
    assert res_empty_action.passed is False
    assert res_empty_action.status_code == "FAILED_UNSUPPORTED_ACTION"

    # 5. No evidence available with pure abstention -> PASS with ABSTAINED status
    abstain_claim = ClaimItem(
        statement="現場資料不足，建議由設備工程師手動量測確認。",
        claim_type="HYPOTHESIS",
        is_actionable=False
    )
    res_abstain = empty_verifier.verify_all([abstain_claim])
    assert res_abstain.passed is True
    assert res_abstain.status_code == "ABSTAINED"

    # 6. Conflict detected gate
    res_conflict = verifier.verify_all([valid_claim], is_conflict=True)
    assert res_conflict.passed is False
    assert res_conflict.status_code == "CONFLICT_DETECTED"
