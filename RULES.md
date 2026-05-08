# Aleens Rules and Scoring

## Deterministic Detection Rules

### `DL-WIN-001` Office spawned PowerShell

- Fires when a PowerShell process is launched by `WINWORD.EXE`, `EXCEL.EXE`, `POWERPNT.EXE`, or `OUTLOOK.EXE`
- ATT&CK: `T1059.001`
- Score: `+20`
- Confidence: `+0.16`

### `DL-PS-001` Encoded PowerShell command

- Fires on `-enc`, `-EncodedCommand`, or `FromBase64String`
- ATT&CK: `T1027`
- Score: `+20`
- Confidence: `+0.18`

### `DL-CR-001` LSASS access signal

- Fires when telemetry targets `lsass.exe`
- ATT&CK: `T1003.001`
- Score: `+35`
- Confidence: `+0.22`

### `DL-NET-001` Suspicious public outbound connection

- Fires when a scripting or LOLBIN process opens a connection to a public IP
- ATT&CK: `T1071`
- Score: `+20`
- Confidence: `+0.16`

### `DL-PER-001` Persistence via registry autorun

- Fires when a Run-key style registry path is modified
- ATT&CK: `T1547`
- Score: `+25`
- Confidence: `+0.18`

### `DL-PER-002` Persistence via scheduled task

- Fires on `schtasks.exe /create` or task-path evidence
- ATT&CK: `T1053`
- Score: `+25`
- Confidence: `+0.18`

### `DL-WIN-002` Suspicious parent-child process chain

- Fires on suspicious Office or shell lineage into PowerShell, `cmd.exe`, `mshta.exe`, `regsvr32.exe`, or `rundll32.exe`
- ATT&CK: `T1059.001`
- Score: `+15`
- Confidence: `+0.12`

## Public Benchmark Coverage

The bundled upstream OTRF/Mordor benchmark pack validates the current rules against exact JSONL fixtures for:

- LSASS memory-dump behavior with execution lineage
- Registry run-key persistence
- PowerShell outbound traffic to public IP infrastructure

## Risk Logic

- Base risk is the sum of all triggered rule contributions.
- Add `+10` when the incident spans three or more ATT&CK tactics.
- Subtract `-5` to `-15` when evidence completeness is low.
- Clamp the final score to `0-100`.

Risk labels:

- `0-29` Low
- `30-59` Medium
- `60-79` High
- `80-100` Critical

## Confidence Logic

- Starts from a deterministic baseline.
- Increases with evidence completeness.
- Increases with rule trace quality and ATT&CK coverage.
- Does not claim certainty beyond the uploaded telemetry.

## Guardrail Logic

- Encoded or payload-like command content is redacted before narrative rendering.
- Structured findings only are forwarded to the narrative layer.
- If optional LLM mode is enabled, it receives only sanitized structured findings and must cite existing evidence IDs and raw references.
- If LLM mode is unavailable or fails validation, the product falls back to deterministic templates.
