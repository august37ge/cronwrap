"""Tests for cronwrap.cooldown."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.cooldown import CooldownResult, check_cooldown, render_cooldown_result
from cronwrap.history import init_db


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _insert(db_path: str, job_name: str, success: bool, offset_seconds: int = 0) -> None:
    """Insert a run record *offset_seconds* ago."""
    ts = (datetime.now(timezone.utc) - timedelta(seconds=offset_seconds)).isoformat()
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute(
        "INSERT INTO runs (job_name, started_at, duration, success, output) VALUES (?,?,?,?,?)",
        (job_name, ts, 1.0, int(success), ""),
    )
    con.commit()
    con.close()


def test_allowed_when_no_history(db_path: str) -> None:
    result = check_cooldown(db_path, "myjob", cooldown_seconds=60)
    assert result.allowed is True
    assert result.last_failure is None
    assert result.retry_after is None


def test_allowed_when_last_run_succeeded(db_path: str) -> None:
    _insert(db_path, "myjob", success=True, offset_seconds=10)
    result = check_cooldown(db_path, "myjob", cooldown_seconds=60)
    assert result.allowed is True


def test_blocked_when_failure_within_window(db_path: str) -> None:
    _insert(db_path, "myjob", success=False, offset_seconds=30)
    result = check_cooldown(db_path, "myjob", cooldown_seconds=60)
    assert result.allowed is False
    assert result.last_failure is not None
    assert result.retry_after is not None


def test_allowed_when_failure_outside_window(db_path: str) -> None:
    _insert(db_path, "myjob", success=False, offset_seconds=120)
    result = check_cooldown(db_path, "myjob", cooldown_seconds=60)
    assert result.allowed is True
    assert result.retry_after is None


def test_render_allowed(db_path: str) -> None:
    result = CooldownResult(
        job_name="j", allowed=True, last_failure=None,
        cooldown_seconds=60, retry_after=None,
    )
    text = render_cooldown_result(result)
    assert "allowed" in text
    assert "j" in text


def test_render_blocked() -> None:
    result = CooldownResult(
        job_name="j", allowed=False,
        last_failure="2024-01-01T00:00:00+00:00",
        cooldown_seconds=300,
        retry_after="2024-01-01T00:05:00+00:00",
    )
    text = render_cooldown_result(result)
    assert "BLOCKED" in text
    assert "2024-01-01T00:05:00" in text
