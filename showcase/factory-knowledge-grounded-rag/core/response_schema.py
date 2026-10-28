"""
Structured Response Schema for Factory Floor Troubleshooting and Diagnosis.
Mandates strict partition between Confirmed Facts, Historical Cases,
Current Hypotheses, Approved Procedures, and Field Checks.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from core.verifier import ClaimItem, VerificationResult


class FactoryDiagnosisResponse(BaseModel):
    """
    Standard structured response delivered to engineering operators.
    Each section is strictly bounded to prevent hallucinated causal links.
    """
    query: str
    asset_id: Optional[str] = None

    # Section 1: Confirmed Current Facts (from active observations and spec tables)
    confirmed_facts: List[str] = Field(
        default_factory=list,
        description="Facts verified against current sensor tags or active specification sheets."
    )

    # Section 2: Historical Similar Cases (strictly historical reference, NOT current root cause)
    historical_similar_cases: List[str] = Field(
        default_factory=list,
        description="Past work orders and similar symptoms. Must NOT be asserted as confirmed root cause."
    )

    # Section 3: Current Hypotheses & Engineering Judgments
    current_hypotheses: List[str] = Field(
        default_factory=list,
        description="Potential trouble causes undergoing field investigation."
    )

    # Section 4: Approved Procedure Steps
    approved_procedure_steps: List[str] = Field(
        default_factory=list,
        description="Verifiable, actionable steps cited directly from active SOP or OEM manuals."
    )

    # Section 5: Unknowns & Missing Information
    unknowns: List[str] = Field(
        default_factory=list,
        description="Gaps in available documentation or telemetry."
    )

    # Section 6: Required Field Checks
    required_field_checks: List[str] = Field(
        default_factory=list,
        description="Manual verification actions required by technicians before taking action."
    )

    # Structured claim tracking for deterministic verification
    claims: List[ClaimItem] = Field(
        default_factory=list,
        description="Fine-grained claim list checked by the deterministic verifier."
    )

    verification_status: Optional[str] = None
    verification_details: Optional[Dict[str, Any]] = None
