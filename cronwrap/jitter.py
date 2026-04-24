"""Jitter support — add randomised delay before running a cron job to
avoide thundering-herd problems when many jobs share the same schedule."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class JitterResult:
    job_name: str
    requested_max_seconds: int
    actual_delay_seconds: float
    skipped: bool  # True when max_seconds <= 0


def compute_jitter(max_seconds: int, *, seed: Optional[int] = None) -> float:
    """Return a random delay in [0, max_seconds].

    Args:
        max_seconds: Upper bound for the random delay.  Values <= 0 produce 0.
        seed: Optional RNG seed (useful in tests).
    """
    if max_seconds <= 0:
        return 0.0
    rng = random.Random(seed)
    return rng.uniform(0, max_seconds)


def apply_jitter(
    job_name: str,
    max_seconds: int,
    *,
    seed: Optional[int] = None,
    _sleep=time.sleep,
) -> JitterResult:
    """Sleep for a random duration up to *max_seconds* and return a result.

    The *_sleep* parameter is injectable for testing.
    """
    if max_seconds <= 0:
        return JitterResult(
            job_name=job_name,
            requested_max_seconds=max_seconds,
            actual_delay_seconds=0.0,
            skipped=True,
        )

    delay = compute_jitter(max_seconds, seed=seed)
    _sleep(delay)
    return JitterResult(
        job_name=job_name,
        requested_max_seconds=max_seconds,
        actual_delay_seconds=delay,
        skipped=False,
    )


def render_jitter_result(result: JitterResult) -> str:
    """Return a human-readable summary of a JitterResult."""
    if result.skipped:
        return f"[jitter] {result.job_name}: jitter disabled (max_seconds={result.requested_max_seconds})"
    return (
        f"[jitter] {result.job_name}: slept {result.actual_delay_seconds:.2f}s "
        f"(max={result.requested_max_seconds}s)"
    )
