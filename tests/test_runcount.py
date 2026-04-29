"""Tests for cronwrap.runcount and cronwrap.cli_runcount."""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.runcount import RunCountResult, count_runs, render_runcount_result
from cronwrap.cli_runcount import add_runcount_subparser, run_runcount


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "test.db")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE runs ("
            "  job_name TEXT NOT NULL,"
            "  started_at TEXT NOT NULL,"
            "  exit_code INTEGER NOT NULL"
            ")"
        )
    return path


def _insert(db_path: str, job_name: str, offset_seconds: int = 0) -> None:
    ts = (datetime.now(tz=timezone.utc) - timedelta(seconds=offset_seconds)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO runs (job_name, started_at, exit_code) VALUES (?, ?, 0)",
            (job_name, ts),
        )


# --- unit tests for count_runs ---

def test_no_runs_returns_zero(db_path: str) -> None:
    result = count_runs(db_path, "myjob", window_seconds=3600)
    assert result.count == 0
    assert result.allowed is True


def test_counts_runs_within_window(db_path: str) -> None:
    _insert(db_path, "myjob", offset_seconds=60)
    _insert(db_path, "myjob", offset_seconds=120)
    result = count_runs(db_path, "myjob", window_seconds=3600)
    assert result.count == 2


def test_ignores_runs_outside_window(db_path: str) -> None:
    _insert(db_path, "myjob", offset_seconds=7200)  # 2 h ago, outside 1 h window
    result = count_runs(db_path, "myjob", window_seconds=3600)
    assert result.count == 0


def test_ignores_other_jobs(db_path: str) -> None:
    _insert(db_path, "otherjob", offset_seconds=10)
    result = count_runs(db_path, "myjob", window_seconds=3600)
    assert result.count == 0


def test_blocked_when_at_limit(db_path: str) -> None:
    for _ in range(3):
        _insert(db_path, "myjob", offset_seconds=30)
    result = count_runs(db_path, "myjob", window_seconds=3600, limit=3)
    assert result.allowed is False
    assert result.count == 3


def test_allowed_when_below_limit(db_path: str) -> None:
    _insert(db_path, "myjob", offset_seconds=30)
    result = count_runs(db_path, "myjob", window_seconds=3600, limit=5)
    assert result.allowed is True


# --- render ---

def test_render_ok_contains_ok() -> None:
    r = RunCountResult("j", 3600, 1, 5, True, "j: 1/5 — allowed")
    assert "[OK]" in render_runcount_result(r)


def test_render_blocked_contains_blocked() -> None:
    r = RunCountResult("j", 3600, 5, 5, False, "j: 5/5 — limit reached")
    assert "[BLOCKED]" in render_runcount_result(r)


# --- CLI ---

def _make_namespace(db_path: str, job_name: str = "myjob", window: int = 3600, limit=None):
    return argparse.Namespace(db=db_path, job_name=job_name, window=window, limit=limit)


def test_add_runcount_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_runcount_subparser(sub)
    ns = parser.parse_args(["runcount", "myjob"])
    assert ns.job_name == "myjob"


def test_run_runcount_returns_zero_when_allowed(db_path: str) -> None:
    ns = _make_namespace(db_path, limit=10)
    assert run_runcount(ns) == 0


def test_run_runcount_returns_one_when_blocked(db_path: str) -> None:
    _insert(db_path, "myjob", offset_seconds=10)
    ns = _make_namespace(db_path, limit=1)
    assert run_runcount(ns) == 1
