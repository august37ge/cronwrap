"""Circuit breaker logic for cron jobs.

Tracks consecutive failures and opens the circuit after a threshold,
preventing further runs until the job recovers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cronwrap.history import JobRecord, get_recent_runs


@dataclass
class CircuitState:
    job_name: str
    state: str          # "closed" | "open" | "half-open"
    consecutive_failures: int
    last_failure_at: Optional[str]
    threshold: int

    @property
    def is_open(self) -> bool:
        return self.state == "open"


def check_circuit(
    job_name: str,
    db_path: str,
    threshold: int = 3,
    lookback: int = 10,
) -> CircuitState:
    """Inspect recent history and return the circuit state for *job_name*."""
    runs: List[JobRecord] = get_recent_runs(db_path, job_name, limit=lookback)

    consecutive = 0
    last_failure_at: Optional[str] = None

    for run in runs:          # newest first
        if run.exit_code != 0:
            consecutive += 1
            if last_failure_at is None:
                last_failure_at = run.started_at
        else:
            break

    if consecutive >= threshold:
        state = "open"
    elif consecutive > 0:
        state = "half-open"
    else:
        state = "closed"

    return CircuitState(
        job_name=job_name,
        state=state,
        consecutive_failures=consecutive,
        last_failure_at=last_failure_at,
        threshold=threshold,
    )


def render_circuit_state(cs: CircuitState) -> str:
    """Return a human-readable summary of the circuit state."""
    icon = {"closed": "✅", "half-open": "⚠️", "open": "🔴"}.get(cs.state, "?")
    lines = [
        f"{icon}  {cs.job_name}: circuit {cs.state.upper()}",
        f"   consecutive failures : {cs.consecutive_failures} / {cs.threshold}",
    ]
    if cs.last_failure_at:
        lines.append(f"   last failure         : {cs.last_failure_at}")
    return "\n".join(lines)
