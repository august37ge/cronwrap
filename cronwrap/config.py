"""Config loading with tag support."""
from __future__ import annotations
import json
import os
from typing import Any, Dict, List


def load_config(path: str) -> Dict[str, Any]:
    """Load a JSON or TOML config file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path) as f:
            return json.load(f)
    if ext == ".toml":
        try:
            import tomllib  # type: ignore
        except ImportError:
            import tomli as tomllib  # type: ignore
        with open(path, "rb") as f:
            return tomllib.load(f)
    raise ValueError(f"Unsupported config format: {ext}")


def get_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the list of job definitions from a config dict.

    Each job may include an optional 'tags' list for filtering.
    """
    jobs = config.get("jobs", [])
    for job in jobs:
        job.setdefault("tags", [])
    return jobs


def get_jobs_by_tag(config: Dict[str, Any], tag: str) -> List[Dict[str, Any]]:
    """Return jobs that include the given tag."""
    return [j for j in get_jobs(config) if tag in j.get("tags", [])]
