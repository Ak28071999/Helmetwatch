from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from ..config import UPLOADS_DIR
from ..schemas import AnalyzeRequest
from .detection import HelmetDetector, cv2


@dataclass
class VideoFrameObservation:
    frame_index: int
    payload: AnalyzeRequest
    frame: object | None


def persist_upload(filename: str, content: bytes) -> Path:
    suffix = Path(filename).suffix or ".bin"
    safe_name = f"{uuid4().hex}{suffix}"
    target = UPLOADS_DIR / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


def sample_video_frames(
    file_path: Path,
    source_name: str,
    area_name: str,
    latitude: float,
    longitude: float,
    captured_at,
    source_type: str,
    sample_every: int = 30,
) -> list[VideoFrameObservation]:
    observations: list[VideoFrameObservation] = []

    if cv2 is None:
        observations.append(
            VideoFrameObservation(
                frame_index=0,
                payload=AnalyzeRequest(
                    source_name=source_name,
                    area_name=area_name,
                    latitude=latitude,
                    longitude=longitude,
                    captured_at=captured_at,
                    image_url=f"/media/uploads/{file_path.name}",
                    vehicle_count=6,
                    source_type=source_type,
                ),
                frame=None,
            )
        )
        return observations

    capture = cv2.VideoCapture(str(file_path))
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        if frame_index % max(sample_every, 1) == 0:
            observations.append(
                VideoFrameObservation(
                    frame_index=frame_index,
                    payload=AnalyzeRequest(
                        source_name=source_name,
                        area_name=area_name,
                        latitude=latitude,
                        longitude=longitude,
                        captured_at=captured_at,
                        image_url=f"/media/uploads/{file_path.name}",
                        vehicle_count=0,
                        source_type=source_type,
                    ),
                    frame=frame,
                )
            )
        frame_index += 1

    capture.release()
    if not observations:
        observations.append(
            VideoFrameObservation(
                frame_index=0,
                payload=AnalyzeRequest(
                    source_name=source_name,
                    area_name=area_name,
                    latitude=latitude,
                    longitude=longitude,
                    captured_at=captured_at,
                    image_url=f"/media/uploads/{file_path.name}",
                    vehicle_count=4,
                    source_type=source_type,
                ),
                frame=None,
            )
        )
    return observations


def summarize_detector(detector: HelmetDetector) -> dict:
    return {
        "detector_name": getattr(detector, "name", detector.__class__.__name__),
        "model_mode": getattr(detector, "model_mode", "custom"),
    }
