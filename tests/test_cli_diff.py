"""Tests for cronwrap.cli_diff."""
import argparse
import pytest
from unittest.mock import patch
from cronwrap.cli_diff import add_diff_subparser, run_diff
from cronwrap.snapshots import Snapshot
from datetime import datetime


def _make_namespace(**kwargs):
    defaults = {"db": ":memory:", "old": "v1", "new": "v2"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _snap(label):
    return Snapshot(label=label, taken_at=datetime.utcnow(), metrics=[])


def test_add_diff_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_diff_subparser(sub)
    args = parser.parse_args(["diff", "--old", "v1", "--new", "v2"])
    assert args.old == "v1"
    assert args.new == "v2"


def test_run_diff_missing_old_returns_one():
    ns = _make_namespace(old="missing", new="v2")
    with patch("cronwrap.cli_diff.get_snapshots", return_value=[_snap("v2")]):
        assert run_diff(ns) == 1


def test_run_diff_missing_new_returns_one():
    ns = _make_namespace(old="v1", new="missing")
    with patch("cronwrap.cli_diff.get_snapshots", return_value=[_snap("v1")]):
        assert run_diff(ns) == 1


def test_run_diff_success(capsys):
    ns = _make_namespace(old="v1", new="v2")
    snaps = [_snap("v1"), _snap("v2")]
    with patch("cronwrap.cli_diff.get_snapshots", return_value=snaps):
        rc = run_diff(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No differences" in out
