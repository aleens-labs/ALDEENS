from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pdf_export import generate_pdf

from app.agents.analystAgent import AnalystAgent
from app.agents.chainAgent import ChainAgent
from app.agents.conductor import Conductor
from app.agents.detectionAgent import DetectionAgent
from app.agents.evidenceAgent import EvidenceAgent
from app.agents.safetyAgent import SafetyAgent
from app.agents.tacticAgent import TacticAgent
from app.core.analyst import AnalystNarrative
from app.core.audit import AuditTrail
from app.core.branding import APP_EXPORT_PREFIX
from app.core.config import get_settings, validate_production_safe
from app.core.detections import DetectionEngine, RuleBook
from app.core.guardrails import GuardrailReviewer
from app.core.memory import FeedbackMemory
from app.core.models import AnalysisRequest, AnalysisResult, ConfidenceOverride, DatasetSummary, FeedbackRecord
from app.core.scoring import ScoreEngine
from app.core.security import (
    InMemoryRateLimiter,
    RatePolicy,
    client_identity,
    resolve_api_key,
    validate_upload_metadata,
    validate_uploaded_events,
)
from app.core.telemetry import TelemetryNormalizer

settings = get_settings()
validate_production_safe(settings)
rate_limiter = InMemoryRateLimiter()
analyze_rate_policy = RatePolicy.parse(settings.analyze_rate_limit)
upload_rate_policy = RatePolicy.parse(settings.upload_rate_limit)

rulebook = RuleBook(settings.rules_dir)
conductor = Conductor(
    settings=settings,
    normalizer=TelemetryNormalizer(),
    evidence_agent=EvidenceAgent(),
    detection_agent=DetectionAgent(DetectionEngine(rulebook)),
    tactic_agent=TacticAgent(),
    chain_agent=ChainAgent(),
    analyst_agent=AnalystAgent(settings),
    safety_agent=SafetyAgent(GuardrailReviewer(settings)),
    scoring=ScoreEngine(),
    audit_trail=AuditTrail(settings.audit_log_path),
    memory=FeedbackMemory(settings.feedback_db_path, settings.memory_dir),
)
reporter = AnalystNarrative()

app = FastAPI(
    title=settings.app_name,
    description="From noisy Windows logs to evidence-backed incident reasoning.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)


def _attach_security_headers(response: Response) -> Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.middleware("http")
async def enforce_api_controls(request: Request, call_next):
    if request.url.path.startswith(settings.api_prefix) and settings.api_key:
        provided_key = resolve_api_key(request.headers.get("X-API-Key"), request.headers.get("Authorization"))
        if provided_key != settings.api_key:
            return _attach_security_headers(
                JSONResponse(status_code=401, content={"detail": "Invalid API key"})
            )

    response = await call_next(request)
    return _attach_security_headers(response)


def _enforce_rate_limit(request: Request, policy: RatePolicy, bucket: str) -> None:
    rate_limiter.enforce(f"{bucket}:{client_identity(request)}", policy)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_event_stream(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dataset `{path.name}` contains invalid JSONL at line {line_number}.",
                ) from exc
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"Dataset `{path.name}` contains a non-object event at line {line_number}.",
                )
            events.append(item)
        return events

    if isinstance(payload, dict) and "events" in payload:
        return list(payload["events"])
    if isinstance(payload, list):
        return payload
    raise HTTPException(status_code=400, detail=f"Dataset `{path.name}` does not contain a supported event list.")


def _dataset_registry() -> list[dict[str, Any]]:
    provenance = _load_json(settings.datasets_dir / "provenance.json")
    return list(provenance["datasets"])


def _dataset_lookup() -> dict[str, dict[str, Any]]:
    return {item["datasetId"]: item for item in _dataset_registry()}


def _dataset_payload() -> list[DatasetSummary]:
    summaries = []
    for item in _dataset_registry():
        summaries.append(
            DatasetSummary(
                datasetId=item["datasetId"],
                title=item["title"],
                description=item["description"],
                samplePath=item["samplePath"],
                attackDescription=item["attackDescription"],
                techniques=item["attckTechnique"],
                sourceName=item["sourceName"],
                sourceUrl=item["sourceUrl"],
                collectionType=item["collectionType"],
                benchmarkTier=item.get("benchmarkTier"),
            )
        )
    return summaries


