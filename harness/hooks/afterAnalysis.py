from __future__ import annotations

from typing import Any


def summarize_analysis(result: dict[str, Any]) -> dict[str, Any]:
    return {
      "analysisId": result.get("analysisId"),
      "riskScore": result.get("scores", {}).get("riskScore"),
      "confidenceScore": result.get("scores", {}).get("confidenceScore"),
      "rulesTriggered": [item.get("ruleId") for item in result.get("findings", [])],
    }

