"""
Unit Tests for MVP-3 Fault Case Knowledge Base and Multimodal Dual-Track Images.
Tests historical work order ingestion, strict root-cause segregation (confirmed vs suspected),
prevention of false causal attribution, and dual-track image candidate safety gates.
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.schema import FaultCase, RootCauseStatus, ApprovalStatus, EvidenceRef, ClaimDomain
from core.case_manager import FaultCaseManager
from core.evidence import EvidencePackage
from core.verifier import DeterministicVerifier, ClaimItem
from adapters.multimodal.image_handler import (
    ImageRegistry, ImageStructuredMetadata, RawImageMetadata, BoundingBox
)


@pytest.fixture
def populated_case_manager():
    mgr = FaultCaseManager()
    cases_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cases", "fault_cases.json"))
    with open(cases_path, "r", encoding="utf-8") as f:
        cases_data = json.load(f)

    for c in cases_data:
        case_obj = FaultCase.model_validate(c)
        mgr.register_case(case_obj)

    return mgr


def test_fault_case_loading_and_search(populated_case_manager):
    """Verify 15 fault cases are loaded and searchable by alarm, asset, and symptom."""
    mgr = populated_case_manager
    assert len(mgr.list_all()) >= 15

    # Alarm search
    cases_3025 = mgr.search_by_alarm("ALM-3025")
    assert len(cases_3025) >= 2
    assert any("CASE-2025-0318-Y52" == c.case_id for c in cases_3025)

    # Symptom keyword search
    oil_cases = mgr.search_by_symptom("油溫")
    assert len(oil_cases) >= 1
    assert any(c.case_id == "CASE-2025-0820-Y52" for c in oil_cases)


def test_root_cause_status_segregation(populated_case_manager):
    """Verify strict segregation between confirmed and suspected root causes."""
    mgr = populated_case_manager

    # Confirmed case
    case_conf = mgr.get_case("CASE-2025-0318-Y52")
    assert case_conf is not None
    assert case_conf.root_cause_status == RootCauseStatus.CONFIRMED.value
    assert "接頭鬆脫" in case_conf.confirmed_cause

    # Suspected case
    case_susp = mgr.get_case("CASE-2025-0610-Y52")
    assert case_susp is not None
    assert case_susp.root_cause_status == RootCauseStatus.SUSPECTED.value
    assert "疑似" in case_conf.confirmed_cause or "疑似" in case_susp.confirmed_cause


def test_historical_case_cannot_elevate_to_current_confirmed_cause():
    """Verify safety rule: historical root cause must NOT be elevated to current confirmed cause."""
    pkg = EvidencePackage()
    ev_hist = EvidenceRef(
        evidence_id="E_HIST_1",
        source_id="CASE-2025-0318-Y52",
        claim_domain=ClaimDomain.HISTORICAL_CASE.value,
        authority_status="active",
        content_snippet="入側編碼器接頭鬆脫 (connector loose)"
    )
    pkg.add_evidence(ev_hist)

    verifier = DeterministicVerifier(pkg)

    # Illegal attempt: claiming historical case as current confirmed root cause
    illegal_claim = ClaimItem(
        statement="本次故障已證實成因為編碼器接頭鬆脫",
        claim_type="CONFIRMED_CAUSE",
        is_actionable=False,
        evidence_ids=["E_HIST_1"]
    )

    res = verifier.verify_all([illegal_claim])
    assert res.passed is False
    assert any("歷史案例" in reason and "不可直接作為本次已證實成因" in reason for reason in res.failure_reasons)


def test_dual_track_image_registry_and_approval_gate():
    """Verify image dual-track separation and candidate review promotion gate."""
    reg = ImageRegistry()

    structured = ImageStructuredMetadata(
        image_id="IMG-TEST-001",
        asset_id="Y52",
        component="Y52-ENC-01",
        defect_type="connector_loose",
        description="自動模型標記之接頭退牙鬆脫跡象",
        tags=["編碼器", "接頭"],
        bounding_boxes=[BoundingBox(label="loose_connector", box=[0.3, 0.4, 0.6, 0.7], confidence=0.88)],
        review_status=ApprovalStatus.CANDIDATE.value
    )
    raw = RawImageMetadata(
        image_path="data/images/test.jpg",
        width=1920,
        height=1080,
        file_format="JPEG",
        captured_at="2026-09-23T10:00:00+08:00",
        checksum="sha256:test"
    )

    reg.register_image("IMG-TEST-001", structured, raw)
    record = reg.get_image("IMG-TEST-001")
    assert record is not None
    assert record.structured_track.review_status == ApprovalStatus.CANDIDATE.value

    # Approved-only query should return empty
    approved_results = reg.search_by_defect("connector_loose", approved_only=True)
    assert len(approved_results) == 0

    # Engineer reviews and approves
    success = reg.approve_image_metadata("IMG-TEST-001", reviewer="Chief_Engineer_Lin")
    assert success is True
    assert record.structured_track.review_status == ApprovalStatus.APPROVED.value
    assert record.structured_track.reviewed_by == "Chief_Engineer_Lin"

    # Now approved-only query finds the record
    approved_results_after = reg.search_by_defect("connector_loose", approved_only=True)
    assert len(approved_results_after) == 1
