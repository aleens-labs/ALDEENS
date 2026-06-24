# Changelog

All notable changes to Aldeens are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Reframed public-facing documentation for production and community use.
- MITRE ATT&CK detection-coverage table in the README.
- Concrete telemetry input schema in the README.
- GitHub Actions CI running backend tests and the frontend build.
- `CONTRIBUTING.md` and `ROADMAP.md`.

## [0.1.0]

### Added
- Local-first Windows incident triage pipeline.
- Deterministic detection rules with traceable rule IDs (`DL-WIN-001` ... `DL-PER-002`) mapped to MITRE ATT&CK.
- Attack-chain reconstruction from timestamped evidence.
- Reproducible risk and confidence scoring.
- OTRF / Mordor public benchmark pack with provenance and hashes.
- Local audit trail and analyst feedback memory.
- PDF, Markdown, and JSON report exports.
- Optional, guardrailed LLM narrative layer.
- FastAPI backend, React + Vite frontend, and a terminal-first CLI.
- Production-safe mode with fail-closed API-key enforcement, rate limiting, and bounded pagination.

[Unreleased]: https://github.com/aleens-labs/ALDEENS/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/aleens-labs/ALDEENS/releases/tag/v0.1.0
