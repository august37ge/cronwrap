"""Tests for cronwrap.cli_pipeline."""
import argparse
import json
import sys
from pathlib import Path

import pytest

from cronwrap.cli_pipeline import add_pipeline_subparser, run_pipeline_cmd


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    ok_cmd = f"{sys.executable} -c 'print(1)'"
    fail_cmd = f"{sys.executable} -c 'raise SystemExit(1)'"
    cfg = {
        "pipelines": {
            "build": {
                "steps": [
                    {"name": "compile", "command": ok_cmd},
                    {"name": "lint", "command": ok_cmd},
                ]
            },
            "broken": {
                "steps": [
                    {"name": "fail", "command": fail_cmd},
                ]
            },
        }
    }
    p = tmp_path / "cronwrap.json"
    p.write_text(json.dumps(cfg))
    return p


def _ns(config: str, name: str, dry_run: bool = False) -> argparse.Namespace:
    return argparse.Namespace(config=config, name=name, dry_run=dry_run)


def test_add_pipeline_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    add_pipeline_subparser(subs)
    args = parser.parse_args(["pipeline", "--config", "x.json", "--name", "build"])
    assert args.cmd == "pipeline"


def test_run_pipeline_success_returns_zero(config_file: Path):
    rc = run_pipeline_cmd(_ns(str(config_file), "build"))
    assert rc == 0


def test_run_pipeline_failure_returns_one(config_file: Path):
    rc = run_pipeline_cmd(_ns(str(config_file), "broken"))
    assert rc == 1


def test_run_pipeline_missing_config_returns_one(tmp_path: Path):
    rc = run_pipeline_cmd(_ns(str(tmp_path / "no.json"), "build"))
    assert rc == 1


def test_run_pipeline_unknown_name_returns_one(config_file: Path):
    rc = run_pipeline_cmd(_ns(str(config_file), "nonexistent"))
    assert rc == 1


def test_dry_run_returns_zero_without_executing(config_file: Path):
    rc = run_pipeline_cmd(_ns(str(config_file), "broken", dry_run=True))
    assert rc == 0
