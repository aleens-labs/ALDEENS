from __future__ import annotations

import json
from pathlib import Path

from app.core.models import AuditRecord


class AuditTrail:
    def __init__(self, audit_log_path: Path) -> None:
        self.audit_log_path = audit_log_path
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.audit_log_path.exists():
            self.audit_log_path.write_text("", encoding="utf-8")

    def record(self, entry: AuditRecord) -> None:
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.model_dump(mode="json", by_alias=True)) + "\n")

    def recent(self, limit: int = 20) -> list[AuditRecord]:
        lines = self.audit_log_path.read_text(encoding="utf-8").splitlines()
        parsed = [AuditRecord.model_validate_json(line) for line in lines[-limit:] if line.strip()]
        return list(reversed(parsed))

    def page(self, limit: int = 20, cursor: str | None = None) -> dict[str, object]:
        lines = [line for line in self.audit_log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        total = len(lines)
        start = 0
        if cursor:
            try:
                start = max(0, int(cursor))
            except ValueError as exc:
                raise ValueError("Audit cursor must be an integer offset.") from exc

        reversed_lines = list(reversed(lines))
        selected = reversed_lines[start : start + limit]
        items = [AuditRecord.model_validate_json(line) for line in selected]
        next_offset = start + len(items)
        has_more = next_offset < total

        return {
            "items": items,
            "nextCursor": str(next_offset) if has_more else None,
            "hasMore": has_more,
            "total": total,
            "limit": limit,
        }
