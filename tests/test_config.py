"""Tests for cronwrap.config."""

import json
import textwrap
from pathlib import Path

import pytest

from cronwrap.config import get_jobs, load_config


def test_load_json_config(tmp_path):
    cfg = {"jobs": [{"name": "backup", "schedule": "0 2 * * *", "command": "backup.sh"}]}
    p = tmp_path / "cronwrap.json"
    p.write_text(json.dumps(cfg))
    loaded = load_config(p)
    assert loaded["jobs"][0]["name"] == "backup"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_load_unsupported_format_raises(tmp_path):
    p = tmp_path / "cronwrap.yaml"
    p.write_text("jobs: []")
    with pytest.raises(ValueError, match="Unsupported"):
        load_config(p)


def test_get_jobs_returns_list():
    config = {"jobs": [{"name": "ping", "schedule": "* * * * *"}]}
    jobs = get_jobs(config)
    assert len(jobs) == 1
    assert jobs[0]["name"] == "ping"


def test_get_jobs_empty_when_missing():
    assert get_jobs({}) == []


def test_load_config_no_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = load_config()
    assert result == {}
