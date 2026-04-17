"""Tests for cronwrap.tag_report."""
import os
import tempfile
import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.tags import build_tag_index
from cronwrap.tag_report import metrics_by_tag, render_tag_report


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    init_db(path)
    yield path
    os.unlink(path)


def _rec(job, success=True, duration=1.0):
    return JobRecord(
        job_name=job, success=success, exit_code=0 if success else 1,
        duration_s=duration, output="ok", retries=0,
    )


JOBS = [
    {"name": "backup", "tags": ["daily"]},
    {"name": "report", "tags": ["daily", "email"]},
]


def test_metrics_by_tag_empty(db_path):
    idx = build_tag_index(JOBS)
    result = metrics_by_tag(idx, db_path)
    assert result["daily"] == []
    assert result["email"] == []


def test_metrics_by_tag_with_data(db_path):
    record_run(db_path, _rec("backup", duration=2.0))
    record_run(db_path, _rec("report", duration=3.0))
    idx = build_tag_index(JOBS)
    result = metrics_by_tag(idx, db_path)
    daily_names = {m.job_name for m in result["daily"]}
    assert daily_names == {"backup", "report"}
    email_names = {m.job_name for m in result["email"]}
    assert email_names == {"report"}


def test_render_tag_report_no_data():
    text = render_tag_report({})
    assert "No tag data" in text


def test_render_tag_report_with_data(db_path):
    record_run(db_path, _rec("backup", duration=5.0))
    idx = build_tag_index(JOBS)
    tag_metrics = metrics_by_tag(idx, db_path)
    text = render_tag_report(tag_metrics)
    assert "[daily]" in text
    assert "backup" in text
    assert "runs=1" in text