def _read_dataset(dataset_name: str) -> list[dict[str, Any]]:
    dataset_meta = _dataset_lookup().get(dataset_name)
    dataset_path = (
        settings.root_dir / dataset_meta["samplePath"]
        if dataset_meta and dataset_meta.get("samplePath")
        else settings.datasets_dir / "samples" / f"{dataset_name}.json"
    )
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset `{dataset_name}` was not found.")
    return _load_event_stream(dataset_path)


def _is_subsequence(expected: list[str], actual: list[str]) -> bool:
    actual_index = 0
    for item in expected:
        while actual_index < len(actual) and actual[actual_index] != item:
            actual_index += 1
        if actual_index >= len(actual):
            return False
        actual_index += 1
    return True


def _citation_count(brief: str) -> int:
    return sum(1 for line in brief.splitlines() if "[Evidence:" in line)


def _evaluate_exports(result: AnalysisResult) -> dict[str, Any]:
    markdown_ok = bool(reporter.export_markdown(result).strip())
    json_ok = bool(json.loads(reporter.export_json(result)))
    pdf_path = settings.exports_dir / f"{result.analysis_id}-benchmark.pdf"
    reporter.export_pdf(result, pdf_path)
    pdf_ok = pdf_path.exists() and pdf_path.stat().st_size > 0
    return {
        "md": markdown_ok,
        "json": json_ok,
        "pdf": pdf_ok,
    }


def _evaluate_result(result: AnalysisResult, dataset_name: str) -> dict[str, Any]:
    expected = _load_json(settings.datasets_dir / "samples" / "expectedFindings.json")
    expected_case = expected["datasets"].get(dataset_name)
    if not expected_case:
        raise HTTPException(status_code=404, detail=f"No expected findings found for `{dataset_name}`.")

    actual_rules = {item.rule_id for item in result.findings}
    expected_rules = set(expected_case["expectedRules"])
    matched = sorted(actual_rules & expected_rules)
    rule_precision_like = round(len(matched) / max(1, len(actual_rules)), 2)
    rule_recall_like = round(len(matched) / max(1, len(expected_rules)), 2)

    actual_techniques = {item.technique_id for item in result.tactics}
    expected_techniques = set(expected_case.get("expectedTechniques", []))
    matched_techniques = sorted(actual_techniques & expected_techniques)
    technique_precision_like = round(len(matched_techniques) / max(1, len(actual_techniques)), 2)
    technique_recall_like = round(len(matched_techniques) / max(1, len(expected_techniques)), 2)

    actual_stages = [item.stage for item in result.attack_chain]
    expected_stages = expected_case.get("expectedStages", [])
    matched_stages = [stage for stage in expected_stages if stage in actual_stages]
    stage_recall_like = round(len(matched_stages) / max(1, len(expected_stages)), 2)
    chain_order_aligned = _is_subsequence(expected_stages, actual_stages)

    citation_count = _citation_count(result.analyst_brief)
    minimum_citations = int(expected_case.get("minimumCitationCount", 0))
    citation_coverage = round(min(citation_count / max(1, minimum_citations), 1.0), 2)

    required_sections = expected_case.get("requiredSections", [])
    missing_sections = [section for section in required_sections if section not in result.analyst_brief]
    sections_present = len(missing_sections) == 0

    export_status = _evaluate_exports(result)
    expected_exports = expected_case.get("expectedExports", [])
    exports_ready = all(export_status.get(item, False) for item in expected_exports)

    risk_aligned = result.scores.risk_label.value in expected_case["acceptableRiskLabels"]
    confidence_aligned = result.scores.confidence_score >= int(expected_case.get("minimumConfidence", 0))
    evidence_aligned = result.evidence_count >= int(expected_case.get("minimumEvidenceCount", 0))
    unexpected_rule_count = len(actual_rules - expected_rules)
    false_positive_pressure_ok = unexpected_rule_count <= int(expected_case.get("maxUnexpectedRules", 0))

    benchmark_score = round(
        (
            ((rule_precision_like + rule_recall_like) / 2) * 0.28
            + ((technique_precision_like + technique_recall_like) / 2) * 0.18
            + stage_recall_like * 0.16
            + (1.0 if chain_order_aligned else 0.0) * 0.08
            + citation_coverage * 0.12
            + (1.0 if sections_present else 0.0) * 0.07
            + (1.0 if exports_ready else 0.0) * 0.05
            + (1.0 if risk_aligned else 0.0) * 0.03
            + (1.0 if confidence_aligned else 0.0) * 0.02
            + (1.0 if false_positive_pressure_ok else 0.0) * 0.01
        )
        * 100,
        1,
    )

    return {
        "dataset": dataset_name,
        "benchmarkSource": expected_case.get("benchmarkSource"),
        "matchedRules": matched,
        "missingRules": sorted(expected_rules - actual_rules),
        "unexpectedRules": sorted(actual_rules - expected_rules),
        "matchedTechniques": matched_techniques,
        "missingTechniques": sorted(expected_techniques - actual_techniques),
        "unexpectedTechniques": sorted(actual_techniques - expected_techniques),
        "rulePrecisionLike": rule_precision_like,
        "ruleRecallLike": rule_recall_like,
        "techniquePrecisionLike": technique_precision_like,
        "techniqueRecallLike": technique_recall_like,
        "stageRecallLike": stage_recall_like,
        "expectedStages": expected_stages,
        "actualStages": actual_stages,
        "chainOrderAligned": chain_order_aligned,
        "citationCount": citation_count,
        "minimumCitationCount": minimum_citations,
        "citationCoverage": citation_coverage,
        "sectionsPresent": sections_present,
        "missingSections": missing_sections,
        "exportsReady": exports_ready,
        "exportStatus": export_status,
        "riskAligned": risk_aligned,
        "confidenceAligned": confidence_aligned,
        "evidenceAligned": evidence_aligned,
        "falsePositivePressureOk": false_positive_pressure_ok,
        "benchmarkScore": benchmark_score,
    }


