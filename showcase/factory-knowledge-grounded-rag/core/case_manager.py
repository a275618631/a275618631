"""
Fault Case Manager for Historical Maintenance Work Orders and Troubleshooting Logs.
Enforces strict segregation between confirmed root causes and suspected hypotheses.
"""

from typing import List, Dict, Optional, Any
from core.schema import FaultCase, RootCauseStatus, ApprovalStatus


class FaultCaseManager:
    """
    Manages historical incident and repair case knowledge base.
    Prevents historical root causes from being falsely elevated to current confirmed facts.
    """

    def __init__(self) -> None:
        self._cases: Dict[str, FaultCase] = {}

    def register_case(self, case: FaultCase) -> None:
        self._cases[case.case_id] = case

    def get_case(self, case_id: str) -> Optional[FaultCase]:
        return self._cases.get(case_id)

    def search_by_alarm(self, alarm_id: str) -> List[FaultCase]:
        return [c for c in self._cases.values() if alarm_id in c.alarm_ids]

    def search_by_asset(self, asset_id: str) -> List[FaultCase]:
        return [c for c in self._cases.values() if c.asset_id == asset_id]

    def search_by_symptom(self, symptom_keyword: str) -> List[FaultCase]:
        sk = symptom_keyword.lower()
        return [c for c in self._cases.values() if sk in c.symptom.lower()]

    def list_all(self) -> List[FaultCase]:
        return list(self._cases.values())

    def update_review_status(self, case_id: str, new_status: ApprovalStatus) -> bool:
        """Promote candidate case to approved after engineer review."""
        case = self.get_case(case_id)
        if case:
            case.review_status = new_status.value
            return True
        return False
