"""Escalation policy: alert different targets based on consecutive failure count."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.history import get_recent_runs


@dataclass
class EscalationLevel:
    """A single escalation tier."""
    after_failures: int          # trigger when consecutive failures >= this
    notify: List[str]            # list of contact identifiers / channels
    label: str = ""              # human-readable label, e.g. "warn", "critical"


@dataclass
class EscalationResult:
    job_name: str
    consecutive_failures: int
    level: Optional[EscalationLevel]
    triggered: bool
    contacts: List[str] = field(default_factory=list)
    message: str = ""


def _count_consecutive_failures(job_name: str, db_path: str, limit: int = 50) -> int:
    """Return how many of the most-recent runs are failures (unbroken streak)."""
    runs = get_recent_runs(job_name, limit=limit, db_path=db_path)
    count = 0
    for run in runs:
        if run.exit_code != 0:
            count += 1
        else:
            break
    return count


def _pick_level(
    consecutive: int, levels: List[EscalationLevel]
) -> Optional[EscalationLevel]:
    """Return the highest applicable escalation level."""
    applicable = [
        lvl for lvl in levels if consecutive >= lvl.after_failures
    ]
    if not applicable:
        return None
    return max(applicable, key=lambda lvl: lvl.after_failures)


def check_escalation(
    job_name: str,
    levels: List[EscalationLevel],
    db_path: str = "cronwrap.db",
) -> EscalationResult:
    """Evaluate escalation policy for *job_name* against its run history."""
    consecutive = _count_consecutive_failures(job_name, db_path)
    level = _pick_level(consecutive, levels)

    if level is None:
        return EscalationResult(
            job_name=job_name,
            consecutive_failures=consecutive,
            level=None,
            triggered=False,
            message="No escalation level reached.",
        )

    msg = (
        f"[{level.label or 'escalation'}] {job_name} has failed "
        f"{consecutive} consecutive time(s) "
        f"(threshold: {level.after_failures})."
    )
    return EscalationResult(
        job_name=job_name,
        consecutive_failures=consecutive,
        level=level,
        triggered=True,
        contacts=list(level.notify),
        message=msg,
    )


def render_escalation_result(result: EscalationResult) -> str:
    lines = [
        f"Job            : {result.job_name}",
        f"Consec. failures: {result.consecutive_failures}",
        f"Triggered      : {result.triggered}",
        f"Message        : {result.message}",
    ]
    if result.triggered and result.contacts:
        lines.append(f"Notify         : {', '.join(result.contacts)}")
    return "\n".join(lines)
