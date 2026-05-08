from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import HTTPException, Request

_RATE_WINDOWS = {
    "second": 1,
    "minute": 60,
    "hour": 60 * 60,
}

_ALLOWED_UPLOAD_CONTENT_TYPES = {
    "",
    "application/json",
    "application/octet-stream",
    "text/json",
    "text/plain",
}

_ALLOWED_UPLOAD_SUFFIXES = {
    ".json",
    ".jsonl",
}


@dataclass(frozen=True)
class RatePolicy:
    limit: int
    window_seconds: int

    @classmethod
    def parse(cls, value: str) -> "RatePolicy":
        count_text, separator, window_text = value.strip().lower().partition("/")
        if not separator or not count_text.isdigit() or window_text not in _RATE_WINDOWS:
            raise ValueError(f"Unsupported rate policy `{value}`.")
        return cls(limit=int(count_text), window_seconds=_RATE_WINDOWS[window_text])


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def enforce(self, key: str, policy: RatePolicy) -> None:
        now = time.monotonic()
        cutoff = now - policy.window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= policy.limit:
                retry_after = max(1, int(policy.window_seconds - (now - bucket[0])))
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Retry in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)


def client_identity(request: Request) -> str:
    return request.client.host if request.client and request.client.host else "unknown-client"


def resolve_api_key(x_api_key: str | None, authorization: str | None) -> str | None:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        return token or None
    return None


def validate_upload_metadata(filename: str | None, content_type: str | None) -> None:
    suffix = Path(filename or "").suffix.lower()
    normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
    if suffix and suffix not in _ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload must use a .json or .jsonl filename.")
    if normalized_type not in _ALLOWED_UPLOAD_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Upload must be JSON telemetry.")


def validate_uploaded_events(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "events" in payload:
        events = payload["events"]
    elif isinstance(payload, list):
        events = payload
    else:
        raise HTTPException(status_code=400, detail="Uploaded JSON must be a list of events or an object with `events`.")

    if not isinstance(events, list) or not events:
        raise HTTPException(status_code=400, detail="Uploaded telemetry must contain at least one event object.")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(events, start=1):
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail=f"Uploaded event #{index} is not a JSON object.")
        normalized.append(item)
    return normalized
