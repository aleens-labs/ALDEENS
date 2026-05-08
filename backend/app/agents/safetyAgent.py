from __future__ import annotations

from app.core.guardrails import GuardrailReviewer
from app.core.models import DetectionFinding, GuardrailResult


class SafetyAgent:
    """Enforces the defensive-only reporting boundary before narrative generation."""

    def __init__(self, reviewer: GuardrailReviewer) -> None:
        self.reviewer = reviewer

    def review(self, findings: list[DetectionFinding], requested_mode: str) -> GuardrailResult:
        return self.reviewer.review(findings, requested_mode)

