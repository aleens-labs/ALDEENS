from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from app import cli
from app.main import _read_dataset, conductor, settings


def _run_cli(args: list[str]) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = cli.main(args)
    assert exit_code == 0
    return buffer.getvalue()


def test_cli_datasets_lists_bundled_registry() -> None:
    output = _run_cli(["datasets"])
    assert "operator console" in output
    assert "Dataset Library" in output
    assert "officeToPowerShell" in output


def test_cli_analyze_dataset_prints_summary() -> None:
    output = _run_cli(["analyze", "--dataset", "officeToPowerShell", "--report-mode", "template"])
    assert "Analysis Complete" in output
    assert "officeToPowerShell" in output
    assert "Critical" in output


def test_cli_export_markdown_writes_file(tmp_path: Path) -> None:
    result = conductor.analyze(
        "officeToPowerShell",
        _read_dataset("officeToPowerShell"),
        "test-cli-export",
        settings.default_report_mode,
    )
    target = tmp_path / "report.md"

    output = _run_cli(
        [
            "export",
            "--analysis-id",
            result.analysis_id,
            "--format",
            "markdown",
            "--output",
            str(target),
        ]
    )

    assert "Export Complete" in output
    assert target.exists()
    assert "Aleens Incident Report" in target.read_text(encoding="utf-8")


def test_cli_audit_prints_page_summary() -> None:
    output = _run_cli(["audit", "--limit", "1"])
    assert "Audit Trail" in output
    assert "Records shown" in output


def test_cli_export_latest_writes_file(tmp_path: Path) -> None:
    conductor.analyze(
        "officeToPowerShell",
        _read_dataset("officeToPowerShell"),
        "test-cli-export-latest",
        settings.default_report_mode,
    )
    target = tmp_path / "latest.json"

    output = _run_cli(
        [
            "export",
            "--latest",
            "--format",
            "json",
            "--output",
            str(target),
        ]
    )

    assert "Export Complete" in output
    assert target.exists()
    assert '"datasetName": "officeToPowerShell"' in target.read_text(encoding="utf-8")
