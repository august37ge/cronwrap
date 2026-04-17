"""Tag-aware reporting: show metrics grouped by tag."""
from __future__ import annotations
from typing import Dict, List, Optional

from cronwrap.tags import TagIndex
from cronwrap.metrics import get_job_metrics, JobMetrics


def metrics_by_tag(tag_index: TagIndex, db_path: str) -> Dict[str, List[JobMetrics]]:
    """Return a mapping of tag -> list of JobMetrics for jobs in that tag."""
    result: Dict[str, List[JobMetrics]] = {}
    for tag in tag_index.all_tags():
        job_names = tag_index.jobs_for_tag(tag)
        metrics_list = []
        for name in job_names:
            m = get_job_metrics(db_path, name)
            if m is not None:
                metrics_list.append(m)
        result[tag] = metrics_list
    return result


def render_tag_report(tag_metrics: Dict[str, List[JobMetrics]]) -> str:
    """Render a text report grouped by tag."""
    if not tag_metrics:
        return "No tag data available.\n"
    lines = []
    for tag in sorted(tag_metrics):
        lines.append(f"[{tag}]")
        entries = tag_metrics[tag]
        if not entries:
            lines.append("  (no history)")
        else:
            for m in sorted(entries, key=lambda x: x.job_name):
                lines.append(
                    f"  {m.job_name}: runs={m.total_runs} "
                    f"ok={m.successful_runs} fail={m.failed_runs} "
                    f"avg={m.avg_duration_s:.1f}s"
                )
        lines.append("")
    return "\n".join(lines)


def print_tag_report(tag_metrics: Dict[str, List[JobMetrics]]) -> None:
    print(render_tag_report(tag_metrics))
