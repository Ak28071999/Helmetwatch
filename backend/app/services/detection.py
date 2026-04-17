from dataclasses import dataclass
from typing import Protocol

from ..schemas import AnalyzeRequest

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - optional at runtime
    cv2 = None

@dataclass
class DetectionResult:
    riders_detected: int
    violations_detected: int
    confidence_score: float
    evidence_notes: str


class HelmetDetector(Protocol):
    def analyze(self, payload: AnalyzeRequest, frame=None, frame_index: int | None = None) -> DetectionResult:
        ...


class HeuristicHelmetDetector:
    """Fallback detector with a CV-aware interface for future model upgrades."""

    name = "heuristic-detector"
    model_mode = "rule-based"

    def analyze(self, payload: AnalyzeRequest, frame=None, frame_index: int | None = None) -> DetectionResult:
        estimated_riders = max(payload.vehicle_count, 1)

        if frame is not None and cv2 is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = float(gray.mean())
            contrast = float(gray.std())
            estimated_riders = max(payload.vehicle_count, int(mean_brightness // 28))
            raw_violation_ratio = min(max((155 - mean_brightness) / 255, 0.18), 0.62)
            confidence = min(0.58 + (contrast / 255) + (estimated_riders * 0.012), 0.97)
            note = (
                f"Heuristic frame analysis at frame {frame_index or 0}. "
                "Swap in a trained helmet model for evidentiary use."
            )
        else:
            raw_violation_ratio = 0.34
            confidence = min(0.55 + (estimated_riders * 0.03), 0.96)
            note = (
                "Payload-only analysis completed. For production, use drone or traffic-camera "
                "frames with a trained helmet detector."
            )

        violations = max(1, round(estimated_riders * raw_violation_ratio)) if estimated_riders else 0
        return DetectionResult(
            riders_detected=estimated_riders,
            violations_detected=min(violations, estimated_riders),
            confidence_score=round(confidence, 2),
            evidence_notes=note,
        )


def build_detector() -> HeuristicHelmetDetector:
    return HeuristicHelmetDetector()


def cv2_is_available() -> bool:
    return cv2 is not None
