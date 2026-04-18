"""Tests for cronwrap.ratelimit."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.ratelimit import check_rate_limit, render_rate_limit_result


@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "history.db")
    init_db(p)
    return p


def _rec(job_name: str, started_at: datetime, success: bool = True, duration: float = 1.0) -> JobRecord:
    return JobRecord(
        job_name=job_name,
        started_at=started_at.isoformat(),
        duration_seconds=duration,
        exit_code=0 if success else 1,
        success=success,
        output="ok",
    )


def test_allowed_when_no_history(db_path):
    result = check_rate_limit(db_path, "myjob", min_interval_seconds=300)
    assert result.allowed is True
    assert result.last_run is None
    assert result.seconds_remaining == 0.0


def test_allowed_when_interval_passed(db_path):
    old = datetime.utcnow() - timedelta(seconds=400)
    record_run(db_path, _rec("myjob", old))
    result = check_rate_limit(db_path, "myjob", min_interval_seconds=300)
    assert result.allowed is True
    assert result.seconds_remaining == 0.0


def test_blocked_when_too_recent(db_path):
    recent = datetime.utcnow() - timedelta(seconds=60)
    record_run(db_path, _rec("myjob", recent))
    result = check_rate_limit(db_path, "myjob", min_interval_seconds=300)
    assert result.allowed is False
    assert result.seconds_remaining > 0


def test_render_allowed(db_path):
    result = check_rate_limit(db_path, "myjob", min_interval_seconds=300)
    text = render_rate_limit_result(result)
    assert "allowed" in text
    assert "myjob" in text


def test_render_blocked(db_path):
    recent = datetime.utcnow() - timedelta(seconds=10)
    record_run(db_path, _rec("myjob", recent))
    result = check_rate_limit(db_path, "myjob", min_interval_seconds=300)
    text = render_rate_limit_result(result)
    assert "rate limited" in text
    assert "remaining" in text
