"""Tests for cronwrap.timeout_policy."""

import pytest

from cronwrap.timeout_policy import (
    TimeoutPolicy,
    evaluate_timeout,
    policy_from_config,
    render_timeout_evaluation,
)


def _policy(warn=None, kill=None):
    return TimeoutPolicy(job_name="backup", warn_seconds=warn, kill_seconds=kill)


# ---------------------------------------------------------------------------
# evaluate_timeout
# ---------------------------------------------------------------------------

def test_within_limits_no_flags():
    ev = evaluate_timeout(_policy(warn=30.0, kill=60.0), duration_seconds=10.0)
    assert not ev.exceeded_warn
    assert not ev.exceeded_kill
    assert "OK" in ev.message


def test_exceeds_warn_only():
    ev = evaluate_timeout(_policy(warn=10.0, kill=60.0), duration_seconds=15.0)
    assert ev.exceeded_warn
    assert not ev.exceeded_kill
    assert "warn" in ev.message.lower()


def test_exceeds_kill_supersedes_warn():
    ev = evaluate_timeout(_policy(warn=10.0, kill=20.0), duration_seconds=25.0)
    assert not ev.exceeded_warn  # kill takes precedence
    assert ev.exceeded_kill
    assert "kill" in ev.message.lower()


def test_no_policy_set():
    ev = evaluate_timeout(_policy(), duration_seconds=999.0)
    assert not ev.exceeded_warn
    assert not ev.exceeded_kill


def test_exactly_at_warn_boundary_not_exceeded():
    # strictly greater-than semantics
    ev = evaluate_timeout(_policy(warn=30.0), duration_seconds=30.0)
    assert not ev.exceeded_warn


def test_just_above_warn_boundary():
    ev = evaluate_timeout(_policy(warn=30.0), duration_seconds=30.001)
    assert ev.exceeded_warn


# ---------------------------------------------------------------------------
# render_timeout_evaluation
# ---------------------------------------------------------------------------

def test_render_ok_contains_ok_label():
    ev = evaluate_timeout(_policy(warn=60.0, kill=120.0), duration_seconds=5.0)
    rendered = render_timeout_evaluation(ev)
    assert "[OK]" in rendered
    assert "5.00s" in rendered


def test_render_warn_contains_warn_label():
    ev = evaluate_timeout(_policy(warn=5.0), duration_seconds=10.0)
    rendered = render_timeout_evaluation(ev)
    assert "[WARN]" in rendered


def test_render_kill_contains_kill_label():
    ev = evaluate_timeout(_policy(kill=5.0), duration_seconds=10.0)
    rendered = render_timeout_evaluation(ev)
    assert "[KILL]" in rendered


def test_render_omits_warn_line_when_not_set():
    ev = evaluate_timeout(_policy(kill=5.0), duration_seconds=1.0)
    rendered = render_timeout_evaluation(ev)
    assert "warn_at" not in rendered


# ---------------------------------------------------------------------------
# policy_from_config
# ---------------------------------------------------------------------------

def test_policy_from_full_config():
    cfg = {"warn_timeout_seconds": 30, "kill_timeout_seconds": 90}
    p = policy_from_config("etl", cfg)
    assert p.job_name == "etl"
    assert p.warn_seconds == 30
    assert p.kill_seconds == 90


def test_policy_from_empty_config():
    p = policy_from_config("etl", {})
    assert p.warn_seconds is None
    assert p.kill_seconds is None
