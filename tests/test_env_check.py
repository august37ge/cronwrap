import os
import pytest
from cronwrap.env_check import (
    check_env,
    check_env_from_config,
    render_env_check_result,
    EnvCheckResult,
)


def test_all_present(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    monkeypatch.setenv("BAZ", "qux")
    result = check_env("myjob", ["FOO", "BAZ"])
    assert result.ok
    assert result.missing == []
    assert set(result.present) == {"FOO", "BAZ"}


def test_some_missing(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    monkeypatch.delenv("MISSING_VAR", raising=False)
    result = check_env("myjob", ["FOO", "MISSING_VAR"])
    assert not result.ok
    assert "MISSING_VAR" in result.missing
    assert "FOO" in result.present


def test_all_missing(monkeypatch):
    monkeypatch.delenv("A", raising=False)
    monkeypatch.delenv("B", raising=False)
    result = check_env("myjob", ["A", "B"])
    assert not result.ok
    assert set(result.missing) == {"A", "B"}
    assert result.present == []


def test_render_ok(monkeypatch):
    monkeypatch.setenv("FOO", "1")
    result = check_env("job1", ["FOO"])
    text = render_env_check_result(result)
    assert "job1" in text
    assert "All required" in text


def test_render_missing(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    result = check_env("job2", ["NOPE"])
    text = render_env_check_result(result)
    assert "MISSING" in text
    assert "NOPE" in text


def test_check_env_from_config_no_vars():
    result = check_env_from_config("job", {})
    assert result is None


def test_check_env_from_config_with_vars(monkeypatch):
    monkeypatch.setenv("TOKEN", "abc")
    monkeypatch.delenv("SECRET", raising=False)
    result = check_env_from_config("job", {"env_vars": ["TOKEN", "SECRET"]})
    assert result is not None
    assert not result.ok
    assert "SECRET" in result.missing
