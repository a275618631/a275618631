# -*- coding: utf-8 -*-
"""
Sprint 1 Unit Tests: FixedWindowChunker & StructureAwareChunker.
Validates BaseChunker contracts, table integrity preservation, and provenance tracking.
"""

import pytest
from core.interfaces import BaseChunker
from core.schema import NormalizedBlock, TableData, TableCell
from adapters.chunking.fixed_window import FixedWindowChunker
from adapters.chunking.structure_aware import StructureAwareChunker


def _build_test_block(b_type: str, content: str, page: int = 1, t_data: TableData = None) -> NormalizedBlock:
    return NormalizedBlock(
        block_id=f"TEST-P{page}-B1",
        document_id="DOC-CHUNK-01",
        page=page,
        block_type=b_type,
        heading_path=["SOP 01", "Procedure"],
        content=content,
        table_data=t_data,
        parser="test_parser",
        parser_version="1.0.0",
        metadata={"source_checksum": "abcdef1234567890"}
    )


def test_chunker_inheritance():
    fixed = FixedWindowChunker(target_size=200, overlap=20)
    struct = StructureAwareChunker(max_chunk_size=300)
    assert isinstance(fixed, BaseChunker)
    assert isinstance(struct, BaseChunker)


def test_fixed_window_chunker_sliding_window():
    chunker = FixedWindowChunker(target_size=100, overlap=20, min_size=10)
    long_text = "A" * 250
    block = _build_test_block("paragraph", long_text)
    
    chunks = chunker.chunk([block])
    assert len(chunks) >= 3
    for c in chunks:
        assert isinstance(c, NormalizedBlock)
        assert c.document_id == "DOC-CHUNK-01"
        assert c.metadata["chunk_strategy"] == "fixed_window"
        assert c.block_id.startswith("DOC-CHUNK-01-P1-")


def test_structure_aware_chunker_table_preservation():
    # Construct a large table that exceeds max_chunk_size
    headers = ["Parameter", "Target", "Tolerance", "Unit", "Remark"]
    rows = [
        [f"Param_{i}", f"{100 + i * 5}", "±0.5", "mm", f"Inspection note {i}"]
        for i in range(15)
    ]
    cells = [
        TableCell(row_idx=r, col_idx=c, col_header=headers[c], value=rows[r][c])
        for r in range(len(rows)) for c in range(len(headers))
    ]
    t_data = TableData(headers=headers, rows=rows, cells=cells)
    
    table_content = "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n"
    for r in rows:
        table_content += "| " + " | ".join(r) + " |\n"

    block = _build_test_block("table", table_content, page=2, t_data=t_data)
    
    chunker = StructureAwareChunker(max_chunk_size=250, preserve_tables=True)
    chunks = chunker.chunk([block])

    assert len(chunks) > 1, "Large table should be partitioned into multiple chunks"
    
    # Verify EVERY sub-chunk retains the table header
    for c in chunks:
        assert c.block_type == "table"
        assert c.table_data is not None
        assert c.table_data.headers == headers, "Header row must be preserved in all table chunks"
        assert "| Parameter | Target | Tolerance | Unit | Remark |" in c.content
        assert c.document_id == "DOC-CHUNK-01"
        assert c.page == 2
        assert c.metadata["chunk_strategy"] == "structure_aware"


def test_structure_aware_preserves_safety_atomic():
    warning_text = "警告：拆卸主軸前必須先切斷氣源與電源，並執行 LOTO 上鎖程序。"
    block = _build_test_block("warning", warning_text)
    
    chunker = StructureAwareChunker(max_chunk_size=300)
    chunks = chunker.chunk([block])
    
    assert len(chunks) == 1
    assert chunks[0].block_type == "warning"
    assert chunks[0].content == warning_text
    assert chunks[0].heading_path == ["SOP 01", "Procedure"]
