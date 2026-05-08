from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskLabel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FeedbackVerdict(str, Enum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    NEEDS_REVIEW = "needs_review"


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    index: int
    timestamp: datetime | None = None
    host: str | None = None
    user: str | None = None
    domain: str | None = None
    user_sid: str | None = Field(default=None, alias="userSid")
    process: str | None = None
    process_id: str | None = Field(default=None, alias="processId")
    parent_process: str | None = Field(default=None, alias="parentProcess")
    parent_process_id: str | None = Field(default=None, alias="parentProcessId")
    command_line: str | None = Field(default=None, alias="commandLine")
    target_process: str | None = Field(default=None, alias="targetProcess")
    source_ip: str | None = Field(default=None, alias="sourceIp")
    destination_ip: str | None = Field(default=None, alias="destinationIp")
    destination_domain: str | None = Field(default=None, alias="destinationDomain")
    integrity_level: str | None = Field(default=None, alias="integrityLevel")
    image_path: str | None = Field(default=None, alias="imagePath")
    parent_image_path: str | None = Field(default=None, alias="parentImagePath")
    file_path: str | None = Field(default=None, alias="filePath")
    hash: str | None = None
    logon_id: str | None = Field(default=None, alias="logonId")
    session_id: str | None = Field(default=None, alias="sessionId")
    event_id: str | None = Field(default=None, alias="eventId")
    provider: str | None = None
    raw_reference: str = Field(alias="rawReference")
    raw_event: dict[str, Any] = Field(default_factory=dict, alias="rawEvent")


class Evidence(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    evidence_id: str = Field(alias="evidenceId")
    timestamp: datetime | None = None
    host: str | None = None
    user: str | None = None
    domain: str | None = None
    user_sid: str | None = Field(default=None, alias="userSid")
    process: str | None = None
    process_id: str | None = Field(default=None, alias="processId")
    parent_process: str | None = Field(default=None, alias="parentProcess")
    parent_process_id: str | None = Field(default=None, alias="parentProcessId")
    command_line: str | None = Field(default=None, alias="commandLine")
    target_process: str | None = Field(default=None, alias="targetProcess")
    source_ip: str | None = Field(default=None, alias="sourceIp")
    destination_ip: str | None = Field(default=None, alias="destinationIp")
    destination_domain: str | None = Field(default=None, alias="destinationDomain")
    integrity_level: str | None = Field(default=None, alias="integrityLevel")
    image_path: str | None = Field(default=None, alias="imagePath")
    parent_image_path: str | None = Field(default=None, alias="parentImagePath")
    file_path: str | None = Field(default=None, alias="filePath")
    hash: str | None = None
    logon_id: str | None = Field(default=None, alias="logonId")
    session_id: str | None = Field(default=None, alias="sessionId")
    event_id: str | None = Field(default=None, alias="eventId")
    provider: str | None = None
    raw_reference: str = Field(alias="rawReference")
    summary: str


class DetectionFinding(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    finding_id: str = Field(alias="findingId")
    rule_id: str = Field(alias="ruleId")
    title: str
    reason: str
    evidence_ids: list[str] = Field(alias="evidenceIds")
    evidence: list[Evidence]
    mitre_technique: str = Field(alias="mitreTechnique")
    tactic: str
    score_contribution: int = Field(alias="scoreContribution")
    confidence_contribution: float = Field(alias="confidenceContribution")


class TacticHit(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    technique_id: str = Field(alias="techniqueId")
    technique_name: str = Field(alias="techniqueName")
    tactic: str
    description: str
    confidence: float
    related_rules: list[str] = Field(alias="relatedRules")


class ChainStep(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stage: str
    timestamp: datetime | None = None
    summary: str
    evidence_ids: list[str] = Field(alias="evidenceIds")
    finding_ids: list[str] = Field(alias="findingIds")
    raw_references: list[str] = Field(default_factory=list, alias="rawReferences")


class ScoreComponent(BaseModel):
    label: str
    value: int
    reason: str


class ScoreCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    risk_score: int = Field(alias="riskScore")
    risk_label: RiskLabel = Field(alias="riskLabel")
    confidence_score: int = Field(alias="confidenceScore")
    completeness: float
    score_trace: list[ScoreComponent] = Field(alias="scoreTrace")
    confidence_trace: list[ScoreComponent] = Field(alias="confidenceTrace")


class SimilarCase(BaseModel):
    rule_id: str = Field(alias="ruleId")
    verdict: FeedbackVerdict
    note: str | None = None
    count: int = 1
    dataset_name: str = Field(alias="datasetName")
    seen_at: str = Field(alias="seenAt")


class GuardrailResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode_requested: str = Field(alias="modeRequested")
    mode_selected: str = Field(alias="modeSelected")
    safe_for_report: bool = Field(alias="safeForReport")
    payload_redactions: int = Field(alias="payloadRedactions")
    review_note: str = Field(alias="reviewNote")
    llm_model: str | None = Field(default=None, alias="llmModel")
    fallback_applied: bool = Field(default=False, alias="fallbackApplied")
    structured_findings: list[dict[str, Any]] = Field(alias="structuredFindings")


class AuditRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str = Field(alias="analysisId")
    timestamp: str
    dataset_name: str = Field(alias="datasetName")
    parser_mode: str = Field(alias="parserMode")
    rules_triggered: list[str] = Field(alias="rulesTriggered")
    risk_score: int = Field(alias="riskScore")
    confidence_score: int = Field(alias="confidenceScore")
    report_mode: str = Field(alias="reportMode")
    safety_check: str = Field(alias="safetyCheck")
    llm_model: str | None = Field(default=None, alias="llmModel")
    provider_request_id: str | None = Field(default=None, alias="providerRequestId")


class FeedbackRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str = Field(alias="analysisId")
    dataset_name: str = Field(alias="datasetName")
    verdict: FeedbackVerdict
    note: str | None = None
    rule_ids: list[str] = Field(alias="ruleIds")


class ConfidenceOverride(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str = Field(alias="analysisId")
    dataset_name: str | None = Field(default=None, alias="datasetName")
    analyst_confidence: int = Field(alias="analystConfidence", ge=0, le=100)
    override_note: str | None = Field(default="", alias="overrideNote")


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str | None = Field(default=None, alias="analysisId")
    dataset_name: str | None = Field(default=None, alias="datasetName")
    events: list[dict[str, Any]] | None = None
    report_mode: str | None = Field(default=None, alias="reportMode")


class DatasetSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dataset_id: str = Field(alias="datasetId")
    title: str
    description: str
    sample_path: str = Field(alias="samplePath")
    attack_description: str = Field(alias="attackDescription")
    techniques: list[str]
    source_name: str = Field(alias="sourceName")
    source_url: str = Field(alias="sourceUrl")
    collection_type: str = Field(alias="collectionType")
    benchmark_tier: str | None = Field(default=None, alias="benchmarkTier")


class AnalysisResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str = Field(alias="analysisId")
    dataset_name: str = Field(alias="datasetName")
    parser_mode: str = Field(alias="parserMode")
    report_mode: str = Field(alias="reportMode")
    evidence_count: int = Field(alias="evidenceCount")
    mitre_count: int = Field(alias="mitreCount")
    evidence: list[Evidence]
    findings: list[DetectionFinding]
    tactics: list[TacticHit]
    attack_chain: list[ChainStep] = Field(alias="attackChain")
    scores: ScoreCard
    analyst_brief: str = Field(alias="analystBrief")
    guardrails: GuardrailResult
    audit: AuditRecord
    similar_cases: list[SimilarCase] = Field(alias="similarCases")
