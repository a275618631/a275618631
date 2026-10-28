import pytest
from core.schema import NormalizedBlock
from core.evidence_builder import EvidenceBuilder


def test_evidence_builder_provenance_and_indexing():
    """Verify EvidenceBuilder creates EvidencePackage while retaining block_id, document_id, and domain."""
    blocks = [
        NormalizedBlock(
            block_id="b-sop-01",
            document_id="DOC-08_Y52",
            page=3,
            block_type="procedure_step",
            parser="test_parser",
            parser_version="1.0",
            content="主軸軸承預緊力矩標準為 45 Nm，使用扭力扳手緊固。",
            metadata={"domain": "PROCEDURE"}
        ),
        NormalizedBlock(
            block_id="b-hist-02",
            document_id="DOC-11_HIST",
            page=1,
            block_type="paragraph",
            parser="test_parser",
            parser_version="1.0",
            content="2025-04 曾因進油管濾網堵塞導致同型號主軸油壓過低報警。",
            metadata={"domain": "HISTORICAL_CASE"}
        )
    ]

    pkg = EvidenceBuilder.build(blocks)
    assert len(pkg.evidences) == 2
    assert pkg.get_evidence("EV-001") is not None
    assert pkg.get_evidence("EV-002") is not None

    ev1 = pkg.get_evidence("EV-001")
    assert ev1.block_id == "b-sop-01"
    assert ev1.source_doc_id == "DOC-08_Y52"
    assert ev1.claim_domain == "PROCEDURE"
    assert "45 Nm" in ev1.content_snippet

    ev2 = pkg.get_evidence("EV-002")
    assert ev2.claim_domain == "HISTORICAL_CASE"

    empty_pkg = EvidenceBuilder.build([])
    assert len(empty_pkg.evidences) == 0
