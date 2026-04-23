"""Dead-letter queue: persist repeatedly-failing job runs for later inspection."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_DB = Path("cronwrap_deadletter.db")


@dataclass
class DeadLetterEntry:
    id: int
    job_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    attempt: int
    recorded_at: str


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_deadletter_db(db_path: Path = DEFAULT_DB) -> None:
    """Create the dead_letter table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dead_letter (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name    TEXT    NOT NULL,
                command     TEXT    NOT NULL,
                exit_code   INTEGER NOT NULL,
                stdout      TEXT    NOT NULL DEFAULT '',
                stderr      TEXT    NOT NULL DEFAULT '',
                attempt     INTEGER NOT NULL DEFAULT 1,
                recorded_at TEXT    NOT NULL
            )
            """
        )


def push_dead_letter(
    job_name: str,
    command: str,
    exit_code: int,
    stdout: str = "",
    stderr: str = "",
    attempt: int = 1,
    db_path: Path = DEFAULT_DB,
) -> None:
    """Record a failed job run in the dead-letter queue."""
    init_deadletter_db(db_path)
    recorded_at = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO dead_letter (job_name, command, exit_code, stdout, stderr, attempt, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (job_name, command, exit_code, stdout, stderr, attempt, recorded_at),
        )


def get_dead_letters(
    job_name: Optional[str] = None,
    limit: int = 50,
    db_path: Path = DEFAULT_DB,
) -> List[DeadLetterEntry]:
    """Retrieve dead-letter entries, optionally filtered by job name."""
    init_deadletter_db(db_path)
    with _connect(db_path) as conn:
        if job_name:
            rows = conn.execute(
                "SELECT * FROM dead_letter WHERE job_name = ? ORDER BY id DESC LIMIT ?",
                (job_name, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM dead_letter ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [DeadLetterEntry(**dict(r)) for r in rows]


def purge_dead_letters(
    job_name: Optional[str] = None,
    db_path: Path = DEFAULT_DB,
) -> int:
    """Delete dead-letter entries; returns number of rows removed."""
    init_deadletter_db(db_path)
    with _connect(db_path) as conn:
        if job_name:
            cur = conn.execute(
                "DELETE FROM dead_letter WHERE job_name = ?", (job_name,)
            )
        else:
            cur = conn.execute("DELETE FROM dead_letter")
        return cur.rowcount
