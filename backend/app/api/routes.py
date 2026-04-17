from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    AnalyzeRequest,
    DashboardStats,
    IncidentResponse,
    PipelineStatus,
    VideoAnalysisResponse,
)
from ..services.detection import build_detector, cv2_is_available
from ..services.repository import (
    build_video_analysis_response,
    create_incident,
    get_dashboard_stats,
    list_incidents,
)
from ..services.video import persist_upload, sample_video_frames, summarize_detector


router = APIRouter(prefix="/api/v1", tags=["helmetwatch"])
detector = build_detector()


@router.get("/health")
def healthcheck():
    return {"status": "ok"}


@router.post("/analyze", response_model=IncidentResponse)
def analyze_frame(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    detection = detector.analyze(payload, frame_index=payload.frame_index)
    incident = create_incident(db, payload, detection)
    return incident


@router.get("/incidents", response_model=list[IncidentResponse])
def incidents(db: Session = Depends(get_db)):
    return list_incidents(db)


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@router.get("/pipeline", response_model=PipelineStatus)
def pipeline_status():
    summary = summarize_detector(detector)
    notes = [
        "Use /api/v1/analyze for structured single-frame ingestion.",
        "Use /api/v1/analyze/video for uploaded video sampling.",
        "Replace the heuristic detector with a trained helmet model for production.",
    ]
    return PipelineStatus(
        detector_name=summary["detector_name"],
        model_mode=summary["model_mode"],
        cv2_available=cv2_is_available(),
        notes=notes,
    )


@router.post("/analyze/video", response_model=VideoAnalysisResponse)
async def analyze_video(
    media: UploadFile = File(...),
    source_name: str = Form(...),
    area_name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    captured_at: datetime = Form(...),
    source_type: str = Form("traffic_camera"),
    sample_every: int = Form(30),
    db: Session = Depends(get_db),
):
    file_path = persist_upload(media.filename or "upload.mp4", await media.read())
    observations = sample_video_frames(
        file_path=file_path,
        source_name=source_name,
        area_name=area_name,
        latitude=latitude,
        longitude=longitude,
        captured_at=captured_at,
        source_type=source_type,
        sample_every=sample_every,
    )

    incidents = []
    for observation in observations:
        payload = observation.payload.model_copy(
            update={
                "stream_id": file_path.stem,
                "frame_index": observation.frame_index,
            }
        )
        detection = detector.analyze(
            payload,
            frame=observation.frame,
            frame_index=observation.frame_index,
        )
        incidents.append(create_incident(db, payload, detection))

    return build_video_analysis_response(
        incidents=incidents,
        source_name=source_name,
        area_name=area_name,
        source_type=source_type,
        frames_processed=len(observations),
    )
