"""Tests for cronwrap.quota."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cronwrap.quota import (
    QuotaResult,
    check_quota,
    init_quota_db,
    record_quota_run,
    render_quota_result,
)


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "quota_test.db")
    init_quota_db(p)
    return p


def _insert(db_path: str, job: str, seconds_ago: int) -> None:
    ts = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    record_quota_run(db_path, job, ran_at=ts)


def test_allowed_when_no_history(db_path: str) -> None:
    result = check_quota(db_path, "backup", limit=3, window_seconds=3600)
    assert result.allowed is True
    assert result.used == 0


def test_allowed_when_under_limit(db_path: str) -> None:
    _insert(db_path, "backup", 60)
    _insert(db_path, "backup", 120)
    result = check_quota(db_path, "backup", limit=3, window_seconds=3600)
    assert result.allowed is True
    assert result.used == 2


def test_blocked_when_at_limit(db_path: str) -> None:
    for i in range(3):
        _insert(db_path, "backup", 60 * (i + 1))
    result = check_quota(db_path, "backup", limit=3, window_seconds=3600)
    assert result.allowed is False
    assert result.used == 3


def test_old_runs_outside_window_ignored(db_path: str) -> None:
    _insert(db_path, "backup", 7200)  # 2 h ago — outside 1-h window
    _insert(db_path, "backup", 7200)
    _insert(db_path, "backup", 7200)
    result = check_quota(db_path, "backup", limit=3, window_seconds=3600)
    assert result.allowed is True
    assert result.used == 0


def test_different_jobs_are_independent(db_path: str) -> None:
    for i in range(3):
        _insert(db_path, "other_job", 60)
    result = check_quota(db_path, "backup", limit=3, window_seconds=3600)
    assert result.allowed is True


def test_record_quota_run_increments_count(db_path: str) -> None:
    record_quota_run(db_path, "sync")
    result = check_quota(db_path, "sync", limit=5, window_seconds=3600)
    assert result.used == 1


def test_render_allowed(db_path: str) -> None:
    result = check_quota(db_path, "myjob", limit=10, window_seconds=600)
    text = render_quota_result(result)
    assert "ALLOWED" in text
    assert "myjob" in text


def test_render_blocked(db_path: str) -> None:
    for _ in range(2):
        _insert(db_path, "myjob", 30)
    result = check_quota(db_path, "myjob", limit=2, window_seconds=3600)
    text = render_quota_result(result)
    assert "BLOCKED" in text
