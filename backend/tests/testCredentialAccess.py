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


def test_lsass_access_maps_to_credential_access() -> None:
    settings = get_settings()
    payload = json.loads((settings.datasets_dir / "samples" / "lsassAccessSignal.json").read_text(encoding="utf-8"))
    result = _conductor().analyze("lsassAccessSignal", payload["events"], "test", "template")

    assert any(item.rule_id == "DL-CR-001" for item in result.findings)
    assert any(item.technique_id == "T1003.001" for item in result.tactics)
    assert any(step.stage == "Credential Access" for step in result.attack_chain)
