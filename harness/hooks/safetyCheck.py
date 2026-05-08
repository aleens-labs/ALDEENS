from __future__ import annotations

from typing import Any


def validate_report_payload(payload: dict[str, Any]) -> bool:
    return payload.get("guardrails", {}).get("safeForReport", False) is True