def _public_benchmark_pack(report_mode: str | None = None) -> dict[str, Any]:
    datasets = [item for item in _dataset_registry() if item.get("benchmarkTier") == "public-upstream"]
    if not datasets:
        raise HTTPException(status_code=404, detail="No public upstream benchmark datasets are configured.")

    evaluations: list[dict[str, Any]] = []
    selected_mode = report_mode or settings.default_report_mode

    for ds in datasets:
        result = conductor.analyze(
            ds["datasetId"],
            _read_dataset(ds["datasetId"]),
            "public-benchmark-pack",
            selected_mode,
        )
        evaluation = _evaluate_result(result, ds["datasetId"])
        evaluation["title"] = ds["title"]
        evaluation["attackDescription"] = ds["attackDescription"]
        evaluation["collectionType"] = ds["collectionType"]
        evaluation["benchmarkTier"] = ds.get("benchmarkTier")
        evaluations.append(evaluation)

    average_benchmark_score = round(sum(item["benchmarkScore"] for item in evaluations) / len(evaluations), 1)
    average_rule_recall = round(sum(item["ruleRecallLike"] for item in evaluations) / len(evaluations), 2)
    average_technique_recall = round(sum(item["techniqueRecallLike"] for item in evaluations) / len(evaluations), 2)
    average_citation_coverage = round(sum(item["citationCoverage"] for item in evaluations) / len(evaluations), 2)
    pass_count = sum(1 for item in evaluations if item["benchmarkScore"] >= 85 and item["missingRules"] == [])

    return {
        "packName": "OTRF/Mordor Public Fixture Pack",
        "sourceName": "OTRF Security Datasets",
        "sourceUrl": "https://github.com/OTRF/Security-Datasets",
        "reportMode": selected_mode,
        "datasetCount": len(evaluations),
        "averageBenchmarkScore": average_benchmark_score,
        "averageRuleRecall": average_rule_recall,
        "averageTechniqueRecall": average_technique_recall,
        "averageCitationCoverage": average_citation_coverage,
        "passRate": round(pass_count / len(evaluations), 2),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "datasets": evaluations,
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "product": settings.app_name,
        "llmAvailable": settings.allow_llm,
        "llmModel": None,
        "defaultReportMode": settings.default_report_mode,
    }


@app.get("/api/datasets")
def list_datasets() -> list[dict[str, Any]]:
    return [item.model_dump(mode="json", by_alias=True) for item in _dataset_payload()]


@app.get("/api/provenance")
def provenance() -> dict[str, Any]:
    return _load_json(settings.datasets_dir / "provenance.json")


@app.get("/api/benchmarks/public")
def public_benchmarks(report_mode: str | None = None) -> dict[str, Any]:
    requested_mode = report_mode or settings.default_report_mode
    return _public_benchmark_pack(requested_mode)


