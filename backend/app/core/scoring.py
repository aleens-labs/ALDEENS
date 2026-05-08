from __future__ import annotations

from statistics import mean

from app.core.models import DetectionFinding, Evidence, RiskLabel, ScoreCard, ScoreComponent, TacticHit


class ScoreEngine:
    def evaluate(
        self,
        evidence: list[Evidence],
        findings: list[DetectionFinding],
        tactics: list[TacticHit],
    ) -> ScoreCard:
        score_trace: list[ScoreComponent] = []
        confidence_trace: list[ScoreComponent] = []

        raw_risk = 0
        for finding in findings:
            raw_risk += finding.score_contribution
            score_trace.append(
                ScoreComponent(
                    label=finding.rule_id,
                    value=finding.score_contribution,
                    reason=finding.title,
                )
            )

        unique_tactics = sorted({item.tactic for item in tactics})
        if len(unique_tactics) >= 3:
            raw_risk += 10
            score_trace.append(
                ScoreComponent(
                    label="TACTIC-DIVERSITY",
                    value=10,
                    reason="Multiple ATT&CK tactics were observed in a single incident chain.",
                )
            )

        completeness = self._completeness(evidence)
        penalty = 0
        if completeness < 0.55:
            penalty = 15
        elif completeness < 0.7:
            penalty = 10
        elif completeness < 0.85:
            penalty = 5

        if penalty:
            raw_risk -= penalty
            score_trace.append(
                ScoreComponent(
                    label="EVIDENCE-GAP",
                    value=-penalty,
                    reason="Some expected Windows context fields were missing from the available evidence.",
                )
            )

        risk_score = max(0, min(100, raw_risk))
        risk_label = self._label(risk_score)

        base_confidence = 25
        completeness_component = round(completeness * 35)
        trace_quality = min(30, round(sum(item.confidence_contribution for item in findings) * 45))
        tactic_component = min(10, len(unique_tactics) * 2)
        confidence_score = max(0, min(100, base_confidence + completeness_component + trace_quality + tactic_component))

        confidence_trace.extend(
            [
                ScoreComponent(
                    label="BASELINE",
                    value=base_confidence,
                    reason="Deterministic pipeline baseline for validated evidence extraction.",
                ),
                ScoreComponent(
                    label="EVIDENCE-COMPLETENESS",
                    value=completeness_component,
                    reason=f"Evidence completeness ratio: {completeness:.2f}",
                ),
                ScoreComponent(
                    label="RULE-TRACE",
                    value=trace_quality,
                    reason="Confidence increases when rules carry direct evidence and MITRE linkage.",
                ),
                ScoreComponent(
                    label="TACTIC-COVERAGE",
                    value=tactic_component,
                    reason=f"{len(unique_tactics)} ATT&CK tactics were reconstructed from the rule trace.",
                ),
            ]
        )

        return ScoreCard(
            riskScore=risk_score,
            riskLabel=risk_label,
            confidenceScore=confidence_score,
            completeness=round(completeness, 2),
            scoreTrace=score_trace,
            confidenceTrace=confidence_trace,
        )

    def _completeness(self, evidence: list[Evidence]) -> float:
        if not evidence:
            return 0.0
        field_scores = []
        for item in evidence:
            present = [
                bool(item.timestamp),
                bool(item.host),
                bool(item.user),
                bool(item.process),
                bool(item.parent_process),
                bool(item.command_line),
                bool(item.event_id),
                bool(item.provider),
                bool(item.raw_reference),
            ]
            field_scores.append(sum(1 for flag in present if flag) / len(present))
        return mean(field_scores)

    def _label(self, risk_score: int) -> RiskLabel:
        if risk_score >= 80:
            return RiskLabel.CRITICAL
        if risk_score >= 60:
            return RiskLabel.HIGH
        if risk_score >= 30:
            return RiskLabel.MEDIUM
        return RiskLabel.LOW

