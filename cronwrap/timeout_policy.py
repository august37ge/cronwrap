"""Timeout policy: define per-job timeout rules and evaluate whether a run exceeded them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TimeoutPolicy:
    job_name: str
    warn_seconds: Optional[float]  # emit a warning but still succeed
    kill_seconds: Optional[float]  # hard limit; run is treated as failed


@dataclass
class TimeoutEvaluation:
    job_name: str
    duration_seconds: float
    warn_seconds: Optional[float]
    kill_seconds: Optional[float]
    exceeded_warn: bool
    exceeded_kill: bool
    message: str


def evaluate_timeout(policy: TimeoutPolicy, duration_seconds: float) -> TimeoutEvaluation:
    """Evaluate a completed run's duration against the given policy."""
    exceeded_kill = (
        policy.kill_seconds is not None and duration_seconds > policy.kill_seconds
    )
    exceeded_warn = (
        not exceeded_kill
        and policy.warn_seconds is not None
        and duration_seconds > policy.warn_seconds
    )

    if exceeded_kill:
        msg = (
            f"Job '{policy.job_name}' exceeded kill timeout "
            f"({duration_seconds:.2f}s > {policy.kill_seconds:.2f}s)."
        )
    elif exceeded_warn:
        msg = (
            f"Job '{policy.job_name}' exceeded warn threshold "
            f"({duration_seconds:.2f}s > {policy.warn_seconds:.2f}s)."
        )
    else:
        msg = (
            f"Job '{policy.job_name}' completed within timeout "
            f"({duration_seconds:.2f}s)."
        )

    return TimeoutEvaluation(
        job_name=policy.job_name,
        duration_seconds=duration_seconds,
        warn_seconds=policy.warn_seconds,
        kill_seconds=policy.kill_seconds,
        exceeded_warn=exceeded_warn,
        exceeded_kill=exceeded_kill,
        message=msg,
    )


def render_timeout_evaluation(ev: TimeoutEvaluation) -> str:
    """Return a human-readable string describing the evaluation."""
    status = "KILL" if ev.exceeded_kill else ("WARN" if ev.exceeded_warn else "OK")
    lines = [
        f"[{status}] {ev.message}",
        f"  duration : {ev.duration_seconds:.2f}s",
    ]
    if ev.warn_seconds is not None:
        lines.append(f"  warn_at  : {ev.warn_seconds:.2f}s")
    if ev.kill_seconds is not None:
        lines.append(f"  kill_at  : {ev.kill_seconds:.2f}s")
    return "\n".join(lines)


def policy_from_config(job_name: str, cfg: dict) -> TimeoutPolicy:
    """Build a TimeoutPolicy from a job config dict.

    Expected keys (both optional):
      ``warn_timeout_seconds`` and ``kill_timeout_seconds``.
    """
    return TimeoutPolicy(
        job_name=job_name,
        warn_seconds=cfg.get("warn_timeout_seconds"),
        kill_seconds=cfg.get("kill_timeout_seconds"),
    )
