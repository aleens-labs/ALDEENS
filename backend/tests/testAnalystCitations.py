import json

from app.agents.analystAgent import AnalystAgent
from app.agents.chainAgent import ChainAgent
from app.agents.conductor import Conductor
from app.agents.detectionAgent import DetectionAgent
from app.agents.evidenceAgent import EvidenceAgent
from app.agents.safetyAgent import SafetyAgent
from app.agents.tacticAgent import TacticAgent
from app.core.audit import AuditTrail
from app.core.config import get_settings
from app.core.detections import DetectionEngine, RuleBook
from app.core.guardrails import GuardrailReviewer
from app.core.memory import FeedbackMemory
from app.core.scoring import ScoreEngine
from app.core.telemetry import TelemetryNormalizer


def _conductor() -> Conductor:
    settings = get_settings()
    return Conductor(
        settings=settings,
        normalizer=TelemetryNormalizer(),
        evidence_agent=EvidenceAgent(),
        detection_agent=DetectionAgent(DetectionEngine(RuleBook(settings.rules_dir))),
        tactic_agent=TacticAgent(),
        chain_agent=ChainAgent(),
        analyst_agent=AnalystAgent(settings),
        safety_agent=SafetyAgent(GuardrailReviewer(settings)),
        scoring=ScoreEngine(),
        audit_trail=AuditTrail(settings.audit_log_path),
        memory=FeedbackMemory(settings.feedback_db_path, settings.memory_dir),
    )


def test_template_report_contains_evidence_citations() -> None:
    settings = get_settings()
    payload = json.loads((settings.datasets_dir / "samples" / "officeToPowerShell.json").read_text(encoding="utf-8"))
    result = _conductor().analyze("officeToPowerShell", payload["events"], "test", "template")

    assert "[Evidence:" in result.analyst_brief
    assert "Raw: event-" in result.analyst_brief
    assert all(step.raw_references for step in result.attack_chain)

