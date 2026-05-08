from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from textwrap import shorten
from typing import Sequence

from app.core.branding import APP_CLI_COMMAND, APP_CLI_TAGLINE, APP_NAME, APP_NAME_UPPER
from app.core.models import AnalysisResult, AuditRecord, DatasetSummary

APP_TAGLINE = APP_CLI_TAGLINE
APP_HEADER_ART = [
    " █████╗ ██╗     ██████╗ ███████╗███████╗███╗   ██╗███████╗",
    "██╔══██╗██║     ██╔══██╗██╔════╝██╔════╝████╗  ██║██╔════╝",
    "███████║██║     ██║  ██║█████╗  █████╗  ██╔██╗ ██║███████╗",
    "██╔══██║██║     ██║  ██║██╔══╝  ██╔══╝  ██║╚██╗██║╚════██║",
    "██║  ██║███████╗██████╔╝███████╗███████╗██║ ╚████║███████║",
    "╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝",
]
APP_SIDE_LOGO = [
    "      ██████              ██████      ",
    "     ████████            ████████     ",
    "    ██      ██          ██      ██    ",
    "    ██      ██          ██      ██    ",
    "    ██████████  ══════  ██████████    ",
    "    ██████████          ██████████    ",
    "    ██      ██          ██      ██    ",
    "   ██        ██        ██        ██   ",
]
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_GOLD_BRIGHT = "\033[38;5;220m"
ANSI_GOLD = "\033[38;5;178m"
ANSI_GOLD_DARK = "\033[38;5;136m"
ANSI_GOLD_DEEP = "\033[38;5;94m"
ANSI_SLATE = "\033[38;5;244m"
ANSI_WHITE = "\033[97m"


def _runtime():
    import app.main as runtime

    return runtime


