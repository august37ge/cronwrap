"""Integration tests for cronwrap.report.print_report."""
from __future__ import annotations

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.report import print_report, render_text_report
from cronwrap.metrics import get_all_job_metrics


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "report.db")
    init_db(p)
    return p


def _rec(name, code, dur):
    return JobRecord(
        job_name=name,
        started_at="2024-06-01T12:00:00",
        duration_seconds=dur,
        exit_code=code,
        stdout="ok",
        stderr="",
        retries=0,
    )


def test_print_report_no_history(db_path, capsys):
    print_report(db_path)
    out = capsys.readouterr().out
    assert "No job history found" in out


def test_print_report_shows_jobs(db_path, capsys):
    record_run(db_path, _rec("cleanup", 0, 10.5))
    record_run(db_path, _rec("cleanup", 1, 2.0))
    print_report(db_path)
    out = capsys.readouterr().out
    assert "cleanup" in out
    assert "50.0" in out  # 50% success rate


def test_report_sorted_alphabetically(db_path):
    record_run(db_path, _rec("zebra", 0, 1.0))
    record_run(db_path, _rec("alpha", 0, 1.0))
    metrics = get_all_job_metrics(db_path)
    report = render_text_report(metrics)
    alpha_pos = report.index("alpha")
    zebra_pos = report.index("zebra")
    assert alpha_pos < zebra_pos


def test_report_respects_limit(db_path):
    for i in range(10):
        record_run(db_path, _rec("job", 0 if i < 8 else 1, float(i)))
    metrics = get_all_job_metrics(db_path, limit=5)
    assert metrics[0].total_runs == 5
