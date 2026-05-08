from fastapi.testclient import TestClient

from app.main import app


def test_evaluator_reports_benchmark_dimensions() -> None:
    client = TestClient(app)
    analysis = client.post("/api/analyze", json={"datasetName": "officeToPowerShell", "reportMode": "template"})
    assert analysis.status_code == 200

    payload = analysis.json()
    evaluation = client.post(
        "/api/evaluate",
        json={"analysisId": payload["analysisId"], "datasetName": "officeToPowerShell"},
    )
    assert evaluation.status_code == 200

    result = evaluation.json()
    assert result["ruleRecallLike"] == 1.0
    assert result["techniqueRecallLike"] == 1.0
    assert result["chainOrderAligned"] is True
    assert result["exportsReady"] is True
    assert result["citationCoverage"] >= 1.0
