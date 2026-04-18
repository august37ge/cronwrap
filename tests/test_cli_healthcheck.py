"""Tests for cronwrap.cli_healthcheck."""
import argparse

import pytest

from cronwrap.runner import RunResult
from cronwrap.healthcheck import write_status
from cronwrap.cli_healthcheck import add_healthcheck_subparser, run_healthcheck


@pytest.fixture()
def status_dir(tmp_path):
    return str(tmp_path / "status")


def _ns(job, status_dir, max_age=0):
    return argparse.Namespace(job=job, status_dir=status_dir, max_age=max_age)


def _result(success=True, exit_code=0):
    return RunResult(success=success, exit_code=exit_code,
                     stdout="done", stderr="", duration=0.5)


def test_add_healthcheck_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_healthcheck_subparser(sub)
    args = parser.parse_args(["healthcheck", "myjob"])
    assert args.job == "myjob"


def test_run_healthcheck_missing_returns_one(status_dir):
    rc = run_healthcheck(_ns("ghost", status_dir))
    assert rc == 1


def test_run_healthcheck_success_returns_zero(status_dir):
    write_status("backup", _result(success=True), status_dir)
    rc = run_healthcheck(_ns("backup", status_dir))
    assert rc == 0


def test_run_healthcheck_failure_returns_one(status_dir):
    write_status("backup", _result(success=False, exit_code=2), status_dir)
    rc = run_healthcheck(_ns("backup", status_dir))
    assert rc == 1


def test_run_healthcheck_stale_returns_two(status_dir):
    write_status("backup", _result(success=True), status_dir)
    rc = run_healthcheck(_ns("backup", status_dir, max_age=0))
    assert rc == 2
