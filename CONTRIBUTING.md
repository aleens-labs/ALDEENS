# Contributing to Aldeens

Thanks for your interest in improving Aldeens. This project is a defensive security research and incident-triage tool, and contributions that make detections more accurate, more transparent, and easier to adopt are very welcome.

## Ways to Contribute

- **New detection rules** mapped to MITRE ATT&CK techniques.
- **Dataset fixtures** (ideally from upstream OTRF / Mordor) with provenance and hashes.
- **Telemetry parsers** for additional Windows / Sysmon / Defender export formats.
- **Documentation** improvements, examples, and walkthroughs.
- **Bug reports** and reproducible test cases.

We do **not** accept contributions that add offensive tooling: exploit generation, malware, credential theft, persistence guidance, or attacker automation. Aldeens stays strictly defensive.

## Development Setup

```bash
# Backend
cd backend
python -m pip install -e .[dev]
python -m pytest

# Frontend
cd frontend
npm install
npm run build
```

## Adding a Detection Rule

1. Implement the rule in the backend rule engine with a stable, unique rule ID (e.g. `DL-XXX-00N`).
2. Map it to the relevant MITRE ATT&CK technique and tactic.
3. Give it an explicit score and confidence contribution.
4. Add a fixture and the expected findings so the evaluator can validate it.
5. Document the rule in `RULES.md` and add it to the coverage table in `README.md`.
6. Run `python -m pytest` and the public benchmark pack before opening a PR.

Every rule must be **deterministic and traceable**: it should point back to concrete evidence, never to opaque heuristics.

## Pull Request Guidelines

- Keep PRs focused and reasonably small.
- Describe what changed and why, and link any related issue.
- Make sure CI passes (backend tests + frontend build).
- Do **not** commit secrets, `.env` files, runtime databases, or generated incident data.
- For new behavior, include or update tests.

## Commit Style

We loosely follow Conventional Commits, for example:

- `feat(rules): add scheduled-task persistence detection`
- `fix(parser): handle missing parent_process_name`
- `docs(readme): clarify telemetry schema`

## Reporting Security Issues

Please do **not** open public issues for vulnerabilities. Follow the process in [`SECURITY.md`](SECURITY.md) instead.

## Code of Conduct

Be respectful and constructive. We want Aldeens to be a welcoming project for blue teamers, researchers, and newcomers alike.
