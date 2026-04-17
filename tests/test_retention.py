"""Tests for cronwrap.retention pruning logic."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.history import init_db, record_run, get_recent_runs
from cronwrap.history import JobRecord
from cronwrap.retention import prune_job, prune_all, prune_from_config


@pytest.fixture()
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    init_db(path)
    yield path
    os.unlink(path)


def _rec(job_name: str, days_ago: int, success: bool = True) -> JobRecord:
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return JobRecord(
        job_name=job_name,
        started_at=ts,
        duration_seconds=1.0,
        exit_code=0 if success else 1,
        success=success,
        stdout="",
        stderr="",
        attempt=1,
    )


def test_prune_job_removes_old_records(db_path):
    record_run(db_path, _rec("job_a", days_ago=40))
    record_run(db_path, _rec("job_a", days_ago=5))
    result = prune_job(db_path, "job_a", keep_days=30)
    assert result.rows_deleted == 1
    assert result.job_name == "job_a"
    remaining = get_recent_runs(db_path, "job_a", limit=10)
    assert len(remaining) == 1


def test_prune_job_does_not_touch_other_jobs(db_path):
    record_run(db_path, _rec("job_a", days_ago=40))
    record_run(db_path, _rec("job_b", days_ago=40))
    prune_job(db_path, "job_a", keep_days=30)
    remaining_b = get_recent_runs(db_path, "job_b", limit=10)
    assert len(remaining_b) == 1


def test_prune_all_removes_across_jobs(db_path):
    record_run(db_path, _rec("job_a", days_ago=40))
    record_run(db_path, _rec("job_b", days_ago=40))
    record_run(db_path, _rec("job_a", days_ago=1))
    result = prune_all(db_path, keep_days=30)
    assert result.rows_deleted == 2
    assert result.job_name is None


def test_prune_from_config(db_path):
    record_run(db_path, _rec("alpha", days_ago=60))
    record_run(db_path, _rec("beta", days_ago=10))
    jobs = [{"name": "alpha", "keep_days": 30}, {"name": "beta", "keep_days": 30}]
    results = prune_from_config(db_path, jobs)
    assert len(results) == 2
    deleted = {r.job_name: r.rows_deleted for r in results}
    assert deleted["alpha"] == 1
    assert deleted["beta"] == 0


def test_prune_nothing_when_all_recent(db_path):
    record_run(db_path, _rec("job_a", days_ago=1))
    result = prune_job(db_path, "job_a", keep_days=30)
    assert result.rows_deleted == 0
