from __future__ import annotations

from app.core.analyst import AnalystNarrative, AnalystWriteResult, OpenAIAnalystNarrative
from app.core.branding import APP_NAME
from app.core.config import Settings
from app.core.models import ChainStep, DetectionFinding, Evidence, GuardrailResult, ScoreCard, SimilarCase, TacticHit


class AnalystAgent:
    """Writes a defensive analyst brief from structured findings only."""

    def __init__(self, settings: Settings) -> None:
        self.narrative = AnalystNarrative()
        self.llm_narrative = OpenAIAnalystNarrative(settings, self.narrative)

    def write(
        self,
        analysis_id: str,
        dataset_name: str,
        evidence: list[Evidence],
        findings: list[DetectionFinding],
        tactics: list[TacticHit],
        chain: list[ChainStep],
        scores: ScoreCard,
        similar_cases: list[SimilarCase],
        guardrails: GuardrailResult,
    ) -> AnalystWriteResult:
        if guardrails.mode_selected == "llm":
            try:
                brief, provider_request_id = self.llm_narrative.render(
                    analysis_id,
                    dataset_name,
                    findings,
                    tactics,
                    chain,
                    scores,
                    similar_cases,
                    guardrails,
                )
                return AnalystWriteResult(
                    brief=brief,
                    mode_selected="llm",
                    review_note=guardrails.review_note,
                    provider_request_id=provider_request_id,
                )
            except Exception as exc:
                fallback_brief = self.narrative.render(
                    dataset_name,
                    evidence,
                    findings,
                    tactics,
                    chain,
                    scores,
                    similar_cases,
                )
                return AnalystWriteResult(
                    brief=fallback_brief,
                    mode_selected="template",
                    review_note=(
                        f"{guardrails.review_note} "
                        f"LLM rendering failed, so {APP_NAME} enforced deterministic template fallback. Reason: {exc}"
                    ),
                    provider_request_id=None,
                )

        return AnalystWriteResult(
            brief=self.narrative.render(dataset_name, evidence, findings, tactics, chain, scores, similar_cases),
            mode_selected="template",
            review_note=guardrails.review_note,
            provider_request_id=None,
        )
