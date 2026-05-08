from __future__ import annotations

from typing import Any


def filter_for_defensive_reporting(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for finding in findings:
        for evidence in finding.get("evidence", []):
            command = evidence.get("commandLine")
            if isinstance(command, str) and "-EncodedCommand" in command:
                evidence["commandLine"] = command.split("-EncodedCommand")[0] + "-EncodedCommand [redacted]"
    return findings

