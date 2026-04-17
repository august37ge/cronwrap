"""Audit log: append-only record of every cronwrap invocation."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    id: int
    job_name: str
    command: str
    started_at: str
    exit_code: int
    duration_s: float
    retries: int
    tags: str  # comma-separated


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_audit_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name    TEXT    NOT NULL,
                command     TEXT    NOT NULL,
                started_at  TEXT    NOT NULL,
                exit_code   INTEGER NOT NULL,
                duration_s  REAL    NOT NULL,
                retries     INTEGER NOT NULL DEFAULT 0,
                tags        TEXT    NOT NULL DEFAULT ''
            )
            """
        )


def record_audit(
    db_path: str,
    job_name: str,
    command: str,
    started_at: datetime,
    exit_code: int,
    duration_s: float,
    retries: int = 0,
    tags: Optional[List[str]] = None,
) -> None:
    tags_str = ",".join(tags) if tags else ""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO audit_log (job_name, command, started_at, exit_code, duration_s, retries, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_name, command, started_at.isoformat(), exit_code, duration_s, retries, tags_str),
        )


def get_audit_entries(db_path: str, job_name: Optional[str] = None, limit: int = 50) -> List[AuditEntry]:
    query = "SELECT * FROM audit_log"
    params: list = []
    if job_name:
        query += " WHERE job_name = ?"
        params.append(job_name)
    query += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    with _connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [AuditEntry(**dict(r)) for r in rows]
