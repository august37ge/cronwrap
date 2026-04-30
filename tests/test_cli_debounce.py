"""Tests for cronwrap.cli_debounce."""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwrap.cli_debounce import add_debounce_subparser, run_debounce


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


def _ns(db_path: str, job_name: str = "myjob", min_gap: float = 60.0, quiet: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        db=db_path,
        job_name=job_name,
        min_gap=min_gap,
        quiet=quiet,
    )


def _insert_recent(db_path: str, job_name: str, seconds_ago: float) -> None:
    dt = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO runs (job_name, started_at, exit_code, success) VALUES (?, ?, 0, 1)",
        (job_name, dt.isoformat()),
    )
    conn.commit()
    conn.close()


# ── subparser registration ────────────────────────────────────────────────────

def test_add_debounce_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_debounce_subparser(subs)
    parsed = parser.parse_args(["debounce", "myjob"])
    assert parsed.job_name == "myjob"


# ── run_debounce exit codes ───────────────────────────────────────────────────

def test_run_debounce_allowed_returns_zero(db_path: str) -> None:
    rc = run_debounce(_ns(db_path, quiet=True))
    assert rc == 0


def test_run_debounce_blocked_returns_one(db_path: str) -> None:
    _insert_recent(db_path, "myjob", seconds_ago=5)
    rc = run_debounce(_ns(db_path, min_gap=60.0, quiet=True))
    assert rc == 1


def test_run_debounce_prints_output(db_path: str, capsys: pytest.CaptureFixture) -> None:
    run_debounce(_ns(db_path, quiet=False))
    captured = capsys.readouterr()
    assert "debounce" in captured.out.lower()


def test_run_debounce_quiet_suppresses_output(db_path: str, capsys: pytest.CaptureFixture) -> None:
    run_debounce(_ns(db_path, quiet=True))
    captured = capsys.readouterr()
    assert captured.out == ""
