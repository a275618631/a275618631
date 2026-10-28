"""
Unit Tests for MVP-1 Structured Ingestion and Retrieval Pipeline.
Tests StructuredParser, SQLite FTS5 exact code matching, DenseVectorStore,
BGEReranker, and Table Row/Cell cell-level extraction.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.schema import SourceDocument, ApprovalStatus, ClaimDomain
from core.authority import AuthorityResolver
from adapters.parsers.structured_parser import StructuredParser
from adapters.retrieval.sqlite_fts import SQLiteFTSRetriever
from adapters.retrieval.vector_store import DenseVectorStore
from adapters.rerank.bge_reranker import BGEReranker
from adapters.retrieval.hybrid_pipeline import HybridRetrievalPipeline


@pytest.fixture
def sample_pipeline():
    """Setup an ingested pipeline fixture with realistic factory documents."""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "source"))
    parser = StructuredParser()
    fts = SQLiteFTSRetriever(":memory:")
    vec = DenseVectorStore()
    reranker = BGEReranker(calibrated_threshold=0.20)
    auth = AuthorityResolver()

    # Documents to ingest
    doc_specs = [
        ("DOC-Y52-SOP-001", "SOP", "Rev.C", "DOC-Y52-SOP-001.md"),
        ("DOC-Y52-ALARM-001", "ALARM_LIST", "Rev.A", "DOC-Y52-ALARM-001.md"),
        ("DOC-Y52-SPEC-001", "SPECIFICATION", "Rev.B", "DOC-Y52-SPEC-001.md"),
        ("DOC-Y52-SAFETY-001", "SAFETY_MANUAL", "Rev.A", "DOC-Y52-SAFETY-001.md"),
        ("DOC-Y52-MANUAL-002", "OEM_MANUAL", "Rev.B", "DOC-Y52-MANUAL-002.md"),
    ]

    all_blocks = []
    for doc_id, s_type, rev, fname in doc_specs:
        fpath = os.path.join(data_dir, fname)
        doc = SourceDocument(
            document_id=doc_id,
            source_type=s_type,
            revision=rev,
            effective_from="2026-01-01",
            approval_status=ApprovalStatus.APPROVED.value,
            checksum=f"sha256-{doc_id}",
            source_path=fpath,
            asset_scope=["Y52"]
        )
        auth.register_document(doc)
        blocks = parser.parse(fpath, doc)
        all_blocks.extend(blocks)

    fts.index_blocks(all_blocks)
    vec.add_blocks(all_blocks)

    pipeline = HybridRetrievalPipeline(fts, vec, reranker, auth)
    return pipeline, all_blocks, auth


def test_structured_parser_headings_and_tables(sample_pipeline):
    """Verify structured parser extracts hierarchical headings and table data."""
    _, all_blocks, _ = sample_pipeline
    table_blocks = [b for b in all_blocks if b.block_type == "table"]
    assert len(table_blocks) >= 2

    # Check SOP table
    sop_table = next(b for b in table_blocks if b.document_id == "DOC-Y52-SOP-001")
    assert sop_table.table_data is not None
    assert "潤滑部位" in sop_table.table_data.headers
    assert len(sop_table.table_data.rows) >= 3
    assert any("Mobilgear 600 XP 220" in cell.value for cell in sop_table.table_data.cells)


def test_exact_alarm_code_lookup(sample_pipeline):
    """Verify exact alarm code lookup achieves Top-1 precision."""
    pipeline, _, _ = sample_pipeline

    # ALM-3025 lookup
    pkg_3025 = pipeline.retrieve("ALM-3025", claim_domain=ClaimDomain.FAILURE_MODE, top_k=3)
    evs_3025 = list(pkg_3025.evidences.values())
    assert len(evs_3025) > 0
    top_block = pkg_3025.get_block(evs_3025[0].block_id)
    assert top_block is not None
    assert "ALM-3025" in top_block.content or "ALM-3025" in " ".join(top_block.heading_path)
    all_content = " ".join([pkg_3025.get_block(e.block_id).content for e in evs_3025 if pkg_3025.get_block(e.block_id)])
    assert "ALM-3025" in all_content
    assert "編碼器" in all_content or "Encoder" in all_content

    # ALM-4102 lookup
    pkg_4102 = pipeline.retrieve("ALM-4102", claim_domain=ClaimDomain.FAILURE_MODE, top_k=3)
    evs_4102 = list(pkg_4102.evidences.values())
    assert len(evs_4102) > 0
    top_block_4102 = pkg_4102.get_block(evs_4102[0].block_id)
    assert "ALM-4102" in top_block_4102.content or "ALM-4102" in " ".join(top_block_4102.heading_path)
    all_content_4102 = " ".join([pkg_4102.get_block(e.block_id).content for e in evs_4102 if pkg_4102.get_block(e.block_id)])
    assert "ALM-4102" in all_content_4102
    assert "油溫" in all_content_4102 or "冷卻水" in all_content_4102


def test_exact_tag_id_lookup(sample_pipeline):
    """Verify exact tag ID lookup returns spec definitions."""
    pipeline, _, _ = sample_pipeline

    # Y52-ENC-FB lookup
    pkg_tag = pipeline.retrieve("Y52-ENC-FB", claim_domain=ClaimDomain.DESIGN_CONFIGURATION, top_k=3)
    evs_tag = list(pkg_tag.evidences.values())
    assert len(evs_tag) > 0
    b = pkg_tag.get_block(evs_tag[0].block_id)
    assert "Y52-ENC-FB" in b.content
    assert "rpm" in b.content

    # Y52-OIL-PRS01 lookup
    pkg_oil = pipeline.retrieve("Y52-OIL-PRS01", claim_domain=ClaimDomain.DESIGN_CONFIGURATION, top_k=3)
    evs_oil = list(pkg_oil.evidences.values())
    assert len(evs_oil) > 0
    b_oil = pkg_oil.get_block(evs_oil[0].block_id)
    assert "18.5 ~ 21.0 bar" in b_oil.content


def test_table_cell_deterministic_location(sample_pipeline):
    """Verify table row/cell location without generative hallucination."""
    _, all_blocks, _ = sample_pipeline
    sop_table = next(b for b in all_blocks if b.document_id == "DOC-Y52-SOP-001" and b.block_type == "table")

    matches = HybridRetrievalPipeline.locate_table_cells(sop_table, "Mobilgear 600 XP 220")
    assert len(matches) > 0
    assert matches[0]["value"] == "Mobilgear 600 XP 220 (ISO VG 220)"
    assert matches[0]["header"] == "潤滑油品規格"


def test_authority_exclusion_in_retrieval(sample_pipeline):
    """Verify superseded document is excluded from retrieved evidence package."""
    pipeline, _, auth = sample_pipeline

    # Mark DOC-Y52-ALARM-001 as superseded
    alarm_doc = auth.get_document("DOC-Y52-ALARM-001")
    alarm_doc.approval_status = ApprovalStatus.SUPERSEDED.value

    pkg = pipeline.retrieve("ALM-3025", claim_domain=ClaimDomain.FAILURE_MODE, top_k=5)
    for ev in pkg.evidences.values():
        assert ev.source_id != "DOC-Y52-ALARM-001"
