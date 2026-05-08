from __future__ import annotations

import hashlib

from app.core.models import Evidence, TelemetryEvent


def _summarize(event: TelemetryEvent) -> str:
    pieces = [
        event.process or "unknown-process",
        f"on {event.host}" if event.host else None,
        f"by {event.user}" if event.user else None,
    ]
    if event.command_line:
        pieces.append(f"cmd={event.command_line[:72]}")
    elif event.destination_ip or event.destination_domain:
        target = event.destination_domain or event.destination_ip
        pieces.append(f"network={target}")
    elif event.target_process:
        pieces.append(f"target={event.target_process}")
    return " | ".join(piece for piece in pieces if piece)


class EvidenceBuilder:
    def from_events(self, events: list[TelemetryEvent]) -> list[Evidence]:
        evidence: list[Evidence] = []
        for event in events:
            digest_source = "|".join(
                [
                    str(event.index),
                    event.timestamp.isoformat() if event.timestamp else "",
                    event.host or "",
                    event.user or "",
                    event.process or "",
                    event.command_line or "",
                    event.raw_reference,
                ]
            )
            evidence_id = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]
            evidence.append(
                Evidence(
                    evidenceId=evidence_id,
                    timestamp=event.timestamp,
                    host=event.host,
                    user=event.user,
                    domain=event.domain,
                    userSid=event.user_sid,
                    process=event.process,
                    processId=event.process_id,
                    parentProcess=event.parent_process,
                    parentProcessId=event.parent_process_id,
                    commandLine=event.command_line,
                    targetProcess=event.target_process,
                    sourceIp=event.source_ip,
                    destinationIp=event.destination_ip,
                    destinationDomain=event.destination_domain,
                    integrityLevel=event.integrity_level,
                    imagePath=event.image_path,
                    parentImagePath=event.parent_image_path,
                    filePath=event.file_path,
                    hash=event.hash,
                    logonId=event.logon_id,
                    sessionId=event.session_id,
                    eventId=event.event_id,
                    provider=event.provider,
                    rawReference=event.raw_reference,
                    summary=_summarize(event),
                )
            )
        return evidence
