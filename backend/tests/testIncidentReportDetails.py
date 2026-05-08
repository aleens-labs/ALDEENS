from __future__ import annotations

import json
from datetime import datetime, timezone

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
from app.core.lens_report_builder import build_template_report
from app.core.memory import FeedbackMemory
from app.core.models import (
    ChainStep,
    DetectionFinding,
    Evidence,
    FeedbackVerdict,
    RiskLabel,
    ScoreCard,
    ScoreComponent,
    SimilarCase,
    TacticHit,
)
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


def _make_evidence(
    *,
    evidence_id: str = "ev-1",
    raw_reference: str = "event-1",
    timestamp: datetime | None = None,
    process: str = "powershell.exe",
    process_id: str | None = None,
    parent_process: str | None = "winword.exe",
    parent_process_id: str | None = None,
    command_line: str | None = "powershell.exe -nop -w hidden -enc AAAA",
    host: str | None = "DESKTOP-01",
    user: str | None = "CORP\\john.doe",
    image_path: str | None = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    parent_image_path: str | None = r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    user_sid: str | None = "S-1-5-21-1",
    destination_ip: str | None = "192.168.1.20",
    source_ip: str | None = "10.0.0.15",
) -> Evidence:
    return Evidence(
        evidenceId=evidence_id,
        rawReference=raw_reference,
        summary="evidence-summary",
        timestamp=timestamp or datetime(2020, 10, 18, 7, 50, 5, tzinfo=timezone.utc),
        host=host,
        user=user,
        domain="CORP",
        userSid=user_sid,
        process=process,
        processId=process_id,
        parentProcess=parent_process,
        parentProcessId=parent_process_id,
        commandLine=command_line,
        imagePath=image_path,
        parentImagePath=parent_image_path,
        destinationIp=destination_ip,
        sourceIp=source_ip,
        eventId="1",
        provider="Microsoft-Windows-Sysmon",
    )


def _make_finding(evidence: list[Evidence], confidence: float = 0.22) -> DetectionFinding:
    return DetectionFinding(
        findingId="finding-1",
        ruleId="DL-CR-001",
        title="LSASS access signal",
        reason="Telemetry indicates contact with LSASS.",
        evidenceIds=[item.evidence_id for item in evidence],
        evidence=evidence,
        mitreTechnique="T1003.001",
        tactic="Credential Access",
        scoreContribution=35,
        confidenceContribution=confidence,
    )


def _make_powerfinding(evidence: list[Evidence]) -> DetectionFinding:
    return DetectionFinding(
        findingId="finding-2",
        ruleId="DL-WIN-002",
        title="Suspicious parent-child process chain",
        reason="PowerShell execution followed an Office parent chain.",
        evidenceIds=[item.evidence_id for item in evidence],
        evidence=evidence,
        mitreTechnique="T1059.001",
        tactic="Execution",
        scoreContribution=15,
        confidenceContribution=0.16,
    )


def _make_scores(confidence: int) -> ScoreCard:
    return ScoreCard(
        riskScore=66,
        riskLabel=RiskLabel.HIGH,
        confidenceScore=confidence,
        completeness=0.8,
        scoreTrace=[ScoreComponent(label="RULE-TRACE", value=35, reason="Detections fired.")],
        confidenceTrace=[ScoreComponent(label="RULE-TRACE", value=30, reason="Evidence aligned.")],
    )


def _make_tactics() -> list[TacticHit]:
    return [
        TacticHit(
            techniqueId="T1003.001",
            techniqueName="LSASS Memory",
            tactic="Credential Access",
            description="LSASS access observed.",
            confidence=0.66,
            relatedRules=["DL-CR-001"],
        ),
        TacticHit(
            techniqueId="T1059.001",
            techniqueName="PowerShell",
            tactic="Execution",
            description="PowerShell execution observed.",
            confidence=0.74,
            relatedRules=["DL-WIN-002"],
        ),
    ]


def _make_chain(evidence: list[Evidence]) -> list[ChainStep]:
    return [
        ChainStep(
            stage="Execution",
            timestamp=evidence[0].timestamp,
            summary="PowerShell execution followed an Office parent chain.",
            evidenceIds=[evidence[0].evidence_id],
            findingIds=["finding-2"],
            rawReferences=[evidence[0].raw_reference],
        )
    ]


