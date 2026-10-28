"""
Claim-Domain Authority Matrix and Revision Lifecycle Resolver.
Ensures obsolete/superseded documents are excluded from active procedures,
and detects unresolved conflicts between active documents.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from pydantic import BaseModel, Field
from core.schema import ClaimDomain, SourceDocument, ApprovalStatus


class AuthorityStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    OBSOLETE = "obsolete"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    UNVERIFIED = "unverified"


class ConflictRecord(BaseModel):
    domain: ClaimDomain
    asset_id: str
    conflicting_doc_ids: List[str]
    description: str


class AuthorityResolver:
    """
    Resolves source document authority based on ClaimDomain and revision lifecycle.
    """

    # Primary source types preferred for each claim domain
    DOMAIN_SOURCE_PRIORITY = {
        ClaimDomain.CURRENT_STATE: ["HISTORIAN", "PLC", "LIVE_OBSERVATION", "ALARM_SYSTEM"],
        ClaimDomain.PROCEDURE: ["SOP", "APPROVED_PROCEDURE", "OEM_MANUAL"],
        ClaimDomain.SAFETY: ["PLANT_SAFETY_RULE", "OEM_SAFETY_MANUAL", "SOP"],
        ClaimDomain.DESIGN_CONFIGURATION: ["AS_BUILT_DRAWING", "ECN", "OEM_SPECIFICATION"],
        ClaimDomain.HISTORICAL_CASE: ["CMMS", "WORK_ORDER", "INCIDENT_REPORT"],
        ClaimDomain.FAILURE_MODE: ["OEM_TROUBLESHOOTING", "ENGINEERING_RCA", "CMMS"]
    }

    def __init__(self) -> None:
        self._docs: Dict[str, SourceDocument] = {}

    def register_document(self, doc: SourceDocument) -> None:
        """Register a source document."""
        self._docs[doc.document_id] = doc

    def get_document(self, doc_id: str) -> Optional[SourceDocument]:
        return self._docs.get(doc_id)

    def is_document_active(self, doc_id: str) -> Tuple[bool, AuthorityStatus, str]:
        """
        Check if document is active or superseded/obsolete.
        Returns: (is_active, authority_status, reason)
        """
        doc = self.get_document(doc_id)
        if not doc:
            return False, AuthorityStatus.UNVERIFIED, f"文件 {doc_id} 不存在"

        # Check explicit status
        if doc.approval_status == ApprovalStatus.SUPERSEDED.value:
            return False, AuthorityStatus.SUPERSEDED, f"文件 {doc_id} 已被取代 (superseded)"

        if doc.approval_status == ApprovalStatus.OBSOLETE.value:
            return False, AuthorityStatus.OBSOLETE, f"文件 {doc_id} 已廢棄 (obsolete)"

        if doc.superseded_by:
            # Check if the replacement exists and is approved
            repl = self.get_document(doc.superseded_by)
            if repl and repl.approval_status == ApprovalStatus.APPROVED.value:
                return False, AuthorityStatus.SUPERSEDED, f"文件 {doc_id} 已被 {doc.superseded_by} 取代"

        return True, AuthorityStatus.ACTIVE, "文件有效且可作為活動依據"

    def filter_active_documents(self, doc_ids: List[str]) -> List[str]:
        """Filter out superseded or obsolete documents."""
        active = []
        for did in doc_ids:
            is_act, _, _ = self.is_document_active(did)
            if is_act:
                active.append(did)
        return active

    def detect_procedure_conflict(self, procedures: List[Dict[str, Any]]) -> Optional[ConflictRecord]:
        """
        Detect conflicts between two or more active procedures for the same parameter or action.
        Each procedure item: {doc_id: str, asset_id: str, parameter: str, value: str}
        """
        if len(procedures) < 2:
            return None

        # Check parameter values
        param_map: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        for p in procedures:
            doc_id = p["doc_id"]
            is_act, _, _ = self.is_document_active(doc_id)
            if not is_act:
                continue
            key = (p.get("asset_id", "GLOBAL"), p["parameter"])
            param_map.setdefault(key, []).append((doc_id, str(p["value"]).strip()))

        for (asset_id, param), entries in param_map.items():
            if len(entries) > 1:
                # Compare values
                values = {val for _, val in entries}
                if len(values) > 1:
                    conflicting_docs = [did for did, _ in entries]
                    return ConflictRecord(
                        domain=ClaimDomain.PROCEDURE,
                        asset_id=asset_id,
                        conflicting_doc_ids=conflicting_docs,
                        description=f"在設備 {asset_id} 上檢測到衝突的 {param} 設定值: {dict(entries)}"
                    )

        return None
