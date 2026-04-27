"""Persist pipeline run results to SQLite for history and reporting."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from cronwrap.pipeline import PipelineResult


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_pipeline_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline    TEXT    NOT NULL,
                ran_at      TEXT    NOT NULL,
                succeeded   INTEGER NOT NULL,
                aborted_at  TEXT,
                duration    REAL    NOT NULL,
                steps_json  TEXT    NOT NULL
            )
            """
        )


def record_pipeline_run(db_path: str, result: PipelineResult) -> int:
    steps_data = [
        {
            "name": o.step.name,
            "returncode": o.result.returncode,
            "duration": o.result.duration,
            "attempt": o.attempt,
        }
        for o in result.outcomes
    ]
    ran_at = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO pipeline_runs
                (pipeline, ran_at, succeeded, aborted_at, duration, steps_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result.pipeline_name,
                ran_at,
                int(result.succeeded),
                result.aborted_at,
                result.total_duration,
                json.dumps(steps_data),
            ),
        )
        return cur.lastrowid  # type: ignore[return-value]


def get_pipeline_runs(
    db_path: str,
    pipeline: Optional[str] = None,
    limit: int = 20,
) -> List[sqlite3.Row]:
    sql = "SELECT * FROM pipeline_runs"
    params: list = []
    if pipeline:
        sql += " WHERE pipeline = ?"
        params.append(pipeline)
    sql += " ORDER BY ran_at DESC LIMIT ?"
    params.append(limit)
    with _connect(db_path) as conn:
        return conn.execute(sql, params).fetchall()
