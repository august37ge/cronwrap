"""Tests for the cli_report subcommand."""
from __future__ import annotations

import sqlite3
import tempfile
import os
import argparse
from datetime import datetime, timezone

import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.cli_report import add_report_subparser, run_report


@pytest.fixture()
def db_path(tmp_path):
    p = tmp_path / "test.db"
    init_db(str(p))
    return str(p)


def _rec(job_id: str, success: bool, tag: str | None = None) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        started_at=datetime.now(timezone.utc),
        duration_seconds=1.0,
        exit_code=0 if success else 1,
        success=success,
        output="ok" if success else "err",
        tags=[tag] if tag else [],
    )


def _make_namespace(db: str, limit: int = 10, tag: str | None = None) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.db = db
    ns.limit = limit
    ns.tag = tag
    ns.func = run_report
    return ns


def test_add_report_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_report_subparser(subs)
    args = parser.parse_args(["report", "--limit", "5"])
    assert args.limit == 5
    assert args.func is run_report


def test_run_report_returns_zero(db_path, capsys):
    record_run(db_path, _rec("job-a", True))
    ns = _make_namespace(db_path)
    rc = run_report(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "job-a" in out


def test_run_report_with_tag_filters(db_path, capsys):
    record_run(db_path, _rec("job-tagged", True, tag="nightly"))
    record_run(db_path, _rec("job-other", True))
    ns = _make_namespace(db_path, tag="nightly")
    rc = run_report(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "nightly" in out


def test_run_report_empty_db_no_crash(db_path, capsys):
    ns = _make_namespace(db_path)
    rc = run_report(ns)
    assert rc == 0
