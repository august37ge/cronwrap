"""Tests for cronwrap.backoff."""
from __future__ import annotations

import argparse

import pytest

from cronwrap.backoff import (
    BackoffResult,
    backoff_sequence,
    compute_backoff,
    render_backoff_result,
)
from cronwrap.cli_backoff import add_backoff_subparser, run_backoff


# ---------------------------------------------------------------------------
# compute_backoff
# ---------------------------------------------------------------------------

def test_first_attempt_equals_base():
    result = compute_backoff(attempt=1, base_seconds=2.0, multiplier=2.0, jitter=False)
    assert result.delay_seconds == 2.0
    assert result.attempt == 1
    assert not result.capped


def test_second_attempt_doubles():
    result = compute_backoff(attempt=2, base_seconds=1.0, multiplier=2.0, jitter=False)
    assert result.delay_seconds == 2.0


def test_delay_is_capped():
    result = compute_backoff(
        attempt=10, base_seconds=1.0, multiplier=2.0, max_seconds=10.0, jitter=False
    )
    assert result.delay_seconds == 10.0
    assert result.capped


def test_attempt_below_one_treated_as_one():
    r_zero = compute_backoff(attempt=0, base_seconds=1.0, jitter=False)
    r_one = compute_backoff(attempt=1, base_seconds=1.0, jitter=False)
    assert r_zero.delay_seconds == r_one.delay_seconds


def test_jitter_within_bounds():
    for attempt in range(1, 6):
        r = compute_backoff(attempt=attempt, base_seconds=1.0, multiplier=2.0,
                            max_seconds=60.0, jitter=True)
        assert 0.0 <= r.delay_seconds <= 60.0
        assert r.jittered


def test_seed_is_deterministic():
    r1 = compute_backoff(attempt=3, jitter=True, seed=42)
    r2 = compute_backoff(attempt=3, jitter=True, seed=42)
    assert r1.delay_seconds == r2.delay_seconds


def test_no_jitter_flag():
    result = compute_backoff(attempt=1, base_seconds=5.0, jitter=False)
    assert not result.jittered
    assert result.delay_seconds == 5.0


# ---------------------------------------------------------------------------
# backoff_sequence
# ---------------------------------------------------------------------------

def test_sequence_length():
    seq = backoff_sequence(max_attempts=4, jitter=False)
    assert len(seq) == 4


def test_sequence_delays_increase():
    seq = backoff_sequence(max_attempts=5, base_seconds=1.0, multiplier=2.0, jitter=False)
    delays = [r.delay_seconds for r in seq]
    assert delays == sorted(delays)


# ---------------------------------------------------------------------------
# render_backoff_result
# ---------------------------------------------------------------------------

def test_render_contains_attempt_and_delay():
    r = BackoffResult(attempt=2, delay_seconds=4.0, capped=False, jittered=False)
    text = render_backoff_result(r)
    assert "2" in text
    assert "4.0" in text


def test_render_shows_capped():
    r = BackoffResult(attempt=5, delay_seconds=300.0, capped=True, jittered=False)
    assert "capped" in render_backoff_result(r)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = dict(attempts=3, base_seconds=1.0, multiplier=2.0,
                    max_seconds=60.0, no_jitter=True)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_backoff_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_backoff_subparser(sub)
    ns = parser.parse_args(["backoff", "--attempts", "2", "--no-jitter"])
    assert ns.attempts == 2


def test_run_backoff_returns_zero(capsys):
    ns = _make_namespace(attempts=3)
    code = run_backoff(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "Attempt" in out


def test_run_backoff_zero_attempts(capsys):
    ns = _make_namespace(attempts=0)
    code = run_backoff(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "No attempts" in out
