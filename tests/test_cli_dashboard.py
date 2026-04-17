"""Tests for cronwrap.cli_dashboard"""
import argparse
import datetime
import pytest

from cronwrap.history import init_db, record_run, JobRecord
from cronwrap.cli_dashboard import add_dashboard_subparser, run_dashboard


@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _make_namespace(db, config=None):
    ns = argparse.Namespace()
    ns.db = db
    ns.config = config
    return ns


def _rec(job):
    return JobRecord(job_name=job, exit_code=0, duration=1.0,
                     stdout="", stderr="",
                     timestamp=datetime.datetime.utcnow().isoformat(),
                     attempt=1)


def test_add_dashboard_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_dashboard_subparser(sub)
    args = parser.parse_args(["dashboard", "--db", "x.db"])
    assert args.db == "x.db"


def test_run_dashboard_returns_zero(db_path):
    record_run(db_path, _rec("job1"))
    ns = _make_namespace(db_path)
    assert run_dashboard(ns) == 0


def test_run_dashboard_empty_db(db_path, capsys):
    ns = _make_namespace(db_path)
    rc = run_dashboard(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No job data" in out


def test_run_dashboard_with_data(db_path, capsys):
    record_run(db_path, _rec("alpha"))
    ns = _make_namespace(db_path)
    run_dashboard(ns)
    out = capsys.readouterr().out
    assert "alpha" in out
