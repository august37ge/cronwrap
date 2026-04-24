"""Tests for cronwrap.cli_quota."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.quota import init_quota_db, record_quota_run
from cronwrap.cli_quota import add_quota_subparser, run_quota


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "cli_quota.db")
    init_quota_db(p)
    return p


def _ns(db_path: str, job: str, limit: int, window: int, record: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        db=db_path,
        job_name=job,
        limit=limit,
        window=window,
        record=record,
    )


def _insert(db_path: str, job: str, seconds_ago: int) -> None:
    ts = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    record_quota_run(db_path, job, ran_at=ts)


def test_add_quota_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_quota_subparser(sub)
    ns = parser.parse_args(["quota", "myjob", "--limit", "5", "--window", "3600", "--db", "x.db"])
    assert ns.job_name == "myjob"
    assert ns.limit == 5
    assert ns.window == 3600


def test_run_quota_allowed_returns_zero(db_path: str) -> None:
    ns = _ns(db_path, "backup", limit=5, window=3600)
    assert run_quota(ns) == 0


def test_run_quota_blocked_returns_one(db_path: str) -> None:
    for _ in range(3):
        _insert(db_path, "backup", 60)
    ns = _ns(db_path, "backup", limit=3, window=3600)
    assert run_quota(ns) == 1


def test_run_quota_record_flag_increments(db_path: str) -> None:
    from cronwrap.quota import check_quota
    ns = _ns(db_path, "sync", limit=10, window=3600, record=True)
    run_quota(ns)
    result = check_quota(db_path, "sync", limit=10, window_seconds=3600)
    assert result.used == 1


def test_run_quota_no_record_when_blocked(db_path: str) -> None:
    from cronwrap.quota import check_quota
    for _ in range(2):
        _insert(db_path, "sync", 30)
    ns = _ns(db_path, "sync", limit=2, window=3600, record=True)
    run_quota(ns)
    # Should still be 2, not 3
    result = check_quota(db_path, "sync", limit=10, window_seconds=3600)
    assert result.used == 2
