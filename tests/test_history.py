"""Tests for cronwrap.history module."""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from cronwrap.history import JobRecord, record_run, get_recent_runs, last_run, init_db


@pytest.fixture
def db_path(tmp_path) -> Path:
    return tmp_path / "test_history.db"


def make_record(job_name="test_job", success=True, exit_code=0, attempt=1) -> JobRecord:
    now = datetime.now(timezone.utc).isoformat()
    return JobRecord(
        job_name=job_name, command="echo hello",
        started_at=now, finished_at=now,
        exit_code=exit_code, success=success,
        stdout="hello", stderr="", attempt=attempt,
    )


def test_init_db_creates_table(db_path):
    init_db(db_path)
    assert db_path.exists()


def test_record_and_retrieve(db_path):
    rec = make_record()
    row_id = record_run(rec, db_path=db_path)
    assert row_id == 1
    runs = get_recent_runs("test_job", db_path=db_path)
    assert len(runs) == 1
    assert runs[0].success is True
    assert runs[0].exit_code == 0


def test_get_recent_runs_limit(db_path):
    for i in range(5):
        record_run(make_record(), db_path=db_path)
    runs = get_recent_runs("test_job", limit=3, db_path=db_path)
    assert len(runs) == 3


def test_last_run_returns_most_recent(db_path):
    record_run(make_record(success=False, exit_code=1), db_path=db_path)
    record_run(make_record(success=True, exit_code=0), db_path=db_path)
    latest = last_run("test_job", db_path=db_path)
    assert latest is not None
    assert latest.success is True


def test_last_run_no_records(db_path):
    result = last_run("nonexistent", db_path=db_path)
    assert result is None


def test_separate_jobs_isolated(db_path):
    record_run(make_record(job_name="job_a"), db_path=db_path)
    record_run(make_record(job_name="job_b"), db_path=db_path)
    assert len(get_recent_runs("job_a", db_path=db_path)) == 1
    assert len(get_recent_runs("job_b", db_path=db_path)) == 1
