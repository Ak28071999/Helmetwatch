from datetime import datetime

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    source_name: str = Field(..., examples=["Ward 12 Junction Camera"])
    area_name: str = Field(..., examples=["Ward 12"])
    latitude: float
    longitude: float
    captured_at: datetime
    image_url: str | None = None
    vehicle_count: int = Field(default=0, ge=0)
    source_type: str = Field(default="aerial")
    stream_id: str | None = None
    frame_index: int | None = None


class IncidentResponse(BaseModel):
    id: int
    source_name: str
    area_name: str
    latitude: float
    longitude: float
    captured_at: datetime
    vehicle_count: int
    riders_detected: int
    violations_detected: int
    confidence_score: float
    image_url: str | None
    evidence_notes: str | None
    source_type: str
    stream_id: str | None
    frame_index: int | None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_incidents: int
    total_violations: int
    total_riders: int
    average_confidence: float
    top_hotspots: list[dict]
    source_mix: list[dict]


class PipelineStatus(BaseModel):
    detector_name: str
    model_mode: str
    cv2_available: bool
    notes: list[str]


class VideoAnalysisResponse(BaseModel):
    source_name: str
    area_name: str
    source_type: str
    frames_processed: int
    incidents_created: int
    total_riders_detected: int
    total_violations_detected: int
    average_confidence: float
    created_incident_ids: list[int]
