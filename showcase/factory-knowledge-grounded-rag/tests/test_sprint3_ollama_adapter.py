import pytest
from core.evidence import EvidencePackage, EvidenceItem
from core.response_schema import FactoryDiagnosisResponse
from adapters.llm.ollama_adapter import OllamaAdapter, OllamaServiceUnavailableError, SchemaValidationError


def test_ollama_unreachable_exception():
    """Verify explicit exception when connecting to invalid endpoint."""
    adapter = OllamaAdapter(endpoint="http://127.0.0.1:99999", timeout=1)
    with pytest.raises(OllamaServiceUnavailableError):
        adapter.generate_structured("test", FactoryDiagnosisResponse)


def test_ollama_empty_evidence_abstain():
    """Verify immediate safe abstain without calling remote LLM when evidence is empty."""
    adapter = OllamaAdapter(endpoint="http://127.0.0.1:11434")
    empty_pkg = EvidencePackage(evidences={})
    resp = adapter.generate_diagnosis("廠長辦公室冷氣不冷", empty_pkg)

    assert resp.verification_status == "ABSTAINED"
    assert len(resp.approved_procedure_steps) == 0
    assert len(resp.unknowns) >= 1
    assert len(resp.claims) == 1
    assert resp.claims[0].is_actionable is False


def test_ollama_conflict_detection():
    """Verify immediate conflict gate trigger when conflict flag is detected."""
    adapter = OllamaAdapter(endpoint="http://127.0.0.1:11434")
    pkg = EvidencePackage(evidences={
        "EV-001": EvidenceItem(evidence_id="EV-001", source_id="DOC-A", claim_domain="PROCEDURE", content_snippet="扭矩 45 Nm"),
        "EV-002": EvidenceItem(evidence_id="EV-002", source_id="DOC-B", claim_domain="PROCEDURE", content_snippet="扭矩 60 Nm")
    })
    resp = adapter.generate_diagnosis("主軸扭矩該設多少", pkg, is_conflict=True)

    assert resp.verification_status == "CONFLICT_DETECTED"
    assert len(resp.approved_procedure_steps) == 0
    assert "衝突" in resp.unknowns[0]
