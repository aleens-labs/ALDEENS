from __future__ import annotations

from datetime import datetime

from app.core.models import ChainStep, DetectionFinding


CHAIN_ORDER = [
    "Initial Access",
    "Execution",
    "Defense Evasion",
    "Credential Access",
    "Command and Control",
    "Persistence",
]


class AttackChainBuilder:
    def reconstruct(self, findings: list[DetectionFinding]) -> list[ChainStep]:
        staged: dict[str, ChainStep] = {}

        def raw_refs(finding: DetectionFinding) -> list[str]:
            return sorted({item.raw_reference for item in finding.evidence})

        def stage_timestamp(stage: str, finding: DetectionFinding) -> datetime | None:
            if not finding.evidence:
                return None

            if finding.rule_id == "DL-WIN-001":
                if stage == "Initial Access":
                    for item in finding.evidence:
                        if item.process in {"winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe"}:
                            return item.timestamp
                if stage == "Execution":
                    for item in finding.evidence:
                        if item.process in {"powershell.exe", "pwsh.exe"}:
                            return item.timestamp

            return finding.evidence[0].timestamp

        def supports_initial_access(finding: DetectionFinding) -> bool:
            macro_extensions = (".docm", ".xlsm", ".pptm", ".ppsm")
            for item in finding.evidence:
                command_line = (item.command_line or "").lower()
                if any(extension in command_line for extension in macro_extensions):
                    return True
                if "\\downloads\\" in command_line or "\\temp\\" in command_line:
                    return True
            return False

        def upsert(stage: str, finding: DetectionFinding, summary: str) -> None:
            if stage in staged:
                current = staged[stage]
                current.evidence_ids = sorted(set([*current.evidence_ids, *finding.evidence_ids]))
                current.finding_ids = sorted(set([*current.finding_ids, finding.finding_id]))
                current.raw_references = sorted(set([*current.raw_references, *raw_refs(finding)]))
                selected_timestamp = stage_timestamp(stage, finding)
                if selected_timestamp and (current.timestamp is None or selected_timestamp < current.timestamp):
                    current.timestamp = selected_timestamp
                return

            staged[stage] = ChainStep(
                stage=stage,
                timestamp=stage_timestamp(stage, finding),
                summary=summary,
                evidenceIds=finding.evidence_ids,
                findingIds=[finding.finding_id],
                rawReferences=raw_refs(finding),
            )

        for finding in findings:
            if finding.rule_id == "DL-WIN-001":
                if supports_initial_access(finding):
                    upsert(
                        "Initial Access",
                        finding,
                        "Office telemetry suggests a likely document-driven entry point, but delivery context should still be confirmed with adjacent host evidence.",
                    )
                upsert(
                    "Execution",
                    finding,
                    "PowerShell execution was initiated directly from an Office lineage.",
                )
            elif finding.rule_id == "DL-PS-001":
                upsert(
                    "Defense Evasion",
                    finding,
                    "Encoded PowerShell execution indicates an attempt to conceal intent or payload content.",
                )
            elif finding.rule_id == "DL-CR-001":
                upsert(
                    "Credential Access",
                    finding,
                    "Telemetry indicates contact with LSASS, suggesting credential collection intent.",
                )
            elif finding.rule_id == "DL-NET-001":
                upsert(
                    "Command and Control",
                    finding,
                    "The process chain reached an outbound network connection to an external address.",
                )
            elif finding.rule_id in {"DL-PER-001", "DL-PER-002"}:
                upsert(
                    "Persistence",
                    finding,
                    "Observed changes suggest the activity attempted to survive process or logon boundaries.",
                )
            elif finding.rule_id == "DL-WIN-002" and "Execution" not in staged:
                upsert(
                    "Execution",
                    finding,
                    "Suspicious parent-child process lineage reinforces the execution portion of the chain.",
                )

        return [staged[stage] for stage in CHAIN_ORDER if stage in staged]
