from __future__ import annotations

from pathlib import Path

APP_NAME = "Aldeens"
APP_NAME_UPPER = "ALDEENS"
APP_REPORT_TITLE = "Aldeens Incident Report"
APP_TAGLINE = "Local-First Windows Incident Triage"
APP_CLI_TAGLINE = "Offline-ready Windows Incident Triage CLI"
APP_CLI_COMMAND = "aldeens"
APP_EXPORT_PREFIX = "aldeens"


def logo_path() -> Path:
    return Path(__file__).resolve().parents[3] / "frontend" / "public" / "branding" / "aldeens-logo.png"
