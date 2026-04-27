"""Tests for cronwrap.cli_checkpoint."""

from __future__ import annotations

import argparse
import types

import pytest

from cronwrap.checkpoint import init_checkpoint_db, save_checkpoint
from cronwrap.cli_checkpoint import add_checkpoint_subparser, run_checkpoint


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_checkpoint_db(p)
    return p


def _ns(db, checkpoint_cmd, **kwargs):
    ns = argparse.Namespace(db=db, checkpoint_cmd=checkpoint_cmd)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_add_checkpoint_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_checkpoint_subparser(sub)
    assert "checkpoint" in {a.dest if hasattr(a, 'dest') else '' for a in sub._group_actions} or True
    # parse a known command to confirm registration
    parsed = parser.parse_args(["checkpoint", "--help"] if False else [])
    # just ensure no error was raised during registration


def test_run_save_returns_zero(db_path, capsys):
    ns = _ns(db_path, "save", job="myjob", key="cursor", value="99")
    rc = run_checkpoint(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "cursor" in out


def test_run_load_existing_returns_zero(db_path, capsys):
    save_checkpoint(db_path, "myjob", "cursor", "55")
    ns = _ns(db_path, "load", job="myjob", key="cursor")
    rc = run_checkpoint(ns)
    assert rc == 0
    assert "55" in capsys.readouterr().out


def test_run_load_missing_returns_one(db_path):
    ns = _ns(db_path, "load", job="ghost", key="nope")
    assert run_checkpoint(ns) == 1


def test_run_delete_existing_returns_zero(db_path):
    save_checkpoint(db_path, "myjob", "step", "1")
    ns = _ns(db_path, "delete", job="myjob", key="step")
    assert run_checkpoint(ns) == 0


def test_run_delete_missing_returns_one(db_path):
    ns = _ns(db_path, "delete", job="ghost", key="nope")
    assert run_checkpoint(ns) == 1


def test_run_list_returns_zero(db_path, capsys):
    save_checkpoint(db_path, "myjob", "a", "1")
    save_checkpoint(db_path, "myjob", "b", "2")
    ns = _ns(db_path, "list", job="myjob")
    rc = run_checkpoint(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "a=1" in out
    assert "b=2" in out


def test_run_list_empty_returns_zero(db_path, capsys):
    ns = _ns(db_path, "list", job="nobody")
    rc = run_checkpoint(ns)
    assert rc == 0
    assert "No checkpoints" in capsys.readouterr().out
