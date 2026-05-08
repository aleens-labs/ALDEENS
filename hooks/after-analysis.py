from __future__ import annotations


def summarize_outcome(risk_score: int, confidence_score: int) -> str:
    return f"Risk={risk_score} Confidence={confidence_score}"

