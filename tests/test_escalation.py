"""Tests for cronwrap.escalation."""
from __future__ import annotations

import pytest

from cronwrap.escalation import (
    EscalationLevel,
    _count_consecutive_failures,
    _pick_level,
    check_escalation,
    render_escalation_result,
)
from cronwrap.history import init_db, record_run
from cronwrap.runner import RunResult


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(db_path=p)
    return p


def _rec(job: str, exit_code: int, db_path: str) -> None:
    r = RunResult(
        exit_code=exit_code,
        stdout="out",
        stderr="err",
        duration=1.0,
        attempts=1,
    )
    record_run(job, r, db_path=db_path)


# ---------------------------------------------------------------------------
# _count_consecutive_failures
# ---------------------------------------------------------------------------

def test_no_failures_returns_zero(db_path):
    _rec("myjob", 0, db_path)
    assert _count_consecutive_failures("myjob", db_path) == 0


def test_counts_unbroken_streak(db_path):
    for _ in range(3):
        _rec("myjob", 1, db_path)
    assert _count_consecutive_failures("myjob", db_path) == 3


def test_streak_broken_by_success(db_path):
    _rec("myjob", 0, db_path)   # success first (oldest)
    _rec("myjob", 1, db_path)   # then two failures
    _rec("myjob", 1, db_path)
    # most-recent runs come first from get_recent_runs
    assert _count_consecutive_failures("myjob", db_path) == 2


def test_unknown_job_returns_zero(db_path):
    assert _count_consecutive_failures("ghost", db_path) == 0


# ---------------------------------------------------------------------------
# _pick_level
# ---------------------------------------------------------------------------

def test_pick_level_none_when_below_all_thresholds():
    levels = [EscalationLevel(3, ["ops"], "warn")]
    assert _pick_level(2, levels) is None


def test_pick_level_returns_highest_applicable():
    warn = EscalationLevel(2, ["dev"], "warn")
    crit = EscalationLevel(5, ["ops"], "critical")
    assert _pick_level(5, [warn, crit]) is crit
    assert _pick_level(3, [warn, crit]) is warn


# ---------------------------------------------------------------------------
# check_escalation
# ---------------------------------------------------------------------------

def test_not_triggered_when_below_threshold(db_path):
    _rec("j", 1, db_path)
    levels = [EscalationLevel(3, ["ops"])]
    result = check_escalation("j", levels, db_path=db_path)
    assert not result.triggered
    assert result.consecutive_failures == 1


def test_triggered_at_threshold(db_path):
    for _ in range(3):
        _rec("j", 1, db_path)
    levels = [EscalationLevel(3, ["ops", "dev"], "critical")]
    result = check_escalation("j", levels, db_path=db_path)
    assert result.triggered
    assert result.contacts == ["ops", "dev"]
    assert "critical" in result.message


def test_render_includes_job_name(db_path):
    levels = [EscalationLevel(1, ["alice"], "warn")]
    _rec("render-job", 1, db_path)
    result = check_escalation("render-job", levels, db_path=db_path)
    text = render_escalation_result(result)
    assert "render-job" in text
    assert "alice" in text
