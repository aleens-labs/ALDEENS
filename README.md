<p align="center">
  <img src="frontend/public/branding/aleens-logo.png" alt="Aleens logo" width="360" />
</p>

# Aleens

**Local-first Windows incident triage with evidence-backed reasoning, deterministic scoring, ATT&CK mapping, analyst memory, and professional incident reporting.**

Aleens helps security analysts turn noisy Windows, Sysmon, Defender-style, and compatible JSON telemetry into a structured investigation view. It is built for security research labs, SOC training, internal validation, and local incident-response workflows where evidence traceability matters more than opaque automation.

The core pipeline is deterministic. Rules extract evidence, map it to MITRE ATT&CK, reconstruct a timeline, calculate risk and confidence, and produce an auditable report. An optional LLM layer can write a grounded narrative from already-sanitized findings, but it does not decide the detection outcome.

## Table of Contents

- [What Aleens Does](#what-aleens-does)
- [Who This Is For](#who-this-is-for)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [CLI Usage](#cli-usage)
- [Configuration](#configuration)
- [Security Defaults](#security-defaults)
- [Working With Real Telemetry](#working-with-real-telemetry)
- [Reports and Exports](#reports-and-exports)
- [Testing](#testing)
- [Public Release Checklist](#public-release-checklist)
- [Responsible Use](#responsible-use)

## What Aleens Does

- Normalizes Windows incident telemetry into a consistent evidence model.
- Applies deterministic detection rules with traceable rule IDs and score contributions.
- Maps detections to MITRE ATT&CK techniques and tactics.
- Reconstructs an attack chain from timestamped evidence.
- Calculates risk and confidence from reproducible scoring formulas.
- Preserves raw event references, evidence IDs, command lines, process context, and host/user context when available.
- Stores analyst feedback and confidence overrides locally.
- Exports professional reports as PDF, Markdown, and JSON.
- Supports reference datasets and uploaded telemetry without requiring cloud services.

## Who This Is For

Aleens is intended for:

- SOC analysts who need a fast local triage surface.
- Security researchers validating detection logic.
- Blue-team labs and training environments.
- Hackathon or research demos that require explainable outputs.
- Teams that want deterministic evidence extraction before using an AI narrative layer.

Aleens is not a managed detection service, EDR replacement, autonomous response engine, or exploit framework.

## System Architecture

```text
Telemetry Input
      |
      v
Parser and Normalizer
      |
      v
Detection Rule Engine
      |
      v
MITRE ATT&CK Mapper
      |
      v
Attack Chain Builder
      |
      v
Risk and Confidence Scoring
      |
      v
Guardrails and Redaction
      |
      v
Analyst Brief, Reports, Audit Trail, Feedback Memory
```

Design principles:

- **Evidence first:** every important claim should point back to evidence IDs or raw event references.
- **Deterministic before AI:** LLM reporting is optional and grounded in structured findings.
- **Local by default:** runtime analysis, audit history, and feedback memory stay on disk.
- **Fail closed in production:** production-safe mode requires an API key before the backend starts.
- **Research-grade transparency:** scoring, rule traces, and limitations are visible to the analyst.

## Repository Structure

```text
.
├── backend/
│   ├── app/                    # FastAPI backend, analysis pipeline, CLI
│   ├── datasets/               # Reference dataset metadata and provenance
│   ├── tests/                  # Backend and report-generation tests
│   └── runtime/                # Local generated analysis data, ignored by git
├── frontend/
│   ├── public/branding/        # Aleens logo and public assets
│   └── src/                    # React + Vite frontend
├── docs/                       # Supporting documentation
├── memory/                     # Local analyst memory, ignored by git
├── docker-compose.yml          # Local full-stack runtime
├── SECURITY.md                 # Vulnerability reporting and security posture
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm
- Git
- Optional: Docker Desktop

### Option A: Run With Docker Compose

From the repository root:

```powershell
docker-compose up --build
```

Open:

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend health: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Option B: Run Backend and Frontend Manually

Backend:

```powershell
cd backend
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## CLI Usage

The backend includes a local CLI for analysts who want terminal-first workflows.

Install the backend package:

```powershell
cd backend
python -m pip install -e .[dev]
```

List available reference datasets:

```powershell
python -m app.cli datasets
```

Run an analysis:

```powershell
python -m app.cli analyze --dataset officeToPowerShell --report-mode template
```

View recent audit records:

```powershell
python -m app.cli audit --limit 5
```

Export the latest analysis:

```powershell
python -m app.cli export --latest --format pdf
python -m app.cli export --latest --format json
python -m app.cli export --latest --format md
```

Export a specific analysis:

```powershell
python -m app.cli export --analysis-id b6091f10eb9b --format pdf
```

Analyze your own telemetry file:

```powershell
python -m app.cli analyze --input C:\path\to\events.json --dataset-name incident-001 --markdown-out C:\path\to\incident-001.md
```

Run the public benchmark pack:

```powershell
python -m app.cli benchmarks public --report-mode template
```

Note: do not type angle-bracket placeholders such as `<analysis-id>` in PowerShell. Use a real analysis ID from the audit output.

## Configuration

Create a local environment file from the example:

```powershell
Copy-Item backend\.env.example backend\.env
```

Important backend variables:

| Variable | Purpose | Recommended value |
| --- | --- | --- |
| `ALEENS_PRODUCTION_SAFE` | Enables fail-closed production safety checks | `true` for public or shared environments |
| `ALEENS_API_KEY` | Required API key when production-safe mode is enabled | A long random secret |
| `ALEENS_CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173` for local dev |
| `ALEENS_MAX_UPLOAD_BYTES` | Maximum upload size | Keep bounded for public use |
| `ALEENS_ANALYZE_RATE_LIMIT` | Rate limit for analysis calls | Example: `10/minute` |
| `ALEENS_UPLOAD_RATE_LIMIT` | Rate limit for upload calls | Example: `5/minute` |
| `ALEENS_AUDIT_LIMIT_MAX` | Maximum page size for audit pagination | Example: `100` |
| `OPENAI_API_KEY` | Optional LLM narrative provider key | Leave unset for deterministic-only mode |
| `ALEENS_LLM_MODEL` | Optional narrative model name | Configure only if using LLM mode |

Important frontend variables:

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend API base URL |
| `VITE_ALEENS_API_KEY` | Mirrors `ALEENS_API_KEY` for authenticated local frontend calls |

Example local development values:

```powershell
$env:ALEENS_CORS_ORIGINS="http://localhost:5173"
$env:ALEENS_ANALYZE_RATE_LIMIT="10/minute"
$env:ALEENS_UPLOAD_RATE_LIMIT="5/minute"
$env:ALEENS_AUDIT_LIMIT_MAX="100"
```

Example production-safe values:

```powershell
$env:ALEENS_PRODUCTION_SAFE="true"
$env:ALEENS_API_KEY="replace-with-a-long-random-secret"
$env:VITE_ALEENS_API_KEY="replace-with-the-same-secret"
$env:ALEENS_CORS_ORIGINS="https://your-trusted-frontend.example"
```

## Security Defaults

Aleens is designed to be safe for public source release, but local runtime secrets and generated artifacts must stay out of git.

Current security posture:

- `.env` files are ignored.
- Runtime analysis output is ignored.
- SQLite databases and local memory artifacts are ignored.
- Production-safe mode fails closed if `ALEENS_API_KEY` is missing.
- Authenticated deployments require `X-API-Key` or `Authorization: Bearer ...`.
- Analyze and upload endpoints are rate-limited.
- Audit pagination is bounded.
- Upload size and JSON parsing are validated by the backend.
- CORS should be restricted to explicit trusted origins for any shared deployment.

Before exposing the backend outside localhost:

1. Set `ALEENS_PRODUCTION_SAFE=true`.
2. Set a strong `ALEENS_API_KEY`.
3. Configure the frontend with `VITE_ALEENS_API_KEY`.
4. Restrict `ALEENS_CORS_ORIGINS`.
5. Keep rate limits enabled.
6. Never commit `.env`, runtime databases, API keys, or generated incident data.

See [SECURITY.md](SECURITY.md) for vulnerability reporting guidance.

## Working With Real Telemetry

Aleens supports reference datasets and uploaded Windows-style telemetry. Reference datasets are included so the pipeline can be tested immediately, but production analysts should upload their own exported telemetry for real investigations.

Supported telemetry should include as many of these fields as possible:

- timestamp
- process name
- parent process name
- command line
- process ID and parent process ID
- hostname
- username and domain
- image path and parent image path
- source and destination IPs
- event ID or raw event reference

If fields are missing, Aleens does not invent them. Reports explicitly show `Not available` or explain that telemetry was incomplete.

Reference dataset provenance is documented in [backend/datasets/provenance.json](backend/datasets/provenance.json).

## Reports and Exports

Aleens can export:

- PDF incident reports for analyst handoff.
- Markdown reports for notes, tickets, and documentation.
- JSON reports for downstream tooling.

Reports preserve:

- executive summary
- risk and confidence score
- final analyst verdict
- MITRE ATT&CK mapping
- timeline
- process tree
- command-line evidence
- host and user context
- detection details
- analyst feedback history
- recommended investigation steps
- telemetry limitations

## Testing

Backend tests:

```powershell
cd backend
python -m pytest
```

CLI tests:

```powershell
cd backend
python -m pytest tests\testCli.py -q
```

Frontend build:

```powershell
cd frontend
npm install
npm run build
```

Security and hygiene checks before public push:

```powershell
git status --short
git ls-files
git grep -n -I "sk-"
git grep -n -I "OPENAI_API_KEY"
```

Variable names in examples are expected. Real secret values must not appear in tracked files.

## Public Release Checklist

Use this checklist before pushing to a public GitHub repository:

- [ ] `git status --short` is clean except intentional changes.
- [ ] No `.env` files are tracked.
- [ ] No SQLite databases are tracked.
- [ ] No `backend/runtime/` output is tracked.
- [ ] No `node_modules/`, virtual environments, or build artifacts are tracked.
- [ ] No API keys, bearer tokens, or provider secrets appear in tracked files.
- [ ] `README.md` explains setup, security, CLI, and report outputs.
- [ ] `SECURITY.md` exists.
- [ ] `.gitignore` covers secrets and runtime artifacts.
- [ ] Backend tests pass.
- [ ] Frontend build passes if frontend changes were made.

## Responsible Use

Aleens is a defensive security research and incident triage tool. Use it only on telemetry you are authorized to analyze. The project does not provide exploit generation, malware development, credential theft, persistence guidance, or offensive automation.

When using optional LLM reporting, review the generated narrative before sharing externally. The deterministic evidence, rule trace, and raw references remain the source of truth.
