from __future__ import annotations

from app.core.evidence import EvidenceBuilder
from app.core.models import Evidence, TelemetryEvent


class EvidenceAgent:
    """Normalizes telemetry into a stable evidence board without executing any system actions."""

    def __init__(self) -> None:
        self.builder = EvidenceBuilder()

    def collect(self, events: list[TelemetryEvent]) -> list[Evidence]:
        return self.builder.from_events(events)

