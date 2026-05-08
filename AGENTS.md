# Aleens Agents

## Roles

- **Conductor**: orchestrates the analysis workflow and persistence
- **EvidenceAgent**: normalizes telemetry into evidence objects
- **DetectionAgent**: applies deterministic rules only
- **TacticAgent**: maps findings to ATT&CK tactics and techniques
- **ChainAgent**: rebuilds a defensible attack chain
- **AnalystAgent**: writes a defensive analyst brief from structured findings
- **SafetyAgent**: enforces payload redaction and defensive-only report boundaries

## Allowed Actions

- Parse uploaded or demo JSON telemetry
- Normalize Windows, Sysmon, and Defender-style fields
- Fire deterministic rules
- Score risk and confidence
- Produce analyst-safe markdown, JSON, and PDF exports
- Record audit events and analyst feedback locally

## Forbidden Actions

- No system command execution
- No shelling out to the host
- No exploit generation
- No payload creation
- No offensive automation
- No evasion advice
- No destructive remediation

## Boundary Rules

- Every claim must cite deterministic evidence or clearly state a limitation.
- Analyst memory may add context, but it must not silently override hard rules.
- If optional LLM mode is unavailable or unsafe, the system must fall back to deterministic reporting.
