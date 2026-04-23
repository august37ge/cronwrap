"""Tests for cronwrap.dependency."""

from __future__ import annotations

import sqlite3
import tempfile
import os
from datetime import datetime, timezone

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.dependency import (
    check_dependency,
    render_dependency_result,
    DependencyResult,
)


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "hist.db")
    init_db(p)
    return p


def _rec(job: str, exit_code: int, db_path: str) -> None:
    record_run(
        JobRecord(
            job_name=job,
            started_at=datetime.now(timezone.utc).isoformat(),
            duration=1.0,
            exit_code=exit_code,
            stdout="",
            stderr="",
            retries=0,
            tags="",
        ),
        db_path=db_path,
    )


def test_ok_when_all_deps_succeeded(db_path):
    _rec("upstream_a", 0, db_path)
    _rec("upstream_b", 0, db_path)
    result = check_dependency("my_job", ["upstream_a", "upstream_b"], db_path)
    assert result.ok is True
    assert result.blocking_jobs == []
    assert result.missing_jobs == []


def test_blocked_when_dep_failed(db_path):
    _rec("upstream_a", 0, db_path)
    _rec("upstream_b", 1, db_path)
    result = check_dependency("my_job", ["upstream_a", "upstream_b"], db_path)
    assert result.ok is False
    assert "upstream_b" in result.blocking_jobs
    assert result.missing_jobs == []


def test_missing_when_dep_never_ran(db_path):
    result = check_dependency("my_job", ["ghost_job"], db_path)
    assert result.ok is False
    assert "ghost_job" in result.missing_jobs


def test_render_ok(db_path):
    _rec("up", 0, db_path)
    result = check_dependency("j", ["up"], db_path)
    text = render_dependency_result(result)
    assert "satisfied" in text


def test_render_blocked(db_path):
    _rec("up", 1, db_path)
    result = check_dependency("j", ["up"], db_path)
    text = render_dependency_result(result)
    assert "BLOCKED" in text
    assert "up" in text


def test_render_missing(db_path):
    result = check_dependency("j", ["ghost"], db_path)
    text = render_dependency_result(result)
    assert "No history" in text
    assert "ghost" in text
