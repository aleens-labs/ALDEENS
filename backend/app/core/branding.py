from __future__ import annotations

from pathlib import Path

APP_NAME = "Aleens"
APP_NAME_UPPER = "ALEENS"
APP_REPORT_TITLE = "Aleens Incident Report"
APP_TAGLINE = "Local-First Windows Incident Triage"
APP_CLI_TAGLINE = "Offline-ready Windows Incident Triage CLI"
APP_CLI_COMMAND = "aleens"
APP_EXPORT_PREFIX = "aleens"


def logo_path() -> Path:
    return Path(__file__).resolve().parents[3] / "frontend" / "public" / "branding" / "aleens-logo.png"
