from pathlib import Path
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


def test_office_chain_reaches_high_or_critical() -> None:
    settings = get_settings()
    payload = json.loads((settings.datasets_dir / "samples" / "officeToPowerShell.json").read_text(encoding="utf-8"))
    result = _conductor().analyze("officeToPowerShell", payload["events"], "test", "template")

    rule_ids = {item.rule_id for item in result.findings}
    assert {"DL-WIN-001", "DL-PS-001", "DL-CR-001", "DL-NET-001"}.issubset(rule_ids)
    assert result.scores.risk_label.value in {"High", "Critical"}
    assert result.scores.confidence_score >= 80
    assert [step.stage for step in result.attack_chain][:4] == [
        "Initial Access",
        "Execution",
        "Defense Evasion",
        "Credential Access",
    ]
    stage_map = {step.stage: step for step in result.attack_chain}
    assert stage_map["Initial Access"].timestamp < stage_map["Execution"].timestamp


def test_ambiguous_admin_powershell_stays_low_risk() -> None:
    settings = get_settings()
    payload = json.loads((settings.datasets_dir / "samples" / "adminPowerShellInventory.json").read_text(encoding="utf-8"))
    result = _conductor().analyze("adminPowerShellInventory", payload["events"], "test", "template")

    rule_ids = {item.rule_id for item in result.findings}
    assert rule_ids == {"DL-WIN-002"}
    assert result.scores.risk_label.value == "Low"
    assert result.scores.confidence_score >= 55
    assert [step.stage for step in result.attack_chain] == ["Execution"]
