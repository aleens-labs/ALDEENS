from __future__ import annotations


def redact_payload_like_content(text: str) -> str:
    return text.replace("-EncodedCommand ", "-EncodedCommand [redacted] ")

