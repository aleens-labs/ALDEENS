# Aleens Backend

FastAPI backend for deterministic Windows incident triage.

The primary project documentation lives in the repository root `README.md`.

## Production-Safe Reminder

For any shared or internet-reachable deployment:

- set `ALEENS_API_KEY`
- set `ALEENS_PRODUCTION_SAFE=true`
- restrict `ALEENS_CORS_ORIGINS`
- do not commit `backend/.env`

## CLI

Aleens also ships with a local CLI for common research and triage flows.
Use `python -m app.cli ...` if your current shell has not yet picked up the `aleens` console-script shim.

```powershell
cd backend
python -m pip install -e .[dev]
python -m app.cli datasets
python -m app.cli analyze --dataset officeToPowerShell --report-mode template
python -m app.cli audit --limit 10
python -m app.cli export --latest --format markdown
python -m app.cli benchmarks public
```

For ad hoc telemetry:

```powershell
python -m app.cli analyze --input C:\path\to\events.json --dataset-name incident-001 --pdf-out C:\path\to\incident-001.pdf
```

If you already know the saved analysis ID:

```powershell
python -m app.cli export --analysis-id b6091f10eb9b --format pdf
```
