from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.models import FeedbackRecord, FeedbackVerdict, SimilarCase


class FeedbackMemory:
    def __init__(self, db_path: Path, memory_dir: Path) -> None:
        self.db_path = db_path
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._bootstrap()

    def _bootstrap(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyst_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL,
                    dataset_name TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    note TEXT,
                    rule_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyst_overrides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL,
                    dataset_name TEXT,
                    analyst_confidence INTEGER NOT NULL CHECK(analyst_confidence BETWEEN 0 AND 100),
                    override_note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        self._write_snapshots()

    def save_feedback(self, feedback: FeedbackRecord) -> None:
        created_at = datetime.now(tz=timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for rule_id in feedback.rule_ids:
                conn.execute(
                    """
                    INSERT INTO analyst_feedback (
                        analysis_id, dataset_name, verdict, note, rule_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback.analysis_id,
                        feedback.dataset_name,
                        feedback.verdict.value,
                        feedback.note,
                        rule_id,
                        created_at,
                    ),
                )
            conn.commit()
        self._write_snapshots()

    def similar_cases(self, rule_ids: list[str], dataset_name: str) -> list[SimilarCase]:
        if not rule_ids:
            return []
        placeholders = ",".join("?" for _ in rule_ids)
        query = f"""
            SELECT rule_id, verdict, COALESCE(note, ''), COUNT(*), dataset_name, MAX(created_at)
            FROM analyst_feedback
            WHERE rule_id IN ({placeholders})
            GROUP BY rule_id, verdict, note, dataset_name
            ORDER BY MAX(created_at) DESC
            LIMIT 6
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, rule_ids).fetchall()
        similar: list[SimilarCase] = []
        for rule_id, verdict, note, count, seen_dataset, seen_at in rows:
            similar.append(
                SimilarCase(
                    ruleId=rule_id,
                    verdict=FeedbackVerdict(verdict),
                    note=note or None,
                    count=int(count),
                    datasetName=seen_dataset or dataset_name,
                    seenAt=seen_at,
                )
            )
        return similar

    def save_confidence_override(
        self,
        analysis_id: str,
        dataset_name: str | None,
        analyst_confidence: int,
        override_note: str | None,
    ) -> dict[str, str | int]:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO analyst_overrides (
                    analysis_id, dataset_name, analyst_confidence, override_note
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    dataset_name,
                    analyst_confidence,
                    override_note,
                ),
            )
            conn.commit()
        return {"status": "saved", "analystConfidence": analyst_confidence}

    def get_confidence_override(self, analysis_id: str) -> dict[str, str | int | None]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT analyst_confidence, override_note, created_at
                FROM analyst_overrides
                WHERE analysis_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (analysis_id,),
            ).fetchone()

        if row:
            analyst_confidence, override_note, created_at = row
            return {
                "analystConfidence": int(analyst_confidence),
                "overrideNote": override_note,
                "createdAt": created_at,
            }
        return {"analystConfidence": None}

    def _write_snapshots(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT rule_id, verdict, COUNT(*), MAX(created_at)
                FROM analyst_feedback
                GROUP BY rule_id, verdict
                ORDER BY MAX(created_at) DESC
                """
            ).fetchall()
            fp_rows = conn.execute(
                """
                SELECT rule_id, dataset_name, COALESCE(note, ''), created_at
                FROM analyst_feedback
                WHERE verdict = ?
                ORDER BY created_at DESC
                LIMIT 25
                """,
                (FeedbackVerdict.FALSE_POSITIVE.value,),
            ).fetchall()

        case_patterns = [
            {
                "ruleId": rule_id,
                "verdict": verdict,
                "count": count,
                "lastSeen": last_seen,
            }
            for rule_id, verdict, count, last_seen in rows
        ]
        false_positive_feedback = [
            {
                "ruleId": rule_id,
                "datasetName": dataset_name,
                "note": note,
                "seenAt": seen_at,
            }
            for rule_id, dataset_name, note, seen_at in fp_rows
        ]

        (self.memory_dir / "case-patterns.json").write_text(
            json.dumps(case_patterns, indent=2),
            encoding="utf-8",
        )
        (self.memory_dir / "false-positive-feedback.json").write_text(
            json.dumps(false_positive_feedback, indent=2),
            encoding="utf-8",
        )
