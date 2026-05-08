from __future__ import annotations

from app.core.chain import AttackChainBuilder
from app.core.models import ChainStep, DetectionFinding


class ChainAgent:
    """Reconstructs a defensible incident chain from deterministic findings."""

    def __init__(self) -> None:
        self.builder = AttackChainBuilder()

    def rebuild(self, findings: list[DetectionFinding]) -> list[ChainStep]:
        return self.builder.reconstruct(findings)