def _load_events_from_path(path: Path) -> list[dict[str, Any]]:
    runtime = _runtime()
    return runtime._load_event_stream(path)


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_bytes(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _banner_width() -> int:
    terminal_width = shutil.get_terminal_size(fallback=(108, 40)).columns
    return max(84, min(108, terminal_width - 2))


def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("CLICOLOR_FORCE") in {"1", "true", "TRUE"}:
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _paint(text: str, *effects: str) -> str:
    if not _supports_color() or not effects:
        return text
    return "".join(effects) + text + ANSI_RESET


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _pad_rendered(rendered: str, plain_text: str, width: int) -> str:
    return rendered + (" " * max(0, width - len(plain_text)))


def _center_plain(text: str, width: int) -> str:
    padding = max(0, (width - len(text)) // 2)
    return " " * padding + text


def _configure_console_encoding() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _print_banner(title: str, subtitle: str | None = None) -> None:
    left_width = max(len(line) for line in APP_SIDE_LOGO)
    title_width = max(len(line) for line in APP_HEADER_ART)
    minimum_right_width = 56
    width = max(_banner_width(), title_width + 4, left_width + minimum_right_width + 7)
    right_width = width - left_width - 7

    palette = [ANSI_GOLD_BRIGHT, ANSI_GOLD_BRIGHT, ANSI_GOLD, ANSI_GOLD, ANSI_GOLD_DARK, ANSI_GOLD_DARK]
    for index, line in enumerate(APP_HEADER_ART):
        color = palette[min(index, len(palette) - 1)]
        print(_paint(_center_plain(line, width), ANSI_BOLD, color))
    print("")

    info_entries = [
        ("Command", title),
        ("Context", subtitle or "Interactive security workflow"),
        ("Workspace", shorten(str(_runtime().settings.root_dir), width=44, placeholder="...")),
        ("Mode", "Offline-ready deterministic-first pipeline"),
        ("Docs", f"python -m app.cli --help | {APP_CLI_COMMAND} --help"),
        ("Export", "use --latest for the newest saved analysis"),
        ("Tagline", APP_TAGLINE),
    ]

    banner_rows: list[tuple[str, str, str]] = [("operator console", "operator console", "header"), ("-" * min(28, right_width), "-" * min(28, right_width), "divider")]
    banner_rows.extend((label, value, "field") for label, value in info_entries)
    row_count = max(len(APP_SIDE_LOGO), len(banner_rows))

    print(_paint("+" + "-" * (width - 2) + "+", ANSI_SLATE))
    for index in range(row_count):
        left_plain = APP_SIDE_LOGO[index] if index < len(APP_SIDE_LOGO) else ""
        left_rendered = _paint(left_plain.ljust(left_width), ANSI_GOLD)

        if index < len(banner_rows):
            label, value, kind = banner_rows[index]
            if kind == "header":
                plain_right = label
                rendered_right = _paint(label, ANSI_BOLD, ANSI_WHITE)
            elif kind == "divider":
                plain_right = label
                rendered_right = _paint(label, ANSI_GOLD_DARK)
            else:
                short_value = shorten(value, width=max(8, right_width - len(label) - 3), placeholder="...")
                plain_right = f"{label:<10}: {short_value}"
                rendered_right = _paint(f"{label:<10}:", ANSI_BOLD, ANSI_GOLD_BRIGHT) + " " + _paint(short_value, ANSI_WHITE)
        else:
            plain_right = ""
            rendered_right = ""

        print(
            _paint("| ", ANSI_SLATE)
            + left_rendered
            + _paint(" | ", ANSI_SLATE)
            + _pad_rendered(rendered_right, plain_right, right_width)
            + _paint(" |", ANSI_SLATE)
        )
    print(_paint("+" + "-" * (width - 2) + "+", ANSI_SLATE))
    print("")


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    separator = "  ".join("-" * widths[index] for index in range(len(headers)))
    print(header_line)
    print(separator)
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def _print_key_values(pairs: list[tuple[str, str]]) -> None:
    label_width = max(len(label) for label, _ in pairs)
    for label, value in pairs:
        print(f"{label.ljust(label_width)} : {value}")


def _print_tip(text: str) -> None:
    print("")
    print(_paint("Tip:", ANSI_BOLD, ANSI_GOLD_BRIGHT) + f" {text}")


def _latest_audit_record() -> AuditRecord | None:
    items = _runtime().conductor.audit_trail.recent(limit=1)
    return items[0] if items else None


def _resolve_analysis_id(analysis_id: str | None, latest: bool) -> str:
    if analysis_id:
        return analysis_id
    if latest:
        latest_record = _latest_audit_record()
        if latest_record:
            return latest_record.analysis_id
        raise SystemExit("No audit records are available yet, so --latest cannot be used.")
    raise SystemExit("Provide --analysis-id or use --latest.")


def _print_analysis_summary(result: AnalysisResult) -> None:
    _print_banner(
        "Analysis Complete",
        f"{result.dataset_name} | Risk {result.scores.risk_score}/100 | Confidence {result.scores.confidence_score}/100",
    )
    _print_key_values(
        [
            ("Analysis ID", result.analysis_id),
            ("Dataset", result.dataset_name),
            ("Parser Mode", result.parser_mode),
            ("Report Mode", result.report_mode),
            ("Risk", f"{result.scores.risk_score}/100 ({result.scores.risk_label.value})"),
            ("Confidence", f"{result.scores.confidence_score}/100"),
            ("Evidence", str(result.evidence_count)),
            ("MITRE", str(result.mitre_count)),
            ("Saved JSON", str(_runtime().settings.analyses_dir / f"{result.analysis_id}.json")),
        ]
    )
    _print_tip(
        f'Export the latest PDF with: python -m app.cli export --analysis-id {result.analysis_id} --format pdf'
    )


def _dataset_rows(items: list[DatasetSummary]) -> list[list[str]]:
    rows: list[list[str]] = []
    for item in items:
        rows.append(
            [
                item.dataset_id,
                shorten(item.title, width=34, placeholder="..."),
                ",".join(item.techniques[:4]),
                item.collection_type,
            ]
        )
    return rows


def _audit_rows(items: list[AuditRecord]) -> list[list[str]]:
    rows: list[list[str]] = []
    for item in items:
        rows.append(
            [
                item.timestamp.replace("T", " ").replace("+00:00", " UTC"),
                str(item.risk_score),
                str(item.confidence_score),
                item.report_mode,
                shorten(item.dataset_name, width=24, placeholder="..."),
                item.analysis_id,
            ]
        )
    return rows


def _cmd_datasets(args: argparse.Namespace) -> int:
    runtime = _runtime()
    datasets = runtime._dataset_payload()
    if args.json:
        print(json.dumps([item.model_dump(mode="json", by_alias=True) for item in datasets], indent=2))
        return 0

    _print_banner("Dataset Library", "Reference incident datasets and public upstream fixtures")
    _print_table(
        ["Dataset ID", "Title", "Techniques", "Source Type"],
        _dataset_rows(datasets),
    )
    _print_tip("Run an analysis with: python -m app.cli analyze --dataset officeToPowerShell --report-mode template")
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    runtime = _runtime()

    if args.dataset:
        dataset_name = args.dataset
        raw_events = runtime._read_dataset(args.dataset)
        parser_mode = "reference-dataset"
    else:
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            raise SystemExit(f"Input file was not found: {input_path}")
        dataset_name = args.dataset_name or input_path.stem
        raw_events = runtime.validate_uploaded_events(_load_events_from_path(input_path))
        parser_mode = "cli-upload"

    report_mode = args.report_mode or runtime.settings.default_report_mode
    result = runtime.conductor.analyze(dataset_name, raw_events, parser_mode, report_mode)

    if args.json_out:
        _write_text(Path(args.json_out).expanduser(), runtime.reporter.export_json(result))
    if args.markdown_out:
        _write_text(Path(args.markdown_out).expanduser(), runtime.reporter.export_markdown(result))
    if args.pdf_out:
        _write_bytes(Path(args.pdf_out).expanduser(), runtime.generate_pdf(result))

    if args.print_json:
        print(runtime.reporter.export_json(result))
    else:
        _print_analysis_summary(result)
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    runtime = _runtime()
    try:
        resolved_analysis_id = _resolve_analysis_id(args.analysis_id, args.latest)
        result = runtime.conductor.load_analysis(resolved_analysis_id)
    except FileNotFoundError as exc:
        raise SystemExit(f"Analysis not found: {resolved_analysis_id}") from exc

    safe_dataset = result.dataset_name.replace(" ", "-")
    ext = "md" if args.format == "markdown" else args.format
    default_path = runtime.settings.exports_dir / f"{APP_CLI_COMMAND}-{safe_dataset}-{result.analysis_id[:8]}.{ext}"
    output_path = Path(args.output).expanduser() if args.output else default_path

    if args.format == "json":
        _write_text(output_path, runtime.reporter.export_json(result))
    elif args.format == "markdown":
        _write_text(output_path, runtime.reporter.export_markdown(result))
    elif args.format == "pdf":
        _write_bytes(output_path, runtime.generate_pdf(result))
    else:
        raise SystemExit("Unsupported export format.")

    _print_banner("Export Complete", f"{result.dataset_name} | {args.format.upper()} report")
    _print_key_values(
        [
            ("Analysis ID", result.analysis_id),
            ("Format", args.format),
            ("Output", str(output_path.resolve())),
        ]
    )
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    runtime = _runtime()
    page = runtime.conductor.audit_trail.page(limit=args.limit, cursor=args.cursor)
    if args.json:
        payload = {
            "items": [
                item.model_dump(mode="json", by_alias=True, exclude={"provider_request_id"})
                for item in page["items"]
            ],
            "nextCursor": page["nextCursor"],
            "hasMore": page["hasMore"],
            "total": page["total"],
            "limit": page["limit"],
        }
        print(json.dumps(payload, indent=2))
        return 0

    items = page["items"]
    _print_banner("Audit Trail", f"Showing up to {args.limit} records from local history")
    if not items:
        print("No audit records found.")
        return 0

    _print_table(
        ["Timestamp", "Risk", "Conf", "Mode", "Dataset", "Analysis ID"],
        _audit_rows(items),
    )
    print("")
    _print_key_values(
        [
            ("Records shown", str(len(items))),
            ("Total records", str(page["total"])),
            ("Has more", str(page["hasMore"]).lower()),
            ("Next cursor", str(page["nextCursor"])),
        ]
    )
    if items:
        _print_tip(
            f"Export the newest record with: python -m app.cli export --analysis-id {items[0].analysis_id} --format pdf"
        )
    return 0


def _cmd_benchmarks_public(args: argparse.Namespace) -> int:
    runtime = _runtime()
    payload = runtime._public_benchmark_pack(args.report_mode)
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    _print_banner("Public Benchmark Pack", payload["sourceName"])
    _print_key_values(
        [
            ("Pack", payload["packName"]),
            ("Source", payload["sourceName"]),
            ("Report Mode", payload["reportMode"]),
            ("Avg Score", str(payload["averageBenchmarkScore"])),
            ("Avg Rule Recall", str(payload["averageRuleRecall"])),
            ("Avg ATT&CK Recall", str(payload["averageTechniqueRecall"])),
            ("Pass Rate", str(payload["passRate"])),
        ]
    )
    print("")

    rows = [
        [
            item["dataset"],
            str(item["benchmarkScore"]),
            str(item["ruleRecallLike"]),
            str(item["techniqueRecallLike"]),
            "yes" if item["chainOrderAligned"] else "no",
        ]
        for item in payload["datasets"]
    ]
    _print_table(["Dataset", "Score", "Rule Recall", "ATT&CK Recall", "Chain OK"], rows)
    _print_tip("Use --json if you want the raw benchmark payload for automation.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_CLI_COMMAND,
        description=f"Local-first CLI for {APP_NAME} incident triage workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    datasets_parser = subparsers.add_parser("datasets", help="List reference incident datasets.")
    datasets_parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a table.")
    datasets_parser.set_defaults(func=_cmd_datasets)

    analyze_parser = subparsers.add_parser("analyze", help="Run an analysis from a dataset or local file.")
    source_group = analyze_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--dataset", help="Dataset ID from the reference dataset library.")
    source_group.add_argument("--input", help="Path to a JSON or JSONL event file.")
    analyze_parser.add_argument("--dataset-name", help="Override the dataset name when using --input.")
    analyze_parser.add_argument(
        "--report-mode",
        choices=["template", "llm"],
        help="Override the default report mode.",
    )
    analyze_parser.add_argument("--json-out", help="Write the full analysis JSON to this path.")
    analyze_parser.add_argument("--markdown-out", help="Write the analyst brief markdown to this path.")
    analyze_parser.add_argument("--pdf-out", help="Write the rendered PDF report to this path.")
    analyze_parser.add_argument("--print-json", action="store_true", help="Print the full analysis JSON to stdout.")
    analyze_parser.set_defaults(func=_cmd_analyze)

    export_parser = subparsers.add_parser("export", help="Export a saved analysis to JSON, markdown, or PDF.")
    export_group = export_parser.add_mutually_exclusive_group(required=True)
    export_group.add_argument("--analysis-id", help="Saved analysis ID.")
    export_group.add_argument("--latest", action="store_true", help="Export the most recent analysis from the audit trail.")
    export_parser.add_argument(
        "--format",
        required=True,
        choices=["json", "markdown", "pdf"],
        help="Output format.",
    )
    export_parser.add_argument("--output", help="Destination file path. Defaults to backend/runtime/exports.")
    export_parser.set_defaults(func=_cmd_export)

    audit_parser = subparsers.add_parser("audit", help="Inspect the local audit trail.")
    audit_parser.add_argument("--limit", type=int, default=20, help="Maximum records to show.")
    audit_parser.add_argument("--cursor", help="Cursor offset from a previous page.")
    audit_parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a table.")
    audit_parser.set_defaults(func=_cmd_audit)

    benchmarks_parser = subparsers.add_parser("benchmarks", help="Run benchmark-oriented CLI workflows.")
    benchmark_subparsers = benchmarks_parser.add_subparsers(dest="benchmark_command", required=True)
    public_parser = benchmark_subparsers.add_parser("public", help="Run the bundled public upstream benchmark pack.")
    public_parser.add_argument(
        "--report-mode",
        choices=["template", "llm"],
        default=None,
        help="Override the report mode for the benchmark run.",
    )
    public_parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a table.")
    public_parser.set_defaults(func=_cmd_benchmarks_public)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
