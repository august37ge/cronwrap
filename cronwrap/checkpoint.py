"""Checkpoint support — persist and retrieve named progress markers for long-running jobs."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Checkpoint:
    job_name: str
    key: str
    value: str
    updated_at: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_checkpoint_db(db_path: str) -> None:
    """Create the checkpoints table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                job_name TEXT NOT NULL,
                key      TEXT NOT NULL,
                value    TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (job_name, key)
            )
            """
        )
        conn.commit()


def save_checkpoint(db_path: str, job_name: str, key: str, value: str) -> None:
    """Insert or replace a checkpoint value."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO checkpoints (job_name, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(job_name, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (job_name, key, value, now),
        )
        conn.commit()


def load_checkpoint(db_path: str, job_name: str, key: str) -> Optional[Checkpoint]:
    """Return the checkpoint or None if it does not exist."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT job_name, key, value, updated_at FROM checkpoints WHERE job_name=? AND key=?",
            (job_name, key),
        ).fetchone()
    if row is None:
        return None
    return Checkpoint(**dict(row))


def delete_checkpoint(db_path: str, job_name: str, key: str) -> bool:
    """Delete a checkpoint. Returns True if a row was removed."""
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM checkpoints WHERE job_name=? AND key=?",
            (job_name, key),
        )
        conn.commit()
    return cursor.rowcount > 0


def list_checkpoints(db_path: str, job_name: str) -> list[Checkpoint]:
    """Return all checkpoints for a job, ordered by key."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT job_name, key, value, updated_at FROM checkpoints WHERE job_name=? ORDER BY key",
            (job_name,),
        ).fetchall()
    return [Checkpoint(**dict(r)) for r in rows]
