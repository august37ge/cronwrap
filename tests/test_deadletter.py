"""Tests for cronwrap.deadletter."""

from __future__ import annotations

import pytest
from pathlib import Path

from cronwrap.deadletter import (
    init_deadletter_db,
    push_dead_letter,
    get_dead_letters,
    purge_dead_letters,
)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "dl.db"


def test_init_creates_table(db_path: Path) -> None:
    init_deadletter_db(db_path)
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert "dead_letter" in tables


def test_push_and_retrieve(db_path: Path) -> None:
    push_dead_letter("backup", "rsync /src /dst", exit_code=1, stderr="error", db_path=db_path)
    entries = get_dead_letters(db_path=db_path)
    assert len(entries) == 1
    e = entries[0]
    assert e.job_name == "backup"
    assert e.command == "rsync /src /dst"
    assert e.exit_code == 1
    assert e.stderr == "error"
    assert e.attempt == 1


def test_get_dead_letters_filter_by_job(db_path: Path) -> None:
    push_dead_letter("job_a", "cmd_a", exit_code=2, db_path=db_path)
    push_dead_letter("job_b", "cmd_b", exit_code=3, db_path=db_path)
    results = get_dead_letters(job_name="job_a", db_path=db_path)
    assert len(results) == 1
    assert results[0].job_name == "job_a"


def test_get_dead_letters_limit(db_path: Path) -> None:
    for i in range(10):
        push_dead_letter("myjob", f"cmd {i}", exit_code=1, db_path=db_path)
    results = get_dead_letters(limit=4, db_path=db_path)
    assert len(results) == 4


def test_purge_by_job_name(db_path: Path) -> None:
    push_dead_letter("job_a", "cmd", exit_code=1, db_path=db_path)
    push_dead_letter("job_b", "cmd", exit_code=1, db_path=db_path)
    removed = purge_dead_letters(job_name="job_a", db_path=db_path)
    assert removed == 1
    remaining = get_dead_letters(db_path=db_path)
    assert all(e.job_name == "job_b" for e in remaining)


def test_purge_all(db_path: Path) -> None:
    for _ in range(5):
        push_dead_letter("anyjob", "cmd", exit_code=1, db_path=db_path)
    removed = purge_dead_letters(db_path=db_path)
    assert removed == 5
    assert get_dead_letters(db_path=db_path) == []


def test_attempt_field_stored(db_path: Path) -> None:
    push_dead_letter("retry_job", "cmd", exit_code=1, attempt=3, db_path=db_path)
    entries = get_dead_letters(job_name="retry_job", db_path=db_path)
    assert entries[0].attempt == 3
