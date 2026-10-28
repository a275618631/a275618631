"""
Base LLM Adapter Definition.
"""

from abc import abstractmethod
from typing import Any, Optional
from core.interfaces import BaseLLM
from core.evidence import EvidencePackage
from core.response_schema import FactoryDiagnosisResponse


class AbstractFactoryLLM(BaseLLM):
    """Abstract class for factory diagnosis generation."""

    @abstractmethod
    def generate_diagnosis(
        self,
        query: str,
        evidence_pkg: EvidencePackage,
        asset_id: Optional[str] = None
    ) -> FactoryDiagnosisResponse:
        """Generate structured diagnosis grounded in evidence package."""
        pass
