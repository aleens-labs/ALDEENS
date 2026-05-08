from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.models import DetectionFinding, Evidence, TacticHit

MISSING_VALUE = "Not available"
MIN_TS = datetime.min.replace(tzinfo=timezone.utc)


def format_missing(value: object) -> str:
    if value in (None, "", [], {}):
        return MISSING_VALUE
    return str(value)


def summarize_command(command_line: str | None, limit: int = 120) -> str:
    text = format_missing(command_line)
    if text == MISSING_VALUE or len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _sort_timestamp(value: datetime | None) -> datetime:
    if value is None:
        return MIN_TS
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)


def split_domain_user(domain: str | None, user: str | None) -> tuple[str | None, str | None]:
    if domain:
        return domain, user
    if user and "\\" in user:
        parsed_domain, parsed_user = user.split("\\", 1)
        return parsed_domain or None, parsed_user or None
    return None, user


def extract_command_lines(
    evidence: list[Evidence],
    findings: list[DetectionFinding],
    tactics: list[TacticHit],
) -> list[dict[str, object]]:
    tactic_names = {item.technique_id: item.technique_name for item in tactics}
    finding_map: dict[str, list[DetectionFinding]] = {}
    for finding in findings:
        for evidence_id in finding.evidence_ids:
            finding_map.setdefault(evidence_id, []).append(finding)

    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in sorted(evidence, key=lambda current: (_sort_timestamp(current.timestamp), current.evidence_id)):
        if not item.command_line or item.evidence_id in seen:
            continue
        seen.add(item.evidence_id)
        related_findings = finding_map.get(item.evidence_id, [])
        rule_ids = sorted({finding.rule_id for finding in related_findings}) or [MISSING_VALUE]
        mitre_entries = sorted(
            {
                f"{finding.mitre_technique} {tactic_names.get(finding.mitre_technique, '')}".strip()
                for finding in related_findings
            }
        ) or [MISSING_VALUE]
        entries.append(
            {
                "timestamp": item.timestamp,
                "process": item.process,
                "parent_process": item.parent_process,
                "command_line": item.command_line,
                "rule_ids": rule_ids,
                "mitre": mitre_entries,
                "raw_event_id": item.raw_reference,
                "evidence_id": item.evidence_id,
            }
        )
    return entries


@dataclass
class ProcessNode:
    key: str
    process_name: str
    process_id: str | None = None
    image_path: str | None = None
    timestamp: datetime | None = None
    command_line: str | None = None
    parent_key: str | None = None
    parent_process_name: str | None = None
    observed: bool = True
    children: set[str] = field(default_factory=set)


def _node_key(item: Evidence) -> str | None:
    if item.process_id:
        return f"pid:{item.process_id}"
    if item.image_path:
        return f"image:{item.image_path.lower()}"
    if item.process:
        return f"process:{item.process.lower()}"
    return None


def _parent_key(item: Evidence) -> str | None:
    if item.parent_process_id:
        return f"pid:{item.parent_process_id}"
    if item.parent_image_path:
        return f"image:{item.parent_image_path.lower()}"
    if item.parent_process:
        return f"process:{item.parent_process.lower()}"
    return None


def _node_header(node: ProcessNode) -> str:
    header = node.process_name or MISSING_VALUE
    if node.process_id:
        header = f"{header} [PID: {node.process_id}]"
    return header


