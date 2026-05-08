<p align="center">
  <img src="frontend/public/branding/aleens-logo.png" alt="Aleens logo" width="160" />
</p>

# Aleens

**Aleens** is a local-first Windows incident triage workspace that converts Windows, Sysmon, and Defender-style telemetry into a structured incident narrative with evidence citations, deterministic scoring, ATT&CK coverage, and analyst feedback memory.

It is designed for security research teams, SOC workflows, internal labs, and hackathon evaluation environments that need a fast triage surface without giving up auditability. Aleens is intentionally opinionated: evidence extraction and scoring remain deterministic, while the optional LLM layer is limited to writing grounded narrative from already-sanitized findings.

## What Aleens Provides

- Deterministic Windows telemetry normalization and rule-based detection
- ATT&CK mapping, chain reconstruction, and confidence scoring
- Inline evidence references, raw event traceability, and analyst feedback history
- Local audit storage, PDF/Markdown/JSON exports, and reference benchmark evaluation
- Optional LLM-assisted reporting with guardrails and deterministic fallback behavior

## Release Posture

Aleens is published as a **security research and incident triage platform**. It is suitable for local evaluation, controlled internal deployments, and offline demonstrations. It is **not** positioned as a managed detection service or an autonomous response product.

For any environment that is reachable beyond localhost, enable the hardened mode documented later in this README:

- set `ALEENS_PRODUCTION_SAFE=true`
- configure `ALEENS_API_KEY`
- mirror that key in `VITE_ALEENS_API_KEY`
- restrict `ALEENS_CORS_ORIGINS` to trusted frontends only

## Problem Statement

SOC teams regularly receive fragmented process, network, and Defender alerts that are difficult to stitch into a coherent story under time pressure. Generic chat assistants can explain a log line, but they do not usually preserve a deterministic chain of evidence, a reproducible scoring model, or a local audit trail that analysts can trust during triage.

## Why This Matters

- Analysts need quick triage without losing provenance.
- High-noise Windows telemetry benefits from repeatable evidence extraction before any narrative layer is involved.
- Judges and defenders should be able to inspect which rules fired, which evidence supported them, how MITRE ATT&CK was mapped, and why the score landed where it did.

## Design Principles

Aleens is intentionally built as a hybrid: deterministic reasoning first, optional narrative AI second.

- It normalizes telemetry into a stable evidence schema.
- It fires reproducible, human-reviewable rules.
- It maps rule output to ATT&CK techniques and tactics.
- It reconstructs an attack chain with timestamped evidence references.
- It logs every analysis into a local audit trail.
- It stores analyst feedback locally without allowing memory to silently override hard rules.
- It can optionally render a structured LLM brief through the OpenAI Responses API, but only from sanitized findings.
- It falls back to deterministic template reporting when no API key is configured or a model call fails.

## Architecture

1. Intake
2. Evidence extraction
3. Detection rules
4. MITRE ATT&CK mapping
5. Attack chain reconstruction
6. Risk and confidence scoring
7. Guardrail review
8. Analyst report rendering with inline evidence citations
9. Audit trail
10. Analyst feedback memory

Pipeline view:

`Evidence Ingestion -> Parser -> Rule Engine -> MITRE Mapper -> Risk Scorer -> Agent Orchestrator -> Analyst Report -> Audit Log -> Feedback Memory`

## Local-First Design

- Reference incident datasets do not require API keys.
- Reference mode ships with both prepared reference incidents and bundled public upstream OTRF/Mordor fixtures.
- All analysis results, audit events, and feedback stay local on disk under `backend/runtime/` and `memory/`.
- Report generation can fall back to deterministic templates when LLM mode is unavailable or unsafe.
- When `ALEENS_API_KEY` is configured, the backend expects `X-API-Key` or `Authorization: Bearer ...` on API requests.
- Analyze and upload endpoints are rate-limited to reduce cost exhaustion and API abuse.

## Agent Design

Controlled agents coordinate the workflow but never execute shell commands, create payloads, or generate offensive content:

- `Conductor`
- `EvidenceAgent`
- `DetectionAgent`
- `TacticAgent`
- `ChainAgent`
- `AnalystAgent`
- `SafetyAgent`

See [AGENTS.md](AGENTS.md) for boundaries and allowed actions.

## Safety Model

- Defensive telemetry analysis only
- No exploit generation
- No payload generation
- No evasion advice
- Guardrail review strips payload-like content before any narrative layer
- Structured findings only are passed into reporting mode
- Evidence IDs and raw references are cited inside the report and attack timeline

See [SECURITY.md](SECURITY.md) and [RULES.md](RULES.md).

## Dataset Provenance

All reference datasets are documented in [backend/datasets/provenance.json](backend/datasets/provenance.json).

The repo now includes:

- a derived reference chain for `officeToPowerShell`
- an exact upstream OTRF LSASS memory-dump fixture
- an exact upstream OTRF run-key persistence fixture
- an exact upstream OTRF PowerShell outbound fixture

Each upstream bundle records:

- `sourceName`
- `sourceUrl`
- `collectionType`
- `attackDescription`
- `attckTechnique`
- `archiveMember`
- `fixtureSha256`

