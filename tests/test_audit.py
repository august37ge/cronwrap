"""Tests for cronwrap.audit and cronwrap.cli_audit."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwrap.audit import AuditEntry, get_audit_entries, init_audit_db, record_audit
from cronwrap.cli_audit import add_audit_subparser, run_audit


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "audit_test.db")
    init_audit_db(p)
    return p


def _ts() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_init_creates_table(db_path: str) -> None:
    # calling init twice is idempotent
    init_audit_db(db_path)
    entries = get_audit_entries(db_path)
    assert entries == []


def test_record_and_retrieve(db_path: str) -> None:
    record_audit(db_path, "backup", "tar czf ...", _ts(), 0, 1.23, retries=0, tags=["daily"])
    entries = get_audit_entries(db_path)
    assert len(entries) == 1
    e = entries[0]
    assert e.job_name == "backup"
    assert e.exit_code == 0
    assert e.duration_s == pytest.approx(1.23)
    assert e.tags == "daily"


def test_filter_by_job_name(db_path: str) -> None:
    record_audit(db_path, "jobA", "cmd", _ts(), 0, 0.5)
    record_audit(db_path, "jobB", "cmd", _ts(), 1, 0.6)
    assert len(get_audit_entries(db_path, job_name="jobA")) == 1
    assert len(get_audit_entries(db_path, job_name="jobB")) == 1
    assert len(get_audit_entries(db_path)) == 2


def test_limit_respected(db_path: str) -> None:
    for i in range(10):
        record_audit(db_path, "job", "cmd", _ts(), 0, float(i))
    assert len(get_audit_entries(db_path, limit=3)) == 3


def test_cli_audit_returns_zero(db_path: str, capsys: pytest.CaptureFixture) -> None:
    record_audit(db_path, "myjob", "echo hi", _ts(), 0, 0.1, tags=["tag1"])
    ns = argparse.Namespace(db=db_path, job=None, limit=10)
    result = run_audit(ns)
    assert result == 0
    out = capsys.readouterr().out
    assert "myjob" in out


def test_cli_audit_no_entries(db_path: str, capsys: pytest.CaptureFixture) -> None:
    ns = argparse.Namespace(db=db_path, job=None, limit=10)
    result = run_audit(ns)
    assert result == 0
    assert "No audit entries" in capsys.readouterr().out


def test_add_audit_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_audit_subparser(sub)
    ns = parser.parse_args(["audit", "--limit", "5"])
    assert ns.limit == 5
