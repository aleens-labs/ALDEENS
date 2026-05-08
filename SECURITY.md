# Security Policy

Aleens is built for defensive telemetry analysis only.

## Allowed Use

- Analyze Windows, Sysmon, and Defender-style logs
- Reconstruct evidence-backed attack chains
- Support SOC triage and explainability
- Export defensive reports for analyst review

## Forbidden Use

- No exploit generation
- No payload generation
- No evasion guidance
- No live endpoint attack workflow
- No persistence instructions
- No credential theft assistance
- No host isolation or destructive action

## Safety Controls

- Guardrail review sanitizes payload-like command content before narrative rendering.
- Only structured findings are eligible for reporting mode.
- Agents are bounded to defensive analysis and cannot execute system commands.
- Deterministic template reporting is always available as the fail-safe mode.

## Data Handling

- Reference incident datasets are not production data.
- Local runtime output is stored under `backend/runtime/`.
- Analyst feedback is stored locally in SQLite and exported snapshots under `memory/`.
- For public or shared deployments, set `ALEENS_API_KEY`, keep `.env` out of version control, and restrict allowed frontend origins.

## Publish-Safe Runtime Settings

- `ALEENS_PRODUCTION_SAFE=true` forces the backend to fail closed if `ALEENS_API_KEY` is missing.
- `ALEENS_CORS_ORIGINS` should list only trusted frontend origins.
- `ALEENS_ANALYZE_RATE_LIMIT` and `ALEENS_UPLOAD_RATE_LIMIT` should remain enabled in any shared deployment.
- `/api/audit` is paginated and bounded to reduce accidental over-disclosure and memory pressure.

## Reporting A Vulnerability

If you discover a security issue in Aleens:

- do not publish live secrets, tokens, or exploit instructions
- capture the affected version, route, and reproduction steps
- report it privately to the repository owner before public disclosure
