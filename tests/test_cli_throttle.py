"""Tests for cronwrap.cli_throttle."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.cli_throttle import add_throttle_subparser, run_throttle


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _ns(job_name, min_interval, db):
    return argparse.Namespace(job_name=job_name, min_interval=min_interval, db=db)


def _rec(job_name, started_at):
    return JobRecord(
        job_name=job_name,
        started_at=started_at,
        duration_seconds=1.0,
        exit_code=0,
        success=True,
        output="",
    )


def test_add_throttle_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_throttle_subparser(sub)
    ns = parser.parse_args(["throttle", "myjob", "--min-interval", "60"])
    assert ns.job_name == "myjob"
    assert ns.min_interval == 60


def test_run_throttle_allowed_returns_zero(db_path):
    ns = _ns("myjob", 300, db_path)
    assert run_throttle(ns) == 0


def test_run_throttle_blocked_returns_two(db_path):
    recent = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    record_run(_rec("myjob", recent), db_path=db_path)
    ns = _ns("myjob", 300, db_path)
    assert run_throttle(ns) == 2


def test_run_throttle_prints_message(db_path, capsys):
    ns = _ns("myjob", 300, db_path)
    run_throttle(ns)
    captured = capsys.readouterr()
    assert "myjob" in captured.out