def test_report_includes_full_command_line_when_available() -> None:
    settings = get_settings()
    payload = json.loads((settings.datasets_dir / "samples" / "officeToPowerShell.json").read_text(encoding="utf-8"))
    result = _conductor().analyze("officeToPowerShell", payload["events"], "test", "template")

    assert "## 7. Command Line Evidence" in result.analyst_brief
    assert "powershell.exe -NoProfile -WindowStyle Hidden -EncodedCommand" in result.analyst_brief


def test_report_handles_missing_command_line_telemetry() -> None:
    evidence = [_make_evidence(command_line=None)]
    report = build_template_report("missing-cmd", evidence, [], [], [], _make_scores(40), [])

    assert "Command line telemetry was not available in the uploaded logs." in report


def test_report_includes_readable_process_tree_when_parent_child_exists() -> None:
    settings = get_settings()
    payload = json.loads((settings.datasets_dir / "samples" / "officeToPowerShell.json").read_text(encoding="utf-8"))
    result = _conductor().analyze("officeToPowerShell", payload["events"], "test", "template")

    assert "## 6. Process Tree" in result.analyst_brief
    assert "winword.exe" in result.analyst_brief
    assert "powershell.exe" in result.analyst_brief
    assert "\\-- " in result.analyst_brief or "+-- " in result.analyst_brief


def test_report_marks_partial_process_tree_when_parent_child_is_incomplete() -> None:
    evidence = [
        _make_evidence(
            evidence_id="ev-1",
            process="winword.exe",
            parent_process=None,
            parent_image_path=None,
            command_line='"WINWORD.EXE" doc.docm',
        ),
        _make_evidence(
            evidence_id="ev-2",
            raw_reference="event-2",
            process="powershell.exe",
            parent_process=None,
            parent_image_path=None,
            command_line="powershell.exe -enc AAAA",
        ),
    ]
    findings = [_make_powerfinding(evidence[1:2])]
    report = build_template_report("partial-tree", evidence, findings, _make_tactics(), _make_chain(evidence[1:2]), _make_scores(55), [])

    assert "Process tree is partial because parent-child telemetry is incomplete." in report


def test_lsass_confidence_66_yields_validation_verdict() -> None:
    evidence = [_make_evidence()]
    findings = [_make_finding(evidence), _make_powerfinding(evidence)]
    report = build_template_report("lsass-66", evidence, findings, _make_tactics(), _make_chain(evidence), _make_scores(66), [])

    assert "Suspicious credential access activity requiring validation." in report


def test_lsass_confidence_70plus_yields_likely_malicious_verdict() -> None:
    evidence = [_make_evidence()]
    findings = [_make_finding(evidence), _make_powerfinding(evidence)]
    report = build_template_report("lsass-72", evidence, findings, _make_tactics(), _make_chain(evidence), _make_scores(72), [])

    assert "Likely malicious credential dumping attempt." in report


def test_false_positive_feedback_adds_validation_warning() -> None:
    evidence = [_make_evidence()]
    findings = [_make_finding(evidence)]
    feedback = [
        SimilarCase(
            ruleId="DL-CR-001",
            verdict=FeedbackVerdict.FALSE_POSITIVE,
            note="Seen during admin diagnostics.",
            count=2,
            datasetName="historical-case",
            seenAt="2026-04-20T00:00:00Z",
        )
    ]
    report = build_template_report("feedback-case", evidence, findings, _make_tactics(), _make_chain(evidence), _make_scores(66), feedback)

    assert "Prior analyst feedback includes false-positive markings, so validation is required before escalation." in report


def test_missing_host_user_context_uses_not_available() -> None:
    evidence = [
        _make_evidence(
            host=None,
            user=None,
            user_sid=None,
            process_id=None,
            parent_process_id=None,
            image_path=None,
            parent_image_path=None,
            source_ip=None,
            destination_ip=None,
            command_line=None,
        )
    ]
    report = build_template_report("missing-context", evidence, [], [], [], _make_scores(30), [])

    assert "## 8. Host and User Context" in report
    assert "- Hostname: Not available" in report
    assert "- User: Not available" in report
    assert "- Integrity Level: Not available" in report
