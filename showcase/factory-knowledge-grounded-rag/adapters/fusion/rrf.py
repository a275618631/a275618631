# -*- coding: utf-8 -*-
"""
Reciprocal Rank Fusion (RRF) Adapter for Grounded Industrial RAG.
Implements BaseFusion contract fusing multiple ranked lists with canonical deduplication.
Preserves individual retriever ranks (fts_rank, dense_rank) and computed rrf_score.
"""

from typing import List, Dict, Any, Optional
from core.interfaces import BaseFusion
from core.schema import NormalizedBlock


class RRFFusion(BaseFusion):
    """
    Reciprocal Rank Fusion (RRF) algorithm:
    RRF_score(d) = sum_m ( w_m / (k + rank_m(d)) )
    Default k = 60.
    """

    def __init__(self, k: int = 60) -> None:
        self.k = k

    def fuse(
        self,
        ranked_lists: List[List[NormalizedBlock]],
        weights: Optional[List[float]] = None,
        top_k: int = 5
    ) -> List[NormalizedBlock]:
        if not ranked_lists:
            return []

        # If only one list provided, simply return sliced Top-K
        if len(ranked_lists) == 1:
            return ranked_lists[0][:top_k]

        w_list = weights if weights and len(weights) == len(ranked_lists) else [1.0] * len(ranked_lists)

        # Map: chunk_id -> {"block": NormalizedBlock, "rrf_score": float, "ranks": Dict[int, int]}
        scored_map: Dict[str, Dict[str, Any]] = {}

        for list_idx, (r_list, weight) in enumerate(zip(ranked_lists, w_list)):
            for rank_0, block in enumerate(r_list):
                rank_1 = rank_0 + 1
                cid = block.block_id
                score_contribution = weight / (self.k + rank_1)

                if cid not in scored_map:
                    scored_map[cid] = {
                        "block": block,
                        "rrf_score": 0.0,
                        "ranks": {}
                    }

                scored_map[cid]["rrf_score"] += score_contribution
                scored_map[cid]["ranks"][list_idx] = rank_1

        # Sort by rrf_score descending
        sorted_items = sorted(
            scored_map.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        fused_blocks: List[NormalizedBlock] = []
        for item in sorted_items[:top_k]:
            orig_block = item["block"]
            # Clone block and enrich metadata
            new_meta = dict(orig_block.metadata)
            new_meta["rrf_score"] = round(item["rrf_score"], 6)

            # Record ranks (list 0 = FTS, list 1 = Dense if passed in standard order)
            if 0 in item["ranks"]:
                new_meta["fts_rank"] = item["ranks"][0]
            if 1 in item["ranks"]:
                new_meta["dense_rank"] = item["ranks"][1]

            fused_block = NormalizedBlock(
                block_id=orig_block.block_id,
                document_id=orig_block.document_id,
                page=orig_block.page,
                block_type=orig_block.block_type,
                heading_path=list(orig_block.heading_path),
                content=orig_block.content,
                table_data=orig_block.table_data,
                bbox=orig_block.bbox,
                parser=orig_block.parser,
                parser_version=orig_block.parser_version,
                parse_confidence=orig_block.parse_confidence,
                metadata=new_meta
            )
            fused_blocks.append(fused_block)

        return fused_blocks
