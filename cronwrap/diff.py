"""Snapshot diff: compare two snapshots and report changes in job metrics."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from cronwrap.snapshots import Snapshot


@dataclass
class MetricDiff:
    job_name: str
    old_success_rate: Optional[float]
    new_success_rate: Optional[float]
    old_avg_duration: Optional[float]
    new_avg_duration: Optional[float]

    @property
    def success_rate_delta(self) -> Optional[float]:
        if self.old_success_rate is None or self.new_success_rate is None:
            return None
        return self.new_success_rate - self.old_success_rate

    @property
    def avg_duration_delta(self) -> Optional[float]:
        if self.old_avg_duration is None or self.new_avg_duration is None:
            return None
        return self.new_avg_duration - self.old_avg_duration


def diff_snapshots(old: Snapshot, new: Snapshot) -> List[MetricDiff]:
    """Return a list of MetricDiff for all jobs appearing in either snapshot."""
    old_data: Dict[str, dict] = {m["job_name"]: m for m in old.metrics}
    new_data: Dict[str, dict] = {m["job_name"]: m for m in new.metrics}
    all_jobs = sorted(set(old_data) | set(new_data))
    diffs = []
    for job in all_jobs:
        o = old_data.get(job, {})
        n = new_data.get(job, {})
        diffs.append(MetricDiff(
            job_name=job,
            old_success_rate=o.get("success_rate"),
            new_success_rate=n.get("success_rate"),
            old_avg_duration=o.get("avg_duration"),
            new_avg_duration=n.get("avg_duration"),
        ))
    return diffs


def render_diff(diffs: List[MetricDiff]) -> str:
    if not diffs:
        return "No differences found."
    lines = [f"{'Job':<30} {'Success Rate Δ':>16} {'Avg Duration Δ':>16}"]
    lines.append("-" * 64)
    for d in diffs:
        sr = f"{d.success_rate_delta:+.1f}%" if d.success_rate_delta is not None else "N/A"
        ad = f"{d.avg_duration_delta:+.2f}s" if d.avg_duration_delta is not None else "N/A"
        lines.append(f"{d.job_name:<30} {sr:>16} {ad:>16}")
    return "\n".join(lines)


def print_diff(diffs: List[MetricDiff]) -> None:
    print(render_diff(diffs))
