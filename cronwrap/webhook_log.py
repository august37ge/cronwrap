"""Webhook delivery log — persists outbound webhook attempts and their outcomes.

Each time ``notify()`` fires a webhook, callers can record the attempt here
so operators can audit delivery history, spot failures, and replay missed
notifications without re-running the underlying job.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class WebhookLogEntry:
    """A single recorded webhook delivery attempt."""

    id: Optional[int]
    job_name: str
    url: str
    status_code: Optional[int]   # None when a network error prevented any response
    success: bool
    error: Optional[str]         # Exception message on network failure
    payload_preview: str         # First 200 chars of the JSON payload
    attempted_at: str            # ISO-8601 timestamp


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_webhook_log_db(db_path: str) -> None:
    """Create the webhook_log table if it does not already exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name      TEXT    NOT NULL,
                url           TEXT    NOT NULL,
                status_code   INTEGER,
                success       INTEGER NOT NULL,
                error         TEXT,
                payload_preview TEXT  NOT NULL DEFAULT '',
                attempted_at  TEXT    NOT NULL
            )
            """
        )


def record_webhook(
    db_path: str,
    job_name: str,
    url: str,
    *,
    status_code: Optional[int] = None,
    success: bool,
    error: Optional[str] = None,
    payload_preview: str = "",
    attempted_at: Optional[str] = None,
) -> WebhookLogEntry:
    """Persist one webhook delivery attempt and return the stored entry."""
    ts = attempted_at or datetime.now(timezone.utc).isoformat()
    preview = payload_preview[:200]

    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO webhook_log
                (job_name, url, status_code, success, error, payload_preview, attempted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (job_name, url, status_code, int(success), error, preview, ts),
        )
        entry_id = cur.lastrowid

    return WebhookLogEntry(
        id=entry_id,
        job_name=job_name,
        url=url,
        status_code=status_code,
        success=success,
        error=error,
        payload_preview=preview,
        attempted_at=ts,
    )


def get_webhook_log(
    db_path: str,
    job_name: Optional[str] = None,
    limit: int = 50,
    failures_only: bool = False,
) -> List[WebhookLogEntry]:
    """Return recent webhook log entries, newest first.

    Args:
        db_path:       Path to the SQLite database.
        job_name:      When provided, restrict results to this job.
        limit:         Maximum number of rows to return.
        failures_only: When True, only return entries where success=0.
    """
    clauses: List[str] = []
    params: List[object] = []

    if job_name is not None:
        clauses.append("job_name = ?")
        params.append(job_name)

    if failures_only:
        clauses.append("success = 0")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)

    sql = f"SELECT * FROM webhook_log {where} ORDER BY id DESC LIMIT ?"

    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        WebhookLogEntry(
            id=r["id"],
            job_name=r["job_name"],
            url=r["url"],
            status_code=r["status_code"],
            success=bool(r["success"]),
            error=r["error"],
            payload_preview=r["payload_preview"],
            attempted_at=r["attempted_at"],
        )
        for r in rows
    ]


def render_webhook_log(entries: List[WebhookLogEntry]) -> str:
    """Return a human-readable table of webhook log entries."""
    if not entries:
        return "No webhook log entries found."

    header = f"{'ID':>6}  {'Job':<20}  {'Status':>6}  {'OK':>4}  {'Attempted At':>25}  URL"
    sep = "-" * len(header)
    lines = [header, sep]

    for e in entries:
        status = str(e.status_code) if e.status_code is not None else "ERR"
        ok = "yes" if e.success else "NO"
        lines.append(
            f"{e.id!s:>6}  {e.job_name:<20}  {status:>6}  {ok:>4}  {e.attempted_at:>25}  {e.url}"
        )
        if e.error:
            lines.append(f"{'':>6}  error: {e.error}")

    return "\n".join(lines)
