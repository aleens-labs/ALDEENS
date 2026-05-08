from __future__ import annotations

from app.core.models import DetectionFinding, TacticHit


TECHNIQUE_CATALOG = {
    "T1059.001": {
        "name": "PowerShell",
        "tactic": "Execution",
        "description": "PowerShell execution or staging from a Windows process lineage.",
    },
    "T1003.001": {
        "name": "LSASS Memory",
        "tactic": "Credential Access",
        "description": "Attempted credential material access through LSASS telemetry.",
    },
    "T1027": {
        "name": "Obfuscated Files or Information",
        "tactic": "Defense Evasion",
        "description": "Encoded or obfuscated content intended to hide execution intent.",
    },
    "T1071": {
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
        "description": "Suspicious outbound application-layer communications to an external host.",
    },
    "T1547": {
        "name": "Boot or Logon Autostart Execution",
        "tactic": "Persistence",
        "description": "Autorun or boot-time execution persistence via registry or startup entries.",
    },
    "T1053": {
        "name": "Scheduled Task/Job",
        "tactic": "Persistence",
        "description": "Task scheduler abuse to re-establish or maintain execution.",
    },
}


class TacticMapper:
    def map_findings(self, findings: list[DetectionFinding]) -> list[TacticHit]:
        by_technique: dict[str, list[DetectionFinding]] = {}
        for finding in findings:
            by_technique.setdefault(finding.mitre_technique, []).append(finding)

        mapped: list[TacticHit] = []
        for technique_id, related_findings in by_technique.items():
            meta = TECHNIQUE_CATALOG.get(
                technique_id,
                {
                    "name": technique_id,
                    "tactic": related_findings[0].tactic,
                    "description": "No catalog description available.",
                },
            )
            confidence = min(0.99, sum(item.confidence_contribution for item in related_findings))
            mapped.append(
                TacticHit(
                    techniqueId=technique_id,
                    techniqueName=meta["name"],
                    tactic=meta["tactic"],
                    description=meta["description"],
                    confidence=round(confidence, 2),
                    relatedRules=[item.rule_id for item in related_findings],
                )
            )

        return sorted(mapped, key=lambda item: (item.tactic, item.technique_id))

