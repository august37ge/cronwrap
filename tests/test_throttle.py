"""Tests for cronwrap.throttle."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.throttle import check_throttle, render_throttle_result


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _rec(job_name: str, started_at: str, success: bool = True) -> JobRecord:
    return JobRecord(
        job_name=job_name,
        started_at=started_at,
        duration_seconds=1.0,
        exit_code=0 if success else 1,
        success=success,
        output="",
    )


def test_allowed_when_no_history(db_path):
    result = check_throttle("myjob", min_interval_seconds=300, db_path=db_path)
    assert result.allowed is True
    assert result.last_run is None
    assert result.seconds_remaining == 0.0


def test_allowed_when_interval_passed(db_path):
    old = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat()
    record_run(_rec("myjob", old), db_path=db_path)
    result = check_throttle("myjob", min_interval_seconds=300, db_path=db_path)
    assert result.allowed is True
    assert result.seconds_remaining == 0.0


def test_blocked_when_too_recent(db_path):
    recent = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    record_run(_rec("myjob", recent), db_path=db_path)
    result = check_throttle("myjob", min_interval_seconds=300, db_path=db_path)
    assert result.allowed is False
    assert result.seconds_remaining > 0
    assert result.seconds_remaining <= 240 + 2  # allow small timing slack


def test_render_allowed(db_path):
    result = check_throttle("myjob", min_interval_seconds=300, db_path=db_path)
    msg = render_throttle_result(result)
    assert "allowed" in msg
    assert "myjob" in msg


def test_render_blocked(db_path):
    recent = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    record_run(_rec("myjob", recent), db_path=db_path)
    result = check_throttle("myjob", min_interval_seconds=300, db_path=db_path)
    msg = render_throttle_result(result)
    assert "throttled" in msg
    assert "myjob" in msg


def test_different_jobs_independent(db_path):
    recent = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    record_run(_rec("job-a", recent), db_path=db_path)
    result_a = check_throttle("job-a", min_interval_seconds=300, db_path=db_path)
    result_b = check_throttle("job-b", min_interval_seconds=300, db_path=db_path)
    assert result_a.allowed is False
    assert result_b.allowed is True
