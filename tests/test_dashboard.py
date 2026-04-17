"""Tests for cronwrap.dashboard"""
import datetime
import os
import pytest

from cronwrap.history import init_db, record_run
from cronwrap.history import JobRecord
from cronwrap.dashboard import build_dashboard, render_dashboard, DashboardRow


@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _rec(job, exit_code=0, duration=1.0, ts=None):
    if ts is None:
        ts = datetime.datetime.utcnow().isoformat()
    return JobRecord(job_name=job, exit_code=exit_code, duration=duration,
                     stdout="ok", stderr="", timestamp=ts, attempt=1)


def test_build_dashboard_empty(db_path):
    rows = build_dashboard(db_path, [])
    assert rows == []


def test_build_dashboard_with_data(db_path):
    record_run(db_path, _rec("alpha", exit_code=0, duration=2.5))
    record_run(db_path, _rec("alpha", exit_code=1, duration=1.0))
    record_run(db_path, _rec("beta", exit_code=0, duration=0.5))

    rows = build_dashboard(db_path, [])
    assert len(rows) == 2
    names = [r.job_name for r in rows]
    assert names == sorted(names)

    alpha = next(r for r in rows if r.job_name == "alpha")
    assert alpha.total_runs == 2
    assert alpha.success_rate == pytest.approx(0.5)
    assert alpha.avg_duration == pytest.approx(1.75)


def test_render_dashboard_no_rows():
    out = render_dashboard([])
    assert "No job data" in out


def test_render_dashboard_shows_job(db_path):
    record_run(db_path, _rec("myjob", exit_code=0, duration=3.0))
    rows = build_dashboard(db_path, [])
    out = render_dashboard(rows)
    assert "myjob" in out
    assert "100.0%" in out


def test_render_dashboard_overdue_flag():
    row = DashboardRow(
        job_name="latejob", total_runs=1, success_rate=1.0,
        avg_duration=1.0, last_exit=0, overdue=True, next_run=None
    )
    out = render_dashboard([row])
    assert "YES" in out
