"""
Evidence Package and Lineage Tracking for Factory Knowledge Base.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from core.schema import EvidenceRef, NormalizedBlock, SourceDocument

# Alias for backward compatibility
EvidenceItem = EvidenceRef


class EvidencePackage(BaseModel):
    """
    Bundled evidence package provided to generation and verification gates.
    """
    evidences: Dict[str, EvidenceRef] = Field(default_factory=dict)
    blocks: Dict[str, NormalizedBlock] = Field(default_factory=dict)
    documents: Dict[str, SourceDocument] = Field(default_factory=dict)

    def add_evidence(
        self,
        evidence: EvidenceRef,
        block: Optional[NormalizedBlock] = None,
        doc: Optional[SourceDocument] = None
    ) -> None:
        self.evidences[evidence.evidence_id] = evidence
        if block:
            self.blocks[block.block_id] = block
        if doc:
            self.documents[doc.document_id] = doc

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRef]:
        return self.evidences.get(evidence_id)

    def get_block(self, block_id: str) -> Optional[NormalizedBlock]:
        return self.blocks.get(block_id)

    def get_document(self, doc_id: str) -> Optional[SourceDocument]:
        return self.documents.get(doc_id)

    def list_evidence_ids(self) -> List[str]:
        return list(self.evidences.keys())
