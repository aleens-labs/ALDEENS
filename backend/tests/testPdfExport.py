from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import _read_dataset, app, conductor, settings


def test_pdf_export_returns_pdf_document() -> None:
    result = conductor.analyze(
        "officeToPowerShell",
        _read_dataset("officeToPowerShell"),
        "test-pdf-export",
        settings.default_report_mode,
    )

    client = TestClient(app)
    response = client.get(f"/api/exports/{result.analysis_id}/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert "aleens-officeToPowerShell-" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
