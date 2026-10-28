"""
Hybrid Retrieval Pipeline with Reciprocal Rank Fusion, Authority Filtering,
and Evidence Package Generation.
"""

from typing import List, Dict, Any, Optional
from core.schema import NormalizedBlock, SourceDocument, EvidenceRef, ClaimDomain
from core.authority import AuthorityResolver
from core.evidence import EvidencePackage
from adapters.retrieval.sqlite_fts import SQLiteFTSRetriever
from adapters.retrieval.vector_store import DenseVectorStore
from adapters.rerank.bge_reranker import BGEReranker


class HybridRetrievalPipeline:
    """
    Orchestrates Exact ID + FTS5 + Dense Vector + RRF Fusion + Reranking + Authority Gate.
    """

    def __init__(
        self,
        fts_retriever: SQLiteFTSRetriever,
        vector_store: DenseVectorStore,
        reranker: BGEReranker,
        authority_resolver: AuthorityResolver
    ) -> None:
        self.fts = fts_retriever
        self.vector_store = vector_store
        self.reranker = reranker
        self.authority = authority_resolver

    def retrieve(
        self,
        query: str,
        claim_domain: ClaimDomain = ClaimDomain.PROCEDURE,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> EvidencePackage:
        """
        Execute full retrieval pipeline and return packaged evidences.
        """
        # 1. Multi-channel retrieval
        fts_results = self.fts.search(query, top_k=top_k * 2, filters=filters)
        vec_results = self.vector_store.search(query, top_k=top_k * 2, filters=filters)

        # 2. Reciprocal Rank Fusion (RRF)
        # score = 1 / (60 + rank)
        rrf_scores: Dict[str, float] = {}
        block_map: Dict[str, NormalizedBlock] = {}

        for rank, b in enumerate(fts_results):
            block_map[b.block_id] = b
            rrf_scores[b.block_id] = rrf_scores.get(b.block_id, 0.0) + (1.0 / (60.0 + rank + 1.0))

        for rank, b in enumerate(vec_results):
            block_map[b.block_id] = b
            rrf_scores[b.block_id] = rrf_scores.get(b.block_id, 0.0) + (1.0 / (60.0 + rank + 1.0))

        # Sort combined candidates
        sorted_block_ids = sorted(rrf_scores.keys(), key=lambda bid: rrf_scores[bid], reverse=True)
        fusion_candidates = [block_map[bid] for bid in sorted_block_ids]

        # 3. Rerank with Cross-Encoder scoring
        reranked_blocks = self.reranker.rerank(query, fusion_candidates)

        # 4. Authority & Revision Filter Gate (Exclude superseded or obsolete documents)
        evidence_pkg = EvidencePackage()
        ev_counter = 1

        for b in reranked_blocks:
            is_active, auth_status, _ = self.authority.is_document_active(b.document_id)
            if not is_active:
                # Exclude superseded/obsolete from active evidence
                continue

            doc = self.authority.get_document(b.document_id)
            ev_id = f"E{ev_counter}"
            ev_ref = EvidenceRef(
                evidence_id=ev_id,
                source_id=b.document_id,
                block_id=b.block_id,
                page=b.page,
                bbox=b.bbox,
                claim_domain=claim_domain.value,
                authority_status=auth_status.value,
                content_snippet=b.content[:300]
            )
            evidence_pkg.add_evidence(ev_ref, block=b, doc=doc)
            ev_counter += 1

            if len(evidence_pkg.evidences) >= top_k:
                break

        return evidence_pkg

    @staticmethod
    def locate_table_cells(block: NormalizedBlock, query_term: str) -> List[Dict[str, Any]]:
        """
        Locate exact cells in a table block matching query_term without generative hallucination.
        """
        if not block.table_data or not block.table_data.cells:
            return []

        q_lower = query_term.lower()
        matched = []
        for cell in block.table_data.cells:
            if q_lower in cell.value.lower() or q_lower in cell.col_header.lower():
                matched.append({
                    "row_idx": cell.row_idx,
                    "col_idx": cell.col_idx,
                    "header": cell.col_header,
                    "value": cell.value,
                    "block_id": block.block_id,
                    "page": block.page
                })
        return matched
