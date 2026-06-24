<div align="center">

<img src="frontend/public/branding/aleens-logo.png" alt="Aldeens logo" width="320" />

# Aldeens

### Local-first Windows incident triage with evidence-backed reasoning, deterministic scoring, and MITRE ATT&CK mapping

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Node 20+](https://img.shields.io/badge/node-20%2B-green.svg)](https://nodejs.org/)
[![CI](https://github.com/aleens-labs/ALDEENS/actions/workflows/ci.yml/badge.svg)](https://github.com/aleens-labs/ALDEENS/actions/workflows/ci.yml)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20mapped-red.svg)](https://attack.mitre.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Turn noisy Windows telemetry into an auditable, evidence-backed investigation in seconds — without sending a single event to the cloud.**

</div>

---

## Why Aldeens

Most triage tools hand you a verdict and hide the reasoning. Aldeens does the opposite. Every risk score, every ATT&CK technique, and every line in the report traces back to a specific piece of evidence with a stable rule ID. The core detection pipeline is **fully deterministic and reproducible** — an optional LLM layer can write a narrative, but it never decides the outcome.

If you have ever had to defend a detection in an audit, a post-incident review, or a customer escalation, Aldeens is built for you.

| Principle | What it means in practice |
|-----------|---------------------------|
| **Evidence first** | Every claim points back to an evidence ID and raw event reference. |
| **Deterministic before AI** | Detection is rule-based and reproducible. The LLM only narrates sanitized findings. |
| **Local by default** | Analysis, audit history, and analyst memory stay on disk. No cloud dependency. |
| **Fail closed** | Production-safe mode refuses to start without an API key. |
| **Transparent** | Scoring, rule traces, and limitations are all visible to the analyst. |

---

## What Aldeens Does

- Normalizes Windows, Sysmon, and Defender-style JSON telemetry into one consistent evidence model.
- Applies deterministic detection rules with traceable rule IDs and explicit score contributions.
- Maps every detection to a MITRE ATT&CK technique and tactic.
- Reconstructs the attack chain from timestamped evidence.
- Calculates risk and confidence from documented, reproducible formulas.
- Validates rules against exact upstream OTRF / Mordor fixtures with provenance and hashes.
- Stores analyst feedback and confidence overrides locally as case memory.
- Exports professional incident reports as PDF, Markdown, and JSON.

Aldeens is **not** a managed detection service, an EDR replacement, an autonomous response engine, or an exploit framework. It is a defensive triage and evidence-reasoning surface.

---

## Detection Coverage (MITRE ATT&CK)

Aldeens ships with deterministic rules mapped to the following ATT&CK techniques. Coverage is intentionally transparent: what you see here is exactly what the engine detects today.

| Rule ID | Detection | ATT&CK | Tactic |
|---------|-----------|--------|--------|
| `DL-WIN-001` | Office application spawned PowerShell | [T1059.001](https://attack.mitre.org/techniques/T1059/001/) | Execution |
| `DL-WIN-002` | Suspicious parent-child process lineage | [T1059.001](https://attack.mitre.org/techniques/T1059/001/) | Execution |
| `DL-PS-001` | Encoded / obfuscated PowerShell command | [T1027](https://attack.mitre.org/techniques/T1027/) | Defense Evasion |
| `DL-CR-001` | LSASS memory access signal | [T1003.001](https://attack.mitre.org/techniques/T1003/001/) | Credential Access |
| `DL-NET-001` | Suspicious public outbound from script/LOLBIN | [T1071](https://attack.mitre.org/techniques/T1071/) | Command and Control |
| `DL-PER-001` | Registry run-key persistence | [T1547](https://attack.mitre.org/techniques/T1547/) | Persistence |
| `DL-PER-002` | Scheduled-task persistence | [T1053](https://attack.mitre.org/techniques/T1053/) | Persistence |

> Scoring formulas, confidence logic, and guardrails are documented in [`RULES.md`](RULES.md). Planned coverage is tracked on the [roadmap](ROADMAP.md).

---

## Benchmarks

Aldeens validates its rules against **exact upstream OTRF / Mordor JSONL fixtures** (not synthetic data), bundled with provenance and hashes. The evaluator compares actual rule output against per-dataset expectations and reports rule recall, ATT&CK recall, citation coverage, and an aggregate benchmark score.

Run the public pack yourself:

```bash
python -m app.cli benchmarks public --report-mode template
```

<!-- BENCHMARK RESULTS: Maintainers — paste your latest reproducible numbers here after running the command above.
| Dataset | Rule recall | ATT&CK recall | Result |
|---------|-------------|---------------|--------|
| otrfLsassMemoryDumpComsvcs | ... | ... | PASS |
| otrfRegistryRunKeyPersistence | ... | ... | PASS |
| otrfPowerShellCmstpOutbound | ... | ... | PASS |
Aggregate score: ...
-->

> _Reproducible benchmark numbers are published per release. See [`EVALUATION.md`](EVALUATION.md) for the full evaluation methodology._

---

## Demo

<!-- SCREENSHOT: Add a dashboard screenshot or demo GIF here for maximum impact.
Place the file in docs/assets/ and reference it like:
![Aldeens dashboard](docs/assets/dashboard.png)
-->

_A 60-second walkthrough is documented in [`DEMO.md`](DEMO.md)._

---

## Quick Start

### Prerequisites

Python 3.11+, Node.js 20+, npm, Git. Docker Desktop is optional.

### Option A — Docker Compose (fastest)

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health

### Option B — Manual

```bash
# Backend
cd backend
python -m pip install -e .[dev]
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173.

---

## CLI Usage

Aldeens ships a terminal-first CLI for analysts who live in the shell.

```bash
cd backend
python -m pip install -e .[dev]

python -m app.cli datasets                                   # list reference datasets
python -m app.cli analyze --dataset officeToPowerShell       # run an analysis
python -m app.cli audit --limit 5                            # view recent audit records
python -m app.cli export --latest --format pdf               # export latest report
python -m app.cli benchmarks public --report-mode template   # run the OTRF benchmark pack
```

Analyze your own telemetry:

```bash
python -m app.cli analyze --input ./events.json --dataset-name incident-001 --markdown-out ./incident-001.md
```

---

## Working With Real Telemetry

Aldeens accepts reference datasets and your own exported Windows-style telemetry. Provide as many of these fields as possible — Aldeens never invents missing data, and reports explicitly flag incomplete telemetry.

```jsonc
{
  "timestamp": "2025-01-10T14:22:31Z",
  "hostname": "WKSTN-01",
  "username": "jdoe",
  "process_name": "powershell.exe",
  "parent_process_name": "WINWORD.EXE",
  "command_line": "powershell -enc <base64>",
  "process_id": 4821,
  "parent_process_id": 3310,
  "image_path": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
  "src_ip": "10.0.0.5",
  "dst_ip": "203.0.113.10",
  "event_id": 1
}
```

Reference dataset provenance is documented in `backend/datasets/provenance.json`.

---

## Reports and Exports

Aldeens exports analyst-ready PDF, Markdown, and JSON reports. Every report preserves: executive summary, risk and confidence score, analyst verdict, ATT&CK mapping, timeline, process tree, command-line evidence, host/user context, detection details, analyst feedback history, recommended next steps, and telemetry limitations.

---

## Security & Production Hardening

Aldeens is designed to be safe for public release. Local secrets and generated artifacts stay out of git by default.

- `.env` files, runtime output, SQLite databases, and local memory artifacts are git-ignored.
- Production-safe mode **fails closed** if `ALEENS_API_KEY` is missing.
- Authenticated deployments require `X-API-Key` or `Authorization: Bearer ...`.
- Analyze and upload endpoints are rate-limited; audit pagination is bounded.
- CORS must be restricted to explicit trusted origins for any shared deployment.

Before exposing the backend beyond localhost, set `ALEENS_PRODUCTION_SAFE=true`, a strong `ALEENS_API_KEY`, restrict `ALEENS_CORS_ORIGINS`, and keep rate limits enabled. See [`SECURITY.md`](SECURITY.md) for the full posture and vulnerability reporting.

The full configuration reference lives in `.env.example`.

---

## Testing

```bash
cd backend && python -m pytest                 # backend + report tests
cd frontend && npm install && npm run build    # frontend build
```

---

## Contributing

Contributions are welcome — new detection rules, dataset fixtures, parsers, and docs especially. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and the [`ROADMAP.md`](ROADMAP.md) for where the project is headed.

---

## Responsible Use

Aldeens is a defensive security research and incident triage tool. Use it only on telemetry you are authorized to analyze. The project does not provide exploit generation, malware development, credential theft, persistence guidance, or offensive automation. When using optional LLM reporting, review the generated narrative before sharing externally — the deterministic evidence, rule trace, and raw references remain the source of truth.

---

## License

Released under the [MIT License](LICENSE).
