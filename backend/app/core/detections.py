from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from app.core.models import DetectionFinding, Evidence


def _safe_lower(value: str | None) -> str:
    return value.lower() if value else ""


def _contains_any(value: str | None, needles: Iterable[str]) -> bool:
    lowered = _safe_lower(value)
    return any(needle in lowered for needle in needles)


def _is_public_ip(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not any(
        [
            parsed.is_private,
            parsed.is_loopback,
            parsed.is_link_local,
            parsed.is_multicast,
            parsed.is_reserved,
            parsed.is_unspecified,
        ]
    )


class RuleBook:
    def __init__(self, rules_dir: Path) -> None:
        self.rules: dict[str, dict[str, Any]] = {}
        for rule_file in sorted(rules_dir.glob("*.yml")):
            payload = yaml.safe_load(rule_file.read_text(encoding="utf-8")) or {}
            for rule in payload.get("rules", []):
                self.rules[rule["id"]] = rule

    def get(self, rule_id: str) -> dict[str, Any]:
        return self.rules[rule_id]


class DetectionEngine:
    def __init__(self, rulebook: RuleBook) -> None:
        self.rulebook = rulebook

    def evaluate(self, evidence: list[Evidence]) -> list[DetectionFinding]:
        findings: list[DetectionFinding] = []
        office_processes = {"winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe"}

        office_chain = [
            item
            for item in evidence
            if item.process in {"powershell.exe", "pwsh.exe"}
            and item.parent_process in office_processes
        ]
        office_openers = [
            item
            for item in evidence
            if item.process in office_processes
            and _contains_any(item.command_line, [".doc", ".docm", ".xls", ".xlsm", ".ppt", ".pptm", ".ppsm"])
        ]
        if office_chain:
            rule_evidence = [*office_openers[:1], *office_chain[:1]]
            findings.append(
                self._build_finding(
                    "DL-WIN-001",
                    rule_evidence,
                    "Office spawned PowerShell, crossing a common user-document to script-execution boundary.",
                )
            )

        encoded_pwsh = [
            item
            for item in evidence
            if item.process in {"powershell.exe", "pwsh.exe"}
            and _contains_any(item.command_line, ["-enc", "-encodedcommand", "frombase64string"])
        ]
        if encoded_pwsh:
            findings.append(
                self._build_finding(
                    "DL-PS-001",
                    encoded_pwsh[:2],
                    "PowerShell command line contains encoded or obfuscated execution flags.",
                )
            )

        lsass_access = [
            item
            for item in evidence
            if item.target_process == "lsass.exe"
            or _contains_any(item.file_path, ["\\lsass", "lsass.exe"])
        ]
        if lsass_access:
            findings.append(
                self._build_finding(
                    "DL-CR-001",
                    lsass_access[:2],
                    "Telemetry shows access or direct targeting of LSASS, which is a strong credential-access signal.",
                )
            )

        outbound = [
            item
            for item in evidence
            if _is_public_ip(item.destination_ip)
            and item.process in {"powershell.exe", "pwsh.exe", "wscript.exe", "cscript.exe", "rundll32.exe"}
        ]
        if outbound:
            findings.append(
                self._build_finding(
                    "DL-NET-001",
                    outbound[:2],
                    "A scripting or living-off-the-land process initiated an outbound connection to a public IP.",
                )
            )

        persistence = [
            item
            for item in evidence
            if _contains_any(item.file_path, ["\\software\\microsoft\\windows\\currentversion\\run", "\\tasks\\"])
            or (
                item.process in {"schtasks.exe", "reg.exe"}
                and _contains_any(item.command_line, ["/create", " currentversion\\run"])
            )
        ]
        if persistence:
            rule_id = "DL-PER-002" if any(item.process == "schtasks.exe" for item in persistence) else "DL-PER-001"
            findings.append(
                self._build_finding(
                    rule_id,
                    persistence[:2],
                    "Persistence telemetry indicates a registry autorun change or scheduled task creation.",
                )
            )

        suspicious_chain = [
            item
            for item in evidence
            if item.parent_process in {"winword.exe", "excel.exe", "outlook.exe", "powershell.exe", "cmd.exe"}
            and item.process in {"cmd.exe", "powershell.exe", "pwsh.exe", "rundll32.exe", "regsvr32.exe", "mshta.exe"}
        ]
        if suspicious_chain:
            findings.append(
                self._build_finding(
                    "DL-WIN-002",
                    suspicious_chain[:3],
                    "The parent-child process lineage matches a suspicious execution chain frequently used in Windows intrusion playbooks.",
                )
            )

        return findings

    def _build_finding(self, rule_id: str, evidence: list[Evidence], reason: str) -> DetectionFinding:
        meta = self.rulebook.get(rule_id)
        finding_id = f"{rule_id}-{evidence[0].evidence_id}"
        return DetectionFinding(
            findingId=finding_id,
            ruleId=rule_id,
            title=meta["title"],
            reason=reason,
            evidenceIds=[item.evidence_id for item in evidence],
            evidence=evidence,
            mitreTechnique=meta["technique"],
            tactic=meta["tactic"],
            scoreContribution=int(meta["score"]),
            confidenceContribution=float(meta["confidence"]),
        )
