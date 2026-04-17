"""Tests for cronwrap.watchdog."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from cronwrap.history import _connect, init_db, record_run, JobRecord
from cronwrap.watchdog import (
    check_job_watchdog,
    check_all_watchdog,
    render_watchdog_report,
    WatchdogAlert,
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


def _insert(db_path, name, started_at, success=True):
    conn = _connect(db_path)
    init_db(conn)
    rec = JobRecord(
        job_name=name,
        started_at=started_at,
        duration_seconds=1.0,
        exit_code=0 if success else 1,
        success=success,
        output="",
    )
    record_run(conn, rec)
    conn.close()


def test_no_alert_when_not_overdue(db_path):
    with patch("cronwrap.watchdog.is_overdue", return_value=False):
        result = check_job_watchdog(db_path, "myjob", "* * * * *")
    assert result is None


def test_alert_when_overdue_never_run(db_path):
    with patch("cronwrap.watchdog.is_overdue", return_value=True), \
         patch("cronwrap.watchdog.next_run_time", return_value=None):
        result = check_job_watchdog(db_path, "myjob", "0 * * * *")
    assert isinstance(result, WatchdogAlert)
    assert result.last_run is None
    assert "never" in result.message


def test_alert_includes_last_run(db_path):
    ts = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    _insert(db_path, "backupjob", ts)
    with patch("cronwrap.watchdog.is_overdue", return_value=True), \
         patch("cronwrap.watchdog.next_run_time", return_value=None):
        result = check_job_watchdog(db_path, "backupjob", "0 2 * * *")
    assert result is not None
    assert result.last_run is not None


def test_check_all_watchdog_filters_overdue(db_path):
    jobs = [
        {"name": "job_a", "schedule": "* * * * *"},
        {"name": "job_b", "schedule": "0 0 * * *"},
    ]
    with patch("cronwrap.watchdog.is_overdue", side_effect=[False, True]), \
         patch("cronwrap.watchdog.next_run_time", return_value=None):
        alerts = check_all_watchdog(db_path, jobs)
    assert len(alerts) == 1
    assert alerts[0].job_name == "job_b"


def test_render_no_alerts():
    out = render_watchdog_report([])
    assert "on schedule" in out


def test_render_with_alerts():
    alert = WatchdogAlert(
        job_name="slow_job",
        schedule="*/5 * * * *",
        last_run=None,
        overdue_by_seconds=300.0,
        message="Job 'slow_job' is overdue.",
    )
    out = render_watchdog_report([alert])
    assert "slow_job" in out
    assert "300" in out
