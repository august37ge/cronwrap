"""Cooldown enforcement — prevent a job from running again too soon after a failure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwrap.history import _connect, init_db


@dataclass
class CooldownResult:
    job_name: str
    allowed: bool
    last_failure: Optional[str]  # ISO timestamp or None
    cooldown_seconds: int
    retry_after: Optional[str]  # ISO timestamp or None


def check_cooldown(db_path: str, job_name: str, cooldown_seconds: int) -> CooldownResult:
    """Return a CooldownResult indicating whether the job is allowed to run.

    A job is blocked when its most recent run was a failure that occurred
    within the last *cooldown_seconds* seconds.
    """
    init_db(db_path)
    con = _connect(db_path)
    try:
        cur = con.execute(
            """
            SELECT started_at, success
            FROM runs
            WHERE job_name = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (job_name,),
        )
        row = cur.fetchone()
    finally:
        con.close()

    if row is None or row["success"]:
        return CooldownResult(
            job_name=job_name,
            allowed=True,
            last_failure=None,
            cooldown_seconds=cooldown_seconds,
            retry_after=None,
        )

    last_failure_ts = row["started_at"]
    last_failure_dt = datetime.fromisoformat(last_failure_ts).replace(
        tzinfo=timezone.utc
    )
    retry_after_dt = last_failure_dt + timedelta(seconds=cooldown_seconds)
    now = datetime.now(timezone.utc)
    allowed = now >= retry_after_dt

    return CooldownResult(
        job_name=job_name,
        allowed=allowed,
        last_failure=last_failure_ts,
        cooldown_seconds=cooldown_seconds,
        retry_after=retry_after_dt.isoformat() if not allowed else None,
    )


def render_cooldown_result(result: CooldownResult) -> str:
    """Return a human-readable summary of the cooldown check."""
    if result.allowed:
        return f"[cooldown] {result.job_name}: allowed (no recent failure)"
    return (
        f"[cooldown] {result.job_name}: BLOCKED — last failure at "
        f"{result.last_failure}, retry after {result.retry_after}"
    )
