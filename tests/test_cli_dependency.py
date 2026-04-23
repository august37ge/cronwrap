"""Tests for cronwrap.cli_dependency."""

from __future__ import annotations

import argparse

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.cli_dependency import add_dependency_subparser, run_dependency
from datetime import datetime, timezone


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
            duration=0.5,
            exit_code=exit_code,
            stdout="",
            stderr="",
            retries=0,
            tags="",
        ),
        db_path=db_path,
    )


def _ns(job, requires, db, lookback=1):
    return argparse.Namespace(job=job, requires=requires, db=db, lookback=lookback)


def test_add_dependency_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_dependency_subparser(sub)
    args = parser.parse_args(["dependency", "myjob", "--requires", "up"])
    assert args.job == "myjob"
    assert args.requires == ["up"]


def test_run_dependency_satisfied_returns_zero(db_path):
    _rec("up", 0, db_path)
    ns = _ns("myjob", ["up"], db_path)
    assert run_dependency(ns) == 0


def test_run_dependency_blocked_returns_one(db_path):
    _rec("up", 1, db_path)
    ns = _ns("myjob", ["up"], db_path)
    assert run_dependency(ns) == 1


def test_run_dependency_missing_returns_one(db_path):
    ns = _ns("myjob", ["ghost"], db_path)
    assert run_dependency(ns) == 1
