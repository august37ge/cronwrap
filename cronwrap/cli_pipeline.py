"""CLI sub-command: cronwrap pipeline — run a named pipeline from config."""
from __future__ import annotations

import argparse
import sys
from typing import Any

from cronwrap.config import load_config
from cronwrap.pipeline import PipelineStep, render_pipeline_result, run_pipeline


def add_pipeline_subparser(subparsers: Any) -> None:
    p = subparsers.add_parser(
        "pipeline",
        help="Run a sequential pipeline of commands defined in config",
    )
    p.add_argument("--config", required=True, help="Path to config file (JSON/YAML)")
    p.add_argument("--name", required=True, help="Pipeline name to run")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print steps without executing",
    )


def run_pipeline_cmd(ns: argparse.Namespace) -> int:
    try:
        cfg = load_config(ns.config)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    pipelines = cfg.get("pipelines", {})
    if ns.name not in pipelines:
        print(f"ERROR: pipeline '{ns.name}' not found in config", file=sys.stderr)
        return 1

    raw_steps = pipelines[ns.name].get("steps", [])
    steps = [
        PipelineStep(
            name=s["name"],
            command=s["command"],
            timeout=s.get("timeout"),
            retries=s.get("retries", 0),
        )
        for s in raw_steps
    ]

    if ns.dry_run:
        print(f"Pipeline '{ns.name}' — dry run ({len(steps)} steps):")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step.name}: {step.command}")
        return 0

    result = run_pipeline(ns.name, steps)
    print(render_pipeline_result(result))
    return 0 if result.succeeded else 1
