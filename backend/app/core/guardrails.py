from __future__ import annotations

import re
from typing import Any

from app.core.config import Settings
from app.core.models import DetectionFinding, Evidence, GuardrailResult


ENCODED_FLAG_PATTERN = re.compile(r"(?i)(-enc(?:odedcommand)?\s+)([A-Za-z0-9+/=]{12,})")


def _sanitize_command(value: str | None) -> tuple[str | None, int]:
    if not value:
        return None, 0
    matches = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal matches
        matches += 1
        return f"{match.group(1)}[redacted-encoded-command]"

    sanitized = ENCODED_FLAG_PATTERN.sub(replace, value)
    return sanitized, matches


def _sanitize_evidence(item: Evidence) -> tuple[dict[str, Any], int]:
    command_line, matches = _sanitize_command(item.command_line)
    return (
        {
            "evidenceId": item.evidence_id,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None,
            "host": item.host,
            "user": item.user,
            "process": item.process,
            "parentProcess": item.parent_process,
            "commandLine": command_line,
            "targetProcess": item.target_process,
            "destinationIp": item.destination_ip,
            "destinationDomain": item.destination_domain,
            "filePath": item.file_path,
            "eventId": item.event_id,
            "provider": item.provider,
            "rawReference": item.raw_reference,
            "summary": item.summary,
        },
        matches,
    )


class GuardrailReviewer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def review(self, findings: list[DetectionFinding], requested_mode: str) -> GuardrailResult:
        redactions = 0
        structured_findings: list[dict[str, Any]] = []
        for finding in findings:
            safe_evidence = []
            for item in finding.evidence:
                sanitized, count = _sanitize_evidence(item)
                redactions += count
                safe_evidence.append(sanitized)
            structured_findings.append(
                {
                    "ruleId": finding.rule_id,
                    "title": finding.title,
                    "reason": finding.reason,
                    "mitreTechnique": finding.mitre_technique,
                    "tactic": finding.tactic,
                    "evidence": safe_evidence,
                }
            )

        mode_selected = "template"
        note = "Deterministic template mode selected for local-first defensive reporting."
        if requested_mode == "llm" and self.settings.allow_llm:
            mode_selected = "llm"
            note = "Structured findings passed guardrail review and can be rendered by a defensive-only LLM."
        elif requested_mode == "llm" and not self.settings.allow_llm:
            note = "Requested LLM mode, but no API key is configured; deterministic template fallback was enforced."

        return GuardrailResult(
            modeRequested=requested_mode,
            modeSelected=mode_selected,
            safeForReport=True,
            payloadRedactions=redactions,
            reviewNote=note,
            llmModel=self.settings.llm_model if mode_selected == "llm" else None,
            fallbackApplied=mode_selected != requested_mode,
            structuredFindings=structured_findings,
        )
