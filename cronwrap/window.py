"""Execution window enforcement — allow jobs to run only within defined time windows."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional


@dataclass
class WindowResult:
    job_name: str
    allowed: bool
    reason: str
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    checked_at: Optional[str] = None


_TIME_RE = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')


def _parse_time(value: str) -> time:
    """Parse a HH:MM string into a time object."""
    m = _TIME_RE.match(value.strip())
    if not m:
        raise ValueError(f"Invalid time format '{value}' — expected HH:MM")
    return time(int(m.group(1)), int(m.group(2)))


def check_window(
    job_name: str,
    window_start: str,
    window_end: str,
    now: Optional[datetime] = None,
) -> WindowResult:
    """Return a WindowResult indicating whether *now* falls within [start, end).

    Windows that span midnight are supported (e.g. 22:00 – 06:00).
    """
    if now is None:
        now = datetime.now()

    checked_at = now.isoformat(timespec="seconds")

    try:
        t_start = _parse_time(window_start)
        t_end = _parse_time(window_end)
    except ValueError as exc:
        return WindowResult(
            job_name=job_name,
            allowed=False,
            reason=str(exc),
            window_start=window_start,
            window_end=window_end,
            checked_at=checked_at,
        )

    current = now.time().replace(second=0, microsecond=0)

    if t_start <= t_end:
        # Normal window: e.g. 08:00 – 18:00
        in_window = t_start <= current < t_end
    else:
        # Overnight window: e.g. 22:00 – 06:00
        in_window = current >= t_start or current < t_end

    if in_window:
        reason = f"Within allowed window {window_start}–{window_end}"
    else:
        reason = f"Outside allowed window {window_start}–{window_end} (current time {current.strftime('%H:%M')})"

    return WindowResult(
        job_name=job_name,
        allowed=in_window,
        reason=reason,
        window_start=window_start,
        window_end=window_end,
        checked_at=checked_at,
    )


def render_window_result(result: WindowResult) -> str:
    status = "ALLOWED" if result.allowed else "BLOCKED"
    lines = [
        f"[window] {result.job_name}: {status}",
        f"  reason : {result.reason}",
        f"  checked: {result.checked_at}",
    ]
    return "\n".join(lines)
