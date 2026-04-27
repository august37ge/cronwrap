"""Tests for cronwrap.checkpoint."""

from __future__ import annotations

import pytest

from cronwrap.checkpoint import (
    Checkpoint,
    delete_checkpoint,
    init_checkpoint_db,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    init_checkpoint_db(p)
    return p


def test_init_creates_table(db_path):
    import sqlite3
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert "checkpoints" in tables


def test_save_and_load(db_path):
    save_checkpoint(db_path, "myjob", "last_id", "42")
    cp = load_checkpoint(db_path, "myjob", "last_id")
    assert cp is not None
    assert isinstance(cp, Checkpoint)
    assert cp.job_name == "myjob"
    assert cp.key == "last_id"
    assert cp.value == "42"


def test_load_missing_returns_none(db_path):
    assert load_checkpoint(db_path, "ghost", "no_key") is None


def test_save_overwrites_existing(db_path):
    save_checkpoint(db_path, "myjob", "cursor", "100")
    save_checkpoint(db_path, "myjob", "cursor", "200")
    cp = load_checkpoint(db_path, "myjob", "cursor")
    assert cp is not None
    assert cp.value == "200"


def test_delete_existing_returns_true(db_path):
    save_checkpoint(db_path, "myjob", "step", "3")
    removed = delete_checkpoint(db_path, "myjob", "step")
    assert removed is True
    assert load_checkpoint(db_path, "myjob", "step") is None


def test_delete_missing_returns_false(db_path):
    assert delete_checkpoint(db_path, "nobody", "nope") is False


def test_list_checkpoints_ordered_by_key(db_path):
    save_checkpoint(db_path, "myjob", "z_key", "z")
    save_checkpoint(db_path, "myjob", "a_key", "a")
    save_checkpoint(db_path, "myjob", "m_key", "m")
    entries = list_checkpoints(db_path, "myjob")
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_list_checkpoints_empty(db_path):
    assert list_checkpoints(db_path, "unknown_job") == []


def test_list_checkpoints_isolated_per_job(db_path):
    save_checkpoint(db_path, "job_a", "k", "1")
    save_checkpoint(db_path, "job_b", "k", "2")
    assert len(list_checkpoints(db_path, "job_a")) == 1
    assert list_checkpoints(db_path, "job_a")[0].value == "1"
