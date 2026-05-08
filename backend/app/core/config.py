from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.branding import APP_NAME

LEGACY_ENV_PREFIX = "".join(["DEFENDER", "LENS"])


def _load_dotenv(env_path: Path) -> None:
    """Minimal .env loader — no external dependency required."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    root_dir: Path
    backend_dir: Path
    rules_dir: Path
    datasets_dir: Path
    reports_dir: Path
    runtime_dir: Path
    analyses_dir: Path
    exports_dir: Path
    audit_log_path: Path
    feedback_db_path: Path
    memory_dir: Path
    default_report_mode: str
    allow_llm: bool
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_timeout_seconds: int
    cors_origins: list[str]
    max_upload_bytes: int
    api_key: str
    analyze_rate_limit: str
    upload_rate_limit: str
    audit_limit_max: int
    production_safe: bool


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip() != "":
            return value.strip()
    return default


def _env_flag_any(names: tuple[str, ...], default: bool = False) -> bool:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _legacy_env(name: str) -> str:
    return f"{LEGACY_ENV_PREFIX}_{name}"


def validate_production_safe(settings: Settings) -> None:
    if settings.production_safe and not settings.api_key:
        raise RuntimeError(
            "ALEENS_PRODUCTION_SAFE is enabled but ALEENS_API_KEY is not configured."
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    root_dir = Path(__file__).resolve().parents[3]
    backend_dir = root_dir / "backend"

    # backend/.env takes priority; root .env fills any remaining gaps
    _load_dotenv(backend_dir / ".env")
    _load_dotenv(root_dir / ".env")

    runtime_dir = backend_dir / "runtime"
    analyses_dir = runtime_dir / "analyses"
    exports_dir = runtime_dir / "exports"
    memory_dir = root_dir / "memory"

    runtime_dir.mkdir(parents=True, exist_ok=True)
    analyses_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)

    origin_env = _env_first(
        "ALEENS_CORS_ORIGINS",
        _legacy_env("CORS_ORIGINS"),
        default="http://localhost:5173,http://127.0.0.1:5173",
    )
    cors_origins = [origin.strip() for origin in origin_env.split(",") if origin.strip()]
    if "*" in cors_origins and _env_first("ALEENS_ALLOW_WILDCARD_CORS", _legacy_env("ALLOW_WILDCARD_CORS"), default="false").lower() != "true":
        cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Accept either OPENAI_API_KEY or OPENROUTER_API_KEY
    llm_api_key = (
        os.getenv("OPENROUTER_API_KEY", "")
        or os.getenv("OPENAI_API_KEY", "")
    ).strip()

    llm_base_url = os.getenv(
        "LLM_BASE_URL",
        "https://openrouter.ai/api/v1" if llm_api_key.startswith("sk-or-") else "https://api.openai.com/v1",
    ).strip()

    report_mode = _env_first("ALEENS_REPORT_MODE", _legacy_env("REPORT_MODE"), default="template").lower()
    default_model = "openai/gpt-4o-mini" if "openrouter" in llm_base_url else "gpt-4o-mini"
    llm_model = (_env_first("ALEENS_LLM_MODEL", _legacy_env("LLM_MODEL")) or default_model)

    return Settings(
        app_name=APP_NAME,
        api_prefix="/api",
        root_dir=root_dir,
        backend_dir=backend_dir,
        rules_dir=backend_dir / "rules",
        datasets_dir=backend_dir / "datasets",
        reports_dir=backend_dir / "reports",
        runtime_dir=runtime_dir,
        analyses_dir=analyses_dir,
        exports_dir=exports_dir,
        audit_log_path=runtime_dir / "audit.jsonl",
        feedback_db_path=runtime_dir / "feedback.sqlite3",
        memory_dir=memory_dir,
        default_report_mode=report_mode if report_mode in {"template", "llm"} else "template",
        allow_llm=bool(llm_api_key),
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_timeout_seconds=int(_env_first("ALEENS_LLM_TIMEOUT_SECONDS", _legacy_env("LLM_TIMEOUT_SECONDS"), default="60")),
        cors_origins=cors_origins,
        max_upload_bytes=int(_env_first("ALEENS_MAX_UPLOAD_BYTES", _legacy_env("MAX_UPLOAD_BYTES"), default=str(2 * 1024 * 1024))),
        api_key=_env_first("ALEENS_API_KEY", _legacy_env("API_KEY")),
        analyze_rate_limit=_env_first("ALEENS_ANALYZE_RATE_LIMIT", _legacy_env("ANALYZE_RATE_LIMIT"), default="10/minute"),
        upload_rate_limit=_env_first("ALEENS_UPLOAD_RATE_LIMIT", _legacy_env("UPLOAD_RATE_LIMIT"), default="5/minute"),
        audit_limit_max=int(_env_first("ALEENS_AUDIT_LIMIT_MAX", _legacy_env("AUDIT_LIMIT_MAX"), default="100")),
        production_safe=_env_flag_any(("ALEENS_PRODUCTION_SAFE", _legacy_env("PRODUCTION_SAFE")), False),
    )
