from __future__ import annotations

from datetime import datetime

from app.core.branding import APP_NAME, APP_REPORT_TITLE
from app.core.models import ChainStep, DetectionFinding, Evidence, ScoreCard, SimilarCase, TacticHit
from app.core.process_graph import (
    extract_command_lines,
    extract_host_context,
    build_process_tree,
    format_missing,
)
from app.core.verdict_engine import generate_final_verdict


def _fmt_ts(value: datetime | None) -> str:
    if value is None:
        return "Not available"
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def _cite(evidence_ids: list[str], raw_references: list[str]) -> str:
    evidence_text = ", ".join(evidence_ids) if evidence_ids else "Not available"
    raw_text = ", ".join(raw_references) if raw_references else "Not available"
    return f"[Evidence: {evidence_text} | Raw: {raw_text}]"


def _finding_citation(finding: DetectionFinding) -> str:
    raw_references = sorted({item.raw_reference for item in finding.evidence})
    return _cite(finding.evidence_ids, raw_references)


def _chain_citation(step: ChainStep) -> str:
    return _cite(step.evidence_ids, step.raw_references)


def _bullet_block(items: list[str], fallback: str) -> list[str]:
    if not items:
        return [f"- {fallback}"]
    return [f"- {item}" for item in items]


def build_template_report(
    dataset_name: str,
    evidence: list[Evidence],
    findings: list[DetectionFinding],
    tactics: list[TacticHit],
    chain: list[ChainStep],
    scores: ScoreCard,
    similar_cases: list[SimilarCase],
) -> str:
    risk_label = scores.risk_label.value if scores.risk_label else "Unknown"
    confidence = scores.confidence_score if scores.confidence_score is not None else 0
    verdict = generate_final_verdict(
        scores.risk_score,
        confidence,
        findings,
        tactics,
        similar_cases,
        evidence,
    )
    command_lines = extract_command_lines(evidence, findings, tactics)
    process_tree_lines, process_tree_partial = build_process_tree(evidence)
    host_context = extract_host_context(evidence)
    technique_lines = [
        f"- **{item.tactic}** -> `{item.technique_id}` {item.technique_name} "
        f"(confidence {round(item.confidence * 100)}%, rules: {', '.join(item.related_rules)})"
        for item in tactics
    ]

    lines = [
        f"# {APP_REPORT_TITLE}",
        "",
        "## 1. Executive Summary",
        (
            f"{APP_NAME} assessed `{dataset_name}` as **{risk_label}** risk with **{confidence}/100** confidence. "
            f"The incident includes {len(findings)} deterministic detections, {len(tactics)} MITRE ATT&CK techniques, "
            f"and {len(evidence)} normalized evidence artifacts."
        ),
        "",
        "## 2. Risk and Confidence",
        f"- Risk Score: **{scores.risk_score}/100** ({risk_label})",
        f"- Confidence Score: **{confidence}/100**",
        f"- Evidence Count: **{len(evidence)}**",
        f"- MITRE Technique Count: **{len(tactics)}**",
        "",
        "## 3. Final Verdict",
        verdict.verdict,
        "",
        "Reason:",
        verdict.reason,
        "",
        "Analyst Note:",
    ]
    lines.extend(_bullet_block(verdict.analyst_notes, "No additional analyst caution notes were generated."))

    lines.extend(["", "## 4. MITRE ATT&CK Mapping"])
    lines.extend(technique_lines or ["- No MITRE ATT&CK mappings were generated."])

    lines.extend(["", "## 5. Timeline"])
    if chain:
        for step in chain:
            lines.append(
                f"- **{step.stage}** at `{_fmt_ts(step.timestamp)}`: {step.summary} {_chain_citation(step)}"
            )
    else:
        lines.append("- No cohesive timeline could be reconstructed from the supplied telemetry.")

    lines.extend(["", "## 6. Process Tree", "```text"])
    lines.extend(process_tree_lines)
    lines.extend(["```"])
    if process_tree_partial:
        lines.append("Process tree is partial because parent-child telemetry is incomplete.")

    lines.extend(["", "## 7. Command Line Evidence"])
    if command_lines:
        for entry in command_lines:
            lines.extend(
                [
                    f"- Time: {_fmt_ts(entry['timestamp'])}",
                    f"- Process: {format_missing(entry['process'])}",
                    f"- Parent: {format_missing(entry['parent_process'])}",
                    f"- CommandLine: {format_missing(entry['command_line'])}",
                    f"- Rule: {', '.join(entry['rule_ids'])}",
                    f"- MITRE: {', '.join(entry['mitre'])}",
                    f"- Evidence: {entry['evidence_id']}",
                    f"- Raw Event: {entry['raw_event_id']}",
                    "",
                ]
            )
        if lines[-1] == "":
            lines.pop()
    else:
        lines.append("Command line telemetry was not available in the uploaded logs.")

    lines.extend(["", "## 8. Host and User Context"])
    if not host_context:
        host_context = [
            {
                "Evidence": "Not available",
                "Raw Event": "Not available",
                "Hostname": "Not available",
                "User": "Not available",
                "Domain": "Not available",
                "User SID": "Not available",
                "Process ID": "Not available",
                "Parent Process ID": "Not available",
                "Integrity Level": "Not available",
                "Hash": "Not available",
                "Image Path": "Not available",
                "Parent Image Path": "Not available",
                "Source IP": "Not available",
                "Destination IP": "Not available",
                "Logon ID": "Not available",
                "Session ID": "Not available",
            }
        ]

    for context in host_context:
        lines.extend([f"- Evidence: {context['Evidence']}", f"- Raw Event: {context['Raw Event']}"])
        for label in [
            "Hostname",
            "User",
            "Domain",
            "User SID",
            "Process ID",
            "Parent Process ID",
            "Integrity Level",
            "Hash",
            "Image Path",
            "Parent Image Path",
            "Source IP",
            "Destination IP",
            "Logon ID",
            "Session ID",
        ]:
            lines.append(f"- {label}: {context[label]}")
        lines.append("")
    if lines[-1] == "":
        lines.pop()

    lines.extend(["", "## 9. Detection Details"])
    if findings:
        for finding in findings:
            lines.extend(
                [
                    f"- Rule ID: `{finding.rule_id}`",
                    f"- Title: {finding.title}",
                    f"- MITRE: `{finding.mitre_technique}` ({finding.tactic})",
                    f"- Score Contribution: +{finding.score_contribution}",
                    f"- Confidence Contribution: +{finding.confidence_contribution:.2f}",
                    f"- Reason: {finding.reason}",
                    f"- Evidence IDs: {', '.join(finding.evidence_ids)}",
                    f"- Raw Event IDs: {', '.join(sorted({item.raw_reference for item in finding.evidence}))}",
                    "",
                ]
            )
        if lines[-1] == "":
            lines.pop()
    else:
        lines.append("- No detection rules fired on the supplied telemetry.")

    lines.extend(["", "## 10. Analyst Feedback History"])
    if similar_cases:
        for case in similar_cases[:8]:
            note = f" Note: {case.note}" if case.note else ""
            lines.append(
                f"- `{case.rule_id}` marked `{case.verdict.value}` {case.count} time(s) in `{case.dataset_name}`.{note}"
            )
    else:
        lines.append("- No prior local analyst feedback has been recorded for these rule IDs.")

    lines.extend(
        [
            "",
            "## 11. Recommended Investigation Steps",
            "- Validate the originating Office document, PowerShell transcript coverage, and AMSI visibility on the host.",
            "- Review authentication events and credential hygiene if LSASS access aligns with unauthorized tooling.",
            "- Confirm whether the outbound destination is expected for the host's business function.",
            "",
            "## 12. Telemetry Limitations",
            "- This report is evidence-backed but bounded by the uploaded logs.",
        ]
    )
    if not command_lines:
        lines.append("- Missing command-line telemetry reduces confidence in execution-chain reconstruction.")
    if process_tree_partial:
        lines.append("- Parent-child process telemetry is incomplete, so the execution chain may omit intermediate processes.")
    lines.append(
        "- Missing command-line, host, user, or process-tree telemetry reduces confidence and may hide lateral movement or follow-on persistence."
    )
    return "\n".join(lines)
