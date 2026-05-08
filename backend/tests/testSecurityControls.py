from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config import validate_production_safe
from app.core.security import RatePolicy


def test_health_hides_model_and_sets_security_headers() -> None:
    client = TestClient(main_module.app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["llmModel"] is None
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"


def test_api_key_guards_sensitive_routes() -> None:
    original_settings = main_module.settings
    main_module.settings = replace(original_settings, api_key="unit-test-key")
    try:
        client = TestClient(main_module.app)

        unauthorized = client.get("/api/audit")
        assert unauthorized.status_code == 401

        authorized = client.get("/api/audit", headers={"X-API-Key": "unit-test-key"})
        assert authorized.status_code == 200
        payload = authorized.json()
        if payload["items"]:
            assert "providerRequestId" not in payload["items"][0]
    finally:
        main_module.settings = original_settings


def test_audit_limit_is_bounded() -> None:
    client = TestClient(main_module.app)

    assert client.get("/api/audit?limit=-1").status_code == 422
    assert client.get("/api/audit?limit=1000").status_code == 422


def test_audit_cursor_pagination_returns_metadata() -> None:
    client = TestClient(main_module.app)

    first_page = client.get("/api/audit?limit=2")
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert "items" in first_payload
    assert "hasMore" in first_payload
    assert "total" in first_payload
    assert len(first_payload["items"]) <= 2

    if first_payload["hasMore"]:
        second_page = client.get(f"/api/audit?limit=2&cursor={first_payload['nextCursor']}")
        assert second_page.status_code == 200
        second_payload = second_page.json()
        first_ids = {item["analysisId"] for item in first_payload["items"]}
        second_ids = {item["analysisId"] for item in second_payload["items"]}
        assert first_ids.isdisjoint(second_ids)


def test_upload_rejects_non_json_extension_and_invalid_event_shape() -> None:
    client = TestClient(main_module.app)

    bad_extension = client.post(
        "/api/analyze/upload",
        files={"file": ("notes.txt", b"[]", "text/plain")},
    )
    assert bad_extension.status_code == 415

    invalid_events = client.post(
        "/api/analyze/upload",
        files={"file": ("events.json", b'{"events":["bad"]}', "application/json")},
    )
    assert invalid_events.status_code == 400


def test_analyze_endpoint_is_rate_limited() -> None:
    original_settings = main_module.settings
    original_policy = main_module.analyze_rate_policy
    main_module.settings = replace(original_settings, analyze_rate_limit="2/minute")
    main_module.analyze_rate_policy = RatePolicy.parse("2/minute")
    main_module.rate_limiter.reset()
    try:
        client = TestClient(main_module.app)
        payload = {"datasetName": "officeToPowerShell", "reportMode": "template"}

        assert client.post("/api/analyze", json=payload).status_code == 200
        assert client.post("/api/analyze", json=payload).status_code == 200

        limited = client.post("/api/analyze", json=payload)
        assert limited.status_code == 429
        assert "Retry-After" in limited.headers
    finally:
        main_module.settings = original_settings
        main_module.analyze_rate_policy = original_policy
        main_module.rate_limiter.reset()


def test_production_safe_requires_api_key() -> None:
    settings = replace(main_module.settings, production_safe=True, api_key="")
    try:
        validate_production_safe(settings)
    except RuntimeError as exc:
        assert "ALEENS_API_KEY" in str(exc)
    else:
        raise AssertionError("production-safe mode should fail closed without an API key")
