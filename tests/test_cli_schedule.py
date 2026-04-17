"""Tests for cronwrap.cli_schedule."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from cronwrap.cli_schedule import add_schedule_subparser, run_schedule


@pytest.fixture()
def config_file():
    data = {
        "jobs": [
            {"name": "backup", "schedule": "0 2 * * *", "command": "tar -czf /tmp/b.tgz /data"},
            {"name": "cleanup", "schedule": "*/10 * * * *", "command": "rm -rf /tmp/old"},
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture()
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


def _make_namespace(config, db, overdue_only=False):
    ns = argparse.Namespace()
    ns.config = config
    ns.db = db
    ns.overdue_only = overdue_only
    ns.func = run_schedule
    return ns


def test_add_schedule_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_schedule_subparser(sub)
    args = parser.parse_args(["schedule", "--config", "c.json"])
    assert args.func is run_schedule


def test_run_schedule_returns_zero(config_file, db_path):
    ns = _make_namespace(config_file, db_path)
    result = run_schedule(ns)
    assert result == 0


def test_run_schedule_overdue_only(config_file, db_path, capsys):
    ns = _make_namespace(config_file, db_path, overdue_only=True)
    result = run_schedule(ns)
    assert result == 0


def test_run_schedule_no_jobs(db_path, tmp_path):
    cfg = tmp_path / "empty.json"
    cfg.write_text(json.dumps({"jobs": []}))
    ns = _make_namespace(str(cfg), db_path)
    result = run_schedule(ns)
    assert result == 0
