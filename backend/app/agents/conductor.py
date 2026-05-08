from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.analystAgent import AnalystAgent
from app.agents.chainAgent import ChainAgent
from app.agents.detectionAgent import DetectionAgent
from app.agents.evidenceAgent import EvidenceAgent
from app.agents.safetyAgent import SafetyAgent
from app.agents.tacticAgent import TacticAgent
from app.core.audit import AuditTrail
from app.core.config import Settings
from app.core.memory import FeedbackMemory
from app.core.models import AnalysisResult, AuditRecord
from app.core.scoring import ScoreEngine
from app.core.telemetry import TelemetryNormalizer


class Conductor:
    """Orchestrates a constrained analysis workflow for defensive telemetry only."""

    def __init__(
        self,
        settings: Settings,
        normalizer: TelemetryNormalizer,
        evidence_agent: EvidenceAgent,
        detection_agent: DetectionAgent,
        tactic_agent: TacticAgent,
        chain_agent: ChainAgent,
        analyst_agent: AnalystAgent,
        safety_agent: SafetyAgent,
        scoring: ScoreEngine,
        audit_trail: AuditTrail,
        memory: FeedbackMemory,
    ) -> None:
        self.settings = settings
        self.normalizer = normalizer
        self.evidence_agent = evidence_agent
        self.detection_agent = detection_agent
        self.tactic_agent = tactic_agent
        self.chain_agent = chain_agent
        self.analyst_agent = analyst_agent
        self.safety_agent = safety_agent
        self.scoring = scoring
        self.audit_trail = audit_trail
        self.memory = memory

    def analyze(
        self,
        dataset_name: str,
        raw_events: list[dict[str, Any]],
        parser_mode: str,
        requested_report_mode: str,
    ) -> AnalysisResult:
        analysis_id = uuid.uuid4().hex[:12]
        normalized = self.normalizer.normalize(raw_events)
        evidence = self.evidence_agent.collect(normalized)
        findings = self.detection_agent.inspect(evidence)
        tactics = self.tactic_agent.map(findings)
        attack_chain = self.chain_agent.rebuild(findings)
        scores = self.scoring.evaluate(evidence, findings, tactics)
        similar_cases = self.memory.similar_cases([item.rule_id for item in findings], dataset_name)
        guardrails = self.safety_agent.review(findings, requested_report_mode)
        report = self.analyst_agent.write(
            analysis_id,
            dataset_name,
            evidence,
            findings,
            tactics,
            attack_chain,
            scores,
            similar_cases,
            guardrails,
        )
        guardrails = guardrails.model_copy(
            update={
                "mode_selected": report.mode_selected,
                "review_note": report.review_note,
                "fallback_applied": report.mode_selected != guardrails.mode_selected,
            }
        )

        audit = AuditRecord(
            analysisId=analysis_id,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            datasetName=dataset_name,
            parserMode=parser_mode,
            rulesTriggered=[item.rule_id for item in findings],
            riskScore=scores.risk_score,
            confidenceScore=scores.confidence_score,
            reportMode=report.mode_selected,
            safetyCheck="pass" if guardrails.safe_for_report else "blocked",
            llmModel=guardrails.llm_model,
            providerRequestId=report.provider_request_id,
        )
        self.audit_trail.record(audit)

        result = AnalysisResult(
            analysisId=analysis_id,
            datasetName=dataset_name,
            parserMode=parser_mode,
            reportMode=report.mode_selected,
            evidenceCount=len(evidence),
            mitreCount=len(tactics),
            evidence=evidence,
            findings=findings,
            tactics=tactics,
            attackChain=attack_chain,
            scores=scores,
            analystBrief=report.brief,
            guardrails=guardrails,
            audit=audit,
            similarCases=similar_cases,
        )

        self._persist(result)
        return result

    def _persist(self, result: AnalysisResult) -> None:
        output_path = self.settings.analyses_dir / f"{result.analysis_id}.json"
        output_path.write_text(
            json.dumps(result.model_dump(mode="json", by_alias=True), indent=2),
            encoding="utf-8",
        )

    def load_analysis(self, analysis_id: str) -> AnalysisResult:
        path = self.settings.analyses_dir / f"{analysis_id}.json"
        return AnalysisResult.model_validate_json(path.read_text(encoding="utf-8"))
