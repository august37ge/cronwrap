"""Job run history tracking using a simple SQLite backend."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict

DEFAULT_DB_PATH = Path.home() / ".cronwrap" / "history.db"


@dataclass
class JobRecord:
    job_name: str
    command: str
    started_at: str
    finished_at: str
    exit_code: int
    success: bool
    stdout: str
    stderr: str
    attempt: int = 1


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                command TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                exit_code INTEGER NOT NULL,
                success INTEGER NOT NULL,
                stdout TEXT,
                stderr TEXT,
                attempt INTEGER DEFAULT 1
            )
        """)


def record_run(record: JobRecord, db_path: Path = DEFAULT_DB_PATH) -> int:
    init_db(db_path)
    with _connect(db_path) as conn:
        cursor = conn.execute("""
            INSERT INTO job_runs
                (job_name, command, started_at, finished_at, exit_code, success, stdout, stderr, attempt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.job_name, record.command, record.started_at, record.finished_at,
            record.exit_code, int(record.success), record.stdout, record.stderr, record.attempt
        ))
        return cursor.lastrowid


def get_recent_runs(job_name: str, limit: int = 10, db_path: Path = DEFAULT_DB_PATH) -> List[JobRecord]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute("""
            SELECT * FROM job_runs WHERE job_name = ?
            ORDER BY started_at DESC LIMIT ?
        """, (job_name, limit)).fetchall()
    return [
        JobRecord(
            job_name=r["job_name"], command=r["command"],
            started_at=r["started_at"], finished_at=r["finished_at"],
            exit_code=r["exit_code"], success=bool(r["success"]),
            stdout=r["stdout"], stderr=r["stderr"], attempt=r["attempt"]
        ) for r in rows
    ]


def last_run(job_name: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[JobRecord]:
    runs = get_recent_runs(job_name, limit=1, db_path=db_path)
    return runs[0] if runs else None
