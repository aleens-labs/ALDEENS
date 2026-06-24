# Aldeens Roadmap

This roadmap describes the direction of the project. It is intentionally public so contributors and adopters can see where Aldeens is going. Items are not strict commitments and may shift based on feedback.

## Now (v0.1.x)

- Deterministic rule engine with traceable rule IDs and ATT&CK mapping.
- Attack-chain reconstruction, risk and confidence scoring.
- OTRF / Mordor benchmark pack with provenance and hashes.
- Local audit trail and analyst memory.
- PDF / Markdown / JSON report exports.
- Optional, guardrailed LLM narrative layer.

## Next

- **Broader detection coverage**: expand beyond the current seven rules toward more Execution, Defense Evasion, Credential Access, Persistence, and Lateral Movement techniques.
- **More native parsers**: direct ingestion of Windows Security/Sysmon EVTX-exported JSON and common EDR export shapes, reducing manual conversion.
- **Published benchmark results**: per-release tables of rule recall, ATT&CK recall, and false-positive characteristics on the public fixture pack.
- **Rule pack format**: a documented, versioned schema so the community can contribute rule packs.

## Later

- Sigma rule import/export interoperability.
- Configurable scoring profiles for different environments.
- Pluggable enrichment (e.g. local threat-intel lookups) that remains offline-friendly.
- Optional containerized single-binary distribution for analysts.

## Explicitly Out of Scope

Aldeens stays strictly defensive. The project will **not** add exploit generation, malware development, credential theft, persistence guidance, autonomous response, or any offensive automation.

## Contributing to the Roadmap

Have a use case or detection you want to see? Open an issue and start the discussion. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
