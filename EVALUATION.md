# Evaluation Guide

## How Judges Can Evaluate Aleens

1. Run the `officeToPowerShell` dataset.
2. Confirm the evidence board contains normalized Windows telemetry fields.
3. Confirm the expected deterministic rules fire.
4. Confirm ATT&CK mapping is visible.
5. Confirm the attack chain contains the expected stages.
6. Confirm the risk score is High or Critical and confidence exceeds 80.
7. Confirm the analyst brief references the chain and rule logic rather than vague AI commentary.
8. Confirm the brief includes inline evidence citations with `evidenceId` and `rawReference`.
9. Confirm exports succeed for Markdown, JSON, and PDF.
10. If LLM mode is enabled, confirm it still uses structured findings only and falls back safely if unavailable.
11. Confirm an audit entry is written locally.
12. Submit analyst feedback and confirm it appears as local memory context on rerun.
13. Run the **Public OTRF Fixture Pack** and confirm the aggregate benchmark score is reproducible.
14. Run `adminPowerShellInventory` and confirm Aleens can keep a suspicious-looking shell chain in low-risk, review-oriented territory.

## Test Cases

- `officeToPowerShell`
  - Expected rules: `DL-WIN-001`, `DL-WIN-002`, `DL-PS-001`, `DL-CR-001`, `DL-NET-001`
  - Expected risk: `High` or `Critical`
  - Expected chain: Initial Access -> Execution -> Defense Evasion -> Credential Access -> Command and Control

- `lsassAccessSignal`
  - Expected rule: `DL-CR-001`
  - Expected ATT&CK technique: `T1003.001`

- `suspiciousOutboundPowerShell`
  - Expected rule: `DL-NET-001`
  - Expected ATT&CK technique: `T1071`

- `adminPowerShellInventory`
  - Expected rule: `DL-WIN-002`
  - Expected ATT&CK technique: `T1059.001`
  - Expected risk: `Low`
  - Expected chain: Execution

- `otrfLsassMemoryDumpComsvcs`
  - Expected rules: `DL-CR-001`, `DL-WIN-002`
  - Expected ATT&CK techniques: `T1003.001`, `T1059.001`
  - Expected chain: Execution -> Credential Access

- `otrfRegistryRunKeyPersistence`
  - Expected rule: `DL-PER-001`
  - Expected ATT&CK technique: `T1547`
  - Expected chain: Persistence

- `otrfPowerShellCmstpOutbound`
  - Expected rule: `DL-NET-001`
  - Expected ATT&CK technique: `T1071`
  - Expected chain: Command and Control

## Evaluator Mode

`expectedFindings.json` is used to compare actual rule output against dataset expectations and return:

- matched rules
- missing rules
- unexpected rules
- rule precision-like and recall-like scores
- ATT&CK precision-like and recall-like scores
- chain-stage recall and ordering
- evidence citation coverage
- required report section coverage
- export integrity
- risk and confidence alignment
- benchmark score

`GET /api/benchmarks/public` runs the bundled upstream OTRF/Mordor fixture pack and returns:

- aggregate benchmark score
- aggregate rule recall
- aggregate ATT&CK recall
- citation coverage
- per-dataset benchmark results
- pass rate for the full public pack

## Limitations

- The hero demo chain is still a derived dataset designed for presentation clarity.
- The bundled OTRF/Mordor fixtures are exact upstream event streams, but they are still public lab telemetry rather than production enterprise captures.
- The confidence score depends on available telemetry completeness.
- Aleens currently uses deterministic scoring and optional structured LLM narration rather than a learned anomaly model.
- The current build is focused on incident triage, not response automation.
- ATT&CK mapping is technique-focused and intentionally narrow for demo clarity.
