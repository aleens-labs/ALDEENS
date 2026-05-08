from __future__ import annotations

from app.core.detections import DetectionEngine
from app.core.models import DetectionFinding, Evidence


class DetectionAgent:
    """Applies deterministic defensive rules to normalized evidence."""

    def __init__(self, engine: DetectionEngine) -> None:
        self.engine = engine

    def inspect(self, evidence: list[Evidence]) -> list[DetectionFinding]:
        return self.engine.evaluate(evidence)