def build_process_tree(evidence: list[Evidence]) -> tuple[list[str], bool]:
    nodes: dict[str, ProcessNode] = {}
    partial = False

    for item in sorted(evidence, key=lambda current: (_sort_timestamp(current.timestamp), current.evidence_id)):
        node_key = _node_key(item)
        if node_key is None:
            partial = True
            continue

        parent_key = _parent_key(item)
        if parent_key is None and len(evidence) > 1:
            partial = True

        node = nodes.get(node_key)
        if node is None:
            node = ProcessNode(
                key=node_key,
                process_name=item.process or format_missing(item.image_path),
                process_id=item.process_id,
                image_path=item.image_path,
                timestamp=item.timestamp,
                command_line=item.command_line,
                parent_key=parent_key,
                parent_process_name=item.parent_process,
            )
            nodes[node_key] = node
        else:
            node.process_name = node.process_name or item.process or format_missing(item.image_path)
            node.process_id = node.process_id or item.process_id
            node.image_path = node.image_path or item.image_path
            node.timestamp = node.timestamp or item.timestamp
            node.command_line = node.command_line or item.command_line
            node.parent_key = node.parent_key or parent_key
            node.parent_process_name = node.parent_process_name or item.parent_process

        if parent_key:
            parent_node = nodes.get(parent_key)
            if parent_node is None:
                parent_node = ProcessNode(
                    key=parent_key,
                    process_name=item.parent_process or format_missing(item.parent_image_path),
                    process_id=item.parent_process_id,
                    image_path=item.parent_image_path,
                    observed=False,
                )
                nodes[parent_key] = parent_node
            parent_node.children.add(node_key)

    if not nodes:
        return ["Process telemetry was not available in the uploaded logs."], True

    roots = [node for node in nodes.values() if not node.parent_key or node.parent_key not in nodes]
    roots.sort(key=lambda current: (_sort_timestamp(current.timestamp), current.process_name))
    if not roots:
        partial = True
        roots = sorted(nodes.values(), key=lambda current: (_sort_timestamp(current.timestamp), current.process_name))

    lines: list[str] = []
    visited: set[str] = set()

    def visit(node: ProcessNode, prefix: str = "", branch: str = "") -> None:
        if node.key in visited:
            return
        visited.add(node.key)
        lines.append(f"{prefix}{branch}{_node_header(node)}")
        context_prefix = f"{prefix}{'    ' if branch else ''}"
        if node.image_path:
            lines.append(f"{context_prefix}Path: {node.image_path}")
        if node.command_line:
            lines.append(f"{context_prefix}CommandLine: {summarize_command(node.command_line)}")
        if node.timestamp:
            lines.append(f"{context_prefix}Time: {node.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        child_keys = sorted(
            node.children,
            key=lambda key: (_sort_timestamp(nodes[key].timestamp), nodes[key].process_name),
        )
        for index, child_key in enumerate(child_keys):
            child_branch = "\\-- " if index == len(child_keys) - 1 else "+-- "
            if not branch:
                child_prefix = prefix
            elif branch == "\\-- ":
                child_prefix = f"{prefix}    "
            else:
                child_prefix = f"{prefix}|   "
            visit(nodes[child_key], child_prefix, child_branch)

    for root in roots:
        visit(root)

    if len(visited) != len(nodes):
        partial = True
        for node in sorted(nodes.values(), key=lambda current: (_sort_timestamp(current.timestamp), current.process_name)):
            if node.key not in visited:
                visit(node)

    return lines, partial


def extract_host_context(evidence: list[Evidence]) -> list[dict[str, str]]:
    contexts: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in sorted(evidence, key=lambda current: (_sort_timestamp(current.timestamp), current.evidence_id)):
        if item.evidence_id in seen:
            continue
        seen.add(item.evidence_id)
        domain, username = split_domain_user(item.domain, item.user)
        contexts.append(
            {
                "Evidence": item.evidence_id,
                "Raw Event": format_missing(item.raw_reference),
                "Hostname": format_missing(item.host),
                "User": format_missing(username or item.user),
                "Domain": format_missing(domain),
                "User SID": format_missing(item.user_sid),
                "Process ID": format_missing(item.process_id),
                "Parent Process ID": format_missing(item.parent_process_id),
                "Integrity Level": format_missing(item.integrity_level),
                "Hash": format_missing(item.hash),
                "Image Path": format_missing(item.image_path),
                "Parent Image Path": format_missing(item.parent_image_path),
                "Source IP": format_missing(item.source_ip),
                "Destination IP": format_missing(item.destination_ip),
                "Logon ID": format_missing(item.logon_id),
                "Session ID": format_missing(item.session_id),
            }
        )

    return contexts
