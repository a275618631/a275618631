# -*- coding: utf-8 -*-
"""
Evidence Package Builder for Grounded Factory RAG.
Converts ranked/reranked NormalizedBlocks into formal EvidenceRefs and bundles them
into an EvidencePackage preserving full source document provenance and authority metadata.
"""

from typing import List, Optional, Dict, Any
from core.schema import NormalizedBlock, EvidenceRef, ClaimDomain
from core.evidence import EvidencePackage


class EvidenceBuilder:
    """
    Constructs immutable EvidencePackage from retrieved chunks.
    Ensures every snippet retains block_id, document_id, page number, and authority status.
    """

    @staticmethod
    def build(
        chunks: List[NormalizedBlock],
        prefix: str = "EV-",
        query_context: Optional[str] = None
    ) -> EvidencePackage:
        """Alias for build_package."""
        return EvidenceBuilder.build_package(chunks=chunks, prefix=prefix, query_context=query_context)

    @staticmethod
    def build_package(
        chunks: List[NormalizedBlock],
        prefix: str = "EV-",
        query_context: Optional[str] = None
    ) -> EvidencePackage:
        """
        Build EvidencePackage from candidate NormalizedBlocks.
        
        Args:
            chunks: Ordered list of NormalizedBlocks (after reranking and threshold gating).
            prefix: Prefix for generated evidence IDs (default 'EV-' -> EV-001, EV-002, ...).
            query_context: Optional user query string for tracing.
            
        Returns:
            EvidencePackage containing indexed EvidenceRefs and block lineage.
        """
        pkg = EvidencePackage()

        for idx, block in enumerate(chunks, start=1):
            evidence_id = f"{prefix}{idx:03d}"
            
            # Infer claim domain from block metadata, block_type, or heading path
            raw_domain = block.metadata.get("claim_domain") or block.metadata.get("domain") or ""
            if not raw_domain:
                if block.block_type == "procedure_step":
                    domain = ClaimDomain.PROCEDURE.value
                elif block.block_type in ("warning", "safety_notice"):
                    domain = ClaimDomain.SAFETY.value
                else:
                    h_path = " > ".join(block.heading_path).lower()
                    if "safety" in h_path or "warning" in h_path or "caution" in h_path or "危險" in h_path or "注意" in h_path:
                        domain = ClaimDomain.SAFETY.value
                    elif "sop" in h_path or "procedure" in h_path or "步驟" in h_path or "作業" in h_path:
                        domain = ClaimDomain.PROCEDURE.value
                    elif "case" in h_path or "troubleshoot" in h_path or "案例" in h_path:
                        domain = ClaimDomain.HISTORICAL_CASE.value
                    elif "spec" in h_path or "parameter" in h_path or "規格" in h_path or "參數" in h_path:
                        domain = ClaimDomain.DESIGN_CONFIGURATION.value
                    else:
                        domain = ClaimDomain.CURRENT_STATE.value
            else:
                domain = raw_domain

            # Authority status resolution
            auth_status = "active"
            if block.metadata.get("is_obsolete", False) or block.metadata.get("approval_status") == "superseded":
                auth_status = "superseded"
            elif block.metadata.get("approval_status") == "candidate":
                auth_status = "candidate"

            # Create EvidenceRef preserving strict provenance
            ref = EvidenceRef(
                evidence_id=evidence_id,
                source_id=block.document_id,
                block_id=block.block_id,
                page=block.page,
                bbox=block.bbox,
                claim_domain=domain,
                authority_status=auth_status,
                content_snippet=block.content.strip(),
                metadata={
                    "heading_path": block.heading_path,
                    "block_type": block.block_type,
                    "parser": block.parser,
                    "parser_version": block.parser_version,
                    "parse_confidence": block.parse_confidence,
                    "reranker_rank": block.metadata.get("reranker_rank", idx),
                    "reranker_score": block.metadata.get("reranker_score", 0.0),
                    "rrf_score": block.metadata.get("rrf_score", 0.0),
                    "query_context": query_context
                }
            )

            pkg.add_evidence(evidence=ref, block=block)

        return pkg
