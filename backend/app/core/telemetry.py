from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PureWindowsPath
from typing import Any

from app.core.models import TelemetryEvent


def _pick(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None


def _basename(value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).replace("/", "\\")
    try:
        return PureWindowsPath(normalized).name.lower()
    except Exception:
        return normalized.lower().split("\\")[-1]


def _coerce_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _flatten_hash(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        joined = ", ".join(f"{key}={val}" for key, val in value.items() if val)
        return joined or None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item) or None
    return str(value)


class TelemetryNormalizer:
    """Normalizes Windows, Sysmon, and Defender-style events into a common shape."""

    def normalize(self, raw_events: list[dict[str, Any]]) -> list[TelemetryEvent]:
        normalized: list[TelemetryEvent] = []

        for index, raw in enumerate(raw_events, start=1):
            process = _pick(
                raw,
                "process",
                "ProcessName",
                "Image",
                "NewProcessName",
                "Application",
                "FileName",
                "initiatingProcessFileName",
            )
            parent_process = _pick(
                raw,
                "parentProcess",
                "ParentImage",
                "ParentProcessName",
                "CreatorProcessName",
                "InitiatingProcessParentFileName",
            )
            command_line = _pick(
                raw,
                "commandLine",
                "CommandLine",
                "ProcessCommandLine",
                "initiatingProcessCommandLine",
                "ScriptBlockText",
            )
            target_process = _pick(raw, "targetProcess", "TargetImage", "TargetProcessName", "TargetProcess", "ObjectName")
            destination_ip = _pick(
                raw,
                "destinationIp",
                "DestinationIp",
                "DestinationAddress",
                "RemoteIP",
                "RemoteAddress",
                "DestAddress",
            )
            destination_domain = _pick(
                raw,
                "destinationDomain",
                "DestinationHostname",
                "DestinationDnsDomain",
                "RemoteUrl",
                "RemoteDomain",
                "QueryName",
            )
            source_ip = _pick(
                raw,
                "sourceIp",
                "SourceIp",
                "SourceAddress",
                "LocalAddress",
                "RemoteIP",
            )
            file_path = _pick(
                raw,
                "filePath",
                "TargetFilename",
                "TargetObject",
                "RegistryPath",
                "Path",
                "ObjectName",
            )
            process_id = _pick(raw, "processId", "ProcessId", "ProcessID", "NewProcessId", "initiatingProcessId")
            parent_process_id = _pick(raw, "parentProcessId", "ParentProcessId", "CreatorProcessId", "InitiatingProcessParentId")
            image_path = str(process) if process else None
            parent_image_path = str(parent_process) if parent_process else None
            domain = _pick(raw, "domain", "Domain", "SubjectDomainName", "AccountDomain", "DomainName", "InitiatingProcessAccountDomain")
            user_sid = _pick(raw, "userSid", "UserSid", "SubjectUserSid", "Sid", "InitiatingProcessAccountSid")
            integrity_level = _pick(raw, "integrityLevel", "IntegrityLevel", "MandatoryLabel", "ProcessIntegrityLevel")
            logon_id = _pick(raw, "logonId", "LogonId", "SubjectLogonId", "TargetLogonId")
            session_id = _pick(raw, "sessionId", "SessionId", "TerminalSessionId")
            event = TelemetryEvent(
                index=index,
                timestamp=_coerce_timestamp(
                    _pick(
                        raw,
                        "timestamp",
                        "@timestamp",
                        "UtcTime",
                        "TimeCreated",
                        "TimeGenerated",
                        "CreatedTime",
                        "EventReceivedTime",
                        "EventTime",
                    )
                ),
                host=_pick(raw, "host", "Computer", "DeviceName", "Hostname", "ComputerName"),
                user=_pick(
                    raw,
                    "user",
                    "User",
                    "UserName",
                    "AccountName",
                    "SubjectUserName",
                    "InitiatingProcessAccountName",
                ),
                domain=str(domain) if domain else None,
                userSid=str(user_sid) if user_sid else None,
                process=_basename(
                    _pick(
                        raw,
                        "process",
                        "ProcessName",
                        "Image",
                        "NewProcessName",
                        "Application",
                        "FileName",
                        "initiatingProcessFileName",
                    )
                )
                or (str(process) if process else None),
                processId=str(process_id) if process_id else None,
                parentProcess=_basename(parent_process) or (str(parent_process) if parent_process else None),
                parentProcessId=str(parent_process_id) if parent_process_id else None,
                commandLine=str(command_line) if command_line else None,
                targetProcess=_basename(target_process) or (str(target_process) if target_process else None),
                sourceIp=str(source_ip) if source_ip else None,
                destinationIp=str(destination_ip) if destination_ip else None,
                destinationDomain=str(destination_domain) if destination_domain else None,
                integrityLevel=str(integrity_level) if integrity_level else None,
                imagePath=image_path,
                parentImagePath=parent_image_path,
                filePath=str(file_path) if file_path else None,
                hash=_flatten_hash(_pick(raw, "hash", "Hashes", "SHA256", "MD5", "Hash")),
                logonId=str(logon_id) if logon_id else None,
                sessionId=str(session_id) if session_id else None,
                eventId=str(_pick(raw, "eventId", "EventID", "EventId", "eventCode")) if _pick(raw, "eventId", "EventID", "EventId", "eventCode") else None,
                provider=str(_pick(raw, "provider", "ProviderName", "Provider", "Channel", "SourceName")) if _pick(raw, "provider", "ProviderName", "Provider", "Channel", "SourceName") else None,
                rawReference=f"event-{index}",
                rawEvent=raw,
            )
            normalized.append(event)

        return normalized
