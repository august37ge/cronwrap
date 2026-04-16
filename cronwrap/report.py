"""Generate human-readable metrics reports."""
from __future__ import annotations

from typing import List

from cronwrap.metrics import JobMetrics, get_all_job_metrics


_HEADER = "{:<30} {:>8} {:>8} {:>8} {:>10} {:>10} {:>10}".format(
    "Job", "Total", "OK", "Fail", "Avg(s)", "Max(s)", "Success%"
)
_SEP = "-" * len(_HEADER)


def _format_row(m: JobMetrics) -> str:
    return "{:<30} {:>8} {:>8} {:>8} {:>10} {:>10} {:>9}%".format(
        m.job_name[:30],
        m.total_runs,
        m.successful_runs,
        m.failed_runs,
        m.avg_duration_seconds,
        m.max_duration_seconds,
        m.success_rate,
    )


def render_text_report(metrics: List[JobMetrics]) -> str:
    """Return a plain-text table of job metrics."""
    if not metrics:
        return "No job history found."
    lines = [_HEADER, _SEP]
    for m in sorted(metrics, key=lambda x: x.job_name):
        lines.append(_format_row(m))
    lines.append(_SEP)
    return "\n".join(lines)


def print_report(db_path: str, limit: int = 100) -> None:
    """Fetch metrics from *db_path* and print a report to stdout."""
    metrics = get_all_job_metrics(db_path, limit=limit)
    print(render_text_report(metrics))
