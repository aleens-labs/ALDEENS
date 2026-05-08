from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.branding import APP_NAME
from app.core.config import Settings
from app.core.lens_report_builder import build_template_report
from app.core.models import (
    AnalysisResult,
    ChainStep,
    DetectionFinding,
    Evidence,
    GuardrailResult,
    ScoreCard,
    SimilarCase,
    TacticHit,
)


@dataclass
class AnalystWriteResult:
    brief: str
    mode_selected: str
    review_note: str
    provider_request_id: str | None = None


class CitationStatement(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    claim: str = Field(min_length=1)
    evidence_ids: list[str] = Field(alias="evidenceIds", min_length=1)
    raw_references: list[str] = Field(alias="rawReferences", min_length=1)


class StructuredLLMBrief(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    headline: str = Field(min_length=1)
    executive_summary: str = Field(alias="executiveSummary", min_length=1)
    observed: list[CitationStatement]
    inferred: list[CitationStatement]
    needs_review: list[CitationStatement] = Field(alias="needsReview")
    recommended_actions: list[str] = Field(alias="recommendedActions")
    limitations: list[str]


class AnalystNarrative:
    def _format_citation(self, evidence_ids: list[str], raw_references: list[str]) -> str:
        evidence_text = ", ".join(evidence_ids)
        raw_text = ", ".join(raw_references)
        return f"[Evidence: {evidence_text} | Raw: {raw_text}]"

    def _finding_citation(self, finding: DetectionFinding) -> str:
        raw_references = sorted({item.raw_reference for item in finding.evidence})
        return self._format_citation(finding.evidence_ids, raw_references)

    def _chain_citation(self, step: ChainStep) -> str:
        return self._format_citation(step.evidence_ids, step.raw_references)

    def _statement_line(self, statement: CitationStatement) -> str:
        return f"- {statement.claim} {self._format_citation(statement.evidence_ids, statement.raw_references)}"

    @staticmethod
    def _fmt_ts(dt: "datetime | None") -> str:
        if dt is None:
            return "time-unavailable"
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    def render(
        self,
        dataset_name: str,
        evidence: list[Evidence],
        findings: list[DetectionFinding],
        tactics: list[TacticHit],
        chain: list[ChainStep],
        scores: ScoreCard,
        similar_cases: list[SimilarCase],
    ) -> str:
        return build_template_report(dataset_name, evidence, findings, tactics, chain, scores, similar_cases)

    def render_llm_markdown(
        self,
        dataset_name: str,
        evidence: list[Evidence],
        findings: list[DetectionFinding],
        tactics: list[TacticHit],
        chain: list[ChainStep],
        scores: ScoreCard,
        similar_cases: list[SimilarCase],
        report: StructuredLLMBrief,
    ) -> str:
        base_report = build_template_report(dataset_name, evidence, findings, tactics, chain, scores, similar_cases)
        lines = [base_report, "", "## LLM Assessment Addendum", report.executive_summary, "", "### Observed Findings"]
        lines.extend(self._statement_line(statement) for statement in report.observed)
        lines.extend(["", "### Inferred Assessment"])
        lines.extend(self._statement_line(statement) for statement in report.inferred)
        lines.extend(["", "### Needs Review"])
        if report.needs_review:
            lines.extend(self._statement_line(statement) for statement in report.needs_review)
        else:
            lines.append("- No additional review-only claims were necessary for this report.")

        lines.extend(["", "### Recommended LLM Actions"])
        lines.extend(f"- {item}" for item in report.recommended_actions[:5])
        lines.extend(
            [
                "",
                "### LLM Limitations",
                *[f"- {item}" for item in report.limitations[:4]],
                "",
                f"_Rendered from structured findings for `{dataset_name}` with {scores.confidence_score}/100 confidence._",
            ]
        )
        return "\n".join(lines)

    def export_markdown(self, result: AnalysisResult) -> str:
        return result.analyst_brief

    def export_json(self, result: AnalysisResult) -> str:
        return json.dumps(result.model_dump(mode="json", by_alias=True), indent=2)

    def export_pdf(self, result: AnalysisResult, target_path: Path) -> Path:
        from pdf_export import generate_pdf

        target_path.write_bytes(generate_pdf(result))
        return target_path


class OpenAIAnalystNarrative:
    """
    Compatible with OpenRouter and any OpenAI-compatible provider.
    Uses chat.completions (not the Responses API) so it works with
    every OpenRouter model including Anthropic, Mistral, Llama, etc.
    """

    def __init__(self, settings: Settings, template_writer: AnalystNarrative) -> None:
        self.settings = settings
        self.template_writer = template_writer

    def render(
        self,
        analysis_id: str,
        dataset_name: str,
        findings: list[DetectionFinding],
        tactics: list[TacticHit],
        chain: list[ChainStep],
        scores: ScoreCard,
        similar_cases: list[SimilarCase],
        guardrails: GuardrailResult,
    ) -> tuple[str, str | None]:
        if not self.settings.allow_llm:
            raise RuntimeError("LLM mode requested but no API key is configured.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The openai SDK is not installed.") from exc

        client = OpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            timeout=float(self.settings.llm_timeout_seconds),
        )

        system_msg = self._system_prompt()
        user_msg = self._report_payload(dataset_name, findings, tactics, chain, scores, similar_cases, guardrails)

        response = client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            extra_headers={"X-Title": APP_NAME},
        )

        raw_text = (response.choices[0].message.content or "").strip()
        if not raw_text:
            raise RuntimeError("LLM returned an empty response.")

        structured = StructuredLLMBrief.model_validate_json(raw_text)
        self._validate_citations(findings, structured)
        unique_evidence = list(
            {
                evidence.evidence_id: evidence
                for finding in findings
                for evidence in finding.evidence
            }.values()
        )
        brief = self.template_writer.render_llm_markdown(
            dataset_name,
            unique_evidence,
            findings,
            tactics,
            chain,
            scores,
            similar_cases,
            structured,
        )
        request_id: str | None = getattr(response, "id", None)
        return brief, request_id

    def _system_prompt(self) -> str:
        schema = json.dumps(StructuredLLMBrief.model_json_schema(), indent=2)
        return (
            f"You are {APP_NAME} AnalystAgent — a defensive-only Windows incident triage assistant.\n\n"
            "RULES:\n"
            "- Use ONLY the structured findings supplied in the user message. Never invent evidence.\n"
            "- Do NOT generate payloads, exploitation advice, or evasion techniques.\n"
            "- Separate OBSERVED facts (directly evidenced) from INFERRED assessment (reasoned) and NEEDS_REVIEW uncertainty.\n"
            "- Every claim in observed/inferred/needsReview MUST cite at least one evidenceId and its matching rawReference from the allowedEvidence map.\n"
            "- Claims that cannot be grounded in evidence go into needsReview or limitations.\n\n"
            "OUTPUT FORMAT: Respond with a single JSON object matching this schema exactly:\n"
            f"{schema}\n\n"
            "Return ONLY the JSON object — no markdown fences, no explanation."
        )

    def _report_payload(
        self,
        dataset_name: str,
        findings: list[DetectionFinding],
        tactics: list[TacticHit],
        chain: list[ChainStep],
        scores: ScoreCard,
        similar_cases: list[SimilarCase],
        guardrails: GuardrailResult,
    ) -> str:
        payload: dict[str, Any] = {
            "datasetName": dataset_name,
            "scores": scores.model_dump(mode="json", by_alias=True),
            "findings": guardrails.structured_findings,
            "tactics": [item.model_dump(mode="json", by_alias=True) for item in tactics],
            "attackChain": [item.model_dump(mode="json", by_alias=True) for item in chain],
            "similarCases": [item.model_dump(mode="json", by_alias=True) for item in similar_cases],
            "allowedEvidence": {
                evidence.evidence_id: {"rawReference": evidence.raw_reference, "summary": evidence.summary}
                for finding in findings
                for evidence in finding.evidence
            },
            "guardrailReview": guardrails.review_note,
        }
        return json.dumps(payload, indent=2)

    def _validate_citations(self, findings: list[DetectionFinding], report: StructuredLLMBrief) -> None:
        evidence_map = {
            evidence.evidence_id: evidence.raw_reference
            for finding in findings
            for evidence in finding.evidence
        }
        for statement in [*report.observed, *report.inferred, *report.needs_review]:
            unknown_evidence = [item for item in statement.evidence_ids if item not in evidence_map]
            if unknown_evidence:
                raise RuntimeError(f"LLM cited unknown evidence IDs: {', '.join(unknown_evidence)}")
            expected_raw = {evidence_map[item] for item in statement.evidence_ids}
            if not set(statement.raw_references).issubset(expected_raw):
                raise RuntimeError("LLM raw references do not match the cited evidence IDs.")