You can refresh the bundled public fixtures from upstream with:

```powershell
cd backend
python scripts/refreshBenchmarks.py
```

The repo also explains how to replace or extend these with:

- OTRF / Mordor security datasets
- Exported Sysmon JSON
- Microsoft Defender-style incident exports

Evaluator mode now scores benchmark fit across:

- rule precision and recall
- ATT&CK precision and recall
- chain ordering
- evidence citation coverage
- report section coverage
- export integrity

## Reference Walkthrough

1. Open the dashboard.
2. Run the **Office to PowerShell Reference Chain** or upload Windows telemetry.
3. Review the risk score, confidence, ATT&CK map, and attack timeline.
4. Inspect the evidence board and rule trace.
5. Run the **Public OTRF Fixture Pack** to show the exact upstream benchmark pack and aggregate benchmark score.
6. Switch to **Administrative PowerShell Inventory** to show an intentionally ambiguous low-risk dataset.
7. Add analyst feedback, rerun the analysis, and show that local memory is surfaced without silently overriding hard rules.
8. Export the incident report as Markdown, JSON, or PDF.
9. Switch between deterministic template mode and optional LLM narrative mode if an API key is configured.

See [DEMO.md](DEMO.md) for the judge-facing flow.

## How To Run

### Quick CLI Workflow

After installing the backend in editable mode, you can use the built-in CLI without starting the frontend.
The most reliable cross-shell form is `python -m app.cli ...`; after opening a fresh shell, the `aleens ...` shortcut is also available.

```powershell
cd backend
python -m pip install -e .[dev]
python -m app.cli datasets
python -m app.cli analyze --dataset officeToPowerShell --report-mode template
python -m app.cli audit --limit 5
python -m app.cli export --latest --format pdf
python -m app.cli benchmarks public --report-mode template
```

You can also analyze your own telemetry file directly:

```powershell
python -m app.cli analyze --input C:\path\to\events.json --dataset-name incident-001 --markdown-out C:\path\to\incident-001.md
```

If you want to export a specific saved run, use a real ID value, not angle-bracket placeholders:

```powershell
python -m app.cli export --analysis-id b6091f10eb9b --format pdf
```

## Security Posture Before Publish

Aleens is safe to publish as source code, but it should not be exposed on a reachable network without local API protection.

Minimum publish-safe controls:

- keep `.env` and `backend/.env` out of git
- set `ALEENS_API_KEY`
- set `VITE_ALEENS_API_KEY` to the same value for the frontend
- keep `ALEENS_PRODUCTION_SAFE=true` for any non-dev deployment
- restrict `ALEENS_CORS_ORIGINS` to trusted frontend origins only
- leave rate limiting enabled on analyze and upload routes

With `ALEENS_PRODUCTION_SAFE=true`, the backend now fails closed at startup if `ALEENS_API_KEY` is missing.

### Docker Compose

From the repository root:

```powershell
docker-compose up --build
```

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Backend Only

```powershell
cd backend
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

### Frontend Only

```powershell
cd frontend
npm install
npm run dev
```

Optional LLM configuration:

```powershell
$env:ALEENS_API_KEY="set-a-local-api-key-before-public-exposure"
$env:VITE_ALEENS_API_KEY="set-the-same-key-for-the-frontend"
$env:ALEENS_PRODUCTION_SAFE="true"
$env:OPENAI_API_KEY="your_key_here"
$env:ALEENS_LLM_MODEL="openai/gpt-4o-mini"
```

Recommended publish-safe local API controls:

```powershell
$env:ALEENS_CORS_ORIGINS="http://localhost:5173"
$env:ALEENS_ANALYZE_RATE_LIMIT="10/minute"
$env:ALEENS_UPLOAD_RATE_LIMIT="5/minute"
$env:ALEENS_AUDIT_LIMIT_MAX="100"
```

Frontend and backend should then be restarted:

```powershell
cd backend
uvicorn app.main:app --reload

cd ../frontend
npm run dev
```

## Deployment Notes

- `/api/audit` now uses bounded pagination with `limit` and `cursor`.
- export endpoints require the same API key when backend auth is enabled.
- `/api/health` intentionally hides the provider model name for public safety.
- audit responses intentionally omit `providerRequestId`.

Example authenticated request:

```powershell
$headers = @{ "X-API-Key" = $env:ALEENS_API_KEY }
Invoke-RestMethod -Uri "http://localhost:8000/api/audit?limit=20" -Headers $headers
```

## Repository Hygiene

Before pushing to GitHub, confirm:

- `.env` is not tracked
- `backend/runtime/` artifacts are not tracked
- local SQLite files are not tracked
- no live API key appears in screenshots, notebooks, or exported JSON
- example env files contain blanks only, never real credentials

## Judge Scoring Alignment

Aleens was shaped to score well on:

- **Impact**: faster analyst triage from noisy Windows telemetry
- **Innovation**: deterministic reasoning before narrative AI
- **Feasibility**: local-first stack with sample data and Docker compose
- **Technical depth**: evidence normalization, ATT&CK mapping, scoring, feedback memory, audit trail
- **Safety**: explicit defensive-only guardrails and fallback behavior
- **Demo clarity**: one-click demo chain with traceable outputs
