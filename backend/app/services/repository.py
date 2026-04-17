from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Incident
from ..schemas import AnalyzeRequest, DashboardStats, VideoAnalysisResponse
from .detection import DetectionResult


def create_incident(
    db: Session, payload: AnalyzeRequest, detection: DetectionResult
) -> Incident:
    incident = Incident(
        source_name=payload.source_name,
        area_name=payload.area_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        captured_at=payload.captured_at,
        vehicle_count=payload.vehicle_count,
        riders_detected=detection.riders_detected,
        violations_detected=detection.violations_detected,
        confidence_score=detection.confidence_score,
        image_url=payload.image_url,
        evidence_notes=detection.evidence_notes,
        source_type=payload.source_type,
        stream_id=getattr(payload, "stream_id", None),
        frame_index=getattr(payload, "frame_index", None),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def list_incidents(db: Session) -> list[Incident]:
    query = select(Incident).order_by(Incident.captured_at.desc())
    return list(db.scalars(query))


def get_dashboard_stats(db: Session) -> DashboardStats:
    totals = db.execute(
        select(
            func.count(Incident.id),
            func.coalesce(func.sum(Incident.violations_detected), 0),
            func.coalesce(func.sum(Incident.riders_detected), 0),
            func.coalesce(func.avg(Incident.confidence_score), 0.0),
        )
    ).one()

    hotspots = db.execute(
        select(
            Incident.area_name,
            func.sum(Incident.violations_detected).label("violations"),
            func.count(Incident.id).label("incidents"),
            func.avg(Incident.latitude).label("latitude"),
            func.avg(Incident.longitude).label("longitude"),
        )
        .group_by(Incident.area_name)
        .order_by(func.sum(Incident.violations_detected).desc())
        .limit(5)
    ).all()

    source_mix = db.execute(
        select(
            Incident.source_type,
            func.count(Incident.id).label("incidents"),
            func.sum(Incident.violations_detected).label("violations"),
        )
        .group_by(Incident.source_type)
        .order_by(func.count(Incident.id).desc())
    ).all()

    return DashboardStats(
        total_incidents=totals[0],
        total_violations=totals[1],
        total_riders=totals[2],
        average_confidence=round(float(totals[3]), 2),
        top_hotspots=[
            {
                "area_name": row.area_name,
                "violations": row.violations,
                "incidents": row.incidents,
                "latitude": round(float(row.latitude), 5),
                "longitude": round(float(row.longitude), 5),
            }
            for row in hotspots
        ],
        source_mix=[
            {
                "source_type": row.source_type,
                "incidents": row.incidents,
                "violations": row.violations or 0,
            }
            for row in source_mix
        ],
    )


def build_video_analysis_response(incidents: list[Incident], source_name: str, area_name: str, source_type: str, frames_processed: int) -> VideoAnalysisResponse:
    total_riders = sum(item.riders_detected for item in incidents)
    total_violations = sum(item.violations_detected for item in incidents)
    avg_confidence = (
        round(sum(item.confidence_score for item in incidents) / len(incidents), 2)
        if incidents
        else 0.0
    )
    return VideoAnalysisResponse(
        source_name=source_name,
        area_name=area_name,
        source_type=source_type,
        frames_processed=frames_processed,
        incidents_created=len(incidents),
        total_riders_detected=total_riders,
        total_violations_detected=total_violations,
        average_confidence=avg_confidence,
        created_incident_ids=[item.id for item in incidents],
    )


def seed_demo_data(db: Session) -> None:
    existing_count = db.scalar(select(func.count(Incident.id)))
    if existing_count:
        return

    demo_incidents = [
        Incident(
            source_name="Bypass Drone 1",
            area_name="Bypass Circle",
            latitude=25.6101,
            longitude=85.1432,
            vehicle_count=12,
            riders_detected=12,
            violations_detected=4,
            confidence_score=0.82,
            captured_at=datetime.fromisoformat("2026-04-17T08:00:00"),
            source_type="drone",
            evidence_notes="Seeded demo incident for dashboard preview.",
        ),
        Incident(
            source_name="Station Road Cam",
            area_name="Station Road",
            latitude=25.6155,
            longitude=85.1520,
            vehicle_count=7,
            riders_detected=7,
            violations_detected=2,
            confidence_score=0.76,
            captured_at=datetime.fromisoformat("2026-04-17T08:15:00"),
            source_type="traffic_camera",
            evidence_notes="Seeded demo incident for dashboard preview.",
        ),
        Incident(
            source_name="Riverfront Aerial",
            area_name="Riverfront",
            latitude=25.6033,
            longitude=85.1309,
            vehicle_count=11,
            riders_detected=11,
            violations_detected=3,
            confidence_score=0.8,
            captured_at=datetime.fromisoformat("2026-04-17T09:00:00"),
            source_type="aerial",
            evidence_notes="Seeded demo incident for dashboard preview.",
        ),
    ]
    db.add_all(demo_incidents)
    db.commit()
