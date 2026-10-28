"""
Canonical Schemas for Factory Knowledge Base and Grounded Industrial RAG.
Tool-agnostic, local-first, offline-capable core data contracts.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ClaimDomain(str, Enum):
    """Claim domain classification for authority resolution."""
    CURRENT_STATE = "CURRENT_STATE"
    PROCEDURE = "PROCEDURE"
    SAFETY = "SAFETY"
    DESIGN_CONFIGURATION = "DESIGN_CONFIGURATION"
    HISTORICAL_CASE = "HISTORICAL_CASE"
    FAILURE_MODE = "FAILURE_MODE"


class ApprovalStatus(str, Enum):
    APPROVED = "approved"
    CANDIDATE = "candidate"
    OBSOLETE = "obsolete"
    SUPERSEDED = "superseded"
    DRAFT = "draft"
    REJECTED = "rejected"


class RootCauseStatus(str, Enum):
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    UNKNOWN = "unknown"


class ObservationQuality(str, Enum):
    GOOD = "good"
    BAD = "bad"
    UNCERTAIN = "uncertain"


class TerminologyStatus(str, Enum):
    APPROVED = "approved"
    CANDIDATE = "candidate"
    DEPRECATED = "deprecated"


class ResolutionState(str, Enum):
    EXACT = "EXACT"
    CANDIDATE = "CANDIDATE"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class SourceDocument(BaseModel):
    """
    Source Document Schema representing formal manuals, SOPs, drawings, and logs.
    """
    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(..., description="Unique document identifier")
    source_type: str = Field(..., description="Type of source: OEM_MANUAL, SOP, DRAWING, etc.")
    revision: str = Field(..., description="Document revision code, e.g. Rev.A, Rev.B")
    effective_from: str = Field(..., description="Effective start date, ISO 8601 or YYYY-MM-DD")
    effective_to: Optional[str] = Field(None, description="Effective end date if superseded or expired")
    approval_status: str = Field(ApprovalStatus.APPROVED.value, description="Lifecycle approval status")
    asset_scope: List[str] = Field(default_factory=list, description="Target asset IDs this document applies to")
    checksum: str = Field(..., description="Cryptographic checksum (sha256)")
    source_path: str = Field(..., description="Relative or absolute path in Source Vault")
    supersedes: Optional[str] = Field(None, description="Previous document_id superseded by this revision")
    superseded_by: Optional[str] = Field(None, description="Newer document_id that supersedes this revision")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TableCell(BaseModel):
    row_idx: int
    col_idx: int
    col_header: str
    value: str
    raw_value: Optional[str] = None


class TableData(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    cells: List[TableCell] = Field(default_factory=list)


class NormalizedBlock(BaseModel):
    """
    Normalized Block Schema representing granular chunks with full provenance.
    """
    model_config = ConfigDict(extra="ignore")

    block_id: str = Field(..., description="Unique block ID: {doc_id}-P{page}-B{idx}")
    document_id: str = Field(..., description="Parent document_id")
    page: int = Field(..., description="1-indexed page number")
    block_type: str = Field(..., description="procedure_step, warning, table, heading, paragraph, etc.")
    heading_path: List[str] = Field(default_factory=list, description="Section hierarchy path")
    content: str = Field(..., description="Text content of the block")
    table_data: Optional[TableData] = Field(None, description="Structured table data if block is a table")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x1, y1, x2, y2] in normalized or pt units")
    parser: str = Field(..., description="Parser name that extracted this block (e.g. docling, structured_parser)")
    parser_version: str = Field(..., description="Version of the parser")
    parse_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Asset(BaseModel):
    """
    Asset Schema representing plants, lines, machines, and physical components.
    """
    model_config = ConfigDict(extra="ignore")

    asset_id: str = Field(..., description="Unique canonical asset identifier, e.g. Y52, Y52-PE-01")
    canonical_name: str = Field(..., description="Canonical human-readable name")
    parent_asset_id: Optional[str] = Field(None, description="Parent asset ID for hierarchy navigation")
    asset_type: str = Field(..., description="line, machine, subsystem, component, sensor, actuator")
    status: str = Field("active", description="active, decommissioned, maintenance")
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Terminology(BaseModel):
    """
    Terminology Registry Schema based on W3C SKOS (prefLabel / altLabels / scope).
    """
    model_config = ConfigDict(extra="ignore")

    term_id: str = Field(..., description="Unique terminology record ID")
    canonical_entity_id: str = Field(..., description="Mapped canonical asset or concept ID")
    pref_label: str = Field(..., description="Standard preferred label")
    alt_labels: List[str] = Field(default_factory=list, description="Slang, abbreviations, legacy names")
    scope: str = Field("global", description="Scope or asset boundary, e.g. Y52, global")
    language: str = Field("zh-TW", description="BCP 47 language code")
    status: str = Field(TerminologyStatus.APPROVED.value, description="approved, candidate, deprecated")
    notes: Optional[str] = None


class FaultCase(BaseModel):
    """
    Fault Case Schema representing historical maintenance work orders and incident records.
    Strictly isolates symptom, observed signals, and confirmed root cause.
    """
    model_config = ConfigDict(extra="ignore")

    case_id: str = Field(..., description="Unique case record ID, e.g. CASE-2025-0318-Y52")
    asset_id: str = Field(..., description="Target asset ID")
    symptom: str = Field(..., description="Reported symptom or trouble description")
    alarm_ids: List[str] = Field(default_factory=list, description="Triggered alarm codes, e.g. ['A3025']")
    observed_signals: List[Dict[str, Any]] = Field(default_factory=list, description="Observed tag values/trends")
    checks_performed: List[str] = Field(default_factory=list, description="Troubleshooting steps carried out")
    confirmed_cause: str = Field(..., description="Identified root cause (only if verified)")
    root_cause_status: str = Field(RootCauseStatus.CONFIRMED.value, description="confirmed, suspected, unknown")
    action_taken: str = Field(..., description="Corrective actions taken")
    result: str = Field(..., description="Resolution outcome, e.g. restored, temporary fix")
    source_ids: List[str] = Field(default_factory=list, description="Work order or log IDs")
    review_status: str = Field(ApprovalStatus.CANDIDATE.value, description="candidate, approved, rejected")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CurrentObservation(BaseModel):
    """
    Current State Schema representing real-time/recent sensor, PLC, or historian observations.
    Never mixed directly into static document embeddings.
    """
    model_config = ConfigDict(extra="ignore")

    asset_id: str = Field(..., description="Associated asset ID")
    tag_id: str = Field(..., description="Sensor or PLC Tag ID, e.g. Y52-ENC-FB")
    value: Any = Field(..., description="Observed value (float, int, str, bool)")
    unit: str = Field(..., description="Physical engineering unit (e.g. rpm, bar, mm, C)")
    observed_at: str = Field(..., description="Observation timestamp, ISO 8601")
    quality: str = Field(ObservationQuality.GOOD.value, description="Data quality: good, bad, uncertain")
    source: str = Field(..., description="Source system: historian, plc, scada, manual")


class EvidenceRef(BaseModel):
    """
    Evidence Reference Schema for grounding claims in verified sources.
    """
    model_config = ConfigDict(extra="ignore")

    evidence_id: str = Field(..., description="Unique evidence handle in this query context (e.g. E1, E2)")
    source_id: str = Field(..., description="Document ID or Case ID or Observation tag")
    block_id: Optional[str] = Field(None, description="NormalizedBlock ID if applicable")
    page: Optional[int] = Field(None, description="Page number")
    bbox: Optional[List[float]] = Field(None, description="Bounding box if region-specific")
    claim_domain: str = Field(..., description="ClaimDomain value: PROCEDURE, SAFETY, etc.")
    authority_status: str = Field("active", description="active, superseded, candidate, unverified")
    content_snippet: str = Field("", description="Exact extracted snippet supporting the claim")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def source_doc_id(self) -> str:
        """Compatibility property for source document identifier."""
        return self.source_id
