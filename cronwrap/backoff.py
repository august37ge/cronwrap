"""Exponential backoff calculation for retry logic."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class BackoffResult:
    attempt: int
    delay_seconds: float
    capped: bool
    jittered: bool

    def __str__(self) -> str:
        cap_note = " (capped)" if self.capped else ""
        jitter_note = " (jittered)" if self.jittered else ""
        return (
            f"Attempt {self.attempt}: wait {self.delay_seconds:.2f}s"
            f"{cap_note}{jitter_note}"
        )


def compute_backoff(
    attempt: int,
    base_seconds: float = 1.0,
    multiplier: float = 2.0,
    max_seconds: float = 300.0,
    jitter: bool = True,
    seed: Optional[int] = None,
) -> BackoffResult:
    """Compute exponential backoff delay for a given attempt number (1-based).

    Args:
        attempt: The current attempt number (1 = first retry).
        base_seconds: Base delay in seconds.
        multiplier: Exponential growth factor.
        max_seconds: Upper bound on delay.
        jitter: Whether to apply full jitter (uniform random in [0, delay]).
        seed: Optional RNG seed for deterministic results.

    Returns:
        BackoffResult with the computed delay.
    """
    if attempt < 1:
        attempt = 1

    raw = base_seconds * (multiplier ** (attempt - 1))
    capped = raw > max_seconds
    delay = min(raw, max_seconds)

    if jitter:
        rng = random.Random(seed)
        delay = rng.uniform(0, delay)

    return BackoffResult(
        attempt=attempt,
        delay_seconds=round(delay, 4),
        capped=capped,
        jittered=jitter,
    )


def render_backoff_result(result: BackoffResult) -> str:
    """Return a human-readable string for a BackoffResult."""
    return str(result)


def backoff_sequence(
    max_attempts: int,
    base_seconds: float = 1.0,
    multiplier: float = 2.0,
    max_seconds: float = 300.0,
    jitter: bool = False,
) -> list[BackoffResult]:
    """Return a list of BackoffResult for each attempt up to max_attempts."""
    return [
        compute_backoff(
            attempt=i,
            base_seconds=base_seconds,
            multiplier=multiplier,
            max_seconds=max_seconds,
            jitter=jitter,
        )
        for i in range(1, max_attempts + 1)
    ]
