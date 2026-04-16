"""Tests for cronwrap.metrics and cronwrap.report."""
from __future__ import annotations

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.metrics import get_job_metrics, get_all_job_metrics
from cronwrap.report import render_text_report


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _rec(job_name, exit_code, duration):
    return JobRecord(
        job_name=job_name,
        started_at="2024-01-01T00:00:00",
        duration_seconds=duration,
        exit_code=exit_code,
        stdout="",
        stderr="",
        retries=0,
    )


def test_no_metrics_for_unknown_job(db_path):
    assert get_job_metrics(db_path, "ghost") is None


def test_metrics_counts(db_path):
    record_run(db_path, _rec("backup", 0, 2.0))
    record_run(db_path, _rec("backup", 0, 4.0))
    record_run(db_path, _rec("backup", 1, 1.0))

    m = get_job_metrics(db_path, "backup")
    assert m is not None
    assert m.total_runs == 3
    assert m.successful_runs == 2
    assert m.failed_runs == 1


def test_metrics_avg_and_max(db_path):
    record_run(db_path, _rec("sync", 0, 3.0))
    record_run(db_path, _rec("sync", 0, 7.0))

    m = get_job_metrics(db_path, "sync")
    assert m.avg_duration_seconds == 5.0
    assert m.max_duration_seconds == 7.0


def test_success_rate(db_path):
    for _ in range(3):
        record_run(db_path, _rec("job", 0, 1.0))
    record_run(db_path, _rec("job", 1, 1.0))

    m = get_job_metrics(db_path, "job")
    assert m.success_rate == 75.0


def test_get_all_job_metrics(db_path):
    record_run(db_path, _rec("a", 0, 1.0))
    record_run(db_path, _rec("b", 1, 2.0))

    all_m = get_all_job_metrics(db_path)
    names = {m.job_name for m in all_m}
    assert names == {"a", "b"}


def test_render_text_report_empty():
    assert render_text_report([]) == "No job history found."


def test_render_text_report_contains_job_name(db_path):
    record_run(db_path, _rec("myjob", 0, 5.0))
    from cronwrap.metrics import get_all_job_metrics as gam
    report = render_text_report(gam(db_path))
    assert "myjob" in report
    assert "100.0" in report
