"""Tests for cronwrap.cli_prune."""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.cli_prune import add_prune_subparser, run_prune


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _rec(job: str, success: bool = True, ts: str = "2024-01-01T00:00:00") -> JobRecord:
    return JobRecord(
        job_name=job,
        started_at=ts,
        duration_seconds=1.0,
        success=success,
        exit_code=0 if success else 1,
        output="ok",
    )


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = {
        "db": "cronwrap.db",
        "job": None,
        "keep": 100,
        "config": None,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_prune_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_prune_subparser(subs)
    ns = parser.parse_args(["prune", "--keep", "50"])
    assert ns.command == "prune"
    assert ns.keep == 50


def test_run_prune_dry_run_returns_zero(db_path: str, capsys):
    ns = _make_namespace(db=db_path, dry_run=True)
    code = run_prune(ns)
    assert code == 0
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


def test_run_prune_all_returns_zero(db_path: str):
    for i in range(5):
        record_run(db_path, _rec("job_a", ts=f"2024-01-{i+1:02d}T00:00:00"))
    ns = _make_namespace(db=db_path, keep=3)
    code = run_prune(ns)
    assert code == 0


def test_run_prune_specific_job(db_path: str):
    for i in range(5):
        record_run(db_path, _rec("job_b", ts=f"2024-01-{i+1:02d}T00:00:00"))
    ns = _make_namespace(db=db_path, job="job_b", keep=2)
    code = run_prune(ns)
    assert code == 0
