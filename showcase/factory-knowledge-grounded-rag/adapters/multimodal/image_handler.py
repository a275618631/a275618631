"""
Multimodal Image Handler for Industrial Equipment and Defect Visual Assets.
Implements the Dual-Track Architecture:
Track 1: Structured Description Track (asset, component, defect_type, bboxes, tags, review_status)
Track 2: Raw Image Track (image_path, resolution, captured_at, checksum)
Enforces safety loop: AI visual features default to 'candidate', approved only after human review.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from core.schema import ApprovalStatus


class BoundingBox(BaseModel):
    label: str
    box: List[float] = Field(..., description="[ymin, xmin, ymax, xmax] in normalized 0-1 range")
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class ImageStructuredMetadata(BaseModel):
    image_id: str
    asset_id: str
    component: str
    defect_type: str  # connector_loose, oil_leak, wire_wear, normal, etc.
    description: str
    tags: List[str] = Field(default_factory=list)
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    review_status: str = Field(ApprovalStatus.CANDIDATE.value, description="candidate or approved")
    reviewed_by: Optional[str] = None


class RawImageMetadata(BaseModel):
    image_path: str
    width: int
    height: int
    file_format: str
    captured_at: str
    checksum: str


class DualTrackImageRecord(BaseModel):
    image_id: str
    structured_track: ImageStructuredMetadata
    raw_track: RawImageMetadata


class ImageRegistry:
    """
    Manages factory equipment photos and visual evidence across both tracks.
    """

    def __init__(self) -> None:
        self._records: Dict[str, DualTrackImageRecord] = {}

    def register_image(
        self,
        image_id: str,
        structured_info: ImageStructuredMetadata,
        raw_info: RawImageMetadata
    ) -> None:
        self._records[image_id] = DualTrackImageRecord(
            image_id=image_id,
            structured_track=structured_info,
            raw_track=raw_info
        )

    def get_image(self, image_id: str) -> Optional[DualTrackImageRecord]:
        return self._records.get(image_id)

    def search_by_defect(self, defect_type: str, approved_only: bool = False) -> List[DualTrackImageRecord]:
        results = []
        for r in self._records.values():
            if r.structured_track.defect_type.lower() == defect_type.lower():
                if approved_only and r.structured_track.review_status != ApprovalStatus.APPROVED.value:
                    continue
                results.append(r)
        return results

    def search_by_asset(self, asset_id: str, approved_only: bool = False) -> List[DualTrackImageRecord]:
        results = []
        for r in self._records.values():
            if r.structured_track.asset_id == asset_id:
                if approved_only and r.structured_track.review_status != ApprovalStatus.APPROVED.value:
                    continue
                results.append(r)
        return results

    def approve_image_metadata(self, image_id: str, reviewer: str) -> bool:
        """Human engineer review gate: promote candidate to approved."""
        record = self.get_image(image_id)
        if record:
            record.structured_track.review_status = ApprovalStatus.APPROVED.value
            record.structured_track.reviewed_by = reviewer
            return True
        return False
