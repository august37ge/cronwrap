"""Tests for cronwrap.circuit_breaker and cronwrap.cli_circuit."""
from __future__ import annotations

import argparse
import os
import tempfile
from datetime import datetime, timezone

import pytest

from cronwrap.history import JobRecord, init_db, record_run
from cronwrap.circuit_breaker import check_circuit, render_circuit_state
from cronwrap.cli_circuit import add_circuit_subparser, run_circuit


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "history.db")
    init_db(p)
    return p


def _rec(job, exit_code, started_at="2024-01-01T00:00:00"):
    return JobRecord(
        job_name=job,
        started_at=started_at,
        finished_at=started_at,
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=1.0,
    )


def test_closed_when_no_failures(db_path):
    record_run(db_path, _rec("myjob", 0))
    cs = check_circuit("myjob", db_path, threshold=3)
    assert cs.state == "closed"
    assert cs.consecutive_failures == 0
    assert not cs.is_open


def test_open_after_threshold_failures(db_path):
    for _ in range(3):
        record_run(db_path, _rec("myjob", 1))
    cs = check_circuit("myjob", db_path, threshold=3)
    assert cs.state == "open"
    assert cs.is_open
    assert cs.consecutive_failures == 3


def test_half_open_below_threshold(db_path):
    record_run(db_path, _rec("myjob", 1))
    cs = check_circuit("myjob", db_path, threshold=3)
    assert cs.state == "half-open"
    assert cs.consecutive_failures == 1


def test_closed_after_success_resets_streak(db_path):
    record_run(db_path, _rec("myjob", 1, "2024-01-01T00:00:00"))
    record_run(db_path, _rec("myjob", 0, "2024-01-01T00:01:00"))
    record_run(db_path, _rec("myjob", 1, "2024-01-01T00:02:00"))
    # newest run is failure but only 1 consecutive
    cs = check_circuit("myjob", db_path, threshold=3)
    assert cs.state == "half-open"


def test_render_circuit_state_open(db_path):
    for _ in range(3):
        record_run(db_path, _rec("myjob", 1))
    cs = check_circuit("myjob", db_path, threshold=3)
    text = render_circuit_state(cs)
    assert "OPEN" in text
    assert "myjob" in text


def test_add_circuit_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_circuit_subparser(subs)
    args = parser.parse_args(["circuit", "myjob", "--db", "/tmp/x.db"])
    assert args.job_name == "myjob"


def test_run_circuit_returns_zero_when_closed(db_path):
    record_run(db_path, _rec("myjob", 0))
    ns = argparse.Namespace(
        job_name="myjob", db=db_path, threshold=3, lookback=10, fail_if_open=False
    )
    assert run_circuit(ns) == 0


def test_run_circuit_returns_one_when_open_and_flag_set(db_path):
    for _ in range(3):
        record_run(db_path, _rec("myjob", 1))
    ns = argparse.Namespace(
        job_name="myjob", db=db_path, threshold=3, lookback=10, fail_if_open=True
    )
    assert run_circuit(ns) == 1
