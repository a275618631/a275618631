# -*- coding: utf-8 -*-
"""
Sprint 2 Unit Tests: Reciprocal Rank Fusion (RRF).
Validates BaseFusion contracts, deduplication, and rank metadata preservation.
"""

import pytest
from core.interfaces import BaseFusion
from core.schema import NormalizedBlock
from adapters.fusion.rrf import RRFFusion


def _make_block(cid: str, doc_id: str) -> NormalizedBlock:
    return NormalizedBlock(
        block_id=cid,
        document_id=doc_id,
        page=1,
        block_type="paragraph",
        heading_path=["Test"],
        content=f"Content for {cid}",
        parser="docling",
        parser_version="2.131.0"
    )


def test_rrf_fusion_contracts_and_deduplication():
    rrf = RRFFusion(k=60)
    assert isinstance(rrf, BaseFusion)

    b1 = _make_block("C1", "D1")
    b2 = _make_block("C2", "D2")
    b3 = _make_block("C3", "D3")

    # List 1 (FTS): C1 (rank 1), C2 (rank 2)
    # List 2 (Dense): C2 (rank 1), C3 (rank 2)
    list1 = [b1, b2]
    list2 = [b2, b3]

    fused = rrf.fuse([list1, list2], top_k=3)
    assert len(fused) == 3

    # C2 appears in both lists, so its RRF score is highest: (1/(60+2) + 1/(60+1))
    assert fused[0].block_id == "C2"
    assert "rrf_score" in fused[0].metadata
    assert fused[0].metadata["fts_rank"] == 2
    assert fused[0].metadata["dense_rank"] == 1
