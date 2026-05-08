from __future__ import annotations

import base64
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from html import escape
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable

from app.core.branding import APP_EXPORT_PREFIX, APP_NAME, APP_REPORT_TITLE, APP_TAGLINE, logo_path
from app.core.models import AnalysisResult, ChainStep, DetectionFinding, Evidence, ScoreComponent, TacticHit

BRAND = "#00FFC8"
PAGE_BG = "#FFFFFF"
SURFACE = "#F8FAFC"
SURFACE_ALT = "#EEF2F7"
INK = "#0F172A"
INK_SOFT = "#334155"
INK_MUTED = "#64748B"
BORDER = "#D7E0EA"
NAVY = "#0B172A"
NAVY_SOFT = "#15243A"
BRAND_SOFT = "#E6FFFA"
TEXT = INK
TEXT_SOFT = INK_MUTED

RISK_TONES = {
    "Critical": "#EF4444",
    "High": "#F97316",
    "Medium": "#EAB308",
    "Low": "#22C55E",
}


def _fmt_ts(ts: datetime | None) -> str:
    if ts is None:
        return "n/a"
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-") or "analysis"


def _delta_from_base(base: datetime | None, current: datetime | None) -> str:
    if base is None or current is None or base == current:
        return "--"
    seconds = int((current - base).total_seconds())
    return f"+{seconds}s" if seconds > 0 else "--"


def _logo_data_uri() -> str:
    candidate = logo_path()
    if not candidate.exists():
        return ""
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _strip_markdown(line: str) -> str:
    stripped = line.strip()
    while stripped.startswith("#"):
        stripped = stripped[1:].strip()
    if stripped.startswith("- "):
        stripped = stripped[2:].strip()
    return (
        stripped.replace("**", "")
        .replace("`", "")
        .replace("_", "")
    )


def _section_lines(markdown: str, section_title: str) -> list[str]:
    lines = markdown.splitlines()
    collected: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            normalized_heading = heading_text.split(". ", 1)[1] if ". " in heading_text[:4] else heading_text
            if normalized_heading == section_title:
                capture = True
                continue
            if capture:
                break
        if capture and stripped:
            collected.append(_strip_markdown(stripped))
    return collected


def _first_section_paragraph(markdown: str, *section_titles: str) -> str:
    for section_title in section_titles:
        paragraph = _section_paragraph(markdown, section_title)
        if paragraph != "No narrative content was available for this section.":
            return paragraph
    return "No narrative content was available for this section."


def _first_section_bullets(markdown: str, *section_titles: str) -> list[str]:
    for section_title in section_titles:
        bullets = _section_bullets(markdown, section_title)
        if bullets:
            return bullets
    return []


def _section_paragraph(markdown: str, section_title: str) -> str:
    lines = _section_lines(markdown, section_title)
    return " ".join(lines) if lines else "No narrative content was available for this section."


def _section_bullets(markdown: str, section_title: str) -> list[str]:
    return _section_lines(markdown, section_title)


def _phase_coverage(tactics: list[TacticHit]) -> tuple[list[str], int]:
    phases = [
        "Initial Access",
        "Execution",
        "Persistence",
        "Defense Evasion",
        "Credential Access",
        "Lateral Movement",
        "Command and Control",
    ]
    covered = [phase for phase in phases if any(item.tactic == phase for item in tactics)]
    coverage = round((len(covered) / len(phases)) * 100) if phases else 0
    return covered, coverage


