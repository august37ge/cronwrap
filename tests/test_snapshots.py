"""Tests for cronwrap.snapshots and cronwrap.cli_snapshot."""
from __future__ import annotations

import argparse
import pytest
from datetime import datetime, timezone, timedelta

from cronwrap.history import init_db, record_run
from cronwrap.snapshots import init_snapshot_db, save_snapshot, get_snapshots, take_snapshot, Snapshot
from cronwrap.cli_snapshot import add_snapshot_subparser, run_snapshot


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(p)
    init_snapshot_db(p)
    return p


def _rec(job_name, success=True, duration=1.0, started_at=None):
    from cronwrap.history import JobRecord
    ts = (started_at or datetime.now(timezone.utc)).isoformat()
    return JobRecord(
        job_name=job_name,
        started_at=ts,
        finished_at=ts,
        success=success,
        exit_code=0 if success else 1,
        duration=duration,
        output="ok",
    )


def test_save_and_get_snapshots(db_path):
    snap = Snapshot(
        job_name="myjob",
        taken_at=datetime.now(timezone.utc).isoformat(),
        total_runs=10,
        success_count=8,
        failure_count=2,
        avg_duration=1.5,
        max_duration=3.0,
    )
    save_snapshot(db_path, snap)
    results = get_snapshots(db_path, "myjob")
    assert len(results) == 1
    assert results[0].total_runs == 10
    assert results[0].success_count == 8


def test_get_snapshots_empty(db_path):
    assert get_snapshots(db_path, "ghost") == []


def test_take_snapshot_no_metrics(db_path):
    snap = take_snapshot(db_path, "nonexistent")
    assert snap is None


def test_take_snapshot_with_metrics(db_path):
    from cronwrap.history import record_run
    record_run(db_path, _rec("backup", success=True, duration=2.0))
    record_run(db_path, _rec("backup", success=False, duration=4.0))
    snap = take_snapshot(db_path, "backup")
    assert snap is not None
    assert snap.total_runs == 2
    assert snap.success_count == 1
    assert snap.failure_count == 1
    assert snap.max_duration == pytest.approx(4.0)


def _make_namespace(**kwargs):
    defaults = {"db": None, "snapshot_cmd": None, "job_name": "job", "limit": 5}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_snapshot_subparser_registers_command():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_snapshot_subparser(sub)
    ns = p.parse_args(["snapshot", "take", "myjob"])
    assert ns.job_name == "myjob"


def test_run_snapshot_take(db_path):
    from cronwrap.history import record_run
    record_run(db_path, _rec("backup", duration=1.0))
    ns = _make_namespace(db=db_path, snapshot_cmd="take", job_name="backup")
    assert run_snapshot(ns) == 0


def test_run_snapshot_view(db_path):
    ns = _make_namespace(db=db_path, snapshot_cmd="view", job_name="backup", limit=5)
    assert run_snapshot(ns) == 0


def test_run_snapshot_no_subcommand(db_path):
    ns = _make_namespace(db=db_path, snapshot_cmd=None)
    assert run_snapshot(ns) == 1
