# -*- coding: utf-8 -*-
"""
Sprint 1 Unit Tests: Docling Parser & Parser Router.
Validates BaseParser inheritance, non-silent error handling, and canonical provenance retention.
"""

import os
import pytest
from core.interfaces import BaseParser
from core.schema import SourceDocument, NormalizedBlock
from adapters.parsers.docling_parser import DoclingParser
from adapters.parsers.router import ParserRouter
from adapters.parsers.structured_parser import StructuredParser


SAMPLE_PDF = os.path.join(
    os.path.dirname(__file__), "..", "data", "demo", "committed_license_safe_samples", "DOC-01_Y52_Digital_Operation_Manual.pdf"
)
SAMPLE_TABLE_PDF = os.path.join(
    os.path.dirname(__file__), "..", "data", "demo", "committed_license_safe_samples", "DOC-04_Y52_Lubrication_Schedule_Table.pdf"
)
SAMPLE_MD = os.path.join(
    os.path.dirname(__file__), "..", "data", "manuals", "Y52_manual.md"
)


def test_docling_parser_inheritance():
    parser = DoclingParser(enable_ocr=False)
    assert isinstance(parser, BaseParser)
    assert parser.parser_name == "docling"
    assert parser.parser_version == "2.131.0"


def test_docling_parser_non_silent_on_missing_file():
    parser = DoclingParser(enable_ocr=False)
    doc_meta = SourceDocument(
        document_id="NON_EXISTENT_DOC",
        source_type="OEM_MANUAL",
        revision="Rev.A",
        effective_from="2026-01-01",
        checksum="dummy_checksum_12345",
        source_path="non_existent.pdf"
    )
    with pytest.raises((FileNotFoundError, RuntimeError)):
        parser.parse("non_existent_file_path_12345.pdf", doc_meta)


def test_docling_parser_real_pdf_extraction():
    if not os.path.exists(SAMPLE_PDF):
        pytest.skip(f"Sample PDF not found at {SAMPLE_PDF}")

    parser = DoclingParser(enable_ocr=False)
    doc_meta = SourceDocument(
        document_id="DOC-TEST-001",
        source_type="SOP",
        revision="Rev.A",
        effective_from="2026-01-01",
        checksum="test_sha_01",
        source_path=SAMPLE_PDF
    )
    blocks = parser.parse(SAMPLE_PDF, doc_meta)

    assert len(blocks) > 0, "Docling should extract at least one block from real PDF"
    
    # Check Canonical Schema compliance
    for b in blocks:
        assert isinstance(b, NormalizedBlock)
        assert b.document_id == "DOC-TEST-001"
        assert b.page >= 1
        assert b.parser == "docling"
        assert b.parser_version == "2.131.0"
        assert isinstance(b.heading_path, list)
        assert len(b.content.strip()) > 0
        if b.bbox is not None:
            assert len(b.bbox) == 4
            assert all(isinstance(coord, (int, float)) for coord in b.bbox)


def test_docling_parser_table_extraction():
    if not os.path.exists(SAMPLE_TABLE_PDF):
        pytest.skip(f"Sample table PDF not found at {SAMPLE_TABLE_PDF}")

    parser = DoclingParser(enable_ocr=False)
    doc_meta = SourceDocument(
        document_id="DOC-TEST-TABLE",
        source_type="OEM_MANUAL",
        revision="Rev.A",
        effective_from="2026-01-01",
        checksum="test_sha_04",
        source_path=SAMPLE_TABLE_PDF
    )
    blocks = parser.parse(SAMPLE_TABLE_PDF, doc_meta)
    table_blocks = [b for b in blocks if b.block_type == "table"]

    assert len(table_blocks) > 0, "Docling should detect structured table in table PDF"
    first_tbl = table_blocks[0]
    assert first_tbl.table_data is not None
    assert len(first_tbl.table_data.headers) > 0
    assert len(first_tbl.table_data.rows) > 0
    assert "|" in first_tbl.content


def test_parser_router_dispatch():
    router = ParserRouter(enable_ocr=False)
    assert isinstance(router, BaseParser)

    doc_meta = SourceDocument(
        document_id="ROUTER-TEST",
        source_type="OEM_MANUAL",
        revision="Rev.A",
        effective_from="2026-01-01",
        checksum="dummy_checksum_12345",
        source_path="dummy"
    )

    # 1. Markdown route
    if os.path.exists(SAMPLE_MD):
        md_blocks = router.parse(SAMPLE_MD, doc_meta)
        assert len(md_blocks) > 0
        assert router.last_run_metrics["parser_used"] == "structured_parser"
        assert router.last_run_metrics["success"] is True

    # 2. PDF route
    if os.path.exists(SAMPLE_PDF):
        pdf_blocks = router.parse(SAMPLE_PDF, doc_meta)
        assert len(pdf_blocks) > 0
        assert router.last_run_metrics["parser_used"] == "docling"
        assert router.last_run_metrics["success"] is True

    # 3. Unsupported format route (must fail non-silently)
    unsupported_path = os.path.join(os.path.dirname(__file__), "dummy.xyz")
    with open(unsupported_path, "w") as f:
        f.write("test")
    try:
        with pytest.raises(RuntimeError) as excinfo:
            router.parse(unsupported_path, doc_meta)
        assert "Unsupported file format" in str(excinfo.value)
    finally:
        if os.path.exists(unsupported_path):
            os.remove(unsupported_path)
