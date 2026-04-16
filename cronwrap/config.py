"""Load cronwrap job configuration from a TOML or JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


DEFAULT_CONFIG_PATHS = ["cronwrap.toml", "cronwrap.json", ".cronwrap.toml", ".cronwrap.json"]


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    """Load configuration from *path*, or search default locations."""
    if path is None:
        for candidate in DEFAULT_CONFIG_PATHS:
            p = Path(candidate)
            if p.exists():
                path = p
                break
        else:
            return {}
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open() as fh:
            return json.load(fh)
    if suffix in (".toml",):
        if tomllib is None:
            raise ImportError("tomllib/tomli is required to read TOML config files")
        with path.open("rb") as fh:
            return tomllib.load(fh)
    raise ValueError(f"Unsupported config format: {suffix}")


def get_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract the list of job definitions from a loaded config dict."""
    return config.get("jobs", [])
