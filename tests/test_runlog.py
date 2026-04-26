"""Tests for cronwrap.runlog."""
from __future__ import annotations

import os
import tempfile

import pytest

from cronwrap.runlog import (
    RunLogEntry,
    append_run,
    get_run_log,
    init_runlog_db,
    summarise_run_log,
)


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "runlog.db")
    init_runlog_db(p)
    return p


def _entry(job="backup", exit_code=0, duration=1.5, attempt=1) -> RunLogEntry:
    return RunLogEntry(
        job_name=job,
        started_at="2024-06-01T10:00:00",
        finished_at="2024-06-01T10:00:01",
        exit_code=exit_code,
        duration_s=duration,
        stdout="ok",
        stderr="",
        attempt=attempt,
    )


def test_init_creates_table(db_path):
    # calling init again should not raise
    init_runlog_db(db_path)
    entries = get_run_log(db_path)
    assert entries == []


def test_append_and_retrieve(db_path):
    append_run(db_path, _entry())
    entries = get_run_log(db_path)
    assert len(entries) == 1
    assert entries[0].job_name == "backup"
    assert entries[0].exit_code == 0
    assert entries[0].duration_s == 1.5


def test_filter_by_job_name(db_path):
    append_run(db_path, _entry(job="backup"))
    append_run(db_path, _entry(job="cleanup"))
    results = get_run_log(db_path, job_name="cleanup")
    assert len(results) == 1
    assert results[0].job_name == "cleanup"


def test_failed_only_filter(db_path):
    append_run(db_path, _entry(exit_code=0))
    append_run(db_path, _entry(exit_code=1))
    append_run(db_path, _entry(exit_code=2))
    results = get_run_log(db_path, failed_only=True)
    assert len(results) == 2
    assert all(e.exit_code != 0 for e in results)


def test_limit_respected(db_path):
    for i in range(10):
        append_run(db_path, _entry())
    results = get_run_log(db_path, limit=3)
    assert len(results) == 3


def test_summarise_empty():
    summary = summarise_run_log([])
    assert summary["total"] == 0
    assert summary["success_rate"] is None
    assert summary["avg_duration_s"] is None


def test_summarise_all_success():
    entries = [_entry(exit_code=0, duration=2.0) for _ in range(4)]
    summary = summarise_run_log(entries)
    assert summary["total"] == 4
    assert summary["failures"] == 0
    assert summary["success_rate"] == 100.0
    assert summary["avg_duration_s"] == 2.0


def test_summarise_mixed():
    entries = [
        _entry(exit_code=0, duration=1.0),
        _entry(exit_code=1, duration=3.0),
    ]
    summary = summarise_run_log(entries)
    assert summary["failures"] == 1
    assert summary["success_rate"] == 50.0
    assert summary["avg_duration_s"] == 2.0


def test_attempt_stored(db_path):
    append_run(db_path, _entry(attempt=3))
    entries = get_run_log(db_path)
    assert entries[0].attempt == 3
