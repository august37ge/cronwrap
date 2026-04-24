"""Tests for cronwrap.cli_cooldown."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.cli_cooldown import add_cooldown_subparser, run_cooldown
from cronwrap.history import init_db


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _ns(db_path: str, job_name: str = "myjob", seconds: int = 300) -> argparse.Namespace:
    return argparse.Namespace(db=db_path, job_name=job_name, seconds=seconds)


def _insert_failure(db_path: str, offset_seconds: int) -> None:
    ts = (datetime.now(timezone.utc) - timedelta(seconds=offset_seconds)).isoformat()
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO runs (job_name, started_at, duration, success, output) VALUES (?,?,?,?,?)",
        ("myjob", ts, 1.0, 0, ""),
    )
    con.commit()
    con.close()


def test_add_cooldown_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_cooldown_subparser(subs)
    args = parser.parse_args(["cooldown", "somejob"])
    assert args.job_name == "somejob"


def test_run_cooldown_allowed_returns_zero(db_path: str) -> None:
    code = run_cooldown(_ns(db_path))
    assert code == 0


def test_run_cooldown_blocked_returns_one(db_path: str) -> None:
    _insert_failure(db_path, offset_seconds=10)
    code = run_cooldown(_ns(db_path, seconds=300))
    assert code == 1


def test_run_cooldown_outside_window_returns_zero(db_path: str) -> None:
    _insert_failure(db_path, offset_seconds=400)
    code = run_cooldown(_ns(db_path, seconds=300))
    assert code == 0
