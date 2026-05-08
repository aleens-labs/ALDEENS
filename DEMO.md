# Aleens Demo

## Judge Flow

1. Start the stack with `docker-compose up --build`.
2. Open the frontend dashboard at `http://localhost:5173`.
3. Press **Run Demo Attack Chain**.
4. Observe:
   - High or Critical risk
   - Confidence above 80
   - Visible attack chain
   - Visible ATT&CK mapping
   - Visible rule trace
   - Inline evidence citations in the report
   - Analyst brief
5. Press **Run Public OTRF Fixture Pack** and show:
   - average benchmark score
   - per-dataset coverage against exact upstream OTRF/Mordor fixtures
   - public-fixture pass rate
6. Switch to **Administrative PowerShell Inventory** and show:
   - Low risk
   - A single deterministic rule
   - Why the case lands in review territory instead of being overcalled as malicious
7. Submit a feedback verdict and note, then rerun the analysis to show memory-backed prior case notes.
8. Switch to optional LLM narrative mode if an API key is present and show that the report still cites only structured evidence.
9. Scroll to the audit trail and confirm a local audit entry was recorded.
10. Export the report as Markdown, JSON, and PDF from the right-side judge report panel.

## Recommended Talk Track

- Aleens does not start from an LLM. It starts from telemetry normalization.
- The product is not a black-box classifier. The core triage decision is deterministic and inspectable.
- Every claim in the brief is backed by one or more deterministic findings.
- The risk score is reproducible and documented in `RULES.md`.
- The benchmark pack is not synthetic: it runs exact upstream OTRF/Mordor fixtures that are bundled with provenance and hashes.
- Guardrails are applied before any optional narrative rendering.
- If no API key exists, the product still works in deterministic template mode.

## Demo Dataset

`officeToPowerShell`

Sequence:

1. Office document launches PowerShell
2. PowerShell uses an encoded command
3. Telemetry shows LSASS access
4. PowerShell opens an outbound connection

Expected result:

- Risk: `High` or `Critical`
- Confidence: `80+`
- Rules: `DL-WIN-001`, `DL-WIN-002`, `DL-PS-001`, `DL-CR-001`, `DL-NET-001`
