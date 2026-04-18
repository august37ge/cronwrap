"""Tests for cronwrap.lockfile."""

from __future__ import annotations

import os
import pytest
from pathlib import Path

from cronwrap import lockfile


@pytest.fixture
def lock_dir(tmp_path):
    return str(tmp_path / "locks")


def test_acquire_creates_lock(lock_dir):
    result = lockfile.acquire(lock_dir, "my-job")
    assert result.acquired is True
    assert Path(result.lock_path).exists()


def test_lock_file_contains_pid(lock_dir):
    lockfile.acquire(lock_dir, "my-job")
    path = Path(lock_dir) / "my-job.lock"
    assert int(path.read_text().strip()) == os.getpid()


def test_acquire_blocked_by_live_lock(lock_dir):
    lockfile.acquire(lock_dir, "my-job")
    result = lockfile.acquire(lock_dir, "my-job")
    assert result.acquired is False
    assert result.existing_pid == os.getpid()
    assert "already running" in result.message


def test_release_removes_lock(lock_dir):
    lockfile.acquire(lock_dir, "my-job")
    removed = lockfile.release(lock_dir, "my-job")
    assert removed is True
    path = Path(lock_dir) / "my-job.lock"
    assert not path.exists()


def test_release_missing_lock_returns_false(lock_dir):
    removed = lockfile.release(lock_dir, "ghost-job")
    assert removed is False


def test_is_locked_true_when_active(lock_dir):
    lockfile.acquire(lock_dir, "my-job")
    assert lockfile.is_locked(lock_dir, "my-job") is True


def test_is_locked_false_after_release(lock_dir):
    lockfile.acquire(lock_dir, "my-job")
    lockfile.release(lock_dir, "my-job")
    assert lockfile.is_locked(lock_dir, "my-job") is False


def test_stale_lock_overwritten(lock_dir, tmp_path):
    os.makedirs(lock_dir, exist_ok=True)
    path = Path(lock_dir) / "stale-job.lock"
    path.write_text("99999999")  # Non-existent PID
    result = lockfile.acquire(lock_dir, "stale-job")
    assert result.acquired is True
    assert int(path.read_text().strip()) == os.getpid()


def test_job_name_with_slashes(lock_dir):
    result = lockfile.acquire(lock_dir, "group/my-job")
    assert result.acquired is True
    assert "group_my-job.lock" in result.lock_path
