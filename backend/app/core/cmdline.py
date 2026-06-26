from __future__ import annotations

import base64
import re
from collections.abc import Iterable

from app.core.models import Evidence


_ENCODED_COMMAND_RE = re.compile(
    r"(?:-|/)(?:enc|encodedcommand)\s+(?P<payload>[A-Za-z0-9+/=]{12,})",
    re.IGNORECASE,
)


def extract_encoded_payload(command_line: str | None) -> str | None:
    if not command_line:
        return None
    match = _ENCODED_COMMAND_RE.search(command_line)
    return match.group("payload") if match else None


def decode_powershell_payload(payload: str | None) -> str | None:
    if not payload:
        return None
    padded = payload + "=" * (-len(payload) % 4)
    for encoding in ("utf-16le", "utf-8"):
        try:
            decoded = base64.b64decode(padded, validate=False).decode(encoding, errors="ignore")
        except (ValueError, UnicodeDecodeError):
            continue
        normalized = " ".join(decoded.split())
        if normalized:
            return normalized
    return None


def summarize_decoded_payloads(evidence: Iterable[Evidence], limit: int = 2) -> list[str]:
    summaries: list[str] = []
    seen: set[str] = set()
    for item in evidence:
        decoded = decode_powershell_payload(extract_encoded_payload(item.command_line))
        if not decoded:
            continue
        summary = decoded[:160] + ("..." if len(decoded) > 160 else "")
        if summary in seen:
            continue
        seen.add(summary)
        summaries.append(summary)
        if len(summaries) >= limit:
            break
    return summaries