@app.post("/api/analyze")
def analyze(request_body: AnalysisRequest, request: Request) -> dict[str, Any]:
    _enforce_rate_limit(request, analyze_rate_policy, "analyze")
    if request_body.events:
        dataset_name = request_body.dataset_name or "uploaded-events"
        raw_events = validate_uploaded_events(request_body.events)
        parser_mode = "json-body"
    elif request_body.dataset_name:
        dataset_name = request_body.dataset_name
        raw_events = _read_dataset(request_body.dataset_name)
        parser_mode = "reference-dataset"
    else:
        raise HTTPException(status_code=400, detail="Provide either `events` or `datasetName`.")

    requested_mode = request_body.report_mode or settings.default_report_mode
    result = conductor.analyze(dataset_name, raw_events, parser_mode, requested_mode)
    return result.model_dump(mode="json", by_alias=True)


@app.post("/api/analyze/upload")
async def analyze_upload(
    request: Request,
    file: UploadFile = File(...),
    report_mode: str | None = Form(default=None),
) -> dict[str, Any]:
    _enforce_rate_limit(request, upload_rate_policy, "upload")
    validate_upload_metadata(file.filename, file.content_type)
    body = await file.read()
    if len(body) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Upload must be a valid JSON file.") from exc

    events = validate_uploaded_events(payload)
    result = conductor.analyze(file.filename or "uploaded-events", events, "upload", report_mode or settings.default_report_mode)
    return result.model_dump(mode="json", by_alias=True)


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str) -> dict[str, Any]:
    try:
        result = conductor.load_analysis(analysis_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Analysis `{analysis_id}` was not found.") from exc
    return result.model_dump(mode="json", by_alias=True)


@app.post("/api/feedback")
def save_feedback(feedback: FeedbackRecord) -> dict[str, Any]:
    conductor.memory.save_feedback(feedback)
    return {"status": "saved"}


@app.post("/api/feedback/confidence-override")
def save_confidence_override(body: ConfidenceOverride) -> dict[str, Any]:
    return conductor.memory.save_confidence_override(
        body.analysis_id,
        body.dataset_name,
        body.analyst_confidence,
        body.override_note,
    )


@app.get("/api/feedback/confidence-override/{analysis_id}")
def get_confidence_override(analysis_id: str) -> dict[str, Any]:
    return conductor.memory.get_confidence_override(analysis_id)


@app.get("/api/audit")
def list_audit(
    limit: int = Query(default=20, ge=1, le=settings.audit_limit_max),
    cursor: str | None = Query(default=None),
) -> dict[str, Any]:
    try:
        page = conductor.audit_trail.page(limit=limit, cursor=cursor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "items": [
            item.model_dump(mode="json", by_alias=True, exclude={"provider_request_id"})
            for item in page["items"]
        ],
        "nextCursor": page["nextCursor"],
        "hasMore": page["hasMore"],
        "total": page["total"],
        "limit": page["limit"],
    }


@app.post("/api/evaluate")
def evaluate(request: AnalysisRequest) -> dict[str, Any]:
    if request.analysis_id:
        try:
            result = conductor.load_analysis(request.analysis_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Analysis `{request.analysis_id}` was not found.") from exc
        dataset_name = request.dataset_name or result.dataset_name
        return _evaluate_result(result, dataset_name)

    if not request.dataset_name:
        raise HTTPException(status_code=400, detail="Evaluation requires `datasetName` or `analysisId`.")

    result = conductor.analyze(
        request.dataset_name,
        _read_dataset(request.dataset_name),
        "evaluation",
        request.report_mode or settings.default_report_mode,
    )
    return _evaluate_result(result, request.dataset_name)


@app.get("/api/exports/{analysis_id}/{fmt}", response_model=None)
def export_report(analysis_id: str, fmt: str) -> Any:
    try:
        result = conductor.load_analysis(analysis_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Analysis `{analysis_id}` was not found.") from exc

    fmt = fmt.lower()
    if fmt == "json":
        return JSONResponse(json.loads(reporter.export_json(result)))
    if fmt == "md":
        return PlainTextResponse(reporter.export_markdown(result), media_type="text/markdown")
    if fmt == "pdf":
        pdf_bytes = generate_pdf(result)
        safe_dataset = result.dataset_name.replace(" ", "-")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{APP_EXPORT_PREFIX}-{safe_dataset}-{analysis_id[:8]}.pdf"'
                )
            },
        )
    raise HTTPException(status_code=400, detail="Supported formats: json, md, pdf.")