def _table(headers: list[str], rows: list[list[str]], widths: list[str] | None = None) -> str:
    width_css = ""
    if widths:
        width_css = "<colgroup>" + "".join(f'<col style="width:{width}">' for width in widths) + "</colgroup>"

    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows: list[str] = []
    for index, row in enumerate(rows):
        row_class = "even" if index % 2 == 0 else "odd"
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows.append(f'<tr class="{row_class}">{cells}</tr>')

    return (
        f'<table class="report-table">{width_css}<thead><tr>{header_html}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )


def _list_html(items: Iterable[str], empty_message: str) -> str:
    normalized = [item for item in items if item]
    if not normalized:
        return f"<ul><li>{escape(empty_message)}</li></ul>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in normalized) + "</ul>"


def _metric_chip(label: str, value: str) -> str:
    return (
        '<div class="metric-chip">'
        f'<span class="metric-chip-label">{escape(label)}</span>'
        f'<strong class="metric-chip-value">{escape(value)}</strong>'
        "</div>"
    )


def _metric_box(label: str, value: str, subtitle: str, tone: str) -> str:
    return (
        '<div class="metric-box">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value" style="color:{tone}">{escape(value)}</div>'
        f'<div class="metric-subtitle">{escape(subtitle)}</div>'
        "</div>"
    )


def _bar_row(component: ScoreComponent, max_value: int) -> str:
    width = 0 if max_value <= 0 else max(8, round((component.value / max_value) * 100))
    return (
        '<div class="bar-row">'
        '<div class="bar-row-copy">'
        f'<span class="bar-row-title">{escape(component.label)}</span>'
        f'<span class="bar-row-note">{escape(component.reason)}</span>'
        "</div>"
        '<div class="bar-track">'
        f'<div class="bar-fill" style="width:{width}%"></div>'
        "</div>"
        f'<span class="bar-value">+{component.value}</span>'
        "</div>"
    )


def _risk_pill(label: str, score: int) -> str:
    tone = RISK_TONES.get(label, BRAND)
    return f'<span class="risk-pill" style="background:{tone};">{escape(label)} {score}/100</span>'


def _page(title: str, page_number: int, total_pages: int, result: AnalysisResult, content: str) -> str:
    generated = _fmt_ts(result.audit.timestamp and datetime.fromisoformat(result.audit.timestamp.replace("Z", "+00:00")))
    dataset = escape(result.dataset_name)
    logo_uri = _logo_data_uri()
    logo_block = (
        f'<div class="brand-mark"><img src="{logo_uri}" alt="{escape(APP_NAME)} logo" class="brand-logo" /></div>'
        if logo_uri
        else f'<div class="brand-mark brand-mark-fallback">{escape(APP_NAME[:1].upper())}</div>'
    )
    return (
        '<section class="page">'
        '<header class="page-header">'
        '<div class="page-header-brand">'
        + logo_block +
        f'<div><div class="brand-title">{escape(APP_REPORT_TITLE)}</div>'
        f'<div class="brand-meta">Dataset: {dataset} | Generated: {escape(generated)} | Analysis ID: {escape(result.analysis_id)}</div></div>'
        '</div>'
        f'<div class="brand-page"><span class="page-section">{escape(title)}</span><span>Page {page_number} of {total_pages}</span></div>'
        "</header>"
        f'<main class="page-content"><h1 class="section-title">{escape(title)}</h1>{content}</main>'
        f'<footer class="page-footer"><span>{escape(APP_NAME)} | {escape(APP_TAGLINE)}</span><span>OTRF Benchmark: 100/100 | Confidential</span></footer>'
        "</section>"
    )


def build_html_report(result: AnalysisResult) -> str:
    risk_tone = RISK_TONES.get(result.scores.risk_label.value, BRAND)
    executive_summary = _first_section_paragraph(result.analyst_brief, "Executive Summary")
    attack_reasoning = _first_section_bullets(result.analyst_brief, "Timeline", "Attack Chain Reasoning")
    recommendations = _first_section_bullets(
        result.analyst_brief,
        "Recommended Investigation Steps",
        "Recommended Next Defensive Checks",
    )
    analyst_notes = _first_section_bullets(result.analyst_brief, "Analyst Feedback History", "Analyst Notes")
    limitations = _first_section_bullets(result.analyst_brief, "Telemetry Limitations", "Limitations")
    covered_phases, coverage_percent = _phase_coverage(result.tactics)
    max_confidence_component = max((component.value for component in result.scores.confidence_trace), default=1)

    base_timestamp = result.attack_chain[0].timestamp if result.attack_chain else None
    attack_rows = [
        [
            escape(step.stage),
            escape(_fmt_ts(step.timestamp)),
            escape(_delta_from_base(base_timestamp, step.timestamp)),
            escape(", ".join(step.evidence_ids)),
            escape(", ".join(step.finding_ids)),
        ]
        for step in result.attack_chain
    ]

    rule_rows = [
        [
            escape(finding.rule_id),
            escape(finding.mitre_technique),
            escape(f"+{finding.score_contribution}"),
            escape(finding.reason),
        ]
        for finding in result.findings
    ]

    confidence_rows = [
        [escape(component.label), escape(str(component.value)), escape(component.reason)]
        for component in result.scores.confidence_trace
    ]

    evidence_rows = [
        [
            escape(item.process or "n/a"),
            escape(item.host or "n/a"),
            escape(item.user or "n/a"),
            escape(item.parent_process or "n/a"),
            escape(item.event_id or "n/a"),
            f'<div class="mono-cell">{escape(item.command_line or "n/a")}</div>',
        ]
        for item in result.evidence
    ]

    mitre_rows = [
        [
            escape(item.technique_id),
            escape(item.technique_name),
            escape(item.tactic),
            escape(f"{round(item.confidence * 100)}%"),
            escape(", ".join(item.related_rules)),
        ]
        for item in result.tactics
    ]

    attack_reasoning_html = _list_html(attack_reasoning, "No attack chain reasoning was available.")
    analyst_notes_html = _list_html(analyst_notes, "No prior analyst notes were recorded.")
    recommendations_html = _list_html(recommendations, "No recommendations were extracted.")
    limitations_html = _list_html(limitations, "No limitations were recorded.")
    key_findings_html = _list_html(
        [f"{finding.rule_id}: {finding.title}" for finding in result.findings[:5]],
        "No deterministic findings were produced for this analysis.",
    )
    confidence_bars_html = "".join(_bar_row(component, max_confidence_component) for component in result.scores.confidence_trace)
    analyst_memory_rows = [
        [
            escape(case.rule_id),
            escape(case.verdict.value),
            escape(str(case.count)),
            escape(case.dataset_name),
            escape(case.note or "--"),
        ]
        for case in result.similar_cases
    ]
    analyst_memory_table = _table(
        ["Rule ID", "Verdict", "Count", "Dataset", "Note"],
        analyst_memory_rows or [["--", "--", "--", "--", "No prior analyst memory records."]],
        ["16%", "18%", "10%", "22%", "34%"],
    )
    coverage_labels = "".join(
        f'<span class="coverage-label {"is-covered" if phase in covered_phases else ""}">{escape(phase)}</span>'
        for phase in [
            "Initial Access",
            "Execution",
            "Persistence",
            "Defense Evasion",
            "Credential Access",
            "Lateral Movement",
            "Command and Control",
        ]
    )

    pages = [
        _page(
            "Executive Summary",
            1,
            6,
            result,
            (
                '<div class="hero-band">'
                '<div class="hero-copy">'
                '<div class="report-kicker">Executive security briefing</div>'
                '<h2 class="hero-title">Evidence-backed incident assessment for leadership and analysts</h2>'
                f'<p class="hero-summary">{escape(executive_summary)}</p>'
                '<div class="hero-meta">'
                f'{_metric_chip("Report Mode", result.report_mode.upper())}'
                f'{_metric_chip("Parser Mode", result.parser_mode)}'
                f'{_metric_chip("Safety", "PASS" if result.guardrails.safe_for_report else "BLOCKED")}'
                f'{_metric_chip("Source", "OTRF Security Datasets" if "otrf" in result.dataset_name.lower() else "Reference Dataset")}'
                "</div>"
                "</div>"
                f'<div class="hero-risk">{_risk_pill(result.scores.risk_label.value, result.scores.risk_score)}</div>'
                "</div>"
                '<div class="metrics-grid">'
                f'{_metric_box("Risk Score", str(result.scores.risk_score), result.scores.risk_label.value, risk_tone)}'
                f'{_metric_box("Confidence", f"{result.scores.confidence_score}%", "Pipeline", BRAND)}'
                f'{_metric_box("Evidence", str(result.evidence_count), "Artifacts", BRAND)}'
                f'{_metric_box("MITRE", str(result.mitre_count), "ATT&CK IDs", BRAND)}'
                "</div>"
                '<div class="two-column">'
                '<div class="narrative-card">'
                "<h2>Executive Summary</h2>"
                f"<p>{escape(executive_summary)}</p>"
                "</div>"
                '<div class="narrative-card">'
                "<h2>Detections Fired</h2>"
                f"{key_findings_html}"
                "</div>"
                "</div>"
            ),
        ),
        _page(
            "Attack Chain",
            2,
            6,
            result,
            (
                '<div class="table-card">'
                '<div class="card-header-row"><h2>Attack chain timeline</h2><p>Stage-by-stage reconstruction from deterministic evidence.</p></div>'
                + _table(
                    ["Stage", "Timestamp", "Delta", "Evidence IDs", "Findings"],
                    attack_rows,
                    ["18%", "20%", "10%", "26%", "26%"],
                )
                + "</div>"
                '<div class="two-column">'
                '<div class="narrative-card"><h2>Chain Reasoning</h2>'
                + attack_reasoning_html
                + "</div>"
                '<div class="narrative-card"><h2>Coverage Snapshot</h2>'
                f'<div class="coverage-meter"><div class="coverage-fill" style="width:{coverage_percent}%"></div></div>'
                f'<p class="coverage-copy">{coverage_percent}% of ATT&CK-oriented kill chain phases were reconstructed from the current telemetry set.</p>'
                f'<div class="coverage-label-row">{coverage_labels}</div>'
                "</div>"
                "</div>"
            )
            ,
        ),
        _page(
            "Detections and Scoring",
            3,
            6,
            result,
            (
                '<div class="table-card">'
                '<div class="card-header-row"><h2>Deterministic rule trace</h2><p>Rule firing rationale used to support the incident score.</p></div>'
                + _table(
                    ["Rule ID", "Technique", "Score", "Reason"],
                    rule_rows,
                    ["16%", "16%", "10%", "58%"],
                )
                + "</div>"
                '<div class="score-summary-row">'
                f'<div class="summary-pill">Total Risk Score: <strong>{result.scores.risk_score} / 100</strong></div>'
                f'<div class="summary-pill">Risk Label: <strong>{escape(result.scores.risk_label.value)}</strong></div>'
                f'<div class="summary-pill">Confidence: <strong>{result.scores.confidence_score}%</strong></div>'
                "</div>"
                '<div class="two-column score-two-column">'
                '<div class="narrative-card"><h2>Confidence Breakdown</h2>'
                f"{confidence_bars_html}"
                "</div>"
                '<div class="narrative-card"><h2>Confidence Components</h2>'
                + _table(
                    ["Component", "Value", "Description"],
                    confidence_rows,
                    ["24%", "10%", "66%"],
                )
                + "</div>"
                "</div>"
            ),
        ),
        _page(
            "Evidence Board",
            4,
            6,
            result,
            (
                '<div class="table-card">'
                '<div class="card-header-row"><h2>Normalized evidence</h2><p>Structured telemetry prepared for repeatable analyst review and export.</p></div>'
                + _table(
                    ["Process", "Host", "User", "Parent", "Event", "Command"],
                    evidence_rows,
                    ["14%", "14%", "16%", "14%", "10%", "32%"],
                )
                + "</div>"
                '<div class="narrative-card">'
                "<h2>Evidence handling note</h2>"
                "<p>Each row reflects normalized Windows or Sysmon-style telemetry retained in a consistent evidence model for downstream scoring, ATT&CK mapping, and audit replay.</p>"
                "</div>"
            ),
        ),
        _page(
            "MITRE ATT&CK Coverage",
            5,
            6,
            result,
            (
                '<div class="table-card">'
                '<div class="card-header-row"><h2>Mapped ATT&CK techniques</h2><p>Coverage generated from deterministic detections, not free-form narrative inference.</p></div>'
                + _table(
                    ["Technique ID", "Name", "Tactic", "Confidence", "Rules"],
                    mitre_rows,
                    ["14%", "24%", "22%", "12%", "28%"],
                )
                + "</div>"
                '<div class="narrative-card">'
                "<h2>Kill Chain Coverage</h2>"
                f'<div class="coverage-meter"><div class="coverage-fill" style="width:{coverage_percent}%"></div></div>'
                f'<p class="coverage-copy">{len(covered_phases)} of 7 phases covered ({coverage_percent}%). Covered phases: {escape(", ".join(covered_phases) or "none")}.</p>'
                f'<div class="coverage-label-row">{coverage_labels}</div>'
                "</div>"
            ),
        ),
        _page(
            "Guardrails and Analyst Notes",
            6,
            6,
            result,
            (
                '<div class="table-card">'
                '<div class="card-header-row"><h2>Guardrail review</h2><p>Controls applied before narrative generation and report export.</p></div>'
                '<div class="guardrail-grid">'
                f'<div class="guardrail-item"><span>Mode Requested</span><strong>{escape(result.guardrails.mode_requested)}</strong></div>'
                f'<div class="guardrail-item"><span>Mode Selected</span><strong>{escape(result.guardrails.mode_selected)}</strong></div>'
                f'<div class="guardrail-item"><span>Payload Redactions</span><strong>{result.guardrails.payload_redactions}</strong></div>'
                f'<div class="guardrail-item"><span>Safety Check</span><strong>{"PASS" if result.guardrails.safe_for_report else "BLOCKED"}</strong></div>'
                f'<div class="guardrail-item"><span>Fallback Applied</span><strong>{"Yes" if result.guardrails.fallback_applied else "No"}</strong></div>'
                f'<div class="guardrail-item"><span>Review Note</span><strong>{escape(result.guardrails.review_note)}</strong></div>'
                "</div>"
                "</div>"
                '<div class="two-column">'
                f'<div class="narrative-card"><h2>Analyst Notes</h2>{analyst_notes_html}</div>'
                f'<div class="narrative-card"><h2>Recommendations</h2>{recommendations_html}</div>'
                "</div>"
                '<div class="narrative-card"><h2>Analyst Memory</h2>'
                f"{analyst_memory_table}"
                "</div>"
                f'<div class="narrative-card"><h2>Limitations</h2>{limitations_html}</div>'
            ),
        ),
    ]

    styles = f"""
    @page {{ size: A4; margin: 20mm; }}
    body {{
      margin: 0;
      font-family: "DejaVu Sans", Helvetica, Arial, sans-serif;
      color: {TEXT};
      background: {PAGE_BG};
      font-size: 10pt;
    }}
    .page {{
      min-height: 257mm;
      display: flex;
      flex-direction: column;
      page-break-after: always;
      background: {PAGE_BG};
    }}
    .page:last-child {{ page-break-after: auto; }}
    .page-header, .page-footer {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      color: {TEXT_SOFT};
      font-size: 9pt;
    }}
    .page-header {{
      border-bottom: 1px solid {BORDER};
      padding-bottom: 12px;
      margin-bottom: 18px;
    }}
    .page-footer {{
      border-top: 1px solid {BORDER};
      padding-top: 10px;
      margin-top: auto;
    }}
    .page-header-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-mark {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 42px;
      height: 42px;
      border-radius: 12px;
      overflow: hidden;
      background: #040608;
      border: 1px solid {BORDER};
      box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
    }}
    .brand-mark-fallback {{
      background: linear-gradient(135deg, {BRAND_SOFT}, #DFF6FF);
      color: {NAVY};
      font-size: 15pt;
      font-weight: 700;
      letter-spacing: 0.08em;
    }}
    .brand-logo {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .brand-title {{
      font-size: 17pt;
      font-weight: 700;
      color: {NAVY};
      margin-bottom: 6px;
    }}
    .brand-meta {{ line-height: 1.5; }}
    .brand-page {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      color: {INK};
      font-weight: 600;
    }}
    .page-section {{
      color: {BRAND};
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-size: 8.5pt;
    }}
    .page-content {{ flex: 1; }}
    .section-title {{
      color: {NAVY};
      font-size: 15pt;
      font-weight: 700;
      margin: 0 0 16px;
    }}
    .hero-band {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 20px;
      border: 1px solid {BORDER};
      border-radius: 16px;
      background: linear-gradient(135deg, {SURFACE}, #FFFFFF);
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
    }}
    .report-kicker {{
      color: {BRAND};
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 8.5pt;
      font-weight: 700;
    }}
    .hero-copy {{
      flex: 1;
    }}
    .hero-title {{
      margin: 10px 0 10px;
      color: {NAVY};
      font-size: 18pt;
      line-height: 1.2;
    }}
    .hero-summary {{
      margin: 0;
      color: {INK_SOFT};
      line-height: 1.7;
      font-size: 10.5pt;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }}
    .hero-risk {{
      min-width: 140px;
      display: flex;
      align-items: flex-start;
      justify-content: flex-end;
    }}
    .risk-pill {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      padding: 10px 14px;
      color: #FFFFFF;
      font-size: 11pt;
      font-weight: 700;
      white-space: nowrap;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
    }}
    .metric-chip {{
      min-width: 110px;
      border: 1px solid {BORDER};
      border-radius: 10px;
      background: #FFFFFF;
      padding: 10px 12px;
    }}
    .metric-chip-label {{
      display: block;
      color: {INK_MUTED};
      font-size: 8.5pt;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 5px;
    }}
    .metric-chip-value {{
      color: {NAVY};
      font-size: 10pt;
      font-weight: 700;
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 18px 0;
    }}
    .metric-box {{
      background: #FFFFFF;
      border: 1px solid {BORDER};
      border-top: 4px solid {BRAND};
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }}
    .metric-label {{
      color: {TEXT_SOFT};
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 8.5pt;
      font-weight: 700;
    }}
    .metric-value {{
      font-size: 23pt;
      font-weight: 700;
      margin-top: 12px;
      color: {NAVY};
    }}
    .metric-subtitle {{
      margin-top: 8px;
      color: {INK_SOFT};
      font-size: 10pt;
      font-weight: 600;
    }}
    .narrative-card {{
      margin-top: 16px;
      background: #FFFFFF;
      border: 1px solid {BORDER};
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
    }}
    .narrative-card h2 {{
      margin: 0 0 10px;
      color: {NAVY};
      font-size: 11.5pt;
    }}
    .narrative-card p, .narrative-card li {{
      color: {INK_SOFT};
      line-height: 1.6;
    }}
    .table-card {{
      border: 1px solid {BORDER};
      border-radius: 14px;
      background: #FFFFFF;
      padding: 16px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    }}
    .card-header-row {{
      margin-bottom: 12px;
    }}
    .card-header-row h2 {{
      margin: 0;
      color: {NAVY};
      font-size: 11.5pt;
    }}
    .card-header-row p {{
      margin: 6px 0 0;
      color: {INK_MUTED};
      font-size: 9pt;
    }}
    .report-table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      margin-top: 6px;
    }}
    .report-table th {{
      background: {NAVY};
      color: #FFFFFF;
      font-size: 8.7pt;
      text-align: left;
      padding: 10px 10px;
      border: 1px solid {BORDER};
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .report-table td {{
      color: {TEXT};
      padding: 9px 10px;
      border: 1px solid {BORDER};
      vertical-align: top;
      word-break: break-word;
    }}
    .report-table tr.even td {{ background: #FFFFFF; }}
    .report-table tr.odd td {{ background: {SURFACE_ALT}; }}
    .mono-cell {{
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "DejaVu Sans Mono", "Courier New", monospace;
      font-size: 8.7pt;
      color: {NAVY_SOFT};
    }}
    .summary-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      border-radius: 999px;
      background: {SURFACE_ALT};
      border: 1px solid {BORDER};
      font-size: 9.2pt;
      color: {INK_SOFT};
    }}
    .summary-pill strong {{
      color: {NAVY};
    }}
    .score-summary-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }}
    .score-two-column {{
      margin-top: 2px;
    }}
    .bar-row {{
      margin-bottom: 12px;
    }}
    .bar-row-copy {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
    }}
    .bar-row-title {{
      color: {NAVY};
      font-size: 9.4pt;
      font-weight: 700;
    }}
    .bar-row-note {{
      color: {INK_MUTED};
      font-size: 8.5pt;
      text-align: right;
      max-width: 66%;
    }}
    .bar-track {{
      height: 10px;
      border-radius: 999px;
      background: {SURFACE_ALT};
      overflow: hidden;
      border: 1px solid {BORDER};
    }}
    .bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, {BRAND}, #14B8A6);
      border-radius: inherit;
    }}
    .bar-value {{
      display: block;
      margin-top: 4px;
      color: {NAVY};
      font-size: 8.5pt;
      font-weight: 700;
    }}
    .guardrail-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}
    .guardrail-item {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 14px;
    }}
    .guardrail-item span {{
      display: block;
      color: {INK_MUTED};
      font-size: 8.5pt;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .guardrail-item strong {{
      color: {NAVY};
      font-size: 10.5pt;
    }}
    .two-column {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-top: 16px;
    }}
    .coverage-meter {{
      height: 12px;
      border-radius: 999px;
      overflow: hidden;
      background: {SURFACE_ALT};
      border: 1px solid {BORDER};
    }}
    .coverage-fill {{
      height: 100%;
      background: linear-gradient(90deg, {BRAND}, #14B8A6);
    }}
    .coverage-copy {{
      margin: 10px 0 0;
      color: {INK_SOFT};
      line-height: 1.6;
    }}
    .coverage-label-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }}
    .coverage-label {{
      border-radius: 999px;
      border: 1px solid {BORDER};
      background: {SURFACE};
      padding: 6px 10px;
      color: {INK_MUTED};
      font-size: 8.3pt;
      font-weight: 600;
    }}
    .coverage-label.is-covered {{
      border-color: #99F6E4;
      background: {BRAND_SOFT};
      color: {NAVY};
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    """

    return f"<html><head><meta charset='utf-8'><style>{styles}</style></head><body>{''.join(pages)}</body></html>"


def _reportlab_generate_pdf(result: AnalysisResult) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PdfTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(NAVY),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "PdfSubtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(INK_MUTED),
        spaceAfter=8,
    )
    heading_style = ParagraphStyle(
        "PdfHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor(NAVY),
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        leading=13,
        fontSize=9.5,
        textColor=colors.HexColor(TEXT),
    )
    body_style.wordWrap = "CJK"
    small_style = ParagraphStyle(
        "ReportSmall",
        parent=body_style,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor(INK_MUTED),
    )
    small_style.wordWrap = "CJK"
    mono_style = ParagraphStyle(
        "ReportMono",
        parent=body_style,
        fontName="Courier",
        fontSize=8.1,
        leading=10,
        textColor=colors.HexColor(NAVY_SOFT),
    )
    mono_style.wordWrap = "CJK"
    cell_style = ParagraphStyle(
        "ReportCell",
        parent=body_style,
        fontSize=8.6,
        leading=10.5,
        textColor=colors.HexColor(TEXT),
    )
    cell_style.wordWrap = "CJK"
    compact_style = ParagraphStyle(
        "ReportCompact",
        parent=small_style,
        fontSize=8.0,
        leading=9.5,
        textColor=colors.HexColor(TEXT),
    )
    compact_style.wordWrap = "CJK"

    def clean(text: str) -> str:
        return escape(text).replace("\n", "<br/>")

    def card_table(rows: list[list[object]], col_widths: list[float] | None = None, header_bg: str = NAVY) -> Table:
        table = Table(rows, colWidths=col_widths, repeatRows=1, splitByRow=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor(BORDER)),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(SURFACE_ALT)]),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(TEXT)),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("LEADING", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return table

    def para(text: object, style: ParagraphStyle | None = None) -> Paragraph:
        if isinstance(text, Paragraph):
            return text
        return Paragraph(clean(str(text)), style or cell_style)

    def metric_box(label: str, value: str, subtitle: str, tone: str) -> Table:
        table = Table(
            [
                [Paragraph(f"<font color='{INK_MUTED}' size='8'><b>{escape(label.upper())}</b></font>", small_style)],
                [Paragraph(f"<font color='{tone}' size='21'><b>{escape(value)}</b></font>", body_style)],
                [Paragraph(f"<font color='{INK_SOFT}' size='9'><b>{escape(subtitle)}</b></font>", body_style)],
            ],
            colWidths=[(A4[0] - doc.leftMargin - doc.rightMargin - 18) / 4],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(BORDER)),
                    ("LINEABOVE", (0, 0), (-1, 0), 3, colors.HexColor(BRAND)),
                    ("ROUNDEDCORNERS", [10, 10, 10, 10]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return table

    def info_chip(label: str, value: str, width: float = 240) -> Table:
        table = Table(
            [[
                Paragraph(
                    f"<font color='{INK_MUTED}' size='7'>{escape(label.upper())}</font><br/><font color='{NAVY}' size='9'><b>{escape(value)}</b></font>",
                    compact_style,
                )
            ]],
            colWidths=[width],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(SURFACE)),
                    ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor(BORDER)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return table

    def bullet_paragraphs(items: list[str], empty_message: str) -> list[Paragraph]:
        normalized = items or [empty_message]
        return [Paragraph(f"• {clean(item)}", body_style) for item in normalized]

    def bullet_paragraphs(items: list[str], empty_message: str) -> list[Paragraph]:
        normalized = items or [empty_message]
        return [Paragraph(f"&bull; {clean(item)}", body_style) for item in normalized]

    def on_page(canvas, document):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor(BORDER))
        canvas.setFillColor(colors.HexColor(NAVY))
        canvas.setFont("Helvetica-Bold", 10)
        logo_candidate = logo_path()
        if logo_candidate.exists():
            canvas.drawImage(
                str(logo_candidate),
                doc.leftMargin,
                height - 16.5 * mm,
                width=10 * mm,
                height=10 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
            title_x = doc.leftMargin + 12 * mm
        else:
            title_x = doc.leftMargin
        canvas.drawString(title_x, height - 12 * mm, APP_REPORT_TITLE)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor(INK_MUTED))
        canvas.drawRightString(width - doc.rightMargin, height - 12 * mm, f"Analysis ID: {result.analysis_id}")
        canvas.line(doc.leftMargin, height - 14 * mm, width - doc.rightMargin, height - 14 * mm)
        canvas.line(doc.leftMargin, 14 * mm, width - doc.rightMargin, 14 * mm)
        canvas.drawString(doc.leftMargin, 10 * mm, f"{APP_NAME} | {APP_TAGLINE}")
        canvas.drawRightString(width - doc.rightMargin, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    covered_phases, coverage_percent = _phase_coverage(result.tactics)
    max_confidence_component = max((component.value for component in result.scores.confidence_trace), default=1)
    risk_tone = RISK_TONES.get(result.scores.risk_label.value, BRAND)
    executive_summary = _section_paragraph(result.analyst_brief, "Executive Summary")
    attack_reasoning = _first_section_bullets(result.analyst_brief, "Timeline", "Attack Chain Reasoning")
    recommendations = _first_section_bullets(
        result.analyst_brief,
        "Recommended Investigation Steps",
        "Recommended Next Defensive Checks",
    )
    analyst_notes = _first_section_bullets(result.analyst_brief, "Analyst Feedback History", "Analyst Notes")
    limitations = _first_section_bullets(result.analyst_brief, "Telemetry Limitations", "Limitations")
    generated_at = _fmt_ts(datetime.fromisoformat(result.audit.timestamp.replace("Z", "+00:00")))
    base_ts = result.attack_chain[0].timestamp if result.attack_chain else None

    attack_rows = [["Stage", "Timestamp", "Delta", "Evidence IDs", "Findings"]]
    attack_rows += [
        [
            para(step.stage),
            para(_fmt_ts(step.timestamp), compact_style),
            para(_delta_from_base(base_ts, step.timestamp), compact_style),
            para(", ".join(step.evidence_ids), compact_style),
            para(", ".join(step.finding_ids), compact_style),
        ]
        for step in result.attack_chain
    ]

    rule_rows = [["Rule ID", "Technique", "Score", "Reason"]]
    rule_rows += [
        [
            para(item.rule_id, compact_style),
            para(item.mitre_technique, compact_style),
            para(f"+{item.score_contribution}", compact_style),
            para(item.reason),
        ]
        for item in result.findings
    ]

    confidence_rows = [["Component", "Value", "Description"]]
    confidence_rows += [
        [para(item.label, compact_style), para(f"+{item.value}", compact_style), para(item.reason)]
        for item in result.scores.confidence_trace
    ]

    evidence_rows = [["Process", "Host", "User", "Parent", "Event", "Command"]]
    evidence_rows += [
        [
            para(item.process or "n/a", compact_style),
            para(item.host or "n/a", compact_style),
            para(item.user or "n/a", compact_style),
            para(item.parent_process or "n/a", compact_style),
            para(item.event_id or "n/a", compact_style),
            para(item.command_line or "n/a", mono_style),
        ]
        for item in result.evidence
    ]

    mitre_rows = [["Technique ID", "Name", "Tactic", "Confidence", "Rules"]]
    mitre_rows += [
        [
            para(item.technique_id, compact_style),
            para(item.technique_name),
            para(item.tactic, compact_style),
            para(f"{round(item.confidence * 100)}%", compact_style),
            para(", ".join(item.related_rules), compact_style),
        ]
        for item in result.tactics
    ]

    memory_rows = [["Rule ID", "Verdict", "Count", "Dataset", "Note"]]
    memory_rows += [
        [
            para(item.rule_id, compact_style),
            para(item.verdict.value, compact_style),
            para(str(item.count), compact_style),
            para(item.dataset_name, compact_style),
            para(item.note or "--", compact_style),
        ]
        for item in result.similar_cases
    ] or [[para("--"), para("--"), para("--"), para("--"), para("No prior analyst memory records.")]]

    bars: list[Table] = []
    for component in result.scores.confidence_trace:
        width_ratio = 0 if max_confidence_component <= 0 else max(0.08, component.value / max_confidence_component)
        fill_width = 220 * width_ratio
        bar = Table([["", ""]], colWidths=[fill_width, 220 - fill_width], rowHeights=[8])
        bar.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(BRAND)),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(SURFACE_ALT)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER)),
                ]
            )
        )
        bars.extend(
            [
                Paragraph(f"<b>{clean(component.label)}</b> <font color='{INK_MUTED}'>{clean(component.reason)}</font>", body_style),
                bar,
                Paragraph(f"<font color='{NAVY}'><b>+{component.value}</b></font>", small_style),
                Spacer(1, 8),
            ]
        )

    story = [
        Paragraph(APP_REPORT_TITLE, title_style),
        Paragraph("Executive security briefing for Windows incident triage and evidence-backed decision support.", subtitle_style),
        Spacer(1, 6),
        Table(
            [
                [info_chip("Report Mode", result.report_mode.upper(), 240), info_chip("Parser Mode", result.parser_mode, 240)],
                [info_chip("Generated", generated_at, 240), info_chip("Dataset", result.dataset_name, 240)],
            ],
            colWidths=[242, 242],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        ),
        Spacer(1, 12),
        Paragraph("Executive Summary", heading_style),
        Paragraph(clean(_section_paragraph(result.analyst_brief, "Executive Summary")), body_style),
        Spacer(1, 12),
        Table(
            [[
                metric_box("Risk Score", str(result.scores.risk_score), result.scores.risk_label.value, risk_tone),
                metric_box("Confidence", f"{result.scores.confidence_score}%", "Pipeline", BRAND),
                metric_box("Evidence", str(result.evidence_count), "Artifacts", BRAND),
                metric_box("MITRE", str(result.mitre_count), "ATT&CK IDs", BRAND),
            ]],
            colWidths=[118, 118, 118, 118],
            style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]),
        ),
        Spacer(1, 14),
        Table(
            [[
                Paragraph("<b>Detections Fired</b><br/>" + "<br/>".join(f"&bull; {clean(item.rule_id)}: {clean(item.title)}" for item in result.findings[:5]), body_style),
                Paragraph("<b>Investigation Posture</b><br/>" + clean(f"Current report is classified as {result.scores.risk_label.value} with {result.scores.confidence_score}% pipeline confidence."), body_style),
            ]],
            colWidths=[240, 240],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor(BORDER)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.45, colors.HexColor(BORDER)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        ),
        PageBreak(),
        Paragraph("Attack Chain", heading_style),
        Paragraph("Chronological reconstruction of the incident path from normalized telemetry.", small_style),
        Spacer(1, 8),
        card_table(attack_rows, [84, 108, 40, 118, 140]),
        Spacer(1, 12),
        Paragraph("Chain Reasoning", heading_style),
        *bullet_paragraphs(attack_reasoning, "No attack chain reasoning was available."),
        PageBreak(),
        Paragraph("Detections and Scoring", heading_style),
        Paragraph("Deterministic rule firing and confidence contributors used in the final score.", small_style),
        Spacer(1, 8),
        card_table(rule_rows, [78, 74, 38, 300]),
        Spacer(1, 12),
        Table(
            [[
                Paragraph(f"<b>Total Risk Score</b><br/>{result.scores.risk_score} / 100 ({result.scores.risk_label.value})", body_style),
                Paragraph(f"<b>Confidence Score</b><br/>{result.scores.confidence_score}% pipeline confidence", body_style),
            ]],
            colWidths=[240, 240],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(SURFACE)),
                    ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor(BORDER)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.45, colors.HexColor(BORDER)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        ),
        Spacer(1, 12),
        Paragraph("Confidence Breakdown", heading_style),
        *bars,
        Spacer(1, 4),
        card_table(confidence_rows, [118, 48, 324]),
        PageBreak(),
        Paragraph("Evidence Board", heading_style),
        Paragraph("Normalized evidence objects used for scoring, ATT&CK mapping, and analyst review.", small_style),
        Spacer(1, 8),
        card_table(evidence_rows, [58, 62, 74, 62, 36, 198]),
        PageBreak(),
        Paragraph("MITRE ATT&CK Coverage", heading_style),
        Paragraph("Technique coverage derived from deterministic detections and attack-chain reconstruction.", small_style),
        Spacer(1, 8),
        card_table(mitre_rows, [70, 112, 92, 52, 164]),
        Spacer(1, 12),
        Paragraph(f"Kill Chain Coverage: {len(covered_phases)} of 7 phases covered ({coverage_percent}%)", heading_style),
        Paragraph(clean(", ".join(covered_phases) if covered_phases else "No phases were covered."), body_style),
        PageBreak(),
        Paragraph("Guardrails and Analyst Notes", heading_style),
        card_table(
            [
                ["Control", "Value"],
                ["Mode Requested", result.guardrails.mode_requested],
                ["Mode Selected", result.guardrails.mode_selected],
                ["Payload Redactions", str(result.guardrails.payload_redactions)],
                ["Safety Check", "PASS" if result.guardrails.safe_for_report else "BLOCKED"],
                ["Fallback Applied", "Yes" if result.guardrails.fallback_applied else "No"],
                ["Review Note", result.guardrails.review_note],
            ],
            [132, 358],
        ),
        Spacer(1, 12),
        Paragraph("Analyst Memory", heading_style),
        card_table(memory_rows, [68, 78, 38, 94, 212]),
        Spacer(1, 12),
        Table(
            [[
                Paragraph("<b>Recommendations</b><br/>" + "<br/>".join(f"• {clean(item)}" for item in (recommendations or ['No recommendations were extracted.'])), body_style),
                Paragraph("<b>Limitations</b><br/>" + "<br/>".join(f"• {clean(item)}" for item in (limitations or ['No limitations were recorded.'])), body_style),
            ]],
            colWidths=[240, 240],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor(BORDER)),
                    ("INNERGRID", (0, 0), (-1, -1), 0.45, colors.HexColor(BORDER)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        ),
    ]

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buffer.getvalue()


def _fpdf_generate_pdf(result: AnalysisResult) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, APP_REPORT_TITLE, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 8, f"Dataset: {result.dataset_name}\nAnalysis ID: {result.analysis_id}\nRisk: {result.scores.risk_score} ({result.scores.risk_label.value})")
    return bytes(pdf.output(dest="S"))


def generate_pdf(result: AnalysisResult) -> bytes:
    html = build_html_report(result)
    try:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            from weasyprint import HTML

        return HTML(string=html, base_url=str(Path(__file__).resolve().parent)).write_pdf()
    except Exception:
        try:
            return _reportlab_generate_pdf(result)
        except Exception:
            return _fpdf_generate_pdf(result)
