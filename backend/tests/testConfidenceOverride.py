from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_confidence_override_roundtrip() -> None:
    client = TestClient(app)
    analysis_id = f"override-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/api/feedback/confidence-override",
        json={
            "analysisId": analysis_id,
            "datasetName": "officeToPowerShell",
            "analystConfidence": 84,
            "overrideNote": "Analyst confirmed strong corroboration from host logs.",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "saved", "analystConfidence": 84}

    lookup = client.get(f"/api/feedback/confidence-override/{analysis_id}")
    assert lookup.status_code == 200
    payload = lookup.json()
    assert payload["analystConfidence"] == 84
    assert payload["overrideNote"] == "Analyst confirmed strong corroboration from host logs."
    assert payload["createdAt"]
