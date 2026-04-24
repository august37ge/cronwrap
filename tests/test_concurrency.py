"""Tests for cronwrap.concurrency."""
from __future__ import annotations

import os
import argparse
import pytest

from cronwrap.concurrency import (
    ConcurrencyResult,
    active_run_count,
    check_concurrency,
    init_concurrency_db,
    register_run,
    render_concurrency_result,
    unregister_run,
)
from cronwrap.cli_concurrency import add_concurrency_subparser, run_concurrency


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test_concurrency.db")
    init_concurrency_db(p)
    return p


def test_init_creates_table(db_path):
    import sqlite3
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert "active_runs" in tables


def test_allowed_when_no_active_runs(db_path):
    result = check_concurrency(db_path, "backup", max_concurrent=1)
    assert result.allowed is True
    assert result.active_count == 0


def test_blocked_when_at_capacity(db_path):
    register_run(db_path, "backup", pid=1234)
    result = check_concurrency(db_path, "backup", max_concurrent=1)
    assert result.allowed is False
    assert result.active_count == 1


def test_allowed_when_below_max(db_path):
    register_run(db_path, "backup", pid=1111)
    result = check_concurrency(db_path, "backup", max_concurrent=3)
    assert result.allowed is True
    assert result.active_count == 1


def test_unregister_removes_record(db_path):
    run_id = register_run(db_path, "backup", pid=9999)
    assert active_run_count(db_path, "backup") == 1
    unregister_run(db_path, run_id)
    assert active_run_count(db_path, "backup") == 0


def test_runs_isolated_by_job_name(db_path):
    register_run(db_path, "job_a", pid=1)
    register_run(db_path, "job_a", pid=2)
    result_a = check_concurrency(db_path, "job_a", max_concurrent=1)
    result_b = check_concurrency(db_path, "job_b", max_concurrent=1)
    assert result_a.allowed is False
    assert result_b.allowed is True


def test_render_allowed(db_path):
    result = check_concurrency(db_path, "myjob", max_concurrent=2)
    text = render_concurrency_result(result)
    assert "ALLOWED" in text
    assert "myjob" in text


def test_render_blocked(db_path):
    register_run(db_path, "myjob", pid=42)
    result = check_concurrency(db_path, "myjob", max_concurrent=1)
    text = render_concurrency_result(result)
    assert "BLOCKED" in text


def _make_namespace(**kwargs):
    defaults = dict(job_name="testjob", max_concurrent=1, db=None, register=False, unregister=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_concurrency_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_concurrency_subparser(sub)
    ns = parser.parse_args(["concurrency", "myjob"])
    assert ns.job_name == "myjob"


def test_run_concurrency_allowed_returns_zero(db_path):
    ns = _make_namespace(db=db_path)
    assert run_concurrency(ns) == 0


def test_run_concurrency_blocked_returns_one(db_path):
    register_run(db_path, "testjob", pid=1)
    ns = _make_namespace(db=db_path, max_concurrent=1)
    assert run_concurrency(ns) == 1


def test_run_concurrency_unregister(db_path):
    run_id = register_run(db_path, "testjob", pid=55)
    ns = _make_namespace(db=db_path, unregister=run_id)
    code = run_concurrency(ns)
    assert code == 0
    assert active_run_count(db_path, "testjob") == 0
