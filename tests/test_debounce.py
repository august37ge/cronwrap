"""Tests for cronwrap.debounce."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.debounce import check_debounce, render_debounce_result


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "test.db")
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            exit_code INTEGER,
            success INTEGER
        )
        """
    )
    conn.commit()
    conn.close()
    return path


def _insert(db_path: str, job_name: str, started_at: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO runs (job_name, started_at, exit_code, success) VALUES (?, ?, 0, 1)",
        (job_name, started_at),
    )
    conn.commit()
    conn.close()


def _ago(seconds: float) -> str:
    dt = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    return dt.isoformat()


# ── core logic ────────────────────────────────────────────────────────────────

def test_allowed_when_no_history(db_path: str) -> None:
    result = check_debounce(db_path, "myjob", min_gap_seconds=30)
    assert result.allowed is True
    assert result.last_run_at is None
    assert "no previous run" in result.reason


def test_allowed_when_gap_exceeds_min(db_path: str) -> None:
    _insert(db_path, "myjob", _ago(120))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    assert result.allowed is True
    assert result.gap_seconds is not None
    assert result.gap_seconds >= 60


def test_debounced_when_gap_too_small(db_path: str) -> None:
    _insert(db_path, "myjob", _ago(10))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    assert result.allowed is False
    assert "debounced" in result.reason


def test_only_checks_latest_run(db_path: str) -> None:
    # old run (would be allowed) + recent run (should be debounced)
    _insert(db_path, "myjob", _ago(300))
    _insert(db_path, "myjob", _ago(5))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    assert result.allowed is False


def test_does_not_affect_other_jobs(db_path: str) -> None:
    _insert(db_path, "other_job", _ago(5))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    assert result.allowed is True


def test_exact_boundary_is_allowed(db_path: str) -> None:
    # gap == min_gap should be allowed
    _insert(db_path, "myjob", _ago(60))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    # floating-point: gap may be 60.0xx
    assert result.allowed is True


# ── rendering ─────────────────────────────────────────────────────────────────

def test_render_allowed(db_path: str) -> None:
    _insert(db_path, "myjob", _ago(120))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    text = render_debounce_result(result)
    assert "ALLOWED" in text
    assert "myjob" in text


def test_render_debounced(db_path: str) -> None:
    _insert(db_path, "myjob", _ago(5))
    result = check_debounce(db_path, "myjob", min_gap_seconds=60)
    text = render_debounce_result(result)
    assert "DEBOUNCED" in text
