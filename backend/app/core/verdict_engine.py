from __future__ import annotations

from dataclasses import dataclass

from app.core.branding import APP_NAME
from app.core.models import DetectionFinding, Evidence, FeedbackVerdict, SimilarCase, TacticHit


@dataclass
class VerdictSummary:
    verdict: str
    reason: str
    analyst_notes: list[str]


def _telemetry_is_incomplete(evidence: list[Evidence]) -> bool:
    if not evidence:
        return True
    has_command_line = any(item.command_line for item in evidence)
    has_process_link = any(item.parent_process or item.parent_process_id for item in evidence)
    has_host_user = any(item.host or item.user for item in evidence)
    return not (has_command_line and has_process_link and has_host_user)


def _format_technique(tactic: TacticHit) -> str:
    return f"{tactic.technique_id} {tactic.technique_name}".strip()


def generate_final_verdict(
    risk: int,
    confidence: int,
    detections: list[DetectionFinding],
    tactics: list[TacticHit],
    feedback: list[SimilarCase],
    evidence: list[Evidence],
) -> VerdictSummary:
    del risk
    has_lsass = any(item.rule_id == "DL-CR-001" or item.mitre_technique == "T1003.001" for item in detections)
    has_false_positive_history = any(item.verdict == FeedbackVerdict.FALSE_POSITIVE for item in feedback)
    telemetry_incomplete = _telemetry_is_incomplete(evidence)

    if has_lsass and confidence >= 70:
        verdict = "Likely malicious credential dumping attempt."
    elif has_lsass and 50 <= confidence <= 69:
        verdict = "Suspicious credential access activity requiring validation."
    else:
        verdict = "Suspicious execution activity requiring review."

    technique_map = {item.technique_id: item for item in tactics}
    mentioned: list[str] = []
    if "T1003.001" in technique_map:
        mentioned.append(f"LSASS memory access mapped to MITRE ATT&CK {_format_technique(technique_map['T1003.001'])}")
    if "T1059.001" in technique_map:
        mentioned.append(f"suspicious PowerShell execution mapped to {_format_technique(technique_map['T1059.001'])}")
    if not mentioned and detections:
        mentioned.append(
            "deterministic detections "
            + ", ".join(f"{item.rule_id} ({item.mitre_technique})" for item in detections[:3])
        )

    if has_lsass and confidence >= 70:
        reason_suffix = "The confidence score is high enough to treat the activity as likely malicious pending containment validation."
    elif has_lsass and 50 <= confidence <= 69:
        reason_suffix = (
            f"The confidence score is {confidence}/100, so the incident should be treated as suspicious but not "
            "automatically confirmed as malicious."
        )
    else:
        reason_suffix = (
            f"Detections currently point to suspicious execution behavior with a confidence score of {confidence}/100, "
            "so analyst review is required before escalation."
        )

    reason = (
        f"{APP_NAME} detected "
        + (" and ".join(mentioned) if mentioned else "suspicious execution behavior")
        + f". {reason_suffix}"
    )

    analyst_notes: list[str] = []
    if has_false_positive_history:
        analyst_notes.append(
            "Prior analyst feedback includes false-positive markings, so validation is required before escalation."
        )
    if telemetry_incomplete:
        analyst_notes.append(
            "Telemetry gaps reduce confidence and may hide lateral movement, persistence, or follow-on activity."
        )

    return VerdictSummary(verdict=verdict, reason=reason, analyst_notes=analyst_notes)
