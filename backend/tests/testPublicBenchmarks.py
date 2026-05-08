from fastapi.testclient import TestClient

from app.main import app


def test_public_fixture_scenarios_trigger_expected_rules() -> None:
    client = TestClient(app)
    expectations = {
        "otrfLsassMemoryDumpComsvcs": {"DL-CR-001", "DL-WIN-002"},
        "otrfRegistryRunKeyPersistence": {"DL-PER-001"},
        "otrfPowerShellCmstpOutbound": {"DL-NET-001"},
    }

    for scenario, expected_rules in expectations.items():
        response = client.post("/api/analyze", json={"scenarioName": scenario, "reportMode": "template"})
        assert response.status_code == 200
        payload = response.json()
        actual_rules = {finding["ruleId"] for finding in payload["findings"]}
        assert actual_rules == expected_rules


def test_public_benchmark_pack_endpoint_returns_aggregate_scores() -> None:
    client = TestClient(app)
    response = client.get("/api/benchmarks/public?report_mode=template")
    assert response.status_code == 200

    payload = response.json()
    assert payload["packName"] == "OTRF/Mordor Public Fixture Pack"
    assert payload["scenarioCount"] == 3
    assert payload["averageBenchmarkScore"] >= 85
    assert payload["passRate"] == 1.0
