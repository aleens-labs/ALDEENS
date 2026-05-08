from __future__ import annotations

from app.core.models import DetectionFinding, TacticHit
from app.core.tactics import TacticMapper


class TacticAgent:
    """Maps validated findings into ATT&CK tactics and techniques."""

    def __init__(self) -> None:
        self.mapper = TacticMapper()

    def map(self, findings: list[DetectionFinding]) -> list[TacticHit]:
        return self.mapper.map_findings(findings)

